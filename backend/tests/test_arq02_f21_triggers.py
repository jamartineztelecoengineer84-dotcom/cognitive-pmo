"""
ARQ-02 F2.1 — tests de los triggers run→live + FK CASCADE + EXISTS check.

Verifica los 4 invariantes que validamos in-tx en F2.1-VERIFY, ahora contra
la BD real (sin BEGIN/ROLLBACK envolvente). Cada test crea su propio ticket
con generar_ticket_id(), valida el comportamiento, y limpia su rastro con
DELETE FROM incidencias_run (la FK CASCADE se encarga del live).

Al final del módulo, setval('inc_ticket_seq', 37, true) restaura baseline.

Ejecutar:
  docker compose exec api python -m pytest tests/test_arq02_f21_triggers.py -v
"""
import asyncio
import os
import pytest
import asyncpg
import httpx


API_URL = "http://localhost:8088"
ADMIN_EMAIL = "admin"
ADMIN_PASS  = "admin"

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "cognitive_pmo")
DB_USER = os.getenv("DB_USER", "jose_admin")
DB_PASS = os.getenv("DB_PASSWORD", "")


async def _conn():
    return await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASS,
    )


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _create_test_ticket(conn, descripcion="ARQ02 F2.1 test", prioridad="P3"):
    """Crea un ticket en incidencias_run con generar_ticket_id() + ESTADO QUEUED."""
    tid = await conn.fetchval("SELECT generar_ticket_id()")
    await conn.execute("""
        INSERT INTO incidencias_run (
            ticket_id, incidencia_detectada, prioridad_ia, estado, categoria,
            sla_limite, tecnico_asignado
        ) VALUES ($1, $2, $3, 'QUEUED', 'TEST', 24, NULL)
    """, tid, descripcion, prioridad)
    return tid


async def _delete_test_ticket(conn, tid):
    """CASCADE borra también de incidencias_live."""
    await conn.execute("DELETE FROM incidencias_run WHERE ticket_id = $1", tid)


# ── Tests ────────────────────────────────────────────────────────────

def test_trigger_insert_crea_live():
    """Invariante I1: INSERT en run con estado abierto crea fila en live."""
    async def _go():
        c = await _conn()
        try:
            tid = await _create_test_ticket(c)
            row = await c.fetchrow(
                "SELECT estado, prioridad, sla_horas FROM incidencias_live WHERE ticket_id = $1",
                tid,
            )
            assert row is not None, f"trigger no creó la fila para {tid}"
            assert row["estado"] == "IN_PROGRESS"
            assert row["prioridad"] == "P3"
            assert float(row["sla_horas"]) == 24.0
            await _delete_test_ticket(c, tid)
        finally:
            await c.close()
    _run(_go())


def test_trigger_update_propaga_no_ui():
    """Invariante I2: UPDATE de tecnico_asignado propaga, progreso_pct intacto."""
    async def _go():
        c = await _conn()
        try:
            tid = await _create_test_ticket(c)
            # Marcar progreso desde el shell (path PUT habitual)
            await c.execute("""
                UPDATE incidencias_live
                SET progreso_pct = 42, total_tareas = 5, tareas_completadas = 2
                WHERE ticket_id = $1
            """, tid)
            # Cambiar tecnico en run
            await c.execute("""
                UPDATE incidencias_run
                SET estado='EN_CURSO', tecnico_asignado='FTE-001'
                WHERE ticket_id = $1
            """, tid)
            row = await c.fetchrow("""
                SELECT estado, tecnico_asignado, progreso_pct, total_tareas, tareas_completadas
                FROM incidencias_live WHERE ticket_id = $1
            """, tid)
            assert row["estado"] == "IN_PROGRESS", "estado live no debe cambiar"
            assert row["tecnico_asignado"] == "FTE-001", "tecnico debe propagarse"
            assert row["progreso_pct"] == 42, "progreso_pct UI no debe ser tocado"
            assert row["total_tareas"] == 5, "total_tareas UI no debe ser tocado"
            assert row["tareas_completadas"] == 2, "tareas_completadas UI no debe ser tocado"
            await _delete_test_ticket(c, tid)
        finally:
            await c.close()
    _run(_go())


def test_trigger_resuelto_borra_live():
    """Invariante I3: UPDATE estado→RESUELTO borra de live, run intacto."""
    async def _go():
        c = await _conn()
        try:
            tid = await _create_test_ticket(c)
            assert await c.fetchval(
                "SELECT 1 FROM incidencias_live WHERE ticket_id = $1", tid
            ) == 1
            await c.execute(
                "UPDATE incidencias_run SET estado='RESUELTO' WHERE ticket_id = $1", tid
            )
            assert await c.fetchval(
                "SELECT COUNT(*) FROM incidencias_live WHERE ticket_id = $1", tid
            ) == 0, "live debería estar vacía tras RESUELTO"
            assert await c.fetchval(
                "SELECT 1 FROM incidencias_run WHERE ticket_id = $1", tid
            ) == 1, "run debe seguir intacto"
            await _delete_test_ticket(c, tid)
        finally:
            await c.close()
    _run(_go())


def test_trigger_reapertura_recrea_live():
    """Invariante I4: ciclo QUEUED → RESUELTO → QUEUED recrea live (fallback)."""
    async def _go():
        c = await _conn()
        try:
            tid = await _create_test_ticket(c)
            await c.execute(
                "UPDATE incidencias_run SET estado='RESUELTO' WHERE ticket_id = $1", tid
            )
            await c.execute(
                "UPDATE incidencias_run SET estado='QUEUED', tecnico_asignado='FTE-002' WHERE ticket_id = $1",
                tid,
            )
            row = await c.fetchrow("""
                SELECT estado, tecnico_asignado, progreso_pct
                FROM incidencias_live WHERE ticket_id = $1
            """, tid)
            assert row is not None, "live debe recrearse al reabrir"
            assert row["estado"] == "IN_PROGRESS"
            assert row["tecnico_asignado"] == "FTE-002"
            assert row["progreso_pct"] == 0, "ticket reabierto empieza con progreso 0"
            await _delete_test_ticket(c, tid)
        finally:
            await c.close()
    _run(_go())


def test_fk_cascade_delete():
    """FK ON DELETE CASCADE: borrar run borra automáticamente live."""
    async def _go():
        c = await _conn()
        try:
            tid = await _create_test_ticket(c)
            assert await c.fetchval(
                "SELECT 1 FROM incidencias_live WHERE ticket_id = $1", tid
            ) == 1
            await c.execute("DELETE FROM incidencias_run WHERE ticket_id = $1", tid)
            assert await c.fetchval(
                "SELECT COUNT(*) FROM incidencias_live WHERE ticket_id = $1", tid
            ) == 0
        finally:
            await c.close()
    _run(_go())


def test_post_incidencias_live_404_si_no_existe_run():
    """EXISTS check del POST /incidencias/live: 404 si el ticket no existe en run."""
    # login admin
    r = httpx.post(
        f"{API_URL}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=10,
    )
    assert r.status_code == 200
    token = r.json()["token"]

    fake_tid = "INC-999999-29991231"
    r = httpx.post(
        f"{API_URL}/incidencias/live",
        json={
            "ticket_id": fake_tid,
            "incidencia_detectada": "Ticket inventado para test 404",
            "prioridad": "P4",
            "sla_horas": 48,
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert r.status_code == 404, f"esperaba 404, got {r.status_code} {r.text}"
    body = r.json()
    assert "no existe" in body.get("detail", "").lower()


def test_zz_reset_sequence():
    """Final del módulo: reset SEQUENCE a baseline 37 (los _create_test_ticket
    consumen valores reales aunque los DELETE limpien las filas)."""
    async def _go():
        c = await _conn()
        try:
            await c.execute("SELECT setval('inc_ticket_seq', 37, true)")
            seq = await c.fetchval("SELECT last_value FROM inc_ticket_seq")
            assert seq == 37
        finally:
            await c.close()
    _run(_go())

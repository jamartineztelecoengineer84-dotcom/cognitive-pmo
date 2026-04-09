"""
ARQ-02 Deuda A.3 — F-ARQ02-05: tests para validar que el trigger F2.1
trg_run_to_live_insert cubre todas las columnas críticas que el endpoint
POST /incidencias/live (ahora deprecado) rellenaba.

Cubre:
1. INSERT manual en incidencias_run dispara trigger → 1 fila correspondiente
   en incidencias_live con el mismo ticket_id
2. Las columnas críticas se propagan correctamente, fecha_limite calculada
   ±2s respecto a fecha_creacion + interval '<sla_horas> hours'
3. POST /incidencias/live deprecated sigue siendo idempotente (ON CONFLICT
   DO NOTHING) cuando llega un ticket_id que ya existe vía trigger

Mismo patrón sync (_run + asyncpg) que el resto del repo.
"""
import asyncio
import os
import asyncpg
import httpx


API_URL = "http://localhost:8088"

DB_HOST = os.getenv("DB_HOST", "192.168.1.49")
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


async def _create_test_run_ticket(conn, **overrides):
    """Insert un ticket de prueba en incidencias_run con generar_ticket_id().
    Devuelve el ticket_id. CASCADE limpia live al borrar."""
    tid = await conn.fetchval("SELECT generar_ticket_id()")
    await conn.execute(f"""
        INSERT INTO incidencias_run (
            ticket_id, incidencia_detectada, prioridad_ia, categoria,
            sla_limite, area_afectada, canal_entrada, reportado_por,
            servicio_afectado, impacto_negocio, estado
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'QUEUED'
        )
    """,
        tid,
        overrides.get("incidencia_detectada", "test deudaA3"),
        overrides.get("prioridad_ia", "P3"),
        overrides.get("categoria", "Base de Datos"),
        overrides.get("sla_limite", 24),
        overrides.get("area_afectada", "Producción"),
        overrides.get("canal_entrada", "test"),
        overrides.get("reportado_por", "pytest"),
        overrides.get("servicio_afectado", "db-test"),
        overrides.get("impacto_negocio", "test impacto"),
    )
    return tid


def test_insert_run_dispara_trigger_a_live():
    """1. INSERT manual en incidencias_run → fila correspondiente en live."""
    async def _go():
        c = await _conn()
        try:
            tid = await _create_test_run_ticket(c)
            n_live = await c.fetchval(
                "SELECT COUNT(*) FROM incidencias_live WHERE ticket_id = $1", tid
            )
            await c.execute("DELETE FROM incidencias_run WHERE ticket_id = $1", tid)
            return n_live
        finally:
            await c.close()
    assert _run(_go()) == 1, "trigger no creó la fila live esperada"


def test_trigger_propaga_columnas_criticas():
    """2. Trigger propaga 8 columnas críticas + calcula fecha_limite con
    tolerancia ±2 segundos respecto a fecha_creacion + N horas."""
    async def _go():
        c = await _conn()
        try:
            tid = await _create_test_run_ticket(c)
            row = await c.fetchrow("""
                SELECT incidencia_detectada, prioridad, sla_horas, estado,
                       canal_entrada, reportado_por, servicio_afectado,
                       impacto_negocio, fecha_creacion, fecha_limite
                FROM incidencias_live WHERE ticket_id = $1
            """, tid)
            await c.execute("DELETE FROM incidencias_run WHERE ticket_id = $1", tid)
            return row
        finally:
            await c.close()
    row = _run(_go())
    assert row is not None, "fila live no encontrada"
    assert row["incidencia_detectada"] == "test deudaA3"
    assert row["prioridad"] == "P3"
    assert float(row["sla_horas"]) == 24.0
    assert row["estado"] == "IN_PROGRESS"
    assert row["canal_entrada"] == "test"
    assert row["reportado_por"] == "pytest"
    assert row["servicio_afectado"] == "db-test"
    assert row["impacto_negocio"] == "test impacto"
    # fecha_limite ≈ fecha_creacion + 24h, tolerancia ±2s
    delta = (row["fecha_limite"] - row["fecha_creacion"]).total_seconds()
    expected = 24 * 3600
    assert abs(delta - expected) < 2, (
        f"fecha_limite mal calculada: delta={delta}s, esperado={expected}±2s"
    )


def test_endpoint_post_live_sigue_idempotente():
    """3. POST /incidencias/live deprecated devuelve 200 cuando el ticket
    YA existe en run+live (vía trigger). ON CONFLICT DO NOTHING absorbe."""
    async def _setup():
        c = await _conn()
        try:
            tid = await _create_test_run_ticket(c, incidencia_detectada="deudaA3 idempotent test")
            return tid
        finally:
            await c.close()

    async def _cleanup(tid):
        c = await _conn()
        try:
            await c.execute("DELETE FROM incidencias_run WHERE ticket_id = $1", tid)
        finally:
            await c.close()

    async def _verify_unique(tid):
        c = await _conn()
        try:
            return await c.fetchval(
                "SELECT COUNT(*) FROM incidencias_live WHERE ticket_id = $1", tid
            )
        finally:
            await c.close()

    tid = _run(_setup())
    try:
        # POST /incidencias/live debería devolver 200 sin crear duplicado
        r = httpx.post(
            f"{API_URL}/incidencias/live",
            json={
                "ticket_id": tid,
                "incidencia_detectada": "deudaA3 idempotent test",
                "prioridad": "P3",
                "sla_horas": 24,
                "canal_entrada": "test",
                "reportado_por": "pytest",
                "servicio_afectado": "db-test",
                "impacto_negocio": "test impacto",
            },
            timeout=10,
        )
        assert r.status_code == 200, f"esperaba 200, got {r.status_code} {r.text}"
        # Sigue habiendo exactamente 1 fila en live
        n = _run(_verify_unique(tid))
        assert n == 1, f"esperaba 1 fila live, got {n} (endpoint NO es idempotente)"
    finally:
        _run(_cleanup(tid))

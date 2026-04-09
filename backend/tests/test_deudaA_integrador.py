"""
Bloque A — cierre: test integrador end-to-end del flow
POST /incidencias → POST /agents/AG-001/invoke con prefijo TICKET:.

Verifica que tras la cadena completa:
- incidencias_run sube exactamente +1 (NO +2 — F-ARQ02-04 cubierta por A.2:
  AG-001 detecta el prefijo TICKET y reusa el ticket vía pre_existing_ticket_id)
- incidencias_live sube exactamente +1 (vía trigger F2.1, F-ARQ02-05 cubierta
  por A.3: el frontend ya no llama POST /incidencias/live, lo crea el trigger)

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


async def _counts():
    c = await _conn()
    try:
        run_n = await c.fetchval("SELECT COUNT(*) FROM incidencias_run")
        live_n = await c.fetchval("SELECT COUNT(*) FROM incidencias_live")
        return run_n, live_n
    finally:
        await c.close()


async def _cleanup(tid):
    c = await _conn()
    try:
        # Deuda C.2 / F-ARQ02-06: borrar kanban hijas + agent_conversations
        # ANTES de la incidencia padre (no hay FK CASCADE entre estas tablas
        # e incidencias_run — son columnas soft). Sin esto, AG-001 dejaría
        # 6-8 kanban huérfanas por cada run, drift acumulativo en los 3 tests
        # F-ARQ02-01.
        await c.execute("DELETE FROM kanban_tareas WHERE id_incidencia = $1", tid)
        await c.execute("DELETE FROM agent_conversations WHERE ticket_id = $1", tid)
        await c.execute("DELETE FROM incidencias_run WHERE ticket_id = $1", tid)
    finally:
        await c.close()


def test_integrador_end_to_end_no_duplica_ticket():
    """POST /incidencias + POST /agents/AG-001/invoke (TICKET: prefix)
    → Δ run == +1 y Δ live == +1 (no +2)."""
    run_pre, live_pre = _run(_counts())

    # 1) Crear ticket vía endpoint shell (igual que hace el frontend)
    r = httpx.post(
        f"{API_URL}/incidencias",
        json={
            "descripcion": "Deuda A integrador test - servidor de base de datos lento",
            "prioridad": "P3",
            "categoria": "Base de Datos",
            "area_afectada": "Producción",
            "sla_limite": 24,
            "canal_entrada": "test",
            "reportado_por": "pytest-integrador",
            "servicio_afectado": "db-test",
            "impacto_negocio": "test impacto integrador",
        },
        timeout=15,
    )
    assert r.status_code == 200, f"POST /incidencias falló: {r.status_code} {r.text}"
    tid = r.json().get("ticket_id")
    assert tid and tid.startswith("INC-"), f"ticket_id inválido: {tid}"

    try:
        # 2) Invocar AG-001 con prefijo TICKET: → debe reusar, no crear nuevo
        invoke_r = httpx.post(
            f"{API_URL}/agents/AG-001/invoke",
            json={
                "message": (
                    f"TICKET: {tid}\n"
                    "El servidor de base de datos está lento, los usuarios "
                    "reportan timeouts en la aplicación principal."
                ),
                "session_id": f"deudaA-integrador-{tid}",
            },
            timeout=180,  # AG-001 hace varias llamadas a Anthropic
        )
        assert invoke_r.status_code == 200, (
            f"invoke AG-001 falló: {invoke_r.status_code} {invoke_r.text[:500]}"
        )

        # 3) Verificar deltas
        run_post, live_post = _run(_counts())
        delta_run = run_post - run_pre
        delta_live = live_post - live_pre

        assert delta_run == 1, (
            f"Δ incidencias_run = {delta_run}, esperaba 1 (AG-001 duplicó "
            f"el ticket — F-ARQ02-04 NO cubierta). pre={run_pre} post={run_post}"
        )
        assert delta_live == 1, (
            f"Δ incidencias_live = {delta_live}, esperaba 1 (trigger F2.1 "
            f"no funcionó o el shell sigue llamando POST /incidencias/live). "
            f"pre={live_pre} post={live_post}"
        )
    finally:
        _run(_cleanup(tid))

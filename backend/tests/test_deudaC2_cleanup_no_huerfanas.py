"""
Deuda C.2 — F-ARQ02-06: tests de regresión para garantizar que no vuelve a
haber kanban_tareas huérfanas (id_incidencia apuntando a fantasma) ni
agent_conversations con ticket_id apuntando a una incidencia inexistente.

El cleanup defensivo en test_deudaA_integrador.py + el SQL one-shot
arq02_deudaC2_cleanup.sql purgaron las residuales históricas. Estos tests
fallarán si vuelve a aparecer drift por un test sin cleanup defensivo o por
un nuevo path de ingesta sin FK CASCADE.

Patrón sync (_run + asyncpg) usado por el resto del repo.
"""
import asyncio
import os
import asyncpg


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


def test_no_kanban_huerfanas():
    """Ningún kanban_tareas con id_incidencia apuntando a una incidencia
    inexistente. Si falla, algún test integrador no está limpiando."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval("""
                SELECT count(*) FROM kanban_tareas k
                WHERE k.id_incidencia IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM incidencias_run r WHERE r.ticket_id = k.id_incidencia
                  )
            """)
        finally:
            await c.close()
    n = _run(_go())
    assert n == 0, (
        f"{n} kanban_tareas huérfanas detectadas — algún test integrador "
        f"no está borrando sus kanban hijas en el cleanup. Ver C_recon.md "
        f"sec 2 + cleanup defensivo en test_deudaA_integrador.py:_cleanup."
    )


def test_no_agent_conversations_fantasma():
    """Toda agent_conversations.ticket_id NOT NULL debe existir en
    incidencias_run. Mismo principio que test_arq02_f5::test_ningun_ticket_id_fantasma
    pero re-evaluado tras el cleanup C.2."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval("""
                SELECT count(*) FROM agent_conversations ac
                WHERE ac.ticket_id IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM incidencias_run r WHERE r.ticket_id = ac.ticket_id
                  )
            """)
        finally:
            await c.close()
    n = _run(_go())
    assert n == 0, (
        f"{n} agent_conversations con ticket_id fantasma — algún test "
        f"integrador no está borrando sus conversations en el cleanup."
    )

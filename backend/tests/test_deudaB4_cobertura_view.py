"""
Deuda B.4 — F-ARQ02-13: tests para la vista agent_conversations_cobertura
que excluye las 56 filas con menciones legacy huérfanas pre-F1.

Cubre:
1. La vista existe y es seleccionable
2. La vista excluye exactamente 56 filas (las huérfanas legacy)
3. La vista NO excluye filas con ticket_id poblado (las 126 sobreviven)

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


def test_view_existe():
    """1. La vista agent_conversations_cobertura existe y es seleccionable."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval(
                "SELECT 1 FROM agent_conversations_cobertura LIMIT 1"
            )
        finally:
            await c.close()
    assert _run(_go()) == 1


def test_view_excluye_56_huerfanos():
    """2. La diferencia tabla−vista debe ser exactamente 56 filas."""
    async def _go():
        c = await _conn()
        try:
            n_tabla = await c.fetchval("SELECT count(*) FROM agent_conversations")
            n_view = await c.fetchval("SELECT count(*) FROM agent_conversations_cobertura")
            return n_tabla, n_view
        finally:
            await c.close()
    n_tabla, n_view = _run(_go())
    diff = n_tabla - n_view
    assert diff == 56, (
        f"vista no excluye exactamente 56 huérfanos: tabla={n_tabla} "
        f"view={n_view} diff={diff}"
    )


def test_view_no_excluye_pobladas():
    """3. Las filas con ticket_id NOT NULL siguen visibles en la vista."""
    async def _go():
        c = await _conn()
        try:
            n_tabla = await c.fetchval(
                "SELECT count(*) FROM agent_conversations WHERE ticket_id IS NOT NULL"
            )
            n_view = await c.fetchval(
                "SELECT count(*) FROM agent_conversations_cobertura WHERE ticket_id IS NOT NULL"
            )
            return n_tabla, n_view
        finally:
            await c.close()
    n_tabla, n_view = _run(_go())
    assert n_tabla == n_view, (
        f"vista perdió filas pobladas: tabla={n_tabla} view={n_view}"
    )

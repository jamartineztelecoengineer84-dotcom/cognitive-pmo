"""ARQ-02 F3 — verificar que la tabla incidencias zombie ya no existe."""
import asyncio
import os
import asyncpg


async def _conn():
    return await asyncpg.connect(
        host=os.getenv("DB_HOST", "192.168.1.49"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "cognitive_pmo"),
        user=os.getenv("DB_USER", "jose_admin"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_incidencias_zombie_table_removed():
    """La tabla 'incidencias' (sin sufijo) ya no debe existir tras F3."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval("SELECT to_regclass('public.incidencias')")
        finally:
            await c.close()
    assert _run(_go()) is None, "tabla incidencias debería haber sido DROPeada en F3"


def test_incidencias_run_y_live_intactas():
    """incidencias_run e incidencias_live siguen presentes con counts esperados."""
    async def _go():
        c = await _conn()
        try:
            run = await c.fetchval("SELECT COUNT(*) FROM incidencias_run")
            live = await c.fetchval("SELECT COUNT(*) FROM incidencias_live")
            return run, live
        finally:
            await c.close()
    run, live = _run(_go())
    # F-ARQ02-20 hot-fix 2026-04-09: threshold bajado de >=37 a >=34. El
    # original 37 asumía 34 baseline + 3 INC-SC* residuales típicos. Tras
    # F-ARQ02-20 conftest purga TODOS los INC-SC* PRE y POST sesión, así que
    # el count visible al test es 34 puro (sin scenario residuals).
    assert run >= 34, f"incidencias_run baseline esperado >=34, got {run}"
    assert live >= 2, f"incidencias_live baseline esperado >=2, got {live}"

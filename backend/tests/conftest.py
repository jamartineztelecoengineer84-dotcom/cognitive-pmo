"""Session-scope fixtures for pytest suite."""
import asyncio
import os
import asyncpg
import pytest


DB_HOST = os.getenv("DB_HOST", "192.168.1.49")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "cognitive_pmo")
DB_USER = os.getenv("DB_USER", "jose_admin")
DB_PASS = os.getenv("DB_PASSWORD", "")


@pytest.fixture(scope="session", autouse=True)
def _purge_scenario_residuals_at_session_start():
    """F-ARQ02-19 2026-04-09: limpia PRJ-SC* residuales de build_live al inicio
    de cada sesión pytest. Los tests scenario (seed_scenario_overload/optimal/
    half) insertan filas con id_proyecto LIKE 'PRJ-SC%' que persisten entre
    sesiones porque v_p96_build_portfolio no filtra. Sin esto,
    test_p96_router::test_build_portfolio ve count 100 en lugar de 60 cuando
    una sesión previa ejecutó tests scenario.

    Scope session = corre una sola vez al arrancar pytest, antes de cualquier
    test. No toca tests individuales ni requiere teardown.
    """
    async def _purge():
        c = await asyncpg.connect(
            host=DB_HOST, port=DB_PORT, database=DB_NAME,
            user=DB_USER, password=DB_PASS,
        )
        try:
            await c.execute("DELETE FROM build_live WHERE id_proyecto LIKE 'PRJ-SC%'")
        finally:
            await c.close()
    asyncio.get_event_loop().run_until_complete(_purge())
    yield

"""Session-scope fixtures for pytest suite."""
import asyncio
import os
import asyncpg
import pytest

from scenario_engine import reset_scenario


DB_HOST = os.getenv("DB_HOST", "192.168.1.49")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "cognitive_pmo")
DB_USER = os.getenv("DB_USER", "jose_admin")
DB_PASS = os.getenv("DB_PASSWORD", "")


@pytest.fixture(scope="session", autouse=True)
def _purge_sc_piloto0_at_session_start_and_end():
    """ARQ-03 F4: limpia sc_piloto0 (esquema de test) PRE y POST sesión.

    Sustituye al purge F-ARQ02-19/20 basado en prefijos SC% sobre primitiva.
    Ahora que los escenarios son esquemas reales (ARQ-03 F1-F3), la limpieza
    es un DROP SCHEMA CASCADE + recreación vacía vía
    compartido.crear_esquema_escenario, mucho más rápido y atómico.

    primitiva NUNCA se toca: el motor refactorizado raise ValueError si se
    le pide reset sobre primitiva.

    PRE: garantiza que sc_piloto0 existe y está vacío para los tests scenario.
    POST: deja sc_piloto0 vacío al cerrar pytest (UI de Jose limpia).
    """
    async def _purge():
        c = await asyncpg.connect(
            host=DB_HOST, port=DB_PORT, database=DB_NAME,
            user=DB_USER, password=DB_PASS,
        )
        try:
            await reset_scenario(c, "sc_piloto0")
        finally:
            await c.close()

    asyncio.get_event_loop().run_until_complete(_purge())
    yield
    asyncio.get_event_loop().run_until_complete(_purge())

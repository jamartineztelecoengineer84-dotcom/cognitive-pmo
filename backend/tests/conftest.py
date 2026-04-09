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
def _purge_scenario_residuals_at_session_start_and_end():
    """F-ARQ02-19 + F-ARQ02-20 2026-04-09: limpia TODOS los residuales
    scenario (PRJ-SC*, KAN-SC*, INC-SC*) PRE y POST sesión pytest.

    PRE: estado determinista para tests que consultan counts (test_p96_*).
    POST: UI real de Jose queda limpia al cerrar pytest (sin KAN-SC*
    visibles en /kanban, sin PRJ-SC* en /build, sin INC-SC* en /itsm).

    Cobertura: reusa scenario_engine.reset_scenario() que cubre 10 tablas:
    - incidencias_run (CASCADE → incidencias_live vía F2.1)
    - kanban_tareas
    - 8 build_* (build_sprint_items, build_sprints, build_quality_gates,
      build_stakeholders, build_risks, build_subtasks, build_project_plans,
      build_live)

    Causa raíz F-ARQ02-20: el fixture original solo corría PRE y solo
    purgaba build_live. Los tests scenario (test_scenario_engine,
    test_scenario_e2e) repoblaban TODAS las tablas SC dentro de la sesión
    y dejaban 180 filas residuales visibles al usuario al cerrar pytest.
    Fix: yield con _purge() pre y post + cobertura ampliada vía
    reset_scenario() canónico.
    """
    async def _purge():
        c = await asyncpg.connect(
            host=DB_HOST, port=DB_PORT, database=DB_NAME,
            user=DB_USER, password=DB_PASS,
        )
        try:
            await reset_scenario(c)
        finally:
            await c.close()

    asyncio.get_event_loop().run_until_complete(_purge())
    yield
    asyncio.get_event_loop().run_until_complete(_purge())

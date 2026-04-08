"""
ARQ-01 F4.1 — tests del scenario engine.

Verifica los invariantes I1-I6 sobre el motor en BD real (mismo enfoque que
test_p96_router.py: usa el contenedor api con asyncpg directo).

Ejecutar:
  docker compose exec api python -m pytest tests/test_scenario_engine.py -v
"""
import asyncio
import os
import pytest
import asyncpg

from scenario_engine import (
    _assert_guard,
    seed_scenario_optimal,
    seed_scenario_empty,
)


# ── Invariantes puros (sin BD) ────────────────────────────────────────
def test_i1_guard_rejects_legacy():
    with pytest.raises(AssertionError):
        _assert_guard("PRJ-MSF001")


def test_i1_guard_accepts_scenario():
    _assert_guard("PRJ-SCA001")
    _assert_guard("PRJ-SCD010")


def test_i1_guard_rejects_other_prefixes():
    for bad in ("PRJ0004", "PRJ-IAF005", "PRJ-XYZ001", "KAN-SC0001"):
        with pytest.raises(AssertionError):
            _assert_guard(bad)


# ── Invariantes con BD real ───────────────────────────────────────────
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


@pytest.fixture(scope="module")
def baseline_counts():
    """Snapshot de counts legacy ANTES de cualquier seed."""
    async def _snap():
        c = await _conn()
        try:
            return {
                "cartera_build": await c.fetchval("SELECT COUNT(*) FROM cartera_build"),
                "build_live_legacy": await c.fetchval(
                    "SELECT COUNT(*) FROM build_live WHERE id_proyecto !~ '^PRJ-SC[A-D][0-9]+$'"
                ),
                "build_subtasks_legacy": await c.fetchval(
                    "SELECT COUNT(*) FROM build_subtasks WHERE id_proyecto !~ '^PRJ-SC[A-D][0-9]+$'"
                ),
                "build_risks_legacy": await c.fetchval(
                    "SELECT COUNT(*) FROM build_risks WHERE id_proyecto !~ '^PRJ-SC[A-D][0-9]+$'"
                ),
                "kanban_legacy": await c.fetchval(
                    "SELECT COUNT(*) FROM kanban_tareas WHERE id NOT LIKE 'KAN-SC%'"
                ),
                "inc_run_legacy": await c.fetchval(
                    "SELECT COUNT(*) FROM incidencias_run WHERE ticket_id NOT LIKE 'INC-SC%'"
                ),
            }
        finally:
            await c.close()
    return _run(_snap())


def test_seed_optimal_inserts_expected_counts(baseline_counts):
    async def _go():
        c = await _conn()
        try:
            await seed_scenario_optimal(c)
            n_proj = await c.fetchval(
                "SELECT COUNT(*) FROM build_live WHERE id_proyecto ~ '^PRJ-SC[A-D][0-9]+$'"
            )
            n_kan = await c.fetchval(
                "SELECT COUNT(*) FROM kanban_tareas WHERE id LIKE 'KAN-SC%'"
            )
            n_inc = await c.fetchval(
                "SELECT COUNT(*) FROM incidencias_run WHERE ticket_id LIKE 'INC-SC%'"
            )
            return n_proj, n_kan, n_inc
        finally:
            await c.close()
    n_proj, n_kan, n_inc = _run(_go())
    assert n_proj == 40
    assert n_kan == 120
    assert n_inc == 12


def test_i5_cartera_build_unchanged(baseline_counts):
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval("SELECT COUNT(*) FROM cartera_build")
        finally:
            await c.close()
    assert _run(_go()) == baseline_counts["cartera_build"]


def test_i4_legacy_build_live_unchanged(baseline_counts):
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval(
                "SELECT COUNT(*) FROM build_live WHERE id_proyecto !~ '^PRJ-SC[A-D][0-9]+$'"
            )
        finally:
            await c.close()
    assert _run(_go()) == baseline_counts["build_live_legacy"]


def test_i3_legacy_kanban_unchanged(baseline_counts):
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval(
                "SELECT COUNT(*) FROM kanban_tareas WHERE id NOT LIKE 'KAN-SC%'"
            )
        finally:
            await c.close()
    assert _run(_go()) == baseline_counts["kanban_legacy"]


def test_idempotency_two_seeds_same_count():
    """Llamar seed_scenario_optimal 2 veces debe dejar exactamente los mismos
    counts (40/120/12). El reset_scenario interno borra antes de re-insertar."""
    async def _go():
        c = await _conn()
        try:
            await seed_scenario_optimal(c)
            n1 = await c.fetchval(
                "SELECT COUNT(*) FROM build_live WHERE id_proyecto ~ '^PRJ-SC[A-D][0-9]+$'"
            )
            await seed_scenario_optimal(c)
            n2 = await c.fetchval(
                "SELECT COUNT(*) FROM build_live WHERE id_proyecto ~ '^PRJ-SC[A-D][0-9]+$'"
            )
            return n1, n2
        finally:
            await c.close()
    n1, n2 = _run(_go())
    assert n1 == n2 == 40


def test_seed_empty_clears_scenario():
    """seed_scenario_empty deja 0 filas scenario en build_live/kanban/inc."""
    async def _go():
        c = await _conn()
        try:
            await seed_scenario_optimal(c)  # ensure something exists
            await seed_scenario_empty(c)
            return (
                await c.fetchval(
                    "SELECT COUNT(*) FROM build_live WHERE id_proyecto ~ '^PRJ-SC[A-D][0-9]+$'"
                ),
                await c.fetchval(
                    "SELECT COUNT(*) FROM kanban_tareas WHERE id LIKE 'KAN-SC%'"
                ),
                await c.fetchval(
                    "SELECT COUNT(*) FROM incidencias_run WHERE ticket_id LIKE 'INC-SC%'"
                ),
            )
        finally:
            await c.close()
    n_proj, n_kan, n_inc = _run(_go())
    assert n_proj == 0 and n_kan == 0 and n_inc == 0

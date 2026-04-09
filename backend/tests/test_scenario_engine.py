"""ARQ-03 F4 — tests del scenario engine refactorizado.

Verifica seed_scenario(conn, scenario, profile) y reset_scenario(conn,
scenario) operando sobre sc_piloto0 (esquema test). primitiva NUNCA se
toca; cualquier intento de escribir en primitiva debe raise ValueError.

El conftest session-scope ya hace DROP+recrea sc_piloto0 PRE/POST sesión.
Cada test individual también puede llamar reset_scenario para partir de
estado vacío.

Ejecutar:
  docker compose exec api python -m pytest tests/test_scenario_engine.py -v
"""
import asyncio
import os
import pytest
import asyncpg

from scenario_engine import (
    seed_scenario,
    reset_scenario,
    PROFILE_COUNTS,
    PROFILES,
    PRIMITIVA,
    _validate,
    _pick_least_loaded_tecnicos,
)


# ── Validación pura (sin BD) ──────────────────────────────────────────
def test_validate_rechaza_primitiva():
    with pytest.raises(ValueError, match="canon inmutable"):
        _validate("primitiva", "optimal")


def test_validate_rechaza_scenario_invalido():
    with pytest.raises(ValueError, match="scenario_name inválido"):
        _validate("sc_hackeame", "optimal")


def test_validate_rechaza_profile_invalido():
    with pytest.raises(ValueError, match="profile inválido"):
        _validate("sc_piloto0", "ultra")


def test_validate_acepta_combo_valido():
    _validate("sc_piloto0", "optimal")
    _validate("sc_iberico", "half")


def test_profile_counts_completos():
    assert set(PROFILE_COUNTS.keys()) == PROFILES
    assert PROFILE_COUNTS["empty"]    == (0,  0,   0)
    assert PROFILE_COUNTS["half"]     == (20, 60,  8)
    assert PROFILE_COUNTS["optimal"]  == (40, 120, 12)
    assert PROFILE_COUNTS["overload"] == (40, 160, 22)


# ── Tests con BD real ─────────────────────────────────────────────────
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


async def _counts_in_schema(conn, schema: str):
    """Devuelve (n_proj, n_kan, n_inc) directamente del esquema dado."""
    return (
        await conn.fetchval(f"SELECT COUNT(*) FROM {schema}.build_live"),
        await conn.fetchval(f"SELECT COUNT(*) FROM {schema}.kanban_tareas"),
        await conn.fetchval(f"SELECT COUNT(*) FROM {schema}.incidencias_run"),
    )


def test_reset_scenario_rechaza_primitiva():
    async def _go():
        c = await _conn()
        try:
            with pytest.raises(ValueError, match="canon inmutable"):
                await reset_scenario(c, "primitiva")
        finally:
            await c.close()
    _run(_go())


def test_seed_scenario_rechaza_primitiva():
    async def _go():
        c = await _conn()
        try:
            with pytest.raises(ValueError, match="canon inmutable"):
                await seed_scenario(c, "primitiva", "optimal")
        finally:
            await c.close()
    _run(_go())


def test_seed_optimal_counts():
    """OPTIMAL: 40 build_live, 120 kanban, 12 incidencias en sc_piloto0."""
    async def _go():
        c = await _conn()
        try:
            await reset_scenario(c, "sc_piloto0")
            result = await seed_scenario(c, "sc_piloto0", "optimal")
            counts = await _counts_in_schema(c, "sc_piloto0")
            return result, counts
        finally:
            await c.close()
    result, (n_proj, n_kan, n_inc) = _run(_go())
    assert result["scenario"] == "sc_piloto0"
    assert result["profile"] == "optimal"
    assert (n_proj, n_kan, n_inc) == (40, 120, 12)


def test_seed_half_counts():
    """HALF: 20 build_live, 60 kanban, 8 incidencias."""
    async def _go():
        c = await _conn()
        try:
            await reset_scenario(c, "sc_piloto0")
            await seed_scenario(c, "sc_piloto0", "half")
            return await _counts_in_schema(c, "sc_piloto0")
        finally:
            await c.close()
    assert _run(_go()) == (20, 60, 8)


def test_seed_overload_counts_y_escalados():
    """OVERLOAD: 40 build_live, 160 kanban, 22 incidencias (3 ESCALADO)."""
    async def _go():
        c = await _conn()
        try:
            await reset_scenario(c, "sc_piloto0")
            await seed_scenario(c, "sc_piloto0", "overload")
            await c.execute("SET search_path = sc_piloto0, compartido, public")
            n_proj = await c.fetchval("SELECT COUNT(*) FROM build_live")
            n_kan = await c.fetchval("SELECT COUNT(*) FROM kanban_tareas")
            n_inc = await c.fetchval("SELECT COUNT(*) FROM incidencias_run")
            n_escalados = await c.fetchval(
                "SELECT COUNT(*) FROM incidencias_run WHERE estado='ESCALADO'"
            )
            return n_proj, n_kan, n_inc, n_escalados
        finally:
            await c.close()
    proj, kan, inc, escalados = _run(_go())
    assert (proj, kan, inc) == (40, 160, 22)
    assert escalados == 3


def test_seed_empty_deja_esquema_vacio():
    """EMPTY: tras un seed previo, llamar EMPTY deja todo a 0."""
    async def _go():
        c = await _conn()
        try:
            await reset_scenario(c, "sc_piloto0")
            await seed_scenario(c, "sc_piloto0", "optimal")
            await seed_scenario(c, "sc_piloto0", "empty")
            return await _counts_in_schema(c, "sc_piloto0")
        finally:
            await c.close()
    assert _run(_go()) == (0, 0, 0)


def test_idempotencia_dos_seeds_iguales():
    """Llamar seed_scenario(optimal) 2 veces deja los mismos counts."""
    async def _go():
        c = await _conn()
        try:
            await reset_scenario(c, "sc_piloto0")
            await seed_scenario(c, "sc_piloto0", "optimal")
            n1 = await _counts_in_schema(c, "sc_piloto0")
            await seed_scenario(c, "sc_piloto0", "optimal")
            n2 = await _counts_in_schema(c, "sc_piloto0")
            return n1, n2
        finally:
            await c.close()
    n1, n2 = _run(_go())
    assert n1 == n2 == (40, 120, 12)


def test_aislamiento_primitiva_no_se_toca():
    """Tras seedear sc_piloto0, los counts de primitiva no cambian."""
    async def _go():
        c = await _conn()
        try:
            # Snapshot pre-seed de primitiva
            await c.execute("SET search_path = primitiva, compartido, public")
            pre = (
                await c.fetchval("SELECT COUNT(*) FROM build_live"),
                await c.fetchval("SELECT COUNT(*) FROM kanban_tareas"),
                await c.fetchval("SELECT COUNT(*) FROM incidencias_run"),
            )
            await reset_scenario(c, "sc_piloto0")
            await seed_scenario(c, "sc_piloto0", "overload")
            # Snapshot post-seed
            await c.execute("SET search_path = primitiva, compartido, public")
            post = (
                await c.fetchval("SELECT COUNT(*) FROM build_live"),
                await c.fetchval("SELECT COUNT(*) FROM kanban_tareas"),
                await c.fetchval("SELECT COUNT(*) FROM incidencias_run"),
            )
            return pre, post
        finally:
            await c.close()
    pre, post = _run(_go())
    assert pre == post, f"primitiva contaminada: {pre} → {post}"


def test_pick_least_loaded_devuelve_n_exactos():
    """_pick_least_loaded_tecnicos en sc_piloto0 vacío devuelve n filas."""
    async def _go():
        c = await _conn()
        try:
            await reset_scenario(c, "sc_piloto0")
            await c.execute("SET search_path = sc_piloto0, compartido, public")
            techs = await _pick_least_loaded_tecnicos(c, 50)
            return len(techs)
        finally:
            await c.close()
    assert _run(_go()) == 50

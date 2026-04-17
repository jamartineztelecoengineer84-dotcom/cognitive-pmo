"""ARQ-03 F4 — E2E del endpoint POST /api/admin/seed-scenario refactorizado.

Body nuevo: {scenario, profile} (sin scenario_id).
Verifica:
  - admin OK con sc_piloto0 + perfil OPTIMAL → 40/120/12
  - admin con perfil EMPTY → 0/0/0
  - PM (no admin) → 403
  - admin intentando seedear primitiva → 400 (raise ValueError mapeado)
  - aislamiento: tras seedear sc_piloto0, primitiva no cambia
"""
import asyncio
import os
import asyncpg
import httpx

API_URL     = "http://localhost:8088"
ADMIN_EMAIL = "admin"
ADMIN_PASS  = "admin"
PM_EMAIL    = "pablo.rivas@cognitive-pmo.es"   # PM-016 (id_usuario=19)
PM_PASS     = "12345"

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "cognitive_pmo")
DB_USER = os.getenv("DB_USER", "jose_admin")
DB_PASS = os.getenv("DB_PASSWORD", "")


def _login(email, password):
    r = httpx.post(f"{API_URL}/auth/login",
                   json={"email": email, "password": password},
                   timeout=10)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()["token"]


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _conn():
    return await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASS,
    )


def test_e2e_seed_optimal_sc_piloto0():
    """Admin POST {sc_piloto0, optimal} → 40/120/12 en sc_piloto0."""
    token = _login(ADMIN_EMAIL, ADMIN_PASS)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Scenario": "sc_piloto0",
    }
    r = httpx.post(
        f"{API_URL}/api/admin/seed-scenario",
        json={"scenario": "sc_piloto0", "profile": "optimal"},
        headers=headers,
        timeout=60,
    )
    assert r.status_code == 200, f"seed: {r.status_code} {r.text}"
    body = r.json()
    assert body["scenario"] == "sc_piloto0"
    assert body["profile"] == "optimal"
    assert body["counts_post"]["build_live"] == 40
    assert body["counts_post"]["kanban_tareas"] == 120
    assert body["counts_post"]["incidencias_run"] == 12


def test_e2e_seed_empty_resetea_sc_piloto0():
    """Admin POST {sc_piloto0, empty} → 0/0/0."""
    token = _login(ADMIN_EMAIL, ADMIN_PASS)
    headers = {"Authorization": f"Bearer {token}", "X-Scenario": "sc_piloto0"}
    r = httpx.post(
        f"{API_URL}/api/admin/seed-scenario",
        json={"scenario": "sc_piloto0", "profile": "empty"},
        headers=headers,
        timeout=30,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["counts_post"] == {
        "build_live": 0, "kanban_tareas": 0, "incidencias_run": 0
    }


def test_e2e_seed_primitiva_rechazado():
    """Admin POST {primitiva, optimal} → 400 (ValueError mapeado)."""
    token = _login(ADMIN_EMAIL, ADMIN_PASS)
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.post(
        f"{API_URL}/api/admin/seed-scenario",
        json={"scenario": "primitiva", "profile": "optimal"},
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 400
    assert "primitiva" in r.json()["detail"].lower()


def test_e2e_aislamiento_primitiva_intacta():
    """Tras seedear sc_piloto0, primitiva no cambia."""
    async def _snapshot_primitiva():
        c = await _conn()
        try:
            await c.execute("SET LOCAL search_path = primitiva, compartido, public")
            return (
                await c.fetchval("SELECT COUNT(*) FROM build_live"),
                await c.fetchval("SELECT COUNT(*) FROM kanban_tareas"),
                await c.fetchval("SELECT COUNT(*) FROM incidencias_run"),
            )
        finally:
            await c.close()

    pre = _run(_snapshot_primitiva())

    token = _login(ADMIN_EMAIL, ADMIN_PASS)
    headers = {"Authorization": f"Bearer {token}", "X-Scenario": "sc_piloto0"}
    r = httpx.post(
        f"{API_URL}/api/admin/seed-scenario",
        json={"scenario": "sc_piloto0", "profile": "overload"},
        headers=headers,
        timeout=60,
    )
    assert r.status_code == 200

    post = _run(_snapshot_primitiva())
    assert pre == post, f"primitiva contaminada: {pre} → {post}"


def test_e2e_seed_scenario_403():
    """PM (no admin) no puede llamar al endpoint."""
    pm_token = _login(PM_EMAIL, PM_PASS)
    r = httpx.post(
        f"{API_URL}/api/admin/seed-scenario",
        json={"scenario": "sc_piloto0", "profile": "empty"},
        headers={"Authorization": f"Bearer {pm_token}"},
        timeout=10,
    )
    assert r.status_code == 403, f"esperaba 403, got {r.status_code} {r.text}"

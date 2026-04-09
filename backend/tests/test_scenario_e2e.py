"""
ARQ-01 F4.3 — E2E del endpoint POST /api/admin/seed-scenario.
Verifica los 7 checks del plan v2 + check 403.

Mismo estilo que test_scenario_engine.py: asyncio + asyncpg + httpx con
cliente sync para los hits HTTP locales al api del propio contenedor.
"""
import asyncio
import os
import asyncpg
import httpx

API_URL     = "http://localhost:8088"
ADMIN_EMAIL = "admin"
ADMIN_PASS  = "admin"
PM_EMAIL    = "pablo.rivas@cognitivepmo.com"   # PM-016 (id_usuario=19)
PM_PASS     = "12345"

DB_HOST = os.getenv("DB_HOST", "192.168.1.49")
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


def test_e2e_seed_scenario():
    """E2E completo: 7 checks contra POST /api/admin/seed-scenario."""
    admin_token = _login(ADMIN_EMAIL, ADMIN_PASS)
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # CHECK 1 — POST seed OPTIMAL con reset
    r = httpx.post(
        f"{API_URL}/api/admin/seed-scenario",
        json={"scenario_id": 2, "reset": True},
        headers=headers_admin,
        timeout=30,
    )
    assert r.status_code == 200, f"CHECK1 fail: {r.status_code} {r.text}"
    body = r.json()
    assert body["scenario"] == "OPTIMAL"
    print("CHECK1 OK", body["counts"])

    async def _db_checks():
        c = await _conn()
        try:
            # CHECK 2 — 40 PRJ-SC en build_live
            n_proj = await c.fetchval(
                "SELECT COUNT(*) FROM build_live WHERE id_proyecto ~ '^PRJ-SC[A-D]'"
            )
            assert n_proj == 40, f"CHECK2 fail: {n_proj}"
            print("CHECK2 OK")

            # CHECK 3 — 120 KAN-SC
            n_kan = await c.fetchval(
                "SELECT COUNT(*) FROM kanban_tareas WHERE id LIKE 'KAN-SC%'"
            )
            assert n_kan == 120, f"CHECK3 fail: {n_kan}"
            print("CHECK3 OK")

            # CHECK 4 — legacy build_live intacto (PRJ-MSF sigue existiendo)
            n_msf = await c.fetchval(
                "SELECT COUNT(*) FROM build_live WHERE id_proyecto = 'PRJ-MSF'"
            )
            assert n_msf == 1, f"CHECK4 fail: PRJ-MSF = {n_msf}"
            print("CHECK4 OK")

            # CHECK 5 — cartera_build = 46
            n_cb = await c.fetchval("SELECT COUNT(*) FROM cartera_build")
            assert n_cb == 46, f"CHECK5 fail: {n_cb}"
            print("CHECK5 OK")
        finally:
            await c.close()
    _run(_db_checks())

    # CHECK 6 — login PM nuevo + my-projects + my-resources
    pm_token = _login(PM_EMAIL, PM_PASS)
    headers_pm = {"Authorization": f"Bearer {pm_token}"}

    r = httpx.get(f"{API_URL}/api/pm/my-projects", headers=headers_pm, timeout=10)
    assert r.status_code == 200
    proj = r.json()
    # Pablo Rivas (id_usuario=19) tiene 8 proyectos legacy de P98 F2 +
    # 4 scenario (40 PRJ-SC repartidos entre 10 PMs en round-robin) = 12 totales.
    # Los invariantes I3/I4 garantizan que la legacy queda intacta.
    n_scenario = sum(1 for p in proj if p["id_proyecto"].startswith("PRJ-SC"))
    n_legacy   = len(proj) - n_scenario
    assert len(proj) == 12, f"CHECK6a fail: {len(proj)} proyectos (esperaba 12 = 8 legacy + 4 scenario)"
    assert n_scenario == 4, f"CHECK6a fail: {n_scenario} scenario (esperaba 4)"
    assert n_legacy == 8, f"CHECK6a fail: {n_legacy} legacy (esperaba 8)"
    print(f"CHECK6a OK ({n_legacy} legacy + {n_scenario} scenario = {len(proj)} total)")

    r = httpx.get(f"{API_URL}/api/pm/my-resources", headers=headers_pm, timeout=10)
    assert r.status_code == 200
    humans = r.json().get("humans", [])
    assert len(humans) > 0, "CHECK6b fail: humans vacío"
    assert all("pct_capacidad" in h for h in humans)
    print(f"CHECK6b OK ({len(humans)} humans)")

    # CHECK 7 — POST seed EMPTY → todo a 0 scenario, legacy intacto
    r = httpx.post(
        f"{API_URL}/api/admin/seed-scenario",
        json={"scenario_id": 0, "reset": True},
        headers=headers_admin,
        timeout=30,
    )
    assert r.status_code == 200
    b = r.json()
    c2 = b["counts"]
    assert c2["build_live_scenario"] == 0
    assert c2["kanban_scenario"] == 0
    assert c2["build_live_legacy"] == 60
    # F-ARQ02-06 C.2 cleanup 2026-04-09: kanban_legacy bajó de 341 original a
    # 332 tras purgar 35 huérfanas + 18 hijas de 4 incidencias residuales.
    # Baseline 341 irreproducible (3 filas del snapshot original ya no existen).
    assert c2["kanban_legacy"] == 332
    assert c2["cartera_build"] == 46
    print("CHECK7 OK", c2)

    print("E2E 7/7 GREEN")


def test_e2e_seed_scenario_403():
    """PMO_SENIOR no puede llamar al endpoint admin."""
    pm_token = _login(PM_EMAIL, PM_PASS)
    r = httpx.post(
        f"{API_URL}/api/admin/seed-scenario",
        json={"scenario_id": 0, "reset": True},
        headers={"Authorization": f"Bearer {pm_token}"},
        timeout=10,
    )
    assert r.status_code == 403, f"esperaba 403, got {r.status_code} {r.text}"
    print("CHECK 403 OK")

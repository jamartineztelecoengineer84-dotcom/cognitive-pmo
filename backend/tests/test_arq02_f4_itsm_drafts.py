"""
ARQ-02 F4 — verificar el rename run_incident_plans → itsm_form_drafts.

Tests:
  1. Tabla renombrada (old NULL, new exists)
  2. Índices renombrados (itsm_form_drafts_pkey + idx_itsm_drafts_ticket)
  3. Endpoint GET /run/plans devuelve filas (mantiene contrato API)
  4. Endpoint POST /run/plans crea draft (mantiene contrato)
  5. Endpoint DELETE /run/plans/{id} borra draft (mantiene contrato)
  6. Cleanup drift aplicado: 0 filas con patrón RUN-YYYYMMDD-HEX residual
"""
import asyncio
import os
import asyncpg
import httpx


API_URL = "http://localhost:8088"

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


def test_table_renamed():
    """Tabla run_incident_plans no existe; itsm_form_drafts sí."""
    async def _go():
        c = await _conn()
        try:
            old = await c.fetchval("SELECT to_regclass('public.run_incident_plans')")
            new = await c.fetchval("SELECT to_regclass('primitiva.itsm_form_drafts')")
            return old, new
        finally:
            await c.close()
    old, new = _run(_go())
    assert old is None, f"run_incident_plans aún existe: {old}"
    assert new is not None, "itsm_form_drafts no existe"


def test_indexes_renamed():
    """Los 2 índices llevan el nombre nuevo coherente con la tabla."""
    async def _go():
        c = await _conn()
        try:
            rows = await c.fetch(
                "SELECT indexname FROM pg_indexes WHERE tablename='itsm_form_drafts' ORDER BY 1"
            )
            return [r["indexname"] for r in rows]
        finally:
            await c.close()
    names = _run(_go())
    assert "itsm_form_drafts_pkey" in names, f"PK no renombrada: {names}"
    assert "idx_itsm_drafts_ticket" in names, f"índice ticket no renombrado: {names}"


def test_count_after_cleanup():
    """Cleanup drift: tabla tiene 61 filas catálogo, 0 drift residual."""
    async def _go():
        c = await _conn()
        try:
            total = await c.fetchval("SELECT COUNT(*) FROM itsm_form_drafts")
            catalog = await c.fetchval(
                "SELECT COUNT(*) FROM itsm_form_drafts WHERE id LIKE 'RUN-CAT-%'"
            )
            drift = await c.fetchval(
                "SELECT COUNT(*) FROM itsm_form_drafts WHERE id ~ '^RUN-2026[0-9]{4}-[A-F0-9]{4}$'"
            )
            return total, catalog, drift
        finally:
            await c.close()
    total, catalog, drift = _run(_go())
    assert total >= 61, f"total={total} (esperado >=61)"
    assert catalog == 61, f"catalog={catalog} (esperado 61)"
    assert drift == 0, f"drift residual={drift} (esperado 0)"


def test_endpoint_get_run_plans_works():
    """GET /run/plans mantiene contrato y devuelve filas reales de la tabla renombrada."""
    r = httpx.get(f"{API_URL}/run/plans", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 61, f"esperado >=61 filas, got {len(data)}"


def test_endpoint_post_run_plans_works():
    """POST /run/plans crea un draft con id RUN-YYYYMMDD-HEX (limpieza al final)."""
    body = {
        "nombre": "F4 test draft - safe to delete",
        "prioridad": "P4",
        "area": "TEST",
        "sla_horas": 24.0,
        "plan_data": {"test": True},
    }
    r = httpx.post(f"{API_URL}/run/plans", json=body, timeout=10)
    assert r.status_code == 200, f"got {r.status_code} {r.text}"
    created = r.json()
    assert created["id"].startswith("RUN-"), f"id format unexpected: {created['id']}"
    assert created["nombre"] == "F4 test draft - safe to delete"
    # Cleanup
    r2 = httpx.delete(f"{API_URL}/run/plans/{created['id']}", timeout=10)
    assert r2.status_code == 200


def test_endpoint_delete_run_plans_works():
    """DELETE /run/plans/{id} con un id inexistente devuelve 404."""
    r = httpx.delete(f"{API_URL}/run/plans/RUN-FAKE-9999", timeout=10)
    assert r.status_code == 404

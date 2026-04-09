"""ARQ-03 F3 — tests del middleware X-Scenario + ContextVar + pool setup.

Verifica que:
1. Sin header → DEFAULT_SCENARIO ('primitiva')
2. Header explícito 'primitiva' → search_path empieza por primitiva
3. Header sc_iberico → search_path empieza por sc_iberico (aunque el
   esquema no exista, Postgres acepta esquemas inexistentes en el path)
4. Header inválido → HTTP 400
5. Header vacío → DEFAULT_SCENARIO
6. Pool reuse: 2º request sin arrastre del 1º
7. Concurrencia: cada request mantiene su escenario aislado
"""
import asyncio
import os
import httpx


API_URL = os.getenv("API_URL", "http://localhost:8088")


def _get(path: str, scenario: str | None = None):
    headers = {}
    if scenario is not None:
        headers["X-Scenario"] = scenario
    return httpx.get(f"{API_URL}{path}", headers=headers, timeout=10)


def test_sin_header_usa_primitiva():
    r = _get("/api/_debug/search_path")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["scenario_ctx"] == "primitiva"
    assert body["search_path"].startswith("primitiva"), body["search_path"]


def test_header_primitiva_explicito():
    r = _get("/api/_debug/search_path", scenario="primitiva")
    assert r.status_code == 200
    body = r.json()
    assert body["scenario_ctx"] == "primitiva"
    assert body["search_path"].startswith("primitiva")


def test_header_sc_iberico():
    r = _get("/api/_debug/search_path", scenario="sc_iberico")
    assert r.status_code == 200
    body = r.json()
    assert body["scenario_ctx"] == "sc_iberico"
    assert body["search_path"].startswith("sc_iberico"), body["search_path"]


def test_header_invalido_400():
    r = _get("/api/_debug/search_path", scenario="sc_hackeame")
    assert r.status_code == 400
    body = r.json()
    assert "X-Scenario inválido" in body["detail"]


def test_header_vacio_usa_default():
    r = _get("/api/_debug/search_path", scenario="")
    assert r.status_code == 200
    body = r.json()
    assert body["scenario_ctx"] == "primitiva"


def test_pool_reuse_no_contamina():
    """1er request con sc_iberico, 2º sin header → vuelve a primitiva."""
    r1 = _get("/api/_debug/search_path", scenario="sc_iberico")
    assert r1.status_code == 200
    assert r1.json()["search_path"].startswith("sc_iberico")

    r2 = _get("/api/_debug/search_path")
    assert r2.status_code == 200
    assert r2.json()["search_path"].startswith("primitiva"), (
        f"pool arrastró estado: {r2.json()['search_path']}"
    )


def test_aislamiento_contextvar_concurrencia():
    """10 requests concurrentes con escenarios mezclados → cada uno
    recibe el suyo sin contaminación."""
    scenarios = ["primitiva", "sc_iberico", "primitiva", "sc_iberico",
                 "primitiva", "sc_iberico", "primitiva", "sc_iberico",
                 "primitiva", "sc_iberico"]

    async def _go():
        async with httpx.AsyncClient(base_url=API_URL, timeout=15) as ac:
            tasks = [
                ac.get("/api/_debug/search_path", headers={"X-Scenario": s})
                for s in scenarios
            ]
            return await asyncio.gather(*tasks)

    responses = asyncio.get_event_loop().run_until_complete(_go())
    assert len(responses) == 10
    for resp, expected in zip(responses, scenarios):
        assert resp.status_code == 200
        body = resp.json()
        assert body["scenario_ctx"] == expected, (
            f"esperado {expected}, got {body['scenario_ctx']}"
        )
        assert body["search_path"].startswith(expected), (
            f"esperado SP empezando por {expected}, got {body['search_path']}"
        )

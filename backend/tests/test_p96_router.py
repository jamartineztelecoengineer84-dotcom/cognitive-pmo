"""
Tests P97 FASE 7 — Smoke + RBAC económico para /api/p96/* y /api/me.

Ejecutar:
  docker compose exec api python3 -m pytest tests/test_p96_router.py -v

Cobertura:
  A) /api/me con CEO, TECH_JUNIOR y sin token
  B) Smoke 200 + shape de los 14 endpoints /api/p96/*
  C) RBAC econ: CEO ve salarios, CIO no
"""
import json
import urllib.request
import urllib.error
import pytest

API = "http://localhost:8088"

CEO_EMAIL  = "alejandro.vidal@cognitivepmo.com"
CFO_EMAIL  = "francisco.herrera@cognitivepmo.com"   # ver_salario_ind=True
CIO_EMAIL  = "roberto.navarro@cognitivepmo.com"     # ver_salario_ind=False
TECH_EMAIL = "adriana.suarez@cognitivepmo.com"      # TECH_JUNIOR
PASS = "12345"


# ── helpers ────────────────────────────────────────────────────────────
def _login(email):
    req = urllib.request.Request(
        f"{API}/auth/login",
        data=json.dumps({"email": email, "password": PASS}).encode(),
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["token"]


def _get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{API}{path}", headers=headers)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body) if body else {}
        except Exception:
            return e.code, {}


# ── fixtures ───────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def ceo_token():
    return _login(CEO_EMAIL)

@pytest.fixture(scope="module")
def cfo_token():
    return _login(CFO_EMAIL)

@pytest.fixture(scope="module")
def cio_token():
    return _login(CIO_EMAIL)

@pytest.fixture(scope="module")
def tech_token():
    return _login(TECH_EMAIL)


# ── A) /api/me ─────────────────────────────────────────────────────────
def test_me_ceo(ceo_token):
    code, data = _get("/api/me", ceo_token)
    assert code == 200
    assert data["role_code"] == "CEO"
    assert data["p96_allowed"] is True
    assert data["scope_who"] == "TODOS"


def test_me_tech_junior(tech_token):
    code, data = _get("/api/me", tech_token)
    assert code == 200
    assert data["role_code"] == "TECH_JUNIOR"
    assert data["p96_allowed"] is False


def test_me_sin_token():
    code, _ = _get("/api/me")
    assert code in (401, 403)


# ── B) Smoke /api/p96/* (con CEO) ──────────────────────────────────────
def test_governors(ceo_token):
    code, data = _get("/api/p96/governors", ceo_token)
    assert code == 200
    assert isinstance(data, list)
    assert len(data) == 15


def test_run_matrix(ceo_token):
    code, data = _get("/api/p96/run/matrix", ceo_token)
    assert code == 200
    assert isinstance(data, list)
    # 8 layers × 4 crits = 32 filas
    assert len(data) == 32
    layers = {row["layer"] for row in data}
    crits = {row["crit"] for row in data}
    assert len(layers) == 8
    assert len(crits) == 4


def test_build_portfolio(ceo_token):
    code, data = _get("/api/p96/build/portfolio", ceo_token)
    assert code == 200
    assert isinstance(data, list)
    assert len(data) == 60
    sample = data[0]
    assert "cpi" in sample
    assert "spi" in sample


def test_pulse_kpis(ceo_token):
    code, data = _get("/api/p96/pulse/kpis", ceo_token)
    assert code == 200
    assert isinstance(data, list) and len(data) > 0


def test_pulse_alerts(ceo_token):
    code, data = _get("/api/p96/pulse/alerts", ceo_token)
    assert code == 200
    assert isinstance(data, list)


def test_pulse_blocks(ceo_token):
    code, data = _get("/api/p96/pulse/blocks", ceo_token)
    assert code == 200
    assert isinstance(data, list)


def test_pulse_decisions(ceo_token):
    code, data = _get("/api/p96/pulse/decisions", ceo_token)
    assert code == 200
    assert isinstance(data, list)


@pytest.mark.parametrize("k", ["dafo", "pestle", "porter", "okr"])
def test_strategy(ceo_token, k):
    code, data = _get(f"/api/p96/strategy/{k}", ceo_token)
    assert code == 200
    assert data is not None


# ── C) RBAC económico — CEO vs CIO ─────────────────────────────────────
def test_cfo_ve_salarios(cfo_token):
    """CFO debe poder ver salarios individuales (ver_salario_ind=True)."""
    code, data = _get("/api/me", cfo_token)
    assert code == 200
    assert data["role_code"] == "CFO"
    assert data["ver_salario_ind"] is True


def test_cio_no_ve_salarios(cio_token):
    """CIO NO debe ver salarios individuales (ver_salario_ind=False)."""
    code, data = _get("/api/me", cio_token)
    assert code == 200
    assert data["role_code"] == "CIO"
    assert data["ver_salario_ind"] is False

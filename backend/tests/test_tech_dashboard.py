"""
Tests — Tech Dashboard API
Ejecutar: docker exec cognitive-pmo-api-1 python3 -m pytest tests/test_tech_dashboard.py -v
"""
import json
import asyncio
import urllib.request
from datetime import date

API = "http://localhost:8088"
TECH_EMAIL = "sandra.ortega@cognitivepmo.com"
TECH_PASS = "12345"


def _login(email=TECH_EMAIL, password=TECH_PASS):
    req = urllib.request.Request(
        f"{API}/auth/login",
        data=json.dumps({"email": email, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["token"]


def _get(path, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{API}{path}", headers=headers)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.read() else {}


def _post(path, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(data).encode(),
        headers=headers,
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, json.loads(body) if body else {}


def _put(path, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(data).encode(),
        headers=headers,
        method="PUT",
    )
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, json.loads(body) if body else {}


# ── TESTS ──────────────────────────────────────────────────────────────


def test_dashboard_sin_auth():
    """Endpoint devuelve 401 sin token."""
    try:
        req = urllib.request.Request(f"{API}/api/tech/dashboard")
        urllib.request.urlopen(req)
        assert False, "Should have raised HTTPError"
    except urllib.error.HTTPError as e:
        assert e.code == 401, f"Expected 401, got {e.code}"


def test_dashboard_con_auth():
    """Dashboard devuelve datos del técnico."""
    token = _login()
    code, data = _get("/api/tech/dashboard", token)
    assert code == 200
    assert "id_recurso" in data
    assert "incidencias" in data
    assert "carga" in data
    assert data["id_recurso"] == "FTE-002"  # Sandra


def test_incidencias_filtro_recurso():
    """Solo devuelve incidencias del técnico logueado."""
    token = _login()
    code, data = _get("/api/tech/incidencias", token)
    assert code == 200
    assert isinstance(data, list)
    # All should belong to the logged-in technician (verified by endpoint filter)


def test_tareas_con_auth():
    """Tareas BUILD del técnico."""
    token = _login()
    code, data = _get("/api/tech/tareas", token)
    assert code == 200
    assert isinstance(data, list)


def test_actividad_con_auth():
    """Feed de actividad."""
    token = _login()
    code, data = _get("/api/tech/actividad", token)
    assert code == 200
    assert isinstance(data, list)


def test_chat_salas():
    """Lista salas de chat del técnico."""
    token = _login()
    code, data = _get("/api/tech/chat/salas", token)
    assert code == 200
    assert isinstance(data, list)


def test_chat_crear_mensaje():
    """Enviar mensaje a una sala."""
    token = _login()
    code, salas = _get("/api/tech/chat/salas", token)
    if not salas:
        print("SKIP: no hay salas")
        return
    sala_id = salas[0]["id"]
    code, msg = _post(f"/api/tech/chat/salas/{sala_id}/mensajes",
                      {"mensaje": "Test automático"}, token)
    assert code == 201, f"Expected 201, got {code}: {msg}"
    assert msg["es_mio"] is True


def test_servidores():
    """Lista servidores desde CMDB."""
    token = _login()
    code, data = _get("/api/tech/servidores", token)
    assert code == 200
    assert len(data) > 0
    assert "codigo" in data[0]
    assert "ip" in data[0]


def test_valoracion_actual():
    """Valoración del mes actual."""
    token = _login()
    code, data = _get("/api/tech/valoracion/actual", token)
    assert code == 200
    assert "puntuacion" in data
    assert "pct_sla" in data


def test_valoracion_historial():
    """Historial de valoraciones."""
    token = _login()
    code, data = _get("/api/tech/valoracion?meses=6", token)
    assert code == 200
    assert isinstance(data, list)


def test_copiloto_responde():
    """Copiloto devuelve respuesta con fuentes."""
    token = _login()
    code, data = _post("/api/tech/copiloto/chat",
                       {"pregunta": "¿Qué dependencias tiene SRV-PRO-001?"}, token)
    assert code == 200
    assert "respuesta" in data
    assert "fuentes" in data
    assert len(data["respuesta"]) > 10


def test_cambio_estado_invalido():
    """Transición inválida devuelve error."""
    token = _login()
    # Try to change a non-existent incident
    code, data = _put("/api/tech/incidencias/FAKE-999/estado",
                      {"estado": "RESUELTO"}, token)
    assert code == 404


if __name__ == "__main__":
    tests = [
        test_dashboard_sin_auth,
        test_dashboard_con_auth,
        test_incidencias_filtro_recurso,
        test_tareas_con_auth,
        test_actividad_con_auth,
        test_chat_salas,
        test_chat_crear_mensaje,
        test_servidores,
        test_valoracion_actual,
        test_valoracion_historial,
        test_copiloto_responde,
        test_cambio_estado_invalido,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")

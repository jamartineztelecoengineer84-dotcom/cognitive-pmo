"""
ARQ-02 Deuda A.1 — F-ARQ02-09: tests para SEQUENCE atómica itsm_draft_seq.

Verifica que:
1. La SEQUENCE existe en pg_sequences
2. La función generar_draft_id() devuelve formato RUN-NNNNNN-YYYYMMDD válido
3. Dos POST /run/plans consecutivos sin id devuelven 2 ids distintos atómicos

Patrón sync (_run + asyncpg.connect) consistente con el resto de tests del repo.
"""
import asyncio
import os
import re
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


def test_sequence_existe():
    """1. La SEQUENCE itsm_draft_seq existe en el schema."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval(
                "SELECT 1 FROM pg_sequences WHERE sequencename='itsm_draft_seq'"
            )
        finally:
            await c.close()
    assert _run(_go()) == 1, "SEQUENCE itsm_draft_seq no existe"


def test_funcion_genera_formato_valido():
    """2. generar_draft_id() devuelve string que cumple ^RUN-[0-9]{6}-[0-9]{8}$."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval("SELECT generar_draft_id()")
        finally:
            await c.close()
    draft_id = _run(_go())
    assert draft_id is not None, "generar_draft_id devolvió NULL"
    assert re.match(r'^RUN-[0-9]{6}-[0-9]{8}$', draft_id), \
        f"Formato inválido: {draft_id}"


def test_post_run_plans_genera_id_atomico():
    """3. Dos POST /run/plans sin id consecutivos devuelven ids distintos válidos
    con formato RUN-NNNNNN-YYYYMMDD. Cleanup al final."""
    body = {
        "nombre": "Deuda A.1 test draft (safe to delete)",
        "prioridad": "P4",
        "area": "TEST",
        "sla_horas": 24.0,
        "plan_data": {"test": "deudaA1"},
    }

    r1 = httpx.post(f"{API_URL}/run/plans", json=body, timeout=10)
    assert r1.status_code == 200, f"POST 1 fail: {r1.status_code} {r1.text}"
    id1 = r1.json()["id"]

    r2 = httpx.post(f"{API_URL}/run/plans", json=body, timeout=10)
    assert r2.status_code == 200, f"POST 2 fail: {r2.status_code} {r2.text}"
    id2 = r2.json()["id"]

    rgx = re.compile(r'^RUN-[0-9]{6}-[0-9]{8}$')
    assert rgx.match(id1), f"id1 formato inválido: {id1}"
    assert rgx.match(id2), f"id2 formato inválido: {id2}"
    assert id1 != id2, f"ids no son distintos: {id1} == {id2}"

    # Cleanup: borrar los 2 drafts creados
    httpx.delete(f"{API_URL}/run/plans/{id1}", timeout=10)
    httpx.delete(f"{API_URL}/run/plans/{id2}", timeout=10)

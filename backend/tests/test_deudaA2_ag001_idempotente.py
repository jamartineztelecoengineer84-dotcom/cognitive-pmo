"""
ARQ-02 Deuda A.2 — F-ARQ02-04: tests para create_incident idempotente
con pre_existing_ticket_id.

Cubre:
1. create_incident sin pre_existing_ticket_id → crea ticket nuevo (formato regex)
2. create_incident con pre_existing_ticket_id válido → devuelve fila existente
   con _idempotent=True, sin INSERT nuevo
3. create_incident con pre_existing_ticket_id inexistente → devuelve error
   con _idempotent=False, sin INSERT
4. CREATE_INCIDENT_SCHEMA tiene pre_existing_ticket_id en properties pero NO
   en required

Mismo patrón sync (_run + asyncpg.connect) que el resto de tests del repo.
"""
import asyncio
import os
import re
import asyncpg


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


# Import directo de la tool y el schema
from agents.tools import create_incident, CREATE_INCIDENT_SCHEMA


def test_create_incident_sin_pre_existing_crea_nueva():
    """1. Llamada normal sin pre_existing_ticket_id → crea ticket nuevo."""
    async def _go():
        c = await _conn()
        try:
            result = await create_incident(
                c,
                descripcion="Deuda A.2 test 1 - sin pre_existing (safe to delete)",
                prioridad="P4",
                categoria="TEST",
                sla_horas=24.0,
                area_afectada="Pruebas",
            )
            tid = result.get("ticket_id")
            # cleanup inmediato
            if tid:
                await c.execute("DELETE FROM incidencias_run WHERE ticket_id=$1", tid)
            return result, tid
        finally:
            await c.close()
    result, tid = _run(_go())
    assert tid is not None, "no devolvió ticket_id"
    assert re.match(r'^INC-[0-9]{6}-[0-9]{8}$', tid), f"formato inválido: {tid}"
    assert "_idempotent" not in result, "_idempotent NO debería estar en respuesta normal"
    assert result.get("status") == "created"


def test_create_incident_con_pre_existing_devuelve_existente():
    """2. Con pre_existing_ticket_id válido → devuelve fila existente, _idempotent=True."""
    async def _go():
        c = await _conn()
        try:
            # crear un ticket de prueba con generar_ticket_id directamente
            tid = await c.fetchval("SELECT generar_ticket_id()")
            await c.execute("""
                INSERT INTO incidencias_run
                (ticket_id, incidencia_detectada, prioridad_ia, categoria,
                 sla_limite, area_afectada, agente_origen, estado)
                VALUES ($1, 'Deuda A.2 test 2 base', 'P3', 'TEST', 24, 'Pruebas', 'AG-001', 'QUEUED')
            """, tid)
            count_pre = await c.fetchval("SELECT COUNT(*) FROM incidencias_run")
            # invocar con pre_existing_ticket_id
            result = await create_incident(
                c,
                descripcion="MENSAJE NUEVO QUE NO DEBERIA INSERTARSE",
                prioridad="P1",
                categoria="OTRO",
                sla_horas=4.0,
                area_afectada="OTRO",
                pre_existing_ticket_id=tid,
            )
            count_post = await c.fetchval("SELECT COUNT(*) FROM incidencias_run")
            # cleanup
            await c.execute("DELETE FROM incidencias_run WHERE ticket_id=$1", tid)
            return result, tid, count_pre, count_post
        finally:
            await c.close()
    result, tid, pre, post = _run(_go())
    assert result["ticket_id"] == tid, f"devolvió ticket distinto: {result['ticket_id']} != {tid}"
    assert result.get("_idempotent") is True, f"_idempotent debería ser True: {result}"
    assert pre == post, f"el count cambió: {pre} → {post} (la tool insertó cuando NO debía)"
    # Los datos son los del ticket original, no los del kwargs nuevo
    assert result["prioridad"] == "P3", "no debe usar la prioridad nueva del kwarg"
    assert result["categoria"] == "TEST"


def test_create_incident_con_pre_existing_inexistente_devuelve_error():
    """3. Con pre_existing_ticket_id inexistente → error, _idempotent=False, NO INSERT."""
    async def _go():
        c = await _conn()
        try:
            count_pre = await c.fetchval("SELECT COUNT(*) FROM incidencias_run")
            result = await create_incident(
                c,
                descripcion="Deuda A.2 test 3",
                prioridad="P4",
                categoria="TEST",
                sla_horas=24.0,
                area_afectada="Pruebas",
                pre_existing_ticket_id="INC-999999-19000101",
            )
            count_post = await c.fetchval("SELECT COUNT(*) FROM incidencias_run")
            return result, count_pre, count_post
        finally:
            await c.close()
    result, pre, post = _run(_go())
    assert "error" in result, f"esperaba 'error' en respuesta: {result}"
    assert result.get("_idempotent") is False
    assert "INC-999999-19000101" in result["error"]
    assert pre == post, f"count cambió ({pre}→{post}): la tool NO debe crear ticket nuevo cuando el pre_existing es inválido"


def test_schema_create_incident_tiene_campo_opcional():
    """4. CREATE_INCIDENT_SCHEMA tiene pre_existing_ticket_id en properties, NO en required."""
    properties = CREATE_INCIDENT_SCHEMA["input_schema"]["properties"]
    required = CREATE_INCIDENT_SCHEMA["input_schema"]["required"]
    assert "pre_existing_ticket_id" in properties, \
        "pre_existing_ticket_id falta en properties"
    assert properties["pre_existing_ticket_id"]["type"] == "string"
    assert "pre_existing_ticket_id" not in required, \
        "pre_existing_ticket_id NO debería ser required (rompería compat hacia atrás)"

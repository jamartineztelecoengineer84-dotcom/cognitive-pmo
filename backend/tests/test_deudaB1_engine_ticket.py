"""
Deuda B.1 — F-ARQ02-12: tests para AgentEngine._log que pobla
agent_conversations.ticket_id vía regex sobre el prefijo 'TICKET:' del
user_msg + EXISTS guard contra incidencias_run.

Cubre:
1. user_msg con prefijo TICKET: y ticket real existente → 2 filas con
   ticket_id poblado en agent_conversations
2. user_msg con prefijo TICKET: pero ticket inexistente → 2 filas con
   ticket_id NULL (EXISTS guard descarta el fantasma)
3. user_msg sin prefijo TICKET: → 2 filas con ticket_id NULL

Patrón sync (_run + asyncpg) usado por el resto del repo.
"""
import asyncio
import os
import asyncpg

from agents.config import AGENT_CONFIGS
from agents.engine import AgentEngine


DB_HOST = os.getenv("DB_HOST", "postgres")
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


CFG = AGENT_CONFIGS["AG-001"]


def test_log_con_ticket_real_propaga_ticket_id():
    """1. TICKET: <id real> → 2 filas con ticket_id poblado."""
    async def _go():
        c = await _conn()
        try:
            tid = await c.fetchval("SELECT generar_ticket_id()")
            await c.execute(
                """INSERT INTO incidencias_run
                   (ticket_id, incidencia_detectada, prioridad_ia, categoria,
                    sla_limite, area_afectada, estado)
                   VALUES ($1, 'B1 test ticket real', 'P3', 'TEST', 24, 'Pruebas', 'QUEUED')""",
                tid,
            )
            session_id = f"deudaB1-real-{tid}"
            engine = AgentEngine(CFG, c)
            await engine._log(
                session_id=session_id,
                user_msg=f"TICKET: {tid}\ndescripcion de prueba",
                response="respuesta del agente",
                tokens=42,
                latency=123,
            )
            rows = await c.fetch(
                """SELECT role, ticket_id FROM agent_conversations
                   WHERE session_id=$1 ORDER BY created_at""",
                session_id,
            )
            # cleanup
            await c.execute(
                "DELETE FROM agent_conversations WHERE session_id=$1", session_id
            )
            await c.execute(
                "DELETE FROM incidencias_run WHERE ticket_id=$1", tid
            )
            return rows, tid
        finally:
            await c.close()

    rows, tid = _run(_go())
    assert len(rows) == 2, f"esperaba 2 filas (user+assistant), got {len(rows)}"
    assert {r["role"] for r in rows} == {"user", "assistant"}
    for r in rows:
        assert r["ticket_id"] == tid, (
            f"role={r['role']} ticket_id={r['ticket_id']} esperado={tid}"
        )


def test_log_con_ticket_inexistente_guard_devuelve_null():
    """2. TICKET: <id inexistente> → EXISTS guard descarta, ticket_id NULL."""
    async def _go():
        c = await _conn()
        try:
            fake_tid = "INC-999998-19000101"
            # asegurar que NO existe
            await c.execute("DELETE FROM incidencias_run WHERE ticket_id=$1", fake_tid)
            session_id = f"deudaB1-fantasma-{fake_tid}"
            engine = AgentEngine(CFG, c)
            await engine._log(
                session_id=session_id,
                user_msg=f"TICKET: {fake_tid}\nincidencia con ticket fantasma",
                response="respuesta",
                tokens=10,
                latency=50,
            )
            rows = await c.fetch(
                """SELECT role, ticket_id FROM agent_conversations
                   WHERE session_id=$1 ORDER BY created_at""",
                session_id,
            )
            await c.execute(
                "DELETE FROM agent_conversations WHERE session_id=$1", session_id
            )
            return rows
        finally:
            await c.close()

    rows = _run(_go())
    assert len(rows) == 2, f"esperaba 2 filas, got {len(rows)}"
    for r in rows:
        assert r["ticket_id"] is None, (
            f"EXISTS guard falló: role={r['role']} ticket_id={r['ticket_id']}"
        )


def test_log_sin_prefijo_ticket_es_null():
    """3. user_msg sin prefijo TICKET: → ticket_id NULL en las 2 filas."""
    async def _go():
        c = await _conn()
        try:
            session_id = "deudaB1-sin-prefijo-test"
            engine = AgentEngine(CFG, c)
            await engine._log(
                session_id=session_id,
                user_msg="hola, esto es una conversacion sin ticket",
                response="respuesta libre",
                tokens=5,
                latency=20,
            )
            rows = await c.fetch(
                """SELECT role, ticket_id FROM agent_conversations
                   WHERE session_id=$1 ORDER BY created_at""",
                session_id,
            )
            await c.execute(
                "DELETE FROM agent_conversations WHERE session_id=$1", session_id
            )
            return rows
        finally:
            await c.close()

    rows = _run(_go())
    assert len(rows) == 2, f"esperaba 2 filas, got {len(rows)}"
    for r in rows:
        assert r["ticket_id"] is None, (
            f"role={r['role']} debería ser NULL, got {r['ticket_id']}"
        )

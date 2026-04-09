"""
Bloque B — cierre: test integrador end-to-end que verifica las 3 invariantes
del Bloque B en una sola pasada.

- B.1 (F-ARQ02-12): agent_conversations.ticket_id se pobla cuando user_msg
  empieza con 'TICKET: <id_real>' (vía AgentEngine._log con regex + EXISTS guard)
- B.2 (F-ARQ02-10): el SQL del backfill F5 usa regexp_matches global, NO
  regexp_match singular (verificación lexical sobre database/arq02_fase5_run.sh)
- B.4 (F-ARQ02-13): la vista agent_conversations_cobertura existe y excluye
  exactamente 56 filas con menciones legacy huérfanas pre-F1

Patrón sync (_run + asyncpg) usado por el resto del repo.
"""
import asyncio
import os
import re
import asyncpg

from agents.config import AGENT_CONFIGS
from agents.engine import AgentEngine


DB_HOST = os.getenv("DB_HOST", "192.168.1.49")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "cognitive_pmo")
DB_USER = os.getenv("DB_USER", "jose_admin")
DB_PASS = os.getenv("DB_PASSWORD", "")

BACKFILL_SH_CANDIDATES = [
    "/app/database/arq02_fase5_run.sh",
    "/app/tests/arq02_fase5_run.sh",
    "/root/cognitive-pmo/database/arq02_fase5_run.sh",
]


async def _conn():
    return await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASS,
    )


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _read_backfill_sh():
    for path in BACKFILL_SH_CANDIDATES:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f.read()
    raise FileNotFoundError(
        f"backfill script not found at any of {BACKFILL_SH_CANDIDATES}"
    )


def test_bloqueB_invariantes_integrador():
    """Verifica las 3 invariantes B en una sola pasada."""
    async def _go():
        c = await _conn()
        try:
            # ── B.1 — engine._log popula ticket_id desde prefijo TICKET: ──
            tid = await c.fetchval("SELECT generar_ticket_id()")
            await c.execute("""
                INSERT INTO incidencias_run
                (ticket_id, incidencia_detectada, prioridad_ia, categoria,
                 sla_limite, area_afectada, estado)
                VALUES ($1, 'B integrador', 'P3', 'TEST', 24, 'Pruebas', 'QUEUED')
            """, tid)
            session_id = f"deudaB-integrador-{tid}"
            engine = AgentEngine(AGENT_CONFIGS["AG-001"], c)
            await engine._log(
                session_id=session_id,
                user_msg=f"TICKET: {tid}\nintegrador end-to-end",
                response="ok",
                tokens=1,
                latency=1,
            )
            b1_rows = await c.fetch(
                "SELECT ticket_id FROM agent_conversations WHERE session_id=$1",
                session_id,
            )
            await c.execute(
                "DELETE FROM agent_conversations WHERE session_id=$1", session_id
            )
            await c.execute("DELETE FROM incidencias_run WHERE ticket_id=$1", tid)

            # ── B.4 — vista cobertura excluye 56 huérfanos ──
            n_tabla = await c.fetchval("SELECT count(*) FROM agent_conversations")
            n_view = await c.fetchval("SELECT count(*) FROM agent_conversations_cobertura")
            return tid, b1_rows, n_tabla, n_view
        finally:
            await c.close()

    tid, b1_rows, n_tabla, n_view = _run(_go())

    # B.1 assertions
    assert len(b1_rows) == 2, f"B.1: esperaba 2 filas log, got {len(b1_rows)}"
    for r in b1_rows:
        assert r["ticket_id"] == tid, (
            f"B.1: ticket_id no propagado: got {r['ticket_id']} esperado {tid}"
        )

    # B.2 lexical assertions sobre el script SQL del backfill
    sh = _read_backfill_sh()
    assert "regexp_matches(" in sh, (
        "B.2: el script de backfill no usa regexp_matches (plural+global)"
    )
    # No debe quedar ningún regexp_match( singular fuera de los comentarios.
    # Heurística: extraer líneas no-comentario y comprobar que ninguna tenga
    # 'regexp_match(' aislado (i.e. no precedido por una 's' que lo haría
    # 'regexp_matches(').
    code_lines = [
        ln for ln in sh.splitlines()
        if ln.strip() and not ln.strip().startswith("--")
    ]
    bad = [
        ln for ln in code_lines
        if re.search(r"(?<!s)regexp_match\(", ln)
    ]
    assert not bad, (
        f"B.2: quedan llamadas a regexp_match (singular) fuera de comentarios: {bad}"
    )

    # B.4 assertions
    diff = n_tabla - n_view
    assert diff == 56, (
        f"B.4: vista cobertura no excluye 56 huérfanos: "
        f"tabla={n_tabla} view={n_view} diff={diff}"
    )

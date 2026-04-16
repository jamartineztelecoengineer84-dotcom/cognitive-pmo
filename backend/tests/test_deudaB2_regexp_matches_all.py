"""
Deuda B.2 — F-ARQ02-10: tests para el backfill F5 corregido con
regexp_matches global. Reproduce el escenario donde una fila tiene varias
menciones de tickets en content, la primera NO está en el map, pero una
secundaria SÍ lo está.

Cubre:
1. Backfill captura el segundo match cuando el primero no está en el map
   (con el regexp_match singular original quedaba NULL).
2. Backfill NO sobreescribe filas que ya tienen ticket_id poblado (el
   WHERE ac.ticket_id IS NULL las protege).

Patrón sync (_run + asyncpg) usado por el resto del repo. Cada test
construye un _ticket_id_map TEMP en una transacción aislada y la rollbackea
al final para no dejar residuos.
"""
import asyncio
import os
import asyncpg


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


# old_id real del CSV ticket_id_map_F1.csv (línea 1 del map)
REAL_OLD_ID = "INC-20260321-6DE9"
REAL_NEW_ID = "INC-000001-20260321"
SESSION_TAG = "deudaB2-test-tag-DO-NOT-USE-IN-PROD"


async def _setup_map_in_tx(conn):
    """Crea _ticket_id_map TEMP con 1 entrada real para el test."""
    await conn.execute("""
        CREATE TEMP TABLE IF NOT EXISTS _ticket_id_map (
            old_id text PRIMARY KEY,
            new_id text NOT NULL
        ) ON COMMIT DROP
    """)
    await conn.execute("DELETE FROM _ticket_id_map")
    await conn.execute(
        "INSERT INTO _ticket_id_map (old_id, new_id) VALUES ($1, $2)",
        REAL_OLD_ID, REAL_NEW_ID,
    )


async def _run_backfill(conn):
    """Ejecuta el UPDATE del backfill corregido (regexp_matches global)."""
    return await conn.execute("""
        UPDATE agent_conversations ac
        SET ticket_id = m.new_id
        FROM _ticket_id_map m
        WHERE ac.ticket_id IS NULL
          AND ac.session_id LIKE $1
          AND EXISTS (
            SELECT 1 FROM regexp_matches(ac.content, 'INC-[0-9]{8}-[A-F0-9]+', 'g') AS r(match)
            WHERE r.match[1] = m.old_id
          )
    """, f"{SESSION_TAG}%")


def test_backfill_captura_segundo_match():
    """1. content con primer INC ficticio + segundo INC en map → ticket_id poblado."""
    async def _go():
        c = await _conn()
        try:
            tx = c.transaction()
            await tx.start()
            try:
                await _setup_map_in_tx(c)
                # Insert fila con multi-mention: primer id ficticio, segundo en map
                conv_id = await c.fetchval("""
                    INSERT INTO agent_conversations
                    (session_id, agent_id, agent_name, role, content)
                    VALUES ($1, 'AG-002', 'Test', 'assistant',
                            'Foo INC-99999999-DEAD bar INC-20260321-6DE9 baz')
                    RETURNING id
                """, f"{SESSION_TAG}-segundo-match")
                # Estado pre-backfill: ticket_id NULL
                pre = await c.fetchval(
                    "SELECT ticket_id FROM agent_conversations WHERE id=$1", conv_id
                )
                assert pre is None
                # Ejecuta backfill
                await _run_backfill(c)
                # Post-backfill: debe estar poblado con REAL_NEW_ID
                post = await c.fetchval(
                    "SELECT ticket_id FROM agent_conversations WHERE id=$1", conv_id
                )
                return post
            finally:
                await tx.rollback()
        finally:
            await c.close()

    post = _run(_go())
    assert post == REAL_NEW_ID, (
        f"backfill no capturó el segundo match: ticket_id={post}, "
        f"esperado={REAL_NEW_ID}"
    )


def test_backfill_no_pisa_pobladas():
    """2. fila con ticket_id ya poblado + multi-mention → backfill NO la pisa."""
    async def _go():
        c = await _conn()
        try:
            tx = c.transaction()
            await tx.start()
            try:
                await _setup_map_in_tx(c)
                # Para no romper la FK lógica del test_ningun_ticket_id_fantasma
                # de F5, usamos un ticket_id real existente en incidencias_run.
                preset = await c.fetchval(
                    "SELECT ticket_id FROM incidencias_run LIMIT 1"
                )
                assert preset is not None, "BD vacía, no hay ticket para preset"
                conv_id = await c.fetchval("""
                    INSERT INTO agent_conversations
                    (session_id, agent_id, agent_name, role, content, ticket_id)
                    VALUES ($1, 'AG-002', 'Test', 'assistant',
                            'Foo INC-99999999-DEAD bar INC-20260321-6DE9 baz', $2)
                    RETURNING id
                """, f"{SESSION_TAG}-no-pisa", preset)
                pre = await c.fetchval(
                    "SELECT ticket_id FROM agent_conversations WHERE id=$1", conv_id
                )
                assert pre == preset
                # Ejecuta backfill
                await _run_backfill(c)
                # Post-backfill: ticket_id sigue siendo el preset (NO se pisó)
                post = await c.fetchval(
                    "SELECT ticket_id FROM agent_conversations WHERE id=$1", conv_id
                )
                return preset, post
            finally:
                await tx.rollback()
        finally:
            await c.close()

    preset, post = _run(_go())
    assert post == preset, (
        f"backfill SOBRESCRIBIÓ una fila ya poblada: pre={preset} post={post}"
    )

"""
ARQ-02 F5 — tests para la columna soft ticket_id en agent_conversations.

Cubre:
1. Columna añadida con tipo y nullability correctos
2. Índice parcial creado
3. Count de backfill >= 126 (126 fue el resultado en F5.1 sobre baseline real)
4. Todo ticket_id poblado apunta a un ticket real en incidencias_run
5. Solo formato nuevo INC-NNNNNN-YYYYMMDD tras backfill (ningún legacy)
6. Filas de agentes BUILD (AG-005, AG-007, AG-013) siguen con ticket_id NULL

Mismo patrón sync (_run + asyncpg.connect) que el resto de tests del repo,
para no requerir pytest-asyncio.
"""
import asyncio
import os
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


def test_column_ticket_id_added():
    """1. Columna ticket_id existe con tipo varchar(30) NULL."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchrow("""
                SELECT data_type, character_maximum_length, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'agent_conversations' AND column_name = 'ticket_id'
            """)
        finally:
            await c.close()
    row = _run(_go())
    assert row is not None, "Columna ticket_id no existe"
    assert row["data_type"] == "character varying"
    assert row["character_maximum_length"] == 30
    assert row["is_nullable"] == "YES"


def test_index_parcial_creado():
    """2. Índice parcial idx_conv_ticket WHERE ticket_id IS NOT NULL."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchrow("""
                SELECT indexdef FROM pg_indexes
                WHERE tablename = 'agent_conversations' AND indexname = 'idx_conv_ticket'
            """)
        finally:
            await c.close()
    row = _run(_go())
    assert row is not None, "Índice idx_conv_ticket no creado"
    assert "ticket_id IS NOT NULL" in row["indexdef"], \
        "Índice no es parcial sobre ticket_id IS NOT NULL"


def test_backfill_minimo_126():
    """3. Backfill pobló >=126 filas (resultado exacto F5.1)."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval(
                "SELECT COUNT(*) FROM agent_conversations WHERE ticket_id IS NOT NULL"
            )
        finally:
            await c.close()
    n = _run(_go())
    assert n >= 126, f"Backfill bajo: solo {n} filas con ticket_id (esperado >=126)"


def test_ningun_ticket_id_fantasma():
    """4. Todo ticket_id poblado apunta a ticket real en incidencias_run."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval("""
                SELECT COUNT(*) FROM agent_conversations ac
                WHERE ac.ticket_id IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM incidencias_run r WHERE r.ticket_id = ac.ticket_id
                  )
            """)
        finally:
            await c.close()
    n = _run(_go())
    assert n == 0, f"{n} filas con ticket_id apuntando a fantasma"


def test_ticket_id_formato_nuevo():
    """5. Todo ticket_id poblado cumple regex INC-NNNNNN-YYYYMMDD."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchval("""
                SELECT COUNT(*) FROM agent_conversations
                WHERE ticket_id IS NOT NULL
                  AND ticket_id !~ '^INC-[0-9]{6}-[0-9]{8}$'
            """)
        finally:
            await c.close()
    legacy = _run(_go())
    assert legacy == 0, f"{legacy} ticket_id con formato no-nuevo"


def test_agentes_build_sin_ticket_id():
    """6. Agentes BUILD (AG-005/007/013) tienen ratio <5% con ticket_id."""
    async def _go():
        c = await _conn()
        try:
            return await c.fetchrow("""
                SELECT
                  COUNT(*) FILTER (WHERE ticket_id IS NOT NULL) AS con_ticket,
                  COUNT(*) AS total
                FROM agent_conversations
                WHERE agent_id LIKE 'AG-005%'
                   OR agent_id LIKE 'AG-007%'
                   OR agent_id LIKE 'AG-013%'
            """)
        finally:
            await c.close()
    row = _run(_go())
    ratio = (row["con_ticket"] / row["total"]) if row["total"] else 0
    assert ratio < 0.05, (
        f"Ratio BUILD con ticket_id {ratio:.1%} >= 5% "
        f"(con_ticket={row['con_ticket']}, total={row['total']})"
    )

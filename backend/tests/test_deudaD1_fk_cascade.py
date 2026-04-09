"""D.1 F-ARQ02-18: FK CASCADE kanban_tareas.id_incidencia → incidencias_run.

Cubre:
1. INSERT en kanban_tareas con id_incidencia inexistente → ForeignKeyViolationError
2. DELETE de incidencias_run → CASCADE limpia kanban_tareas hijas

Patrón sync (_run + asyncpg) usado por el resto del repo.
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


def test_fk_cascade_rechaza_id_incidencia_fantasma():
    """1. INSERT con id_incidencia inexistente → ForeignKeyViolationError."""
    async def _go():
        c = await _conn()
        try:
            # Asegurar que el id no existe
            await c.execute("DELETE FROM kanban_tareas WHERE id='KT-D1-TEST-001'")
            try:
                await c.execute("""
                    INSERT INTO kanban_tareas
                    (id, titulo, tipo, prioridad, columna, id_incidencia)
                    VALUES ('KT-D1-TEST-001', 'fk test', 'RUN', 'Media',
                            'Backlog', 'INC-999999-20260409')
                """)
                # Si llega aquí, no levantó la excepción esperada
                await c.execute("DELETE FROM kanban_tareas WHERE id='KT-D1-TEST-001'")
                return False
            except asyncpg.ForeignKeyViolationError:
                return True
        finally:
            await c.close()
    rejected = _run(_go())
    assert rejected, (
        "INSERT con id_incidencia fantasma NO fue rechazado por FK CASCADE"
    )


def test_fk_cascade_borra_hijas_al_borrar_padre():
    """2. DELETE incidencias_run cascadea a kanban_tareas hijas."""
    async def _go():
        c = await _conn()
        try:
            tid = 'INC-888888-20260409'
            kid = 'KT-D1-CASCADE-001'
            # cleanup previo idempotente (CASCADE al borrar incidencia limpia kanban)
            await c.execute("DELETE FROM kanban_tareas WHERE id=$1", kid)
            await c.execute("DELETE FROM incidencias_run WHERE ticket_id=$1", tid)
            # seed incidencia padre
            await c.execute("""
                INSERT INTO incidencias_run
                (ticket_id, incidencia_detectada, prioridad_ia, categoria, estado)
                VALUES ($1, 'd1 cascade test', 'P3', 'TEST', 'QUEUED')
            """, tid)
            # seed kanban hija
            await c.execute("""
                INSERT INTO kanban_tareas
                (id, titulo, tipo, prioridad, columna, id_incidencia)
                VALUES ($1, 'hija cascade', 'RUN', 'Media', 'Backlog', $2)
            """, kid, tid)
            n_before = await c.fetchval(
                "SELECT count(*) FROM kanban_tareas WHERE id_incidencia=$1", tid
            )
            assert n_before == 1, f"seed falló: n_before={n_before}"
            # borrar padre → CASCADE hijas
            await c.execute("DELETE FROM incidencias_run WHERE ticket_id=$1", tid)
            n_after = await c.fetchval(
                "SELECT count(*) FROM kanban_tareas WHERE id_incidencia=$1", tid
            )
            return n_after
        finally:
            await c.close()
    n_after = _run(_go())
    assert n_after == 0, (
        f"CASCADE no borró hijas al borrar padre: {n_after} filas residuales"
    )

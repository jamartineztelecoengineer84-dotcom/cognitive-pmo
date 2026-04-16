import asyncio
import json
import logging
from agents.engine import AgentEngine
from agents.config import AGENT_CONFIGS

log = logging.getLogger("task_advisor")


async def task_advisor_loop(db_pool):
    """Detecta tarjetas Kanban nuevas sin instrucciones y las enriquece con AG-012"""
    log.info("Task Advisor Worker started")
    while True:
        try:
            if "AG-012" not in AGENT_CONFIGS:
                await asyncio.sleep(30)
                continue

            rows = await db_pool.fetch("""
                SELECT kt.id, kt.titulo, kt.id_incidencia, kt.id_proyecto,
                       kt.id_tecnico, kt.descripcion, kt.tipo
                FROM kanban_tareas kt
                WHERE kt.fecha_creacion > now() - interval '10 minutes'
                AND (
                    kt.descripcion IS NULL
                    OR kt.descripcion = ''
                    OR NOT (kt.descripcion::text LIKE '%"enriched"%')
                )
                ORDER BY kt.fecha_creacion DESC
                LIMIT 3
            """)

            if rows:
                log.info(f"Task Advisor: {len(rows)} tarjetas por enriquecer")

            engine = AgentEngine(AGENT_CONFIGS["AG-012"], db_pool)

            for task in rows:
                context_parts = [
                    "Tarea Kanban a enriquecer:",
                    f"  ID: {task['id']}",
                    f"  Título: {task['titulo']}",
                    f"  Tipo: {task['tipo'] or 'Desconocido'}",
                ]

                if task['id_incidencia']:
                    inc = await db_pool.fetchrow("""
                        SELECT ticket_id, incidencia_detectada, prioridad_ia,
                               ci_afectado, servicio_afectado, area_afectada
                        FROM incidencias_run WHERE ticket_id = $1
                    """, task['id_incidencia'])
                    if inc:
                        context_parts.extend([
                            f"  Incidencia: {inc['ticket_id']}",
                            f"  Descripción: {inc['incidencia_detectada']}",
                            f"  Prioridad: {inc['prioridad_ia']}",
                            f"  CI afectado: {inc['ci_afectado'] or 'No especificado'}",
                            f"  Servicio: {inc['servicio_afectado'] or 'No especificado'}",
                        ])

                elif task['id_proyecto']:
                    proy = await db_pool.fetchrow("""
                        SELECT nombre_proyecto, prioridad_estrategica
                        FROM cartera_build WHERE id_proyecto = $1
                    """, task['id_proyecto'])
                    if proy:
                        context_parts.extend([
                            f"  Proyecto: {task['id_proyecto']}",
                            f"  Nombre: {proy['nombre_proyecto']}",
                            f"  Prioridad: {proy['prioridad_estrategica']}",
                        ])

                if task['id_tecnico']:
                    tech = await db_pool.fetchrow("""
                        SELECT nombre, nivel, silo_especialidad
                        FROM pmo_staff_skills WHERE id_recurso = $1
                    """, task['id_tecnico'])
                    if tech:
                        context_parts.append(
                            f"  Técnico asignado: {tech['nombre']} ({tech['nivel']}, {tech['silo_especialidad']})")

                context = "\n".join(context_parts)

                try:
                    await engine.invoke(context, session_id=task['id'])
                    log.info(f"Task Advisor: enriched {task['id']}")
                except Exception as e:
                    log.error(f"Task Advisor error for {task['id']}: {e}")

        except Exception as e:
            log.error(f"Task Advisor loop error: {e}")

        await asyncio.sleep(15)

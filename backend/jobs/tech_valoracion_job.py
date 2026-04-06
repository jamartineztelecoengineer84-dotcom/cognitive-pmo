"""
COGNITIVE PMO — Job de valoración mensual de técnicos.
Calcula puntuación compuesta basada en SLA (RUN) + velocidad SP (BUILD) + calidad.
"""

import logging
from datetime import date, timedelta
from calendar import monthrange

logger = logging.getLogger(__name__)

# Target: 10 story points per week
OBJETIVO_SP_SEMANA = 10


async def calcular_valoracion_mensual(pool, mes: date = None):
    """
    Calcula la valoración mensual de todos los técnicos.
    mes: primer día del mes a calcular. Si None, mes anterior.
    Returns: dict con stats de ejecución.
    """
    if not pool:
        return {"error": "DB pool no disponible"}

    if mes is None:
        hoy = date.today()
        primer_dia_actual = hoy.replace(day=1)
        mes = (primer_dia_actual - timedelta(days=1)).replace(day=1)

    # Ensure mes is first day
    mes = mes.replace(day=1)
    dias_mes = monthrange(mes.year, mes.month)[1]
    mes_fin = date(mes.year, mes.month, dias_mes)
    semanas_mes = max(dias_mes / 7, 1)

    logger.info(f"Calculando valoración: {mes} → {mes_fin} ({dias_mes} días, {semanas_mes:.1f} semanas)")

    stats = {"mes": str(mes), "tecnicos_procesados": 0, "upserted": 0, "errores": 0}

    async with pool.acquire() as conn:
        # Get all technicians who had activity in this month
        tecnicos = await conn.fetch("""
            SELECT DISTINCT id_recurso FROM (
                SELECT tecnico_asignado as id_recurso FROM incidencias_run
                WHERE tecnico_asignado IS NOT NULL
                  AND timestamp_creacion >= $1 AND timestamp_creacion <= $2
                UNION
                SELECT id_tecnico as id_recurso FROM kanban_tareas
                WHERE id_tecnico IS NOT NULL
                  AND fecha_creacion >= $1 AND fecha_creacion <= $2
            ) sub
            WHERE id_recurso IS NOT NULL
        """, mes, mes_fin)

        # Also include all staff with existing assignments
        all_staff = await conn.fetch("""
            SELECT DISTINCT id_recurso FROM (
                SELECT tecnico_asignado as id_recurso FROM incidencias_run
                WHERE tecnico_asignado IS NOT NULL
                  AND timestamp_resolucion >= $1 AND timestamp_resolucion <= $2
                UNION
                SELECT id_tecnico as id_recurso FROM kanban_tareas
                WHERE id_tecnico IS NOT NULL
                  AND fecha_cierre >= $1 AND fecha_cierre <= $2
                UNION
                SELECT id_recurso FROM (SELECT tecnico_asignado as id_recurso FROM incidencias_run
                    WHERE tecnico_asignado IS NOT NULL
                    AND timestamp_creacion >= $1 AND timestamp_creacion <= $2) s2
            ) sub WHERE id_recurso IS NOT NULL
        """, mes, mes_fin)

        # Merge unique
        recurso_ids = list(set(
            [r["id_recurso"] for r in tecnicos] + [r["id_recurso"] for r in all_staff]
        ))

        for id_recurso in recurso_ids:
            try:
                # === RUN METRICS ===
                # Incidencias resueltas en el mes
                total_incidencias = await conn.fetchval("""
                    SELECT COUNT(*) FROM incidencias_run
                    WHERE tecnico_asignado = $1
                      AND estado IN ('RESUELTO', 'CERRADO')
                      AND timestamp_resolucion >= $2 AND timestamp_resolucion <= $3
                """, id_recurso, mes, mes_fin) or 0

                # Incidencias dentro de SLA
                incidencias_en_sla = 0
                if total_incidencias > 0:
                    incidencias_en_sla = await conn.fetchval("""
                        SELECT COUNT(*) FROM incidencias_run
                        WHERE tecnico_asignado = $1
                          AND estado IN ('RESUELTO', 'CERRADO')
                          AND timestamp_resolucion >= $2 AND timestamp_resolucion <= $3
                          AND sla_limite IS NOT NULL
                          AND tiempo_resolucion_minutos IS NOT NULL
                          AND tiempo_resolucion_minutos <= (sla_limite * 60)
                    """, id_recurso, mes, mes_fin) or 0

                pct_sla = round((incidencias_en_sla / total_incidencias) * 100, 2) if total_incidencias > 0 else 0

                # === BUILD METRICS ===
                # Tareas completadas en el mes
                total_tareas = await conn.fetchval("""
                    SELECT COUNT(*) FROM kanban_tareas
                    WHERE id_tecnico = $1
                      AND columna = 'Completado'
                      AND fecha_cierre >= $2 AND fecha_cierre <= $3
                """, id_recurso, mes, mes_fin) or 0

                story_points_completados = await conn.fetchval("""
                    SELECT COALESCE(SUM(horas_estimadas), 0) FROM kanban_tareas
                    WHERE id_tecnico = $1
                      AND columna = 'Completado'
                      AND fecha_cierre >= $2 AND fecha_cierre <= $3
                """, id_recurso, mes, mes_fin) or 0
                story_points_completados = int(story_points_completados)

                velocidad_media_sp = round(story_points_completados / semanas_mes, 2) if semanas_mes > 0 else 0

                # === CALIDAD ===
                # Tasa reopen: incidencias que volvieron de RESUELTO a otro estado
                # Approximate: count incidents resolved this month that have estado != RESUELTO/CERRADO
                tasa_reopen = 0.0  # Default, no reopen tracking in current schema

                # === PUNTUACIÓN COMPUESTA ===
                # 40% SLA + 35% velocidad SP + 25% calidad (100 - reopen)
                vel_pct = min((velocidad_media_sp / OBJETIVO_SP_SEMANA) * 100, 100) if OBJETIVO_SP_SEMANA > 0 else 0
                puntuacion = round(
                    (pct_sla * 0.40) +
                    (vel_pct * 0.35) +
                    ((100 - tasa_reopen) * 0.25),
                    2
                )

                # === UPSERT ===
                await conn.execute("""
                    INSERT INTO tech_valoracion_mensual
                    (id_recurso, mes, total_incidencias, incidencias_en_sla, pct_sla,
                     total_tareas, story_points_completados, velocidad_media_sp,
                     tasa_reopen, puntuacion)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id_recurso, mes) DO UPDATE SET
                        total_incidencias = EXCLUDED.total_incidencias,
                        incidencias_en_sla = EXCLUDED.incidencias_en_sla,
                        pct_sla = EXCLUDED.pct_sla,
                        total_tareas = EXCLUDED.total_tareas,
                        story_points_completados = EXCLUDED.story_points_completados,
                        velocidad_media_sp = EXCLUDED.velocidad_media_sp,
                        tasa_reopen = EXCLUDED.tasa_reopen,
                        puntuacion = EXCLUDED.puntuacion
                """, id_recurso, mes, total_incidencias, incidencias_en_sla, pct_sla,
                    total_tareas, story_points_completados, velocidad_media_sp,
                    tasa_reopen, puntuacion)

                stats["upserted"] += 1
                logger.info(f"  {id_recurso}: SLA={pct_sla}% SP={story_points_completados} Vel={velocidad_media_sp} Punt={puntuacion}")

            except Exception as e:
                logger.error(f"Error valoración {id_recurso}: {e}")
                stats["errores"] += 1

        stats["tecnicos_procesados"] = len(recurso_ids)

    logger.info(f"Valoración completada: {stats}")
    return stats

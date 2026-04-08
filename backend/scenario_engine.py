"""
ARQ-01 F4 Scenario Engine.

Genera escenarios de demo (EMPTY, HALF, OPTIMAL, OVERLOAD) para poblar
build_live y sus tablas hijas SIN tocar la data legacy de agentes IA ni
cartera_build.

INVARIANTES (unit-testeados):
  I1 · Toda DML tiene el guard regex ^PRJ-[A-Z]{3}[0-9]+$ o prefijo KAN-SC*/INC-SC*.
  I2 · UPDATE de build_live.id_pm_usuario SIEMPRE escribe también pm_asignado
       con nombre_completo, para preservar el ILIKE de v_p96_build_portfolio.
  I3 · Nunca tocar kanban_tareas.id LIKE 'KAN-%' que no empiece por 'KAN-SC'.
  I4 · Nunca tocar build_live.id_proyecto ~ '^PRJ-(?!SC[A-D])' (PRJ-MSF/IAF/...).
  I5 · cartera_build es read-only. Ni un INSERT/UPDATE/DELETE.
  I6 · random.seed(42); reproducible.
"""
import random
import re
import asyncpg

SCENARIO_PREFIXES = ('A', 'B', 'C', 'D')  # PRJ-SCA, SCB, SCC, SCD
GUARD_REGEX_PROJ  = r'^PRJ-SC[A-D][0-9]+$'
LEGACY_PROJ_REGEX = r'^PRJ-(?!SC[A-D])'    # todo menos nuestros scenario ids


def _assert_guard(id_proyecto: str) -> None:
    """Invariante I1: solo se aceptan ids con prefijo scenario."""
    if not re.match(GUARD_REGEX_PROJ, id_proyecto):
        raise AssertionError(f"Guard regex violation: {id_proyecto}")


async def reset_scenario(conn: asyncpg.Connection) -> None:
    """Borra SOLO las filas scenario. Legacy intacto."""
    async with conn.transaction():
        await conn.execute(
            "DELETE FROM incidencias_run WHERE ticket_id LIKE 'INC-SC%'"
        )
        await conn.execute(
            "DELETE FROM kanban_tareas WHERE id LIKE 'KAN-SC%'"
        )
        for tbl in (
            'build_sprint_items', 'build_sprints', 'build_quality_gates',
            'build_stakeholders', 'build_risks', 'build_subtasks',
            'build_project_plans', 'build_live',
        ):
            await conn.execute(
                f"DELETE FROM {tbl} WHERE id_proyecto ~ '^PRJ-SC[A-D][0-9]+$'"
            )


async def seed_scenario_empty(conn: asyncpg.Connection) -> None:
    """Escenario 0 — EMPTY: sin data scenario, todo legacy intacto."""
    await reset_scenario(conn)


async def seed_scenario_optimal(conn: asyncpg.Connection) -> None:
    """Escenario 2 — OPTIMAL: 40 proyectos PRJ-SCA/B/C/D, 10 PMs x 4 proy cada uno,
    120 kanban nuevas, 12 incidencias nuevas, pct_capacidad <= 95%."""
    random.seed(42)
    await reset_scenario(conn)

    # Obtener los 10 PMs nuevos (PM-016..PM-025) con su id_usuario_rbac
    pms = await conn.fetch("""
        SELECT p.id_pm, p.nombre, p.id_usuario_rbac
        FROM pmo_project_managers p
        WHERE p.id_pm ~ '^PM-0(1[6-9]|2[0-5])$'
          AND p.id_usuario_rbac IS NOT NULL
        ORDER BY p.id_pm
    """)
    assert len(pms) == 10, f"Esperaba 10 PMs nuevos, encontré {len(pms)}"

    prefixes = list(SCENARIO_PREFIXES)

    # 40 proyectos: 10 por prefijo A/B/C/D
    for i in range(40):
        prefix = prefixes[i // 10]
        num    = (i % 10) + 1
        id_proj = f"PRJ-SC{prefix}{num:03d}"
        _assert_guard(id_proj)

        pm = pms[i % 10]
        # Invariante I2: doble escritura id_pm_usuario + pm_asignado
        await conn.execute("""
            INSERT INTO build_live (
                id_proyecto, nombre, pm_asignado, id_pm_usuario,
                prioridad, estado, progreso_pct, sprint_actual, total_sprints,
                presupuesto_bac, presupuesto_consumido, risk_score,
                gate_actual, silo, ai_lead, fecha_inicio, fecha_fin_prevista
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                now(), now() + interval '180 days'
            )
        """,
            id_proj,
            f"Scenario Optimal Project {prefix}{num}",
            pm['nombre'],            # pm_asignado (varchar para ILIKE)
            pm['id_usuario_rbac'],   # id_pm_usuario (FK int)
            random.choice(['Alta', 'Media', 'Crítica']),
            'PLANIFICACION',
            random.randint(10, 40),
            random.randint(1, 4),
            16,
            random.randint(200000, 800000),
            random.randint(10000, 100000),
            round(random.uniform(0.1, 0.5), 2),
            'G2-PLANIFICACION',
            random.choice(['IT-CLOUD', 'IT-APPS', 'IT-DATA', 'IT-SEGURIDAD']),
            False,
        )

    # 120 kanban_tareas nuevas con columna VÁLIDA (CHECK existente en tabla)
    columnas_validas = ['Backlog', 'Análisis', 'En Progreso', 'Code Review', 'Testing']
    tecnicos = await conn.fetch(
        "SELECT id_recurso FROM pmo_staff_skills ORDER BY id_recurso LIMIT 50"
    )
    assert len(tecnicos) > 0, "No hay técnicos en pmo_staff_skills"

    for i in range(120):
        kan_id = f"KAN-SC{i:04d}"
        proj_idx = i % 40
        prefix = prefixes[proj_idx // 10]
        num = (proj_idx % 10) + 1
        id_proj = f"PRJ-SC{prefix}{num:03d}"
        await conn.execute("""
            INSERT INTO kanban_tareas (
                id, titulo, tipo, prioridad, columna,
                id_tecnico, id_proyecto, horas_estimadas
            ) VALUES ($1, $2, 'BUILD', $3, $4, $5, $6, $7)
        """,
            kan_id,
            f"Tarea scenario {i}",
            random.choice(['Alta', 'Media', 'Baja']),
            random.choice(columnas_validas),
            random.choice(tecnicos)['id_recurso'],
            id_proj,
            random.randint(2, 16),
        )

    # 12 incidencias scenario con estado VÁLIDO + id_proyecto (gracias a F4.0)
    estados_validos     = ['QUEUED', 'EN_CURSO', 'RESUELTO']
    prioridades_validas = ['P2', 'P3', 'P4']
    for i in range(12):
        ticket = f"INC-SC{i:03d}"
        proj_idx = i % 40
        prefix = prefixes[proj_idx // 10]
        num = (proj_idx % 10) + 1
        id_proj = f"PRJ-SC{prefix}{num:03d}"
        await conn.execute("""
            INSERT INTO incidencias_run (
                ticket_id, incidencia_detectada, prioridad_ia, estado,
                tecnico_asignado, id_proyecto
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """,
            ticket,
            f"Scenario incidente {i}",
            random.choice(prioridades_validas),
            random.choice(estados_validos),
            random.choice(tecnicos)['id_recurso'],
            id_proj,
        )

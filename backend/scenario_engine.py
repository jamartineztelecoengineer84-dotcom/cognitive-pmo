"""ARQ-03 F4 — Scenario engine (refactor post-esquemas).

Puebla esquemas destino (sc_*) con perfiles de demo (empty/half/optimal/
overload). El aislamiento lo provee PostgreSQL vía esquemas (ARQ-03 F1-F3),
no los prefijos de ID. primitiva es canon inmutable y NUNCA se escribe
desde este módulo.

Invariantes preservados del motor histórico:
  - I2 · UPDATE de build_live.id_pm_usuario SIEMPRE escribe también
         pm_asignado con nombre_completo (preserva ILIKE de
         v_p96_build_portfolio).
  - I5 · cartera_build es read-only. Ni un INSERT/UPDATE/DELETE.
  - I6 · random.seed(42); reproducible.

Invariantes disueltos por obsolescencia (esquemas reales sustituyen a
los prefijos):
  - I1, I3, I4 (guards de prefijo SC[A-D] / KAN-SC% / PRJ-SC).
"""
import random
import asyncpg

from scenario_context import SCENARIOS_VALIDOS

PROFILES = {"empty", "half", "optimal", "overload"}
PRIMITIVA = "primitiva"  # canon inmutable

# Perfil → (n_proyectos, n_kanban, n_incidencias)
PROFILE_COUNTS = {
    "empty":    (0,  0,   0),
    "half":     (20, 60,  8),
    "optimal":  (40, 120, 12),
    "overload": (40, 160, 22),
}


def _validate(scenario_name: str, profile: str) -> None:
    if scenario_name == PRIMITIVA:
        raise ValueError(
            "scenario_engine NO escribe en primitiva. "
            "primitiva es canon inmutable. Use sc_piloto0 o similar."
        )
    if scenario_name not in SCENARIOS_VALIDOS:
        raise ValueError(
            f"scenario_name inválido: {scenario_name!r}. "
            f"Válidos: {sorted(SCENARIOS_VALIDOS)}"
        )
    if profile not in PROFILES:
        raise ValueError(
            f"profile inválido: {profile!r}. Válidos: {sorted(PROFILES)}"
        )


async def _ensure_schema_exists(conn: asyncpg.Connection, scenario_name: str) -> bool:
    """Si el esquema no existe, lo crea vía
    compartido.crear_esquema_escenario(). Devuelve True si lo creó."""
    existe = await conn.fetchval(
        "SELECT EXISTS(SELECT 1 FROM information_schema.schemata "
        "WHERE schema_name = $1)",
        scenario_name,
    )
    if existe:
        return False
    await conn.execute(
        "SELECT compartido.crear_esquema_escenario($1)",
        scenario_name,
    )
    return True


async def _pick_least_loaded_tecnicos(conn: asyncpg.Connection, n: int):
    """Devuelve los n técnicos con MENOS horas abiertas en el esquema actual.

    Como el motor opera dentro del esquema destino vía search_path, el LEFT
    JOIN sobre kanban_tareas cuenta carga del esquema activo. En esquemas
    recién creados/reseteados todos tienen carga 0, así que devuelve los n
    primeros por id_recurso ASC (determinista). pmo_staff_skills vive en
    compartido y se resuelve por search_path.
    """
    rows = await conn.fetch("""
        SELECT s.id_recurso,
               COALESCE(SUM(k.horas_estimadas) FILTER (
                   WHERE k.columna NOT IN ('Completado','Bloqueado')
               ), 0) AS horas_abiertas
        FROM pmo_staff_skills s
        LEFT JOIN kanban_tareas k ON k.id_tecnico = s.id_recurso
        GROUP BY s.id_recurso
        ORDER BY horas_abiertas ASC, s.id_recurso ASC
        LIMIT $1
    """, n)
    assert len(rows) == n, f"Esperaba {n} técnicos, encontré {len(rows)}"
    return rows


async def _seed_empty(conn: asyncpg.Connection) -> None:
    """Perfil EMPTY: no hace nada (esquema queda vacío tras el reset)."""
    pass


async def _seed_optimal(conn: asyncpg.Connection) -> None:
    """40 proyectos, 10 PMs × 4 proy cada uno, 120 kanban, 12 incidencias."""
    pms = await conn.fetch("""
        SELECT p.id_pm, p.nombre, p.id_usuario_rbac
        FROM pmo_project_managers p
        WHERE p.id_pm ~ '^PM-0(1[6-9]|2[0-5])$'
          AND p.id_usuario_rbac IS NOT NULL
        ORDER BY p.id_pm
    """)
    assert len(pms) == 10, f"Esperaba 10 PMs nuevos, encontré {len(pms)}"

    for i in range(40):
        id_proj = f"PRJ-{i+1:03d}"
        pm = pms[i % 10]
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
            f"Scenario Optimal Project {i+1:03d}",
            pm['nombre'],            # I2: pm_asignado (varchar para ILIKE)
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

    columnas_validas = ['Backlog', 'Análisis', 'En Progreso', 'Code Review', 'Testing']
    tecnicos = await _pick_least_loaded_tecnicos(conn, 50)

    for i in range(120):
        kan_id = f"KAN-{i+1:04d}"
        proj_idx = i % 40
        id_proj = f"PRJ-{proj_idx+1:03d}"
        await conn.execute("""
            INSERT INTO kanban_tareas (
                id, titulo, tipo, prioridad, columna,
                id_tecnico, id_proyecto, horas_estimadas
            ) VALUES ($1, $2, 'BUILD', $3, $4, $5, $6, $7)
        """,
            kan_id,
            f"Tarea scenario {i+1}",
            random.choice(['Alta', 'Media', 'Baja']),
            random.choice(columnas_validas),
            random.choice(tecnicos)['id_recurso'],
            id_proj,
            random.randint(2, 16),
        )

    estados_validos     = ['QUEUED', 'EN_CURSO', 'RESUELTO']
    prioridades_validas = ['P2', 'P3', 'P4']
    for i in range(12):
        ticket = f"INC-{i+1:03d}"
        proj_idx = i % 40
        id_proj = f"PRJ-{proj_idx+1:03d}"
        await conn.execute("""
            INSERT INTO incidencias_run (
                ticket_id, incidencia_detectada, prioridad_ia, estado,
                tecnico_asignado, id_proyecto
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """,
            ticket,
            f"Scenario incidente {i+1}",
            random.choice(prioridades_validas),
            random.choice(estados_validos),
            random.choice(tecnicos)['id_recurso'],
            id_proj,
        )


async def _seed_half(conn: asyncpg.Connection) -> None:
    """20 proyectos, 5 PMs (PM-016..PM-020) × 4 proy, 60 kanban, 8 incidencias."""
    pms = await conn.fetch("""
        SELECT p.id_pm, p.nombre, p.id_usuario_rbac
        FROM pmo_project_managers p
        WHERE p.id_pm ~ '^PM-0(1[6-9]|20)$'
          AND p.id_usuario_rbac IS NOT NULL
        ORDER BY p.id_pm
    """)
    assert len(pms) == 5, f"Esperaba 5 PMs, encontré {len(pms)}"

    for i in range(20):
        id_proj = f"PRJ-{i+1:03d}"
        pm = pms[i % 5]
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
            f"Scenario Half Project {i+1:03d}",
            pm['nombre'], pm['id_usuario_rbac'],
            random.choice(['Alta', 'Media']),
            'PLANIFICACION',
            random.randint(20, 60),
            random.randint(1, 4), 16,
            random.randint(150000, 500000),
            random.randint(20000, 80000),
            round(random.uniform(0.2, 0.6), 2),
            'G2-PLANIFICACION',
            random.choice(['IT-CLOUD', 'IT-APPS', 'IT-DATA']),
            False,
        )

    columnas_validas = ['Backlog', 'Análisis', 'En Progreso', 'Code Review', 'Testing']
    tecnicos = await _pick_least_loaded_tecnicos(conn, 30)

    for i in range(60):
        kan_id = f"KAN-{i+1:04d}"
        proj_idx = i % 20
        id_proj = f"PRJ-{proj_idx+1:03d}"
        await conn.execute("""
            INSERT INTO kanban_tareas (
                id, titulo, tipo, prioridad, columna,
                id_tecnico, id_proyecto, horas_estimadas
            ) VALUES ($1, $2, 'BUILD', $3, $4, $5, $6, $7)
        """,
            kan_id, f"Tarea half {i+1}",
            random.choice(['Alta', 'Media', 'Baja']),
            random.choice(columnas_validas),
            random.choice(tecnicos)['id_recurso'],
            id_proj,
            random.randint(2, 12),
        )

    estados_validos = ['QUEUED', 'EN_CURSO', 'RESUELTO']
    for i in range(8):
        ticket = f"INC-{i+1:03d}"
        proj_idx = i % 20
        id_proj = f"PRJ-{proj_idx+1:03d}"
        await conn.execute("""
            INSERT INTO incidencias_run (
                ticket_id, incidencia_detectada, prioridad_ia, estado,
                tecnico_asignado, id_proyecto
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """,
            ticket, f"Half incidente {i+1}",
            random.choice(['P2', 'P3', 'P4']),
            random.choice(estados_validos),
            random.choice(tecnicos)['id_recurso'],
            id_proj,
        )


async def _seed_overload(conn: asyncpg.Connection) -> None:
    """40 proyectos, 160 kanban (sesgo: 3 hot reciben 120/160), 22 incidencias
    (3 ESCALADO)."""
    pms = await conn.fetch("""
        SELECT p.id_pm, p.nombre, p.id_usuario_rbac
        FROM pmo_project_managers p
        WHERE p.id_pm ~ '^PM-0(1[6-9]|2[0-5])$'
          AND p.id_usuario_rbac IS NOT NULL
        ORDER BY p.id_pm
    """)
    assert len(pms) == 10

    for i in range(40):
        id_proj = f"PRJ-{i+1:03d}"
        pm = pms[i % 10]
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
            f"Scenario Overload Project {i+1:03d}",
            pm['nombre'], pm['id_usuario_rbac'],
            random.choice(['Alta', 'Crítica']),
            'EJECUCION',
            random.randint(30, 70),
            random.randint(2, 8), 16,
            random.randint(300000, 900000),
            random.randint(50000, 200000),
            round(random.uniform(0.5, 0.9), 2),
            'G3-EJECUCION',
            random.choice(['IT-CLOUD', 'IT-APPS', 'IT-DATA', 'IT-SEGURIDAD']),
            False,
        )

    # Sesgo: 3 técnicos hot reciben 40 kanban cada uno (120 de 160).
    # Los otros 40 kanban se reparten entre 20 técnicos cualesquiera.
    tecnicos = await _pick_least_loaded_tecnicos(conn, 23)
    hot_tecnicos  = tecnicos[:3]
    cold_tecnicos = tecnicos[3:]

    columnas_validas = ['Backlog', 'Análisis', 'En Progreso', 'Code Review', 'Testing']

    for i in range(160):
        kan_id = f"KAN-{i+1:04d}"
        proj_idx = i % 40
        id_proj = f"PRJ-{proj_idx+1:03d}"
        if i < 120:
            tec = hot_tecnicos[i % 3]
        else:
            tec = random.choice(cold_tecnicos)
        await conn.execute("""
            INSERT INTO kanban_tareas (
                id, titulo, tipo, prioridad, columna,
                id_tecnico, id_proyecto, horas_estimadas
            ) VALUES ($1, $2, 'BUILD', $3, $4, $5, $6, $7)
        """,
            kan_id, f"Tarea overload {i+1}",
            random.choice(['Alta', 'Crítica']),
            random.choice(columnas_validas),
            tec['id_recurso'],
            id_proj,
            random.randint(8, 16),
        )

    # 22 incidencias: 3 con estado 'ESCALADO', 19 con QUEUED/EN_CURSO/RESUELTO
    estados_normales = ['QUEUED', 'EN_CURSO', 'RESUELTO']
    for i in range(22):
        ticket = f"INC-{i+1:03d}"
        proj_idx = i % 40
        id_proj = f"PRJ-{proj_idx+1:03d}"
        estado = 'ESCALADO' if i < 3 else random.choice(estados_normales)
        await conn.execute("""
            INSERT INTO incidencias_run (
                ticket_id, incidencia_detectada, prioridad_ia, estado,
                tecnico_asignado, id_proyecto
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """,
            ticket, f"Overload incidente {i+1}",
            random.choice(['P1', 'P2', 'P3']),
            estado,
            random.choice(tecnicos)['id_recurso'],
            id_proj,
        )


_SEED_FUNCS = {
    "empty":    _seed_empty,
    "half":     _seed_half,
    "optimal":  _seed_optimal,
    "overload": _seed_overload,
}


async def seed_scenario(
    conn: asyncpg.Connection,
    scenario_name: str,
    profile: str = "optimal",
) -> dict:
    """Puebla el esquema destino con el perfil pedido.

    Si el esquema no existe, lo crea vía compartido.crear_esquema_escenario.
    Antes de seedear, hace reset_scenario(scenario_name) para garantizar
    estado vacío. Toda la operación va dentro de una transacción explícita
    con SET LOCAL search_path al esquema destino.

    Devuelve dict con scenario, profile, schema_created y counts esperados.
    """
    _validate(scenario_name, profile)
    creado = await _ensure_schema_exists(conn, scenario_name)
    random.seed(42)

    n_proj, n_kan, n_inc = PROFILE_COUNTS[profile]

    async with conn.transaction():
        await conn.execute(
            f"SET LOCAL search_path = {scenario_name}, compartido, public"
        )
        # Limpiar estado del esquema antes de seedear (idempotencia)
        await conn.execute("DELETE FROM kanban_tareas")
        await conn.execute("DELETE FROM incidencias_run")
        await conn.execute("DELETE FROM build_live")

        await _SEED_FUNCS[profile](conn)

    return {
        "scenario": scenario_name,
        "profile": profile,
        "schema_created": creado,
        "counts_expected": {
            "proyectos": n_proj,
            "kanban": n_kan,
            "incidencias": n_inc,
        },
    }


async def reset_scenario(conn: asyncpg.Connection, scenario_name: str) -> None:
    """Limpia un escenario completo: DROP SCHEMA CASCADE + recreación vacía.

    primitiva NUNCA se toca: raise ValueError.
    """
    if scenario_name == PRIMITIVA:
        raise ValueError(
            "reset_scenario no puede tocar primitiva. "
            "primitiva es canon inmutable."
        )
    if scenario_name not in SCENARIOS_VALIDOS:
        raise ValueError(
            f"scenario_name inválido: {scenario_name!r}. "
            f"Válidos: {sorted(SCENARIOS_VALIDOS)}"
        )

    await conn.execute(f'DROP SCHEMA IF EXISTS "{scenario_name}" CASCADE')
    await conn.execute(
        "SELECT compartido.crear_esquema_escenario($1)",
        scenario_name,
    )

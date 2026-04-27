#!/usr/bin/env python3
"""Seed de imputaciones realistas 12 semanas en primitiva.horas_imputadas.

- Ventana: 2026-01-22 (lunes W04) → 2026-04-15 (miércoles W16)
- Scope: primitiva.cartera_build estado NOT IN ('cerrado','Standby')
- Pool: compartido.rbac_usuarios role TECH_* activos con id_recurso (FTE-XXX)
- Match: preferir silo del perfil_requerido; rellenar con otros
- Grain: 1 registro por técnico-proyecto-día L-V (5 días/semana)
- Horas semanales: normal µ=20 σ=8 clip [4,38] → repartidas 5 días (~4h/día + jitter)
- Rojos: ~15% técnicos sobrecargados (multi-proyecto), ~10% proyectos con 4+ técnicos
- Idempotente: DELETE ventana antes de INSERT. random.seed(42)
"""
import os
import random
import datetime as dt
from collections import defaultdict

import psycopg2
from psycopg2.extras import execute_values


random.seed(42)

WINDOW_START = dt.date(2026, 1, 22)   # Jueves — ajusto al lunes
WINDOW_START = WINDOW_START - dt.timedelta(days=WINDOW_START.weekday())  # lunes 2026-01-19
WINDOW_END   = dt.date(2026, 4, 15)

DSN = dict(
    host=os.getenv("DB_HOST", "postgres"),
    port=int(os.getenv("DB_PORT", 5432)),
    dbname=os.getenv("DB_NAME", "cognitive_pmo"),
    user=os.getenv("DB_USER", "pmo_admin"),
    password=os.getenv("DB_PASSWORD", ""),
)

SILO_KEYWORDS = {
    "Backend":  ["backend", "api", "sql", "python", "java", "node"],
    "Frontend": ["frontend", "react", "vue", "angular", "ui"],
    "Redes":    ["redes", "network", "vpn", "port security", "switch", "router", "vlan", "dns"],
    "Windows":  ["windows", "ad ", "dominio", "gpo"],
    "DevOps":   ["devops", "docker", "kubernetes", "cloud", "aws", "azure", "gcp", "ci/cd", "linux"],
    "BBDD":     ["bbdd", "database", "sql:", "oracle", "postgres", "mysql"],
    "Seguridad":["seguridad", "security", "firewall", "siem", "mfa", "pentest"],
    "QA":       ["qa", "testing", "pruebas"],
    "Soporte":  ["soporte", "helpdesk", "hardware"],
}

def detect_silo(perfil: str):
    if not perfil:
        return None
    p = perfil.lower()
    best, hits = None, 0
    for silo, kws in SILO_KEYWORDS.items():
        h = sum(1 for kw in kws if kw in p)
        if h > hits:
            best, hits = silo, h
    return best if hits > 0 else None


def normal_clip(mu, sigma, lo, hi):
    v = random.gauss(mu, sigma)
    return max(lo, min(hi, v))


def iso_week(d: dt.date) -> int:
    return d.isocalendar()[1]


def main():
    conn = psycopg2.connect(**DSN)
    conn.autocommit = False
    cur = conn.cursor()

    # 1. Proyectos objetivo
    cur.execute("""
        SELECT id_proyecto, id_pm_usuario, perfil_requerido
        FROM primitiva.cartera_build
        WHERE id_pm_usuario IS NOT NULL
          AND estado NOT IN ('cerrado','Standby')
        ORDER BY id_proyecto
    """)
    proyectos = cur.fetchall()
    print(f"[recon] {len(proyectos)} proyectos activos")

    # 2. Pool de técnicos
    cur.execute("""
        SELECT u.id_recurso, ps.silo_especialidad, ps.nivel
        FROM compartido.rbac_usuarios u
        JOIN compartido.rbac_roles r ON u.id_role = r.id_role
        LEFT JOIN compartido.pmo_staff_skills ps ON ps.id_recurso = u.id_recurso
        WHERE r.code LIKE 'TECH_%%' AND u.activo = TRUE
          AND u.id_recurso IS NOT NULL AND u.id_recurso <> ''
    """)
    tecnicos = cur.fetchall()
    por_silo = defaultdict(list)
    for fte, silo, _ in tecnicos:
        if silo:
            por_silo[silo].append(fte)
    all_fte = [t[0] for t in tecnicos]
    print(f"[recon] {len(all_fte)} técnicos activos · silos={list(por_silo.keys())}")

    # 3. Asignaciones: por proyecto, [3-6] técnicos, preferir silo match
    #    Rojos: 10% proyectos con 7 técnicos (para generar conflictos multi-PM).
    asignaciones = {}       # id_proyecto -> [fte,...]
    carga_fte_proyectos = defaultdict(set)  # fte -> {id_proyecto,...}
    hot_projects = set(random.sample([p[0] for p in proyectos], max(1, len(proyectos)//10)))
    for id_proj, _pm, perfil in proyectos:
        size = 7 if id_proj in hot_projects else random.randint(3, 6)
        silo = detect_silo(perfil)
        pool_pref = list(por_silo.get(silo, []))
        random.shuffle(pool_pref)
        pool_rest = [f for f in all_fte if f not in pool_pref]
        random.shuffle(pool_rest)
        elegidos = (pool_pref + pool_rest)[:size]
        asignaciones[id_proj] = elegidos
        for f in elegidos:
            carga_fte_proyectos[f].add(id_proj)

    # 4. Sobrecarga: forzar 15% técnicos con µ más alto (µ=28 σ=8 clip[10,42])
    tecnicos_sobrecargados = set(random.sample(all_fte, max(1, len(all_fte)*15//100)))

    # 5. Borrar ventana e insertar
    print(f"[delete] ventana {WINDOW_START}..{WINDOW_END}")
    cur.execute(
        "DELETE FROM primitiva.horas_imputadas WHERE fecha BETWEEN %s AND %s",
        (WINDOW_START, WINDOW_END),
    )
    print(f"[delete] {cur.rowcount} filas previas eliminadas")

    # 6. Generar registros
    rows = []
    days_lv = []
    d = WINDOW_START
    while d <= WINDOW_END:
        if d.weekday() < 5:
            days_lv.append(d)
        d += dt.timedelta(days=1)
    # Agrupar en semanas ISO para distribución
    weeks = defaultdict(list)
    for d in days_lv:
        weeks[(d.isocalendar()[0], d.isocalendar()[1])].append(d)

    # Invertir: por técnico → sus proyectos. Carga TOTAL semanal se reparte.
    fte_to_projects = defaultdict(list)
    for id_proj, ftes in asignaciones.items():
        for f in ftes:
            fte_to_projects[f].append(id_proj)

    for (yr, wk), days_of_week in weeks.items():
        for fte, proj_list in fte_to_projects.items():
            # carga TOTAL semanal del técnico (suma a través de todos sus proyectos)
            if fte in tecnicos_sobrecargados:
                horas_sem_total = normal_clip(45, 6, 38, 58)   # sobrecarga real >40h
            else:
                horas_sem_total = normal_clip(20, 8, 4, 38)
            # Reparto entre proyectos: pesos aleatorios, sin caer en 0
            pesos = [random.uniform(0.5, 1.5) for _ in proj_list]
            total_peso = sum(pesos)
            horas_por_proj = [horas_sem_total * p / total_peso for p in pesos]
            # Cada proyecto a su vez se reparte en los días L-V de la semana con jitter
            for id_proj, h_proj_sem in zip(proj_list, horas_por_proj):
                if h_proj_sem < 0.5:
                    continue
                base = h_proj_sem / len(days_of_week)
                for dia in days_of_week:
                    h = max(0.2, base + random.uniform(-0.6, 0.6))
                    h = round(h, 1)
                    if h >= 0.2:
                        rows.append((id_proj, fte, dia, h, dia.isocalendar()[1]))

    print(f"[gen] {len(rows)} registros generados")

    # 7. Insertar en batches
    execute_values(cur,
        "INSERT INTO primitiva.horas_imputadas (id_proyecto, id_tecnico, fecha, horas, semana_iso) VALUES %s",
        rows, page_size=1000)
    conn.commit()
    print(f"[insert] OK — commit done")

    # 8. Poblar kanban_tareas para que pm_dashboard_team vea el pool
    # Solo PM-016 (Pablo, id=19) tenía tareas pre-existentes; respetarlas.
    # Para el resto de proyectos del seed, generar 2-4 tareas por (tec, proy).
    cur.execute("SELECT id_proyecto FROM primitiva.kanban_tareas GROUP BY id_proyecto")
    proys_con_kanban = {r[0] for r in cur.fetchall()}
    cur.execute("""
        SELECT id_proyecto FROM primitiva.cartera_build
        WHERE id_pm_usuario = 19 AND id_proyecto IN (
            SELECT DISTINCT id_proyecto FROM primitiva.kanban_tareas
        )
    """)
    proys_pablo_intactos = {r[0] for r in cur.fetchall()}

    # Limpiar tareas de proyectos no-Pablo dentro de la ventana del seed
    proys_seed_sin_pablo = [p for p in asignaciones.keys() if p not in proys_pablo_intactos]
    if proys_seed_sin_pablo:
        cur.execute(
            "DELETE FROM primitiva.kanban_tareas WHERE id_proyecto = ANY(%s)",
            (proys_seed_sin_pablo,)
        )
        print(f"[kanban] {cur.rowcount} tareas previas eliminadas (proyectos no-Pablo)")

    # Valores válidos según CHECK constraints reales
    COLUMNAS = ['En Progreso', 'En Progreso', 'En Progreso', 'Code Review', 'Testing',
                'Análisis', 'Backlog', 'Bloqueado', 'Completado']
    TIPOS = ['BUILD', 'BUILD', 'BUILD', 'RUN']
    PRIORIDADES = ['Crítica', 'Alta', 'Alta', 'Media', 'Media', 'Media', 'Baja']
    TITULOS = [
        'Implementar endpoint', 'Revisar PR', 'Fix query lenta', 'Refactor módulo',
        'Testing regresión', 'Config firewall', 'Migrar schema', 'Optimizar índice',
        'Añadir logging', 'Documentar API', 'Deploy PRE', 'Rollback producción',
        'Configurar alertas', 'Revisar logs', 'Análisis impacto',
    ]
    kanban_rows = []
    tid = 1
    # Prefijo único por run para evitar colisiones con seeds previos
    import time as _t
    run_tag = f"S{int(_t.time()) % 100000:05d}"
    for id_proj, ftes in asignaciones.items():
        if id_proj in proys_pablo_intactos:
            continue  # no tocar Pablo
        for fte in ftes:
            n_tareas = random.randint(2, 4)
            for _ in range(n_tareas):
                task_id = f"KT-{run_tag}-{tid:06d}"
                tid += 1
                kanban_rows.append((
                    task_id,
                    random.choice(TITULOS) + f" ({id_proj[:10]})",
                    random.choice(TIPOS),
                    random.choice(PRIORIDADES),
                    random.choice(COLUMNAS),
                    fte,
                    id_proj,
                    round(random.uniform(4, 40), 1),  # horas_estimadas
                ))
    if kanban_rows:
        execute_values(cur,
            "INSERT INTO primitiva.kanban_tareas "
            "(id, titulo, tipo, prioridad, columna, id_tecnico, id_proyecto, horas_estimadas) VALUES %s",
            kanban_rows, page_size=1000)
        conn.commit()
        print(f"[kanban] {len(kanban_rows)} tareas insertadas en {len(proys_seed_sin_pablo)} proyectos")

    # 9. Stats
    cur.execute("""
        SELECT COUNT(*), COUNT(DISTINCT id_tecnico), COUNT(DISTINCT id_proyecto),
               ROUND(AVG(horas)::numeric, 2), ROUND(SUM(horas)::numeric, 0)
        FROM primitiva.horas_imputadas
        WHERE fecha BETWEEN %s AND %s
    """, (WINDOW_START, WINDOW_END))
    n, nt, np_, avg, total = cur.fetchone()
    print(f"\n=== ESTADÍSTICAS FINALES ===")
    print(f"registros_nuevos       : {n}")
    print(f"tecnicos_activos       : {nt}")
    print(f"proyectos_con_actividad: {np_}")
    print(f"horas_avg              : {avg}")
    print(f"horas_total            : {total}")

    cur.execute("""
        SELECT id_tecnico, SUM(horas) AS total, ROUND((SUM(horas)/12.0)::numeric, 1) AS h_sem
        FROM primitiva.horas_imputadas WHERE fecha BETWEEN %s AND %s
        GROUP BY id_tecnico ORDER BY total DESC LIMIT 20
    """, (WINDOW_START, WINDOW_END))
    print("\n=== TOP 20 técnicos por carga 12 semanas ===")
    for fte, total, hsem in cur.fetchall():
        flag = "🔥" if float(hsem) > 40 else ""
        print(f"  {fte}  total={total}h  avg={hsem}h/sem  {flag}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()

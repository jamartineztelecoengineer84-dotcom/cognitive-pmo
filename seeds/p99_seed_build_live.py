#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P99 - Seed build_live por escenario.
Cruza con cartera_build existente para generar proyectos activos
con progreso diferenciado por banco.

Ejecutar en NAS: python3 /root/cognitive-pmo/seeds/p99_seed_build_live.py
"""
import subprocess, random
from datetime import datetime, timedelta

random.seed(99)

DB = {
    "host": "postgres",
    "user": "jose_admin",
    "password": "REDACTED-old-password",
    "dbname": "cognitive_pmo",
}

SCHEMAS = ["sc_norte", "sc_iberico", "sc_litoral"]

SCALE = {
    "sc_norte":   {"label": "Norte",   "factor": 0.6, "prefix": "NOR"},
    "sc_iberico": {"label": "Iberico", "factor": 1.0, "prefix": "IBE"},
    "sc_litoral": {"label": "Litoral", "factor": 1.5, "prefix": "LIT"},
}

SILOS = ["IT-INFRA", "IT-APPS", "IT-SEGURIDAD", "IT-DATA", "IT-CLOUD"]
GATES = ["G1-IDEA", "G2-PLANIFICACION", "G3-EJECUCION", "G4-CIERRE", "G5-OPERACION"]
ESTADOS = ["PLANIFICACION", "EN_EJECUCION", "EN_EJECUCION", "EN_EJECUCION", "CERRADO"]
PMS = [
    "Pablo Rivas", "Carmen Ruiz", "Javier Iglesias",
    "Elena Marin", "Isabel Mora", "Raul Santos",
    "Laura Vega", "Sergio Mateos", "Andres Vela",
]


def psql(sql):
    cmd = [
        "psql",
        "-h", DB["host"], "-U", DB["user"],
        "-d", DB["dbname"], "-t", "-A", "-c", sql,
    ]
    env = {"PGPASSWORD": DB["password"], "PATH": "/usr/bin:/bin:/usr/local/bin"}
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(f"  [ERROR] {r.stderr.strip()}")
    return r.stdout.strip()


def psql_exec(sql):
    cmd = [
        "psql",
        "-h", DB["host"], "-U", DB["user"],
        "-d", DB["dbname"], "-c", sql,
    ]
    env = {"PGPASSWORD": DB["password"], "PATH": "/usr/bin:/bin:/usr/local/bin"}
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(f"  [ERROR] {r.stderr.strip()}")
    return r.returncode == 0


def get_projects(schema):
    rows = psql(
        f"SELECT id_proyecto, nombre_proyecto, prioridad_estrategica "
        f"FROM {schema}.cartera_build ORDER BY id_proyecto LIMIT 100"
    )
    result = []
    for line in rows.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            result.append({
                "id": parts[0].strip(),
                "nombre": parts[1].strip(),
                "prio": parts[2].strip(),
            })
    return result


print("=" * 60)
print("  P99 - Seedeando build_live por escenario")
print("=" * 60)

all_sql = ["BEGIN;"]

for sc in SCHEMAS:
    s = SCALE[sc]
    f = s["factor"]
    px = s["prefix"]
    label = s["label"]
    print(f"\n-- {sc} ({label}) --")

    projects = get_projects(sc)
    print(f"  cartera_build tiene {len(projects)} proyectos")

    # Activar un subset: Norte=60%, Iberico=70%, Litoral=80%
    n_active = max(5, int(len(projects) * (0.5 + f * 0.2)))
    active = projects[:n_active]

    for i, p in enumerate(active):
        pid = p["id"].replace("'", "''")
        nombre = p["nombre"].replace("'", "''")
        prio = p["prio"]
        pm = random.choice(PMS)
        silo = random.choice(SILOS)

        # Progreso variable por escenario
        gate_idx = min(4, int(random.gauss(2 + f * 0.5, 1)))
        gate_idx = max(0, gate_idx)
        gate = GATES[gate_idx]
        estado = ESTADOS[gate_idx]

        progreso = min(100, max(0, int(gate_idx * 25 + random.randint(-10, 15))))
        total_tareas = int(random.randint(20, 80) * f)
        tareas_comp = int(total_tareas * progreso / 100)
        total_sprints = random.choice([8, 12, 16, 20])
        sprint_actual = max(1, int(total_sprints * progreso / 100))

        bac_val = round(random.uniform(80000, 600000) * f, 2)
        consumido = round(bac_val * progreso / 100 * random.uniform(0.8, 1.3), 2)

        risk = round(random.uniform(5, 40) * f, 1)
        sp_total = int(random.randint(50, 200) * f)
        sp_done = int(sp_total * progreso / 100)
        velocity = round(random.uniform(8, 25) * f, 1)

        inicio = (datetime.now() - timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d")
        fin_prev = (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")

        ai_lead = "true" if random.random() < 0.3 else "false"

        all_sql.append(
            f"INSERT INTO {sc}.build_live "
            f"(id_proyecto, nombre, pm_asignado, prioridad, estado, "
            f"fecha_inicio, fecha_fin_prevista, progreso_pct, "
            f"total_tareas, tareas_completadas, sprint_actual, total_sprints, "
            f"presupuesto_bac, presupuesto_consumido, risk_score, "
            f"gate_actual, story_points_total, story_points_completados, "
            f"velocity_media, silo, ai_lead) "
            f"VALUES ('{pid}', '{nombre}', '{pm}', '{prio}', '{estado}', "
            f"'{inicio}', '{fin_prev}', {progreso}, "
            f"{total_tareas}, {tareas_comp}, {sprint_actual}, {total_sprints}, "
            f"{bac_val}, {consumido}, {risk}, "
            f"'{gate}', {sp_total}, {sp_done}, "
            f"{velocity}, '{silo}', {ai_lead}) "
            f"ON CONFLICT (id_proyecto) DO NOTHING;"
        )

    print(f"  build_live: {n_active} proyectos activos")

all_sql.append("COMMIT;")

print(f"\n-- Ejecutando {len(all_sql)} sentencias SQL... --")

sql_file = "/tmp/p99_seed_build_live.sql"
with open(sql_file, "w") as fout:
    fout.write("\n".join(all_sql))

ok = psql_exec(f"\\i {sql_file}")
if ok:
    print("[OK] Seed build_live completado")
else:
    print("[WARN] Hubo errores")

print("\n" + "=" * 60)
print("  VERIFICACION - build_live por escenario")
print("=" * 60)

for sc in SCHEMAS:
    c = psql(f"SELECT COUNT(*) FROM {sc}.build_live")
    avg_prog = psql(f"SELECT ROUND(AVG(progreso_pct)) FROM {sc}.build_live")
    avg_bac = psql(f"SELECT ROUND(AVG(presupuesto_bac)) FROM {sc}.build_live")
    print(f"  {sc:15s} count={c:>3s}  avg_prog={avg_prog:>3s}%  avg_bac={avg_bac}")

# Confirmar que el endpoint devolvera datos distintos
print("\n-- Test v_p96_build_portfolio --")
for sc in SCHEMAS:
    c = psql(f"SELECT COUNT(*) FROM {sc}.v_p96_build_portfolio")
    print(f"  {sc:15s} portfolio_rows={c}")

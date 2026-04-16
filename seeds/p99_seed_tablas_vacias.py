#!/usr/bin/env python3
"""
P99 — Seedea las 9 tablas vacías prioritarias en los 3 escenarios.
Ejecutar en NAS: python3 /root/cognitive-pmo/seeds/p99_seed_tablas_vacias.py

Lee IDs existentes de incidencias_run, cmdb_activos, cartera_build
para respetar FKs. Genera datos distintos por escenario.
"""
import subprocess, sys, random, json
from datetime import date, timedelta

random.seed(42)  # Reproducible

DB = {
    "host": "postgres",
    "user": "jose_admin",
    "password": "REDACTED-old-password",
    "dbname": "cognitive_pmo",
}

SCHEMAS = ["sc_norte", "sc_iberico", "sc_litoral"]

# Escalas por escenario
SCALE = {
    "sc_norte":   {"label": "Norte",   "factor": 0.6, "prefix": "NOR"},
    "sc_iberico": {"label": "Ibérico", "factor": 1.0, "prefix": "IBE"},
    "sc_litoral": {"label": "Litoral", "factor": 1.5, "prefix": "LIT"},
}


def psql(sql):
    """Ejecuta SQL y devuelve stdout."""
    cmd = [
        "psql",
        "-h", DB["host"],
        "-U", DB["user"],
        "-d", DB["dbname"],
        "-t", "-A", "-c", sql,
    ]
    env = {"PGPASSWORD": DB["password"], "PATH": "/usr/bin:/bin:/usr/local/bin"}
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(f"  [ERROR] {r.stderr.strip()}")
    return r.stdout.strip()


def psql_exec(sql):
    """Ejecuta SQL sin retorno."""
    cmd = [
        "psql",
        "-h", DB["host"],
        "-U", DB["user"],
        "-d", DB["dbname"],
        "-c", sql,
    ]
    env = {"PGPASSWORD": DB["password"], "PATH": "/usr/bin:/bin:/usr/local/bin"}
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(f"  [ERROR] {r.stderr.strip()}")
    return r.returncode == 0


def get_ids(schema, table, col):
    """Lee IDs existentes de una tabla."""
    rows = psql(f"SELECT {col} FROM {schema}.{table} ORDER BY {col} LIMIT 200")
    return [r for r in rows.split("\n") if r.strip()]


# ════════════════════════════════════════════════════════════
print("═══════════════════════════════════════════════════════════════")
print("  P99 — Seedeando tablas vacías por escenario")
print("═══════════════════════════════════════════════════════════════")

all_sql = ["BEGIN;"]

for sc in SCHEMAS:
    s = SCALE[sc]
    f = s["factor"]
    px = s["prefix"]
    print(f"\n── {sc} ({s['label']}) ──")

    # ── Leer IDs existentes para FKs ──
    ticket_ids = get_ids(sc, "incidencias_run", "ticket_id")
    activo_ids = get_ids(sc, "cmdb_activos", "id_activo")
    proyecto_ids = get_ids(sc, "cartera_build", "id_proyecto")
    tecnico_ids = [f"FTE-{i:03d}" for i in range(1, 151)]

    print(f"  tickets={len(ticket_ids)} activos={len(activo_ids)} proyectos={len(proyecto_ids)}")

    # ════════════════════════════════════════════════════════
    # 1. p96_pulse_kpis — 6 KPIs del Pulso Estratégico
    # ════════════════════════════════════════════════════════
    kpis = [
        ("MTTR", "MTTR Medio", f"{max(1, int(4.2 * f))}h {int(12 * f)}m", "horas", "gn" if f < 1 else ("or" if f < 1.3 else "rd"),
         f"SLO: 4h" if f < 1 else "SLO: 4h ⚠️ presión", f"Tiempo medio resolución incidencias. {s['label']}: {'holgura' if f < 1 else 'saturación'}"),
        ("SLA", "Uptime SLA", f"{99.95 - f * 0.1:.2f}%", "%", "gn",
         f"Compromiso 99.9%", f"Disponibilidad servicios críticos banco {s['label']}"),
        ("CPI", "CPI Cartera", f"{1.05 - f * 0.1:.2f}", "ratio", "gn" if f < 1 else "or",
         f"{len(proyecto_ids)} proyectos", f"Cost Performance Index agregado"),
        ("SPI", "SPI Cartera", f"{1.02 - f * 0.08:.2f}", "ratio", "gn" if f < 1 else "or",
         f"{int(len(proyecto_ids) * 0.15)} en retraso", f"Schedule Performance Index agregado"),
        ("RISK", "Risk Score", f"{int(28 * f)}/100", "score", "gn" if f < 1 else ("or" if f < 1.3 else "rd"),
         f"{int(3 * f)} PMs en zona crítica", f"Riesgo agregado cartera {s['label']}"),
        ("ADOP", "Adopción IA", f"{int(72 - f * 5)}%", "%", "gn",
         f"media téc. con copiloto", f"Porcentaje técnicos usando asistente IA"),
    ]
    for k, lb, vl, un, rag, sub, tt in kpis:
        vl_esc = vl.replace("'", "''")
        sub_esc = sub.replace("'", "''")
        tt_esc = tt.replace("'", "''")
        all_sql.append(
            f"INSERT INTO {sc}.p96_pulse_kpis (k, lb, vl, un, rag, sub, tt) "
            f"VALUES ('{k}', '{lb}', '{vl_esc}', '{un}', '{rag}', '{sub_esc}', '{tt_esc}') ON CONFLICT DO NOTHING;"
        )
    print(f"  ✅ p96_pulse_kpis: 6 KPIs")

    # ════════════════════════════════════════════════════════
    # 2. p96_pulse_alerts — alertas estratégicas
    # ════════════════════════════════════════════════════════
    n_alerts = int(3 + f * 4)
    alert_templates = [
        ("rd", "Saturación capacidad cloud", f"Cluster K8s al {int(75*f)}% — threshold 80%", "Sergio Mateos"),
        ("or", "Licencia Oracle próxima a expirar", f"Renovación antes del {(date.today() + timedelta(days=int(30/f))).isoformat()}", "Carmen Ruiz"),
        ("rd", "SLA en riesgo: IT-SEGURIDAD", f"3 incidencias P1 en 72h — downtime acumulado {int(2*f)}h", "Elena Marín"),
        ("or", "Desviación presupuestaria CAPEX", f"EAC supera BAC en {int(8*f)}% — proyecto PRJ-{px}-005", "Pablo Rivas"),
        ("yl", "Rotación equipo Backend", f"{int(2*f)} bajas en 30 días — cobertura al {int(85/f)}%", "Marta Núñez"),
        ("or", "Retraso migración legacy", f"Sprint {int(4*f)} sin cerrar — bloqueo integración", "Laura Vega"),
        ("rd", "Brecha compliance PCI-DSS", f"{int(3*f)} controles pendientes — auditoría en {int(15/f)} días", "Elena Marín"),
        ("yl", "Degradación rendimiento DW", f"Queries > {int(5*f)}s en hora punta — impacto reporting", "Isabel Mora"),
    ]
    for i, (sev, title, desc, ow) in enumerate(alert_templates[:n_alerts]):
        desc_esc = desc.replace("'", "''")
        all_sql.append(
            f"INSERT INTO {sc}.p96_pulse_alerts (id, sev, title, descripcion, meta, ow) "
            f"VALUES ('ALR-{px}-{i+1:03d}', '{sev}', '{title}', '{desc_esc}', '{{}}', '{ow}') ON CONFLICT DO NOTHING;"
        )
    print(f"  ✅ p96_pulse_alerts: {n_alerts}")

    # ════════════════════════════════════════════════════════
    # 3. p96_pulse_blocks — bloqueos activos
    # ════════════════════════════════════════════════════════
    n_blocks = int(2 + f * 3)
    block_templates = [
        ("rd", "Proveedor no entrega hardware", f"PRJ-{px}-002", "Javier Iglesias", int(15 * f)),
        ("or", "Aprobación CAB pendiente", f"PRJ-{px}-008", "Raúl Santos", int(8 * f)),
        ("rd", "Integración API terceros bloqueada", f"PRJ-{px}-003", "Andrés Vela", int(22 * f)),
        ("or", "Certificación seguridad retrasada", f"PRJ-{px}-005", "Elena Marín", int(12 * f)),
        ("yl", "Dependencia con equipo externo", f"PRJ-{px}-010", "Marta Núñez", int(5 * f)),
        ("rd", "Licencia expirada bloquea despliegue", f"PRJ-{px}-007", "Carmen Ruiz", int(18 * f)),
        ("or", "Migración datos incompleta", f"PRJ-{px}-012", "Isabel Mora", int(10 * f)),
    ]
    for i, (sev, title, pj, own, days) in enumerate(block_templates[:n_blocks]):
        all_sql.append(
            f"INSERT INTO {sc}.p96_pulse_blocks (id, sev, title, descripcion, pj, own, days) "
            f"VALUES ('BLK-{px}-{i+1:03d}', '{sev}', '{title}', 'Bloqueo activo — impacto en timeline', '{pj}', '{own}', {days}) ON CONFLICT DO NOTHING;"
        )
    print(f"  ✅ p96_pulse_blocks: {n_blocks}")

    # ════════════════════════════════════════════════════════
    # 4. p96_pulse_decisions — decisiones pendientes comité
    # ════════════════════════════════════════════════════════
    n_dec = int(2 + f * 3)
    dec_templates = [
        ("Aprobar ampliación cloud", "Raúl Santos", f"{int(120*f)}k€", 7, "alta"),
        ("Renovar licencia Oracle", "Carmen Ruiz", f"{int(200*f)}k€", 14, "crítica"),
        ("Contratar 3 FTEs Backend", "Marta Núñez", f"{int(45*f)}k€/año", 21, "media"),
        ("Migrar a Azure vs AWS", "Sergio Mateos", f"{int(500*f)}k€", 30, "alta"),
        ("Externalizar SOC nocturno", "Elena Marín", f"{int(80*f)}k€/año", 10, "alta"),
        ("Cancelar proyecto PRJ-008", "Pablo Rivas", f"-{int(150*f)}k€", 5, "crítica"),
        ("Ampliar ventana CAB", "Raúl Santos", "0€", 3, "media"),
    ]
    for i, (title, own, amt, days_due, urg) in enumerate(dec_templates[:n_dec]):
        due = (date.today() + timedelta(days=days_due)).isoformat()
        all_sql.append(
            f"INSERT INTO {sc}.p96_pulse_decisions (id, title, descripcion, own, amt, due, urg) "
            f"VALUES ('DEC-{px}-{i+1:03d}', '{title}', 'Decisión pendiente comité dirección', '{own}', '{amt}', '{due}', '{urg}') ON CONFLICT DO NOTHING;"
        )
    print(f"  ✅ p96_pulse_decisions: {n_dec}")

    # ════════════════════════════════════════════════════════
    # 5. p96_pulse_responsables — responsables por departamento
    # ════════════════════════════════════════════════════════
    responsables = [
        ("Pablo Rivas", "PMO Senior", "cross", "PR", f"{1.02-f*0.05:.2f}", "CPI Cartera", "gn" if f < 1 else "or"),
        ("Javier Iglesias", "Director Infra", "IT-INFRA", "JI", f"{99.9-f*0.1:.1f}%", "SLA Infra", "gn"),
        ("Elena Marín", "Director Sec", "IT-SEGURIDAD", "EM", f"{int(3*f)}", "Incidencias P1", "gn" if f < 1 else "rd"),
        ("Raúl Santos", "VP Ops", "CROSS", "RS", f"{int(35*f)}/100", "Risk Score", "gn" if f < 1 else "or"),
        ("Carmen Ruiz", "Director Apps", "IT-APPS", "CR", f"{int(85-f*10)}%", "Adopción IA", "gn"),
        ("Isabel Mora", "PMO Data", "IT-DATA", "IM", f"{0.98-f*0.05:.2f}", "SPI Data", "gn" if f < 1 else "or"),
    ]
    for nm, rl, ct, ini, kpi_vl, kpi_lb, lg in responsables:
        all_sql.append(
            f"INSERT INTO {sc}.p96_pulse_responsables (nm, rl, ct, ini, kpi_vl, kpi_lb, lg) "
            f"VALUES ('{nm}', '{rl}', '{ct}', '{ini}', '{kpi_vl}', '{kpi_lb}', '{lg}');"
        )
    print(f"  ✅ p96_pulse_responsables: {len(responsables)}")

    # ════════════════════════════════════════════════════════
    # 6. p96_pulse_hitos — hitos próximas 4 semanas
    # ════════════════════════════════════════════════════════
    n_hitos = int(3 + f * 4)
    hito_templates = [
        ("S+1", "Go-live módulo reporting", "DEPLOY", "Pablo Rivas"),
        ("S+1", "Auditoría PCI-DSS", "AUDIT", "Elena Marín"),
        ("S+2", "Cierre sprint backbone", "BUILD", "Javier Iglesias"),
        ("S+2", "Demo comité cloud", "REVIEW", "Sergio Mateos"),
        ("S+3", "Entrega piloto IA", "DEPLOY", "Carmen Ruiz"),
        ("S+3", "Renovación licencias Q2", "ADMIN", "Raúl Santos"),
        ("S+4", "Migración DW fase 2", "BUILD", "Isabel Mora"),
        ("S+4", "Revisión presupuestaria H1", "FINANCE", "Pablo Rivas"),
    ]
    for i, (wk, title, tg, tgt) in enumerate(hito_templates[:n_hitos]):
        dt = (date.today() + timedelta(days=7*(i//2+1))).isoformat()
        all_sql.append(
            f"INSERT INTO {sc}.p96_pulse_hitos (dt, wk, title, descripcion, tg, tgt) "
            f"VALUES ('{dt}', '{wk}', '{title}', 'Hito planificado — banco {s['label']}', '{tg}', '{tgt}');"
        )
    print(f"  ✅ p96_pulse_hitos: {n_hitos}")

    # ════════════════════════════════════════════════════════
    # 7. p96_build_project_detail — detalle de gates por proyecto
    # ════════════════════════════════════════════════════════
    n_detail = min(len(proyecto_ids), int(10 * f))
    for pid in proyecto_ids[:n_detail]:
        gates = json.dumps({
            f"G{g}": {
                "status": random.choice(["PASSED", "PASSED", "PENDING", "BLOCKED"]) if g < 4 else "PENDING",
                "date": (date.today() - timedelta(days=random.randint(5, 60))).isoformat() if g < 3 else None,
            }
            for g in range(6)
        })
        team_json = json.dumps([
            {"id": random.choice(tecnico_ids), "role": random.choice(["DEV", "QA", "ARCH", "PM"])}
            for _ in range(random.randint(2, 6))
        ])
        risks_json = json.dumps([
            {"desc": random.choice(["Retraso proveedor", "Falta recursos", "Cambio scope", "Integración compleja"]),
             "prob": random.choice(["ALTA", "MEDIA", "BAJA"]),
             "impact": random.choice(["ALTO", "MEDIO", "BAJO"])}
            for _ in range(random.randint(1, 4))
        ])
        pid_esc = pid.replace("'", "''")
        all_sql.append(
            f"INSERT INTO {sc}.p96_build_project_detail (id_proyecto, gates, team, risks) "
            f"VALUES ('{pid_esc}', '{gates}'::jsonb, '{team_json}'::jsonb, '{risks_json}'::jsonb) ON CONFLICT DO NOTHING;"
        )
    print(f"  ✅ p96_build_project_detail: {n_detail}")

    # ════════════════════════════════════════════════════════
    # 8. cmdb_costes — costes por activo
    # ════════════════════════════════════════════════════════
    if activo_ids:
        n_costes = min(len(activo_ids), int(30 * f))
        categorias = ["HARDWARE", "SOFTWARE", "CLOUD", "LICENCIAS", "MANTENIMIENTO", "SOPORTE", "CONSULTORIA"]
        for i in range(n_costes):
            aid = activo_ids[i % len(activo_ids)]
            cat = random.choice(categorias)
            tipo = random.choice(["CAPEX", "OPEX"])
            importe = round(random.uniform(500, 15000) * f, 2)
            prov = random.choice(["Microsoft", "Oracle", "Red Hat", "VMware", "Cisco", "AWS", "Fortinet", "Dell"])
            all_sql.append(
                f"INSERT INTO {sc}.cmdb_costes (id_activo, concepto, categoria, tipo, importe, proveedor, centro_coste) "
                f"VALUES ({aid}, '{cat} - {prov} {s['label']}', '{cat}', '{tipo}', {importe}, '{prov}', 'CC-{px}-{(i%5)+1:02d}');"
            )
        print(f"  ✅ cmdb_costes: {n_costes}")
    else:
        print(f"  ⚠️ cmdb_costes: sin activos para FK")

    # ════════════════════════════════════════════════════════
    # 9. kanban_tareas — tareas derivadas de incidencias
    # ════════════════════════════════════════════════════════
    columnas = ["Backlog", "Análisis", "En Progreso", "Code Review", "Testing", "Despliegue", "Completado"]
    col_weights = [0.10, 0.10, 0.25, 0.15, 0.15, 0.10, 0.15]
    n_tareas = int(15 + f * 20)

    for i in range(n_tareas):
        tid = f"KAN-{px}-{i+1:04d}"
        tipo = random.choice(["RUN", "RUN", "BUILD"])
        prioridad = random.choices(["Crítica", "Alta", "Media", "Baja"], weights=[0.1, 0.25, 0.4, 0.25])[0]
        col = random.choices(columnas, weights=col_weights)[0]
        tec = random.choice(tecnico_ids[:int(50 * f)])  # Más técnicos en bancos grandes
        inc_ref = random.choice(ticket_ids) if ticket_ids and tipo == "RUN" else None
        proj_ref = random.choice(proyecto_ids) if proyecto_ids and tipo == "BUILD" else None

        titulo = random.choice([
            f"Resolver incidencia {inc_ref or 'pendiente'}",
            f"Desplegar parche seguridad {px}",
            f"Revisar configuración firewall",
            f"Actualizar firmware switches",
            f"Migrar VM a nuevo cluster",
            f"Optimizar query reporting",
            f"Documentar runbook {px}-{i+1}",
            f"Testing integración API {px}",
            f"Backup verificación mensual",
            f"Capacidad storage review",
        ])
        titulo_esc = titulo.replace("'", "''")

        horas_est = round(random.uniform(1, 24), 1)
        horas_real = round(horas_est * random.uniform(0.5, 1.5), 1) if col in ("Completado", "Testing", "Despliegue") else 0

        inc_sql = f"'{inc_ref}'" if inc_ref else "NULL"
        proj_sql = f"'{proj_ref}'" if proj_ref else "NULL"

        all_sql.append(
            f"INSERT INTO {sc}.kanban_tareas (id, titulo, tipo, prioridad, columna, id_tecnico, id_proyecto, id_incidencia, horas_estimadas, horas_reales) "
            f"VALUES ('{tid}', '{titulo_esc}', '{tipo}', '{prioridad}', '{col}', '{tec}', {proj_sql}, {inc_sql}, {horas_est}, {horas_real}) ON CONFLICT DO NOTHING;"
        )
    print(f"  ✅ kanban_tareas: {n_tareas}")

all_sql.append("COMMIT;")

# ════════════════════════════════════════════════════════════
# EJECUTAR
# ════════════════════════════════════════════════════════════
print(f"\n── Ejecutando {len(all_sql)} sentencias SQL... ──")

full_sql = "\n".join(all_sql)

# Guardar a archivo temporal y ejecutar
sql_file = "/tmp/p99_seed_vacias.sql"
with open(sql_file, "w") as f:
    f.write(full_sql)

ok = psql_exec(f"\\i {sql_file}")

if ok:
    print("[OK] Seed completado")
else:
    print("[WARN] Hubo errores — revisar arriba")

# ════════════════════════════════════════════════════════════
# VERIFICACIÓN
# ════════════════════════════════════════════════════════════
print("\n═══════════════════════════════════════════════════════════════")
print("  VERIFICACIÓN — Conteos por escenario")
print("═══════════════════════════════════════════════════════════════")

tables = [
    "p96_pulse_kpis", "p96_pulse_alerts", "p96_pulse_blocks",
    "p96_pulse_decisions", "p96_pulse_responsables", "p96_pulse_hitos",
    "p96_build_project_detail", "cmdb_costes", "kanban_tareas"
]

for t in tables:
    counts = []
    for sc in SCHEMAS:
        c = psql(f"SELECT COUNT(*) FROM {sc}.{t}")
        counts.append(c)
    different = len(set(counts)) > 1
    status = "✅" if different else ("⚠️" if all(c == "0" for c in counts) else "🔒")
    print(f"  {status} {t:35s} N={counts[0]:>4s}  I={counts[1]:>4s}  L={counts[2]:>4s}")

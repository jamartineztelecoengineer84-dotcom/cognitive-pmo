#!/usr/bin/env python3
"""
P98 SEED PRIMITIVA — Datos demo PM Dashboard para PM-016
=========================================================
S1: Asignar 12 proyectos a PM-016
S2: Diversidad EVM (4 perfiles narrativos)
S3: Reasignar kanban_tareas a esos 12 proyectos
S4: Crear horas_imputadas + seed 200 registros
S5: Ajustar endpoint A1 si necesario

Uso: python3 p98_seed_primitiva_pm.py 2>&1 | tee /tmp/p98_seed_primitiva.log
"""
import subprocess, os, random, json
from datetime import date, timedelta

random.seed(42)

PM_ID = 'PM-016'
PM_NOMBRE = 'Pablo Rivas Camacho'

def psql(query, schema='primitiva'):
    full = f"SET search_path = {schema}, compartido, public; {query}" if schema else query
    env = os.environ.copy()
    env['PGPASSWORD'] = 'Seacaboelabuso_0406'
    r = subprocess.run(['psql', '-h', 'localhost', '-U', 'jose_admin', '-d', 'cognitive_pmo',
                        '-t', '-A', '-c', full], capture_output=True, text=True, timeout=30, env=env)
    out = r.stdout.strip()
    if out.startswith('SET\n'):
        out = out[4:]
    elif out == 'SET':
        out = ''
    return out

def psql_exec(query, schema='primitiva'):
    full = f"SET search_path = {schema}, compartido, public; {query}" if schema else query
    env = os.environ.copy()
    env['PGPASSWORD'] = 'Seacaboelabuso_0406'
    r = subprocess.run(['psql', '-h', 'localhost', '-U', 'jose_admin', '-d', 'cognitive_pmo',
                        '-c', full], capture_output=True, text=True, timeout=30, env=env)
    if r.returncode != 0:
        err = r.stderr[:300].strip()
        if err:
            print(f'    ERR: {err}')
        return False
    return True

print('=' * 66)
print('P98 SEED PRIMITIVA — PM Dashboard Demo Data')
print('=' * 66)

# ═══════════════════════════════════════════════════════════════
# S1: Asignar 12 proyectos a PM-016
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('S1: Asignar 12 proyectos a PM-016')
print('═' * 66)

# Add column if needed
psql_exec("ALTER TABLE cartera_build ADD COLUMN IF NOT EXISTS id_pm_usuario VARCHAR(20)")
psql_exec("ALTER TABLE cartera_build ADD COLUMN IF NOT EXISTS ac NUMERIC(12,2)")
psql_exec("ALTER TABLE cartera_build ADD COLUMN IF NOT EXISTS pct_avance INT DEFAULT 0")
psql_exec("ALTER TABLE cartera_build ADD COLUMN IF NOT EXISTS fecha_fin_plan DATE")
psql_exec("ALTER TABLE cartera_build ADD COLUMN IF NOT EXISTS fecha_inicio DATE")
print('  Columnas añadidas/verificadas')

# Get 10 en ejecucion + promote 2 more
en_ejec = psql("SELECT id_proyecto FROM cartera_build WHERE estado='en ejecucion' ORDER BY id_proyecto LIMIT 10")
projects_10 = [p.strip() for p in en_ejec.split('\n') if p.strip()]

# Promote 2 more to en ejecucion
otros = psql("SELECT id_proyecto FROM cartera_build WHERE estado NOT IN ('cerrado','en ejecucion') ORDER BY id_proyecto LIMIT 2")
extras = [p.strip() for p in otros.split('\n') if p.strip()]
for prj in extras:
    psql_exec(f"UPDATE cartera_build SET estado='en ejecucion' WHERE id_proyecto='{prj}'")

all_12 = projects_10 + extras
print(f'  12 proyectos seleccionados: {len(all_12)}')

# Assign PM-016
for prj in all_12:
    psql_exec(f"UPDATE cartera_build SET id_pm_usuario='{PM_ID}' WHERE id_proyecto='{prj}'")

count = psql(f"SELECT COUNT(*) FROM cartera_build WHERE id_pm_usuario='{PM_ID}'")
print(f'  Proyectos asignados a {PM_ID}: {count}')

# Also update governance_scoring to link these to PM-016
for prj in all_12:
    psql_exec(f"UPDATE pmo_governance_scoring SET id_pm='{PM_ID}' WHERE id_proyecto='{prj}'")

for p in all_12:
    print(f'    {p}')

# ═══════════════════════════════════════════════════════════════
# S2: Diversidad EVM — 4 perfiles narrativos
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('S2: Diversidad EVM — 4 perfiles')
print('═' * 66)

today = date.today()

# Get BAC for each project
bacs = {}
for prj in all_12:
    bac_raw = psql(f"SELECT bac_total FROM presupuestos WHERE id_proyecto='{prj}' ORDER BY version DESC LIMIT 1")
    bacs[prj] = float(bac_raw) if bac_raw else 150000.0

# Profile assignments
profiles = {
    'A_verde': all_12[0:3],      # 3 projects — green
    'B_ambar': all_12[3:7],      # 4 projects — amber
    'C_rojo':  all_12[7:10],     # 3 projects — red
    'D_atrasado_barato': all_12[10:12],  # 2 projects — late but cheap
}

profile_params = {
    'A_verde': {
        'pct_avance': (60, 75),
        'fecha_fin_offset': (170, 260),  # days from today
        'fecha_inicio_offset': (-200, -150),  # days before today
        'ac_factor': (0.50, 0.58),  # AC = factor × BAC → CPI ≈ avance/factor ≈ 1.05-1.15
    },
    'B_ambar': {
        'pct_avance': (40, 55),
        'fecha_fin_offset': (90, 140),
        'fecha_inicio_offset': (-180, -120),
        'ac_factor': (0.45, 0.58),  # CPI ≈ 0.90-0.99
    },
    'C_rojo': {
        'pct_avance': (25, 40),
        'fecha_fin_offset': (45, 90),
        'fecha_inicio_offset': (-240, -180),
        'ac_factor': (0.55, 0.70),  # CPI ≈ 0.45-0.65
    },
    'D_atrasado_barato': {
        'pct_avance': (30, 45),
        'fecha_fin_offset': (60, 105),
        'fecha_inicio_offset': (-300, -200),
        'ac_factor': (0.25, 0.35),  # CPI good, SPI bad
    },
}

for profile_name, prj_list in profiles.items():
    params = profile_params[profile_name]
    print(f'\n  Perfil {profile_name}: {len(prj_list)} proyectos')

    for prj in prj_list:
        bac = bacs.get(prj, 150000)
        pct = random.randint(*params['pct_avance'])
        fin_off = random.randint(*params['fecha_fin_offset'])
        ini_off = random.randint(*params['fecha_inicio_offset'])
        ac_f = round(random.uniform(*params['ac_factor']), 3)

        fecha_inicio = today + timedelta(days=ini_off)
        fecha_fin = today + timedelta(days=fin_off)
        ac = round(bac * ac_f, 2)

        # Calculate expected CPI for logging
        ev = bac * (pct / 100)
        cpi = round(ev / ac, 2) if ac > 0 else 0

        sql = f"""UPDATE cartera_build SET
            pct_avance = {pct},
            fecha_inicio = '{fecha_inicio}',
            fecha_fin_plan = '{fecha_fin}',
            ac = {ac}
            WHERE id_proyecto = '{prj}'"""
        psql_exec(sql)
        print(f'    {prj}: avance={pct}%, BAC={bac:,.0f}, AC={ac:,.0f}, CPI≈{cpi}')

# ═══════════════════════════════════════════════════════════════
# S3: Reasignar kanban_tareas a los 12 proyectos
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('S3: Reasignar kanban_tareas a 12 proyectos')
print('═' * 66)

# Get all kanban tasks with technicians
all_kan = psql("SELECT id FROM kanban_tareas WHERE id_tecnico IS NOT NULL ORDER BY random() LIMIT 72")
kan_ids = [k.strip() for k in all_kan.split('\n') if k.strip()]
print(f'  {len(kan_ids)} tareas disponibles para reasignar')

# Distribute ~6 per project
idx = 0
for i, prj in enumerate(all_12):
    n_tasks = 6 if i < 8 else 5  # 8×6 + 4×5 = 68
    chunk = kan_ids[idx:idx+n_tasks]
    idx += n_tasks
    if not chunk:
        break
    ids_str = ','.join(f"'{k}'" for k in chunk)
    psql_exec(f"UPDATE kanban_tareas SET id_proyecto='{prj}' WHERE id IN ({ids_str})")

# Also make some tasks active (not all Completado)
columnas_activas = ['Análisis', 'En Progreso', 'Code Review', 'Testing', 'Despliegue']
for prj in all_12:
    # Set ~60% of tasks to active columns
    tasks = psql(f"SELECT id FROM kanban_tareas WHERE id_proyecto='{prj}' ORDER BY random()")
    task_ids = [t.strip() for t in tasks.split('\n') if t.strip()]
    n_active = max(2, int(len(task_ids) * 0.6))
    for j, tid in enumerate(task_ids):
        if j < n_active:
            col = random.choice(columnas_activas)
            psql_exec(f"UPDATE kanban_tareas SET columna='{col}' WHERE id='{tid}'")

# Verify
print('\n  Distribución:')
for prj in all_12:
    stats = psql(f"SELECT COUNT(DISTINCT id_tecnico), COUNT(*) FROM kanban_tareas WHERE id_proyecto='{prj}'")
    if stats:
        parts = stats.split('|')
        print(f'    {prj}: {parts[0]} técnicos, {parts[1]} tareas')

# ═══════════════════════════════════════════════════════════════
# S4: Horas imputadas — últimas 4 semanas
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('S4: Crear tabla horas_imputadas + seed')
print('═' * 66)

psql_exec("""
CREATE TABLE IF NOT EXISTS primitiva.horas_imputadas (
    id SERIAL PRIMARY KEY,
    id_proyecto VARCHAR(80),
    id_tecnico VARCHAR(20),
    fecha DATE NOT NULL,
    horas NUMERIC(4,1) NOT NULL,
    semana_iso INT,
    created_at TIMESTAMP DEFAULT NOW()
)
""", schema=None)
print('  Tabla horas_imputadas creada/verificada')

# Clear old demo data
psql_exec("DELETE FROM primitiva.horas_imputadas WHERE id_proyecto IN (" +
          ','.join(f"'{p}'" for p in all_12) + ")", schema=None)

# For each project, get assigned technicians and create 4 weeks of data
total_inserted = 0
for prj in all_12:
    techs = psql(f"SELECT DISTINCT id_tecnico FROM kanban_tareas WHERE id_proyecto='{prj}' AND id_tecnico IS NOT NULL")
    tech_list = [t.strip() for t in techs.split('\n') if t.strip()]
    if not tech_list:
        continue

    for week_offset in range(4):
        # Monday of the week
        week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=week_offset)
        for tech in tech_list:
            # 3-5 work days per week, 4-10 hours per day
            n_days = random.randint(3, 5)
            for d in range(n_days):
                work_date = week_start + timedelta(days=d)
                hours = round(random.uniform(4, 10), 1)
                iso_week = work_date.isocalendar()[1]
                sql = f"""INSERT INTO primitiva.horas_imputadas
                    (id_proyecto, id_tecnico, fecha, horas, semana_iso)
                    VALUES ('{prj}', '{tech}', '{work_date}', {hours}, {iso_week})"""
                ok = psql_exec(sql, schema=None)
                if ok:
                    total_inserted += 1

print(f'  {total_inserted} registros de horas insertados')

# Verify
for prj in all_12[:3]:
    stats = psql(f"SELECT COUNT(*), SUM(horas), COUNT(DISTINCT id_tecnico) FROM primitiva.horas_imputadas WHERE id_proyecto='{prj}'", schema=None)
    print(f'    {prj}: {stats}')

# ═══════════════════════════════════════════════════════════════
# S5: Ajustar endpoint A1 para leer datos reales
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('S5: Ajustar endpoint A1 para datos reales')
print('═' * 66)

MAIN_PY = '/root/cognitive-pmo/backend/main.py'
with open(MAIN_PY, 'r') as f:
    code = f.read()

changes = 0

# Fix 1: Use real pct_avance and ac from cartera_build if available
old_avance = """            # Kanban progress for real % avance
            total_tasks = await conn.fetchval(
                "SELECT COUNT(*) FROM kanban_tareas WHERE id_proyecto = $1", id_proyecto) or 0
            done_tasks = await conn.fetchval(
                "SELECT COUNT(*) FROM kanban_tareas WHERE id_proyecto = $1 "
                "AND columna IN ('Completado','Done')", id_proyecto) or 0
            pct_avance = done_tasks / max(total_tasks, 1)"""

new_avance = """            # Real pct_avance from cartera_build, fallback to kanban
            db_avance = prj_d.get('pct_avance')
            if db_avance and int(db_avance) > 0:
                pct_avance = int(db_avance) / 100
            else:
                total_tasks = await conn.fetchval(
                    "SELECT COUNT(*) FROM kanban_tareas WHERE id_proyecto = $1", id_proyecto) or 0
                done_tasks = await conn.fetchval(
                    "SELECT COUNT(*) FROM kanban_tareas WHERE id_proyecto = $1 "
                    "AND columna IN ('Completado','Done')", id_proyecto) or 0
                pct_avance = done_tasks / max(total_tasks, 1)"""

if old_avance in code:
    code = code.replace(old_avance, new_avance, 1)
    changes += 1
    print('  OK: pct_avance lee de cartera_build primero')

# Fix 2: Use real AC from cartera_build if available
old_ac = """            # SINTETICO: EVM calculations
            pv = round(bac * pct_time, 2)
            ev = round(bac * pct_avance, 2)
            # AC = EV + small variance (simulating cost deviation)
            seed_val = int(hashlib.md5(id_proyecto.encode()).hexdigest()[:8], 16) % 100
            cost_factor = 0.85 + (seed_val / 100) * 0.3  # 0.85 to 1.15
            ac = round(ev * cost_factor, 2) if ev > 0 else round(pv * 0.3, 2)"""

new_ac = """            # EVM calculations — use real AC if available, else synthetic
            pv = round(bac * pct_time, 2)
            ev = round(bac * pct_avance, 2)
            db_ac = prj_d.get('ac')
            if db_ac and float(db_ac) > 0:
                ac = round(float(db_ac), 2)
            else:
                seed_val = int(hashlib.md5(id_proyecto.encode()).hexdigest()[:8], 16) % 100
                cost_factor = 0.85 + (seed_val / 100) * 0.3
                ac = round(ev * cost_factor, 2) if ev > 0 else round(pv * 0.3, 2)"""

if old_ac in code:
    code = code.replace(old_ac, new_ac, 1)
    changes += 1
    print('  OK: AC lee de cartera_build primero')

# Fix 3: Use real fecha_inicio/fecha_fin_plan from cartera_build
old_dates = """            bac = float(pres['bac_total']) if pres and pres['bac_total'] else float(prj_d.get('horas_estimadas', 100)) * 110
            fecha_inicio = pres['fecha_inicio'] if pres and pres['fecha_inicio'] else (prj_d.get('fecha_creacion') or datetime.now()).date() if hasattr(prj_d.get('fecha_creacion', ''), 'date') else datetime.now().date()
            fecha_fin = pres['fecha_fin'] if pres and pres['fecha_fin'] else fecha_inicio + timedelta(days=180)"""

new_dates = """            bac = float(pres['bac_total']) if pres and pres['bac_total'] else float(prj_d.get('horas_estimadas', 100)) * 110
            # Dates: prefer cartera_build fields, then presupuestos, then defaults
            fecha_inicio = prj_d.get('fecha_inicio') or (pres['fecha_inicio'] if pres and pres.get('fecha_inicio') else None)
            if not fecha_inicio:
                fc = prj_d.get('fecha_creacion')
                fecha_inicio = fc.date() if hasattr(fc, 'date') else (fc or datetime.now().date())
            fecha_fin = prj_d.get('fecha_fin_plan') or (pres['fecha_fin'] if pres and pres.get('fecha_fin') else None)
            if not fecha_fin:
                fecha_fin = fecha_inicio + timedelta(days=180) if isinstance(fecha_inicio, date) else date.today() + timedelta(days=180)"""

if old_dates in code:
    code = code.replace(old_dates, new_dates, 1)
    changes += 1
    print('  OK: fechas leen de cartera_build primero')

# Fix 4: Imputaciones from horas_imputadas table
old_imput = """            # ── Imputaciones (kanban_tareas horas) ──
            week_tasks = await conn.fetch(
                "SELECT k.id_tecnico, s.nombre, k.horas_reales "
                "FROM kanban_tareas k LEFT JOIN compartido.pmo_staff_skills s "
                "ON k.id_tecnico = s.id_recurso "
                "WHERE k.id_proyecto = $1 AND k.horas_reales > 0 "
                "ORDER BY k.horas_reales DESC", id_proyecto)
            semana_actual = [{"tecnico_id": r['id_tecnico'], "nombre": r['nombre'] or r['id_tecnico'],
                              "horas": float(r['horas_reales'])} for r in week_tasks[:10]]
            top3 = semana_actual[:3]
            total_horas = sum(float(r['horas_reales'] or 0) for r in week_tasks)
            imputaciones = {
                "semana_actual": semana_actual,
                "ultimas_4_semanas": [
                    {"semana": f"S{i}", "total_horas": round(total_horas / 4 * (0.8 + i * 0.1), 1)}
                    for i in range(1, 5)
                ],  # SINTETICO: distribución estimada
                "top3_tecnicos": top3,
            }"""

new_imput = """            # ── Imputaciones (horas_imputadas si existe, fallback kanban) ──
            has_imput = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                "WHERE table_name='horas_imputadas' AND table_schema='primitiva')")
            if has_imput:
                # Real data from horas_imputadas
                week_data = await conn.fetch(
                    "SELECT h.id_tecnico, s.nombre, SUM(h.horas) as total_h "
                    "FROM primitiva.horas_imputadas h "
                    "LEFT JOIN compartido.pmo_staff_skills s ON h.id_tecnico = s.id_recurso "
                    "WHERE h.id_proyecto = $1 AND h.fecha >= CURRENT_DATE - INTERVAL '7 days' "
                    "GROUP BY h.id_tecnico, s.nombre ORDER BY total_h DESC", id_proyecto)
                semana_actual = [{"tecnico_id": r['id_tecnico'], "nombre": r['nombre'] or r['id_tecnico'],
                                  "horas": round(float(r['total_h']), 1)} for r in week_data]

                weeks_summary = await conn.fetch(
                    "SELECT semana_iso, SUM(horas) as total "
                    "FROM primitiva.horas_imputadas WHERE id_proyecto = $1 "
                    "GROUP BY semana_iso ORDER BY semana_iso DESC LIMIT 4", id_proyecto)
                ultimas_4 = [{"semana": f"S{r['semana_iso']}", "total_horas": round(float(r['total']), 1)}
                             for r in weeks_summary]

                top3_rows = await conn.fetch(
                    "SELECT h.id_tecnico, s.nombre, SUM(h.horas) as total_h "
                    "FROM primitiva.horas_imputadas h "
                    "LEFT JOIN compartido.pmo_staff_skills s ON h.id_tecnico = s.id_recurso "
                    "WHERE h.id_proyecto = $1 "
                    "GROUP BY h.id_tecnico, s.nombre ORDER BY total_h DESC LIMIT 3", id_proyecto)
                top3 = [{"nombre": r['nombre'] or r['id_tecnico'],
                         "horas_acumuladas": round(float(r['total_h']), 1)} for r in top3_rows]
            else:
                # Fallback: kanban horas
                week_tasks = await conn.fetch(
                    "SELECT k.id_tecnico, s.nombre, k.horas_reales "
                    "FROM kanban_tareas k LEFT JOIN compartido.pmo_staff_skills s "
                    "ON k.id_tecnico = s.id_recurso "
                    "WHERE k.id_proyecto = $1 AND k.horas_reales > 0 "
                    "ORDER BY k.horas_reales DESC", id_proyecto)
                semana_actual = [{"tecnico_id": r['id_tecnico'], "nombre": r['nombre'] or r['id_tecnico'],
                                  "horas": float(r['horas_reales'])} for r in week_tasks[:10]]
                top3 = [{"nombre": r['nombre'] or r['id_tecnico'],
                         "horas_acumuladas": float(r['horas_reales'])} for r in week_tasks[:3]]
                total_horas = sum(float(r['horas_reales'] or 0) for r in week_tasks)
                ultimas_4 = [{"semana": f"S{i}", "total_horas": round(total_horas / 4 * (0.8 + i * 0.1), 1)}
                             for i in range(1, 5)]

            imputaciones = {
                "semana_actual": semana_actual,
                "ultimas_4_semanas": ultimas_4,
                "top3_tecnicos": top3,
            }"""

if old_imput in code:
    code = code.replace(old_imput, new_imput, 1)
    changes += 1
    print('  OK: imputaciones leen de horas_imputadas')

if changes > 0:
    with open(MAIN_PY, 'w') as f:
        f.write(code)
    print(f'\n  main.py: {changes} cambios guardados')

    # Syntax check
    import py_compile
    try:
        py_compile.compile(MAIN_PY, doraise=True)
        print('  SYNTAX OK')
    except py_compile.PyCompileError as e:
        print(f'  SYNTAX ERROR: {e}')
        exit(1)

    # Deploy
    os.system('docker cp /root/cognitive-pmo/backend/main.py cognitive-pmo-api-1:/app/main.py')
    os.system('docker restart cognitive-pmo-api-1')
    import time
    time.sleep(6)
    print('  Backend reiniciado')
else:
    print('  Sin cambios en main.py')

# ═══════════════════════════════════════════════════════════════
# S5: Verificación final
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('S5: Verificación final')
print('═' * 66)

import urllib.parse

# Pick 3 representative projects: verde, ambar, rojo
test_projects = {
    'VERDE': all_12[0],
    'AMBAR': all_12[4],
    'ROJO':  all_12[8],
}

for label, prj in test_projects.items():
    enc = urllib.parse.quote(prj)
    print(f'\n  ── {label}: {prj} ──')

    # PMBOK
    r = subprocess.run(['curl', '-s', f'http://localhost:8088/api/pm/project/{enc}/pmbok'],
                       capture_output=True, text=True, timeout=15)
    try:
        d = json.loads(r.stdout)
        p = d.get('proyecto', {})
        e = d.get('evm', {})
        imp = d.get('imputaciones', {})
        print(f'    Proyecto: {p.get("nombre","?")} | avance={p.get("pct_avance")}% | tiempo={p.get("pct_tiempo")}%')
        print(f'    EVM: PV={e.get("pv"):,.0f} EV={e.get("ev"):,.0f} AC={e.get("ac"):,.0f}')
        print(f'         CPI={e.get("cpi")} SPI={e.get("spi")} CV={e.get("cv"):,.0f} SV={e.get("sv"):,.0f}')
        print(f'         EAC={e.get("eac"):,.0f} VAC={e.get("vac"):,.0f}')
        print(f'         → {e.get("interpretacion")}')
        print(f'    Imputaciones: {len(imp.get("semana_actual",[]))} técnicos esta semana')
        print(f'    Top3: {[t.get("nombre","?") for t in imp.get("top3_tecnicos",[])]}')
    except Exception as ex:
        print(f'    ERROR: {ex}')
        print(f'    Raw: {r.stdout[:300]}')

    # Team
    r2 = subprocess.run(['curl', '-s', f'http://localhost:8088/api/pm/project/{enc}/team'],
                        capture_output=True, text=True, timeout=15)
    try:
        team = json.loads(r2.stdout)
        print(f'    Equipo: {len(team)} técnicos')
        for t in team[:3]:
            print(f'      {t.get("tecnico_id")}: {t.get("nombre")} ({t.get("silo")}) — {t.get("tareas_activas_proyecto")} tareas activas')
    except:
        print(f'    TEAM ERROR: {r2.stdout[:200]}')

print('\n' + '=' * 66)
print('P98 SEED PRIMITIVA COMPLETO')
print('Recarga navegador: Cmd+Shift+R')
print('=' * 66)

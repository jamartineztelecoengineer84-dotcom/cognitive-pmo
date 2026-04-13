#!/usr/bin/env python3
"""
P99 FIX CONCEPTUAL v2 — 3 fixes acotados
==========================================
Fix 1: P6 cartera_build estados diversificados (CHECK-safe)
Fix 2: P3 governance_dashboard.pms_asignados = COUNT(DISTINCT) real
Fix 3: P4 umbrales /pmo/managers realineados con seed (max 3 proy/PM)

Uso: python3 p99_fix_conceptual_v2.py 2>&1 | tee /tmp/p99_fix_conceptual_v2.log
"""
import subprocess, os, shutil, json

MAIN_PY = '/root/cognitive-pmo/backend/main.py'
SCHEMAS = ['sc_norte', 'sc_iberico', 'sc_litoral']

def psql(query, schema=None):
    if schema:
        query = f"SET search_path = {schema}, compartido, public; {query}"
    env = os.environ.copy()
    env['PGPASSWORD'] = 'Seacaboelabuso_0406'
    cmd = ['psql', '-h', 'localhost', '-U', 'jose_admin', '-d', 'cognitive_pmo', '-t', '-A', '-c', query]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
    out = r.stdout.strip()
    if out.startswith('SET\n'):
        out = out[4:]
    elif out == 'SET':
        out = ''
    if r.returncode != 0 and r.stderr.strip():
        print(f'    PSQL ERROR: {r.stderr[:200]}')
    return out

def psql_exec(query, schema=None):
    if schema:
        query = f"SET search_path = {schema}, compartido, public; {query}"
    env = os.environ.copy()
    env['PGPASSWORD'] = 'Seacaboelabuso_0406'
    cmd = ['psql', '-h', 'localhost', '-U', 'jose_admin', '-d', 'cognitive_pmo', '-c', query]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
    if r.returncode != 0:
        print(f'    PSQL ERROR: {r.stderr[:200]}')
        return False
    return True

def curl_json(path, scenario='sc_norte'):
    r = subprocess.run(
        ['curl', '-s', '-H', f'X-Scenario: {scenario}', f'http://localhost:8088{path}'],
        capture_output=True, text=True, timeout=15
    )
    try:
        return json.loads(r.stdout)
    except:
        return None

print('=' * 66)
print('P99 FIX CONCEPTUAL v2 — 3 fixes acotados')
print('=' * 66)

# Backup
bak = MAIN_PY + '.bak-conceptual-v2'
if not os.path.exists(bak):
    shutil.copy2(MAIN_PY, bak)
    print(f'Backup: {bak}')

# ═══════════════════════════════════════════════════════════════
# FIX 1: P6 cartera_build estados diversificados
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('FIX 1: P6 cartera_build — diversificar estados')
print('═' * 66)

# Valid states from CHECK: Standby, En analisis, pendiente, en revision,
# Aprobado, en ejecucion, en cierre, cerrado, PAUSADO_POR_RIESGO_P1
# Distribution for non-cerrado projects:
# 10% Standby, 10% En analisis, 10% pendiente, 15% en revision, 5% en cierre, rest en ejecucion

for sc in SCHEMAS:
    # Get non-cerrado project IDs in deterministic order
    raw = psql("SELECT id_proyecto FROM cartera_build WHERE estado != 'cerrado' ORDER BY id_proyecto", sc)
    projects = [p.strip() for p in raw.split('\n') if p.strip()]
    total = len(projects)

    if total == 0:
        print(f'  {sc}: sin proyectos activos, SKIP')
        continue

    # Check if already diversified
    distinct_estados = psql("SELECT COUNT(DISTINCT estado) FROM cartera_build WHERE estado != 'cerrado'", sc)
    if distinct_estados and int(distinct_estados) >= 4:
        current = psql("SELECT estado, COUNT(*) FROM cartera_build GROUP BY estado ORDER BY COUNT(*) DESC", sc)
        print(f'\n  {sc}: Ya diversificado ({distinct_estados} estados): {current}')
        continue

    # Show before
    before = psql("SELECT estado, COUNT(*) FROM cartera_build GROUP BY estado ORDER BY COUNT(*) DESC", sc)
    print(f'\n  {sc} ANTES: {before}')

    # Calculate counts
    n_standby = max(1, round(total * 0.10))
    n_analisis = max(1, round(total * 0.10))
    n_pendiente = max(1, round(total * 0.10))
    n_revision = max(1, round(total * 0.15))
    n_cierre = max(1, round(total * 0.05))
    # Rest stays en ejecucion

    idx = 0
    changes = {
        'Standby': projects[idx:idx+n_standby],
        'En analisis': projects[idx+n_standby:idx+n_standby+n_analisis],
        'pendiente': projects[idx+n_standby+n_analisis:idx+n_standby+n_analisis+n_pendiente],
        'en revision': projects[idx+n_standby+n_analisis+n_pendiente:idx+n_standby+n_analisis+n_pendiente+n_revision],
        'en cierre': projects[idx+n_standby+n_analisis+n_pendiente+n_revision:idx+n_standby+n_analisis+n_pendiente+n_revision+n_cierre],
    }

    for estado, prj_list in changes.items():
        if not prj_list:
            continue
        ids_str = ','.join(f"'{p}'" for p in prj_list)
        sql = f"UPDATE cartera_build SET estado = '{estado}' WHERE id_proyecto IN ({ids_str})"
        ok = psql_exec(sql, sc)
        if ok:
            print(f'    {estado}: {len(prj_list)} proyectos')
        else:
            print(f'    FALLO {estado} — ABORTANDO FIX 1')
            break

    after = psql("SELECT estado, COUNT(*) FROM cartera_build GROUP BY estado ORDER BY COUNT(*) DESC", sc)
    print(f'  {sc} DESPUÉS: {after}')


# ═══════════════════════════════════════════════════════════════
# FIX 2: P3 governance_dashboard.pms_asignados
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('FIX 2: P3 governance_dashboard — pms_asignados = PMs DISTINTOS')
print('═' * 66)

with open(MAIN_PY, 'r', encoding='utf-8') as f:
    code = f.read()

# Step 1: Remove dead B4 block from debug_search_path
# The block sits between `sp = await conn.fetchval(...)` and `return {...}`
# Replace the whole dead chunk, keeping the function clean
old_debug = '''    async with pool.acquire() as conn:
        sp = await conn.fetchval("SELECT current_setting('search_path')")
    # B4: PM asignados dinámico PER-SCHEMA (CORREGIDO P3+P4)
        # pms_asignados = nº PMs DISTINTOS con al menos 1 proyecto activo
        # pms_sobrecargados = PMs con > 5 proyectos activos (antes era > 3)
        # pms_cerca_limite = PMs con 4-5 proyectos activos
        try:
            pms_asignados = await conn.fetchval("""
                SELECT COUNT(DISTINCT id_pm) FROM pmo_governance_scoring
                WHERE id_pm IS NOT NULL AND id_pm != ''
                AND gate_status NOT IN ('COMPLETED','CERRADO','CANCELLED')
            """) or 0

            pms_sobrecargados = await conn.fetchval("""
                SELECT COUNT(*) FROM (
                    SELECT id_pm, COUNT(*) AS n
                    FROM pmo_governance_scoring
                    WHERE id_pm IS NOT NULL AND id_pm != ''
                    AND gate_status NOT IN ('COMPLETED','CERRADO','CANCELLED')
                    GROUP BY id_pm
                    HAVING COUNT(*) > 5
                ) sub
            """) or 0

            pms_cerca_limite = await conn.fetchval("""
                SELECT COUNT(*) FROM (
                    SELECT id_pm, COUNT(*) AS n
                    FROM pmo_governance_scoring
                    WHERE id_pm IS NOT NULL AND id_pm != ''
                    AND gate_status NOT IN ('COMPLETED','CERRADO','CANCELLED')
                    GROUP BY id_pm
                    HAVING COUNT(*) BETWEEN 4 AND 5
                ) sub
            """) or 0

            proyectos_activos_schema = await conn.fetchval("""
                SELECT COUNT(*) FROM pmo_governance_scoring
                WHERE gate_status NOT IN ('COMPLETED','CERRADO','CANCELLED')
            """) or 0

            total_pms_pool = await conn.fetchval(
                "SELECT COUNT(*) FROM compartido.pmo_project_managers"
            ) or 0

            carga_media_pm = round(
                (proyectos_activos_schema / max(pms_asignados, 1)) * 25, 1
            )
        except Exception as e:
            logger.warning(f"P3+P4 governance metrics error: {e}")
            pms_asignados = 0
            pms_sobrecargados = 0
            pms_cerca_limite = 0
            proyectos_activos_schema = 0
            total_pms_pool = 25
            carga_media_pm = 0
    return {"search_path": sp, "scenario_ctx": get_current_scenario()}'''

new_debug = '''    async with pool.acquire() as conn:
        sp = await conn.fetchval("SELECT current_setting('search_path')")
    return {"search_path": sp, "scenario_ctx": get_current_scenario()}'''

if old_debug in code:
    code = code.replace(old_debug, new_debug, 1)
    print('  Eliminado bloque B4 muerto de debug_search_path')
else:
    print('  SKIP: Bloque B4 muerto no encontrado (ya limpiado?)')

# Step 2: Fix governance_dashboard — asignados should count DISTINCT FTEs
# The current query counts DISTINCT cb.responsable_asignado which are FTE-xxx
# That's actually correct for counting unique assigned resources.
# But the PROBLEM is: it returns 30/50/75 (one per project) because each project
# has a unique FTE assigned (round-robin from p99_fixes_all.py).
# Real fix: this is counting correctly, the data just has 1:1 mapping.
# The dashboard label says "pms_asignados" but it's really counting resources.
# Let's make it count actual PMs from governance_scoring.

old_asignados = '''            # B4: PM asignados = PMs con al menos 1 proyecto activo en este schema
            asignados = await conn.fetchval(
                "SELECT COUNT(DISTINCT cb.responsable_asignado) "
                "FROM cartera_build cb "
                "WHERE cb.estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado') "
                "AND cb.responsable_asignado IS NOT NULL"
            ) or 0
            # Si no hay responsable_asignado, contar por id_pm
            if asignados == 0:
                asignados = await conn.fetchval(
                    "SELECT COUNT(DISTINCT pm.id_pm) FROM pmo_project_managers pm "
                    "INNER JOIN cartera_build cb ON pm.id_pm = cb.responsable_asignado OR pm.nombre = cb.responsable_asignado "
                    "WHERE cb.estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado')"
                ) or 0'''

new_asignados = '''            # P3-v2: PMs DISTINTOS con proyectos activos (via governance_scoring)
            asignados = await conn.fetchval(
                "SELECT COUNT(DISTINCT g.id_pm) FROM pmo_governance_scoring g "
                "WHERE g.id_pm IS NOT NULL AND g.gate_status NOT IN ('COMPLETED','CERRADO')"
            ) or 0'''

if old_asignados in code:
    code = code.replace(old_asignados, new_asignados, 1)
    print('  OK: asignados → COUNT(DISTINCT id_pm) FROM governance_scoring')
else:
    print('  WARN: Bloque asignados no encontrado exacto, buscando alternativa...')
    # Try to find and show what's there
    idx = code.find('PM asignados')
    if idx > -1:
        print(f'    Encontrado en pos {idx}: {code[idx:idx+100]}')

# Step 3: Fix sobrecargados in governance_dashboard — use governance_scoring
old_sobre = '''            # B4: PM sobrecargados = PMs con >3 proyectos activos en este schema
            sobrecargados_rows = await conn.fetch(
                "SELECT cb.responsable_asignado, COUNT(*) as cnt "
                "FROM cartera_build cb "
                "WHERE cb.estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado') "
                "AND cb.responsable_asignado IS NOT NULL "
                "GROUP BY cb.responsable_asignado HAVING COUNT(*) > 3"
            )
            sobrecargados = len(sobrecargados_rows)'''

new_sobre = '''            # P3-v2: PMs sobrecargados (>=3 proyectos activos en governance)
            sobrecargados_rows = await conn.fetch(
                "SELECT id_pm, COUNT(*) as cnt FROM pmo_governance_scoring "
                "WHERE id_pm IS NOT NULL AND gate_status NOT IN ('COMPLETED','CERRADO') "
                "GROUP BY id_pm HAVING COUNT(*) >= 3"
            )
            sobrecargados = len(sobrecargados_rows)'''

if old_sobre in code:
    code = code.replace(old_sobre, new_sobre, 1)
    print('  OK: sobrecargados → governance_scoring HAVING >= 3')
else:
    print('  WARN: Bloque sobrecargados no encontrado exacto')

# Step 4: Fix proyectos_activos to also use governance_scoring for consistency
old_proy = '''            # B4: Métricas per-schema
            proyectos_activos = await conn.fetchval(
                "SELECT COUNT(*) FROM cartera_build WHERE estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado')"
            ) or 0
            carga_media_pm = 0
            if asignados > 0 and proyectos_activos > 0:
                carga_media_pm = round(proyectos_activos / max(1, asignados) * 25, 1)'''

new_proy = '''            # P3-v2: Métricas per-schema
            proyectos_activos = await conn.fetchval(
                "SELECT COUNT(*) FROM cartera_build WHERE estado NOT IN ('cerrado')"
            ) or 0
            carga_media_pm = 0
            if asignados > 0 and proyectos_activos > 0:
                carga_media_pm = round(proyectos_activos / max(1, asignados) * 25, 1)'''

if old_proy in code:
    code = code.replace(old_proy, new_proy, 1)
    print('  OK: proyectos_activos filtro simplificado')
else:
    print('  WARN: Bloque proyectos_activos no encontrado exacto')


# ═══════════════════════════════════════════════════════════════
# FIX 3: P4 umbrales /pmo/managers
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('FIX 3: P4 /pmo/managers — umbrales realineados')
print('═' * 66)

old_umbrales = """                    if proj_count > 3:
                        d['estado'] = 'SOBRECARGADO'
                    elif proj_count > 0:
                        d['estado'] = 'ASIGNADO'
                    else:
                        d['estado'] = 'DISPONIBLE'"""

new_umbrales = """                    if proj_count >= 3:
                        d['estado'] = 'SOBRECARGADO'
                    elif proj_count == 2:
                        d['estado'] = 'CERCA_LIMITE'
                    elif proj_count == 1:
                        d['estado'] = 'ASIGNADO'
                    else:
                        d['estado'] = 'DISPONIBLE'"""

if old_umbrales in code:
    code = code.replace(old_umbrales, new_umbrales, 1)
    print('  OK: >=3 SOBRECARGADO, 2 CERCA_LIMITE, 1 ASIGNADO, 0 DISPONIBLE')
else:
    print('  WARN: Bloque umbrales no encontrado exacto')

# ═══════════════════════════════════════════════════════════════
# GUARDAR + SYNTAX CHECK
# ═══════════════════════════════════════════════════════════════
print('\n' + '─' * 66)
print('Guardando main.py...')
with open(MAIN_PY, 'w', encoding='utf-8') as f:
    f.write(code)

import py_compile
try:
    py_compile.compile(MAIN_PY, doraise=True)
    print('  SYNTAX OK')
except py_compile.PyCompileError as e:
    print(f'  SYNTAX ERROR: {e}')
    print('  RESTAURANDO BACKUP')
    shutil.copy2(bak, MAIN_PY)
    exit(1)

# ═══════════════════════════════════════════════════════════════
# DEPLOY + RESTART
# ═══════════════════════════════════════════════════════════════
print('\nDesplegando...')
os.system('docker cp /root/cognitive-pmo/backend/main.py cognitive-pmo-api-1:/app/main.py')
os.system('docker restart cognitive-pmo-api-1')

import time
time.sleep(6)

# Check backend started
r = subprocess.run(['docker', 'logs', 'cognitive-pmo-api-1', '--tail', '3'],
                   capture_output=True, text=True)
if 'Uvicorn running' in r.stdout or 'Application startup complete' in r.stdout:
    print('  Backend arrancado OK')
else:
    print(f'  WARN: Backend puede no estar listo: {r.stdout[-200:]}')


# ═══════════════════════════════════════════════════════════════
# VERIFICACIÓN
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('VERIFICACIÓN')
print('═' * 66)

# Fix 1: cartera_build estados
print('\n── Fix 1: cartera_build estados ──')
for sc in SCHEMAS:
    estados = psql("SELECT estado, COUNT(*) FROM cartera_build GROUP BY estado ORDER BY estado", sc)
    print(f'  {sc}: {estados}')

# Fix 2: governance dashboard
print('\n── Fix 2: governance_dashboard ──')
for sc in SCHEMAS:
    d = curl_json('/pmo/governance/dashboard', sc)
    if d:
        print(f'  {sc}: pms_asignados={d.get("pms_asignados")}, sobrecargados={d.get("pms_sobrecargados")}, '
              f'proy_activos={d.get("proyectos_activos_schema")}, carga_media={d.get("carga_media_pm")}')
    else:
        print(f'  {sc}: ERROR respuesta API')

# Fix 3: /pmo/managers estados
print('\n── Fix 3: /pmo/managers estados PM ──')
for sc in SCHEMAS:
    d = curl_json('/pmo/managers', sc)
    if d and isinstance(d, list):
        estados = {}
        for pm in d:
            est = pm.get('estado', '?')
            estados[est] = estados.get(est, 0) + 1
        print(f'  {sc}: {len(d)} PMs — {estados}')
    else:
        print(f'  {sc}: ERROR respuesta API')

# Ocupación (no debería cambiar)
print('\n── Ocupación técnicos (control) ──')
for sc in SCHEMAS:
    d = curl_json('/team/tecnicos', sc)
    if d and isinstance(d, list):
        estados = {}
        for t in d:
            est = t.get('estado', '?')
            estados[est] = estados.get(est, 0) + 1
        ocu = len(d) - estados.get('DISPONIBLE', 0)
        print(f'  {sc}: {ocu}/{len(d)} ocupados — {estados}')
    else:
        print(f'  {sc}: ERROR')

print('\n' + '=' * 66)
print('P99 FIX CONCEPTUAL v2 COMPLETO')
print('Tag sugerido: p99-fix-conceptual-v2')
print('Recarga navegador: Cmd+Shift+R')
print('=' * 66)

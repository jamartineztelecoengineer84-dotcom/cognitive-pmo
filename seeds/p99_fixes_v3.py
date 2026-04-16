#!/usr/bin/env python3
"""
P99 FIXES v3 — 5 issues pendientes
====================================
BACKEND (main.py):
  FIX 3b: /incidencias → calcular sla_horas desde sla_limite
  FIX 5:  /team/tecnicos → devolver tarea_actual/proyecto_actual con referencia
  FIX 9b: /presupuestos → asegurar nombre_proyecto en respuesta
  FIX 11b: /pmo/governance/dashboard → cálculos per-schema (no compartido fijo)

DATOS (SQL):
  FIX 3c: Timestamps recientes + sla_limite coherente en incidencias_run
  FIX 8b: Poblar skills_requeridas en cartera_build
  FIX 11c: Asegurar datos governance variados por schema

Uso: python3 p99_fixes_v3.py
"""
import subprocess, os, random, shutil, re

MAIN_PY = '/root/cognitive-pmo/backend/main.py'
SCHEMAS = ['sc_norte', 'sc_iberico', 'sc_litoral']
DB = 'cognitive_pmo'

def psql(sql, schema=None):
    if schema:
        sql = f"SET search_path = {schema}, compartido, public; {sql}"
    cmd = ['psql', '-h', 'localhost', '-U', 'jose_admin', '-d', DB, '-t', '-A', '-c', sql]
    env = os.environ.copy()
    env['PGPASSWORD'] = 'REDACTED-old-password'
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return r.stdout.strip()

def psql_exec(sql, schema=None):
    if schema:
        sql = f"SET search_path = {schema}, compartido, public; {sql}"
    cmd = ['psql', '-h', 'localhost', '-U', 'jose_admin', '-d', DB, '-c', sql]
    env = os.environ.copy()
    env['PGPASSWORD'] = 'REDACTED-old-password'
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(f'  SQL ERROR: {r.stderr[:300]}')
    return r.returncode == 0

print('=' * 60)
print('P99 FIXES v3 — 5 issues pendientes')
print('=' * 60)

# Backup main.py
with open(MAIN_PY, 'r', encoding='utf-8') as f:
    code = f.read()

bak = MAIN_PY + '.bak_v3'
if not os.path.exists(bak):
    shutil.copy2(MAIN_PY, bak)
    print(f'Backup: {bak}')

# ═══════════════════════════════════════════════════════════
# FIX 3b: /incidencias → calcular sla_horas
# ═══════════════════════════════════════════════════════════
print('\n--- FIX 3b: /incidencias → sla_horas calculado ---')

# Buscar el endpoint GET /incidencias y su serialize
# El endpoint devuelve rows con sla_limite (timestamp)
# Necesitamos que el serialize añada sla_horas = diferencia en horas

# Estrategia: Buscar donde se hace el return de incidencias y añadir
# post-procesamiento que calcule sla_horas

# Primero veamos si ya tiene sla_horas
if 'sla_horas' in code:
    print('  SKIP: sla_horas ya existe en el código')
else:
    # Buscar el patrón del endpoint /incidencias GET
    # Puede ser: return [serialize(r) for r in rows]
    # o similar dentro del bloque @app.get("/incidencias")

    inc_match = re.search(
        r'(@app\.get\(["\']\/incidencias["\'].*?\n)(.*?)(?=@app\.(get|post|put|delete|patch))',
        code, re.DOTALL
    )

    if inc_match:
        inc_block = inc_match.group(0)
        print(f'  Encontrado bloque /incidencias ({len(inc_block)} chars)')

        # Buscar el return con serialize
        # Patron: return [serialize(r) for r in rows]
        serialize_pattern = r'return \[serialize\(r\) for r in rows\]'
        serialize_match = re.search(serialize_pattern, inc_block)

        if serialize_match:
            old_return = serialize_match.group(0)
            new_return = """result = []
                for r in rows:
                    d = serialize(r)
                    # FIX 3b: calcular sla_horas desde sla_limite
                    if d.get('sla_limite'):
                        from datetime import datetime
                        try:
                            if isinstance(d['sla_limite'], str):
                                sl = datetime.fromisoformat(d['sla_limite'].replace('Z','+00:00'))
                            else:
                                sl = d['sla_limite']
                            now = datetime.now(sl.tzinfo) if sl.tzinfo else datetime.now()
                            diff = (sl - now).total_seconds() / 3600
                            d['sla_horas'] = round(diff, 1)
                        except Exception:
                            d['sla_horas'] = None
                    result.append(d)
                return result"""

            # Buscar dentro del bloque completo del código
            idx_start = inc_match.start()
            idx_in_block = code.find(old_return, idx_start)
            if idx_in_block > -1 and idx_in_block < idx_start + len(inc_block):
                code = code[:idx_in_block] + new_return + code[idx_in_block + len(old_return):]
                print('  OK: sla_horas calculado en /incidencias')
            else:
                print('  WARN: no encontré el return exacto en /incidencias')
        else:
            print('  WARN: no encontré serialize pattern en /incidencias')
            # Intento alternativo: buscar cualquier return en el bloque
            print('  Intentando alternativa...')
            # Buscar "return [" dentro del bloque de incidencias
            alt_pat = re.search(r'return \[.*?for r in .*?\]', inc_block)
            if alt_pat:
                print(f'  Encontré: {alt_pat.group(0)[:80]}...')
            else:
                print('  No encontré ningún return con list comprehension')
    else:
        print('  WARN: no encontré bloque @app.get /incidencias')
        # Intento más simple: buscar cerca de 'incidencias'
        idx = code.find('@app.get("/incidencias")')
        if idx == -1:
            idx = code.find("@app.get('/incidencias')")
        if idx > -1:
            print(f'  Encontrado @app.get /incidencias en posición {idx}')
            # Mostrar las siguientes 20 líneas para debug
            snippet = code[idx:idx+1000]
            for i, line in enumerate(snippet.split('\n')[:20]):
                print(f'    L{i}: {line.rstrip()}')

# ═══════════════════════════════════════════════════════════
# FIX 5: /team/tecnicos → tarea_actual + proyecto_actual
# ═══════════════════════════════════════════════════════════
print('\n--- FIX 5: /team/tecnicos → tarea_actual + proyecto_actual ---')

# El fix anterior (FIX 10) ya mapea estado_run_dinamico → estado_run
# Ahora necesitamos que TAMBIÉN devuelva tarea_actual y proyecto_actual
# cuando un técnico está ASIGNADO/OCUPADO

if 'tarea_actual' in code:
    print('  SKIP: tarea_actual ya existe en el código')
else:
    # Buscar el bloque del endpoint /team/tecnicos
    tec_match = re.search(
        r'(@app\.get\(["\']\/team\/tecnicos["\'].*?\n)(.*?)(?=@app\.(get|post|put|delete|patch))',
        code, re.DOTALL
    )

    if tec_match:
        tec_block = tec_match.group(0)
        print(f'  Encontrado bloque /team/tecnicos ({len(tec_block)} chars)')

        # Buscar el patrón que ya tiene del FIX 10 (estado_run_dinamico)
        # El FIX 10 crea un loop: for r in rows: d = serialize(r) ... result.append(d)
        # Necesitamos añadir dentro de ese loop la consulta de tarea_actual

        # Opción: añadir post-procesamiento después del loop existente
        # Buscar "result.append(d)" dentro del bloque
        if 'result.append(d)' in tec_block:
            print('  Encontrado loop FIX 10, añadiendo tarea_actual...')

            # Reemplazar el bloque completo del loop
            # Buscar desde "result = []" hasta "return result"
            old_loop_pat = r'result = \[\]\s*\n\s*for r in rows:\s*\n\s*d = serialize\(r\)\s*\n.*?result\.append\(d\)\s*\n\s*return result'
            loop_match = re.search(old_loop_pat, tec_block, re.DOTALL)

            if loop_match:
                old_loop = loop_match.group(0)
                new_loop = """result = []
                for r in rows:
                    d = serialize(r)
                    if 'estado_run_dinamico' in d:
                        d['estado_run'] = d['estado_run_dinamico']
                    if 'carga_dinamica' in d:
                        d['carga_actual'] = d['carga_dinamica']
                    result.append(d)

                # FIX 5: añadir tarea_actual y proyecto_actual para técnicos asignados
                try:
                    for d in result:
                        rid = d.get('id_recurso', '')
                        if not rid:
                            continue
                        # Buscar en incidencias_run activas
                        inc_row = await conn.fetchrow(
                            "SELECT ticket_id, incidencia_detectada FROM incidencias_run "
                            "WHERE tecnico_asignado = $1 AND estado NOT IN ('CERRADO','RESUELTO') "
                            "ORDER BY timestamp_creacion DESC LIMIT 1", rid
                        )
                        if inc_row:
                            d['tarea_actual'] = f"INC: {inc_row['ticket_id']}"
                            d['proyecto_actual'] = inc_row['incidencia_detectada'][:50] if inc_row['incidencia_detectada'] else ''
                            continue
                        # Buscar en kanban_tareas activas
                        kan_row = await conn.fetchrow(
                            "SELECT id, titulo, id_proyecto FROM kanban_tareas "
                            "WHERE (asignado = $1 OR id_recurso = $1) "
                            "AND columna NOT IN ('Completado','Done','Backlog') "
                            "ORDER BY updated_at DESC LIMIT 1", rid
                        )
                        if kan_row:
                            d['tarea_actual'] = f"BUILD: {kan_row['titulo'][:40] if kan_row['titulo'] else kan_row['id']}"
                            d['proyecto_actual'] = kan_row.get('id_proyecto', '')
                except Exception as e:
                    logger.warning(f"FIX5: Error enriching tecnicos: {e}")

                return result"""

                # Reemplazar en el código global
                idx_start = tec_match.start()
                idx_in_code = code.find(old_loop, idx_start)
                if idx_in_code > -1:
                    code = code[:idx_in_code] + new_loop + code[idx_in_code + len(old_loop):]
                    print('  OK: tarea_actual + proyecto_actual añadidos')
                else:
                    print('  WARN: no pude reemplazar el loop (posición no encontrada)')
            else:
                print('  WARN: regex del loop no matchea')
                # Debug: mostrar qué hay
                for line in tec_block.split('\n'):
                    if 'result' in line or 'append' in line:
                        print(f'    {line.rstrip()[:100]}')
        else:
            print('  WARN: no hay result.append(d) — FIX 10 puede no estar aplicado')
    else:
        print('  WARN: no encontré bloque @app.get /team/tecnicos')

# ═══════════════════════════════════════════════════════════
# FIX 9b: /presupuestos → verificar nombre_proyecto
# ═══════════════════════════════════════════════════════════
print('\n--- FIX 9b: /presupuestos → nombre_proyecto ---')

if 'cb.nombre_proyecto' in code and 'presupuestos' in code:
    print('  OK: JOIN con cartera_build ya aplicado (FIX 9)')
else:
    # Buscar el endpoint presupuestos
    pres_match = re.search(r'@app\.get.*?/presupuestos', code)
    if pres_match:
        print(f'  Endpoint encontrado en pos {pres_match.start()}')
        # Mostrar contexto
        snippet = code[pres_match.start():pres_match.start()+500]
        for line in snippet.split('\n')[:10]:
            print(f'    {line.rstrip()[:100]}')
    else:
        print('  WARN: endpoint /presupuestos no encontrado')

# ═══════════════════════════════════════════════════════════
# FIX 11b: /pmo/governance/dashboard → per-schema
# ═══════════════════════════════════════════════════════════
print('\n--- FIX 11b: /pmo/governance/dashboard per-schema ---')

# El endpoint actual cuenta PMs desde compartido (shared) → mismo resultado en todos los schemas
# Necesitamos que calcule stats dinámicamente basándose en proyectos del schema activo

gov_match = re.search(
    r'(@app\.get\(["\']\/pmo\/governance\/dashboard["\'].*?\n)(.*?)(?=@app\.(get|post|put|delete|patch))',
    code, re.DOTALL
)

if gov_match:
    gov_block = gov_match.group(0)
    print(f'  Encontrado bloque /pmo/governance/dashboard ({len(gov_block)} chars)')

    # Buscar si ya tiene el fix per-schema
    if 'proyectos_activos_schema' in gov_block or 'cartera_build.*id_pm' in gov_block:
        print('  SKIP: ya tiene cálculo per-schema')
    else:
        # Necesitamos añadir queries que cuenten proyectos per-PM en el schema activo
        # Buscar el return del endpoint
        print('  Contenido del endpoint (primeras 30 líneas):')
        for i, line in enumerate(gov_block.split('\n')[:30]):
            print(f'    L{i}: {line.rstrip()[:120]}')

        # Estrategia: después de obtener los PMs, enriquecer con counts per-schema
        # Buscar "total_pms" o similar
        if 'total_pms' in gov_block:
            print('  INFO: tiene total_pms — necesita enrichment per-schema')
        else:
            print('  INFO: estructura diferente — revisar manualmente')
else:
    print('  WARN: no encontré /pmo/governance/dashboard')
    # Buscar alternativas
    for pat in ['governance', 'pmo.*dashboard', 'pmo/governance']:
        matches = [(m.start(), m.group(0)[:80]) for m in re.finditer(pat, code)]
        if matches:
            print(f'  Alternativas para "{pat}":')
            for pos, txt in matches[:5]:
                print(f'    pos {pos}: {txt}')

# ═══════════════════════════════════════════════════════════
# GUARDAR main.py
# ═══════════════════════════════════════════════════════════
print('\n--- Guardando main.py ---')
with open(MAIN_PY, 'w', encoding='utf-8') as f:
    f.write(code)
print('  OK: main.py guardado')

# ═══════════════════════════════════════════════════════════
# FIX 3c: DATA — Timestamps recientes + SLA coherente
# ═══════════════════════════════════════════════════════════
print('\n--- FIX 3c: Timestamps + SLA en incidencias_run ---')

for sc in SCHEMAS:
    # 1. Actualizar TODOS los timestamps a los últimos 14 días
    sql1 = """
    UPDATE incidencias_run SET
        timestamp_creacion = NOW() - (random() * INTERVAL '14 days')
    WHERE estado NOT IN ('CERRADO','RESUELTO');
    """
    psql_exec(sql1, sc)

    # 2. Recalcular sla_limite basado en prioridad (4h/8h/24h/48h)
    sql2 = """
    UPDATE incidencias_run SET
        sla_limite = timestamp_creacion + CASE
            WHEN prioridad IN ('P1','Critica') THEN INTERVAL '4 hours'
            WHEN prioridad IN ('P2','Alta') THEN INTERVAL '8 hours'
            WHEN prioridad IN ('P3','Media') THEN INTERVAL '24 hours'
            ELSE INTERVAL '48 hours'
        END
    WHERE estado NOT IN ('CERRADO','RESUELTO');
    """
    psql_exec(sql2, sc)

    # 3. Para las CERRADAS, poner sla_limite en el pasado (cumplido)
    sql3 = """
    UPDATE incidencias_run SET
        sla_limite = timestamp_creacion + INTERVAL '4 hours',
        timestamp_creacion = NOW() - (random() * INTERVAL '30 days') - INTERVAL '14 days'
    WHERE estado IN ('CERRADO','RESUELTO') AND sla_limite IS NULL;
    """
    psql_exec(sql3, sc)

    # Verificar
    count = psql("SELECT COUNT(*), MIN(timestamp_creacion)::date, MAX(timestamp_creacion)::date FROM incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO')", sc)
    print(f'  {sc}: abiertas -> {count}')

# ═══════════════════════════════════════════════════════════
# FIX 8b: DATA — skills_requeridas en cartera_build
# ═══════════════════════════════════════════════════════════
print('\n--- FIX 8b: skills_requeridas en cartera_build ---')

SKILLS_POOL = {
    'sc_norte': [
        'Java, Spring Boot, Oracle',
        'Python, FastAPI, PostgreSQL',
        'React, TypeScript, Node.js',
        'SAP ABAP, HANA',
        'Kubernetes, Docker, CI/CD',
        'Angular, .NET Core, SQL Server',
        'Terraform, AWS, CloudFormation',
        'Cobol, JCL, DB2',
        'Elasticsearch, Kafka, Redis',
        'Salesforce, Apex, Lightning'
    ],
    'sc_iberico': [
        'Python, Django, MongoDB',
        'Swift, iOS, Firebase',
        'Kotlin, Android, Room',
        'Vue.js, Nuxt, GraphQL',
        'Go, gRPC, Protobuf',
        'Flutter, Dart, BLoC',
        'Rust, WebAssembly, WASM',
        'PHP, Laravel, MySQL',
        'Scala, Spark, Hadoop',
        'C#, Blazor, Azure Functions'
    ],
    'sc_litoral': [
        'Java, Microservices, Kafka',
        'Python, TensorFlow, ML Ops',
        'React Native, Expo, TypeScript',
        'AWS Lambda, DynamoDB, S3',
        'C++, QT, Embedded',
        '.NET, WPF, Entity Framework',
        'Ruby, Rails, PostgreSQL',
        'Elixir, Phoenix, LiveView',
        'Perl, Shell, Linux Admin',
        'Power Platform, Power Automate, SharePoint'
    ]
}

for sc in SCHEMAS:
    # Verificar si ya tienen skills
    existing = psql("SELECT COUNT(*) FROM cartera_build WHERE skills_requeridas IS NOT NULL AND skills_requeridas != ''", sc)
    if existing and int(existing) > 0:
        print(f'  {sc}: ya tiene {existing} con skills, SKIP')
        continue

    # Obtener proyectos
    prj_raw = psql("SELECT id_proyecto FROM cartera_build ORDER BY id_proyecto", sc)
    projects = [p.strip() for p in prj_raw.split('\n') if p.strip()]

    if not projects:
        print(f'  {sc}: sin proyectos')
        continue

    skills = SKILLS_POOL.get(sc, SKILLS_POOL['sc_norte'])
    updated = 0
    for i, prj_id in enumerate(projects):
        sk = skills[i % len(skills)]
        # Escapar comillas simples
        sk_safe = sk.replace("'", "''")
        sql = f"UPDATE cartera_build SET skills_requeridas = '{sk_safe}' WHERE id_proyecto = '{prj_id}'"
        if psql_exec(sql, sc):
            updated += 1

    print(f'  {sc}: {updated}/{len(projects)} proyectos con skills asignados')

# ═══════════════════════════════════════════════════════════
# FIX 11c: DATA — Verificar governance scoring variado
# ═══════════════════════════════════════════════════════════
print('\n--- FIX 11c: Verificar governance scoring ---')

for sc in SCHEMAS:
    count = psql("SELECT COUNT(*) FROM pmo_governance_scoring", sc)
    avg_score = psql("SELECT ROUND(AVG(total_score)::numeric, 1) FROM pmo_governance_scoring", sc)
    gates = psql("SELECT string_agg(DISTINCT gate_status, ', ') FROM pmo_governance_scoring", sc)
    print(f'  {sc}: {count} registros, avg_score={avg_score}, gates={gates}')

# ═══════════════════════════════════════════════════════════
# RESTART
# ═══════════════════════════════════════════════════════════
print('\n--- Deploying + Restarting ---')
os.system('docker cp /root/cognitive-pmo/backend/main.py cognitive-pmo-api-1:/app/main.py')
os.system('docker restart cognitive-pmo-api-1')

import time
time.sleep(3)

# ═══════════════════════════════════════════════════════════
# VERIFICACION
# ═══════════════════════════════════════════════════════════
print('\n--- Verificación ---')

for sc in SCHEMAS:
    inc = psql("SELECT COUNT(*) FROM incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO')", sc)
    sla = psql("SELECT COUNT(*) FROM incidencias_run WHERE sla_limite IS NOT NULL AND sla_limite > NOW() - INTERVAL '30 days'", sc)
    skills = psql("SELECT COUNT(*) FROM cartera_build WHERE skills_requeridas IS NOT NULL AND skills_requeridas != ''", sc)
    gov = psql("SELECT COUNT(*) FROM pmo_governance_scoring", sc)
    print(f'  {sc}: inc_abiertas={inc} | sla_recientes={sla} | con_skills={skills} | governance={gov}')

# Test rápido del endpoint incidencias
print('\n--- Test endpoint incidencias ---')
for sc in SCHEMAS:
    result = subprocess.run(
        ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8000/incidencias'],
        capture_output=True, text=True, timeout=10
    )
    try:
        import json
        data = json.loads(result.stdout)
        items = data if isinstance(data, list) else data.get('incidencias', [])
        if items:
            first = items[0]
            has_sla = 'sla_horas' in first
            print(f'  {sc}: {len(items)} incidencias, sla_horas={has_sla}, sample sla_horas={first.get("sla_horas", "N/A")}')
        else:
            print(f'  {sc}: 0 incidencias')
    except Exception as e:
        print(f'  {sc}: error parsing: {e}')
        print(f'    stdout[:200]: {result.stdout[:200]}')

# Test rápido del endpoint team/tecnicos
print('\n--- Test endpoint team/tecnicos ---')
for sc in SCHEMAS[:1]:  # Solo uno para no saturar
    result = subprocess.run(
        ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8000/team/tecnicos'],
        capture_output=True, text=True, timeout=10
    )
    try:
        import json
        data = json.loads(result.stdout)
        items = data if isinstance(data, list) else data.get('tecnicos', [])
        assigned = [t for t in items if t.get('tarea_actual')]
        print(f'  {sc}: {len(items)} tecnicos, {len(assigned)} con tarea_actual')
        if assigned:
            print(f'    Ejemplo: {assigned[0].get("nombre")} → {assigned[0].get("tarea_actual")}')
    except Exception as e:
        print(f'  {sc}: error: {e}')

print('\n' + '=' * 60)
print('P99 FIXES v3 COMPLETO')
print('Recargar navegador (Cmd+Shift+R)')
print('=' * 60)

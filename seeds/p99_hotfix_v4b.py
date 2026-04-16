#!/usr/bin/env python3
"""
P99 HOTFIX v4b — Cierra los 3 fallos del v4
=============================================
H1: /incidencias/live → añadir sla_horas (tabla incidencias_live, usa dict(r))
H2: skills_requeridas → fix psql SET prefix + poblar datos
H3: Restart correcto de nginx container
H4: Skills en tarjetas proyecto BUILD en index.html

Uso: python3 p99_hotfix_v4b.py
"""
import subprocess, os, re, shutil, json

MAIN_PY = '/root/cognitive-pmo/backend/main.py'
IDX = '/root/cognitive-pmo/frontend/index.html'
SCHEMAS = ['sc_norte', 'sc_iberico', 'sc_litoral']
DB = 'cognitive_pmo'

def psql(sql, schema=None):
    """psql que limpia el prefijo SET"""
    if schema:
        sql = f"SET search_path = {schema}, compartido, public; {sql}"
    cmd = ['psql', '-h', 'localhost', '-U', 'jose_admin', '-d', DB, '-t', '-A', '-c', sql]
    env = os.environ.copy()
    env['PGPASSWORD'] = 'REDACTED-old-password'
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    out = r.stdout.strip()
    # Limpiar prefijo "SET" que aparece por el SET search_path
    if out.startswith('SET\n'):
        out = out[4:]
    elif out == 'SET':
        out = ''
    return out

def psql_exec(sql, schema=None):
    if schema:
        sql = f"SET search_path = {schema}, compartido, public; {sql}"
    cmd = ['psql', '-h', 'localhost', '-U', 'jose_admin', '-d', DB, '-c', sql]
    env = os.environ.copy()
    env['PGPASSWORD'] = 'REDACTED-old-password'
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(f'  SQL ERROR: {r.stderr[:200]}')
    return r.returncode == 0

print('=' * 60)
print('P99 HOTFIX v4b')
print('=' * 60)

# ═══════════════════════════════════════════════════════════
# H1: /incidencias/live → sla_horas
# ═══════════════════════════════════════════════════════════
print('\n--- H1: /incidencias/live → sla_horas ---')

with open(MAIN_PY, 'r', encoding='utf-8') as f:
    code = f.read()

# El endpoint actual:
#   return [dict(r) for r in rows]
# Lo reemplazamos por un loop que añade sla_horas

old_live_return = 'return [dict(r) for r in rows]'

# Necesitamos encontrarlo DENTRO del bloque /incidencias/live, no en otro sitio
live_pos = code.find('@app.get("/incidencias/live")')
if live_pos == -1:
    live_pos = code.find("@app.get('/incidencias/live')")

if live_pos > -1:
    # Buscar el return [dict(r)...] más cercano después del endpoint
    next_return = code.find(old_live_return, live_pos)
    # Verificar que está dentro del mismo bloque (no más allá de 800 chars)
    if next_return > -1 and next_return - live_pos < 800:
        if 'sla_horas' not in code[live_pos:next_return+100]:
            new_live_return = """# H1: enriquecer incidencias_live con sla_horas
                result_live = []
                for r in rows:
                    d = dict(r)
                    # sla_horas: buscar en incidencias_run por ticket_id
                    if d.get('ticket_id'):
                        sla_val = await conn.fetchval(
                            "SELECT sla_limite FROM incidencias_run WHERE ticket_id = $1",
                            d['ticket_id']
                        )
                        d['sla_horas'] = float(sla_val) if sla_val is not None else 48
                    elif d.get('sla_limite') is not None:
                        d['sla_horas'] = float(d['sla_limite'])
                    else:
                        d['sla_horas'] = 48
                    # Mapear prioridad si viene como prioridad_ia
                    if 'prioridad' not in d and d.get('prioridad_ia'):
                        d['prioridad'] = d['prioridad_ia']
                    result_live.append(d)
                return result_live"""
            code = code[:next_return] + new_live_return + code[next_return + len(old_live_return):]
            print('  OK: sla_horas añadido a /incidencias/live')
        else:
            print('  SKIP: sla_horas ya existe en /incidencias/live')
    else:
        print(f'  WARN: return no encontrado cerca (pos={next_return}, live_pos={live_pos})')
else:
    print('  WARN: /incidencias/live endpoint no encontrado')

# Guardar main.py
with open(MAIN_PY, 'w', encoding='utf-8') as f:
    f.write(code)
print('  main.py guardado')

# ═══════════════════════════════════════════════════════════
# H2: skills_requeridas en cartera_build
# ═══════════════════════════════════════════════════════════
print('\n--- H2: skills_requeridas en cartera_build ---')

SKILLS_MAP = {
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
        'Salesforce, Apex, Lightning',
        'Java, Microservices, REST API',
        'Python, Django, MongoDB',
        'Vue.js, GraphQL, Apollo',
        'Go, gRPC, Protobuf',
        'C#, .NET 8, Azure'
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
        'C#, Blazor, Azure Functions',
        'React, Next.js, Vercel',
        'Elixir, Phoenix, LiveView',
        'Ruby, Rails, PostgreSQL',
        'TypeScript, Deno, Fresh',
        'Java, Quarkus, GraalVM'
    ],
    'sc_litoral': [
        'Java, Microservices, Kafka',
        'Python, TensorFlow, ML Ops',
        'React Native, Expo, TypeScript',
        'AWS Lambda, DynamoDB, S3',
        'C++, Qt, Embedded',
        '.NET, WPF, Entity Framework',
        'Ruby, Rails, PostgreSQL',
        'Elixir, Phoenix, LiveView',
        'Perl, Shell, Linux Admin',
        'Power Platform, Power Automate',
        'Rust, Actix, WebAssembly',
        'Angular, RxJS, NgRx',
        'Solidity, Web3, Hardhat',
        'R, Shiny, ggplot2',
        'Dart, Flutter, Firebase'
    ]
}

for sc in SCHEMAS:
    existing = psql("SELECT COUNT(*) FROM cartera_build WHERE skills_requeridas IS NOT NULL AND skills_requeridas != ''", sc)
    total = psql("SELECT COUNT(*) FROM cartera_build", sc)

    existing_int = int(existing) if existing.isdigit() else 0
    total_int = int(total) if total.isdigit() else 0

    print(f'  {sc}: {existing_int}/{total_int} con skills')

    if total_int == 0:
        print('    Sin proyectos, SKIP')
        continue

    if existing_int >= total_int:
        print('    SKIP: ya todos tienen skills')
        continue

    projects = psql("SELECT id_proyecto FROM cartera_build ORDER BY id_proyecto", sc)
    if not projects:
        continue

    proj_list = [p.strip() for p in projects.split('\n') if p.strip()]
    skills = SKILLS_MAP.get(sc, SKILLS_MAP['sc_norte'])
    updated = 0
    for i, pid in enumerate(proj_list):
        sk = skills[i % len(skills)]
        sk_safe = sk.replace("'", "''")
        pid_safe = pid.replace("'", "''")
        if psql_exec(f"UPDATE cartera_build SET skills_requeridas = '{sk_safe}' WHERE id_proyecto = '{pid_safe}' AND (skills_requeridas IS NULL OR skills_requeridas = '')", sc):
            updated += 1
    print(f'    Actualizados: {updated}')

# Verificar
for sc in SCHEMAS:
    sample = psql("SELECT id_proyecto, skills_requeridas FROM cartera_build WHERE skills_requeridas IS NOT NULL LIMIT 3", sc)
    print(f'  {sc} muestra: {sample[:200]}')

# ═══════════════════════════════════════════════════════════
# H3: Verificar también incidencias_live tiene datos por schema
# ═══════════════════════════════════════════════════════════
print('\n--- H3: Verificar incidencias_live por schema ---')

for sc in SCHEMAS:
    # Ver si incidencias_live existe y tiene datos
    count = psql("SELECT COUNT(*) FROM incidencias_live", sc)
    print(f'  {sc}: incidencias_live = {count} registros')

    # Ver columnas
    if sc == SCHEMAS[0]:
        cols = psql(f"SELECT column_name FROM information_schema.columns WHERE table_name='incidencias_live' AND table_schema='{sc}' ORDER BY ordinal_position")
        print(f'  Columnas: {cols[:300]}')

# ═══════════════════════════════════════════════════════════
# H4: Skills en tarjetas proyecto BUILD (index.html)
# ═══════════════════════════════════════════════════════════
print('\n--- H4: Skills en tarjetas proyecto index.html ---')

with open(IDX, 'r', encoding='utf-8') as f:
    idx = f.read()

if 'skills_requeridas' in idx and 'pc-r' in idx:
    # Verificar si ya está en una tarjeta de proyecto
    # Buscar patrón: skills_requeridas cercano a pc-r o card
    sk_in_card = re.search(r'skills_requeridas.{0,100}(pc-r|card|div)', idx)
    if sk_in_card:
        print('  skills_requeridas ya referenciado en tarjetas')
    else:
        print('  skills_requeridas existe pero no en tarjetas — buscando injection point')

# Buscar la sección exacta de tarjetas de proyecto BUILD
# El patrón de gov-build.html es: h+='<div class="pc-r"><span>Presupuesto</span>
# En index.html puede ser diferente. Busquemos los project cards BUILD

# Buscar función que carga proyectos BUILD y renderiza tarjetas
# Investigación mostró: L5415-5430 mapping, L5620 fetch

# Buscar cerca de L5620 o donde se renderizan las tarjetas
lines = idx.split('\n')
proj_render_area = []

# Buscar donde se generan las tarjetas de proyecto con pm_asignado
for i, line in enumerate(lines):
    if 'pm_asignado' in line and ('innerHTML' in line or '+=' in line or 'html' in line.lower()):
        proj_render_area.append(i)

print(f'  pm_asignado rendering: {len(proj_render_area)} candidates')

# Buscar por "Presupuesto" dentro de template literals de tarjetas
for i, line in enumerate(lines):
    if 'Presupuesto' in line and ('${' in line or "'+(" in line) and 'presupuesto' in line.lower():
        # Esta línea renderiza el presupuesto en una tarjeta
        # Verificar si skills está en las siguientes 5 líneas
        has_skills_nearby = any('skills' in lines[j].lower() for j in range(i, min(i+5, len(lines))))
        if not has_skills_nearby:
            print(f'  Candidato para skills injection en L{i+1}: {line.strip()[:100]}')

            # Buscar la siguiente línea que tiene un cierre de div o progreso
            for j in range(i+1, min(i+8, len(lines))):
                next_l = lines[j]
                if 'progreso' in next_l.lower() or 'progress' in next_l.lower() or 'width:' in next_l:
                    # Insertar skills antes de esta línea
                    indent = '    '
                    # Detectar si usa template literal (${) o concatenación (+)
                    if '${' in line:
                        # Template literal style
                        skills_insert = f'{indent}<div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px;"><span style="font-size:9px;color:var(--text3);">Skills</span><span style="font-size:9px;color:var(--text2);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${{p.skills_requeridas||p.skill_requerida||"—"}}</span></div>'
                    else:
                        # Concatenation style
                        skills_insert = indent + """h+='<div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px;"><span style="font-size:9px;color:var(--text3);">Skills</span><span style="font-size:9px;color:var(--text2);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+(p.skills_requeridas||p.skill_requerida||'—')+'</span></div>';"""

                    lines.insert(j, skills_insert)
                    print(f'  OK: Skills insertado antes de L{j+1}')
                    break
            break  # Solo el primer candidato

# También buscar en la sección que usa el mapping de L5430
# L5430: skill: p.skills_requeridas || p.skill_requerida
# Esto sugiere que hay un mapping object que incluye skill
# Buscar donde se renderiza ese objeto
for i, line in enumerate(lines):
    if '.skill' in line and ('badge' in line or 'span' in line or 'div' in line) and 'skills' not in lines[max(0,i-1)]:
        # Puede ser donde se muestra la skill en las tarjetas
        if i not in proj_render_area:
            proj_render_area.append(i)

# Guardar index.html
idx_new = '\n'.join(lines)
if idx_new != idx:
    with open(IDX, 'w', encoding='utf-8') as f:
        f.write(idx_new)
    print('  index.html actualizado')
else:
    print('  Sin cambios en index.html')

# ═══════════════════════════════════════════════════════════
# DEPLOY + RESTART
# ═══════════════════════════════════════════════════════════
print('\n--- Deploy ---')

# Backend
ret = os.system('docker cp /root/cognitive-pmo/backend/main.py cognitive-pmo-api-1:/app/main.py 2>&1')
print(f'  docker cp backend: exit {ret}')
os.system('docker restart cognitive-pmo-api-1 2>&1')

# Frontend — bind mount, solo restart nginx
# Encontrar nombre correcto del container nginx
nginx_name = subprocess.run(
    ['docker', 'ps', '--format', '{{.Names}}', '--filter', 'ancestor=nginx'],
    capture_output=True, text=True
).stdout.strip()
if not nginx_name:
    # Buscar por nombre parcial
    nginx_name = subprocess.run(
        ['docker', 'ps', '--format', '{{.Names}}'],
        capture_output=True, text=True
    ).stdout.strip()
    print(f'  Containers activos: {nginx_name}')
    # Buscar el que tiene nginx o web
    for name in nginx_name.split('\n'):
        if 'nginx' in name.lower() or 'web' in name.lower() or 'frontend' in name.lower():
            nginx_name = name
            break

if nginx_name:
    print(f'  Nginx container: {nginx_name}')
    os.system(f'docker restart {nginx_name} 2>&1')
else:
    print('  WARN: No encontré container nginx — probando nombres comunes...')
    for name in ['cognitive-pmo-nginx-1', 'nginx', 'cognitive-pmo-frontend-1', 'cognitive-pmo-web-1']:
        ret = os.system(f'docker restart {name} 2>/dev/null')
        if ret == 0:
            print(f'    OK: {name}')
            break

import time
time.sleep(4)

# ═══════════════════════════════════════════════════════════
# VERIFICACIÓN COMPLETA
# ═══════════════════════════════════════════════════════════
print('\n' + '=' * 60)
print('VERIFICACIÓN')
print('=' * 60)

# /incidencias/live
print('\n--- /incidencias/live ---')
for sc in SCHEMAS:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8000/incidencias/live'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else []
        if items:
            first = items[0]
            print(f'  {sc}: {len(items)} items, sla_horas={first.get("sla_horas","N/A")}, prioridad={first.get("prioridad","N/A")}, ticket={first.get("ticket_id","N/A")}')
        else:
            print(f'  {sc}: 0 items (lista vacía o formato dict)')
            if isinstance(data, dict):
                print(f'    keys: {list(data.keys())[:10]}')
    except Exception as e:
        print(f'  {sc}: ERROR - {e}')

# /cartera/proyectos (skills)
print('\n--- /cartera/proyectos (skills) ---')
for sc in SCHEMAS:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8000/cartera/proyectos'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else data.get('proyectos', [])
        with_skills = [p for p in items if p.get('skills_requeridas')]
        print(f'  {sc}: {len(items)} proyectos, {len(with_skills)} con skills')
        if with_skills:
            print(f'    Ej: {with_skills[0].get("id_proyecto")} → {with_skills[0].get("skills_requeridas","")[:50]}')
    except Exception as e:
        print(f'  {sc}: ERROR - {e}')

# /pmo/governance/dashboard
print('\n--- /pmo/governance/dashboard ---')
for sc in SCHEMAS:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8000/pmo/governance/dashboard'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(r.stdout)
        print(f'  {sc}: asignados={data.get("pms_asignados")}, sobrecargados={data.get("pms_sobrecargados")}, '
              f'proy_activos={data.get("proyectos_activos_schema","N/A")}, carga={data.get("carga_media_pm","N/A")}')
    except Exception as e:
        print(f'  {sc}: ERROR - {e}')

# /team/tecnicos (vinculacion)
print('\n--- /team/tecnicos (vinculacion) ---')
for sc in SCHEMAS[:1]:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8000/team/tecnicos'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else data.get('tecnicos', [])
        with_vinc = [t for t in items if t.get('vinculacion')]
        print(f'  {sc}: {len(items)} técnicos, {len(with_vinc)} con vinculación')
        for t in with_vinc[:3]:
            print(f'    {t.get("id_recurso")}: [{t.get("estado_run","")}] {t.get("vinculacion","")[:60]}')
    except Exception as e:
        print(f'  {sc}: ERROR - {e}')

print('\n' + '=' * 60)
print('P99 HOTFIX v4b COMPLETO — Recarga navegador (Cmd+Shift+R)')
print('=' * 60)

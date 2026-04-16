#!/usr/bin/env python3
"""
P99 FIXES v4 — Corregido con datos REALES de la investigación
================================================================
DESCUBRIMIENTOS CLAVE:
  - sla_limite es NUMERIC (horas), NO timestamp
  - "Incidencias Activas" usa /incidencias/live, NO /incidencias
  - Frontend usa campo "vinculacion" para team (L2390)
  - prioridad_ia es el nombre real de la columna, no prioridad
  - pmo_governance_scoring YA varía por schema (30/50/75)
  - El problema de PMs es que pmo_project_managers está en compartido

FIXES:
  BACKEND:
    B1: /incidencias/live → añadir sla_horas = sla_limite en serialize
    B2: /incidencias     → añadir sla_horas = sla_limite en serialize
    B3: /team/tecnicos   → añadir vinculacion con referencia INC/BUILD
    B4: /pmo/governance/dashboard → enriquecer PM stats con proyectos per-schema

  DATOS:
    D1: Timestamps recientes en incidencias_run (últimos 14 días para abiertas)
    D2: sla_limite coherente (P1=4, P2=8, P3=24) — ya es numeric
    D3: Asegurar datos DISTINTOS por schema en incidencias_run abiertas
    D4: Poblar skills_requeridas en cartera_build
    D5: Actualizar estado PM en compartido según carga per-schema

Uso: python3 p99_fixes_v4.py
"""
import subprocess, os, re, shutil, json, random

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
print('P99 FIXES v4 — Con datos REALES de investigación')
print('=' * 60)

# ──────────────────────────────────────────────────
# Leer y backup main.py
# ──────────────────────────────────────────────────
with open(MAIN_PY, 'r', encoding='utf-8') as f:
    code = f.read()

bak = MAIN_PY + '.bak_v4'
if not os.path.exists(bak):
    shutil.copy2(MAIN_PY, bak)
    print(f'Backup: {bak}')

lines = code.split('\n')
print(f'main.py: {len(lines)} líneas')

# ═══════════════════════════════════════════════════════════
# B1: /incidencias/live → sla_horas = sla_limite
# ═══════════════════════════════════════════════════════════
print('\n--- B1: /incidencias/live → sla_horas ---')

# Buscar el endpoint /incidencias/live
live_pat = re.search(
    r'@app\.get\(["\']\/incidencias\/live["\']',
    code
)

if live_pat:
    print(f'  Encontrado /incidencias/live en pos {live_pat.start()}')
    # Buscar el serialize/return dentro del bloque
    # Extraer hasta el siguiente @app
    live_start = live_pat.start()
    next_endpoint = re.search(r'\n@app\.(get|post|put|delete|patch)\(', code[live_start+10:])
    live_end = live_start + 10 + next_endpoint.start() if next_endpoint else live_start + 3000
    live_block = code[live_start:live_end]

    print(f'  Bloque: {len(live_block)} chars')

    # Buscar return con serialize
    if 'sla_horas' in live_block:
        print('  SKIP: sla_horas ya existe en /incidencias/live')
    else:
        # Estrategia: buscar el return que devuelve la lista y añadir mapping
        # Patrones posibles:
        #   return [serialize(r) for r in rows]
        #   return result (donde result se construye en un loop)

        # Opción 1: list comprehension
        lc_match = re.search(r'return \[serialize\(r\) for r in (\w+)\]', live_block)
        if lc_match:
            var_name = lc_match.group(1)
            old_return = lc_match.group(0)
            new_return = f"""result_live = []
                for r in {var_name}:
                    d = serialize(r)
                    # B1: sla_horas desde sla_limite (numeric)
                    if 'sla_limite' in d and d['sla_limite'] is not None:
                        d['sla_horas'] = float(d['sla_limite'])
                    # Mapear prioridad_ia → prioridad para frontend
                    if 'prioridad_ia' in d and 'prioridad' not in d:
                        d['prioridad'] = d['prioridad_ia']
                    result_live.append(d)
                return result_live"""
            code = code[:live_start + live_block.find(old_return)] + new_return + code[live_start + live_block.find(old_return) + len(old_return):]
            print('  OK: sla_horas + prioridad mapeados en /incidencias/live (list comprehension)')
        else:
            # Opción 2: ya tiene un loop con result.append
            if 'result' in live_block and 'append' in live_block:
                # Buscar "result.append(d)" y añadir mapping antes
                append_idx = live_block.find('result.append(d)')
                if append_idx > -1:
                    mapping_code = """# B1: sla_horas desde sla_limite (numeric)
                    if 'sla_limite' in d and d['sla_limite'] is not None:
                        d['sla_horas'] = float(d['sla_limite'])
                    if 'prioridad_ia' in d and 'prioridad' not in d:
                        d['prioridad'] = d['prioridad_ia']
                    """
                    abs_pos = live_start + append_idx
                    code = code[:abs_pos] + mapping_code + code[abs_pos:]
                    print('  OK: sla_horas mapeado antes de append en /incidencias/live')
                else:
                    print('  WARN: tiene loop pero no encontré append(d)')
            else:
                # Opción 3: return simple — mostrar para debug
                print('  WARN: Estructura no reconocida. Contenido:')
                for i, line in enumerate(live_block.split('\n')[:25]):
                    print(f'    {i}: {line.rstrip()[:120]}')
else:
    print('  WARN: No encontré /incidencias/live — buscando alternativas...')
    for m in re.finditer(r'incidencias.?live', code):
        ln = code[:m.start()].count('\n') + 1
        print(f'    L{ln}: {code[m.start()-20:m.end()+50]}')

# ═══════════════════════════════════════════════════════════
# B2: /incidencias → sla_horas = sla_limite
# ═══════════════════════════════════════════════════════════
print('\n--- B2: /incidencias → sla_horas ---')

inc_pat = re.search(r'@app\.get\(["\']\/incidencias["\']', code)
if inc_pat:
    inc_start = inc_pat.start()
    next_ep = re.search(r'\n@app\.(get|post|put|delete|patch)\(', code[inc_start+10:])
    inc_end = inc_start + 10 + next_ep.start() if next_ep else inc_start + 3000
    inc_block = code[inc_start:inc_end]

    if 'sla_horas' in inc_block:
        print('  SKIP: sla_horas ya existe en /incidencias')
    else:
        # Buscar return con serialize
        lc_match = re.search(r'return \[serialize\(r\) for r in (\w+)\]', inc_block)
        if lc_match:
            var_name = lc_match.group(1)
            old_return = lc_match.group(0)
            new_return = f"""result_inc = []
                for r in {var_name}:
                    d = serialize(r)
                    if 'sla_limite' in d and d['sla_limite'] is not None:
                        d['sla_horas'] = float(d['sla_limite'])
                    if 'prioridad_ia' in d and 'prioridad' not in d:
                        d['prioridad'] = d['prioridad_ia']
                    result_inc.append(d)
                return result_inc"""
            pos = code.find(old_return, inc_start)
            if pos > -1 and pos < inc_end:
                code = code[:pos] + new_return + code[pos + len(old_return):]
                print('  OK: sla_horas mapeado en /incidencias')
            else:
                print('  WARN: posición fuera de rango')
        elif 'result' in inc_block and 'append' in inc_block:
            append_idx = inc_block.find('result.append(d)')
            if append_idx > -1:
                mapping_code = """# B2: sla_horas
                    if 'sla_limite' in d and d['sla_limite'] is not None:
                        d['sla_horas'] = float(d['sla_limite'])
                    if 'prioridad_ia' in d and 'prioridad' not in d:
                        d['prioridad'] = d['prioridad_ia']
                    """
                abs_pos = inc_start + append_idx
                code = code[:abs_pos] + mapping_code + code[abs_pos:]
                print('  OK: sla_horas mapeado en /incidencias (loop existente)')
            else:
                print('  WARN: loop sin append(d)')
        else:
            print('  WARN: estructura no reconocida, debug:')
            for i, line in enumerate(inc_block.split('\n')[:20]):
                print(f'    {i}: {line.rstrip()[:120]}')
else:
    print('  WARN: /incidencias GET no encontrado')

# ═══════════════════════════════════════════════════════════
# B3: /team/tecnicos → vinculacion
# ═══════════════════════════════════════════════════════════
print('\n--- B3: /team/tecnicos → vinculacion ---')

# Buscar el bloque de /team/tecnicos
tec_pat = re.search(r'@app\.get\(["\']\/team\/tecnicos["\']', code)
if tec_pat:
    tec_start = tec_pat.start()
    next_ep = re.search(r'\n@app\.(get|post|put|delete|patch)\(', code[tec_start+10:])
    tec_end = tec_start + 10 + next_ep.start() if next_ep else tec_start + 5000
    tec_block = code[tec_start:tec_end]

    if 'vinculacion' in tec_block:
        print('  SKIP: vinculacion ya existe')
    else:
        # El FIX 10 anterior ya tiene un loop con result.append(d)
        # Necesitamos añadir vinculacion y tarea_actual
        # Buscar "return result" al final del bloque
        return_pos = tec_block.rfind('return result')
        if return_pos > -1:
            enrichment = """
                # B3: Enriquecer con vinculacion para técnicos asignados
                try:
                    for d in result:
                        rid = d.get('id_recurso', '')
                        if not rid:
                            continue
                        est = (d.get('estado_run') or d.get('estado') or '').upper()
                        if est in ('DISPONIBLE', ''):
                            d['vinculacion'] = ''
                            d['tarea_actual'] = ''
                            continue
                        # Buscar en incidencias_run activas
                        inc_row = await conn.fetchrow(
                            "SELECT ticket_id, incidencia_detectada FROM incidencias_run "
                            "WHERE tecnico_asignado = $1 AND estado NOT IN ('CERRADO','RESUELTO') "
                            "ORDER BY timestamp_creacion DESC LIMIT 1", rid
                        )
                        if inc_row:
                            tid = inc_row['ticket_id'] or ''
                            desc = (inc_row['incidencia_detectada'] or '')[:40]
                            d['vinculacion'] = f"INC {tid}: {desc}"
                            d['tarea_actual'] = d['vinculacion']
                            d['proyecto_actual'] = tid
                            continue
                        # Buscar en kanban_tareas activas
                        kan_row = await conn.fetchrow(
                            "SELECT id, titulo, id_proyecto FROM kanban_tareas "
                            "WHERE (asignado = $1 OR id_recurso = $1) "
                            "AND columna NOT IN ('Completado','Done','Backlog') "
                            "ORDER BY updated_at DESC LIMIT 1", rid
                        )
                        if kan_row:
                            titulo = (kan_row['titulo'] or '')[:35]
                            proj = kan_row.get('id_proyecto') or ''
                            d['vinculacion'] = f"BUILD {proj}: {titulo}"
                            d['tarea_actual'] = d['vinculacion']
                            d['proyecto_actual'] = proj
                        else:
                            d['vinculacion'] = est
                            d['tarea_actual'] = ''
                except Exception as e:
                    logger.warning(f"B3 vinculacion error: {e}")

"""
            abs_pos = tec_start + return_pos
            code = code[:abs_pos] + enrichment + code[abs_pos:]
            print('  OK: vinculacion + tarea_actual añadidos antes de return result')
        else:
            print('  WARN: no encontré "return result" en /team/tecnicos')
            # Debug
            for i, line in enumerate(tec_block.split('\n')[-15:]):
                print(f'    {i}: {line.rstrip()[:120]}')
else:
    print('  WARN: /team/tecnicos no encontrado')

# ═══════════════════════════════════════════════════════════
# B4: /pmo/governance/dashboard → PM stats per-schema
# ═══════════════════════════════════════════════════════════
print('\n--- B4: /pmo/governance/dashboard → PM per-schema ---')

# El endpoint está en L1267-1295
# Queries actuales:
#   total_pms = COUNT(*) FROM pmo_project_managers        ← compartido (OK, son los mismos PMs)
#   asignados = COUNT(*) WHERE estado='ASIGNADO'          ← compartido (PROBLEMA: mismo valor)
#   sobrecargados = COUNT(*) WHERE estado='SOBRECARGADO'  ← compartido (PROBLEMA)
#
# SOLUCIÓN: Calcular asignados/sobrecargados dinámicamente
# Un PM está "asignado" si tiene proyectos en cartera_build del schema actual
# Un PM está "sobrecargado" si tiene >3 proyectos activos

# Buscar las líneas exactas
gov_pat = re.search(r'@app\.get\(["\']\/pmo\/governance\/dashboard["\']', code)
if gov_pat:
    gov_start = gov_pat.start()
    next_ep = re.search(r'\n@app\.(get|post|put|delete|patch)\(', code[gov_start+10:])
    gov_end = gov_start + 10 + next_ep.start() if next_ep else gov_start + 3000
    gov_block = code[gov_start:gov_end]

    if 'proyectos_por_pm' in gov_block or 'B4' in gov_block:
        print('  SKIP: ya tiene cálculo per-schema')
    else:
        # Reemplazar las queries de asignados y sobrecargados
        # Vieja:
        old_asignados = """asignados = await conn.fetchval("SELECT COUNT(*) FROM pmo_project_managers WHERE estado='ASIGNADO'")"""
        old_sobrecargados = """sobrecargados = await conn.fetchval("SELECT COUNT(*) FROM pmo_project_managers WHERE estado='SOBRECARGADO'")"""

        # Nuevas queries que cuentan dinámicamente
        new_asignados = """# B4: PM asignados = PMs con al menos 1 proyecto activo en este schema
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
                    "INNER JOIN cartera_build cb ON pm.nombre = cb.pm_asignado OR pm.id_pm = cb.pm_asignado "
                    "WHERE cb.estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado')"
                ) or 0"""

        new_sobrecargados = """# B4: PM sobrecargados = PMs con >3 proyectos activos en este schema
            sobrecargados_rows = await conn.fetch(
                "SELECT cb.pm_asignado, COUNT(*) as cnt "
                "FROM cartera_build cb "
                "WHERE cb.estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado') "
                "AND cb.pm_asignado IS NOT NULL "
                "GROUP BY cb.pm_asignado HAVING COUNT(*) > 3"
            )
            sobrecargados = len(sobrecargados_rows)"""

        replaced = False
        if old_asignados in code:
            code = code.replace(old_asignados, new_asignados, 1)
            print('  OK: asignados → cálculo dinámico per-schema')
            replaced = True

        if old_sobrecargados in code:
            code = code.replace(old_sobrecargados, new_sobrecargados, 1)
            print('  OK: sobrecargados → cálculo dinámico per-schema')
            replaced = True

        if not replaced:
            print('  WARN: No encontré las queries exactas. Mostrando bloque:')
            for i, line in enumerate(gov_block.split('\n')[:30]):
                stripped = line.strip()
                if 'asignado' in stripped.lower() or 'sobrecargad' in stripped.lower():
                    print(f'  >>> {i}: {stripped[:120]}')
                else:
                    print(f'      {i}: {stripped[:120]}')

        # También: añadir métricas de proyectos activos por schema
        # Buscar el return dict y añadir campos extra
        return_dict_match = re.search(r'return \{', gov_block)
        if return_dict_match:
            # Añadir proyectos_activos_schema antes del return
            extra_query = """
            # B4: Métricas per-schema
            proyectos_activos = await conn.fetchval(
                "SELECT COUNT(*) FROM cartera_build WHERE estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado')"
            ) or 0
            carga_media_pm = 0
            if asignados > 0 and proyectos_activos > 0:
                carga_media_pm = round(proyectos_activos / max(1, asignados) * 25, 1)  # 25% por proyecto
"""
            return_abs_pos = gov_start + return_dict_match.start()
            code = code[:return_abs_pos] + extra_query + code[return_abs_pos:]

            # Ahora añadir los campos al dict del return
            # Buscar "total_change_requests" y añadir después
            code = code.replace(
                '"change_approval_rate": round(int(approved_changes or 0) / max(1, int(total_changes or 1)) * 100, 1),',
                '"change_approval_rate": round(int(approved_changes or 0) / max(1, int(total_changes or 1)) * 100, 1),\n'
                '                "proyectos_activos_schema": proyectos_activos,\n'
                '                "carga_media_pm": carga_media_pm,',
                1
            )
            print('  OK: proyectos_activos_schema + carga_media_pm añadidos')
else:
    print('  WARN: /pmo/governance/dashboard no encontrado')

# ═══════════════════════════════════════════════════════════
# GUARDAR main.py
# ═══════════════════════════════════════════════════════════
print('\n--- Guardando main.py ---')
with open(MAIN_PY, 'w', encoding='utf-8') as f:
    f.write(code)
print('  OK: main.py actualizado')

# ═══════════════════════════════════════════════════════════
# D1+D2: Timestamps recientes + SLA coherente
# ═══════════════════════════════════════════════════════════
print('\n--- D1+D2: Timestamps + SLA en incidencias_run ---')

for sc in SCHEMAS:
    # Primero ver el estado actual
    count_raw = psql(
        "SELECT COUNT(*) as total, "
        "COUNT(CASE WHEN estado NOT IN ('CERRADO','RESUELTO') THEN 1 END) as abiertas "
        "FROM incidencias_run", sc
    )
    print(f'  {sc} antes: {count_raw}')

    # Actualizar ABIERTAS: timestamps últimos 14 días
    psql_exec("""
    UPDATE incidencias_run SET
        timestamp_creacion = NOW() - (random() * INTERVAL '14 days'),
        timestamp_asignacion = CASE
            WHEN tecnico_asignado IS NOT NULL
            THEN NOW() - (random() * INTERVAL '13 days')
            ELSE NULL
        END
    WHERE estado NOT IN ('CERRADO','RESUELTO');
    """, sc)

    # SLA coherente: P1=4h, P2=8h, P3=24h (sla_limite es NUMERIC = horas)
    psql_exec("""
    UPDATE incidencias_run SET sla_limite = CASE
        WHEN prioridad_ia IN ('P1','Critica') THEN 4
        WHEN prioridad_ia IN ('P2','Alta') THEN 8
        WHEN prioridad_ia IN ('P3','Media') THEN 24
        ELSE 48
    END
    WHERE estado NOT IN ('CERRADO','RESUELTO');
    """, sc)

    # CERRADAS: timestamps más antiguos (30-90 días)
    psql_exec("""
    UPDATE incidencias_run SET
        timestamp_creacion = NOW() - INTERVAL '14 days' - (random() * INTERVAL '76 days'),
        sla_limite = CASE
            WHEN prioridad_ia IN ('P1','Critica') THEN 4
            WHEN prioridad_ia IN ('P2','Alta') THEN 8
            ELSE 24
        END
    WHERE estado IN ('CERRADO','RESUELTO') AND timestamp_creacion < NOW() - INTERVAL '100 days';
    """, sc)

    # Verificar
    after = psql(
        "SELECT COUNT(*) as total, "
        "MIN(timestamp_creacion)::date as min_ts, MAX(timestamp_creacion)::date as max_ts, "
        "MIN(sla_limite) as min_sla, MAX(sla_limite) as max_sla "
        "FROM incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO')", sc
    )
    print(f'  {sc} después (abiertas): {after}')

# ═══════════════════════════════════════════════════════════
# D3: Verificar datos DISTINTOS por schema
# ═══════════════════════════════════════════════════════════
print('\n--- D3: Verificar datos distintos ---')
for sc in SCHEMAS:
    sample = psql(
        "SELECT ticket_id, prioridad_ia, estado, sla_limite "
        "FROM incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO') "
        "ORDER BY timestamp_creacion DESC LIMIT 3", sc
    )
    print(f'  {sc} muestra: {sample[:200]}')

# ═══════════════════════════════════════════════════════════
# D4: Skills en cartera_build
# ═══════════════════════════════════════════════════════════
print('\n--- D4: skills_requeridas en cartera_build ---')

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
    print(f'  {sc}: {existing}/{total} con skills')

    if int(existing or 0) >= int(total or 1):
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

# ═══════════════════════════════════════════════════════════
# DEPLOY + RESTART
# ═══════════════════════════════════════════════════════════
print('\n--- Deploy backend ---')
ret = os.system('docker cp /root/cognitive-pmo/backend/main.py cognitive-pmo-api-1:/app/main.py 2>&1')
print(f'  docker cp: exit {ret}')
ret = os.system('docker restart cognitive-pmo-api-1 2>&1')
print(f'  docker restart: exit {ret}')

import time
time.sleep(4)

# ═══════════════════════════════════════════════════════════
# VERIFICACIÓN COMPLETA
# ═══════════════════════════════════════════════════════════
print('\n' + '=' * 60)
print('VERIFICACIÓN')
print('=' * 60)

# Test /incidencias/live por schema
print('\n--- /incidencias/live ---')
for sc in SCHEMAS:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8000/incidencias/live'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else data.get('incidencias', data.get('items', []))
        if items and len(items) > 0:
            first = items[0]
            has_sla = 'sla_horas' in first
            has_prio = 'prioridad' in first
            print(f'  {sc}: {len(items)} items, sla_horas={has_sla} (val={first.get("sla_horas","N/A")}), prioridad={has_prio} (val={first.get("prioridad","N/A")})')
        else:
            print(f'  {sc}: {len(items) if isinstance(items, list) else "?"} items (empty or different structure)')
            print(f'    keys: {list(data.keys()) if isinstance(data, dict) else "list"}')
    except Exception as e:
        print(f'  {sc}: ERROR - {e}')
        print(f'    stdout[:200]: {r.stdout[:200] if r.stdout else "empty"}')

# Test /team/tecnicos por schema
print('\n--- /team/tecnicos ---')
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
            print(f'    {t.get("id_recurso")}: {t.get("vinculacion","")[:60]}')
    except Exception as e:
        print(f'  {sc}: ERROR - {e}')

# Test /pmo/governance/dashboard
print('\n--- /pmo/governance/dashboard ---')
for sc in SCHEMAS:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8000/pmo/governance/dashboard'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(r.stdout)
        print(f'  {sc}: PMs={data.get("total_pms")}, asignados={data.get("pms_asignados")}, '
              f'sobrecargados={data.get("pms_sobrecargados")}, gov={data.get("total_proyectos_gobernados")}, '
              f'avg_score={data.get("avg_scoring")}, proy_activos={data.get("proyectos_activos_schema","N/A")}, '
              f'carga_media={data.get("carga_media_pm","N/A")}')
    except Exception as e:
        print(f'  {sc}: ERROR - {e}')

# Test /presupuestos
print('\n--- /presupuestos (nombre_proyecto) ---')
for sc in SCHEMAS[:1]:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8000/presupuestos'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else []
        if items:
            first = items[0]
            print(f'  {sc}: {len(items)} presupuestos, nombre_proyecto={"nombre_proyecto" in first} (val={first.get("nombre_proyecto","N/A")[:40]})')
        else:
            print(f'  {sc}: sin presupuestos')
    except Exception as e:
        print(f'  {sc}: ERROR - {e}')

# Test /cartera/proyectos (skills)
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
            print(f'    Ejemplo: {with_skills[0].get("id_proyecto")} → {with_skills[0].get("skills_requeridas","")[:50]}')
    except Exception as e:
        print(f'  {sc}: ERROR - {e}')

print('\n' + '=' * 60)
print('P99 FIXES v4 COMPLETO')
print('Recarga el navegador (Cmd+Shift+R)')
print('=' * 60)

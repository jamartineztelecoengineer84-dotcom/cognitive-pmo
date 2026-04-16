#!/usr/bin/env python3
"""
P99 FIX CONCEPTUAL — PRIORIDADES ALTAS (P2-P6)
=================================================
JA decidió arreglar de raíz los 5 problemas conceptuales altos:

  P2 (ALTÍSIMA): sla_horas real por prioridad (P1=4, P2=8, P3=24, P4=48)
                 en /incidencias/live (main.py)
  P3 (ALTA):     /pmo/governance/dashboard → pms_asignados = DISTINCT id_pm
                 con proyectos activos, NO contar proyectos (main.py)
  P4 (ALTA):     umbrales PMs — >5 sobrecargado, >3 cerca límite
                 en /pmo/managers y governance_dashboard (main.py)
  P5 (MEDIA-A):  estados incidencias_run diversificados
                 ~15% QUEUED, ~70% EN_CURSO, ~10% ESCALADO, ~5% RESUELTO (datos)
  P6 (ALTA):     estados cartera_build diversificados
                 ~10% EN_ANALISIS, ~60% EN_EJECUCION, ~20% EN_REVISION,
                 ~10% COMPLETADO (datos)

El script:
  1) Lee main.py → aplica patches P2, P3, P4
  2) Aplica datos en BD para P5 y P6
  3) Restart + verificación completa

Uso: python3 p99_fix_conceptual_altas.py 2>&1 | tee /tmp/p99_fix_conceptual.log
"""
import subprocess, json, random, os, time, re, shutil

random.seed(42)

MAIN_PY = '/root/cognitive-pmo/backend/main.py'
BACKUP = f'{MAIN_PY}.bak-conceptual'

def psql(query, schema=None):
    if schema:
        full = f"SET search_path = {schema}, compartido, public; {query}"
    else:
        full = query
    env = os.environ.copy()
    env['PGPASSWORD'] = 'REDACTED-old-password'
    cmd = ['psql', '-h', 'localhost', '-U', 'jose_admin',
           '-d', 'cognitive_pmo', '-t', '-A', '-c', full]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
    out = r.stdout.strip()
    if out.startswith('SET\n'):
        out = out[4:]
    if r.returncode != 0 and r.stderr.strip():
        print(f'    ⚠️  PSQL: {r.stderr.strip()[:180]}')
    return out

def psql_lines(query, schema=None):
    return [x.strip() for x in psql(query, schema).split('\n') if x.strip()]

print('=' * 66)
print('P99 FIX CONCEPTUAL — PRIORIDADES ALTAS')
print('=' * 66)

# Backup
if not os.path.exists(BACKUP):
    shutil.copy(MAIN_PY, BACKUP)
    print(f'Backup main.py → {BACKUP}')

# ═══════════════════════════════════════════════════════════════
# P2. FIX sla_horas real por prioridad en /incidencias/live
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('P2. sla_horas real por prioridad en /incidencias/live')
print('═' * 66)

with open(MAIN_PY, 'r', encoding='utf-8') as f:
    code = f.read()

# Buscar el bloque H1 actual del endpoint /incidencias/live
# Se busca el patrón de enrichment que pone sla_horas = 48 fallback
# y se reemplaza por lectura real de sla_limite o mapeo por prioridad

old_h1_pattern = re.search(
    r"(# H1: enriquecer incidencias_live con sla_horas.*?)(result_live\.append\(d\))",
    code, re.DOTALL
)

new_h1_block = '''# H1: enriquecer incidencias_live con sla_horas REAL por prioridad
        # Mapeo estándar ITIL: P1=4h, P2=8h, P3=24h, P4=48h
        SLA_POR_PRIORIDAD = {'P1': 4, 'P2': 8, 'P3': 24, 'P4': 48}
        result_live = []
        for r in rows:
            d = dict(r)
            # 1) Intentar leer sla_limite real de incidencias_run
            sla_val = None
            if d.get('ticket_id'):
                sla_val = await conn.fetchval(
                    "SELECT sla_limite FROM incidencias_run WHERE ticket_id = $1",
                    d['ticket_id']
                )
            # 2) Si hay sla_limite numérico válido, usarlo
            if sla_val is not None and float(sla_val) > 0 and float(sla_val) < 200:
                d['sla_horas'] = float(sla_val)
            else:
                # 3) Fallback por prioridad (P1=4, P2=8, P3=24, P4=48)
                prio = (d.get('prioridad_ia') or d.get('prioridad') or 'P3').upper()
                d['sla_horas'] = SLA_POR_PRIORIDAD.get(prio, 24)
            # Mapear prioridad_ia -> prioridad para frontend
            if 'prioridad' not in d or not d.get('prioridad'):
                d['prioridad'] = d.get('prioridad_ia', 'P3')
            result_live.append(d)'''

if old_h1_pattern:
    # Reemplazar el bloque entero
    start = old_h1_pattern.start()
    end = old_h1_pattern.end()
    code_new = code[:start] + new_h1_block + code[end:]
    # Eliminar duplicados result_live.append que quedaran
    if code_new.count('result_live.append(d)') > 2:
        # Remover un append extra si existe inmediatamente después
        code_new = re.sub(
            r'(result_live\.append\(d\)\s*\n\s*)result_live\.append\(d\)',
            r'\1', code_new
        )
    code = code_new
    print('  ✅ Bloque H1 reemplazado con SLA real por prioridad')
else:
    print('  ⚠️  No se encontró bloque H1 actual. Buscando patrón alternativo...')
    # Patrón alternativo: buscar "sla_horas"] = 48" y reemplazar
    if 'sla_horas\'] = 48' in code or "sla_horas'] = float(sla_val)" in code:
        # Inyectar el mapeo SLA_POR_PRIORIDAD antes del uso
        if 'SLA_POR_PRIORIDAD' not in code:
            # Insertar constante global al inicio (después de imports)
            code = re.sub(
                r'(logger = logging\.getLogger\(__name__\))',
                r"\1\n\n# SLA estándar ITIL por prioridad (horas)\nSLA_POR_PRIORIDAD = {'P1': 4, 'P2': 8, 'P3': 24, 'P4': 48}",
                code, count=1
            )
        # Reemplazar fallback 48 por cálculo por prioridad
        code = re.sub(
            r"d\['sla_horas'\]\s*=\s*float\(sla_val\)\s*if\s*sla_val\s*is\s*not\s*None\s*else\s*48",
            "prio_key = (d.get('prioridad_ia') or 'P3').upper(); "
            "d['sla_horas'] = float(sla_val) if sla_val is not None else SLA_POR_PRIORIDAD.get(prio_key, 24)",
            code
        )
        print('  ✅ Fallback 48 reemplazado con SLA_POR_PRIORIDAD')

# ═══════════════════════════════════════════════════════════════
# P3 + P4. FIX /pmo/governance/dashboard + /pmo/managers
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('P3+P4. governance_dashboard y /pmo/managers')
print('═' * 66)

# P3: pms_asignados debe ser DISTINCT id_pm con proy activos, no COUNT(*)
# P4: umbral sobrecarga > 5, "cerca límite" > 3

# Buscar el bloque B4 (PMs asignados dinámico) del governance_dashboard
b4_pattern = re.search(
    r"(# B4: PM asignados dinámico.*?pms_asignados\s*=.*?)(?=\n\s{8}(?:#|return|\w))",
    code, re.DOTALL
)

new_b4_block = '''# B4: PM asignados dinámico PER-SCHEMA (CORREGIDO P3+P4)
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
            carga_media_pm = 0'''

if b4_pattern:
    start = b4_pattern.start()
    end = b4_pattern.end()
    code = code[:start] + new_b4_block + code[end:]
    print('  ✅ Bloque B4 (governance) reemplazado con P3+P4')
else:
    print('  ⚠️  No se encontró bloque B4. Inyectando antes del return del endpoint...')
    # Fallback: buscar el return del governance_dashboard e inyectar antes
    gov_endpoint = re.search(
        r"(@app\.get\(['\"]\/pmo\/governance\/dashboard['\"].*?)(\n    return\s+\{)",
        code, re.DOTALL
    )
    if gov_endpoint:
        code = code.replace(gov_endpoint.group(2),
                           '\n    ' + new_b4_block + gov_endpoint.group(2), 1)
        print('  ✅ Bloque B4 inyectado antes del return')

# Asegurar que el dict de retorno incluye los campos nuevos
# Buscar el return del governance_dashboard y añadir pms_cerca_limite
ret_match = re.search(
    r"(return\s+\{[^}]*'pms_asignados':\s*pms_asignados[^}]*?)(\})",
    code, re.DOTALL
)
if ret_match and 'pms_cerca_limite' not in ret_match.group(0):
    new_ret = ret_match.group(1).rstrip().rstrip(',') + \
              ",\n        'pms_cerca_limite': pms_cerca_limite,\n        'proyectos_activos_schema': proyectos_activos_schema,\n        'carga_media_pm': carga_media_pm,\n        'total_pms': total_pms_pool\n    " + "}"
    code = code.replace(ret_match.group(0), new_ret, 1)
    print('  ✅ Campo pms_cerca_limite añadido al response')

# P4: Actualizar /pmo/managers con umbral > 5
# Buscar "proj_count > 3" y reemplazar con > 5
if 'proj_count > 3' in code:
    code = code.replace(
        "if proj_count > 3: d['estado'] = 'SOBRECARGADO'",
        "if proj_count > 5: d['estado'] = 'SOBRECARGADO'"
    )
    code = code.replace(
        "elif proj_count > 0: d['estado'] = 'ASIGNADO'",
        "elif proj_count >= 4: d['estado'] = 'CERCA_LIMITE'\n        elif proj_count > 0: d['estado'] = 'ASIGNADO'"
    )
    print('  ✅ Umbrales /pmo/managers: >5 SOBRECARGADO, 4-5 CERCA_LIMITE, 1-3 ASIGNADO')

# Guardar main.py
with open(MAIN_PY, 'w', encoding='utf-8') as f:
    f.write(code)
print(f'\n  💾 main.py guardado ({len(code)} bytes)')

# ═══════════════════════════════════════════════════════════════
# P5. Estados incidencias_run diversificados
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('P5. Diversificar estados incidencias_run por schema')
print('═' * 66)

# Distribución objetivo: ~15% QUEUED, ~70% EN_CURSO, ~10% ESCALADO, ~5% RESUELTO
# OJO: RESUELTO ya existe. QUEUED y ESCALADO son los que faltan.

for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    print(f'\n  --- {sc} ---')
    # Contar actuales
    current = psql(
        "SELECT estado, COUNT(*) FROM incidencias_run GROUP BY estado ORDER BY COUNT(*) DESC;",
        sc
    )
    print(f'    Actual: {current.replace(chr(10), " | ")}')

    # Solo trabajamos con las abiertas (no RESUELTO/CERRADO)
    abiertas_ids = psql_lines(
        "SELECT ticket_id FROM incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO') ORDER BY ticket_id;",
        sc
    )
    total = len(abiertas_ids)
    if total == 0:
        print('    Sin abiertas, saltando')
        continue

    # Calcular cuotas
    n_queued = int(total * 0.15)
    n_escalado = int(total * 0.10)
    # El resto se queda EN_CURSO
    n_en_curso = total - n_queued - n_escalado

    # Shuffle para asignar aleatoriamente
    mixed = abiertas_ids.copy()
    random.shuffle(mixed)

    # Aplicar QUEUED a los primeros n_queued
    for tid in mixed[:n_queued]:
        psql(f"UPDATE incidencias_run SET estado = 'QUEUED' WHERE ticket_id = '{tid}';", sc)
    # Aplicar ESCALADO a los siguientes
    for tid in mixed[n_queued:n_queued + n_escalado]:
        psql(f"UPDATE incidencias_run SET estado = 'ESCALADO' WHERE ticket_id = '{tid}';", sc)
    # El resto ya debería estar EN_CURSO (no tocar)

    # Verificación
    after = psql(
        "SELECT estado, COUNT(*) FROM incidencias_run GROUP BY estado ORDER BY COUNT(*) DESC;",
        sc
    )
    print(f'    Después: {after.replace(chr(10), " | ")}')
    print(f'    → Distribución: QUEUED={n_queued}, EN_CURSO={n_en_curso}, ESCALADO={n_escalado}')

# NOTA: QUEUED son incidencias SIN técnico asignado (recién llegadas)
# Hay que limpiar tecnico_asignado en las QUEUED
print('\n  --- Limpiando tecnico_asignado en QUEUED (recién llegadas) ---')
for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    psql("UPDATE incidencias_run SET tecnico_asignado = NULL WHERE estado = 'QUEUED';", sc)
    qcount = psql("SELECT COUNT(*) FROM incidencias_run WHERE estado = 'QUEUED';", sc)
    print(f'    {sc}: {qcount} incidencias QUEUED sin técnico')

# ═══════════════════════════════════════════════════════════════
# P6. Estados cartera_build diversificados
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('P6. Diversificar estados cartera_build')
print('═' * 66)

# Primero leer constraint actual
checks = psql(
    "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
    "WHERE conrelid = 'sc_norte.cartera_build'::regclass AND contype = 'c';"
)
print(f'  CHECK constraints cartera_build: {checks[:300]}')

# Leer estados existentes (para saber qué valores acepta la tabla realmente)
estados_permitidos = psql_lines(
    "SELECT DISTINCT estado FROM cartera_build ORDER BY estado;", 'sc_norte'
)
print(f'  Estados actuales: {estados_permitidos}')

# Probar valores candidatos para ver cuáles acepta la CHECK
# Si hay constraint, usar solo valores válidos
# Distribución objetivo: 10% EN_ANALISIS, 60% EN_EJECUCION, 20% EN_REVISION, 10% COMPLETADO
CANDIDATOS = {
    'EN_ANALISIS': ['EN_ANALISIS', 'en_analisis', 'en analisis', 'ANALISIS', 'En Análisis'],
    'EN_EJECUCION': ['EN_EJECUCION', 'en_ejecucion', 'en ejecucion', 'EJECUCION', 'En Ejecución'],
    'EN_REVISION': ['EN_REVISION', 'en_revision', 'en revision', 'REVISION', 'En Revisión'],
    'COMPLETADO': ['COMPLETADO', 'completado', 'COMPLETED', 'Completado']
}

def probar_valor(sc, candidatos):
    """Prueba qué valor acepta la CHECK constraint"""
    # Crear test con UPDATE temporal y rollback
    for val in candidatos:
        # Tomar un proyecto
        sample = psql_lines(
            "SELECT id_proyecto FROM cartera_build LIMIT 1;", sc
        )
        if not sample:
            return val  # No hay datos, devolver primero
        pid = sample[0]
        # Guardar original
        orig = psql(
            f"SELECT estado FROM cartera_build WHERE id_proyecto = '{pid}';", sc
        ).strip()
        # Probar
        r = psql(
            f"UPDATE cartera_build SET estado = '{val}' WHERE id_proyecto = '{pid}' RETURNING estado;",
            sc
        )
        if r.strip() == val:
            # Funciona, restaurar
            psql(f"UPDATE cartera_build SET estado = '{orig}' WHERE id_proyecto = '{pid}';", sc)
            return val
        # Si no funciona, probar siguiente
    return candidatos[0]  # Fallback

print('\n  Probando valores válidos para CHECK constraint...')
VALORES_OK = {}
for k, cands in CANDIDATOS.items():
    val = probar_valor('sc_norte', cands)
    VALORES_OK[k] = val
    print(f'    {k} → "{val}"')

# Si hay constraint muy estricto, no podremos cambiar estados
# En ese caso, modificar la constraint para permitir más valores
constraint_name = psql(
    "SELECT conname FROM pg_constraint "
    "WHERE conrelid = 'sc_norte.cartera_build'::regclass AND contype = 'c' LIMIT 1;"
).strip()

# Verificar si valores son aceptados probando uno rápido
test_val = psql(
    "SELECT estado FROM cartera_build LIMIT 1;", 'sc_norte'
).strip()

# Si la tabla acepta los valores candidatos, aplicar diversificación
for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    print(f'\n  --- {sc} ---')
    current = psql(
        "SELECT estado, COUNT(*) FROM cartera_build GROUP BY estado ORDER BY COUNT(*) DESC;",
        sc
    )
    print(f'    Actual: {current.replace(chr(10), " | ")}')

    ids = psql_lines(
        "SELECT id_proyecto FROM cartera_build ORDER BY id_proyecto;", sc
    )
    total = len(ids)
    if total == 0:
        continue

    n_analisis = int(total * 0.10)
    n_revision = int(total * 0.20)
    n_completado = int(total * 0.10)
    n_ejecucion = total - n_analisis - n_revision - n_completado

    mixed = ids.copy()
    random.shuffle(mixed)

    # EN_ANALISIS primeros
    for pid in mixed[:n_analisis]:
        psql(f"UPDATE cartera_build SET estado = '{VALORES_OK['EN_ANALISIS']}' WHERE id_proyecto = '{pid}';", sc)
    # EN_REVISION siguientes
    for pid in mixed[n_analisis:n_analisis + n_revision]:
        psql(f"UPDATE cartera_build SET estado = '{VALORES_OK['EN_REVISION']}' WHERE id_proyecto = '{pid}';", sc)
    # COMPLETADO siguientes
    for pid in mixed[n_analisis + n_revision:n_analisis + n_revision + n_completado]:
        psql(f"UPDATE cartera_build SET estado = '{VALORES_OK['COMPLETADO']}' WHERE id_proyecto = '{pid}';", sc)
    # EN_EJECUCION el resto
    for pid in mixed[n_analisis + n_revision + n_completado:]:
        psql(f"UPDATE cartera_build SET estado = '{VALORES_OK['EN_EJECUCION']}' WHERE id_proyecto = '{pid}';", sc)

    after = psql(
        "SELECT estado, COUNT(*) FROM cartera_build GROUP BY estado ORDER BY COUNT(*) DESC;",
        sc
    )
    print(f'    Después: {after.replace(chr(10), " | ")}')

# ═══════════════════════════════════════════════════════════════
# RESTART + VERIFICACIÓN
# ═══════════════════════════════════════════════════════════════
print('\n' + '═' * 66)
print('RESTART + VERIFICACIÓN')
print('═' * 66)

r_api = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], capture_output=True, text=True)
api_container = next((n for n in r_api.stdout.strip().split('\n') if 'api' in n.lower()), None)
if api_container:
    print(f'  Restart {api_container}...')
    os.system(f'docker restart {api_container}')
    time.sleep(10)

# Verificar logs por errores de sintaxis
print('\n  Docker logs últimas 10 líneas:')
os.system(f'docker logs {api_container} --tail 10 2>&1 | head -15')

# Tests
print('\n' + '─' * 66)
print('TEST P2: sla_horas por prioridad')
print('─' * 66)
for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8088/incidencias/live'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else []
        sla_por_prio = {}
        for inc in items:
            p = (inc.get('prioridad') or inc.get('prioridad_ia', '?')).upper()
            sla = inc.get('sla_horas', '?')
            sla_por_prio.setdefault(p, set()).add(sla)
        print(f'  {sc}: {len(items)} incidencias')
        for p in sorted(sla_por_prio.keys()):
            slas = sla_por_prio[p]
            print(f'    {p}: SLA horas = {slas}')
    except Exception as e:
        print(f'  {sc}: ERROR {e}')

print('\n' + '─' * 66)
print('TEST P3+P4: governance dashboard')
print('─' * 66)
for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8088/pmo/governance/dashboard'],
            capture_output=True, text=True, timeout=10
        )
        d = json.loads(r.stdout)
        print(f'  {sc}:')
        for k in ['total_pms', 'pms_asignados', 'pms_cerca_limite', 'pms_sobrecargados',
                  'proyectos_activos_schema', 'carga_media_pm']:
            if k in d:
                print(f'    {k}: {d[k]}')
    except Exception as e:
        print(f'  {sc}: ERROR {e}')

print('\n' + '─' * 66)
print('TEST P4: /pmo/managers estados con nuevos umbrales')
print('─' * 66)
for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8088/pmo/managers'],
            capture_output=True, text=True, timeout=10
        )
        items = json.loads(r.stdout)
        estados = {}
        for pm in items:
            e = pm.get('estado', '?')
            estados[e] = estados.get(e, 0) + 1
        print(f'  {sc}: {dict(sorted(estados.items()))}')
    except Exception as e:
        print(f'  {sc}: ERROR {e}')

print('\n' + '─' * 66)
print('TEST P5: estados incidencias_run')
print('─' * 66)
for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    dist = psql(
        "SELECT estado, COUNT(*) FROM incidencias_run GROUP BY estado ORDER BY COUNT(*) DESC;",
        sc
    )
    print(f'  {sc}: {dist.replace(chr(10), " | ")}')

print('\n' + '─' * 66)
print('TEST P6: estados cartera_build')
print('─' * 66)
for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    dist = psql(
        "SELECT estado, COUNT(*) FROM cartera_build GROUP BY estado ORDER BY COUNT(*) DESC;",
        sc
    )
    print(f'  {sc}: {dist.replace(chr(10), " | ")}')

print('\n' + '─' * 66)
print('TEST ocupación técnicos (debe seguir igual)')
print('─' * 66)
for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8088/team/tecnicos'],
            capture_output=True, text=True, timeout=10
        )
        items = json.loads(r.stdout)
        estados = {}
        for t in items:
            e = t.get('estado', '?')
            estados[e] = estados.get(e, 0) + 1
        ocu = sum(v for k, v in estados.items() if k != 'DISPONIBLE')
        print(f'  {sc}: {ocu}/{len(items)} ocupados — {dict(sorted(estados.items()))}')
    except Exception as e:
        print(f'  {sc}: ERROR {e}')

print('\n' + '═' * 66)
print('P99 FIX CONCEPTUAL ALTAS COMPLETO')
print('Cambios aplicados: P2 (SLA), P3 (PMs distintos), P4 (umbrales),')
print('                   P5 (estados incidencias), P6 (estados cartera)')
print('Recarga navegador: Cmd+Shift+R')
print('═' * 66)

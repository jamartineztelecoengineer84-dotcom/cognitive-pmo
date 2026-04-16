#!/usr/bin/env python3
"""
P99 FIX OCUPACIÓN v3 — Lee CHECK constraints, luego actúa
===========================================================
v1: pocas filas donde asignar técnicos
v2: CHECK constraints rechazaron estados/columnas inventados
v3: PRIMERO lee los valores válidos de la BD, LUEGO opera

Uso: python3 p99_fix_occupation_v3.py 2>&1 | tee /tmp/p99_fix_occ_v3.log
"""
import subprocess, json, random, os, time, re

random.seed(42)

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
    return out

def psql_lines(query, schema=None):
    """Devuelve lista limpia de líneas no vacías"""
    raw = psql(query, schema)
    return [x.strip() for x in raw.split('\n') if x.strip()]

print('=' * 60)
print('P99 FIX OCUPACIÓN v3 — SMART CONSTRAINTS')
print('=' * 60)

# ═══════════════════════════════════════════════════════════
# PASO 0: DESCUBRIR estructura real de las tablas
# ═══════════════════════════════════════════════════════════
print('\n--- 0. Descubriendo estructura de tablas ---')

# 0a. Columnas de incidencias_run
inc_cols_raw = psql(
    "SELECT column_name, is_nullable, data_type FROM information_schema.columns "
    "WHERE table_name = 'incidencias_run' AND table_schema = 'sc_norte' "
    "ORDER BY ordinal_position;")
print(f'\n  incidencias_run columnas:')
for line in inc_cols_raw.split('\n'):
    if line.strip():
        print(f'    {line.strip()}')

# 0b. CHECK constraints de incidencias_run
inc_checks = psql(
    "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
    "WHERE conrelid = 'sc_norte.incidencias_run'::regclass AND contype = 'c';")
print(f'\n  incidencias_run CHECK constraints:')
for line in inc_checks.split('\n'):
    if line.strip():
        print(f'    {line.strip()}')

# 0c. Valores REALES de estado en incidencias_run
inc_estados_reales = psql_lines(
    "SELECT DISTINCT estado FROM incidencias_run ORDER BY estado;", 'sc_norte')
print(f'\n  incidencias_run estados reales: {inc_estados_reales}')

# 0d. Columnas de kanban_tareas
kan_cols_raw = psql(
    "SELECT column_name, is_nullable, data_type FROM information_schema.columns "
    "WHERE table_name = 'kanban_tareas' AND table_schema = 'sc_norte' "
    "ORDER BY ordinal_position;")
print(f'\n  kanban_tareas columnas:')
for line in kan_cols_raw.split('\n'):
    if line.strip():
        print(f'    {line.strip()}')

# 0e. CHECK constraints de kanban_tareas
kan_checks = psql(
    "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
    "WHERE conrelid = 'sc_norte.kanban_tareas'::regclass AND contype = 'c';")
print(f'\n  kanban_tareas CHECK constraints:')
for line in kan_checks.split('\n'):
    if line.strip():
        print(f'    {line.strip()}')

# 0f. Valores REALES de columna en kanban_tareas
kan_columnas_reales = psql_lines(
    "SELECT DISTINCT columna FROM kanban_tareas ORDER BY columna;", 'sc_norte')
print(f'\n  kanban_tareas columnas reales: {kan_columnas_reales}')

# 0g. Valores REALES de tipo en kanban_tareas
kan_tipos_reales = psql_lines(
    "SELECT DISTINCT tipo FROM kanban_tareas WHERE tipo IS NOT NULL ORDER BY tipo;", 'sc_norte')
print(f'\n  kanban_tareas tipos reales: {kan_tipos_reales}')

# 0h. Valores REALES de prioridad en kanban_tareas
kan_prio_reales = psql_lines(
    "SELECT DISTINCT prioridad FROM kanban_tareas WHERE prioridad IS NOT NULL ORDER BY prioridad;", 'sc_norte')
print(f'\n  kanban_tareas prioridades reales: {kan_prio_reales}')

# 0i. Una fila de ejemplo de incidencias_run
inc_sample = psql("SELECT * FROM incidencias_run LIMIT 1;", 'sc_norte')
print(f'\n  incidencias_run sample row: {inc_sample[:300]}')

# 0j. Una fila de ejemplo de kanban_tareas
kan_sample = psql("SELECT * FROM kanban_tareas LIMIT 1;", 'sc_norte')
print(f'\n  kanban_tareas sample row: {kan_sample[:300]}')

# ═══════════════════════════════════════════════════════════
# PASO 1: Determinar estados/columnas válidos "abiertos"
# ═══════════════════════════════════════════════════════════
print('\n--- 1. Determinando valores válidos ---')

# Estados ABIERTOS = todos los que NO son cerrado/resuelto
ESTADOS_CERRADOS = set()
for e in inc_estados_reales:
    if e.upper() in ('CERRADO', 'RESUELTO', 'COMPLETADO'):
        ESTADOS_CERRADOS.add(e)

ESTADOS_ABIERTOS = [e for e in inc_estados_reales if e not in ESTADOS_CERRADOS]
print(f'  Estados abiertos incidencias: {ESTADOS_ABIERTOS}')
print(f'  Estados cerrados incidencias: {ESTADOS_CERRADOS}')

if not ESTADOS_ABIERTOS:
    ESTADOS_ABIERTOS = ['Abierto']  # fallback
    print('  WARN: No se encontraron estados abiertos, usando fallback')

# Columnas ACTIVAS kanban = todos los que NO son Completado/Done/Backlog
COLUMNAS_CERRADAS = set()
for c in kan_columnas_reales:
    if c in ('Completado', 'Done', 'Backlog', 'Cerrado'):
        COLUMNAS_CERRADAS.add(c)

COLUMNAS_ACTIVAS = [c for c in kan_columnas_reales if c not in COLUMNAS_CERRADAS]
print(f'  Columnas activas kanban: {COLUMNAS_ACTIVAS}')
print(f'  Columnas cerradas kanban: {COLUMNAS_CERRADAS}')

if not COLUMNAS_ACTIVAS:
    COLUMNAS_ACTIVAS = ['En Progreso']
    print('  WARN: No se encontraron columnas activas, usando fallback')

# ═══════════════════════════════════════════════════════════
# PASO 2: Pool de técnicos
# ═══════════════════════════════════════════════════════════
print('\n--- 2. Pool de técnicos ---')
all_ftes = psql_lines("SELECT id_recurso FROM compartido.pmo_staff_skills ORDER BY id_recurso;")
all_ftes = [x for x in all_ftes if x.startswith('FTE-')]
print(f'  Total: {len(all_ftes)}')
if len(all_ftes) < 50:
    print('  ERROR: Pool < 50, abortando')
    exit(1)

# ═══════════════════════════════════════════════════════════
# PASO 3: Fix por schema
# ═══════════════════════════════════════════════════════════
BANKS = {
    'sc_norte':   {'target': 60,  'label': 'Pequeño (30 proy)'},
    'sc_iberico': {'target': 82,  'label': 'Mediano (50 proy)'},
    'sc_litoral': {'target': 112, 'label': 'Grande (75 proy)'},
}

TAREAS_TITULOS = [
    'Configuración entorno', 'Desarrollo módulo core', 'Integración API REST',
    'Testing unitario', 'Revisión código PR', 'Documentación técnica',
    'Deploy staging', 'Migración datos', 'Optimización queries',
    'Corrección bugs sprint', 'Refactoring módulo', 'Setup CI/CD',
    'Diseño schema BD', 'Cache Redis', 'Monitorización Grafana',
    'Tests E2E', 'Hardening seguridad', 'Performance tuning',
    'Integración SSO', 'API gateway config'
]

for sc, cfg in BANKS.items():
    target = cfg['target']
    # ~60% via incidencias, ~55% via kanban (con overlap → target únicos)
    inc_need = int(target * 0.6)
    kan_need = int(target * 0.55)

    print(f'\n{"═" * 60}')
    print(f'  {sc} — {cfg["label"]} — Objetivo: {target}/150 ocupados')
    print(f'  Necesito: {inc_need} en INC + {kan_need} en KAN (con overlap)')
    print(f'{"═" * 60}')

    shuffled = all_ftes.copy()
    random.shuffle(shuffled)
    inc_ftes = shuffled[:inc_need]
    # Overlap: los últimos 15% de inc_ftes también en kanban
    overlap_start = inc_need - int(inc_need * 0.15)
    kan_ftes = shuffled[overlap_start:overlap_start + kan_need]
    if len(kan_ftes) < kan_need:
        kan_ftes = shuffled[:kan_need]

    # ─── A. INCIDENCIAS ───
    print(f'\n  --- A. Incidencias ---')
    # ¿Cuántas abiertas hay?
    open_n = int(psql(
        f"SELECT COUNT(*) FROM incidencias_run WHERE estado NOT IN ({','.join(repr(e) for e in ESTADOS_CERRADOS)});", sc) or '0')
    total_n = int(psql("SELECT COUNT(*) FROM incidencias_run;", sc) or '0')
    print(f'  Total: {total_n}, Abiertas: {open_n}, Necesito: {inc_need}')

    if open_n < inc_need:
        # Reabrir cerradas usando SOLO estados válidos
        need_reopen = min(inc_need - open_n, total_n - open_n)
        if need_reopen > 0:
            cerradas_ids = psql_lines(
                f"SELECT ticket_id FROM incidencias_run WHERE estado IN ({','.join(repr(e) for e in ESTADOS_CERRADOS)}) "
                f"LIMIT {need_reopen};", sc)
            print(f'  Reabriendo {len(cerradas_ids)} con estados válidos: {ESTADOS_ABIERTOS}')
            for i, tid in enumerate(cerradas_ids):
                nuevo_estado = ESTADOS_ABIERTOS[i % len(ESTADOS_ABIERTOS)]
                psql(f"UPDATE incidencias_run SET estado = '{nuevo_estado}' WHERE ticket_id = '{tid}';", sc)

        # Re-check
        open_n = int(psql(
            f"SELECT COUNT(*) FROM incidencias_run WHERE estado NOT IN ({','.join(repr(e) for e in ESTADOS_CERRADOS)});", sc) or '0')
        print(f'  Abiertas después de reabrir: {open_n}')

    # Asignar técnicos
    open_ids = psql_lines(
        f"SELECT ticket_id FROM incidencias_run WHERE estado NOT IN ({','.join(repr(e) for e in ESTADOS_CERRADOS)}) "
        f"ORDER BY ticket_id;", sc)
    updates = []
    for i, tid in enumerate(open_ids):
        fte = inc_ftes[i % len(inc_ftes)]
        updates.append(f"UPDATE incidencias_run SET tecnico_asignado = '{fte}' WHERE ticket_id = '{tid}';")
    for start in range(0, len(updates), 40):
        psql('\n'.join(updates[start:start+40]), schema=sc)
    distinct_inc = len(set(inc_ftes[:len(open_ids)]))
    print(f'  OK: {len(open_ids)} incidencias con {min(len(inc_ftes), len(open_ids))} técnicos asignados')

    # ─── B. KANBAN ───
    print(f'\n  --- B. Kanban ---')
    active_n = int(psql(
        f"SELECT COUNT(*) FROM kanban_tareas WHERE columna NOT IN ({','.join(repr(c) for c in COLUMNAS_CERRADAS)});", sc) or '0')
    total_kan = int(psql("SELECT COUNT(*) FROM kanban_tareas;", sc) or '0')
    print(f'  Total: {total_kan}, Activas: {active_n}, Necesito: {kan_need}')

    if active_n < kan_need:
        # Mover completadas a activas usando SOLO columnas válidas
        need_activate = min(kan_need - active_n, total_kan - active_n)
        if need_activate > 0:
            completadas_ids = psql_lines(
                f"SELECT id FROM kanban_tareas WHERE columna IN ({','.join(repr(c) for c in COLUMNAS_CERRADAS)}) "
                f"LIMIT {need_activate};", sc)
            print(f'  Activando {len(completadas_ids)} con columnas válidas: {COLUMNAS_ACTIVAS}')
            for i, kid in enumerate(completadas_ids):
                nueva_col = COLUMNAS_ACTIVAS[i % len(COLUMNAS_ACTIVAS)]
                psql(f"UPDATE kanban_tareas SET columna = '{nueva_col}' WHERE id = '{kid}';", sc)

        # Re-check
        active_n = int(psql(
            f"SELECT COUNT(*) FROM kanban_tareas WHERE columna NOT IN ({','.join(repr(c) for c in COLUMNAS_CERRADAS)});", sc) or '0')

        # Si aún faltan, crear nuevas con TODOS los campos NOT NULL
        if active_n < kan_need:
            still_need = kan_need - active_n
            print(f'  Creando {still_need} tareas nuevas...')
            # Obtener proyectos
            proyectos = psql_lines(
                "SELECT id_proyecto FROM cartera_build ORDER BY id_proyecto;", sc)
            prefix = sc[-3:].upper()
            tipo_default = kan_tipos_reales[0] if kan_tipos_reales else 'BUILD'
            prio_default = kan_prio_reales[0] if kan_prio_reales else 'Media'

            for i in range(still_need):
                task_id = f'KAN-{prefix}-{8000+i:04d}'
                prj = proyectos[i % len(proyectos)] if proyectos else f'PRJ-{prefix}-001'
                col = COLUMNAS_ACTIVAS[i % len(COLUMNAS_ACTIVAS)]
                titulo = TAREAS_TITULOS[i % len(TAREAS_TITULOS)]
                tipo = kan_tipos_reales[i % len(kan_tipos_reales)] if kan_tipos_reales else tipo_default
                prio = kan_prio_reales[i % len(kan_prio_reales)] if kan_prio_reales else prio_default
                dias = random.randint(1, 25)
                fte = kan_ftes[i % len(kan_ftes)]

                psql(
                    f"INSERT INTO kanban_tareas (id, titulo, id_proyecto, tipo, prioridad, columna, id_tecnico, created_at) "
                    f"VALUES ('{task_id}', '{titulo}', '{prj}', '{tipo}', '{prio}', '{col}', '{fte}', "
                    f"NOW() - interval '{dias} days') "
                    f"ON CONFLICT (id) DO UPDATE SET columna = '{col}', id_tecnico = '{fte}';", sc)

            active_n = int(psql(
                f"SELECT COUNT(*) FROM kanban_tareas WHERE columna NOT IN ({','.join(repr(c) for c in COLUMNAS_CERRADAS)});", sc) or '0')
            print(f'  Activas después de crear: {active_n}')

    # Asignar técnicos a todas las activas
    active_ids = psql_lines(
        f"SELECT id FROM kanban_tareas WHERE columna NOT IN ({','.join(repr(c) for c in COLUMNAS_CERRADAS)}) "
        f"ORDER BY id;", sc)
    updates = []
    for i, kid in enumerate(active_ids):
        fte = kan_ftes[i % len(kan_ftes)]
        updates.append(f"UPDATE kanban_tareas SET id_tecnico = '{fte}' WHERE id = '{kid}';")
    for start in range(0, len(updates), 40):
        psql('\n'.join(updates[start:start+40]), schema=sc)
    print(f'  OK: {len(active_ids)} tareas con técnicos')

    # ─── C. incidencias_live ───
    has_col = psql(
        f"SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema = '{sc}' AND table_name = 'incidencias_live' "
        f"AND column_name = 'tecnico_asignado';")
    if has_col.strip():
        live_ids = psql_lines("SELECT ticket_id FROM incidencias_live ORDER BY ticket_id;", sc)
        if live_ids:
            updates = []
            for i, tid in enumerate(live_ids):
                fte = inc_ftes[i % len(inc_ftes)]
                updates.append(f"UPDATE incidencias_live SET tecnico_asignado = '{fte}' WHERE ticket_id = '{tid}';")
            for start in range(0, len(updates), 40):
                psql('\n'.join(updates[start:start+40]), schema=sc)
            print(f'  incidencias_live: {len(live_ids)} con técnicos')

    # ─── RESUMEN ───
    occ = psql(f"""
        SELECT COUNT(DISTINCT tecnico) FROM (
          SELECT tecnico_asignado AS tecnico FROM incidencias_run
            WHERE estado NOT IN ({','.join(repr(e) for e in ESTADOS_CERRADOS)})
            AND tecnico_asignado IS NOT NULL AND tecnico_asignado != ''
          UNION
          SELECT id_tecnico AS tecnico FROM kanban_tareas
            WHERE columna NOT IN ({','.join(repr(c) for c in COLUMNAS_CERRADAS)})
            AND id_tecnico IS NOT NULL AND id_tecnico != ''
        ) sub;
    """, schema=sc)
    print(f'\n  ★ {sc}: {occ}/150 técnicos únicos ocupados')

# ═══════════════════════════════════════════════════════════
# PASO 4: Restart + test
# ═══════════════════════════════════════════════════════════
print('\n' + '=' * 60)
print('RESTART + VERIFICACIÓN API')
print('=' * 60)

r_api = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], capture_output=True, text=True)
api_container = next((n for n in r_api.stdout.strip().split('\n') if 'api' in n.lower()), None)
if api_container:
    os.system(f'docker restart {api_container}')
    time.sleep(8)

for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8088/team/tecnicos'],
            capture_output=True, text=True, timeout=15)
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else []
        estados = {}
        for t in items:
            e = t.get('estado', '?')
            estados[e] = estados.get(e, 0) + 1
        ocu = sum(v for k, v in estados.items() if k not in ('DISPONIBLE', '?', ''))
        pct = 100 * ocu // max(len(items), 1)
        print(f'  {sc}: {ocu}/{len(items)} ocupados ({pct}%) — {dict(sorted(estados.items()))}')
        with_v = [t for t in items if t.get('vinculacion')]
        for t in with_v[:2]:
            print(f'    {t["id_recurso"]}: {t.get("vinculacion","")[:80]}')
    except Exception as e:
        print(f'  {sc}: ERROR — {e}')

print('\n' + '=' * 60)
print('v3 COMPLETO — Recarga: Cmd+Shift+R')
print('=' * 60)

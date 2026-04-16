#!/usr/bin/env python3
"""
P99 FIX OCUPACIÓN REALISTA — Seeds proporcionales por banco
=============================================================
PROBLEMA: Solo ~10-20 técnicos distintos aparecen en incidencias_run
y kanban_tareas → 1% ocupación incluso en banco grande.

SOLUCIÓN: Asignar FTE-xxx reales de compartido.pmo_staff_skills a:
  1) incidencias_run.tecnico_asignado → técnicos en incidencias ABIERTAS
  2) kanban_tareas.id_tecnico → técnicos en tareas ACTIVAS

DISTRIBUCIÓN OBJETIVO:
  sc_norte  (pequeño):  ~40% ocupación → ~60 técnicos ocupados
  sc_iberico (mediano): ~55% ocupación → ~82 técnicos ocupados
  sc_litoral (grande):  ~75% ocupación → ~112 técnicos ocupados

Uso: python3 p99_fix_occupation.py 2>&1 | tee /tmp/p99_fix_occ.log
"""
import subprocess, json, random, os

random.seed(42)  # Reproducible

# Auto-detectar contenedor de BD
def detect_db_container():
    r = subprocess.run(
        ['docker', 'ps', '--format', '{{.Names}}'],
        capture_output=True, text=True, timeout=10
    )
    for name in r.stdout.strip().split('\n'):
        if 'db' in name.lower() or 'postgres' in name.lower():
            return name
    return None

DB_CONTAINER = detect_db_container()

def psql(query, schema=None):
    """Ejecuta query en PostgreSQL"""
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

print('=' * 60)
print('P99 FIX OCUPACIÓN REALISTA')
print(f'DB Container: {DB_CONTAINER or "psql directo"}')
print('=' * 60)

# ═══════════════════════════════════════════════════════════
# PASO 1: Obtener lista completa de FTE-xxx del pool
# ═══════════════════════════════════════════════════════════
print('\n--- 1. Obteniendo pool de técnicos ---')
fte_raw = psql("SELECT id_recurso FROM compartido.pmo_staff_skills ORDER BY id_recurso;")
all_ftes = [x.strip() for x in fte_raw.split('\n') if x.strip().startswith('FTE-')]
print(f'  Pool total: {len(all_ftes)} técnicos')

if len(all_ftes) < 50:
    print('  ERROR: Pool demasiado pequeño, abortando')
    exit(1)

# ═══════════════════════════════════════════════════════════
# PASO 2: Configuración por banco
# ═══════════════════════════════════════════════════════════
BANKS = {
    'sc_norte': {
        'target_pct': 0.40,    # 40% ocupación
        'inc_weight': 0.6,     # 60% de ocupados via incidencias
        'kan_weight': 0.4,     # 40% de ocupados via kanban
        'label': 'Pequeño (30 proyectos)'
    },
    'sc_iberico': {
        'target_pct': 0.55,    # 55% ocupación
        'inc_weight': 0.55,
        'kan_weight': 0.45,
        'label': 'Mediano (50 proyectos)'
    },
    'sc_litoral': {
        'target_pct': 0.75,    # 75% ocupación
        'inc_weight': 0.50,
        'kan_weight': 0.50,
        'label': 'Grande (75 proyectos)'
    }
}

for sc, cfg in BANKS.items():
    print(f'\n{"═" * 60}')
    print(f'  SCHEMA: {sc} — {cfg["label"]}')
    print(f'{"═" * 60}')

    total_ftes = len(all_ftes)
    target_occupied = int(total_ftes * cfg['target_pct'])
    # Shuffle para que cada banco tenga técnicos diferentes ocupados
    shuffled = all_ftes.copy()
    random.shuffle(shuffled)
    occupied_ftes = shuffled[:target_occupied]

    # Dividir entre incidencias y kanban (con overlap natural)
    n_inc = int(target_occupied * cfg['inc_weight'])
    n_kan = int(target_occupied * cfg['kan_weight'])

    # Algunos técnicos estarán en AMBAS (más realista)
    inc_ftes = occupied_ftes[:n_inc]
    kan_ftes = occupied_ftes[n_inc - int(n_inc * 0.15):][:n_kan]  # 15% overlap

    print(f'  Objetivo: {target_occupied}/{total_ftes} ocupados ({cfg["target_pct"]*100:.0f}%)')
    print(f'  Via incidencias: {len(inc_ftes)} técnicos')
    print(f'  Via kanban: {len(kan_ftes)} técnicos')

    # ─── 2a. Obtener incidencias ABIERTAS del schema ───
    print(f'\n  --- Asignando técnicos a incidencias_run ---')
    inc_abiertas_raw = psql(
        "SELECT ticket_id FROM incidencias_run "
        "WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto') "
        "ORDER BY ticket_id;",
        schema=sc
    )
    inc_tickets = [x.strip() for x in inc_abiertas_raw.split('\n') if x.strip()]
    print(f'  Incidencias abiertas: {len(inc_tickets)}')

    if len(inc_tickets) > 0:
        # Asignar técnicos a incidencias abiertas (round-robin)
        updates_inc = []
        for i, ticket in enumerate(inc_tickets):
            fte = inc_ftes[i % len(inc_ftes)]
            updates_inc.append(f"UPDATE incidencias_run SET tecnico_asignado = '{fte}' WHERE ticket_id = '{ticket}';")

        # Ejecutar en batch
        batch_size = 50
        for start in range(0, len(updates_inc), batch_size):
            batch = '\n'.join(updates_inc[start:start+batch_size])
            psql(batch, schema=sc)
        print(f'  OK: {len(updates_inc)} incidencias actualizadas con {len(inc_ftes)} técnicos distintos')
    else:
        print(f'  WARN: No hay incidencias abiertas — creando algunas')
        # Si no hay incidencias abiertas, poner algunas como EN_CURSO
        total_inc = int(psql("SELECT COUNT(*) FROM incidencias_run;", schema=sc) or '0')
        if total_inc > 0:
            # Reabrir ~60% de las cerradas
            reopen_n = max(int(total_inc * 0.6), 10)
            psql(
                f"UPDATE incidencias_run SET estado = 'EN_CURSO' "
                f"WHERE ticket_id IN (SELECT ticket_id FROM incidencias_run ORDER BY ticket_id LIMIT {reopen_n});",
                schema=sc
            )
            print(f'  Reabiertas {reopen_n} incidencias')
            # Re-obtener
            inc_abiertas_raw = psql(
                "SELECT ticket_id FROM incidencias_run "
                "WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto') "
                "ORDER BY ticket_id;",
                schema=sc
            )
            inc_tickets = [x.strip() for x in inc_abiertas_raw.split('\n') if x.strip()]
            updates_inc = []
            for i, ticket in enumerate(inc_tickets):
                fte = inc_ftes[i % len(inc_ftes)]
                updates_inc.append(f"UPDATE incidencias_run SET tecnico_asignado = '{fte}' WHERE ticket_id = '{ticket}';")
            batch_size = 50
            for start in range(0, len(updates_inc), batch_size):
                batch = '\n'.join(updates_inc[start:start+batch_size])
                psql(batch, schema=sc)
            print(f'  OK: {len(updates_inc)} incidencias actualizadas')

    # ─── 2b. Obtener tareas ACTIVAS del kanban ───
    print(f'\n  --- Asignando técnicos a kanban_tareas ---')
    kan_activas_raw = psql(
        "SELECT id FROM kanban_tareas "
        "WHERE columna NOT IN ('Completado','Done','Backlog') "
        "ORDER BY id;",
        schema=sc
    )
    kan_ids = [x.strip() for x in kan_activas_raw.split('\n') if x.strip()]
    print(f'  Tareas activas kanban: {len(kan_ids)}')

    if len(kan_ids) > 0:
        updates_kan = []
        for i, kid in enumerate(kan_ids):
            fte = kan_ftes[i % len(kan_ftes)]
            updates_kan.append(f"UPDATE kanban_tareas SET id_tecnico = '{fte}' WHERE id = '{kid}';")

        batch_size = 50
        for start in range(0, len(updates_kan), batch_size):
            batch = '\n'.join(updates_kan[start:start+batch_size])
            psql(batch, schema=sc)
        print(f'  OK: {len(updates_kan)} tareas actualizadas con {len(kan_ftes)} técnicos distintos')
    else:
        print(f'  WARN: No hay tareas activas en kanban')
        # Verificar si hay tareas en total
        total_kan = int(psql("SELECT COUNT(*) FROM kanban_tareas;", schema=sc) or '0')
        if total_kan > 0:
            # Mover algunas a estados activos
            activate_n = max(int(total_kan * 0.5), 10)
            columnas_activas = ['En Progreso', 'En Revisión', 'Testing', 'Desarrollo']
            for i in range(activate_n):
                col = columnas_activas[i % len(columnas_activas)]
                fte = kan_ftes[i % len(kan_ftes)]
                psql(
                    f"UPDATE kanban_tareas SET columna = '{col}', id_tecnico = '{fte}' "
                    f"WHERE id = (SELECT id FROM kanban_tareas WHERE columna IN ('Completado','Done','Backlog') LIMIT 1);",
                    schema=sc
                )
            print(f'  Activadas ~{activate_n} tareas con técnicos asignados')
        else:
            # Crear tareas kanban para los proyectos activos
            print(f'  Creando tareas kanban para proyectos activos...')
            prj_raw = psql(
                "SELECT id_proyecto FROM cartera_build "
                "WHERE estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado') "
                "LIMIT 30;",
                schema=sc
            )
            proyectos = [x.strip() for x in prj_raw.split('\n') if x.strip()]
            columnas_activas = ['En Progreso', 'En Revisión', 'Testing', 'Desarrollo']
            tareas_titles = [
                'Configuración entorno', 'Desarrollo módulo principal',
                'Integración API', 'Testing unitario', 'Revisión código',
                'Documentación técnica', 'Deploy staging', 'Migración datos',
                'Optimización rendimiento', 'Corrección bugs'
            ]
            inserts = []
            for i, prj in enumerate(proyectos):
                # 2-4 tareas por proyecto
                n_tareas = random.randint(2, 4)
                for j in range(n_tareas):
                    fte = kan_ftes[(i * 4 + j) % len(kan_ftes)]
                    col = columnas_activas[(i + j) % len(columnas_activas)]
                    titulo = tareas_titles[(i + j) % len(tareas_titles)]
                    task_id = f'KAN-{sc[-3:].upper()}-{i*10+j:04d}'
                    inserts.append(
                        f"INSERT INTO kanban_tareas (id, titulo, id_proyecto, id_tecnico, columna, created_at) "
                        f"VALUES ('{task_id}', '{titulo}', '{prj}', '{fte}', '{col}', NOW() - interval '{random.randint(1,30)} days') "
                        f"ON CONFLICT (id) DO UPDATE SET id_tecnico = '{fte}', columna = '{col}';"
                    )
            if inserts:
                batch_size = 50
                for start in range(0, len(inserts), batch_size):
                    batch = '\n'.join(inserts[start:start+batch_size])
                    psql(batch, schema=sc)
                print(f'  OK: {len(inserts)} tareas kanban creadas/actualizadas')

    # ─── 2c. También asegurar que incidencias_live tenga técnicos ───
    print(f'\n  --- Verificando incidencias_live ---')
    live_count = int(psql("SELECT COUNT(*) FROM incidencias_live;", schema=sc) or '0')
    if live_count > 0:
        # Verificar si tiene columna tecnico_asignado
        has_tec = psql(
            "SELECT column_name FROM information_schema.columns "
            f"WHERE table_schema = '{sc}' AND table_name = 'incidencias_live' "
            "AND column_name = 'tecnico_asignado';",
        )
        if has_tec.strip():
            live_ids_raw = psql("SELECT ticket_id FROM incidencias_live ORDER BY ticket_id;", schema=sc)
            live_ids = [x.strip() for x in live_ids_raw.split('\n') if x.strip()]
            updates_live = []
            for i, tid in enumerate(live_ids):
                fte = inc_ftes[i % len(inc_ftes)]
                updates_live.append(f"UPDATE incidencias_live SET tecnico_asignado = '{fte}' WHERE ticket_id = '{tid}';")
            if updates_live:
                batch_size = 50
                for start in range(0, len(updates_live), batch_size):
                    batch = '\n'.join(updates_live[start:start+batch_size])
                    psql(batch, schema=sc)
                print(f'  OK: {len(updates_live)} incidencias_live con técnicos')
        else:
            print(f'  incidencias_live no tiene columna tecnico_asignado (normal)')
    else:
        print(f'  No hay incidencias_live en {sc}')

# ═══════════════════════════════════════════════════════════
# PASO 3: Verificación
# ═══════════════════════════════════════════════════════════
print('\n' + '=' * 60)
print('VERIFICACIÓN POST-FIX')
print('=' * 60)

for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    print(f'\n--- {sc} ---')

    # Contar técnicos únicos ocupados en BD
    occ = psql(f"""
        SELECT COUNT(DISTINCT tecnico) FROM (
          SELECT tecnico_asignado AS tecnico FROM {sc}.incidencias_run
            WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto')
            AND tecnico_asignado IS NOT NULL AND tecnico_asignado != ''
          UNION
          SELECT id_tecnico AS tecnico FROM {sc}.kanban_tareas
            WHERE columna NOT IN ('Completado','Done','Backlog')
            AND id_tecnico IS NOT NULL AND id_tecnico != ''
        ) sub;
    """)
    total = len(all_ftes)
    try:
        occ_n = int(occ.strip())
    except:
        occ_n = 0
    print(f'  BD: {occ_n}/{total} técnicos ocupados ({100*occ_n//max(total,1)}%)')

    # Test endpoint real
    import subprocess as sp
    try:
        r = sp.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8088/team/tecnicos'],
            capture_output=True, text=True, timeout=15
        )
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else data.get('tecnicos', [])
        estados = {}
        for t in items:
            e = t.get('estado', 'SIN')
            estados[e] = estados.get(e, 0) + 1
        ocu_api = sum(v for k, v in estados.items() if k not in ('DISPONIBLE', 'SIN', ''))
        print(f'  API: {ocu_api}/{len(items)} ocupados ({100*ocu_api//max(len(items),1)}%), Estados: {dict(sorted(estados.items()))}')
    except Exception as e:
        print(f'  API ERROR: {e}')

# ═══════════════════════════════════════════════════════════
# PASO 4: Restart para limpiar cache
# ═══════════════════════════════════════════════════════════
print('\n--- Restart API ---')
# Auto-detectar contenedor API
r_api = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], capture_output=True, text=True)
api_container = next((n for n in r_api.stdout.strip().split('\n') if 'api' in n.lower()), None)
if api_container:
    print(f'  Restarting {api_container}...')
    os.system(f'docker restart {api_container}')
else:
    print('  No se encontró contenedor API, restart manual necesario')

import time
time.sleep(5)

# Re-test después del restart
print('\n' + '=' * 60)
print('VERIFICACIÓN POST-RESTART')
print('=' * 60)

for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    print(f'\n--- {sc} ---')
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8088/team/tecnicos'],
            capture_output=True, text=True, timeout=15
        )
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else data.get('tecnicos', [])
        estados = {}
        for t in items:
            e = t.get('estado', 'SIN')
            estados[e] = estados.get(e, 0) + 1
        total = len(items)
        ocu = sum(v for k, v in estados.items() if k not in ('DISPONIBLE', 'SIN', ''))
        pct = 100 * ocu // max(total, 1)
        print(f'  {ocu}/{total} ocupados ({pct}%) — Estados: {dict(sorted(estados.items()))}')
        # Mostrar vinculaciones de muestra
        with_vinc = [t for t in items if t.get('vinculacion')]
        for t in with_vinc[:3]:
            print(f'    {t.get("id_recurso")}: {t.get("estado")} → {t.get("vinculacion","")[:80]}')
    except Exception as e:
        print(f'  ERROR: {e}')

print('\n' + '=' * 60)
print('P99 FIX OCUPACIÓN COMPLETO')
print('Objetivos: sc_norte ~40%, sc_iberico ~55%, sc_litoral ~75%')
print('Recarga navegador (Cmd+Shift+R)')
print('=' * 60)

#!/usr/bin/env python3
"""
P99 FIX OCUPACIÓN v2 — Crear suficientes filas + asignar técnicos
===================================================================
PROBLEMA v1: Solo había 12-33 filas abiertas por schema → máximo 25-61 técnicos.
SOLUCIÓN v2:
  1) Reabrir incidencias cerradas hasta tener suficientes abiertas
  2) Crear/activar tareas kanban hasta tener suficientes activas
  3) Asignar FTE-xxx distintos a cada fila

DISTRIBUCIÓN OBJETIVO:
  sc_norte  (pequeño):  ~40% → ~60 técnicos ocupados
  sc_iberico (mediano): ~55% → ~82 técnicos ocupados
  sc_litoral (grande):  ~75% → ~112 técnicos ocupados

Uso: python3 p99_fix_occupation_v2.py 2>&1 | tee /tmp/p99_fix_occ_v2.log
"""
import subprocess, json, random, os, time

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
    if r.returncode != 0 and r.stderr.strip():
        print(f'    PSQL ERROR: {r.stderr.strip()[:200]}')
    return out

print('=' * 60)
print('P99 FIX OCUPACIÓN v2 — MÁS FILAS + ASIGNACIÓN')
print('=' * 60)

# ═══════════════════════════════════════════════════════════
# PASO 1: Pool de técnicos
# ═══════════════════════════════════════════════════════════
print('\n--- 1. Pool de técnicos ---')
fte_raw = psql("SELECT id_recurso FROM compartido.pmo_staff_skills ORDER BY id_recurso;")
all_ftes = [x.strip() for x in fte_raw.split('\n') if x.strip().startswith('FTE-')]
print(f'  Total: {len(all_ftes)}')
if len(all_ftes) < 50:
    print('  ERROR: Pool < 50, abortando')
    exit(1)

# ═══════════════════════════════════════════════════════════
# PASO 2: Diagnóstico actual
# ═══════════════════════════════════════════════════════════
print('\n--- 2. Diagnóstico actual por schema ---')
for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    total_inc = psql("SELECT COUNT(*) FROM incidencias_run;", sc)
    open_inc = psql("SELECT COUNT(*) FROM incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto');", sc)
    total_kan = psql("SELECT COUNT(*) FROM kanban_tareas;", sc)
    active_kan = psql("SELECT COUNT(*) FROM kanban_tareas WHERE columna NOT IN ('Completado','Done','Backlog');", sc)
    print(f'  {sc}: inc_total={total_inc} inc_abiertas={open_inc} | kan_total={total_kan} kan_activas={active_kan}')

# ═══════════════════════════════════════════════════════════
# PASO 3: Configuración por banco
# ═══════════════════════════════════════════════════════════
BANKS = {
    'sc_norte': {
        'target_occupied': 60,   # 40% de 150
        'inc_target': 35,        # técnicos via incidencias
        'kan_target': 35,        # técnicos via kanban (con ~10 overlap = 60 únicos)
        'label': 'Pequeño'
    },
    'sc_iberico': {
        'target_occupied': 82,   # 55% de 150
        'inc_target': 48,        # técnicos via incidencias
        'kan_target': 48,        # (con ~14 overlap = 82 únicos)
        'label': 'Mediano'
    },
    'sc_litoral': {
        'target_occupied': 112,  # 75% de 150
        'inc_target': 65,        # técnicos via incidencias
        'kan_target': 65,        # (con ~18 overlap = 112 únicos)
        'label': 'Grande'
    }
}

# Estados realistas para incidencias reabiertas
ESTADOS_ABIERTOS = ['EN_CURSO', 'ASIGNADO', 'EN_INVESTIGACION', 'PENDIENTE_PROVEEDOR']
PRIORIDADES = ['P1', 'P2', 'P3', 'P4']
PRIORIDAD_WEIGHTS = [0.10, 0.25, 0.40, 0.25]  # P3 más común

# Columnas activas kanban
COLUMNAS_ACTIVAS = ['En Progreso', 'En Revisión', 'Testing', 'Desarrollo']
TAREAS_TITULOS = [
    'Configuración entorno', 'Desarrollo módulo core', 'Integración API REST',
    'Testing unitario', 'Revisión código PR', 'Documentación técnica',
    'Deploy staging', 'Migración datos', 'Optimización queries',
    'Corrección bugs sprint', 'Refactoring módulo auth', 'Setup CI/CD pipeline',
    'Diseño schema BD', 'Implementar cache Redis', 'Monitorización Grafana',
    'Automatización tests E2E', 'Hardening seguridad', 'Performance tuning',
    'Integración SSO', 'API gateway config'
]

for sc, cfg in BANKS.items():
    print(f'\n{"═" * 60}')
    print(f'  {sc} — {cfg["label"]} — Objetivo: {cfg["target_occupied"]}/150 ocupados')
    print(f'{"═" * 60}')

    shuffled = all_ftes.copy()
    random.shuffle(shuffled)

    # ─── 3a. INCIDENCIAS: asegurar suficientes abiertas ───
    inc_target = cfg['inc_target']
    print(f'\n  --- 3a. Incidencias (target: {inc_target} con técnico) ---')

    # Contar abiertas actuales
    open_count = int(psql(
        "SELECT COUNT(*) FROM incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto');", sc) or '0')
    print(f'  Abiertas actuales: {open_count}')

    if open_count < inc_target:
        # Reabrir cerradas
        need_reopen = inc_target - open_count
        print(f'  Reabriendo {need_reopen} incidencias cerradas...')

        # Obtener IDs de cerradas
        cerradas_raw = psql(
            f"SELECT ticket_id FROM incidencias_run "
            f"WHERE estado IN ('CERRADO','RESUELTO','Cerrado','Resuelto') "
            f"ORDER BY ticket_id LIMIT {need_reopen};", sc)
        cerradas = [x.strip() for x in cerradas_raw.split('\n') if x.strip()]
        print(f'  Cerradas disponibles para reabrir: {len(cerradas)}')

        # Si no hay suficientes cerradas, crear nuevas
        if len(cerradas) < need_reopen:
            falta = need_reopen - len(cerradas)
            print(f'  Creando {falta} incidencias nuevas...')
            prefix = sc[-3:].upper()  # NOR, IBE, LIT

            # Obtener max ticket_id numérico
            max_id_raw = psql(
                "SELECT ticket_id FROM incidencias_run ORDER BY ticket_id DESC LIMIT 1;", sc)
            try:
                max_num = int(''.join(filter(str.isdigit, max_id_raw or '0')))
            except:
                max_num = 500

            servicios = ['Red', 'Servidor', 'Base de Datos', 'Aplicación Web',
                        'VPN', 'Firewall', 'Storage', 'Backup', 'Email', 'DNS',
                        'Active Directory', 'Virtualización', 'Cloud AWS', 'Monitoring']
            descripciones = [
                'Latencia elevada en', 'Error intermitente en', 'Caída parcial de',
                'Timeout en conexiones a', 'Degradación rendimiento en',
                'Alerta crítica en', 'Fallo autenticación en', 'Pérdida paquetes en',
                'CPU al límite en', 'Disco lleno en', 'Certificado expirado en',
                'Memory leak en', 'Conexiones rechazadas en'
            ]

            inserts = []
            for i in range(falta):
                tid = f'INC-{prefix}-{max_num + i + 1:04d}'
                estado = random.choices(ESTADOS_ABIERTOS, weights=[0.4, 0.3, 0.2, 0.1])[0]
                prio = random.choices(PRIORIDADES, weights=PRIORIDAD_WEIGHTS)[0]
                sla_map = {'P1': 4, 'P2': 8, 'P3': 24, 'P4': 48}
                sla = sla_map[prio]
                servicio = random.choice(servicios)
                desc = f"{random.choice(descripciones)} {servicio}"
                dias = random.randint(0, 13)
                horas = random.randint(0, 23)

                inserts.append(
                    f"INSERT INTO incidencias_run (ticket_id, incidencia_detectada, estado, prioridad, "
                    f"sla_limite, servicio_afectado, timestamp_creacion) VALUES "
                    f"('{tid}', '{desc}', '{estado}', '{prio}', {sla}, '{servicio}', "
                    f"NOW() - interval '{dias} days {horas} hours') "
                    f"ON CONFLICT (ticket_id) DO NOTHING;"
                )
            # Ejecutar en batches
            for start in range(0, len(inserts), 30):
                batch = '\n'.join(inserts[start:start+30])
                psql(batch, schema=sc)
            print(f'  OK: {len(inserts)} incidencias nuevas creadas')

        # Reabrir las cerradas
        if cerradas:
            for i, tid in enumerate(cerradas):
                estado = random.choices(ESTADOS_ABIERTOS, weights=[0.4, 0.3, 0.2, 0.1])[0]
                psql(f"UPDATE incidencias_run SET estado = '{estado}' WHERE ticket_id = '{tid}';", sc)
            print(f'  OK: {len(cerradas)} incidencias reabiertas')

    # Ahora asignar técnicos a TODAS las abiertas
    open_raw = psql(
        "SELECT ticket_id FROM incidencias_run "
        "WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto') "
        "ORDER BY ticket_id;", sc)
    open_tickets = [x.strip() for x in open_raw.split('\n') if x.strip()]
    print(f'  Incidencias abiertas totales: {len(open_tickets)}')

    # Asignar FTE-xxx (primeros N del shuffle para incidencias)
    inc_ftes = shuffled[:inc_target]
    updates = []
    for i, tid in enumerate(open_tickets):
        fte = inc_ftes[i % len(inc_ftes)]
        updates.append(f"UPDATE incidencias_run SET tecnico_asignado = '{fte}' WHERE ticket_id = '{tid}';")
    for start in range(0, len(updates), 40):
        batch = '\n'.join(updates[start:start+40])
        psql(batch, schema=sc)
    print(f'  OK: {len(updates)} incidencias con {len(inc_ftes)} técnicos distintos')

    # ─── 3b. KANBAN: asegurar suficientes activas ───
    kan_target = cfg['kan_target']
    print(f'\n  --- 3b. Kanban (target: {kan_target} con técnico) ---')

    active_count = int(psql(
        "SELECT COUNT(*) FROM kanban_tareas WHERE columna NOT IN ('Completado','Done','Backlog');", sc) or '0')
    print(f'  Activas actuales: {active_count}')

    if active_count < kan_target:
        need_more = kan_target - active_count

        # Primero mover completadas a activas
        completadas_raw = psql(
            f"SELECT id FROM kanban_tareas WHERE columna IN ('Completado','Done','Backlog') "
            f"LIMIT {need_more};", sc)
        completadas = [x.strip() for x in completadas_raw.split('\n') if x.strip()]
        print(f'  Completadas disponibles para activar: {len(completadas)}')

        for i, kid in enumerate(completadas):
            col = COLUMNAS_ACTIVAS[i % len(COLUMNAS_ACTIVAS)]
            psql(f"UPDATE kanban_tareas SET columna = '{col}' WHERE id = '{kid}';", sc)

        still_need = need_more - len(completadas)
        if still_need > 0:
            print(f'  Creando {still_need} tareas kanban nuevas...')
            # Obtener proyectos activos
            prj_raw = psql(
                "SELECT id_proyecto FROM cartera_build "
                "WHERE estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado') "
                "ORDER BY id_proyecto;", sc)
            proyectos = [x.strip() for x in prj_raw.split('\n') if x.strip()]
            if not proyectos:
                prj_raw = psql("SELECT id_proyecto FROM cartera_build ORDER BY id_proyecto LIMIT 20;", sc)
                proyectos = [x.strip() for x in prj_raw.split('\n') if x.strip()]

            prefix = sc[-3:].upper()
            inserts = []
            for i in range(still_need):
                task_id = f'KAN-{prefix}-{9000+i:04d}'
                prj = proyectos[i % len(proyectos)] if proyectos else f'PRJ-{prefix}-001'
                col = COLUMNAS_ACTIVAS[i % len(COLUMNAS_ACTIVAS)]
                titulo = TAREAS_TITULOS[i % len(TAREAS_TITULOS)]
                dias = random.randint(0, 20)
                inserts.append(
                    f"INSERT INTO kanban_tareas (id, titulo, id_proyecto, columna, created_at) VALUES "
                    f"('{task_id}', '{titulo}', '{prj}', '{col}', "
                    f"NOW() - interval '{dias} days') "
                    f"ON CONFLICT (id) DO UPDATE SET columna = '{col}';"
                )
            for start in range(0, len(inserts), 30):
                batch = '\n'.join(inserts[start:start+30])
                psql(batch, schema=sc)
            print(f'  OK: {len(inserts)} tareas creadas')

    # Ahora asignar técnicos a TODAS las activas
    active_raw = psql(
        "SELECT id FROM kanban_tareas "
        "WHERE columna NOT IN ('Completado','Done','Backlog') "
        "ORDER BY id;", sc)
    active_ids = [x.strip() for x in active_raw.split('\n') if x.strip()]
    print(f'  Tareas activas totales: {len(active_ids)}')

    # Usar segunda mitad del shuffle (con algo de overlap con incidencias → realista)
    overlap = int(inc_target * 0.15)  # 15% overlap
    kan_ftes = shuffled[inc_target - overlap:inc_target - overlap + kan_target]
    # Si no hay suficientes, extender
    if len(kan_ftes) < kan_target:
        kan_ftes = shuffled[:kan_target]

    updates = []
    for i, kid in enumerate(active_ids):
        fte = kan_ftes[i % len(kan_ftes)]
        updates.append(f"UPDATE kanban_tareas SET id_tecnico = '{fte}' WHERE id = '{kid}';")
    for start in range(0, len(updates), 40):
        batch = '\n'.join(updates[start:start+40])
        psql(batch, schema=sc)
    print(f'  OK: {len(updates)} tareas con {len(kan_ftes)} técnicos distintos')

    # ─── 3c. incidencias_live: también asignar ───
    print(f'\n  --- 3c. incidencias_live ---')
    has_col = psql(
        f"SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema = '{sc}' AND table_name = 'incidencias_live' "
        f"AND column_name = 'tecnico_asignado';")
    if has_col.strip():
        live_raw = psql("SELECT ticket_id FROM incidencias_live ORDER BY ticket_id;", sc)
        live_ids = [x.strip() for x in live_raw.split('\n') if x.strip()]
        if live_ids:
            updates = []
            for i, tid in enumerate(live_ids):
                fte = inc_ftes[i % len(inc_ftes)]
                updates.append(f"UPDATE incidencias_live SET tecnico_asignado = '{fte}' WHERE ticket_id = '{tid}';")
            for start in range(0, len(updates), 40):
                batch = '\n'.join(updates[start:start+40])
                psql(batch, schema=sc)
            print(f'  OK: {len(live_ids)} live con técnicos')
        else:
            print('  Sin datos en incidencias_live')
    else:
        print('  No tiene columna tecnico_asignado')

    # ─── 3d. RESUMEN schema ───
    union_count = psql(f"""
        SELECT COUNT(DISTINCT tecnico) FROM (
          SELECT tecnico_asignado AS tecnico FROM incidencias_run
            WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto')
            AND tecnico_asignado IS NOT NULL AND tecnico_asignado != ''
          UNION
          SELECT id_tecnico AS tecnico FROM kanban_tareas
            WHERE columna NOT IN ('Completado','Done','Backlog')
            AND id_tecnico IS NOT NULL AND id_tecnico != ''
        ) sub;
    """, schema=sc)
    print(f'\n  ★ RESULTADO {sc}: {union_count}/150 técnicos únicos ocupados')

# ═══════════════════════════════════════════════════════════
# PASO 4: Restart + verificación
# ═══════════════════════════════════════════════════════════
print('\n' + '=' * 60)
print('RESTART API + VERIFICACIÓN')
print('=' * 60)

r_api = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], capture_output=True, text=True)
api_container = next((n for n in r_api.stdout.strip().split('\n') if 'api' in n.lower()), None)
if api_container:
    print(f'Restarting {api_container}...')
    os.system(f'docker restart {api_container}')
    time.sleep(8)
else:
    print('No se encontró contenedor API')

for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8088/team/tecnicos'],
            capture_output=True, text=True, timeout=15
        )
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else data.get('tecnicos', [])
        estados = {}
        for t in items:
            e = t.get('estado', '?')
            estados[e] = estados.get(e, 0) + 1
        total = len(items)
        ocu = sum(v for k, v in estados.items() if k not in ('DISPONIBLE', '?', ''))
        pct = 100 * ocu // max(total, 1)
        print(f'  {sc}: {ocu}/{total} ocupados ({pct}%) — {dict(sorted(estados.items()))}')
        # Muestra vinculaciones
        with_v = [t for t in items if t.get('vinculacion')]
        for t in with_v[:2]:
            print(f'    {t.get("id_recurso")}: {t.get("vinculacion","")[:80]}')
    except Exception as e:
        print(f'  {sc}: ERROR — {e}')

print('\n' + '=' * 60)
print('P99 FIX OCUPACIÓN v2 COMPLETO')
print('Objetivos: sc_norte ~40%, sc_iberico ~55%, sc_litoral ~75%')
print('Recarga navegador: Cmd+Shift+R')
print('=' * 60)

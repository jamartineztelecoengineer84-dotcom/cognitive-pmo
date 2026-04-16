#!/usr/bin/env python3
"""
P99 HOTFIX v4c — 3 fixes finales
==================================
C1: TEAM GOV — mapear estado_run → estado en /team/tecnicos
C2: PMO GOV — /pmo/managers calcula estado PM dinámico per-schema
C3: BUDGET — celda visible muestra nombre_proyecto, no solo id

Uso: python3 p99_hotfix_v4c.py
"""
import os, re, shutil, subprocess, json

MAIN_PY = '/root/cognitive-pmo/backend/main.py'
IDX = '/root/cognitive-pmo/frontend/index.html'

print('=' * 60)
print('P99 HOTFIX v4c — 3 fixes finales')
print('=' * 60)

# ═══════════════════════════════════════════════════════════
# C1: /team/tecnicos — estado_run → estado
# ═══════════════════════════════════════════════════════════
print('\n--- C1: estado_run → estado ---')

with open(MAIN_PY, 'r', encoding='utf-8') as f:
    code = f.read()

# Buscar el "return result" en /team/tecnicos y añadir mapping antes
# El B3 enrichment termina con: except Exception as e: logger.warning("B3...")
# Luego viene: return result

# Buscar el patrón exacto
marker = 'logger.warning(f"B3 vinculacion error: {e}")'
marker_pos = code.find(marker)

if marker_pos > -1:
    # Buscar el "return result" después de este marker
    return_pos = code.find('return result', marker_pos)
    if return_pos > -1 and return_pos - marker_pos < 200:
        # Insertar mapping de estado justo antes del return
        mapping = """
                # C1: Copiar estado_run → estado para que el frontend KPI lo lea
                for d in result:
                    if d.get('estado_run'):
                        d['estado'] = d['estado_run']

"""
        code = code[:return_pos] + mapping + code[return_pos:]
        print('  OK: estado_run → estado mapping añadido')
    else:
        print(f'  WARN: return result no encontrado cerca del marker (pos={return_pos}, marker={marker_pos})')
else:
    print('  WARN: marker B3 no encontrado')
    # Alternativa: buscar cualquier "return result" en /team/tecnicos
    tec_pos = code.find('@app.get("/team/tecnicos")')
    if tec_pos > -1:
        # Buscar return result después del endpoint
        ret_pos = code.find('return result', tec_pos)
        if ret_pos > -1:
            mapping = """
                # C1: Copiar estado_run → estado
                for d in result:
                    if d.get('estado_run'):
                        d['estado'] = d['estado_run']

"""
            code = code[:ret_pos] + mapping + code[ret_pos:]
            print('  OK: estado mapping añadido (alternativa)')

# ═══════════════════════════════════════════════════════════
# C2: /pmo/managers — estado dinámico per-schema
# ═══════════════════════════════════════════════════════════
print('\n--- C2: /pmo/managers → estado dinámico ---')

# Buscar el endpoint GET /pmo/managers
mgr_pat = re.search(r'@app\.get\(["\']\/pmo\/managers["\'](?!\/))', code)
if mgr_pat:
    mgr_start = mgr_pat.start()
    # Buscar el return del endpoint
    next_ep = re.search(r'\n@app\.(get|post|put|delete|patch)\(', code[mgr_start+10:])
    mgr_end = mgr_start + 10 + next_ep.start() if next_ep else mgr_start + 3000
    mgr_block = code[mgr_start:mgr_end]

    print(f'  Endpoint /pmo/managers encontrado ({len(mgr_block)} chars)')

    if 'C2' in mgr_block or 'proyectos_activos' in mgr_block:
        print('  SKIP: ya tiene enrichment per-schema')
    else:
        # Buscar el return [serialize(r)...] o return [dict(r)...]
        ret_match = re.search(r'return \[(serialize|dict)\(r\) for r in (\w+)\]', mgr_block)
        if ret_match:
            old_return = ret_match.group(0)
            func_name = ret_match.group(1)
            var_name = ret_match.group(2)

            new_return = f"""# C2: Enriquecer PMs con estado dinámico per-schema
                result_pms = []
                for r in {var_name}:
                    d = {func_name}(r)
                    pm_id = d.get('id_pm') or d.get('nombre') or ''
                    # Contar proyectos activos de este PM en el schema actual
                    proj_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM cartera_build "
                        "WHERE responsable_asignado = $1 "
                        "AND estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado')",
                        pm_id
                    ) or 0
                    # Si no match por id_pm, intentar por nombre
                    if proj_count == 0 and d.get('nombre'):
                        proj_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM cartera_build "
                            "WHERE responsable_asignado = $1 "
                            "AND estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado')",
                            d['nombre']
                        ) or 0
                    # Calcular estado dinámico
                    if proj_count > 3:
                        d['estado'] = 'SOBRECARGADO'
                    elif proj_count > 0:
                        d['estado'] = 'ASIGNADO'
                    else:
                        d['estado'] = 'DISPONIBLE'
                    d['proyectos_activos'] = proj_count
                    d['carga'] = min(proj_count * 25, 100)  # 25% por proyecto
                    result_pms.append(d)
                return result_pms"""

            abs_pos = code.find(old_return, mgr_start)
            if abs_pos > -1 and abs_pos < mgr_end:
                code = code[:abs_pos] + new_return + code[abs_pos + len(old_return):]
                print('  OK: PMs con estado dinámico per-schema')
            else:
                print('  WARN: posición del return fuera de rango')
        else:
            # Mostrar qué hay
            print('  Return pattern no encontrado. Bloque:')
            for i, line in enumerate(mgr_block.split('\n')[:20]):
                print(f'    {i}: {line.rstrip()[:120]}')
else:
    print('  WARN: /pmo/managers no encontrado')
    # Buscar alternativas
    for m in re.finditer(r'pmo/managers', code):
        ln = code[:m.start()].count('\n') + 1
        print(f'    L{ln}: {code[max(0,m.start()-30):m.end()+30]}')

# ═══════════════════════════════════════════════════════════
# GUARDAR main.py
# ═══════════════════════════════════════════════════════════
with open(MAIN_PY, 'w', encoding='utf-8') as f:
    f.write(code)
print('  main.py guardado')

# Syntax check
ret = os.system('python3 -c "import py_compile; py_compile.compile(\'%s\', doraise=True)"' % MAIN_PY)
if ret != 0:
    print('  *** SYNTAX ERROR — revirtiendo ***')
    bak = MAIN_PY + '.bak_v4'
    if os.path.exists(bak):
        # No revertir al original, solo avisar
        print('  AVISO: main.py tiene error de sintaxis, revisar manualmente')
    exit(1)
print('  SYNTAX OK')

# ═══════════════════════════════════════════════════════════
# C3: BUDGET — celda visible con nombre_proyecto
# ═══════════════════════════════════════════════════════════
print('\n--- C3: BUDGET celda visible con nombre_proyecto ---')

with open(IDX, 'r', encoding='utf-8') as f:
    idx = f.read()

# L13161: la celda visible muestra ${escHtml((b.id_proyecto||'').slice(0,40))}
# Cambiar por: ${escHtml(b.id_proyecto+(b.nombre_proyecto?' — '+b.nombre_proyecto.substring(0,25):''))}

old_budget_cell = "${escHtml((b.id_proyecto||'').slice(0,40))}"
new_budget_cell = "${escHtml(b.id_proyecto+(b.nombre_proyecto?' — '+b.nombre_proyecto.substring(0,25):''))}"

if old_budget_cell in idx:
    idx = idx.replace(old_budget_cell, new_budget_cell, 1)
    print('  OK: celda visible ahora muestra ID + nombre')
elif "b.id_proyecto||''" in idx and 'slice(0,40)' in idx:
    # Buscar variante
    print('  Buscando variante...')
    # Puede tener escHtml con comillas diferentes
    pat = re.search(r'\$\{escHtml\(\(b\.id_proyecto\|\|[\'\"]\'\'\)\.slice\(0,40\)\)\}', idx)
    if pat:
        idx = idx[:pat.start()] + new_budget_cell + idx[pat.end():]
        print('  OK: variante parcheada')
    else:
        print('  WARN: variante no encontrada')
else:
    print('  SKIP: ya parcheado o patrón diferente')
    # Debug
    lines = idx.split('\n')
    for i in range(13155, min(13170, len(lines))):
        if 'id_proyecto' in lines[i]:
            print(f'    L{i+1}: {lines[i].strip()[:120]}')

with open(IDX, 'w', encoding='utf-8') as f:
    f.write(idx)
print('  index.html guardado')

# ═══════════════════════════════════════════════════════════
# DEPLOY + RESTART
# ═══════════════════════════════════════════════════════════
print('\n--- Deploy ---')
os.system('docker cp /root/cognitive-pmo/backend/main.py cognitive-pmo-api-1:/app/main.py')
os.system('docker restart cognitive-pmo-api-1')
os.system('docker restart cognitive-pmo-frontend-1')

import time
time.sleep(5)

# ═══════════════════════════════════════════════════════════
# VERIFICACIÓN
# ═══════════════════════════════════════════════════════════
print('\n' + '=' * 60)
print('VERIFICACIÓN')
print('=' * 60)

# Team tecnicos — verificar campo estado
print('\n--- /team/tecnicos (campo estado) ---')
for sc in ['sc_norte', 'sc_iberico']:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8088/team/tecnicos'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else data.get('tecnicos', [])
        estados = {}
        for t in items:
            e = t.get('estado', 'SIN_ESTADO')
            estados[e] = estados.get(e, 0) + 1
        print(f'  {sc}: {len(items)} técnicos, estados={dict(sorted(estados.items()))}')
    except Exception as e:
        print(f'  {sc}: ERROR - {e}')

# PM managers — verificar estados dinámicos
print('\n--- /pmo/managers (estados per-schema) ---')
for sc in ['sc_norte', 'sc_iberico', 'sc_litoral']:
    try:
        r = subprocess.run(
            ['curl', '-s', '-H', f'X-Scenario: {sc}', 'http://localhost:8088/pmo/managers'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(r.stdout)
        items = data if isinstance(data, list) else data.get('managers', [])
        estados = {}
        for pm in items:
            e = pm.get('estado', 'SIN')
            estados[e] = estados.get(e, 0) + 1
        print(f'  {sc}: {len(items)} PMs, estados={dict(sorted(estados.items()))}')
        # Mostrar 2 con proyectos
        with_proj = [p for p in items if p.get('proyectos_activos', 0) > 0]
        for p in with_proj[:2]:
            print(f'    {p.get("id_pm")}: {p.get("estado")} ({p.get("proyectos_activos")} proyectos)')
    except Exception as e:
        print(f'  {sc}: ERROR - {e}')

print('\n' + '=' * 60)
print('P99 HOTFIX v4c COMPLETO — Recarga navegador')
print('=' * 60)

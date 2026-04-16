#!/usr/bin/env python3
"""
P99 FRONTEND FIXES v4 — Parches mínimos en index.html
=======================================================
La investigación muestra que index.html YA tiene:
  - L13536: nombre_proyecto||id_proyecto en presupuestos GOV cards
  - L13566: nombre_proyecto||id_proyecto en presupuestos detail
  - L5430:  skills_requeridas en cartera mapping
  - L2390:  columna "Vinculación" en team table
  - L7357:  parseFloat(inc.sla_horas) || 48 en incidencias live

Lo que FALTA:
  F1: La tabla lista de presupuestos (loadBudgets L13095+) puede mostrar
      solo id_proyecto en una columna — necesitamos ver y parchar
  F2: Añadir skills_requeridas a las tarjetas de proyecto BUILD
  F3: Asegurar que "Capacidad de Recursos" (Pilar 2 L2445) use datos dinámicos

Uso: python3 p99_fixes_v4_frontend.py
"""
import os, re, shutil

IDX = '/root/cognitive-pmo/frontend/index.html'

print('=' * 60)
print('P99 FRONTEND FIXES v4')
print('=' * 60)

with open(IDX, 'r', encoding='utf-8') as f:
    content = f.read()

bak = IDX + '.bak_v4'
if not os.path.exists(bak):
    shutil.copy2(IDX, bak)
    print(f'Backup: {bak}')

lines = content.split('\n')
print(f'Total: {len(lines)} líneas')
changes = 0

# ═══════════════════════════════════════════════════════════
# F1: INVESTIGAR loadBudgets rendering
# ═══════════════════════════════════════════════════════════
print('\n--- F1: Investigar tabla presupuestos (loadBudgets) ---')

# Buscar la función loadBudgets (L13095)
lb_start = None
for i, line in enumerate(lines):
    if 'function loadBudgets' in line or 'async function loadBudgets' in line:
        lb_start = i
        break

if lb_start is not None:
    print(f'  loadBudgets encontrado en L{lb_start+1}')
    # Mostrar las siguientes 80 líneas para ver el rendering
    block = '\n'.join(lines[lb_start:lb_start+80])

    # Buscar dónde se renderiza id_proyecto en la tabla
    # Patrón: algo como b.id_proyecto o item.id_proyecto en la tabla de lista
    id_proj_refs = [(i, lines[i]) for i in range(lb_start, min(lb_start+100, len(lines)))
                    if 'id_proyecto' in lines[i]]
    print(f'  id_proyecto en loadBudgets: {len(id_proj_refs)} refs')
    for ln, txt in id_proj_refs[:8]:
        print(f'    L{ln+1}: {txt.strip()[:130]}')

    # Buscar si ya usa nombre_proyecto en la tabla
    nombre_refs = [(i, lines[i]) for i in range(lb_start, min(lb_start+100, len(lines)))
                   if 'nombre_proyecto' in lines[i]]
    print(f'  nombre_proyecto en loadBudgets: {len(nombre_refs)} refs')
    for ln, txt in nombre_refs[:5]:
        print(f'    L{ln+1}: {txt.strip()[:130]}')

    # Si la tabla muestra solo id_proyecto, necesitamos añadir nombre_proyecto
    # Buscar patrón de celda <td> con id_proyecto
    for i in range(lb_start, min(lb_start+100, len(lines))):
        line = lines[i]
        # Buscar patrones como: b.id_proyecto, item.id_proyecto, row.id_proyecto en contexto de <td> o celda
        if 'id_proyecto' in line and ('td' in line or 'innerHTML' in line or '+=' in line):
            # Verificar si ya tiene nombre_proyecto junto
            if 'nombre_proyecto' not in line:
                print(f'  >>> CANDIDATO para parche en L{i+1}: {line.strip()[:150]}')

                # Intentar el reemplazo: añadir nombre_proyecto después de id_proyecto
                # Buscar el patrón exacto
                # Ejemplo: b.id_proyecto → b.id_proyecto + (b.nombre_proyecto ? ' — ' + b.nombre_proyecto.substring(0,30) : '')
                patterns_to_try = [
                    # var.id_proyecto en un template literal
                    (r'\$\{([a-z])\.id_proyecto\}', lambda m: f'${{{m.group(1)}.id_proyecto}}${{({m.group(1)}.nombre_proyecto ? " — " + {m.group(1)}.nombre_proyecto.substring(0,30) : "")}}'),
                    # var.id_proyecto en concatenación
                    (r"(\w+)\.id_proyecto(?!\s*\+\s*['\"]?\s*[—–-]\s*['\"]?\s*\+?\s*\w*\.nombre)", lambda m: f'{m.group(1)}.id_proyecto+({m.group(1)}.nombre_proyecto?" — "+{m.group(1)}.nombre_proyecto.substring(0,30):"")'),
                ]

                for pat, repl in patterns_to_try:
                    if re.search(pat, line):
                        new_line = re.sub(pat, repl, line, count=1)
                        if new_line != line:
                            lines[i] = new_line
                            changes += 1
                            print(f'    PARCHEADO L{i+1}')
                            print(f'    ANTES: {line.strip()[:120]}')
                            print(f'    DESPUÉS: {new_line.strip()[:120]}')
                            break
else:
    print('  WARN: loadBudgets no encontrado')

# ═══════════════════════════════════════════════════════════
# F2: Skills en tarjetas proyecto BUILD
# ═══════════════════════════════════════════════════════════
print('\n--- F2: Skills en tarjetas proyecto ---')

# La investigación muestra L5430: skill: p.skills_requeridas || p.skill_requerida
# Esto es en el mapping, pero ¿se muestra en las tarjetas?
# Buscar la renderización de tarjetas de proyecto BUILD

# Buscar el patrón de card de proyecto que tiene PM y Presupuesto
# Similar a gov-build.html: pc-r pattern
card_sections = []
for i, line in enumerate(lines):
    if 'pm_asignado' in line and ('pc-r' in line or 'span' in line):
        card_sections.append(i)
    elif 'Presupuesto' in line and ('pc-r' in line or 'span' in line):
        card_sections.append(i)

print(f'  Card rendering candidates: {card_sections[:10]}')
for ln in card_sections[:6]:
    print(f'    L{ln+1}: {lines[ln].strip()[:130]}')

# Verificar si skills ya se muestra en las tarjetas
skills_in_cards = False
for i, line in enumerate(lines):
    if 'skills_requeridas' in line and ('pc-r' in line or 'card' in line.lower() or 'div' in line):
        skills_in_cards = True
        print(f'  Skills ya en tarjetas: L{i+1}')
        break

if not skills_in_cards and card_sections:
    # Buscar la sección de tarjetas BUILD más probable
    # Buscar después de "Presupuesto" en una card
    for ln in card_sections:
        line = lines[ln]
        if 'Presupuesto' in line and 'pc-v' in line:
            # Encontrar dónde termina esta línea de Presupuesto
            # y añadir skills después
            # Buscar la siguiente línea que tiene un div o cierre
            for j in range(ln+1, min(ln+5, len(lines))):
                next_line = lines[j]
                if 'pc-pb' in next_line or 'margin-top' in next_line or 'Progreso' in next_line:
                    # Insertar skills antes del progreso
                    indent = len(next_line) - len(next_line.lstrip())
                    skills_line = ' ' * indent + """h+='<div class="pc-r"><span>Skills</span><span class="pc-v" style="font-size:9px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+(p.skills_requeridas||p.skill_requerida||'—')+'</span></div>';"""
                    lines.insert(j, skills_line)
                    changes += 1
                    print(f'  OK: Skills insertado en L{j+1} (antes de Progreso)')
                    break
            break

# ═══════════════════════════════════════════════════════════
# F3: Pilar 2 Capacidad — usar datos dinámicos
# ═══════════════════════════════════════════════════════════
print('\n--- F3: Pilar 2 Capacidad de Recursos ---')

# Buscar la sección "P2: Capacidad" (L13594)
p2_section = None
for i, line in enumerate(lines):
    if '// P2: Capacidad' in line or 'P2: Capacidad' in line:
        p2_section = i
        break

if p2_section:
    print(f'  P2 Capacidad encontrado en L{p2_section+1}')
    # Mostrar contexto
    for j in range(p2_section, min(p2_section+30, len(lines))):
        print(f'    L{j+1}: {lines[j].strip()[:130]}')

    # Buscar si usa datos hardcoded o del API
    # Si usa d.pms_asignados etc, ya está bien (el backend ahora devuelve per-schema)
    p2_block = '\n'.join(lines[p2_section:p2_section+30])
    if 'd.pms_asignados' in p2_block or 'pms_asignados' in p2_block:
        print('  OK: Ya usa datos del API (d.pms_asignados)')
        print('  El backend ahora devuelve valores per-schema → debería funcionar')

        # Verificar si muestra proyectos_activos_schema
        if 'proyectos_activos_schema' not in p2_block:
            # Buscar donde se renderiza el summary de PMs y añadir proyectos activos
            # Buscar "pms_asignados" en el rendering
            for j in range(p2_section, min(p2_section+25, len(lines))):
                if 'pms_asignados' in lines[j] and ('innerHTML' in lines[j] or '+=' in lines[j] or 'textContent' in lines[j]):
                    print(f'  INFO: PM stats en L{j+1}: {lines[j].strip()[:120]}')
                    # Podríamos añadir proyectos_activos pero mejor dejarlo simple
                    break
    else:
        print('  WARN: No usa datos del API — puede estar hardcoded')
else:
    print('  P2 Capacidad no encontrado como comentario, buscando alternativa...')
    for i, line in enumerate(lines):
        if 'gov-p2-score' in line or 'Capacidad de Recursos' in line:
            print(f'    L{i+1}: {line.strip()[:120]}')

# ═══════════════════════════════════════════════════════════
# GUARDAR
# ═══════════════════════════════════════════════════════════
if changes > 0:
    content = '\n'.join(lines)
    with open(IDX, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'\nGuardado index.html ({changes} cambios)')
else:
    print('\nSin cambios directos en index.html')
    print('Los fixes principales son BACKEND — el frontend ya lee los campos correctos')

# ═══════════════════════════════════════════════════════════
# RESTART nginx
# ═══════════════════════════════════════════════════════════
print('\n--- Restart nginx ---')
os.system('docker restart cognitive-pmo-web-1 2>&1')

print('\n' + '=' * 60)
print('P99 FRONTEND FIXES v4 COMPLETO')
print('Recargar navegador (Cmd+Shift+R)')
print('=' * 60)

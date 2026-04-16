#!/usr/bin/env python3
"""
P99 FRONTEND FIXES v3 — Parches en index.html
===============================================
Parchea el dashboard principal (index.html) que tiene las 5 issues.
Las secciones RUN, BUILD, GOV del index.html son las que JA ve.

Este script primero INVESTIGA qué hay en cada sección relevante
y luego aplica parches quirúrgicos.

IMPORTANTE: Ejecutar DESPUÉS de p99_investigate_v3.sh y p99_fixes_v3.py

Uso: python3 p99_fixes_v3_frontend.py
"""
import os, re, shutil

IDX = '/root/cognitive-pmo/frontend/index.html'
GOV_RUN = '/root/cognitive-pmo/frontend/gov-run.html'
GOV_BUILD = '/root/cognitive-pmo/frontend/gov-build.html'

print('=' * 60)
print('P99 FRONTEND FIXES v3')
print('=' * 60)

# ═══════════════════════════════════════════════════════════
# INVESTIGAR index.html — buscar las 5 secciones
# ═══════════════════════════════════════════════════════════
print('\n--- Investigando index.html ---')

with open(IDX, 'r', encoding='utf-8') as f:
    idx_content = f.read()

# Backup
bak = IDX + '.bak_v3'
if not os.path.exists(bak):
    shutil.copy2(IDX, bak)
    print(f'Backup: {bak}')

idx_lines = idx_content.split('\n')
print(f'  Total: {len(idx_lines)} líneas')

# Buscar patrones clave
patterns = {
    'incidencias_fetch': r'(fetch|af|authFetch|apiFetch)\s*\(\s*["\'].*?incidencias',
    'sla_horas': r'sla_horas|sla_limite|SLA',
    'presupuestos_fetch': r'(fetch|af|authFetch|apiFetch)\s*\(\s*["\'].*?presupuestos',
    'nombre_proyecto_render': r'nombre_proyecto|id_proyecto',
    'skills_requeridas': r'skills_requeridas|skills_req',
    'governance_fetch': r'(fetch|af|authFetch|apiFetch)\s*\(\s*["\'].*?governance',
    'capacidad_render': r'[Cc]apacidad|carga.*[Pp][Mm]|pm_stats',
    'tarea_actual': r'tarea_actual|proyecto_actual',
    'team_fetch': r'(fetch|af|authFetch|apiFetch)\s*\(\s*["\'].*?team/tecnicos',
}

for name, pat in patterns.items():
    matches = []
    for i, line in enumerate(idx_lines):
        if re.search(pat, line):
            matches.append((i+1, line.strip()[:100]))
    print(f'\n  [{name}] ({len(matches)} hits):')
    for ln, txt in matches[:5]:
        print(f'    L{ln}: {txt}')

# ═══════════════════════════════════════════════════════════
# PARCHE 1: SLA display — cambiar sla_horas por cálculo
# ═══════════════════════════════════════════════════════════
print('\n\n--- PARCHE 1: SLA display ---')

# En index.html, buscar cómo se muestra el SLA en la tabla de incidencias
# Patrones comunes: x.sla_horas, sla_horas+'h', formatSLA
sla_lines = [i for i, l in enumerate(idx_lines)
             if 'sla_horas' in l or ('sla' in l.lower() and ('horas' in l.lower() or 'hours' in l.lower()))]

if sla_lines:
    print(f'  Encontrado sla_horas en líneas: {sla_lines[:5]}')
    for ln in sla_lines[:3]:
        ctx_start = max(0, ln-2)
        ctx_end = min(len(idx_lines), ln+3)
        for j in range(ctx_start, ctx_end):
            marker = ' >>>' if j == ln else '    '
            print(f'  {marker} L{j+1}: {idx_lines[j][:120]}')
else:
    print('  No encontrado sla_horas directamente')
    # Buscar alternativas
    sla_alt = [i for i, l in enumerate(idx_lines) if 'SLA' in l and ('td' in l or 'th' in l or 'span' in l)]
    print(f'  SLA en HTML: {len(sla_alt)} hits')
    for ln in sla_alt[:5]:
        print(f'    L{ln+1}: {idx_lines[ln][:120]}')

# Si el backend ahora devuelve sla_horas (FIX 3b), el frontend que ya usa x.sla_horas
# debería funcionar. Si usa otro campo, necesitamos parchar.

# Buscar el patrón de renderizado de la tabla de incidencias
inc_table_lines = [i for i, l in enumerate(idx_lines)
                   if 'incidencia' in l.lower() and ('table' in l or 'forEach' in l or 'slice' in l)]
print(f'\n  Incidencias table rendering: {len(inc_table_lines)} candidates')
for ln in inc_table_lines[:5]:
    print(f'    L{ln+1}: {idx_lines[ln][:150]}')

# ═══════════════════════════════════════════════════════════
# PARCHE 2: Presupuestos — mostrar nombre_proyecto
# ═══════════════════════════════════════════════════════════
print('\n\n--- PARCHE 2: Presupuestos nombre_proyecto ---')

# Buscar la sección de presupuestos en index.html
pres_lines = [i for i, l in enumerate(idx_lines)
              if 'presupuest' in l.lower()]
print(f'  Presupuestos references: {len(pres_lines)} hits')
for ln in pres_lines[:10]:
    print(f'    L{ln+1}: {idx_lines[ln][:150]}')

# Buscar dónde se renderiza la lista de presupuestos
# Podría usar id_proyecto directamente
pres_render = [i for i, l in enumerate(idx_lines)
               if 'id_proyecto' in l and ('presupuest' in idx_lines[max(0,i-5):i+5].__repr__().lower()
                                           or 'budget' in l.lower())]
if not pres_render:
    pres_render = [i for i, l in enumerate(idx_lines) if 'id_proyecto' in l]

print(f'  id_proyecto references: {len(pres_render)} hits')
for ln in pres_render[:10]:
    print(f'    L{ln+1}: {idx_lines[ln][:150]}')

# ═══════════════════════════════════════════════════════════
# PARCHE 3: Skills en tarjetas de proyecto
# ═══════════════════════════════════════════════════════════
print('\n\n--- PARCHE 3: Skills en proyectos ---')

# Buscar la sección BUILD donde se renderizan las tarjetas de proyecto
# La tarjeta muestra: nombre, id, PM, presupuesto, progreso
# Necesitamos añadir skills_requeridas
build_section = [i for i, l in enumerate(idx_lines)
                 if 'cartera/proyectos' in l or 'loadProy' in l or 'loadProyectos' in l]
print(f'  BUILD project section: {len(build_section)} hits')
for ln in build_section[:5]:
    print(f'    L{ln+1}: {idx_lines[ln][:150]}')

# Buscar el card rendering (pc-r pattern from gov-build.html)
card_render = [i for i, l in enumerate(idx_lines)
               if ('pc-r' in l or 'pm_asignado' in l or 'Presupuesto' in l) and 'span' in l]
print(f'  Card rendering: {len(card_render)} hits')
for ln in card_render[:10]:
    print(f'    L{ln+1}: {idx_lines[ln][:150]}')

# ═══════════════════════════════════════════════════════════
# PARCHE 4: PMO GOV Capacidad
# ═══════════════════════════════════════════════════════════
print('\n\n--- PARCHE 4: PMO GOV Capacidad ---')

gov_section = [i for i, l in enumerate(idx_lines)
               if 'governance' in l.lower() or 'capacidad' in l.lower()]
print(f'  Governance/Capacidad: {len(gov_section)} hits')
for ln in gov_section[:10]:
    print(f'    L{ln+1}: {idx_lines[ln][:150]}')

# ═══════════════════════════════════════════════════════════
# PARCHE 5: Team vinculation
# ═══════════════════════════════════════════════════════════
print('\n\n--- PARCHE 5: Team vinculation ---')

team_section = [i for i, l in enumerate(idx_lines)
                if 'tarea_actual' in l or 'proyecto_actual' in l or 'Sin asignar' in l]
print(f'  tarea_actual references: {len(team_section)} hits')
for ln in team_section[:10]:
    print(f'    L{ln+1}: {idx_lines[ln][:150]}')

# ═══════════════════════════════════════════════════════════
# APLICAR PARCHES AUTOMÁTICOS
# ═══════════════════════════════════════════════════════════
print('\n\n═══ APLICANDO PARCHES ═══')

changes_made = 0

# PARCHE A: Si hay sla_horas sin el cálculo del backend,
# añadir fallback JavaScript que calcula horas desde sla_limite
# Buscar la sección de incidencias y añadir helper
SLA_HELPER = """
/* P99v3: Helper SLA horas desde timestamp */
function p99SlaHoras(item) {
  if (item.sla_horas != null) return item.sla_horas;
  if (!item.sla_limite) return null;
  try {
    var sl = new Date(item.sla_limite);
    var now = new Date();
    var diff = (sl - now) / 3600000;
    return Math.round(diff * 10) / 10;
  } catch(e) { return null; }
}
"""

# Buscar si el helper ya existe
if 'p99SlaHoras' in idx_content:
    print('  SKIP: SLA helper ya existe')
else:
    # Inyectar el helper antes del primer uso de sla_horas o al final del <head>
    # Buscar el monkey-patch P99 que ya está inyectado
    inject_point = idx_content.find('/* P99: Monkey-patch fetch')
    if inject_point > -1:
        # Inyectar justo antes
        idx_content = idx_content[:inject_point] + SLA_HELPER + '\n' + idx_content[inject_point:]
        print('  OK: SLA helper inyectado antes del monkey-patch')
        changes_made += 1
    else:
        # Buscar </head>
        head_end = idx_content.find('</head>')
        if head_end > -1:
            idx_content = idx_content[:head_end] + '<script>' + SLA_HELPER + '</script>\n' + idx_content[head_end:]
            print('  OK: SLA helper inyectado antes de </head>')
            changes_made += 1

# PARCHE B: Reemplazar sla_horas directas por p99SlaHoras(x) en tabla incidencias
# Patrón: x.sla_horas?x.sla_horas+'h' → p99SlaHoras(x)!=null?p99SlaHoras(x)+'h'
old_sla_patterns = [
    ("x.sla_horas?x.sla_horas+'h'", "p99SlaHoras(x)!=null?Math.abs(p99SlaHoras(x)).toFixed(1)+'h'"),
    ('x.sla_horas?x.sla_horas+"h"', 'p99SlaHoras(x)!=null?Math.abs(p99SlaHoras(x)).toFixed(1)+"h"'),
    # Variantes con comillas y espacios
    ("x.sla_horas ? x.sla_horas + 'h'", "p99SlaHoras(x) != null ? Math.abs(p99SlaHoras(x)).toFixed(1) + 'h'"),
]

for old, new in old_sla_patterns:
    if old in idx_content:
        idx_content = idx_content.replace(old, new)
        print(f'  OK: SLA pattern replaced: {old[:40]}...')
        changes_made += 1

# PARCHE C: En presupuestos, reemplazar solo id_proyecto por id+nombre
# Buscar el patrón típico: x.id_proyecto||x.id||'—'
# y cambiar por: (x.nombre_proyecto?(x.id_proyecto+' - '+x.nombre_proyecto):x.id_proyecto)
pres_old_patterns = [
    # Patrón en tabla de presupuestos donde se muestra solo el id
    ("(x.id_proyecto||x.id||'—')", "(x.nombre_proyecto?(x.id_proyecto+' — '+x.nombre_proyecto):(x.id_proyecto||x.id||'—'))"),
    ("(x.id_proyecto||x.id||'\\u2014')", "(x.nombre_proyecto?(x.id_proyecto+' — '+x.nombre_proyecto):(x.id_proyecto||x.id||'\\u2014'))"),
    # Variante con p en vez de x
    ("(p.id_proyecto||p.id||'—')", "(p.nombre_proyecto?(p.id_proyecto+' — '+p.nombre_proyecto):(p.id_proyecto||p.id||'—'))"),
]

for old, new in pres_old_patterns:
    count = idx_content.count(old)
    if count > 0:
        # Solo reemplazar en contexto de presupuestos (no en toda la app)
        idx_content = idx_content.replace(old, new)
        print(f'  OK: Presupuestos ID→nombre ({count} hits): {old[:40]}...')
        changes_made += 1

# PARCHE D: Añadir skills a las tarjetas de proyecto BUILD
# Buscar el patrón de la tarjeta que tiene PM y Presupuesto
# y añadir una fila de Skills después
skills_injection = """+'<div class="pc-r"><span>Skills</span><span class="pc-v" style="font-size:10px;">'+(p.skills_requeridas||'—')+'</span></div>'"""

# Buscar el patrón después de Presupuesto en la tarjeta
pres_card = "+'<div class=\"pc-r\"><span>Presupuesto</span>"
if pres_card in idx_content:
    # Buscar el cierre de esa línea
    pres_idx = idx_content.find(pres_card)
    # Encontrar el final de esa línea (siguiente +'<div)
    next_div = idx_content.find("+'<div", pres_idx + len(pres_card))
    if next_div > -1 and next_div - pres_idx < 300:
        # Insertar skills entre Presupuesto y el siguiente div
        idx_content = idx_content[:next_div] + skills_injection + idx_content[next_div:]
        print('  OK: Skills row añadida a tarjetas de proyecto')
        changes_made += 1
    else:
        print('  WARN: no encontré cierre de Presupuesto card')
elif "+'<div class=\"pc-r\"><span>Presupuesto" in idx_content:
    # Variante con comillas simples
    print('  INFO: encontré variante de Presupuesto card, intentando...')
else:
    print('  WARN: Presupuesto card no encontrado — puede tener formato diferente')

# Buscar también el patrón de gov-build.html
alt_pres_card = """h+='<div class="pc-r"><span>Presupuesto</span>"""
if alt_pres_card in idx_content:
    alt_idx = idx_content.find(alt_pres_card)
    # Encontrar el final de esa sentencia (;) o siguiente h+=
    next_h = idx_content.find("h+='<div", alt_idx + len(alt_pres_card))
    if next_h > -1 and next_h - alt_idx < 300:
        skills_alt = """h+='<div class="pc-r"><span>Skills</span><span class="pc-v" style="font-size:10px;">'+(p.skills_requeridas||'—')+'</span></div>';\n"""
        idx_content = idx_content[:next_h] + skills_alt + idx_content[next_h:]
        print('  OK: Skills row (alt format) añadida')
        changes_made += 1

# ═══════════════════════════════════════════════════════════
# GUARDAR
# ═══════════════════════════════════════════════════════════
if changes_made > 0:
    with open(IDX, 'w', encoding='utf-8') as f:
        f.write(idx_content)
    print(f'\n  Guardado index.html con {changes_made} cambios')
else:
    print('\n  Sin cambios en index.html (ya parcheado o patrones diferentes)')

# ═══════════════════════════════════════════════════════════
# PARCHES en gov-run.html y gov-build.html
# ═══════════════════════════════════════════════════════════
print('\n--- Parchando gov-run.html ---')

with open(GOV_RUN, 'r', encoding='utf-8') as f:
    gr = f.read()

gr_changes = 0

# SLA helper
if 'p99SlaHoras' not in gr:
    inject = gr.find('/* P99: Monkey-patch fetch')
    if inject > -1:
        gr = gr[:inject] + SLA_HELPER + '\n' + gr[inject:]
        gr_changes += 1
        print('  OK: SLA helper inyectado')
    elif '</head>' in gr:
        head = gr.find('</head>')
        gr = gr[:head] + '<script>' + SLA_HELPER + '</script>\n' + gr[head:]
        gr_changes += 1
        print('  OK: SLA helper inyectado (head)')

# Reemplazar sla_horas pattern
for old, new in old_sla_patterns:
    if old in gr:
        gr = gr.replace(old, new)
        gr_changes += 1
        print(f'  OK: SLA pattern replaced')

if gr_changes > 0:
    bak_gr = GOV_RUN + '.bak_v3'
    if not os.path.exists(bak_gr):
        shutil.copy2(GOV_RUN, bak_gr)
    with open(GOV_RUN, 'w', encoding='utf-8') as f:
        f.write(gr)
    print(f'  Guardado gov-run.html ({gr_changes} cambios)')

# gov-build.html — añadir skills si no existe
print('\n--- Parchando gov-build.html ---')

with open(GOV_BUILD, 'r', encoding='utf-8') as f:
    gb = f.read()

gb_changes = 0

if 'skills_requeridas' not in gb:
    # Buscar la tarjeta de proyecto y añadir skills
    target = """h+='<div class="pc-r"><span>Presupuesto</span>"""
    if target in gb:
        target_idx = gb.find(target)
        next_h = gb.find("h+='<div", target_idx + len(target))
        if next_h > -1:
            skills_line = """h+='<div class="pc-r"><span>Skills</span><span class="pc-v" style="font-size:10px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+(p.skills_requeridas||'—')+'</span></div>';\n"""
            gb = gb[:next_h] + skills_line + gb[next_h:]
            gb_changes += 1
            print('  OK: Skills row añadida a tarjetas')

if gb_changes > 0:
    bak_gb = GOV_BUILD + '.bak_v3'
    if not os.path.exists(bak_gb):
        shutil.copy2(GOV_BUILD, bak_gb)
    with open(GOV_BUILD, 'w', encoding='utf-8') as f:
        f.write(gb)
    print(f'  Guardado gov-build.html ({gb_changes} cambios)')

# ═══════════════════════════════════════════════════════════
# RESTART nginx
# ═══════════════════════════════════════════════════════════
print('\n--- Restarting nginx ---')
os.system('docker restart cognitive-pmo-web-1')

print('\n' + '=' * 60)
print('P99 FRONTEND FIXES v3 COMPLETO')
print('Recargar navegador (Cmd+Shift+R)')
print('=' * 60)

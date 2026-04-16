#!/usr/bin/env python3
"""
P99 Frontend Patch v2 — Fixes 1, 6, 7
=======================================
Aplica sobre archivos YA parcheados por p99_patch_frontend.py

FIX 1: Tab persistence — al cambiar banco, vuelve a la misma tab (no a RUN)
FIX 6: Primitiva en drawer — boton "Datos Originales" para ir al escenario demo
FIX 7: Bordes degradados — contorno de color del banco activo estilo Cowork takeover

Uso: python3 p99_patch_frontend_v2.py
"""
import os

BASE = '/root/cognitive-pmo/frontend'

# ═══════════════════════════════════════════════════════════
# FIX 1: Tab persistence en el monkey-patch (TODOS los HTML)
# ═══════════════════════════════════════════════════════════

OLD_ONCHANGE = """  if (window.ScenarioBridge) {
    ScenarioBridge.onChange(function(sc) {
      console.log('[P99] Scenario changed to ' + sc + ' - reloading...');
      window.location.reload();
    });
  }"""

NEW_ONCHANGE = """  if (window.ScenarioBridge) {
    ScenarioBridge.onChange(function(sc) {
      console.log('[P99] Scenario changed to ' + sc + ' - reloading...');
      /* FIX 1: guardar tab activa antes de reload */
      var ap = document.querySelector('.page.active');
      if (ap) sessionStorage.setItem('p99_active_tab', ap.id.replace('page-',''));
      /* Guardar scroll position */
      sessionStorage.setItem('p99_scroll', window.scrollY.toString());
      window.location.reload();
    });
    /* FIX 1: restaurar tab despues de reload por cambio de escenario */
    var savedTab = sessionStorage.getItem('p99_active_tab');
    if (savedTab) {
      sessionStorage.removeItem('p99_active_tab');
      window.addEventListener('DOMContentLoaded', function(){
        setTimeout(function(){
          var tabBtn = document.querySelector('.nav-tab.' + savedTab);
          if (tabBtn && window.showPage) {
            showPage(savedTab, tabBtn);
            var sy = parseInt(sessionStorage.getItem('p99_scroll')||'0');
            sessionStorage.removeItem('p99_scroll');
            if (sy) window.scrollTo(0, sy);
          }
        }, 200);
      });
    }
  }"""

# ═══════════════════════════════════════════════════════════
# FIX 6 + 7: Nuevo drawer con primitiva + bordes de color
# ═══════════════════════════════════════════════════════════

OLD_DRAWER = '<!-- ═══ P99 SCENARIO DRAWER ═══ -->'
END_DRAWER = '<!-- ═══ END P99 SCENARIO DRAWER ═══ -->'

NEW_DRAWER_FULL = '''<!-- ═══ P99 SCENARIO DRAWER ═══ -->
<style>
#p99-trigger{position:fixed;left:0;top:0;width:5px;height:100vh;z-index:10001;cursor:default;}
#p99-drawer{
  position:fixed;left:0;top:0;width:270px;height:100vh;
  background:var(--bg2);border-right:1px solid var(--border);
  z-index:10000;transform:translateX(-100%);transition:transform .25s cubic-bezier(.4,0,.2,1);
  padding:24px 16px;overflow-y:auto;
  box-shadow:4px 0 24px rgba(0,0,0,.4);
}
#p99-trigger:hover ~ #p99-drawer,
#p99-drawer:hover{transform:translateX(0);}
.p99-hdr{font-size:10px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:var(--text2);margin-bottom:14px;display:flex;align-items:center;gap:6px;}
.p99-hdr svg{width:14px;height:14px;stroke:var(--text2);}
.p99-bank{
  display:flex;align-items:center;gap:10px;
  padding:11px 13px;border-radius:8px;cursor:pointer;
  border:1px solid var(--border);margin-bottom:7px;
  transition:all .2s;
}
.p99-bank:hover{background:rgba(255,255,255,.03);border-color:var(--text3);}
.p99-bank.active{border-color:var(--bclr);background:color-mix(in srgb, var(--bclr) 8%, transparent);}
.p99-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;transition:box-shadow .2s;}
.p99-bank.active .p99-dot{box-shadow:0 0 8px var(--bclr);}
.p99-bname{font-size:13px;font-weight:600;color:var(--text);}
.p99-bsub{font-size:10px;color:var(--text2);margin-top:1px;}
.p99-sep{height:1px;background:var(--border);margin:18px 0;}
.p99-info{padding:12px;background:var(--bg3);border-radius:8px;border:1px solid var(--border2);}
.p99-info-title{font-size:9px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--text3);margin-bottom:8px;}
.p99-irow{display:flex;justify-content:space-between;font-size:11px;padding:3px 0;color:var(--text2);}
.p99-ival{color:var(--text);font-weight:600;font-family:var(--mono);}
.p99-footer{margin-top:16px;font-size:10px;color:var(--text3);line-height:1.5;}
/* FIX 6: estilo especial para primitiva */
.p99-bank.primitiva{border-style:dashed;opacity:.85;}
.p99-bank.primitiva:hover{opacity:1;}
.p99-bank.primitiva.active{border-style:solid;opacity:1;}
/* FIX 7: borde degradado por banco */
#p99-border-overlay{
  position:fixed;inset:0;z-index:9998;pointer-events:none;
  border:2px solid transparent;
  transition:border-color .4s, box-shadow .4s;
  border-radius:0;
}
#p99-border-overlay.active{
  border-color:var(--p99-bcolor);
  box-shadow:inset 0 0 30px -10px var(--p99-bcolor),
             inset 0 0 80px -30px color-mix(in srgb, var(--p99-bcolor) 20%, transparent);
}
</style>
<!-- FIX 7: overlay de bordes -->
<div id="p99-border-overlay"></div>
<div id="p99-trigger"></div>
<div id="p99-drawer">
  <div class="p99-hdr">
    <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
    Escenario Activo
  </div>
  <div id="p99-banks"></div>
  <div class="p99-sep"></div>
  <div class="p99-info">
    <div class="p99-info-title">Conexion actual</div>
    <div id="p99-sinfo"></div>
  </div>
  <div class="p99-sep"></div>
  <div class="p99-info">
    <div class="p99-info-title">Como funciona</div>
    <div class="p99-footer">
      Cada banco es un esquema PostgreSQL independiente.<br><br>
      Al cambiar de banco, <strong style="color:var(--text);">todos los datos</strong> de los 17 endpoints se recargan automaticamente.<br><br>
      Los <strong style="color:var(--text);">150 tecnicos</strong> son compartidos entre bancos (pool comun), pero su ocupacion se calcula en tiempo real segun las incidencias y tareas de cada banco.
    </div>
  </div>
</div>
<script>
(function(){
  var banks = [
    {key:'primitiva',  name:'Datos Originales', sub:'Escenario demo completo', color:'#a855f7', prim:true},
    {key:'sc_norte',   name:'Banco Norte',   sub:'Banca tradicional',        color:'#2196F3', prim:false},
    {key:'sc_iberico', name:'Banco Iberico',  sub:'Banca digital',           color:'#FF9800', prim:false},
    {key:'sc_litoral', name:'Banco Litoral',  sub:'Banca gran escala',       color:'#4CAF50', prim:false}
  ];
  var el = document.getElementById('p99-banks');
  var borderEl = document.getElementById('p99-border-overlay');
  if (!el || !window.ScenarioBridge) return;

  /* FIX 7: aplicar borde de color (solo bancos, NO primitiva) */
  function applyBorder(bank){
    if (!borderEl) return;
    if (bank.prim) {
      /* Primitiva = limpio, sin borde */
      borderEl.classList.remove('active');
      return;
    }
    borderEl.style.setProperty('--p99-bcolor', bank.color);
    borderEl.classList.add('active');
  }

  function render(){
    var cur = ScenarioBridge.get();
    var curBank = banks.find(function(x){ return x.key === cur; }) || banks[0];

    /* FIX 7: borde (solo bancos, primitiva = limpio) */
    applyBorder(curBank);

    var html = '';
    banks.forEach(function(b, i){
      var act = b.key === cur;
      var cls = 'p99-bank' + (act ? ' active' : '') + (b.prim ? ' primitiva' : '');
      /* Separador entre primitiva y los bancos */
      if (i === 1) {
        html += '<div style="margin:12px 0 8px;display:flex;align-items:center;gap:8px;">'
          + '<div style="flex:1;height:1px;background:var(--border);"></div>'
          + '<span style="font-size:9px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--text3);">Bancos</span>'
          + '<div style="flex:1;height:1px;background:var(--border);"></div>'
          + '</div>';
      }
      html += '<div class="' + cls + '" style="--bclr:' + b.color + ';" data-sc="' + b.key + '">'
        + '<div class="p99-dot" style="background:' + b.color + ';"></div>'
        + '<div><div class="p99-bname">' + b.name + '</div>'
        + '<div class="p99-bsub">' + b.sub + '</div></div>'
        + '</div>';
    });
    el.innerHTML = html;

    /* Bind clicks */
    el.querySelectorAll('.p99-bank').forEach(function(btn){
      btn.addEventListener('click', function(){
        ScenarioBridge.set(btn.dataset.sc);
      });
    });

    /* Info panel */
    var info = document.getElementById('p99-sinfo');
    if(info){
      info.innerHTML = ''
        + '<div class="p99-irow"><span>Esquema PG</span><span class="p99-ival">' + cur + '</span></div>'
        + '<div class="p99-irow"><span>Header HTTP</span><span class="p99-ival">X-Scenario</span></div>'
        + '<div class="p99-irow"><span>Search path</span><span class="p99-ival">' + cur + ', compartido</span></div>'
        + '<div class="p99-irow"><span>Estado</span><span class="p99-ival" style="color:' + curBank.color + ';">\\u25CF Activo</span></div>';
    }
  }
  render();
  ScenarioBridge.onChange(function(){ render(); });
})();
</script>
<!-- ═══ END P99 SCENARIO DRAWER ═══ -->'''

# ═══════════════════════════════════════════════════════════
# APLICAR PARCHES
# ═══════════════════════════════════════════════════════════

FILES_MONKEY = [
    'index.html',
    'gov-run.html',
    'gov-build.html',
    'tech-dashboard.html',
    'p96/index.html',
]

print('P99 Frontend Patch v2 — Fixes 1, 6, 7')
print('=' * 50)

# FIX 1: Tab persistence en TODOS los HTML
for fname in FILES_MONKEY:
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f'  NOT FOUND: {fname}')
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if OLD_ONCHANGE in content:
        content = content.replace(OLD_ONCHANGE, NEW_ONCHANGE, 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  FIX 1 OK: {fname} — tab persistence')
    elif 'p99_active_tab' in content:
        print(f'  FIX 1 SKIP: {fname} — ya parcheado')
    else:
        print(f'  FIX 1 WARN: {fname} — no encontre el bloque onChange')

# FIX 6 + 7: Drawer + bordes SOLO en index.html
idx_path = os.path.join(BASE, 'index.html')
with open(idx_path, 'r', encoding='utf-8') as f:
    content = f.read()

if OLD_DRAWER in content and END_DRAWER in content:
    start = content.index(OLD_DRAWER)
    end = content.index(END_DRAWER) + len(END_DRAWER)
    content = content[:start] + NEW_DRAWER_FULL + content[end:]
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  FIX 6+7 OK: index.html — primitiva + bordes degradados')
elif 'p99-border-overlay' in content:
    print(f'  FIX 6+7 SKIP: index.html — ya parcheado')
else:
    print(f'  FIX 6+7 WARN: index.html — no encontre marcadores del drawer')

# FIX 6 extra: añadir primitiva a VALID en scenario-bridge.js
sb_path = os.path.join(BASE, 'js/scenario-bridge.js')
with open(sb_path, 'r', encoding='utf-8') as f:
    sb = f.read()

if "'primitiva'" not in sb:
    OLD_VALID = "sc_litoral: { label: 'Banco Litoral', color: '#4CAF50' }"
    NEW_VALID = "sc_litoral: { label: 'Banco Litoral', color: '#4CAF50' },\n    primitiva:  { label: 'Datos Originales', color: '#a855f7' }"
    if OLD_VALID in sb:
        sb = sb.replace(OLD_VALID, NEW_VALID, 1)
        print(f'  FIX 6 OK: scenario-bridge.js — primitiva añadida a VALID')
    else:
        print(f'  FIX 6 WARN: scenario-bridge.js — no encontre VALID dict')
else:
    print(f'  FIX 6 SKIP: scenario-bridge.js — primitiva ya existe')

# Cambiar DEFAULT a primitiva
OLD_DEFAULT = "var DEFAULT     = 'sc_norte';"
NEW_DEFAULT = "var DEFAULT     = 'primitiva';"
if OLD_DEFAULT in sb:
    sb = sb.replace(OLD_DEFAULT, NEW_DEFAULT, 1)
    print(f'  FIX 6 OK: scenario-bridge.js — DEFAULT cambiado a primitiva')
elif NEW_DEFAULT in sb:
    print(f'  FIX 6 SKIP: scenario-bridge.js — DEFAULT ya es primitiva')

with open(sb_path, 'w', encoding='utf-8') as f:
    f.write(sb)

print('')
print('=' * 50)
print('LISTO. Recargar navegador (Cmd+Shift+R)')
print('=' * 50)

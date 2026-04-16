#!/usr/bin/env python3
"""
P99 Frontend Patch — Multi-Escenario
=====================================
Inyecta en los 5 dashboards HTML:
  1. <script src="/js/scenario-bridge.js">
  2. Monkey-patch global fetch → auto X-Scenario header
  3. Auto-reload on scenario change

Solo en index.html:
  4. Drawer lateral oculto (borde izquierdo) con selector de banco

Cada HTML se parchea insertando ANTES del primer </head>.
Backups: *.bak_p99_frontend

Uso: python3 p99_patch_frontend.py
"""
import os, shutil, sys

BASE = '/root/cognitive-pmo/frontend'

# ─────────────────────────────────────────────────────────
# SNIPPET 1: scenario-bridge + monkey-patch (TODOS los HTML)
# ─────────────────────────────────────────────────────────
BRIDGE_AND_MONKEY = '''<!-- ═══ P99 MULTI-ESCENARIO ═══ -->
<script src="/js/scenario-bridge.js"></script>
<script>
/* P99: Monkey-patch fetch -> auto-inject X-Scenario */
(function(){
  var _F = window.fetch;
  window.fetch = function(url, opts) {
    opts = opts || {};
    if (!opts.headers) opts.headers = {};
    if (typeof opts.headers.set === 'function') {
      if (!opts.headers.has('X-Scenario'))
        opts.headers.set('X-Scenario', window.ScenarioBridge ? ScenarioBridge.get() : 'sc_norte');
    } else {
      if (!opts.headers['X-Scenario'])
        opts.headers['X-Scenario'] = window.ScenarioBridge ? ScenarioBridge.get() : 'sc_norte';
    }
    return _F.call(this, url, opts);
  };
  if (window.ScenarioBridge) {
    ScenarioBridge.onChange(function(sc) {
      console.log('[P99] Scenario changed to ' + sc + ' - reloading...');
      window.location.reload();
    });
  }
})();
</script>
<!-- ═══ END P99 MULTI-ESCENARIO ═══ -->
'''

# ─────────────────────────────────────────────────────────
# SNIPPET 2: Drawer lateral (SOLO index.html)
# ─────────────────────────────────────────────────────────
DRAWER_HTML = '''<!-- ═══ P99 SCENARIO DRAWER ═══ -->
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
</style>
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
    {key:'sc_norte',   name:'Banco Norte',   sub:'Banca tradicional', color:'#2196F3'},
    {key:'sc_iberico', name:'Banco Iberico',  sub:'Banca digital',    color:'#FF9800'},
    {key:'sc_litoral', name:'Banco Litoral',  sub:'Banca gran escala',color:'#4CAF50'}
  ];
  var el = document.getElementById('p99-banks');
  if (!el || !window.ScenarioBridge) return;

  function render(){
    var cur = ScenarioBridge.get();
    el.innerHTML = banks.map(function(b){
      var act = b.key === cur;
      return '<div class="p99-bank' + (act ? ' active' : '') + '" style="--bclr:' + b.color + ';" data-sc="' + b.key + '">'
        + '<div class="p99-dot" style="background:' + b.color + ';"></div>'
        + '<div><div class="p99-bname">' + b.name + '</div>'
        + '<div class="p99-bsub">' + b.sub + '</div></div>'
        + '</div>';
    }).join('');
    // Bind clicks
    el.querySelectorAll('.p99-bank').forEach(function(btn){
      btn.addEventListener('click', function(){
        ScenarioBridge.set(btn.dataset.sc);
      });
    });
    // Info panel
    var info = document.getElementById('p99-sinfo');
    if(info){
      var b = banks.find(function(x){ return x.key === cur; });
      info.innerHTML = ''
        + '<div class="p99-irow"><span>Esquema PG</span><span class="p99-ival">' + cur + '</span></div>'
        + '<div class="p99-irow"><span>Header HTTP</span><span class="p99-ival">X-Scenario</span></div>'
        + '<div class="p99-irow"><span>Search path</span><span class="p99-ival">' + cur + ', compartido</span></div>'
        + '<div class="p99-irow"><span>Estado</span><span class="p99-ival" style="color:' + b.color + ';">● Activo</span></div>';
    }
  }
  render();
  ScenarioBridge.onChange(function(){ render(); });
})();
</script>
<!-- ═══ END P99 SCENARIO DRAWER ═══ -->
'''

# ─────────────────────────────────────────────────────────
# ARCHIVOS A PARCHEAR
# ─────────────────────────────────────────────────────────
FILES = [
    'index.html',
    'gov-run.html',
    'gov-build.html',
    'tech-dashboard.html',
    'p96/index.html',
]

errors = []
ok = []

for fname in FILES:
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        errors.append(f'NOT FOUND: {fname}')
        continue

    # Backup
    bak = path + '.bak_p99_frontend'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        print(f'  Backup: {fname} -> {fname}.bak_p99_frontend')
    else:
        print(f'  Backup ya existe: {fname}.bak_p99_frontend')

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already patched
    if 'P99 MULTI-ESCENARIO' in content:
        print(f'  SKIP: {fname} ya parcheado')
        ok.append(fname)
        continue

    # 1. Inject scenario-bridge + monkey-patch before first </head>
    if '</head>' not in content:
        errors.append(f'NO </head> IN: {fname}')
        continue

    content = content.replace('</head>', BRIDGE_AND_MONKEY + '</head>', 1)

    # 2. For index.html only: inject drawer after <body>
    if fname == 'index.html':
        if '<body>' in content:
            content = content.replace('<body>', '<body>\n' + DRAWER_HTML, 1)
            print(f'  Drawer inyectado en {fname}')
        else:
            errors.append(f'NO <body> IN: {fname}')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    ok.append(fname)
    print(f'  OK: {fname}')

# ─────────────────────────────────────────────────────────
# RESUMEN
# ─────────────────────────────────────────────────────────
print('\n' + '=' * 50)
print(f'RESULTADO: {len(ok)}/{len(FILES)} parcheados')
if errors:
    print('ERRORES:')
    for e in errors:
        print(f'  ! {e}')
else:
    print('Sin errores.')
print('=' * 50)
print('\nSiguiente paso:')
print('  docker cp /root/cognitive-pmo/frontend/ cognitive-pmo-web-1:/usr/share/nginx/html/')
print('  O si nginx sirve directo del volumen, solo recargar el navegador.')

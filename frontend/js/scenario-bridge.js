/**
 * scenario-bridge.js — Cognitive PMO Scenario Switching
 * =====================================================
 * Utilidad compartida para TODOS los dashboards.
 * Gestiona el escenario activo (X-Scenario header) y notifica cambios.
 *
 * Uso desde cualquier HTML:
 *   <script src="/js/scenario-bridge.js"></script>
 *
 * API:
 *   ScenarioBridge.get()                → 'sc_norte' | 'sc_iberico' | 'sc_litoral'
 *   ScenarioBridge.set('sc_iberico')    → cambia + dispara evento + persiste
 *   ScenarioBridge.header()             → { 'X-Scenario': 'sc_iberico' }
 *   ScenarioBridge.onChange(callback)    → registra listener
 *   ScenarioBridge.injectInto(headers)  → muta el objeto headers añadiendo X-Scenario
 */
(function (root) {
  'use strict';

  var STORAGE_KEY = 'cpm_active_scenario';
  var EVENT_NAME  = 'scenario-changed';
  var DEFAULT     = 'primitiva';

  /* ── Catálogo de escenarios válidos ── */
  var VALID = {
    sc_norte:   { label: 'Banco Norte',   color: '#2196F3' },
    sc_iberico: { label: 'Banco Ibérico', color: '#FF9800' },
    sc_litoral: { label: 'Banco Litoral', color: '#4CAF50' },
    primitiva:  { label: 'Datos Originales', color: '#a855f7' },
    primitiva:  { label: 'Datos Originales', color: '#a855f7' }
  };

  /* ── Leer escenario activo ── */
  function get() {
    // 1. URL param tiene prioridad (para links directos)
    var params = new URLSearchParams(window.location.search);
    var fromUrl = params.get('scenario');
    if (fromUrl && VALID[fromUrl]) return fromUrl;

    // 2. localStorage
    try {
      var stored = localStorage.getItem(STORAGE_KEY);
      if (stored && VALID[stored]) return stored;
    } catch (e) { /* private browsing */ }

    return DEFAULT;
  }

  /* ── Cambiar escenario ── */
  function set(name) {
    if (!VALID[name]) {
      console.warn('[ScenarioBridge] Escenario no válido:', name, '— válidos:', Object.keys(VALID));
      return;
    }
    try { localStorage.setItem(STORAGE_KEY, name); } catch (e) { /* ok */ }

    // Disparar evento global (lo escuchan todos los dashboards)
    var evt = new CustomEvent(EVENT_NAME, { detail: { scenario: name, meta: VALID[name] } });
    window.dispatchEvent(evt);

    // También storage event para tabs cruzados
    // (localStorage ya lo hace automáticamente en otras pestañas)
  }

  /* ── Header listo para inyectar en fetch ── */
  function header() {
    var h = {};
    h['X-Scenario'] = get();
    return h;
  }

  /* ── Inyectar X-Scenario en un objeto headers existente ── */
  function injectInto(headers) {
    if (!headers) headers = {};
    headers['X-Scenario'] = get();
    return headers;
  }

  /* ── Registrar callback de cambio ── */
  function onChange(cb) {
    window.addEventListener(EVENT_NAME, function (e) {
      cb(e.detail.scenario, e.detail.meta);
    });
    // También escuchar cambios desde otra pestaña
    window.addEventListener('storage', function (e) {
      if (e.key === STORAGE_KEY && e.newValue && VALID[e.newValue]) {
        cb(e.newValue, VALID[e.newValue]);
      }
    });
  }

  /* ── Info del escenario activo ── */
  function info() {
    var s = get();
    return { scenario: s, label: VALID[s].label, color: VALID[s].color };
  }

  /* ── Lista completa de escenarios ── */
  function list() {
    return Object.keys(VALID).map(function (k) {
      return { key: k, label: VALID[k].label, color: VALID[k].color, active: k === get() };
    });
  }

  /* ── Selector UI reutilizable (inyecta HTML en un contenedor) ── */
  function renderSelector(containerId) {
    var el = document.getElementById(containerId);
    if (!el) return;

    var current = get();
    var html = '<div class="scenario-selector" style="display:flex;gap:6px;align-items:center;">';
    html += '<span style="font-size:11px;color:#999;margin-right:4px;">BANCO:</span>';

    Object.keys(VALID).forEach(function (k) {
      var v = VALID[k];
      var isActive = k === current;
      html += '<button class="scenario-btn' + (isActive ? ' active' : '') + '" '
            + 'data-scenario="' + k + '" '
            + 'style="'
            + 'padding:4px 10px;border-radius:4px;font-size:11px;font-weight:600;cursor:pointer;'
            + 'border:1px solid ' + v.color + ';'
            + 'background:' + (isActive ? v.color : 'transparent') + ';'
            + 'color:' + (isActive ? '#fff' : v.color) + ';'
            + 'transition:all .2s;"'
            + '>' + v.label + '</button>';
    });
    html += '</div>';
    el.innerHTML = html;

    // Bind clicks
    el.querySelectorAll('.scenario-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        set(btn.dataset.scenario);
        renderSelector(containerId); // re-render
      });
    });
  }

  /* ── Indicador de banco activo (badge) ── */
  function renderBadge(containerId) {
    var el = document.getElementById(containerId);
    if (!el) return;
    var i = info();
    el.innerHTML = '<span style="'
      + 'display:inline-flex;align-items:center;gap:5px;'
      + 'padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;'
      + 'background:' + i.color + '22;color:' + i.color + ';border:1px solid ' + i.color + '44;">'
      + '<span style="width:7px;height:7px;border-radius:50%;background:' + i.color + ';"></span>'
      + i.label
      + '</span>';
  }

  /* ── Exponer API pública ── */
  root.ScenarioBridge = {
    get: get,
    set: set,
    header: header,
    injectInto: injectInto,
    onChange: onChange,
    info: info,
    list: list,
    renderSelector: renderSelector,
    renderBadge: renderBadge,
    VALID: VALID,
    DEFAULT: DEFAULT
  };

})(window);

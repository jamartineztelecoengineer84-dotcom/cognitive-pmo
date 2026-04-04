// ═══════════════════════════════════════════════════════════════════
// JAVASCRIPT: Pestaña "Calendario CAB" para gov-build.html
// INSERTAR: dentro del bloque <script> de gov-build.html
// ═══════════════════════════════════════════════════════════════════

// ── Variables globales CAB ──
var cabCurrentMonth = new Date().getMonth();
var cabCurrentYear = new Date().getFullYear();
var cabPeriodos = [];
var cabCurrentPropuestaId = null;
var cabMonthNames = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];

// ── Navegación entre sub-vistas CAB ──
function showCABView(view) {
  var views = ['calendar','proposals','newform','progress','detail'];
  views.forEach(function(v) {
    var el = document.getElementById('cab-view-' + v);
    if (el) el.style.display = v === view ? 'block' : 'none';
  });
  var btns = document.querySelectorAll('.cab-sub-btn');
  btns.forEach(function(b) {
    var bv = b.getAttribute('data-cabview');
    if (bv === view) {
      b.style.background = 'var(--accent,#7c3aed)';
      b.style.color = '#fff';
      b.style.border = 'none';
    } else {
      b.style.background = 'var(--bg3,#2a2a3e)';
      b.style.color = 'var(--text2,#aaa)';
      b.style.border = '1px solid var(--border,#333)';
    }
  });
}

// ── Carga inicial de datos CAB ──
async function loadCABData() {
  try {
    // Cargar periodos
    var periodos = await af('/cab/periodos');
    if (Array.isArray(periodos)) {
      cabPeriodos = periodos;
      // Poblar selector
      var sel = document.getElementById('cab-periodo-select');
      if (sel) {
        sel.innerHTML = '<option value="">-- Seleccionar periodo --</option>';
        periodos.forEach(function(p) {
          var o = document.createElement('option');
          o.value = p.nombre_periodo;
          o.textContent = p.nombre_periodo + ' (' + p.impacto_estimado + ', ' + p.carga_pico_esperada_pct + '%)';
          sel.appendChild(o);
        });
      }
      // Sidebar periodos
      var sidebar = document.getElementById('cab-periodos-sidebar');
      if (sidebar) {
        sidebar.innerHTML = periodos.map(function(p) {
          var impColor = p.impacto_estimado === 'ALTO' ? '#ef4444' : '#f59e0b';
          var impBg = p.impacto_estimado === 'ALTO' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)';
          return '<div style="padding:4px 0;border-bottom:1px solid var(--border,#333);">' +
            '<span style="background:' + impBg + ';color:' + impColor + ';padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;">' + p.impacto_estimado + '</span> ' +
            '<span style="color:var(--text1,#fff);margin-left:4px;">' + p.nombre_periodo.replace(/_/g,' ').substring(0,20) + '</span>' +
            '<div style="color:var(--text2,#888);font-size:10px;">' + (p.fecha_inicio||'').substring(0,10) + ' — ' + (p.fecha_fin||'').substring(0,10) + ' (' + p.carga_pico_esperada_pct + '%)</div></div>';
        }).join('');
      }
    }

    // Total activos
    try {
      var dashboard = await af('/cmdb/dashboard');
      var totalEl = document.getElementById('cab-total-activos');
      if (totalEl && dashboard && dashboard.total_activos) totalEl.textContent = dashboard.total_activos;
    } catch(e) { /* ignore */ }

    // Cargar propuestas
    await loadCABPropuestas();

    // Renderizar calendario
    cabRenderCalendar();

  } catch(e) { console.error('Error loading CAB data:', e); }
}

// ── Cargar lista de propuestas ──
async function loadCABPropuestas() {
  try {
    var props = await af('/cab/propuestas');
    var list = document.getElementById('cab-propuestas-list');
    if (!list) return;
    if (!Array.isArray(props) || props.length === 0) {
      list.innerHTML = '<p style="color:var(--text2,#aaa);">Sin propuestas aun. Genera la primera.</p>';
      return;
    }
    list.innerHTML = props.map(function(p) {
      var stColor = p.estado === 'APLICADO' ? '#10b981' : p.estado === 'RECHAZADO' ? '#ef4444' : '#f59e0b';
      var stBg = p.estado === 'APLICADO' ? 'rgba(16,185,129,0.15)' : p.estado === 'RECHAZADO' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)';
      return '<div style="background:var(--bg2,#1e1e2e);border-radius:10px;padding:14px 16px;margin-bottom:8px;cursor:pointer;border:1px solid var(--border,#333);" onclick="cargarPropuestaCAB(\'' + p.id + '\')">' +
        '<div style="display:flex;justify-content:space-between;align-items:center;">' +
          '<div>' +
            '<p style="margin:0;font-size:14px;font-weight:600;color:var(--text1,#fff);">' + (p.periodo||'').replace(/_/g,' ') + ' #' + (p.numero_propuesta||1) + '</p>' +
            '<p style="margin:2px 0 0;font-size:12px;color:var(--text2,#aaa);">' + (p.cambios_aplicados||0) + ' cambios aplicados</p>' +
          '</div>' +
          '<span style="background:' + stBg + ';color:' + stColor + ';padding:3px 10px;border-radius:10px;font-size:11px;font-weight:600;">' + p.estado + '</span>' +
        '</div>' +
        '<div style="display:flex;gap:16px;margin-top:6px;font-size:11px;color:var(--text2,#888);">' +
          '<span>' + (p.fecha_generacion||'').substring(0,16).replace('T',' ') + '</span>' +
          '<span>' + (p.generado_por||'AG-011') + '</span>' +
        '</div></div>';
    }).join('');
  } catch(e) { console.error('Error loading propuestas:', e); }
}

// ── Calendario mensual ──
function cabRenderCalendar() {
  var label = document.getElementById('cab-month-label');
  if (label) label.textContent = cabMonthNames[cabCurrentMonth] + ' ' + cabCurrentYear;
  var container = document.getElementById('cab-cal-days');
  if (!container) return;
  container.innerHTML = '';
  var first = new Date(cabCurrentYear, cabCurrentMonth, 1);
  var dow = (first.getDay() + 6) % 7;
  var daysInMonth = new Date(cabCurrentYear, cabCurrentMonth + 1, 0).getDate();

  for (var i = 0; i < dow; i++) {
    var empty = document.createElement('div');
    empty.style.cssText = 'visibility:hidden;padding:6px;';
    container.appendChild(empty);
  }

  for (var d = 1; d <= daysInMonth; d++) {
    var el = document.createElement('div');
    el.style.cssText = 'text-align:center;padding:6px 2px;border-radius:4px;font-size:12px;color:var(--text2,#aaa);';
    el.textContent = d;
    var dt = new Date(cabCurrentYear, cabCurrentMonth, d);
    var cls = '';
    for (var pi = 0; pi < cabPeriodos.length; pi++) {
      var ps = new Date(cabPeriodos[pi].fecha_inicio);
      var pe = new Date(cabPeriodos[pi].fecha_fin);
      if (dt >= ps && dt <= pe) {
        if (cabPeriodos[pi].impacto_estimado === 'ALTO') cls = 'excl';
        else if (!cls) cls = 'warn';
      }
    }
    if (cls === 'excl') {
      el.style.background = 'rgba(239,68,68,0.2)';
      el.style.color = '#ef4444';
      el.style.fontWeight = '600';
    } else if (cls === 'warn') {
      el.style.background = 'rgba(245,158,11,0.2)';
      el.style.color = '#f59e0b';
      el.style.fontWeight = '600';
    } else if (dt.getDay() === 0 || dt.getDay() === 6) {
      el.style.background = 'rgba(16,185,129,0.12)';
      el.style.color = '#10b981';
    }
    container.appendChild(el);
  }
}

function cabChangeMonth(delta) {
  cabCurrentMonth += delta;
  if (cabCurrentMonth > 11) { cabCurrentMonth = 0; cabCurrentYear++; }
  if (cabCurrentMonth < 0) { cabCurrentMonth = 11; cabCurrentYear--; }
  cabRenderCalendar();
}

// ── Generar propuesta CAB (POST + SSE) ──
async function generarPropuestaCAB() {
  var periodo = document.getElementById('cab-periodo-select').value;
  if (!periodo) { alert('Selecciona un periodo'); return; }

  showCABView('progress');
  var log = document.getElementById('cab-progress-log');
  var bar = document.getElementById('cab-progress-bar');
  var pctLabel = document.getElementById('cab-pct-label');
  if (log) log.innerHTML = '';
  if (bar) bar.style.width = '5%';
  if (pctLabel) pctLabel.textContent = '5%';

  try {
    var r = await fetch('/agents/build/cab-generator', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + TK},
      body: JSON.stringify({periodo: periodo, accion: 'GENERAR_PROPUESTA'})
    });
    var data = JSON.parse(await r.text());
    var jobId = data.job_id;

    cabAddLog(log, '✅ Job creado: ' + jobId);
    cabSetProgress(bar, pctLabel, 10);

    var es = new EventSource(data.stream_url);

    es.addEventListener('director_start', function(e) {
      cabAddLog(log, '🎯 Director: Iniciando analisis...'); cabSetProgress(bar, pctLabel, 15);
    });
    es.addEventListener('director_analysis', function(e) {
      var d = JSON.parse(e.data);
      cabAddLog(log, '📊 Director: ' + (d.total_activos||'?') + ' activos, ' + (d.incidencias_activas||0) + ' incidencias activas, ' + (d.proyectos_build_activos||0) + ' proyectos BUILD');
      cabSetProgress(bar, pctLabel, 20);
    });
    es.addEventListener('workers_spawning', function(e) {
      var d = JSON.parse(e.data);
      cabAddLog(log, '🔄 Spawning ' + d.workers + ' workers (' + d.activos_por_worker + ' activos c/u)...');
      cabSetProgress(bar, pctLabel, 25);
    });
    es.addEventListener('worker_complete', function(e) {
      var d = JSON.parse(e.data);
      cabAddLog(log, '✅ Worker ' + d.worker_id + ' completado');
      var pct = Math.min(80, 25 + (d.worker_id || 1) * 9);
      cabSetProgress(bar, pctLabel, pct);
    });
    es.addEventListener('workers_complete', function(e) {
      var d = JSON.parse(e.data);
      cabAddLog(log, '📦 ' + (d.propuestas_totales||'?') + ' propuestas de ' + (d.workers_completados||'?') + ' workers');
      cabSetProgress(bar, pctLabel, 85);
    });
    es.addEventListener('merger_start', function(e) {
      cabAddLog(log, '🔗 Merger: Consolidando + cruzando con BUILD/RUN...');
      cabSetProgress(bar, pctLabel, 90);
    });
    es.addEventListener('merger_complete', function(e) {
      var d = JSON.parse(e.data);
      cabAddLog(log, '✅ Merger completado: ' + (d.cambios_propuestos||'?') + ' cambios, ' + (d.alertas_generadas||0) + ' alertas generadas');
      cabSetProgress(bar, pctLabel, 95);
    });
    es.addEventListener('complete', function(e) {
      var d = JSON.parse(e.data);
      es.close();
      cabAddLog(log, '🎉 COMPLETADO. Propuesta: ' + d.propuesta_id);
      cabSetProgress(bar, pctLabel, 100);
      setTimeout(function() {
        cargarPropuestaCAB(d.propuesta_id);
        loadCABPropuestas();
      }, 1500);
    });
    es.addEventListener('error', function(e) {
      try { var d = JSON.parse(e.data); cabAddLog(log, '❌ Error: ' + (d.mensaje||'desconocido')); } catch(ex) {}
    });
    es.onerror = function() { es.close(); };

  } catch(e) {
    cabAddLog(log, '❌ Error: ' + e.message);
  }
}

function cabAddLog(container, text) {
  if (!container) return;
  var line = document.createElement('div');
  var ts = new Date().toLocaleTimeString();
  line.textContent = '[' + ts + '] ' + text;
  line.style.marginBottom = '4px';
  container.appendChild(line);
  container.scrollTop = container.scrollHeight;
}

function cabSetProgress(bar, label, pct) {
  if (bar) bar.style.width = pct + '%';
  if (label) label.textContent = pct + '%';
}

// ── Cargar detalle de propuesta ──
async function cargarPropuestaCAB(propuestaId) {
  cabCurrentPropuestaId = propuestaId;
  showCABView('detail');
  try {
    var data = await af('/cab/propuestas/' + propuestaId);
    if (!data || !data.propuesta_json) return;
    var prop = typeof data.propuesta_json === 'string' ? JSON.parse(data.propuesta_json) : data.propuesta_json;

    // Header
    var header = document.getElementById('cab-detail-header');
    if (header) {
      var stColor = data.estado === 'APLICADO' ? '#10b981' : data.estado === 'RECHAZADO' ? '#ef4444' : '#f59e0b';
      header.innerHTML = '<div>' +
        '<p style="font-size:16px;font-weight:600;margin:0;color:var(--text1,#fff);">Propuesta CAB — ' + (data.periodo||'').replace(/_/g,' ') + ' #' + (data.numero_propuesta||1) + '</p>' +
        '<p style="font-size:12px;color:var(--text2,#aaa);margin:2px 0 0;">Generada ' + (data.fecha_generacion||'').substring(0,16).replace('T',' ') + ' por AG-011</p></div>' +
        '<div style="display:flex;gap:6px;">' +
          (data.estado === 'PENDING_HUMAN_REVIEW' ? '<button onclick="aprobarPropuestaCAB()" style="padding:5px 14px;background:#10b981;color:#fff;border:none;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;">✅ Aprobar</button><button onclick="rechazarPropuestaCAB()" style="padding:5px 14px;background:var(--bg3,#2a2a3e);color:#ef4444;border:1px solid #ef4444;border-radius:8px;font-size:12px;cursor:pointer;">❌ Rechazar</button>' : '<span style="color:' + stColor + ';font-weight:600;font-size:14px;">' + data.estado + '</span>') +
        '</div>';
    }

    // KPIs
    var resumen = prop.resumen_ejecutivo || {};
    var kpis = document.getElementById('cab-detail-kpis');
    if (kpis) {
      var items = [
        {v: resumen.total_cambios_propuestos || prop.total_propuestas || '?', l: 'Cambios', c: '#7c3aed'},
        {v: (resumen.score_confianza_promedio || 0).toFixed ? (resumen.score_confianza_promedio || 0).toFixed(2) : '?', l: 'Score medio', c: '#10b981'},
        {v: (resumen.conflictos_resueltos || 0), l: 'Conflictos', c: '#f59e0b'},
        {v: (resumen.activos_bloqueados_por_incidencia || 0), l: 'Bloq. por RUN', c: '#ef4444'},
        {v: (resumen.activos_ajustados_por_sprint || 0), l: 'Ajust. por BUILD', c: '#06b6d4'}
      ];
      kpis.innerHTML = items.map(function(m) {
        return '<div style="background:var(--bg2,#1e1e2e);border-radius:10px;padding:10px;text-align:center;">' +
          '<div style="font-size:20px;font-weight:700;color:' + m.c + ';">' + m.v + '</div>' +
          '<div style="font-size:11px;color:var(--text2,#aaa);margin-top:2px;">' + m.l + '</div></div>';
      }).join('');
    }

    // Sub-tabs del detalle
    var cambios = prop.cambios_propuestos || [];
    var conflictos = prop.conflictos_y_resoluciones || [];
    var alertas = prop.alertas_para_humano || [];
    var alertasGob = prop.alertas_para_gobernadores || [];

    var tabs = document.getElementById('cab-detail-tabs');
    if (tabs) {
      tabs.innerHTML = [
        {id:'changes', label:'Cambios (' + cambios.length + ')'},
        {id:'conflicts', label:'Conflictos (' + conflictos.length + ')'},
        {id:'alerts', label:'Alertas (' + alertas.length + ')'},
        {id:'gov-alerts', label:'Alertas gobernadores (' + alertasGob.length + ')'}
      ].map(function(t, i) {
        var active = i === 0;
        return '<button onclick="showCABDetailTab(\'' + t.id + '\')" data-dtab="' + t.id + '" style="padding:4px 10px;border-radius:6px;font-size:11px;font-weight:600;cursor:pointer;' +
          (active ? 'background:var(--accent,#7c3aed);color:#fff;border:none;' : 'background:var(--bg3,#2a2a3e);color:var(--text2,#aaa);border:1px solid var(--border,#333);') +
          '">' + t.label + '</button>';
      }).join('');
    }

    // Guardar datos para sub-tabs
    window._cabDetailData = {cambios: cambios, conflictos: conflictos, alertas: alertas, alertasGob: alertasGob};
    showCABDetailTab('changes');

  } catch(e) { console.error('Error cargando propuesta:', e); }
}

function showCABDetailTab(tabId) {
  var data = window._cabDetailData || {};
  var content = document.getElementById('cab-detail-content');
  if (!content) return;

  // Actualizar botones
  document.querySelectorAll('#cab-detail-tabs button').forEach(function(b) {
    var dt = b.getAttribute('data-dtab');
    if (dt === tabId) { b.style.background='var(--accent,#7c3aed)'; b.style.color='#fff'; b.style.border='none'; }
    else { b.style.background='var(--bg3,#2a2a3e)'; b.style.color='var(--text2,#aaa)'; b.style.border='1px solid var(--border,#333)'; }
  });

  if (tabId === 'changes') {
    var cambios = data.cambios || [];
    content.innerHTML = '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:12px;">' +
      '<thead><tr style="border-bottom:1px solid var(--border,#333);color:var(--text2,#aaa);">' +
      '<th style="text-align:left;padding:6px;">Activo</th><th style="padding:6px;">Criticidad</th><th style="padding:6px;">Ventana</th><th style="padding:6px;">Riesgo</th><th style="padding:6px;">Score</th><th style="padding:6px;">Contexto</th></tr></thead><tbody>' +
      cambios.map(function(c) {
        var v = c.ventana_final || c.ventana_recomendada || {};
        var ctx = c.contexto_operativo || {};
        var incCount = (ctx.incidencias_activas || []).length;
        var sprintCount = (ctx.sprints_solapantes || []).length;
        var ctxHtml = '';
        if (incCount > 0) ctxHtml += '<span style="background:rgba(239,68,68,0.15);color:#ef4444;padding:1px 5px;border-radius:4px;font-size:10px;">P1/P2: ' + incCount + '</span> ';
        if (sprintCount > 0) ctxHtml += '<span style="background:rgba(6,182,212,0.15);color:#06b6d4;padding:1px 5px;border-radius:4px;font-size:10px;">Sprint: ' + sprintCount + '</span>';
        if (!ctxHtml) ctxHtml = '<span style="color:var(--text2,#888);">—</span>';
        var critColor = c.criticidad === 'CRITICA' ? '#ef4444' : c.criticidad === 'ALTA' ? '#f59e0b' : '#06b6d4';
        var riskColor = c.riesgo === 'BAJO' ? '#10b981' : c.riesgo === 'MEDIO' ? '#f59e0b' : '#ef4444';
        var scoreColor = (c.score_confianza || 0) >= 0.85 ? '#10b981' : (c.score_confianza || 0) >= 0.70 ? '#f59e0b' : '#ef4444';
        return '<tr style="border-bottom:1px solid var(--border,#333);">' +
          '<td style="padding:6px;font-weight:600;color:var(--text1,#fff);">' + (c.activo_nombre || c.id_activo) + '</td>' +
          '<td style="padding:6px;text-align:center;color:' + critColor + ';font-weight:600;">' + (c.criticidad||'') + '</td>' +
          '<td style="padding:6px;text-align:center;font-family:monospace;font-size:11px;color:var(--text2,#aaa);">' + (v.dias||[]).join(',') + ' ' + (v.hora_inicio||'') + '-' + (v.hora_fin||'') + '</td>' +
          '<td style="padding:6px;text-align:center;color:' + riskColor + ';font-weight:600;">' + (c.riesgo||'') + '</td>' +
          '<td style="padding:6px;text-align:center;font-weight:600;color:' + scoreColor + ';">' + ((c.score_confianza||0).toFixed ? (c.score_confianza||0).toFixed(2) : '?') + '</td>' +
          '<td style="padding:6px;">' + ctxHtml + '</td></tr>';
      }).join('') + '</tbody></table></div>';

  } else if (tabId === 'conflicts') {
    var conf = data.conflictos || [];
    content.innerHTML = conf.length === 0 ? '<p style="color:var(--text2,#aaa);">Sin conflictos detectados.</p>' :
      conf.map(function(c) {
        return '<div style="background:var(--bg2,#1e1e2e);border-radius:8px;padding:10px 12px;margin-bottom:8px;">' +
          '<div style="display:flex;justify-content:space-between;margin-bottom:4px;">' +
            '<span style="font-size:13px;font-weight:600;color:#f59e0b;">' + (c.tipo||'CONFLICTO') + '</span>' +
            '<span style="background:rgba(16,185,129,0.15);color:#10b981;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600;">' + (c.estado||'RESUELTO') + '</span></div>' +
          '<p style="font-size:12px;color:var(--text1,#fff);margin:0 0 4px;">' + (c.problema||'') + '</p>' +
          '<p style="font-size:12px;color:#10b981;margin:0;">Resolucion: ' + (c.resolucion||'') + '</p></div>';
      }).join('');

  } else if (tabId === 'alerts') {
    var al = data.alertas || [];
    content.innerHTML = al.length === 0 ? '<p style="color:var(--text2,#aaa);">Sin alertas.</p>' :
      al.map(function(a) {
        return '<div style="background:var(--bg2,#1e1e2e);border-radius:8px;padding:10px 12px;margin-bottom:6px;font-size:12px;color:var(--text2,#aaa);">' + a + '</div>';
      }).join('');

  } else if (tabId === 'gov-alerts') {
    var ga = data.alertasGob || [];
    content.innerHTML = ga.length === 0 ? '<p style="color:var(--text2,#aaa);">Sin alertas para gobernadores.</p>' :
      ga.map(function(a) {
        var destColor = a.destino === 'gov-run' ? '#ef4444' : '#06b6d4';
        var destLabel = a.destino === 'gov-run' ? 'GOB. RUN' : 'GOB. BUILD';
        var sevColor = a.severity === 'HIGH' ? '#ef4444' : a.severity === 'CRITICAL' ? '#ef4444' : '#f59e0b';
        return '<div style="background:var(--bg2,#1e1e2e);border-radius:8px;padding:10px 12px;margin-bottom:8px;border-left:3px solid ' + destColor + ';">' +
          '<div style="display:flex;gap:8px;align-items:center;margin-bottom:4px;">' +
            '<span style="background:rgba(124,58,237,0.15);color:#7c3aed;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;">' + destLabel + '</span>' +
            '<span style="color:' + sevColor + ';font-size:11px;font-weight:600;">' + (a.severity||'') + '</span>' +
            '<span style="color:var(--text2,#aaa);font-size:11px;">' + (a.alert_type||'').replace(/_/g,' ') + '</span></div>' +
          '<p style="font-size:12px;font-weight:600;color:var(--text1,#fff);margin:0 0 2px;">' + (a.title||'') + '</p>' +
          '<p style="font-size:11px;color:var(--text2,#aaa);margin:0;">' + (a.description||'') + '</p></div>';
      }).join('');
  }
}

// ── Aprobar / Rechazar ──
async function aprobarPropuestaCAB() {
  if (!cabCurrentPropuestaId) return;
  if (!confirm('Aprobar propuesta y crear ventanas CAB?')) return;
  try {
    var r = await fetch('/cab/propuestas/' + cabCurrentPropuestaId + '/aprobar', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + TK},
      body: JSON.stringify({revisado_por: 'coordinador_build', notas: 'Aprobado desde panel gobernador'})
    });
    var data = JSON.parse(await r.text());
    alert('Propuesta aprobada. ' + (data.ventanas_insertadas || 0) + ' ventanas CAB creadas.');
    loadCABPropuestas();
    cargarPropuestaCAB(cabCurrentPropuestaId);
  } catch(e) { alert('Error al aprobar: ' + e.message); }
}

async function rechazarPropuestaCAB() {
  if (!cabCurrentPropuestaId) return;
  var motivo = prompt('Motivo del rechazo:');
  if (!motivo) return;
  try {
    await fetch('/cab/propuestas/' + cabCurrentPropuestaId + '/rechazar', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + TK},
      body: JSON.stringify({revisado_por: 'coordinador_build', motivo_rechazo: motivo})
    });
    alert('Propuesta rechazada.');
    loadCABPropuestas();
    cargarPropuestaCAB(cabCurrentPropuestaId);
  } catch(e) { alert('Error: ' + e.message); }
}

// ── Alertas CAB en el dashboard BUILD (banner) ──
async function loadCABBuildAlerts() {
  try {
    var alerts = await af('/cab/alertas');
    if (!Array.isArray(alerts) || alerts.length === 0) return;
    var buildAlerts = alerts.filter(function(a) {
      return a.alert_type === 'CAB_SPRINT_OVERLAP' || a.alert_type === 'CAB_PROPOSAL_READY' || a.alert_type === 'CAB_WINDOW_CONFLICT';
    });
    if (buildAlerts.length === 0) return;
    var container = document.getElementById('cab-alerts-build');
    if (!container) {
      container = document.createElement('div');
      container.id = 'cab-alerts-build';
      container.style.cssText = 'margin-bottom:12px;';
      var main = document.querySelector('.main-content') || document.querySelector('.content') || document.body.firstElementChild;
      if (main) main.prepend(container);
    }
    container.innerHTML = buildAlerts.map(function(a) {
      var color = a.severity === 'CRITICAL' || a.severity === 'HIGH' ? '#f59e0b' : '#06b6d4';
      return '<div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);border-radius:8px;padding:10px 14px;margin-bottom:6px;font-size:12px;cursor:pointer;" onclick="showGovTab(\'cab\')">' +
        '<strong style="color:' + color + ';">🔔 ' + (a.alert_type||'').replace(/_/g,' ') + '</strong> — ' +
        '<span style="color:var(--text1,#fff);">' + (a.title||'') + '</span>' +
        '<span style="float:right;font-size:11px;color:' + color + ';opacity:0.8;"> → Calendario CAB</span></div>';
    }).join('');
  } catch(e) { /* silent */ }
}

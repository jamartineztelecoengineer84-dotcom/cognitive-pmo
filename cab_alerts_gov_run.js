// ═══════════════════════════════════════════════════════════════════
// JAVASCRIPT: Alertas CAB para gov-run.html
// INSERTAR: dentro del bloque <script> de gov-run.html
// LLAMAR: loadCABRunAlerts() en el init/DOMContentLoaded
// ═══════════════════════════════════════════════════════════════════

async function loadCABRunAlerts() {
  try {
    var alerts = await af('/cab/alertas');
    if (!Array.isArray(alerts) || alerts.length === 0) return;
    var runAlerts = alerts.filter(function(a) {
      return a.alert_type === 'CAB_INCIDENT_BLOCKS_CHANGE' || a.alert_type === 'CAB_WINDOW_EXPIRED';
    });
    if (runAlerts.length === 0) return;
    var container = document.getElementById('cab-alerts-run');
    if (!container) {
      container = document.createElement('div');
      container.id = 'cab-alerts-run';
      container.style.cssText = 'margin-bottom:12px;';
      var main = document.querySelector('.main-content') || document.querySelector('.content') || document.body.firstElementChild;
      if (main) main.prepend(container);
    }
    container.innerHTML = '<div style="margin-bottom:6px;font-size:12px;font-weight:600;color:#f59e0b;">🔔 Alertas CAB activas</div>' +
      runAlerts.map(function(a) {
        var sevColor = a.severity === 'CRITICAL' ? '#ef4444' : a.severity === 'HIGH' ? '#f59e0b' : '#06b6d4';
        var sevBg = a.severity === 'CRITICAL' ? 'rgba(239,68,68,0.1)' : a.severity === 'HIGH' ? 'rgba(245,158,11,0.1)' : 'rgba(6,182,212,0.1)';
        var entities = a.affected_entities || {};
        var entityText = '';
        if (entities.activo) entityText += 'Activo: ' + entities.activo + ' ';
        if (entities.incidencia) entityText += '| Inc: ' + entities.incidencia;
        return '<div style="background:' + sevBg + ';border:1px solid rgba(245,158,11,0.25);border-radius:8px;padding:10px 14px;margin-bottom:6px;font-size:12px;">' +
          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">' +
            '<strong style="color:' + sevColor + ';">' + (a.alert_type||'').replace(/_/g,' ') + '</strong>' +
            '<span style="font-size:10px;color:var(--text2,#aaa);">' + (a.created_at||'').substring(0,16).replace('T',' ') + '</span></div>' +
          '<div style="color:var(--text1,#fff);margin-bottom:2px;">' + (a.title||'') + '</div>' +
          (entityText ? '<div style="color:var(--text2,#aaa);font-size:11px;">' + entityText + '</div>' : '') +
        '</div>';
      }).join('');
  } catch(e) { console.error('Error CAB run alerts:', e); }
}

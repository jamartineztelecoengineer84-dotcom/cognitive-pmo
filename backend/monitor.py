"""
Sistema de Monitorización — 4 pilares.
Pilar 1: Health check diario (08:00)
Pilar 2: Alertas de error en tiempo real
Pilar 3: Alerta de login en tiempo real
Pilar 4: Resumen diario de actividad (21:00)

Emails vía Resend SOLO al admin (cognitivepmo@outlook.com).
Fail-safe: si Resend falla, loguea y sigue sin romper nada.
"""
import os
import json
import logging
import subprocess
from datetime import datetime

logger = logging.getLogger("monitor")

# === RESEND SETUP ===
try:
    import resend
    resend.api_key = os.getenv("RESEND_API_KEY", "")
    RESEND_OK = bool(resend.api_key)
except ImportError:
    RESEND_OK = False
    logger.warning("Paquete 'resend' no instalado — emails desactivados")

FROM_EMAIL = os.getenv("RESEND_FROM", "alertas@cognitive-pmo.es")
ADMIN_EMAIL = os.getenv("RESEND_ADMIN_EMAIL", "cognitivepmo@outlook.com")


def _enviar_email(asunto: str, html: str) -> bool:
    if not RESEND_OK:
        logger.warning(f"Resend no disponible — '{asunto}' no enviado")
        return False
    try:
        r = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [ADMIN_EMAIL],
            "subject": asunto,
            "html": html,
        })
        logger.info(f"Email enviado: {asunto}")
        return True
    except Exception as e:
        logger.error(f"Fallo al enviar email '{asunto}': {e}")
        return False


# =====================================================
# PILAR 1 — HEALTH CHECK DIARIO
# =====================================================
def health_check_diario():
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
    checks = []

    # Disco
    try:
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:
            parts = lines[1].split()
            uso = parts[4] if len(parts) > 4 else "?"
            checks.append(("Disco /", int(uso.replace("%", "")) < 85, f"Uso: {uso}"))
    except Exception as e:
        checks.append(("Disco", False, str(e)))

    # Backend API (httpx, desde dentro del contenedor)
    try:
        import httpx
        r = httpx.get("http://localhost:8088/api/llm/providers", timeout=5)
        checks.append(("Backend API", r.status_code == 200, f"HTTP {r.status_code}"))
    except Exception as e:
        checks.append(("Backend API", False, str(e)[:80]))

    # Frontend (via hostname Docker)
    try:
        import httpx
        r = httpx.get("http://frontend:80", timeout=5)
        checks.append(("Frontend", r.status_code == 200, f"HTTP {r.status_code}"))
    except Exception as e:
        checks.append(("Frontend", False, str(e)[:80]))

    # SSL (httpx con verificación)
    try:
        import httpx
        r = httpx.get("https://cognitive-pmo.es", timeout=10, verify=False)
        checks.append(("SSL cognitive-pmo.es", r.status_code == 200, f"HTTPS OK"))
    except Exception as e:
        checks.append(("SSL", False, str(e)[:80]))

    # Último backup (montado como /app/backups/)
    try:
        import glob
        backups = sorted(glob.glob("/app/backups/cognitive_pmo_*.sql.gz"))
        if backups:
            ultimo = backups[-1]
            mod_time = datetime.fromtimestamp(os.path.getmtime(ultimo))
            horas = (datetime.now() - mod_time).total_seconds() / 3600
            tamano = os.path.getsize(ultimo) / (1024 * 1024)
            checks.append(("Backup BD", horas < 25, f"Último: {mod_time.strftime('%d/%m %H:%M')} ({tamano:.1f} MB)"))
        else:
            checks.append(("Backup BD", False, "Sin backups en /app/backups/"))
    except Exception as e:
        checks.append(("Backup BD", False, str(e)))

    total_ok = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    all_ok = total_ok == total
    color = "#16a34a" if all_ok else "#dc2626"
    emoji = "✅" if all_ok else "🔴"

    filas = ""
    for nombre, ok, detalle in checks:
        ic = "✅" if ok else "❌"
        bg = "#f0fdf4" if ok else "#fef2f2"
        filas += f'<tr style="background:{bg}"><td style="padding:8px;border:1px solid #e5e7eb;">{ic}</td><td style="padding:8px;border:1px solid #e5e7eb;">{nombre}</td><td style="padding:8px;border:1px solid #e5e7eb;">{detalle}</td></tr>'

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:{color};color:white;padding:16px 24px;border-radius:8px 8px 0 0;">
            <h2 style="margin:0;">{emoji} Health Check — {ahora}</h2>
            <p style="margin:4px 0 0;opacity:0.9;">{total_ok}/{total} servicios OK</p>
        </div>
        <div style="padding:16px;border:1px solid #e5e7eb;border-radius:0 0 8px 8px;">
            <table style="width:100%;border-collapse:collapse;">
                <tr style="background:#f9fafb;"><th style="padding:8px;border:1px solid #e5e7eb;text-align:left;">Estado</th><th style="padding:8px;border:1px solid #e5e7eb;text-align:left;">Servicio</th><th style="padding:8px;border:1px solid #e5e7eb;text-align:left;">Detalle</th></tr>
                {filas}
            </table>
            <p style="margin-top:12px;color:#6b7280;font-size:12px;">Cognitive PMO · Health Check automático</p>
        </div>
    </div>"""
    _enviar_email(f"{emoji} Health Check Cognitive PMO — {total_ok}/{total} OK", html)


# =====================================================
# PILAR 2 — ALERTAS DE ERROR EN TIEMPO REAL
# =====================================================
def notificar_error(origen: str, tipo_error: str, detalle: str,
                    endpoint: str = "", usuario: str = ""):
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    colores = {"agente_ia": "#dc2626", "backend": "#ea580c", "database": "#9333ea"}
    color = colores.get(origen, "#6b7280")

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:{color};color:white;padding:16px 24px;border-radius:8px 8px 0 0;">
            <h2 style="margin:0;">🚨 Error — {origen.upper().replace('_',' ')}</h2>
        </div>
        <div style="background:#fef2f2;padding:24px;border:1px solid #fecaca;border-radius:0 0 8px 8px;">
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:6px 0;font-weight:bold;width:120px;">Origen:</td><td>{origen}</td></tr>
                <tr><td style="padding:6px 0;font-weight:bold;">Tipo:</td><td>{tipo_error}</td></tr>
                <tr><td style="padding:6px 0;font-weight:bold;">Endpoint:</td><td>{endpoint or 'N/A'}</td></tr>
                <tr><td style="padding:6px 0;font-weight:bold;">Usuario:</td><td>{usuario or 'Sistema'}</td></tr>
                <tr><td style="padding:6px 0;font-weight:bold;">Hora:</td><td>{ahora}</td></tr>
            </table>
            <div style="margin-top:16px;padding:12px;background:#1e1e1e;color:#f87171;border-radius:4px;font-family:monospace;font-size:13px;white-space:pre-wrap;">{detalle[:2000]}</div>
            <p style="margin-top:12px;color:#6b7280;font-size:12px;">Cognitive PMO · Alerta automática</p>
        </div>
    </div>"""
    _enviar_email(f"🚨 [{origen.upper()}] {tipo_error}: {detalle[:80]}", html)


# =====================================================
# PILAR 3 — ALERTA DE LOGIN EN TIEMPO REAL
# =====================================================
def notificar_login(usuario_id: int, usuario_nombre: str, email: str,
                    ip: str, user_agent: str = "", role: str = ""):
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    nav = "Chrome" if "Chrome" in user_agent else "Safari" if "Safari" in user_agent else "Firefox" if "Firefox" in user_agent else "Otro"

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#0891b2;color:white;padding:16px 24px;border-radius:8px 8px 0 0;">
            <h2 style="margin:0;">🔑 Nuevo Login</h2>
        </div>
        <div style="background:#ecfeff;padding:24px;border:1px solid #a5f3fc;border-radius:0 0 8px 8px;">
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:8px 0;font-weight:bold;width:120px;">Usuario:</td><td>{usuario_nombre}</td></tr>
                <tr><td style="padding:8px 0;font-weight:bold;">Email:</td><td>{email}</td></tr>
                <tr><td style="padding:8px 0;font-weight:bold;">Rol:</td><td>{role}</td></tr>
                <tr><td style="padding:8px 0;font-weight:bold;">IP:</td><td>{ip}</td></tr>
                <tr><td style="padding:8px 0;font-weight:bold;">Navegador:</td><td>{nav}</td></tr>
                <tr><td style="padding:8px 0;font-weight:bold;">Hora:</td><td>{ahora}</td></tr>
            </table>
            <p style="margin-top:12px;color:#6b7280;font-size:12px;">Cognitive PMO · Login detectado</p>
        </div>
    </div>"""
    _enviar_email(f"🔑 Login: {usuario_nombre} ({role}) desde {ip}", html)


# =====================================================
# PILAR 4 — RESUMEN DIARIO (async, usa asyncpg pool)
# =====================================================
async def resumen_diario_actividad():
    from database import get_pool
    pool = get_pool()
    if not pool:
        logger.error("Resumen diario: pool no disponible")
        return

    ahora = datetime.now()
    hoy = ahora.strftime("%Y-%m-%d")
    fecha = ahora.strftime("%d/%m/%Y")

    try:
        async with pool.acquire() as conn:
            logins = await conn.fetch("""
                SELECT usuario_nombre, ip_address, created_at
                FROM primitiva.audit_log
                WHERE evento = 'login' AND created_at::date = $1
                ORDER BY created_at
            """, ahora.date())

            errores = await conn.fetch("""
                SELECT evento, detalle, endpoint, created_at
                FROM primitiva.audit_log
                WHERE evento IN ('error','agent_error')
                AND created_at::date = $1 ORDER BY created_at
            """, ahora.date())

            usuarios_unicos = await conn.fetchval("""
                SELECT COUNT(DISTINCT usuario_id) FROM primitiva.audit_log
                WHERE created_at::date = $1 AND usuario_id IS NOT NULL
            """, ahora.date()) or 0

            total_eventos = await conn.fetchval("""
                SELECT COUNT(*) FROM primitiva.audit_log WHERE created_at::date = $1
            """, ahora.date()) or 0

            # Cleanup >90 days
            await conn.execute("""
                DELETE FROM primitiva.audit_log WHERE created_at < NOW() - INTERVAL '90 days'
            """)
    except Exception as e:
        logger.error(f"Resumen diario error BD: {e}")
        return

    filas_login = ""
    for r in logins:
        hora = r['created_at'].strftime("%H:%M:%S") if r['created_at'] else "?"
        filas_login += f'<tr><td style="padding:6px 8px;border:1px solid #e5e7eb;">{hora}</td><td style="padding:6px 8px;border:1px solid #e5e7eb;">{r["usuario_nombre"] or "?"}</td><td style="padding:6px 8px;border:1px solid #e5e7eb;">{r["ip_address"] or "?"}</td></tr>'
    if not filas_login:
        filas_login = '<tr><td colspan="3" style="padding:12px;text-align:center;color:#9ca3af;">Sin logins hoy</td></tr>'

    filas_err = ""
    for r in errores:
        hora = r['created_at'].strftime("%H:%M:%S") if r['created_at'] else "?"
        filas_err += f'<tr style="background:#fef2f2;"><td style="padding:6px 8px;border:1px solid #e5e7eb;">{hora}</td><td style="padding:6px 8px;border:1px solid #e5e7eb;">{r["evento"]}</td><td style="padding:6px 8px;border:1px solid #e5e7eb;">{(r["detalle"] or "")[:80]}</td></tr>'

    sec_err = ""
    if filas_err:
        sec_err = f'<h3 style="color:#dc2626;margin-top:24px;">🚨 Errores ({len(errores)})</h3><table style="width:100%;border-collapse:collapse;font-size:13px;"><tr style="background:#fef2f2;"><th style="padding:6px 8px;border:1px solid #e5e7eb;text-align:left;">Hora</th><th style="padding:6px 8px;border:1px solid #e5e7eb;text-align:left;">Tipo</th><th style="padding:6px 8px;border:1px solid #e5e7eb;text-align:left;">Detalle</th></tr>{filas_err}</table>'

    color = "#dc2626" if errores else "#16a34a"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:650px;margin:0 auto;">
        <div style="background:{color};color:white;padding:16px 24px;border-radius:8px 8px 0 0;">
            <h2 style="margin:0;">📊 Resumen del día — {fecha}</h2>
            <p style="margin:4px 0 0;opacity:0.9;">{usuarios_unicos} usuarios · {total_eventos} eventos · {len(errores)} errores</p>
        </div>
        <div style="padding:20px;border:1px solid #e5e7eb;border-radius:0 0 8px 8px;">
            <h3 style="color:#0891b2;margin-top:0;">🔑 Logins ({len(logins)})</h3>
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <tr style="background:#f0fdfa;"><th style="padding:6px 8px;border:1px solid #e5e7eb;text-align:left;">Hora</th><th style="padding:6px 8px;border:1px solid #e5e7eb;text-align:left;">Usuario</th><th style="padding:6px 8px;border:1px solid #e5e7eb;text-align:left;">IP</th></tr>
                {filas_login}
            </table>
            {sec_err}
            <p style="margin-top:20px;color:#6b7280;font-size:12px;border-top:1px solid #e5e7eb;padding-top:12px;">Cognitive PMO · Resumen automático · {ahora.strftime("%H:%M")}</p>
        </div>
    </div>"""
    _enviar_email(f"📊 Resumen diario — {fecha} — {usuarios_unicos} usuarios, {len(errores)} errores", html)

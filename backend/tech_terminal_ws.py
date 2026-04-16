"""
COGNITIVE PMO — Tech Terminal WebSocket
SSH proxy simulado con auditoría completa en tech_terminal_log.
Protocolo: 1) JWT token → 2) {servidor, vinculado_tipo, vinculado_id} → 3) bidireccional
"""

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional

from database import get_pool
from auth import decode_jwt, get_current_user, UserInfo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tech Terminal"])

# Active sessions tracking (rate limit: max 3 per technician)
_active_sessions = {}  # id_recurso -> [session_ids]

INACTIVITY_TIMEOUT = 30 * 60  # 30 minutes

# Simulated server responses (production: replace with asyncssh)
SIMULATED_FS = {
    "/": "backup/  config/  data/  logs/  scripts/  tmp/",
    "/backup": "daily/  weekly/  monthly/  retention.conf",
    "/config": "postgresql.conf  pg_hba.conf  recovery.conf  watchdog.conf",
    "/data": "base/  global/  pg_wal/  pg_xlog/  postmaster.pid",
    "/logs": "postgresql-15-main.log  pg_audit.log  watchdog.log  failover.log",
    "/scripts": "backup.sh  rotate_logs.sh  health_check.sh  failover.sh",
}


def _simulate_command(cmd: str, servidor: str, hostname: str) -> str:
    """Simulate SSH command output for demo environment."""
    cmd_lower = cmd.strip().lower()

    if cmd_lower == "whoami":
        return "tecnico"
    elif cmd_lower == "hostname":
        return hostname
    elif cmd_lower == "date":
        return datetime.now().strftime("%a %b %d %H:%M:%S CET %Y")
    elif cmd_lower == "uptime":
        return f" {datetime.now().strftime('%H:%M:%S')} up 45 days, 12:20,  3 users,  load average: 0.42, 0.38, 0.35"
    elif cmd_lower.startswith("ping"):
        target = cmd.split()[-1] if len(cmd.split()) > 1 else "localhost"
        return f"PING {target} ({target}) 56(84) bytes of data.\n64 bytes from {target}: icmp_seq=1 ttl=64 time=0.432 ms\n64 bytes from {target}: icmp_seq=2 ttl=64 time=0.389 ms\n\n--- {target} ping statistics ---\n2 packets transmitted, 2 received, 0% packet loss, time 1001ms"
    elif cmd_lower == "df -h":
        return "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       100G   62G   38G  62% /\n/dev/sdb1       500G  312G  188G  63% /data\ntmpfs           8.0G  1.2G  6.8G  15% /dev/shm"
    elif cmd_lower == "free -h":
        return "              total        used        free      shared  buff/cache   available\nMem:           31Gi       8.2Gi       4.1Gi       1.2Gi        19Gi        21Gi\nSwap:         8.0Gi          0B       8.0Gi"
    elif cmd_lower.startswith("systemctl status"):
        svc = cmd.split()[-1] if len(cmd.split()) > 2 else "postgresql"
        return f"● {svc}.service - {svc} service\n     Loaded: loaded (/lib/systemd/system/{svc}.service; enabled)\n     Active: active (running) since Mon {datetime.now().strftime('%Y-%m-%d')} 08:15:22 CET\n   Main PID: 1234 ({svc})\n      Tasks: 12 (limit: 4915)\n     Memory: 256.4M\n        CPU: 45.231s"
    elif "pg_stat_activity" in cmd_lower:
        return " pid  | state  | query                    | wait_event | client_addr\n------+--------+--------------------------+------------+-------------\n 1256 | active | SELECT * FROM transact.. | NULL       | 10.0.2.10\n 1257 | idle   | NULL                     | ClientRead | 10.0.2.10\n 1260 | active | INSERT INTO audit_log..  | NULL       | 10.0.1.55\n 1289 | idle   | NULL                     | ClientRead | 10.0.3.20\n(4 rows)"
    elif cmd_lower.startswith("ls"):
        path = cmd.split()[-1] if len(cmd.split()) > 1 and not cmd.split()[-1].startswith("-") else "/"
        if "-la" in cmd_lower or "-l" in cmd_lower:
            return f"total 48\ndrwxr-xr-x  8 postgres postgres 4096 {datetime.now().strftime('%b %d %H:%M')} .\ndrwxr-xr-x  3 root     root     4096 Feb 20 10:00 ..\ndrwxr-xr-x  2 postgres postgres 4096 Apr  5 03:00 backup\ndrwxr-xr-x  2 postgres postgres 4096 Apr  1 12:00 config\ndrwxr-xr-x 14 postgres postgres 4096 {datetime.now().strftime('%b %d %H:%M')} data\ndrwxr-xr-x  2 postgres postgres 4096 {datetime.now().strftime('%b %d %H:%M')} logs\ndrwxr-xr-x  2 postgres postgres 4096 Mar 25 09:00 scripts"
        return SIMULATED_FS.get(path, SIMULATED_FS.get("/", ""))
    elif cmd_lower.startswith("cat") and "log" in cmd_lower:
        return f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CET [1234-1] LOG:  checkpoint starting: time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CET [1234-2] LOG:  checkpoint complete\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CET [1256-1] WARNING:  connection pool reaching 80%"
    elif cmd_lower == "clear":
        return "\033[2J\033[H"
    elif cmd_lower == "exit" or cmd_lower == "logout":
        return "logout\nConnection to " + servidor + " closed."
    elif cmd_lower == "id":
        return "uid=1001(tecnico) gid=1001(tecnico) groups=1001(tecnico),27(sudo),999(docker)"
    elif cmd_lower.startswith("show") or cmd_lower.startswith("select"):
        return " server_version\n----------------\n 15.6\n(1 row)"
    elif cmd_lower == "pwd":
        return "/home/tecnico"
    elif cmd_lower == "w":
        return f"  {datetime.now().strftime('%H:%M:%S')} up 45 days,  3 users,  load average: 0.42, 0.38, 0.35\nUSER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT\ntecnico  pts/0    10.0.1.100       {datetime.now().strftime('%H:%M')}    0.00s  0.01s  0.00s w"
    elif cmd_lower == "help":
        return "Comandos disponibles: ls, cd, cat, pwd, whoami, hostname, date, uptime, df, free,\n                     ping, systemctl, id, w, clear, exit\nComandos PostgreSQL: psql, pg_stat_activity, show"
    else:
        return f"bash: {cmd.split()[0]}: command simulated\nTip: escribe 'help' para ver comandos disponibles"


@router.websocket("/ws/tech/terminal")
async def terminal_websocket(ws: WebSocket):
    await ws.accept()
    id_recurso = None
    sesion_id = str(uuid.uuid4())
    servidor = None
    hostname = None
    vinculado_tipo = None
    vinculado_id = None
    last_activity = asyncio.get_event_loop().time()
    pool = get_pool()

    try:
        # Step 1: Authenticate (first message = JWT)
        token = await asyncio.wait_for(ws.receive_text(), timeout=10)
        claims = decode_jwt(token)
        if not claims:
            await ws.send_text("\r\n\033[31mError: Token inválido o expirado\033[0m\r\n")
            await ws.close(1008)
            return

        # Get id_recurso
        if pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT id_recurso FROM rbac_usuarios WHERE id_usuario = $1",
                    claims.get("sub"))
                if not row or not row["id_recurso"]:
                    await ws.send_text("\r\n\033[31mError: Usuario sin recurso técnico vinculado\033[0m\r\n")
                    await ws.close(1008)
                    return
                id_recurso = row["id_recurso"]

        # Rate limit: max 3 sessions
        if id_recurso in _active_sessions and len(_active_sessions[id_recurso]) >= 3:
            await ws.send_text("\r\n\033[31mError: Máximo 3 sesiones simultáneas\033[0m\r\n")
            await ws.close(1008)
            return

        _active_sessions.setdefault(id_recurso, []).append(sesion_id)

        # Step 2: Server info (second message = JSON)
        config_raw = await asyncio.wait_for(ws.receive_text(), timeout=10)
        config = json.loads(config_raw)
        servidor = config.get("servidor", "")
        vinculado_tipo = config.get("vinculado_tipo")
        vinculado_id = config.get("vinculado_id")

        # Validate server in whitelist (CMDB activos with tipo servidor)
        if pool:
            async with pool.acquire() as conn:
                srv = await conn.fetchrow("""
                    SELECT a.codigo, a.nombre, i.direccion_ip, i.hostname
                    FROM cmdb_activos a
                    JOIN cmdb_ips i ON a.id_activo = i.id_activo
                    WHERE a.codigo = $1
                      AND (a.tipo ILIKE '%servidor%' OR a.tipo ILIKE '%vm%')
                """, servidor)
                if not srv:
                    await ws.send_text(f"\r\n\033[31mError: Servidor {servidor} no autorizado o no encontrado en CMDB\033[0m\r\n")
                    await ws.close(1008)
                    return
                hostname = srv["hostname"] or servidor

        # Connected!
        ip_display = srv["direccion_ip"] if srv else "0.0.0.0"
        await ws.send_text(
            f"\033[32m✓ Conexión SSH establecida\033[0m\r\n"
            f"\033[33m⚠ Sesión vinculada a: {vinculado_tipo or 'libre'} {vinculado_id or ''}\033[0m\r\n"
            f"\033[90mSesión: {sesion_id[:8]}... | Todos los comandos serán auditados\033[0m\r\n\r\n"
        )
        await ws.send_text(f"tecnico@{hostname}:~$ ")

        # Step 3: Interactive loop
        cmd_buffer = ""
        while True:
            try:
                data = await asyncio.wait_for(
                    ws.receive_text(),
                    timeout=INACTIVITY_TIMEOUT
                )
                last_activity = asyncio.get_event_loop().time()
            except asyncio.TimeoutError:
                await ws.send_text("\r\n\033[33mSesión cerrada por inactividad (30 min)\033[0m\r\n")
                break

            for char in data:
                if char == "\r" or char == "\n":
                    # Execute command
                    cmd = cmd_buffer.strip()
                    cmd_buffer = ""
                    await ws.send_text("\r\n")

                    if not cmd:
                        await ws.send_text(f"tecnico@{hostname}:~$ ")
                        continue

                    if cmd.lower() in ("exit", "logout"):
                        output = _simulate_command(cmd, servidor, hostname)
                        await ws.send_text(output + "\r\n")
                        # Log it
                        if pool:
                            async with pool.acquire() as conn:
                                await conn.execute("""
                                    INSERT INTO tech_terminal_log
                                    (id_recurso, sesion_id, servidor, comando, salida, vinculado_tipo, vinculado_id)
                                    VALUES ($1, $2::uuid, $3, $4, $5, $6, $7)
                                """, id_recurso, sesion_id, servidor, cmd, output[:4096],
                                    vinculado_tipo, vinculado_id)
                        return

                    # Simulate output
                    output = _simulate_command(cmd, servidor, hostname)
                    await ws.send_text(output + "\r\n")
                    await ws.send_text(f"tecnico@{hostname}:~$ ")

                    # Log to DB
                    if pool:
                        try:
                            async with pool.acquire() as conn:
                                await conn.execute("""
                                    INSERT INTO tech_terminal_log
                                    (id_recurso, sesion_id, servidor, comando, salida, vinculado_tipo, vinculado_id)
                                    VALUES ($1, $2::uuid, $3, $4, $5, $6, $7)
                                """, id_recurso, sesion_id, servidor, cmd, output[:4096],
                                    vinculado_tipo, vinculado_id)
                        except Exception as e:
                            logger.warning(f"Error logging terminal command: {e}")

                elif char == "\x7f" or char == "\b":
                    # Backspace
                    if cmd_buffer:
                        cmd_buffer = cmd_buffer[:-1]
                        await ws.send_text("\b \b")
                elif char == "\x03":
                    # Ctrl+C
                    cmd_buffer = ""
                    await ws.send_text("^C\r\n")
                    await ws.send_text(f"tecnico@{hostname}:~$ ")
                elif char == "\t":
                    # Tab completion (basic)
                    pass
                else:
                    cmd_buffer += char
                    await ws.send_text(char)

    except WebSocketDisconnect:
        logger.info(f"Terminal disconnected: {id_recurso} @ {servidor}")
    except Exception as e:
        logger.error(f"Terminal error: {e}")
        try:
            await ws.send_text(f"\r\n\033[31mError: {str(e)}\033[0m\r\n")
        except Exception:
            pass
    finally:
        # Cleanup active session
        if id_recurso and id_recurso in _active_sessions:
            if sesion_id in _active_sessions[id_recurso]:
                _active_sessions[id_recurso].remove(sesion_id)
            if not _active_sessions[id_recurso]:
                del _active_sessions[id_recurso]
        try:
            await ws.close()
        except Exception:
            pass

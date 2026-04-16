"""
Tech Dashboard API — Cognitive PMO v5.1
Endpoints para el dashboard de técnicos.
Tablas: tech_chat_salas, tech_chat_mensajes, tech_terminal_log, tech_valoracion_mensual, tech_adjuntos
Requiere: JWT con id_recurso vinculado en rbac_usuarios
Fases: F0 tablas, F1 endpoints, F2 frontend, F3 pipelines, F4 chat, F5 terminal, F6 copiloto, F7 valoración, F8 testing
"""

import os
import uuid
import logging
from datetime import datetime, date
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from pydantic import BaseModel

from database import get_pool
from auth import get_current_user, UserInfo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tech", tags=["Tech Dashboard"])

UPLOAD_DIR = "/app/uploads/tech"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'.doc', '.docx', '.xlsx', '.xls', '.pdf', '.png', '.jpg', '.jpeg',
                      '.txt', '.py', '.sql', '.sh', '.log', '.csv', '.json', '.yaml', '.yml', '.md'}
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB


def _validate_upload(file: UploadFile, content: bytes):
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Tipo de archivo no permitido: {ext}")
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"Archivo demasiado grande (máx {MAX_UPLOAD_SIZE // 1048576}MB)")


# ── Helpers ──────────────────────────────────────────────────────────────

async def _get_id_recurso(user: UserInfo) -> str:
    """Get id_recurso from rbac_usuarios for the current user."""
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id_recurso FROM rbac_usuarios WHERE id_usuario = $1",
            user.id_usuario,
        )
    if not row or not row["id_recurso"]:
        raise HTTPException(status_code=403, detail="Usuario sin recurso técnico vinculado")
    return row["id_recurso"]


def _require_auth(user: Optional[UserInfo]) -> UserInfo:
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return user


# ── F4b: GET /api/tech/me ── identidad del técnico autenticado ───────────

@router.get("/me")
async def tech_me(user: Optional[UserInfo] = Depends(get_current_user)):
    """Devuelve {fte_id, nombre, email, silo, nivel, skill_principal, rol, activo}.
    404 si no es TECH_SENIOR/TECH_JUNIOR activo o carece de id_recurso."""
    if user is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    if user.role_code not in ("TECH_SENIOR", "TECH_JUNIOR"):
        raise HTTPException(status_code=404, detail="Usuario no es técnico")
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT u.id_recurso, u.nombre_completo, u.email,
                   ps.silo_especialidad, ps.nivel, ps.skill_principal
            FROM rbac_usuarios u
            LEFT JOIN pmo_staff_skills ps ON ps.id_recurso = u.id_recurso
            WHERE u.id_usuario = $1 AND u.activo = TRUE
        """, user.id_usuario)
    if not row or not row["id_recurso"]:
        raise HTTPException(status_code=404, detail="Técnico sin id_recurso (FTE-XXX)")
    return {
        "fte_id": row["id_recurso"],
        "nombre": row["nombre_completo"],
        "email": user.email,
        "silo": row["silo_especialidad"],
        "nivel": row["nivel"],
        "skill_principal": row["skill_principal"],
        "rol": user.role_code,
        "activo": True,
    }


# ── ENDPOINT 1: GET /api/tech/dashboard ──────────────────────────────────

@router.get("/dashboard")
async def tech_dashboard(user: Optional[UserInfo] = Depends(get_current_user)):
    """Resumen 'Mi Día': incidencias abiertas, tareas sprint, SLA, carga."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        # Incidencias abiertas por prioridad
        inc_rows = await conn.fetch("""
            SELECT prioridad_ia, COUNT(*) as total
            FROM incidencias_run
            WHERE tecnico_asignado = $1
              AND estado NOT IN ('RESUELTO', 'CERRADO')
            GROUP BY prioridad_ia
        """, id_recurso)

        inc_by_prio = {r["prioridad_ia"]: r["total"] for r in inc_rows}
        total_inc = sum(inc_by_prio.values())

        # Tareas kanban activas (BUILD)
        tareas_activas = await conn.fetchval("""
            SELECT COUNT(*)
            FROM kanban_tareas
            WHERE id_tecnico = $1
              AND tipo = 'BUILD'
              AND columna NOT IN ('Completado')
        """, id_recurso)

        # Valoración mensual actual
        hoy = date.today()
        primer_dia_mes = hoy.replace(day=1)
        valoracion = await conn.fetchrow("""
            SELECT pct_sla, puntuacion, total_incidencias, incidencias_en_sla
            FROM tech_valoracion_mensual
            WHERE id_recurso = $1 AND mes = $2
        """, id_recurso, primer_dia_mes)

        # Carga actual del recurso
        staff = await conn.fetchrow("""
            SELECT carga_actual, nombre, nivel, silo_especialidad
            FROM pmo_staff_skills
            WHERE id_recurso = $1
        """, id_recurso)

        carga_pct = round((staff["carga_actual"] / 40) * 100, 1) if staff and staff["carga_actual"] else 0

    return {
        "id_recurso": id_recurso,
        "nombre": staff["nombre"] if staff else None,
        "nivel": staff["nivel"] if staff else None,
        "silo": staff["silo_especialidad"] if staff else None,
        "incidencias": {
            "total_abiertas": total_inc,
            "por_prioridad": {
                "P1": inc_by_prio.get("P1", 0),
                "P2": inc_by_prio.get("P2", 0),
                "P3": inc_by_prio.get("P3", 0),
                "P4": inc_by_prio.get("P4", 0),
            },
        },
        "tareas_build_activas": tareas_activas,
        "sla": {
            "pct_sla": float(valoracion["pct_sla"]) if valoracion else None,
            "puntuacion": float(valoracion["puntuacion"]) if valoracion else None,
            "total_incidencias": valoracion["total_incidencias"] if valoracion else 0,
            "en_sla": valoracion["incidencias_en_sla"] if valoracion else 0,
        },
        "carga": {
            "horas_asignadas": staff["carga_actual"] if staff else 0,
            "capacidad_max": 40,
            "pct_ocupacion": carga_pct,
        },
    }


# ── ENDPOINT 2: GET /api/tech/incidencias ────────────────────────────────

@router.get("/incidencias")
async def list_incidencias(
    estado: Optional[str] = Query(None, description="Filtro estados separados por coma"),
    prioridad: Optional[str] = Query(None, description="Filtro prioridades separadas por coma"),
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Lista incidencias asignadas al técnico."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    query = """
        SELECT ticket_id, incidencia_detectada, prioridad_ia, estado,
               sla_limite, ci_afectado, timestamp_creacion, timestamp_asignacion,
               timestamp_resolucion, servicio_afectado, categoria
        FROM incidencias_run
        WHERE tecnico_asignado = $1
    """
    params = [id_recurso]
    idx = 2

    if estado:
        estados = [e.strip().upper() for e in estado.split(",")]
        placeholders = ", ".join(f"${idx + i}" for i in range(len(estados)))
        query += f" AND estado IN ({placeholders})"
        params.extend(estados)
        idx += len(estados)

    if prioridad:
        prios = [p.strip().upper() for p in prioridad.split(",")]
        placeholders = ", ".join(f"${idx + i}" for i in range(len(prios)))
        query += f" AND prioridad_ia IN ({placeholders})"
        params.extend(prios)

    query += " ORDER BY prioridad_ia ASC, timestamp_creacion ASC"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    now = datetime.now()
    results = []
    for r in rows:
        # Calcular SLA restante en horas
        sla_restante = None
        if r["sla_limite"] and r["timestamp_creacion"]:
            deadline = r["timestamp_creacion"] + __import__("datetime").timedelta(hours=float(r["sla_limite"]))
            sla_restante = round((deadline - now).total_seconds() / 3600, 1)

        results.append({
            "ticket_id": r["ticket_id"],
            "titulo": r["incidencia_detectada"][:120],
            "prioridad": r["prioridad_ia"],
            "estado": r["estado"],
            "sla_limite_horas": float(r["sla_limite"]) if r["sla_limite"] else None,
            "sla_restante_horas": sla_restante,
            "ci_afectado": r["ci_afectado"],
            "servicio": r["servicio_afectado"],
            "categoria": r["categoria"],
            "created_at": r["timestamp_creacion"].isoformat() if r["timestamp_creacion"] else None,
        })

    return results


# ── ENDPOINT 3: GET /api/tech/incidencias/{ticket_id} ────────────────────

@router.get("/incidencias/{ticket_id}")
async def get_incidencia_detail(
    ticket_id: str,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Detalle completo de una incidencia con contexto CMDB y tareas kanban."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        inc = await conn.fetchrow("""
            SELECT * FROM incidencias_run WHERE ticket_id = $1 AND tecnico_asignado = $2
        """, ticket_id, id_recurso)

        if not inc:
            raise HTTPException(status_code=404, detail="Incidencia no encontrada")

        # Contexto CMDB
        cmdb = None
        if inc["ci_afectado"]:
            cmdb = await conn.fetchrow("""
                SELECT id_activo, codigo, nombre, tipo, subtipo, criticidad,
                       entorno, ubicacion, responsable_tecnico, estado_ciclo
                FROM cmdb_activos
                WHERE nombre = $1 OR codigo = $1
                LIMIT 1
            """, inc["ci_afectado"])

        # IPs del CI
        cmdb_ips = []
        if cmdb:
            cmdb_ips = await conn.fetch("""
                SELECT ip, mascara, vlan_id, gateway, tipo
                FROM cmdb_ips WHERE id_activo = $1
            """, cmdb["id_activo"])

        # Tareas kanban vinculadas
        tareas = await conn.fetch("""
            SELECT id, titulo, columna, prioridad, horas_estimadas, horas_reales
            FROM kanban_tareas
            WHERE id_incidencia = $1
            ORDER BY fecha_creacion
        """, ticket_id)

        # SLA timer
        sla_info = None
        if inc["sla_limite"] and inc["timestamp_creacion"]:
            from datetime import timedelta
            deadline = inc["timestamp_creacion"] + timedelta(hours=float(inc["sla_limite"]))
            now = datetime.now()
            restante = (deadline - now).total_seconds() / 3600
            sla_info = {
                "limite_horas": float(inc["sla_limite"]),
                "deadline": deadline.isoformat(),
                "restante_horas": round(restante, 2),
                "en_sla": restante > 0,
                "pct_consumido": round(max(0, min(100, (1 - restante / float(inc["sla_limite"])) * 100)), 1),
            }

    return {
        "incidencia": dict(inc),
        "sla": sla_info,
        "cmdb": dict(cmdb) if cmdb else None,
        "cmdb_ips": [dict(ip) for ip in cmdb_ips],
        "tareas_kanban": [dict(t) for t in tareas],
    }


# ── ENDPOINT 4: PUT /api/tech/incidencias/{ticket_id}/estado ─────────────

class CambioEstadoIncidencia(BaseModel):
    estado: str
    pct_completado: Optional[int] = None
    nota: Optional[str] = None


TRANSICIONES_RUN = {
    "QUEUED": ["EN_CURSO"],
    "EN_CURSO": ["ESCALADO", "RESUELTO"],
    "ESCALADO": ["EN_CURSO"],
}


@router.put("/incidencias/{ticket_id}/estado")
async def cambiar_estado_incidencia(
    ticket_id: str,
    body: CambioEstadoIncidencia,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Cambiar estado de incidencia con validación de transiciones."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        inc = await conn.fetchrow(
            "SELECT estado FROM incidencias_run WHERE ticket_id = $1 AND tecnico_asignado = $2",
            ticket_id, id_recurso,
        )
        if not inc:
            raise HTTPException(status_code=404, detail="Incidencia no encontrada")

        estado_actual = inc["estado"]
        nuevo_estado = body.estado.upper()

        transiciones_validas = TRANSICIONES_RUN.get(estado_actual, [])
        if nuevo_estado not in transiciones_validas:
            raise HTTPException(
                status_code=400,
                detail=f"Transición inválida: {estado_actual} → {nuevo_estado}. Válidas: {transiciones_validas}",
            )

        updates = ["estado = $2"]
        params = [ticket_id, nuevo_estado]
        idx = 3

        # Fecha inicio real al entrar en curso por primera vez
        if nuevo_estado == "EN_CURSO":
            updates.append(f"timestamp_asignacion = COALESCE(timestamp_asignacion, ${idx})")
            params.append(datetime.now())
            idx += 1

        # Fecha resolución
        if nuevo_estado == "RESUELTO":
            updates.append(f"timestamp_resolucion = ${idx}")
            params.append(datetime.now())
            idx += 1
            # Calcular tiempo resolución
            updates.append(f"tiempo_resolucion_minutos = EXTRACT(EPOCH FROM (${idx}::timestamp - timestamp_creacion)) / 60")
            params.append(datetime.now())
            idx += 1

        await conn.execute(
            f"UPDATE incidencias_run SET {', '.join(updates)} WHERE ticket_id = $1",
            *params,
        )

        # Si hay nota, insertar en chat
        if body.nota:
            sala = await conn.fetchrow(
                "SELECT id FROM tech_chat_salas WHERE tipo = 'run' AND id_referencia = $1",
                ticket_id,
            )
            if not sala:
                sala_id = await conn.fetchval("""
                    INSERT INTO tech_chat_salas (tipo, id_referencia, nombre)
                    VALUES ('run', $1, $2) RETURNING id
                """, ticket_id, f"Incidencia {ticket_id}")
            else:
                sala_id = sala["id"]

            await conn.execute("""
                INSERT INTO tech_chat_mensajes (id_sala, id_autor, rol_autor, mensaje)
                VALUES ($1, $2, 'tecnico', $3)
            """, sala_id, id_recurso, body.nota)

    return {"ok": True, "ticket_id": ticket_id, "estado_anterior": estado_actual, "estado_nuevo": nuevo_estado}


# ── ENDPOINT 5: GET /api/tech/tareas ─────────────────────────────────────

@router.get("/tareas")
async def list_tareas(
    sprint: Optional[int] = Query(None),
    estado: Optional[str] = Query(None, description="Filtro estados separados por coma"),
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Lista tareas BUILD asignadas al técnico."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    query = """
        SELECT k.id, k.titulo, k.columna, k.prioridad, k.horas_estimadas,
               k.horas_reales, k.fecha_creacion, k.fecha_cierre,
               k.id_proyecto, c.nombre_proyecto
        FROM kanban_tareas k
        LEFT JOIN cartera_build c ON k.id_proyecto = c.id_proyecto
        WHERE k.id_tecnico = $1 AND k.tipo = 'BUILD'
    """
    params = [id_recurso]
    idx = 2

    if estado:
        estados = [e.strip() for e in estado.split(",")]
        placeholders = ", ".join(f"${idx + i}" for i in range(len(estados)))
        query += f" AND k.columna IN ({placeholders})"
        params.extend(estados)
        idx += len(estados)

    query += " ORDER BY k.fecha_creacion ASC"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [
        {
            "id": r["id"],
            "titulo": r["titulo"],
            "columna": r["columna"],
            "prioridad": r["prioridad"],
            "horas_estimadas": float(r["horas_estimadas"]) if r["horas_estimadas"] else 0,
            "horas_reales": float(r["horas_reales"]) if r["horas_reales"] else 0,
            "proyecto": r["nombre_proyecto"],
            "id_proyecto": r["id_proyecto"],
            "created_at": r["fecha_creacion"].isoformat() if r["fecha_creacion"] else None,
        }
        for r in rows
    ]


# ── ENDPOINT 6: GET /api/tech/tareas/{tarea_id} ─────────────────────────

@router.get("/tareas/{tarea_id}")
async def get_tarea_detail(
    tarea_id: str,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Detalle completo de tarea BUILD."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        tarea = await conn.fetchrow("""
            SELECT k.*, c.nombre_proyecto
            FROM kanban_tareas k
            LEFT JOIN cartera_build c ON k.id_proyecto = c.id_proyecto
            WHERE k.id = $1 AND k.id_tecnico = $2
        """, tarea_id, id_recurso)

        if not tarea:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        # Sprint info si tiene proyecto
        sprint_info = None
        if tarea["id_proyecto"]:
            sprint_info = await conn.fetchrow("""
                SELECT s.sprint_number, s.nombre, s.sprint_goal,
                       s.fecha_inicio, s.fecha_fin, s.estado,
                       s.story_points_planificados, s.story_points_completados
                FROM build_sprints s
                WHERE s.id_proyecto = $1 AND s.estado = 'ACTIVO'
                LIMIT 1
            """, tarea["id_proyecto"])

    return {
        "tarea": dict(tarea),
        "sprint": dict(sprint_info) if sprint_info else None,
    }


# ── ENDPOINT 7: PUT /api/tech/tareas/{tarea_id}/estado ───────────────────

class CambioEstadoTarea(BaseModel):
    columna: str
    nota: Optional[str] = None


TRANSICIONES_BUILD = {
    "Backlog": ["Análisis", "En Progreso"],
    "Análisis": ["En Progreso", "Backlog"],
    "En Progreso": ["Code Review", "Testing", "Bloqueado"],
    "Code Review": ["Testing", "En Progreso"],
    "Testing": ["Completado", "En Progreso"],
    "Bloqueado": ["En Progreso"],
    "Despliegue": ["Completado"],
}


@router.put("/tareas/{tarea_id}/estado")
async def cambiar_estado_tarea(
    tarea_id: str,
    body: CambioEstadoTarea,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Cambiar columna de tarea BUILD con validación de transiciones."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        tarea = await conn.fetchrow(
            "SELECT columna, historial_columnas FROM kanban_tareas WHERE id = $1 AND id_tecnico = $2",
            tarea_id, id_recurso,
        )
        if not tarea:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        col_actual = tarea["columna"]
        nueva_col = body.columna

        transiciones_validas = TRANSICIONES_BUILD.get(col_actual, [])
        if nueva_col not in transiciones_validas:
            raise HTTPException(
                status_code=400,
                detail=f"Transición inválida: {col_actual} → {nueva_col}. Válidas: {transiciones_validas}",
            )

        now = datetime.now()
        historial = tarea["historial_columnas"] or []
        historial.append({"de": col_actual, "a": nueva_col, "ts": now.isoformat()})

        updates = "columna = $2, historial_columnas = $3::jsonb"
        params = [tarea_id, nueva_col, __import__("json").dumps(historial)]

        if nueva_col == "En Progreso" and col_actual in ("Backlog", "Análisis"):
            updates += ", fecha_inicio_ejecucion = COALESCE(fecha_inicio_ejecucion, $4)"
            params.append(now)

        if nueva_col == "Completado":
            updates += f", fecha_cierre = ${len(params) + 1}"
            params.append(now)

        await conn.execute(
            f"UPDATE kanban_tareas SET {updates} WHERE id = $1",
            *params,
        )

        # Nota en chat
        if body.nota:
            sala = await conn.fetchrow(
                "SELECT id FROM tech_chat_salas WHERE tipo = 'build' AND id_referencia = $1",
                tarea_id,
            )
            if not sala:
                sala_id = await conn.fetchval("""
                    INSERT INTO tech_chat_salas (tipo, id_referencia, nombre)
                    VALUES ('build', $1, $2) RETURNING id
                """, tarea_id, f"Tarea {tarea_id}")
            else:
                sala_id = sala["id"]

            await conn.execute("""
                INSERT INTO tech_chat_mensajes (id_sala, id_autor, rol_autor, mensaje)
                VALUES ($1, $2, 'tecnico', $3)
            """, sala_id, id_recurso, body.nota)

    return {"ok": True, "tarea_id": tarea_id, "columna_anterior": col_actual, "columna_nueva": nueva_col}


# ── ENDPOINT 8: GET /api/tech/actividad ──────────────────────────────────

@router.get("/actividad")
async def feed_actividad(
    limit: int = Query(20, le=50),
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Feed de actividad reciente del técnico."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        # Incidencias recientes asignadas o actualizadas
        inc_activity = await conn.fetch("""
            SELECT 'incidencia' as tipo_actividad,
                   ticket_id as id_referencia,
                   incidencia_detectada as titulo,
                   estado,
                   prioridad_ia as prioridad,
                   COALESCE(timestamp_resolucion, timestamp_asignacion, timestamp_creacion) as fecha
            FROM incidencias_run
            WHERE tecnico_asignado = $1
            ORDER BY COALESCE(timestamp_resolucion, timestamp_asignacion, timestamp_creacion) DESC
            LIMIT $2
        """, id_recurso, limit)

        # Tareas kanban recientes
        tarea_activity = await conn.fetch("""
            SELECT 'tarea' as tipo_actividad,
                   id as id_referencia,
                   titulo,
                   columna as estado,
                   prioridad,
                   COALESCE(fecha_cierre, fecha_inicio_ejecucion, fecha_creacion) as fecha
            FROM kanban_tareas
            WHERE id_tecnico = $1
            ORDER BY COALESCE(fecha_cierre, fecha_inicio_ejecucion, fecha_creacion) DESC
            LIMIT $2
        """, id_recurso, limit)

        # Mensajes de chat recientes
        chat_activity = await conn.fetch("""
            SELECT 'mensaje' as tipo_actividad,
                   s.id_referencia,
                   s.nombre as titulo,
                   m.rol_autor as estado,
                   s.tipo as prioridad,
                   m.created_at as fecha
            FROM tech_chat_mensajes m
            JOIN tech_chat_salas s ON m.id_sala = s.id
            WHERE m.id_autor = $1 OR s.id_referencia IN (
                SELECT ticket_id FROM incidencias_run WHERE tecnico_asignado = $1
                UNION
                SELECT id FROM kanban_tareas WHERE id_tecnico = $1
            )
            ORDER BY m.created_at DESC
            LIMIT $2
        """, id_recurso, limit)

    # Merge and sort
    all_activity = []
    for r in inc_activity:
        all_activity.append({**dict(r), "fecha": r["fecha"].isoformat() if r["fecha"] else None})
    for r in tarea_activity:
        all_activity.append({**dict(r), "fecha": r["fecha"].isoformat() if r["fecha"] else None})
    for r in chat_activity:
        all_activity.append({**dict(r), "fecha": r["fecha"].isoformat() if r["fecha"] else None})

    all_activity.sort(key=lambda x: x.get("fecha") or "", reverse=True)
    return all_activity[:limit]


# ── ENDPOINT 9: POST /api/tech/adjuntos ──────────────────────────────────

@router.post("/adjuntos")
async def subir_adjunto(
    file: UploadFile = File(...),
    tipo: str = Form(..., description="run o build"),
    id_referencia: str = Form(...),
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Subir archivo adjunto a incidencia o tarea."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)

    if tipo not in ("run", "build"):
        raise HTTPException(status_code=400, detail="tipo debe ser 'run' o 'build'")

    # Save file
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    content = await file.read()
    _validate_upload(file, content)

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    pool = get_pool()
    async with pool.acquire() as conn:
        # Check if adjuntos table exists, create if not
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables WHERE table_name = 'tech_adjuntos'
            )
        """)
        if not exists:
            await conn.execute("""
                CREATE TABLE tech_adjuntos (
                    id SERIAL PRIMARY KEY,
                    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('run','build')),
                    id_referencia VARCHAR(30) NOT NULL,
                    nombre_original VARCHAR(255),
                    nombre_archivo VARCHAR(255) NOT NULL,
                    mime_type VARCHAR(100),
                    size_bytes INTEGER,
                    id_recurso VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

        await conn.execute("""
            INSERT INTO tech_adjuntos (tipo, id_referencia, nombre_original, nombre_archivo, mime_type, size_bytes, id_recurso)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, tipo, id_referencia, file.filename, filename, file.content_type, len(content), id_recurso)

    return {
        "ok": True,
        "filename": filename,
        "original": file.filename,
        "size": len(content),
        "tipo": tipo,
        "id_referencia": id_referencia,
    }


# ══════════════════════════════════════════════════════════════════════════
# CHAT ENDPOINTS (Teams-style)
# ══════════════════════════════════════════════════════════════════════════

CHAT_UPLOAD_DIR = "/app/uploads/chat"
os.makedirs(CHAT_UPLOAD_DIR, exist_ok=True)


@router.get("/chat/salas")
async def list_chat_salas(
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Lista salas de chat del técnico (vinculadas a sus incidencias y tareas)."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT s.id, s.tipo, s.id_referencia, s.nombre, s.activa, s.created_at,
                   (SELECT m.mensaje FROM tech_chat_mensajes m
                    WHERE m.id_sala = s.id ORDER BY m.created_at DESC LIMIT 1) as ultimo_mensaje,
                   (SELECT m.created_at FROM tech_chat_mensajes m
                    WHERE m.id_sala = s.id ORDER BY m.created_at DESC LIMIT 1) as fecha_ultimo,
                   (SELECT COUNT(*) FROM tech_chat_mensajes m
                    WHERE m.id_sala = s.id) as total_mensajes
            FROM tech_chat_salas s
            WHERE s.activa = TRUE
              AND (
                s.id_referencia IN (SELECT ticket_id FROM incidencias_run WHERE tecnico_asignado = $1)
                OR s.id_referencia IN (SELECT id FROM kanban_tareas WHERE id_tecnico = $1)
              )
            ORDER BY fecha_ultimo DESC NULLS LAST
        """, id_recurso)

    return [
        {
            "id": r["id"],
            "tipo": r["tipo"],
            "id_referencia": r["id_referencia"],
            "nombre": r["nombre"],
            "ultimo_mensaje": r["ultimo_mensaje"][:100] if r["ultimo_mensaje"] else None,
            "fecha_ultimo": r["fecha_ultimo"].isoformat() if r["fecha_ultimo"] else None,
            "total_mensajes": r["total_mensajes"],
            "activa": r["activa"],
        }
        for r in rows
    ]


@router.get("/chat/salas/{sala_id}/mensajes")
async def list_chat_mensajes(
    sala_id: int,
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    since: Optional[str] = Query(None, description="ISO timestamp para polling incremental"),
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Lista mensajes de una sala con paginación y polling incremental."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        # Verify access
        sala = await conn.fetchrow("""
            SELECT s.id FROM tech_chat_salas s
            WHERE s.id = $1
              AND (
                s.id_referencia IN (SELECT ticket_id FROM incidencias_run WHERE tecnico_asignado = $2)
                OR s.id_referencia IN (SELECT id FROM kanban_tareas WHERE id_tecnico = $2)
              )
        """, sala_id, id_recurso)
        if not sala:
            raise HTTPException(status_code=404, detail="Sala no encontrada")

        if since:
            # Polling: only new messages
            rows = await conn.fetch("""
                SELECT m.id, m.mensaje, m.rol_autor, m.id_autor, m.created_at,
                       COALESCE(p.nombre, m.id_autor) as nombre_autor
                FROM tech_chat_mensajes m
                LEFT JOIN pmo_staff_skills p ON m.id_autor = p.id_recurso
                WHERE m.id_sala = $1 AND m.created_at > $2::timestamp
                ORDER BY m.created_at ASC
            """, sala_id, since)
        else:
            rows = await conn.fetch("""
                SELECT m.id, m.mensaje, m.rol_autor, m.id_autor, m.created_at,
                       COALESCE(p.nombre, m.id_autor) as nombre_autor
                FROM tech_chat_mensajes m
                LEFT JOIN pmo_staff_skills p ON m.id_autor = p.id_recurso
                WHERE m.id_sala = $1
                ORDER BY m.created_at ASC
                LIMIT $2 OFFSET $3
            """, sala_id, limit, offset)

    return [
        {
            "id": r["id"],
            "mensaje": r["mensaje"],
            "rol_autor": r["rol_autor"],
            "id_autor": r["id_autor"],
            "nombre_autor": r["nombre_autor"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "es_mio": r["id_autor"] == id_recurso,
        }
        for r in rows
    ]


class ChatMensajeCreate(BaseModel):
    mensaje: str


@router.post("/chat/salas/{sala_id}/mensajes", status_code=201)
async def send_chat_mensaje(
    sala_id: int,
    body: ChatMensajeCreate,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Enviar mensaje a una sala de chat."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    if not body.mensaje.strip():
        raise HTTPException(status_code=400, detail="Mensaje vacío")

    async with pool.acquire() as conn:
        # Verify access
        sala = await conn.fetchrow("""
            SELECT s.id FROM tech_chat_salas s
            WHERE s.id = $1
              AND (
                s.id_referencia IN (SELECT ticket_id FROM incidencias_run WHERE tecnico_asignado = $2)
                OR s.id_referencia IN (SELECT id FROM kanban_tareas WHERE id_tecnico = $2)
              )
        """, sala_id, id_recurso)
        if not sala:
            raise HTTPException(status_code=404, detail="Sala no encontrada")

        row = await conn.fetchrow("""
            INSERT INTO tech_chat_mensajes (id_sala, id_autor, rol_autor, mensaje)
            VALUES ($1, $2, 'tecnico', $3)
            RETURNING id, created_at
        """, sala_id, id_recurso, body.mensaje.strip())

    nombre = await _get_nombre_recurso(id_recurso)
    return {
        "id": row["id"],
        "mensaje": body.mensaje.strip(),
        "rol_autor": "tecnico",
        "id_autor": id_recurso,
        "nombre_autor": nombre,
        "created_at": row["created_at"].isoformat(),
        "es_mio": True,
    }


async def _get_nombre_recurso(id_recurso: str) -> str:
    pool = get_pool()
    if not pool:
        return id_recurso
    async with pool.acquire() as conn:
        nombre = await conn.fetchval(
            "SELECT nombre FROM pmo_staff_skills WHERE id_recurso = $1", id_recurso)
    return nombre or id_recurso


@router.get("/chat/salas/{sala_id}/participantes")
async def list_chat_participantes(
    sala_id: int,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Lista participantes de una sala de chat."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        sala = await conn.fetchrow(
            "SELECT id, tipo, id_referencia FROM tech_chat_salas WHERE id = $1", sala_id)
        if not sala:
            raise HTTPException(status_code=404, detail="Sala no encontrada")

        participantes = []

        # Técnico asignado
        if sala["tipo"] == "run":
            tec = await conn.fetchrow("""
                SELECT tecnico_asignado as id_recurso FROM incidencias_run
                WHERE ticket_id = $1
            """, sala["id_referencia"])
        else:
            tec = await conn.fetchrow("""
                SELECT id_tecnico as id_recurso FROM kanban_tareas WHERE id = $1
            """, sala["id_referencia"])

        if tec and tec["id_recurso"]:
            staff = await conn.fetchrow("""
                SELECT nombre, nivel, silo_especialidad FROM pmo_staff_skills
                WHERE id_recurso = $1
            """, tec["id_recurso"])
            participantes.append({
                "id": tec["id_recurso"],
                "nombre": staff["nombre"] if staff else tec["id_recurso"],
                "rol": "tecnico",
                "nivel": staff["nivel"] if staff else None,
                "departamento": staff["silo_especialidad"] if staff else None,
                "es_yo": tec["id_recurso"] == id_recurso,
            })

        # Agentes que han participado
        agentes = await conn.fetch("""
            SELECT DISTINCT id_autor FROM tech_chat_mensajes
            WHERE id_sala = $1 AND rol_autor = 'agente'
        """, sala_id)
        for a in agentes:
            participantes.append({
                "id": a["id_autor"],
                "nombre": a["id_autor"],
                "rol": "agente",
                "nivel": None,
                "departamento": "Motor Cognitivo",
                "es_yo": False,
            })

        # PM o Gobernador (buscar en directorio si existe)
        if sala["tipo"] == "build":
            pm = await conn.fetchrow("""
                SELECT responsable_asignado FROM cartera_build
                WHERE id_proyecto = (SELECT id_proyecto FROM kanban_tareas WHERE id = $1)
            """, sala["id_referencia"])
            if pm and pm["responsable_asignado"]:
                pm_staff = await conn.fetchrow(
                    "SELECT nombre FROM pmo_staff_skills WHERE id_recurso = $1",
                    pm["responsable_asignado"])
                participantes.append({
                    "id": pm["responsable_asignado"],
                    "nombre": pm_staff["nombre"] if pm_staff else pm["responsable_asignado"],
                    "rol": "pm",
                    "nivel": None,
                    "departamento": "PMO",
                    "es_yo": False,
                })

    return participantes


# ── ARCHIVOS DE SALA ─────────────────────────────────────────────────────

@router.get("/chat/salas/{sala_id}/archivos")
async def list_chat_archivos(
    sala_id: int,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Lista archivos compartidos en una sala."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        sala = await conn.fetchrow(
            "SELECT id, tipo, id_referencia FROM tech_chat_salas WHERE id = $1", sala_id)
        if not sala:
            raise HTTPException(status_code=404, detail="Sala no encontrada")

        # Check if tech_adjuntos exists
        exists = await conn.fetchval("""
            SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tech_adjuntos')
        """)
        if not exists:
            return []

        rows = await conn.fetch("""
            SELECT id, nombre_original, nombre_archivo, mime_type, size_bytes,
                   id_recurso, created_at
            FROM tech_adjuntos
            WHERE tipo = $1 AND id_referencia = $2
            ORDER BY created_at DESC
        """, sala["tipo"], sala["id_referencia"])

    results = []
    for r in rows:
        subido_por = await _get_nombre_recurso(r["id_recurso"])
        results.append({
            "id": r["id"],
            "nombre": r["nombre_original"],
            "archivo": r["nombre_archivo"],
            "mime_type": r["mime_type"],
            "size_bytes": r["size_bytes"],
            "subido_por": subido_por,
            "id_recurso": r["id_recurso"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        })
    return results


@router.post("/chat/salas/{sala_id}/archivos", status_code=201)
async def upload_chat_archivo(
    sala_id: int,
    file: UploadFile = File(...),
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Subir archivo a una sala de chat."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        sala = await conn.fetchrow(
            "SELECT id, tipo, id_referencia FROM tech_chat_salas WHERE id = $1", sala_id)
        if not sala:
            raise HTTPException(status_code=404, detail="Sala no encontrada")

        # Save file
        sala_dir = os.path.join(CHAT_UPLOAD_DIR, str(sala_id))
        os.makedirs(sala_dir, exist_ok=True)
        content = await file.read()
        _validate_upload(file, content)

        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(sala_dir, filename)
        with open(filepath, "wb") as f:
            f.write(content)

        # Ensure table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tech_adjuntos (
                id SERIAL PRIMARY KEY,
                tipo VARCHAR(10) NOT NULL,
                id_referencia VARCHAR(30) NOT NULL,
                nombre_original VARCHAR(255),
                nombre_archivo VARCHAR(255) NOT NULL,
                mime_type VARCHAR(100),
                size_bytes INTEGER,
                id_recurso VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        row = await conn.fetchrow("""
            INSERT INTO tech_adjuntos (tipo, id_referencia, nombre_original, nombre_archivo, mime_type, size_bytes, id_recurso)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, created_at
        """, sala["tipo"], sala["id_referencia"], file.filename, filename,
            file.content_type, len(content), id_recurso)

        # Post notification in chat
        await conn.execute("""
            INSERT INTO tech_chat_mensajes (id_sala, id_autor, rol_autor, mensaje)
            VALUES ($1, $2, 'tecnico', $3)
        """, sala_id, id_recurso, f"📎 Archivo compartido: {file.filename}")

    return {
        "id": row["id"],
        "nombre": file.filename,
        "archivo": filename,
        "size_bytes": len(content),
        "created_at": row["created_at"].isoformat(),
    }


from fastapi.responses import FileResponse


# ══════════════════════════════════════════════════════════════════════════
# VALORACIÓN MENSUAL
# ══════════════════════════════════════════════════════════════════════════

@router.get("/valoracion")
async def get_valoraciones(
    meses: int = Query(6, le=24),
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Últimas N valoraciones del técnico logueado."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM tech_valoracion_mensual
            WHERE id_recurso = $1
            ORDER BY mes DESC
            LIMIT $2
        """, id_recurso, meses)

    return [
        {**dict(r), "mes": r["mes"].isoformat() if r["mes"] else None,
         "created_at": r["created_at"].isoformat() if r["created_at"] else None,
         "pct_sla": float(r["pct_sla"]) if r["pct_sla"] else 0,
         "velocidad_media_sp": float(r["velocidad_media_sp"]) if r["velocidad_media_sp"] else 0,
         "tasa_reopen": float(r["tasa_reopen"]) if r["tasa_reopen"] else 0,
         "puntuacion": float(r["puntuacion"]) if r["puntuacion"] else 0}
        for r in rows
    ]


@router.get("/valoracion/actual")
async def get_valoracion_actual(
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Valoración del mes actual (desde DB o calculada en vivo)."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    hoy = date.today()
    primer_dia = hoy.replace(day=1)

    async with pool.acquire() as conn:
        # Try stored value first
        stored = await conn.fetchrow("""
            SELECT * FROM tech_valoracion_mensual
            WHERE id_recurso = $1 AND mes = $2
        """, id_recurso, primer_dia)

        if stored:
            return {**dict(stored), "mes": stored["mes"].isoformat(),
                    "created_at": stored["created_at"].isoformat() if stored["created_at"] else None,
                    "pct_sla": float(stored["pct_sla"]),
                    "velocidad_media_sp": float(stored["velocidad_media_sp"]),
                    "tasa_reopen": float(stored["tasa_reopen"]),
                    "puntuacion": float(stored["puntuacion"]),
                    "fuente": "almacenada"}

        # Calculate live
        from calendar import monthrange
        dias_mes = monthrange(hoy.year, hoy.month)[1]
        mes_fin = date(hoy.year, hoy.month, dias_mes)
        semanas = max(dias_mes / 7, 1)

        total_inc = await conn.fetchval("""
            SELECT COUNT(*) FROM incidencias_run
            WHERE tecnico_asignado = $1 AND estado IN ('RESUELTO','CERRADO')
              AND timestamp_resolucion >= $2 AND timestamp_resolucion <= $3
        """, id_recurso, primer_dia, mes_fin) or 0

        inc_sla = 0
        if total_inc > 0:
            inc_sla = await conn.fetchval("""
                SELECT COUNT(*) FROM incidencias_run
                WHERE tecnico_asignado = $1 AND estado IN ('RESUELTO','CERRADO')
                  AND timestamp_resolucion >= $2 AND timestamp_resolucion <= $3
                  AND sla_limite IS NOT NULL AND tiempo_resolucion_minutos IS NOT NULL
                  AND tiempo_resolucion_minutos <= (sla_limite * 60)
            """, id_recurso, primer_dia, mes_fin) or 0

        pct_sla = round((inc_sla / total_inc) * 100, 2) if total_inc > 0 else 0

        total_tareas = await conn.fetchval("""
            SELECT COUNT(*) FROM kanban_tareas
            WHERE id_tecnico = $1 AND columna = 'Completado'
              AND fecha_cierre >= $2 AND fecha_cierre <= $3
        """, id_recurso, primer_dia, mes_fin) or 0

        sp = await conn.fetchval("""
            SELECT COALESCE(SUM(horas_estimadas), 0) FROM kanban_tareas
            WHERE id_tecnico = $1 AND columna = 'Completado'
              AND fecha_cierre >= $2 AND fecha_cierre <= $3
        """, id_recurso, primer_dia, mes_fin) or 0

        vel = round(float(sp) / semanas, 2)
        vel_pct = min((vel / 10) * 100, 100)
        punt = round((pct_sla * 0.40) + (vel_pct * 0.35) + (100 * 0.25), 2)

    return {
        "id_recurso": id_recurso,
        "mes": primer_dia.isoformat(),
        "total_incidencias": total_inc,
        "incidencias_en_sla": inc_sla,
        "pct_sla": pct_sla,
        "total_tareas": total_tareas,
        "story_points_completados": int(sp),
        "velocidad_media_sp": vel,
        "tasa_reopen": 0,
        "puntuacion": punt,
        "fuente": "calculada_en_vivo",
    }


# ── SERVIDORES + TERMINAL HISTORIAL ──────────────────────────────────────

@router.get("/servidores")
async def list_servidores(
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Lista servidores accesibles para el técnico (desde CMDB)."""
    u = _require_auth(user)
    pool = get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT a.codigo, a.nombre, a.tipo, a.criticidad, a.estado_ciclo,
                   i.direccion_ip, i.hostname
            FROM cmdb_activos a
            JOIN cmdb_ips i ON a.id_activo = i.id_activo
            WHERE (a.tipo ILIKE '%servidor%' OR a.tipo ILIKE '%vm%')
              AND a.estado_ciclo = 'OPERATIVO'
            ORDER BY a.codigo
        """)

    return [
        {
            "codigo": r["codigo"],
            "nombre": r["nombre"],
            "tipo": r["tipo"],
            "ip": r["direccion_ip"],
            "hostname": r["hostname"],
            "criticidad": r["criticidad"],
        }
        for r in rows
    ]


@router.get("/terminal/historial")
async def terminal_historial(
    sesion_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Historial de comandos del terminal (auditoría)."""
    u = _require_auth(user)
    id_recurso = await _get_id_recurso(u)
    pool = get_pool()

    async with pool.acquire() as conn:
        if sesion_id:
            rows = await conn.fetch("""
                SELECT comando, LEFT(salida, 500) as salida, servidor,
                       vinculado_tipo, vinculado_id, created_at
                FROM tech_terminal_log
                WHERE id_recurso = $1 AND sesion_id = $2::uuid
                ORDER BY created_at ASC
                LIMIT $3
            """, id_recurso, sesion_id, limit)
        else:
            rows = await conn.fetch("""
                SELECT sesion_id, servidor, comando, LEFT(salida, 200) as salida,
                       vinculado_tipo, vinculado_id, created_at
                FROM tech_terminal_log
                WHERE id_recurso = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, id_recurso, limit)

    return [
        {**dict(r), "created_at": r["created_at"].isoformat() if r["created_at"] else None,
         "sesion_id": str(r["sesion_id"]) if "sesion_id" in r.keys() else None}
        for r in rows
    ]


@router.get("/chat/salas/{sala_id}/archivos/{archivo_id}/descargar")
async def descargar_chat_archivo(
    sala_id: int,
    archivo_id: int,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Descargar un archivo de una sala."""
    u = _require_auth(user)
    pool = get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT nombre_original, nombre_archivo, mime_type
            FROM tech_adjuntos WHERE id = $1
        """, archivo_id)
        if not row:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

    # Try sala-specific path first, then global
    filepath = os.path.join(CHAT_UPLOAD_DIR, str(sala_id), row["nombre_archivo"])
    if not os.path.exists(filepath):
        filepath = os.path.join(UPLOAD_DIR, row["nombre_archivo"])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")

    return FileResponse(
        filepath,
        filename=row["nombre_original"],
        media_type=row["mime_type"] or "application/octet-stream",
    )


# ── F-IMPUTACIONES V2: tareas BUILD+RUN + actividades generales + jornada 8h ──

AVANCE_POR_COLUMNA = {
    'Backlog': 0, 'Análisis': 10, 'En Progreso': 30, 'Code Review': 60,
    'Testing': 80, 'Despliegue': 90, 'Completado': 100, 'Bloqueado': -1,
}


async def _total_jornada_dia(conn, id_tecnico: str, fecha) -> float:
    imp = float(await conn.fetchval(
        "SELECT COALESCE(SUM(horas),0) FROM horas_imputadas WHERE id_tecnico=$1 AND fecha=$2",
        id_tecnico, fecha) or 0)
    gen = float(await conn.fetchval(
        "SELECT COALESCE(SUM(horas),0) FROM horas_actividades_generales WHERE id_tecnico=$1 AND fecha=$2",
        id_tecnico, fecha) or 0)
    return round(imp + gen, 1)


@router.get("/imputaciones/{id_tecnico}")
async def get_imputaciones(id_tecnico: str, user: Optional[UserInfo] = Depends(get_current_user)):
    """V2: tareas BUILD+RUN + actividades generales + dashboard jornada."""
    _require_auth(user)
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        await conn.execute("SET search_path = primitiva, compartido, public")
        hoy = date.today()
        from datetime import timedelta
        lunes = hoy - timedelta(days=hoy.weekday())
        mes_inicio = hoy.replace(day=1)

        # Tareas activas (BUILD + RUN), con incidencia si existe
        tareas = await conn.fetch("""
            SELECT k.id, k.titulo, k.id_proyecto, k.id_incidencia, k.tipo, k.columna,
                   k.horas_estimadas, k.prioridad,
                   k.fecha_inicio_ejecucion, k.fecha_cierre,
                   cb.nombre_proyecto, cb.id_pm_usuario,
                   ir.categoria AS run_categoria, ir.sla_limite AS run_sla,
                   ir.area_afectada AS run_area
            FROM kanban_tareas k
            LEFT JOIN cartera_build cb ON cb.id_proyecto = k.id_proyecto AND k.tipo = 'BUILD'
            LEFT JOIN incidencias_run ir ON ir.ticket_id = k.id_incidencia AND k.tipo = 'RUN'
            WHERE k.id_tecnico = $1
              AND k.columna NOT IN ('Completado','Backlog')
            ORDER BY k.tipo, k.columna, k.titulo
        """, id_tecnico)

        result = []
        h_hoy_build = h_hoy_run = h_sem_build = h_sem_run = 0.0
        tareas_alerta = 0

        for t in tareas:
            imps = await conn.fetch("""
                SELECT id, fecha, horas, justificacion
                FROM horas_imputadas
                WHERE id_tecnico = $1 AND id_tarea = $2
                  AND fecha >= (CURRENT_DATE - INTERVAL '30 days')
                ORDER BY fecha DESC LIMIT 10
            """, id_tecnico, t['id'])
            total_imp = float(await conn.fetchval(
                "SELECT COALESCE(SUM(horas),0) FROM horas_imputadas WHERE id_tarea=$1",
                t['id']) or 0)
            h_est = float(t['horas_estimadas'] or 0)
            h_disp = max(0, h_est - total_imp) if t['tipo'] == 'BUILD' else None
            avance = AVANCE_POR_COLUMNA.get(t['columna'], 0)
            alerta = (t['tipo'] == 'BUILD' and h_est > 0 and total_imp / h_est > 0.9)
            if alerta:
                tareas_alerta += 1

            # PM name
            pm_nombre = None
            if t['id_pm_usuario']:
                pm_row = await conn.fetchrow(
                    "SELECT u.nombre_completo FROM rbac_usuarios u WHERE u.id_usuario=$1",
                    t['id_pm_usuario'])
                if pm_row:
                    pm_nombre = pm_row['nombre_completo']

            imp_list = []
            for i in imps:
                h = float(i['horas'])
                imp_list.append({
                    "id": i['id'], "fecha": i['fecha'].isoformat(),
                    "horas": h, "justificacion": i['justificacion'] or "",
                })
                if i['fecha'] == hoy:
                    if t['tipo'] == 'BUILD': h_hoy_build += h
                    else: h_hoy_run += h
                if i['fecha'] >= lunes:
                    if t['tipo'] == 'BUILD': h_sem_build += h
                    else: h_sem_run += h

            dias_rest = None
            if t['fecha_cierre']:
                d = t['fecha_cierre']
                if hasattr(d, 'date'):
                    d = d.date()
                dias_rest = (d - hoy).days

            # BUILD: proyecto + PM. RUN: referencia operativa + silo
            if t['tipo'] == 'BUILD':
                ref = t['id_proyecto'] or ''
                ref_nombre = t['nombre_proyecto'] or t['id_proyecto'] or ''
            else:
                ref = ('INC-' + t['id_incidencia']) if t['id_incidencia'] else ('OPS-' + t['id'][:12])
                ref_nombre = t.get('run_categoria') or t.get('run_area') or 'Operaciones'

            result.append({
                "id_tarea": t['id'], "titulo": t['titulo'],
                "referencia": ref, "referencia_nombre": ref_nombre,
                "tipo": t['tipo'], "columna": t['columna'],
                "avance_pct": avance, "prioridad": t['prioridad'],
                "pm_nombre": pm_nombre if t['tipo'] == 'BUILD' else None,
                "fecha_limite": t['fecha_cierre'].isoformat() if t['fecha_cierre'] else None,
                "dias_restantes": dias_rest,
                "horas_estimadas": h_est, "horas_imputadas_total": total_imp,
                "horas_disponibles": round(h_disp, 1) if h_disp is not None else None,
                "sin_tope": t['tipo'] == 'RUN',
                "sla_min": float(t['run_sla']) if t.get('run_sla') else None,
                "alerta": alerta, "imputaciones": imp_list,
            })

        # Actividades generales del día + semana
        act_hoy = await conn.fetch(
            "SELECT * FROM horas_actividades_generales WHERE id_tecnico=$1 AND fecha=$2 ORDER BY categoria",
            id_tecnico, hoy)
        act_semana = await conn.fetch(
            "SELECT * FROM horas_actividades_generales WHERE id_tecnico=$1 AND fecha>=$2 ORDER BY fecha DESC, categoria",
            id_tecnico, lunes)
        h_hoy_gen = sum(float(r['horas']) for r in act_hoy)
        h_sem_gen = sum(float(r['horas']) for r in act_semana)

        def _act(r):
            return {"id": r['id'], "fecha": r['fecha'].isoformat(), "categoria": r['categoria'],
                    "horas": float(r['horas']), "justificacion": r['justificacion']}

        # Calendar heatmap: daily totals for current month (L-V only)
        cal_raw = await conn.fetch("""
            SELECT d.fecha,
                   COALESCE((SELECT SUM(horas) FROM horas_imputadas WHERE id_tecnico=$1 AND fecha=d.fecha), 0)
                 + COALESCE((SELECT SUM(horas) FROM horas_actividades_generales WHERE id_tecnico=$1 AND fecha=d.fecha), 0) AS total
            FROM generate_series($2::date, $3::date, '1 day'::interval) AS d(fecha)
            WHERE EXTRACT(dow FROM d.fecha) BETWEEN 1 AND 5
            ORDER BY d.fecha
        """, id_tecnico, mes_inicio, hoy)
        dias_mes = [{"fecha": r['fecha'].isoformat(), "horas": round(float(r['total']), 1)} for r in cal_raw]

        # Histórico semanal (últimas 4 semanas)
        hist_sem = []
        for w in range(4):
            w_start = lunes - timedelta(weeks=w)
            w_end = w_start + timedelta(days=4)
            wn = w_start.isocalendar()[1]
            b = float(await conn.fetchval(
                "SELECT COALESCE(SUM(h.horas),0) FROM horas_imputadas h JOIN kanban_tareas k ON k.id=h.id_tarea WHERE h.id_tecnico=$1 AND h.fecha BETWEEN $2 AND $3 AND k.tipo='BUILD'",
                id_tecnico, w_start, w_end) or 0)
            r = float(await conn.fetchval(
                "SELECT COALESCE(SUM(h.horas),0) FROM horas_imputadas h JOIN kanban_tareas k ON k.id=h.id_tarea WHERE h.id_tecnico=$1 AND h.fecha BETWEEN $2 AND $3 AND k.tipo='RUN'",
                id_tecnico, w_start, w_end) or 0)
            # Also include imputaciones without id_tarea (seed data)
            seed = float(await conn.fetchval(
                "SELECT COALESCE(SUM(horas),0) FROM horas_imputadas WHERE id_tecnico=$1 AND fecha BETWEEN $2 AND $3 AND id_tarea IS NULL",
                id_tecnico, w_start, w_end) or 0)
            g = float(await conn.fetchval(
                "SELECT COALESCE(SUM(horas),0) FROM horas_actividades_generales WHERE id_tecnico=$1 AND fecha BETWEEN $2 AND $3",
                id_tecnico, w_start, w_end) or 0)
            hist_sem.append({"semana": f"W{wn:02d}", "build": round(b + seed, 1), "run": round(r, 1), "general": round(g, 1), "total": round(b + seed + r + g, 1)})

        # Semana actual detalle por día (para gráfico barras)
        dias_semana = []
        for d in range(5):
            dia = lunes + timedelta(days=d)
            db = float(await conn.fetchval(
                "SELECT COALESCE(SUM(horas),0) FROM horas_imputadas WHERE id_tecnico=$1 AND fecha=$2",
                id_tecnico, dia) or 0)
            dg = float(await conn.fetchval(
                "SELECT COALESCE(SUM(horas),0) FROM horas_actividades_generales WHERE id_tecnico=$1 AND fecha=$2",
                id_tecnico, dia) or 0)
            dias_semana.append({"fecha": dia.isoformat(), "dia": ['Lun','Mar','Mié','Jue','Vie'][d],
                                "horas": round(db + dg, 1), "es_hoy": dia == hoy})

        h_hoy = round(h_hoy_build + h_hoy_run + h_hoy_gen, 1)
        h_sem = round(h_sem_build + h_sem_run + h_sem_gen, 1)

        # Perfil mes
        h_mes = float(await conn.fetchval(
            "SELECT COALESCE(SUM(horas),0) FROM horas_imputadas WHERE id_tecnico=$1 AND fecha>=$2",
            id_tecnico, mes_inicio) or 0)
        h_mes_gen = float(await conn.fetchval(
            "SELECT COALESCE(SUM(horas),0) FROM horas_actividades_generales WHERE id_tecnico=$1 AND fecha>=$2",
            id_tecnico, mes_inicio) or 0)
        h_mes_total = round(h_mes + h_mes_gen, 1)
        dias_lab = max(1, (hoy - mes_inicio).days + 1)

        return {
            "tareas": result,
            "actividades_generales": [_act(r) for r in act_semana],
            "resumen": {
                "horas_hoy": h_hoy, "objetivo_diario": 8.0,
                "horas_hoy_build": round(h_hoy_build, 1), "horas_hoy_run": round(h_hoy_run, 1),
                "horas_hoy_general": round(h_hoy_gen, 1),
                "horas_pendientes_hoy": round(max(0, 8 - h_hoy), 1),
                "pct_jornada_hoy": min(100, round(h_hoy / 8 * 100)),
                "horas_semana": h_sem,
                "tareas_activas": len(result), "tareas_con_alerta": tareas_alerta,
            },
            "dias_semana": dias_semana,
            "dias_mes": dias_mes,
            "historico_semanal": hist_sem,
            "perfil_resumen": {
                "total_horas_mes": h_mes_total,
                "media_horas_dia": round(h_mes_total / dias_lab, 1),
            },
        }


class ImputacionCreate(BaseModel):
    id_tecnico: str
    id_tarea: str
    fecha: str
    horas: float
    justificacion: str


@router.post("/imputaciones")
async def post_imputacion(body: ImputacionCreate, user: Optional[UserInfo] = Depends(get_current_user)):
    """Crea o actualiza imputación diaria. Regla BUILD: no superar horas_estimadas. Jornada max 10h."""
    _require_auth(user)
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    if not body.justificacion or len(body.justificacion.strip()) < 5:
        raise HTTPException(400, "La justificación debe tener al menos 5 caracteres")
    if body.horas <= 0 or body.horas > 12:
        raise HTTPException(400, "Las horas deben estar entre 0.1 y 12")
    try:
        fecha = date.fromisoformat(body.fecha)
    except ValueError:
        raise HTTPException(400, "Formato de fecha inválido (YYYY-MM-DD)")
    if fecha > date.today():
        raise HTTPException(400, "No se puede imputar en el futuro")

    async with pool.acquire() as conn:
        await conn.execute("SET search_path = primitiva, compartido, public")
        tarea = await conn.fetchrow(
            "SELECT tipo, horas_estimadas, id_proyecto FROM kanban_tareas WHERE id = $1",
            body.id_tarea)
        if not tarea:
            raise HTTPException(404, f"Tarea {body.id_tarea} no encontrada")
        h_est = float(tarea['horas_estimadas'] or 0)
        iso_week = fecha.isocalendar()[1]

        # Jornada máxima 10h
        total_dia = await _total_jornada_dia(conn, body.id_tecnico, fecha)
        existing_this = float(await conn.fetchval(
            "SELECT COALESCE(SUM(horas),0) FROM horas_imputadas WHERE id_tecnico=$1 AND id_tarea=$2 AND fecha=$3",
            body.id_tecnico, body.id_tarea, fecha) or 0)
        if total_dia - existing_this + body.horas > 10:
            raise HTTPException(400, f"Jornada máxima 10h/día superada. Total actual: {total_dia}h")

        # Regla BUILD
        if tarea['tipo'] == 'BUILD' and h_est > 0:
            total_previo = float(await conn.fetchval(
                "SELECT COALESCE(SUM(horas),0) FROM horas_imputadas "
                "WHERE id_tarea=$1 AND NOT (id_tecnico=$2 AND fecha=$3)",
                body.id_tarea, body.id_tecnico, fecha) or 0)
            if total_previo + body.horas > h_est:
                raise HTTPException(409, detail={
                    "error": "BUDGET_EXCEEDED",
                    "message": "Supera las horas estimadas. Solicita ampliación a tu PM.",
                    "horas_estimadas": h_est,
                    "horas_imputadas": round(total_previo + existing_this, 1),
                    "horas_solicitadas": body.horas,
                    "exceso": round(total_previo + body.horas - h_est, 1),
                })

        existing_id = await conn.fetchval(
            "SELECT id FROM horas_imputadas WHERE id_tecnico=$1 AND id_tarea=$2 AND fecha=$3",
            body.id_tecnico, body.id_tarea, fecha)
        if existing_id:
            await conn.execute("""
                UPDATE horas_imputadas SET horas=$1, justificacion=$2, modified_by=$3,
                       updated_at=NOW(), semana_iso=$4, id_proyecto=$5
                WHERE id=$6
            """, body.horas, body.justificacion.strip(), body.id_tecnico,
                iso_week, tarea['id_proyecto'], existing_id)
            return {"ok": True, "id": existing_id, "mode": "updated"}
        else:
            new_id = await conn.fetchval("""
                INSERT INTO horas_imputadas
                    (id_tecnico, id_tarea, id_proyecto, fecha, horas, semana_iso,
                     justificacion, created_by)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id
            """, body.id_tecnico, body.id_tarea, tarea['id_proyecto'],
                fecha, body.horas, iso_week,
                body.justificacion.strip(), body.id_tecnico)
            return {"ok": True, "id": new_id, "mode": "created"}


class ActividadGeneralCreate(BaseModel):
    id_tecnico: str
    fecha: str
    categoria: str
    horas: float
    justificacion: str


CATEGORIAS_VALIDAS = {'REUNION_DEPTO','REUNION_PROYECTO','FORMACION','INVESTIGACION_ID',
                      'MENTORING','ADMINISTRATIVO','GUARDIA','OTRO'}

@router.post("/actividades-generales")
async def post_actividad_general(body: ActividadGeneralCreate, user: Optional[UserInfo] = Depends(get_current_user)):
    """Registra actividad general (reunión, formación, etc.). Jornada max 10h."""
    _require_auth(user)
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    if not body.justificacion or len(body.justificacion.strip()) < 5:
        raise HTTPException(400, "La justificación debe tener al menos 5 caracteres")
    if body.horas < 0.5 or body.horas > 8:
        raise HTTPException(400, "Las horas deben estar entre 0.5 y 8")
    if body.categoria not in CATEGORIAS_VALIDAS:
        raise HTTPException(400, f"Categoría inválida: {body.categoria}")
    try:
        fecha = date.fromisoformat(body.fecha)
    except ValueError:
        raise HTTPException(400, "Formato de fecha inválido (YYYY-MM-DD)")
    if fecha > date.today():
        raise HTTPException(400, "No se puede registrar en el futuro")

    async with pool.acquire() as conn:
        await conn.execute("SET search_path = primitiva, compartido, public")
        total_dia = await _total_jornada_dia(conn, body.id_tecnico, fecha)
        existing = float(await conn.fetchval(
            "SELECT COALESCE(SUM(horas),0) FROM horas_actividades_generales WHERE id_tecnico=$1 AND fecha=$2 AND categoria=$3",
            body.id_tecnico, fecha, body.categoria) or 0)
        if total_dia - existing + body.horas > 10:
            raise HTTPException(400, f"Jornada máxima 10h/día superada. Total actual: {total_dia}h")

        existing_id = await conn.fetchval(
            "SELECT id FROM horas_actividades_generales WHERE id_tecnico=$1 AND fecha=$2 AND categoria=$3",
            body.id_tecnico, fecha, body.categoria)
        if existing_id:
            await conn.execute(
                "UPDATE horas_actividades_generales SET horas=$1, justificacion=$2, updated_at=NOW() WHERE id=$3",
                body.horas, body.justificacion.strip(), existing_id)
            return {"ok": True, "id": existing_id, "mode": "updated"}
        else:
            new_id = await conn.fetchval("""
                INSERT INTO horas_actividades_generales (id_tecnico, fecha, categoria, horas, justificacion, created_by)
                VALUES ($1,$2,$3,$4,$5,$6) RETURNING id
            """, body.id_tecnico, fecha, body.categoria, body.horas,
                body.justificacion.strip(), body.id_tecnico)
            return {"ok": True, "id": new_id, "mode": "created"}

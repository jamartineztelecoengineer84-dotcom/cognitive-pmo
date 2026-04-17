import os
import re
import json
import uuid
import logging
from datetime import datetime, date, timedelta
import hashlib
import secrets
import time as _time
import asyncio as _asyncio
from typing import Any, Dict, List, Optional

import psycopg2
import httpx
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_pool, get_pool, close_pool
from scenario_context import (
    validate_scenario,
    set_current_scenario,
    reset_current_scenario,
    get_current_scenario,
)
from models import (
    ProyectoCreate,
    IncidenciaCreate,
    AsignarTecnico,
    BufferUpdate,
    KanbanTareaCreate,
)
from rbac_api import router as rbac_router
from cmdb_api import router as cmdb_router
from p96_router import router as p96_router, me_router as p96_me_router
from pm_router import pm_router
from scenario_engine import seed_scenario, reset_scenario
from db_loader import router as db_loader_router
from tech_routes import router as tech_router
from tech_terminal_ws import router as tech_terminal_router
from tech_copiloto import router as tech_copiloto_router
from auth import get_current_user, UserInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── DB Config ──────────────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "cognitive_pmo")
DB_USER = os.getenv("DB_USER", "jose_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def get_sync_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
    )


def run_init_sql():
    """Run init.sql and rbac_schema.sql using psycopg2 on startup. Executes statement-by-statement to tolerate duplicates."""
    base_dir = os.path.dirname(__file__)
    sql_files = ["init.sql", "rbac_schema.sql", "cmdb_schema.sql", "cmdb_seed_extra.sql", "cmdb_ips_seed.sql", "cmdb_costes_schema.sql", "agents_migrations.sql", "llm_provider_schema.sql"]
    for sql_file in sql_files:
        sql_path = os.path.join(base_dir, sql_file)
        if not os.path.exists(sql_path):
            logger.warning(f"{sql_file} not found, skipping")
            continue
        try:
            with open(sql_path, "r", encoding="utf-8") as f:
                sql = f.read()
            conn = get_sync_conn()
            conn.autocommit = True
            cur = conn.cursor()
            # Split by semicolons and execute each statement individually
            # so that duplicate index/insert errors don't abort everything
            statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
            ok, skip = 0, 0
            for stmt in statements:
                try:
                    cur.execute(stmt)
                    ok += 1
                except Exception as e:
                    err_msg = str(e).lower()
                    if 'already exists' in err_msg or 'duplicate' in err_msg or 'unique' in err_msg:
                        skip += 1
                    else:
                        logger.debug(f"SQL skip ({sql_file}): {err_msg[:80]}")
                        skip += 1
            cur.close()
            conn.close()
            logger.info(f"{sql_file} initialized: {ok} statements OK, {skip} skipped")
        except Exception as e:
            logger.warning(f"{sql_file} init failed: {e}")


# ── Startup / Shutdown ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    run_init_sql()
    await init_pool()
    # Scheduler de monitorización (Pilares 1 y 4)
    _scheduler = None
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        from monitor import health_check_diario, resumen_diario_actividad
        _scheduler = AsyncIOScheduler(timezone="Europe/Madrid")
        _scheduler.add_job(health_check_diario, CronTrigger(hour=8, minute=0), id="health_08")
        _scheduler.add_job(resumen_diario_actividad, CronTrigger(hour=21, minute=0), id="resumen_21")
        _scheduler.start()
        logger.info("Monitor scheduler: health 08:00, resumen 21:00 (Europe/Madrid)")
    except Exception as e:
        logger.warning(f"Monitor scheduler no iniciado: {e}")
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)
    await close_pool()


app = FastAPI(title="Cognitive PMO API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── F5 · role_gate (defensa en profundidad /api/pm /api/tech /api/p96) ──
from authz import role_gate_middleware
app.middleware("http")(role_gate_middleware)


# ── ARQ-03 F3: middleware X-Scenario → ContextVar → pool setup callback ──
@app.middleware("http")
async def scenario_middleware(request: Request, call_next):
    """Lee header X-Scenario, valida contra whitelist, setea ContextVar.

    El pool_setup_callback de asyncpg leerá el ContextVar en cada
    pool.acquire() y fijará search_path = <scenario>, compartido, public.
    Cero cambios en handlers existentes; siguen usando pool.acquire()
    directo.
    """
    header = request.headers.get("x-scenario")
    try:
        scenario = validate_scenario(header)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail},
        )
    token = set_current_scenario(scenario)
    try:
        response = await call_next(request)
    finally:
        reset_current_scenario(token)
    return response


# ── ARQ-03 F3: endpoint debug para verificar X-Scenario end-to-end ───────
@app.get("/api/_debug/search_path")
async def debug_search_path():
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    async with pool.acquire() as conn:
        sp = await conn.fetchval("SELECT current_setting('search_path')")
    return {"search_path": sp, "scenario_ctx": get_current_scenario()}


# ── RBAC Router ───────────────────────────────────────────────────────────
app.include_router(rbac_router)
app.include_router(cmdb_router)
app.include_router(db_loader_router)
app.include_router(tech_router)
app.include_router(tech_terminal_router)
app.include_router(tech_copiloto_router)
app.include_router(p96_router)
app.include_router(p96_me_router)
app.include_router(pm_router)


# ── Admin: Valoración mensual ─────────────────────────────────────────────
@app.post("/api/admin/valoracion/calcular")
async def admin_calcular_valoracion(
    mes: Optional[str] = None,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Ejecutar job de valoración mensual. Solo admin/superadmin."""
    from jobs.tech_valoracion_job import calcular_valoracion_mensual
    if user and hasattr(user, 'role_code') and user.role_code not in ('SUPERADMIN', 'CTO', 'CIO', 'VP_PMO', 'PMO_SENIOR'):
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar este job")
    pool = get_pool()
    mes_date = None
    if mes:
        from datetime import date as d
        mes_date = d.fromisoformat(mes)
    result = await calcular_valoracion_mensual(pool, mes_date)
    return result


# ── Helpers ────────────────────────────────────────────────────────────────
def serialize(row: Any) -> Any:
    """Convert asyncpg Record or psycopg2 dict to plain dict."""
    if row is None:
        return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, (datetime, date)):
            d[k] = v.isoformat()
    return d


# ── ARQ-03 F4 · Scenario Engine admin endpoint (post-esquemas) ─────────────
@app.post("/api/admin/seed-scenario")
async def admin_seed_scenario(
    body: dict,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Seed un escenario destino con el perfil pedido.

    Body: {"scenario": "sc_piloto0", "profile": "empty|half|optimal|overload"}.
    Solo SUPERADMIN. primitiva NUNCA se escribe (raise ValueError → 400).
    El scenario_engine refactorizado opera dentro del esquema destino vía
    SET LOCAL search_path; el header X-Scenario es opcional.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    if user.role_code != 'SUPERADMIN':
        raise HTTPException(status_code=403, detail="SUPERADMIN required")

    scenario = body.get("scenario", "sc_piloto0")
    profile  = body.get("profile",  "optimal")

    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")

    async with pool.acquire() as conn:
        try:
            result = await seed_scenario(conn, scenario, profile)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Counts post-seed dentro del esquema destino
        await conn.execute(
            f"SET LOCAL search_path = {scenario}, compartido, public"
        )
        counts_post = {
            "build_live":      await conn.fetchval("SELECT COUNT(*) FROM build_live"),
            "kanban_tareas":   await conn.fetchval("SELECT COUNT(*) FROM kanban_tareas"),
            "incidencias_run": await conn.fetchval("SELECT COUNT(*) FROM incidencias_run"),
        }

    return {**result, "counts_post": counts_post}


# ── Mock Data ──────────────────────────────────────────────────────────────
MOCK_TECNICOS = [
    {"id_recurso": "FTE-001", "nombre": "Jorge Sánchez Iglesias", "silo_especialidad": "Backend", "nivel": "N2", "total_skills": 40, "skills_json": ["Git: Clonar repositorios", "Backend: Crear Endpoint REST"], "estado_run": "DISPONIBLE", "carga_actual": 0, "skill_principal": "Git: Clonar repositorios"},
    {"id_recurso": "FTE-010", "nombre": "Marta Ruiz Hernández", "silo_especialidad": "Frontend", "nivel": "N2", "total_skills": 38, "skills_json": ["CSS: Flexbox", "JS: Manipulación DOM"], "estado_run": "DISPONIBLE", "carga_actual": 0, "skill_principal": "CSS: Flexbox"},
    {"id_recurso": "FTE-030", "nombre": "Carlos Díaz Moreno", "silo_especialidad": "Redes", "nivel": "N3", "total_skills": 52, "skills_json": ["Redes: IP/Gateway", "Redes: BGP"], "estado_run": "DISPONIBLE", "carga_actual": 0, "skill_principal": "Redes: BGP"},
]

MOCK_PROYECTOS = [
    {"id_proyecto": "PRJ0001 - [9470-2023]", "nombre_proyecto": "Centralizar la gestión de identidades", "prioridad_estrategica": "Media", "estado": "en ejecucion", "horas_estimadas": 60, "skills_requeridas": "AD: Crear Usuario", "fecha_creacion": "2025-01-15"},
    {"id_proyecto": "PRJ0009 - [9470-2023]", "nombre_proyecto": "Rearquitectura de la red de los Data Centers", "prioridad_estrategica": "Alta", "estado": "en ejecucion", "horas_estimadas": 150, "skills_requeridas": "Redes: Netstat", "fecha_creacion": "2025-01-05"},
]

MOCK_INCIDENCIAS = [
    {"ticket_id": "INC-MOCK001", "incidencia_detectada": "Caída servicio SWIFT Alliance", "prioridad_ia": "P1", "estado": "EN_CURSO", "timestamp_creacion": "2026-01-01T00:00:00"},
    {"ticket_id": "INC-MOCK002", "incidencia_detectada": "Resolver latencia red CPD Madrid", "prioridad_ia": "P2", "estado": "QUEUED", "timestamp_creacion": "2026-01-01T00:00:00"},
]


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return {"status": "ok", "db": "conectado"}
        except Exception:
            pass
    return {"status": "ok", "db": "sin conexion"}


@app.get("/cartera/proyectos")
async def get_proyectos():
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT *, CASE prioridad_estrategica
                        WHEN 'Crítica' THEN 1 WHEN 'Alta' THEN 2
                        WHEN 'Media' THEN 3 WHEN 'Baja' THEN 4 ELSE 5 END as prioridad_num
                    FROM cartera_build
                    ORDER BY prioridad_num, fecha_creacion
                """)
                return [serialize(r) for r in rows]
        except Exception as e:
            logger.warning(f"DB error in /cartera/proyectos: {e}")
    return MOCK_PROYECTOS


@app.get("/disponibilidad/global")
async def get_disponibilidad():
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM pmo_staff_skills WHERE estado_run = 'DISPONIBLE' ORDER BY nombre"
                )
                return [serialize(r) for r in rows]
        except Exception as e:
            logger.warning(f"DB error in /disponibilidad/global: {e}")
    return [t for t in MOCK_TECNICOS if t["estado_run"] == "DISPONIBLE"]


@app.get("/team/tecnicos")
async def get_tecnicos():
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT s.*,
                           COALESCE(inc.n_inc, 0) AS incidencias_activas,
                           COALESCE(kan.n_kan, 0) AS tareas_activas,
                           CASE
                             WHEN COALESCE(inc.n_inc,0)+COALESCE(kan.n_kan,0) = 0 THEN 'DISPONIBLE'
                             WHEN COALESCE(inc.n_inc,0)+COALESCE(kan.n_kan,0) <= 3 THEN 'ASIGNADO'
                             ELSE 'OCUPADO'
                           END AS estado_run_dinamico,
                           LEAST(COALESCE(inc.n_inc,0)+COALESCE(kan.n_kan,0), 10)*10 AS carga_dinamica
                    FROM compartido.pmo_staff_skills s
                    LEFT JOIN (
                        SELECT tecnico_asignado, COUNT(*) AS n_inc
                        FROM incidencias_run
                        WHERE estado NOT IN ('CERRADO','RESUELTO')
                        GROUP BY tecnico_asignado
                    ) inc ON inc.tecnico_asignado = s.id_recurso
                    LEFT JOIN (
                        SELECT id_tecnico, COUNT(*) AS n_kan
                        FROM kanban_tareas
                        WHERE columna NOT IN ('Completado','Backlog')
                        GROUP BY id_tecnico
                    ) kan ON kan.id_tecnico = s.id_recurso
                    ORDER BY s.nombre
                """)
                result = []
                for r in rows:
                    d = serialize(r)
                    if 'estado_run_dinamico' in d:
                        d['estado_run'] = d['estado_run_dinamico']
                    if 'carga_dinamica' in d:
                        d['carga_actual'] = d['carga_dinamica']
                    result.append(d)
                
                # B3: Enriquecer con vinculacion para técnicos asignados
                try:
                    for d in result:
                        rid = d.get('id_recurso', '')
                        if not rid:
                            continue
                        est = (d.get('estado_run') or d.get('estado') or '').upper()
                        if est in ('DISPONIBLE', ''):
                            d['vinculacion'] = ''
                            d['tarea_actual'] = ''
                            continue
                        # Buscar en incidencias_run activas
                        inc_row = await conn.fetchrow(
                            "SELECT ticket_id, incidencia_detectada FROM incidencias_run "
                            "WHERE tecnico_asignado = $1 AND estado NOT IN ('CERRADO','RESUELTO') "
                            "ORDER BY timestamp_creacion DESC LIMIT 1", rid
                        )
                        if inc_row:
                            tid = inc_row['ticket_id'] or ''
                            desc = (inc_row['incidencia_detectada'] or '')[:40]
                            d['vinculacion'] = f"INC {tid}: {desc}"
                            d['tarea_actual'] = d['vinculacion']
                            d['proyecto_actual'] = tid
                            continue
                        # Buscar en kanban_tareas activas
                        kan_row = await conn.fetchrow(
                            "SELECT id, titulo, id_proyecto FROM kanban_tareas "
                            "WHERE id_tecnico = $1 "
                            "AND columna NOT IN ('Completado','Done','Backlog') "
                            "ORDER BY created_at DESC LIMIT 1", rid
                        )
                        if kan_row:
                            titulo = (kan_row['titulo'] or '')[:35]
                            proj = kan_row.get('id_proyecto') or ''
                            d['vinculacion'] = f"BUILD {proj}: {titulo}"
                            d['tarea_actual'] = d['vinculacion']
                            d['proyecto_actual'] = proj
                        else:
                            d['vinculacion'] = est
                            d['tarea_actual'] = ''
                except Exception as e:
                    logger.warning(f"B3 vinculacion error: {e}")

                # C1: estado_run -> estado para frontend KPIs
                for d in result:
                    d['estado'] = d.get('estado_run') or d.get('estado', 'DISPONIBLE')

                return result
        except Exception as e:
            logger.warning(f"DB error in /team/tecnicos: {e}")
    return MOCK_TECNICOS


async def _sync_tecnico_estado(conn, id_tecnico: str):
    """Auto-update technician estado_run based on their active kanban tasks."""
    if not id_tecnico:
        return
    active = await conn.fetchval(
        "SELECT COUNT(*) FROM kanban_tareas WHERE id_tecnico=$1 AND columna NOT IN ('Completado','Backlog')",
        id_tecnico,
    )
    new_estado = 'OCUPADO' if active and active > 0 else 'DISPONIBLE'
    # Only change if currently DISPONIBLE or OCUPADO (don't override GUARDIA/BAJA/VACACIONES)
    await conn.execute(
        """UPDATE pmo_staff_skills SET estado_run=$1
           WHERE id_recurso=$2 AND estado_run IN ('DISPONIBLE','OCUPADO')""",
        new_estado, id_tecnico,
    )


# TODO-DEPRECATE P95-F7 (eliminar tras 2026-04-21):
# Endpoint legacy del kanban 8-columnas. Mantenido como alias durante 2 semanas
# para no romper consumidores existentes (gov-build loadTeam, jobs, dist/*).
# El reemplazo es GET /api/kanban/tareas con schema unificado RUN+BUILD.
@app.get("/kanban/tareas")
async def get_kanban():
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT k.*, s.nombre as nombre_tecnico
                    FROM kanban_tareas k
                    LEFT JOIN pmo_staff_skills s ON k.id_tecnico = s.id_recurso
                    ORDER BY k.fecha_creacion DESC
                """)
                return [serialize(r) for r in rows]
        except Exception as e:
            logger.warning(f"DB error in /kanban/tareas: {e}")
    return []


class KanbanTareaFull(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    tipo: str = "RUN"
    prioridad: str = "Media"
    columna: str = "Backlog"
    id_tecnico: Optional[str] = None
    id_proyecto: Optional[str] = None
    id_incidencia: Optional[str] = None
    bloqueador: Optional[str] = None
    horas_estimadas: float = 0
    horas_reales: float = 0


@app.post("/kanban/tareas")
async def create_kanban_tarea(t: KanbanTareaFull):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    # Generate ID: KT-YYYYMMDD-NNN
    prefix = f"KT-{datetime.now().strftime('%Y%m%d')}"
    try:
        async with pool.acquire() as conn:
            cnt = await conn.fetchval(
                "SELECT COUNT(*) FROM kanban_tareas WHERE id LIKE $1", prefix + '%'
            )
            task_id = f"{prefix}-{(cnt or 0)+1:03d}"
            fe = None
            fc = None
            if t.columna in ('En Progreso','Code Review','Testing','Despliegue'):
                fe = datetime.now()
            if t.columna == 'Completado':
                fe = fe or datetime.now()
                fc = datetime.now()
            hist = json.dumps([{"columna": t.columna, "timestamp": datetime.now().isoformat()}])
            row = await conn.fetchrow(
                """INSERT INTO kanban_tareas
                    (id,titulo,descripcion,tipo,prioridad,columna,id_tecnico,
                     id_proyecto,id_incidencia,bloqueador,horas_estimadas,horas_reales,
                     fecha_inicio_ejecucion,fecha_cierre,historial_columnas)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15::jsonb) RETURNING *""",
                task_id, t.titulo, t.descripcion, t.tipo, t.prioridad, t.columna,
                t.id_tecnico, t.id_proyecto, t.id_incidencia, t.bloqueador,
                t.horas_estimadas, t.horas_reales, fe, fc, hist,
            )
            await _sync_tecnico_estado(conn, t.id_tecnico)
            return serialize(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/kanban/tareas/{task_id}")
async def update_kanban_tarea(task_id: str, t: KanbanTareaFull):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    try:
        async with pool.acquire() as conn:
            old = await conn.fetchrow("SELECT columna, fecha_inicio_ejecucion, historial_columnas FROM kanban_tareas WHERE id=$1", task_id)
            if not old:
                raise HTTPException(status_code=404, detail="Tarea no encontrada")
            fe = old['fecha_inicio_ejecucion']
            fc = None
            # Auto-set fecha_inicio_ejecucion when entering work columns
            if t.columna in ('En Progreso','Code Review','Testing','Despliegue') and not fe:
                fe = datetime.now()
            # Auto-set fecha_cierre when completing
            if t.columna == 'Completado':
                fc = datetime.now()
                if not fe:
                    fe = datetime.now()
            # Update history if column changed
            hist = old['historial_columnas'] or []
            if isinstance(hist, str):
                hist = json.loads(hist)
            if t.columna != old['columna']:
                hist.append({"columna": t.columna, "timestamp": datetime.now().isoformat()})
            row = await conn.fetchrow(
                """UPDATE kanban_tareas SET
                    titulo=$2, descripcion=$3, tipo=$4, prioridad=$5, columna=$6,
                    id_tecnico=$7, id_proyecto=$8, id_incidencia=$9, bloqueador=$10,
                    horas_estimadas=$11, horas_reales=$12,
                    fecha_inicio_ejecucion=$13, fecha_cierre=$14,
                    historial_columnas=$15::jsonb
                WHERE id=$1 RETURNING *""",
                task_id, t.titulo, t.descripcion, t.tipo, t.prioridad, t.columna,
                t.id_tecnico, t.id_proyecto, t.id_incidencia, t.bloqueador,
                t.horas_estimadas, t.horas_reales, fe, fc, json.dumps(hist),
            )
            await _sync_tecnico_estado(conn, t.id_tecnico)
            # If technician changed, also sync the old one
            if old['id_tecnico'] and old['id_tecnico'] != t.id_tecnico:
                await _sync_tecnico_estado(conn, old['id_tecnico'])
            return serialize(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/kanban/tareas/{task_id}/mover")
async def mover_kanban_tarea(task_id: str, columna: str = ""):
    """Move a task to a new column, auto-updating dates."""
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    try:
        async with pool.acquire() as conn:
            old = await conn.fetchrow("SELECT * FROM kanban_tareas WHERE id=$1", task_id)
            if not old:
                raise HTTPException(status_code=404, detail="Tarea no encontrada")
            fe = old['fecha_inicio_ejecucion']
            fc = old['fecha_cierre']
            if columna in ('En Progreso','Code Review','Testing','Despliegue') and not fe:
                fe = datetime.now()
            if columna == 'Completado':
                fc = datetime.now()
                if not fe:
                    fe = datetime.now()
            # Reset cierre if moving back from Completado
            if old['columna'] == 'Completado' and columna != 'Completado':
                fc = None
            hist = old['historial_columnas'] or []
            if isinstance(hist, str):
                hist = json.loads(hist)
            hist.append({"columna": columna, "timestamp": datetime.now().isoformat()})
            row = await conn.fetchrow(
                """UPDATE kanban_tareas SET columna=$2,
                    fecha_inicio_ejecucion=$3, fecha_cierre=$4,
                    historial_columnas=$5::jsonb
                WHERE id=$1 RETURNING *""",
                task_id, columna, fe, fc, json.dumps(hist),
            )
            await _sync_tecnico_estado(conn, old['id_tecnico'])
            # Hook: notificación al técnico cuando cambia estado
            try:
                if old['id_tecnico'] and columna != old['columna']:
                    tech_user = await conn.fetchval(
                        "SELECT id_usuario FROM rbac_usuarios WHERE id_recurso=$1", old['id_tecnico'])
                    if tech_user:
                        await crear_notificacion(
                            conn, tech_user, 'estado',
                            f'Tarea movida a {columna}',
                            f'{old["titulo"][:80]} cambió de {old["columna"]} a {columna}.',
                            'tarea', task_id)
            except Exception:
                pass
            return serialize(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/kanban/tareas/{task_id}")
async def delete_kanban_tarea(task_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    try:
        async with pool.acquire() as conn:
            old = await conn.fetchrow("SELECT id_tecnico FROM kanban_tareas WHERE id=$1", task_id)
            result = await conn.execute("DELETE FROM kanban_tareas WHERE id=$1", task_id)
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Tarea no encontrada")
            if old and old['id_tecnico']:
                await _sync_tecnico_estado(conn, old['id_tecnico'])
            return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/kanban/metricas")
async def kanban_metricas():
    """Kanban metrics: throughput, flow efficiency, CFD data, control chart data."""
    pool = get_pool()
    if not pool:
        return {}
    try:
        async with pool.acquire() as conn:
            # Total by column
            col_counts = await conn.fetch(
                "SELECT columna, COUNT(*) as cnt FROM kanban_tareas GROUP BY columna"
            )
            # Throughput (completed per week, last 4 weeks)
            throughput = await conn.fetch("""
                SELECT DATE_TRUNC('week', fecha_cierre) as semana, COUNT(*) as completadas
                FROM kanban_tareas WHERE fecha_cierre IS NOT NULL
                GROUP BY DATE_TRUNC('week', fecha_cierre)
                ORDER BY semana DESC LIMIT 8
            """)
            # Lead time (creation to close) for completed tasks
            lead_times = await conn.fetch("""
                SELECT id, titulo, prioridad,
                       EXTRACT(EPOCH FROM (fecha_cierre - fecha_creacion))/3600 as lead_time_h,
                       EXTRACT(EPOCH FROM (fecha_cierre - COALESCE(fecha_inicio_ejecucion, fecha_creacion)))/3600 as cycle_time_h,
                       fecha_cierre
                FROM kanban_tareas
                WHERE fecha_cierre IS NOT NULL
                ORDER BY fecha_cierre DESC LIMIT 50
            """)
            # CFD data: daily cumulative count per column (last 30 days)
            cfd = await conn.fetch("""
                SELECT d.day::date as fecha,
                       SUM(CASE WHEN k.columna='Backlog' THEN 1 ELSE 0 END) as backlog,
                       SUM(CASE WHEN k.columna='Análisis' THEN 1 ELSE 0 END) as analisis,
                       SUM(CASE WHEN k.columna='En Progreso' THEN 1 ELSE 0 END) as en_progreso,
                       SUM(CASE WHEN k.columna='Code Review' THEN 1 ELSE 0 END) as code_review,
                       SUM(CASE WHEN k.columna='Testing' THEN 1 ELSE 0 END) as testing,
                       SUM(CASE WHEN k.columna='Despliegue' THEN 1 ELSE 0 END) as despliegue,
                       SUM(CASE WHEN k.columna='Bloqueado' THEN 1 ELSE 0 END) as bloqueado,
                       SUM(CASE WHEN k.columna='Completado' THEN 1 ELSE 0 END) as completado
                FROM generate_series(CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE, '1 day') d(day)
                CROSS JOIN kanban_tareas k
                WHERE k.fecha_creacion <= d.day + INTERVAL '1 day'
                  AND (k.fecha_cierre IS NULL OR k.fecha_cierre >= d.day)
                GROUP BY d.day ORDER BY d.day
            """)
            # Total counts
            total = await conn.fetchval("SELECT COUNT(*) FROM kanban_tareas")
            completadas = await conn.fetchval("SELECT COUNT(*) FROM kanban_tareas WHERE columna='Completado'")
            bloqueadas = await conn.fetchval("SELECT COUNT(*) FROM kanban_tareas WHERE columna='Bloqueado'")
            avg_lead = await conn.fetchval("""
                SELECT AVG(EXTRACT(EPOCH FROM (fecha_cierre - fecha_creacion))/3600)
                FROM kanban_tareas WHERE fecha_cierre IS NOT NULL
            """)
            avg_cycle = await conn.fetchval("""
                SELECT AVG(EXTRACT(EPOCH FROM (fecha_cierre - COALESCE(fecha_inicio_ejecucion, fecha_creacion)))/3600)
                FROM kanban_tareas WHERE fecha_cierre IS NOT NULL
            """)
            return {
                "total": total or 0,
                "completadas": completadas or 0,
                "bloqueadas": bloqueadas or 0,
                "avg_lead_time_h": round(float(avg_lead or 0), 1),
                "avg_cycle_time_h": round(float(avg_cycle or 0), 1),
                "flow_efficiency": round(float(avg_cycle or 0) / float(avg_lead or 1) * 100, 1) if avg_lead else 0,
                "col_counts": {r['columna']: r['cnt'] for r in col_counts},
                "throughput": [serialize(r) for r in throughput],
                "lead_times": [serialize(r) for r in lead_times],
                "cfd": [serialize(r) for r in cfd],
            }
    except Exception as e:
        logger.warning(f"DB error in /kanban/metricas: {e}")
        return {}


@app.get("/prediccion/demanda")
async def get_prediccion():
    """Simple linear trend forecast — no Prophet required."""
    import math
    historical = [12, 15, 11, 18, 14, 20, 17, 22, 19, 25, 21, 28]
    n = len(historical)
    x_mean = (n - 1) / 2
    y_mean = sum(historical) / n
    slope_num = sum((i - x_mean) * (historical[i] - y_mean) for i in range(n))
    slope_den = sum((i - x_mean) ** 2 for i in range(n))
    slope = slope_num / slope_den if slope_den != 0 else 1
    intercept = y_mean - slope * x_mean
    forecast = []
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    for i in range(6):
        val = round(intercept + slope * (n + i), 1)
        forecast.append({"mes": meses[(n + i) % 12], "incidencias_previstas": max(0, val)})
    return {
        "historico": [{"mes": meses[i % 12], "incidencias": historical[i]} for i in range(n)],
        "forecast": forecast,
        "slope": round(slope, 3),
        "modelo": "linear_trend",
    }


@app.get("/catalogo/incidencias")
async def get_catalogo_incidencias():
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM catalogo_incidencias ORDER BY area_afectada, incidencia")
                return [serialize(r) for r in rows]
        except Exception as e:
            logger.warning(f"DB error in /catalogo/incidencias: {e}")
    return []


@app.get("/incidencias")
async def get_incidencias(estado: Optional[str] = None, limit: int = 50):
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                if estado:
                    rows = await conn.fetch(
                        "SELECT * FROM incidencias_run WHERE estado=$1 ORDER BY timestamp_creacion DESC LIMIT $2",
                        estado, limit)
                else:
                    rows = await conn.fetch(
                        "SELECT * FROM incidencias_run ORDER BY timestamp_creacion DESC LIMIT $1", limit)
                result_inc = []
                for r in rows:
                    d = serialize(r)
                    if 'sla_limite' in d and d['sla_limite'] is not None:
                        d['sla_horas'] = float(d['sla_limite'])
                    if 'prioridad_ia' in d and 'prioridad' not in d:
                        d['prioridad'] = d['prioridad_ia']
                    result_inc.append(d)
                return result_inc
        except Exception as e:
            logger.warning(f"DB error in GET /incidencias: {e}")
    return []


class IncidenciaITSM(BaseModel):
    id_catalogo: Optional[int] = None
    descripcion: str
    prioridad: str = "P3"
    categoria: Optional[str] = None
    area_afectada: Optional[str] = None
    urgencia: str = "Media"
    impacto: str = "Medio"
    sla_limite: Optional[float] = None
    impacto_negocio: Optional[str] = None
    canal_entrada: str = "Portal ITSM"
    reportado_por: Optional[str] = None
    servicio_afectado: Optional[str] = None
    ci_afectado: Optional[str] = None
    notas_adicionales: Optional[str] = None


@app.post("/incidencias")
async def crear_incidencia(inc: IncidenciaITSM):
    inc_id = "INC-MOCK-NODB"  # F1.3b fallback si no hay pool
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                inc_id = await conn.fetchval("SELECT generar_ticket_id()")
                row = await conn.fetchrow(
                    """INSERT INTO incidencias_run
                       (ticket_id, incidencia_detectada, id_catalogo, prioridad_ia,
                        categoria, area_afectada, sla_limite, impacto_negocio,
                        urgencia, impacto, canal_entrada, reportado_por,
                        servicio_afectado, ci_afectado, notas_adicionales, estado)
                       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,'QUEUED')
                       RETURNING *""",
                    inc_id, inc.descripcion, inc.id_catalogo, inc.prioridad,
                    inc.categoria, inc.area_afectada,
                    inc.sla_limite, inc.impacto_negocio,
                    inc.urgencia, inc.impacto, inc.canal_entrada,
                    inc.reportado_por, inc.servicio_afectado,
                    inc.ci_afectado, inc.notas_adicionales,
                )
                return serialize(row)
        except Exception as e:
            logger.warning(f"DB error in POST /incidencias: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"ticket_id": inc_id, "estado": "QUEUED", "_mock": True}


class TecnicoCreate(BaseModel):
    id_recurso: str
    nombre: str
    nivel: str
    silo_especialidad: str
    skills_json: List[str] = []
    skill_principal: Optional[str] = None
    estado_run: Optional[str] = "DISPONIBLE"
    email: Optional[str] = None
    telefono: Optional[str] = None

class TecnicoUpdate(BaseModel):
    nombre: str
    nivel: str
    silo_especialidad: str
    skills_json: List[str] = []
    skill_principal: Optional[str] = None
    estado_run: Optional[str] = "DISPONIBLE"
    email: Optional[str] = None
    telefono: Optional[str] = None

class ProyectoUpdate(BaseModel):
    id_proyecto: str
    nombre: str
    prioridad: str
    prioridad_num: Optional[int] = 3
    estado: str
    horas_estimadas: int
    skill_requerida: Optional[str] = None

@app.post("/team/tecnicos")
async def crear_tecnico(t: TecnicoCreate):
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """INSERT INTO pmo_staff_skills
                       (id_recurso, nombre, nivel, silo_especialidad, skills_json,
                        skill_principal, total_skills, estado_run, email, telefono)
                       VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9,$10)
                       ON CONFLICT (id_recurso) DO NOTHING RETURNING *""",
                    t.id_recurso, t.nombre, t.nivel, t.silo_especialidad,
                    json.dumps(t.skills_json, ensure_ascii=False),
                    t.skill_principal, len(t.skills_json),
                    t.estado_run or "DISPONIBLE", t.email, t.telefono,
                )
                if row is None:
                    raise HTTPException(status_code=409, detail=f"El ID {t.id_recurso} ya existe")
                return serialize(row)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"DB error in POST /team/tecnicos: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"id_recurso": t.id_recurso, "nombre": t.nombre, "_mock": True}


@app.put("/team/tecnicos/{id_recurso}")
async def update_tecnico(id_recurso: str, t: TecnicoUpdate):
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """UPDATE pmo_staff_skills SET
                       nombre=$1, nivel=$2, silo_especialidad=$3,
                       skills_json=$4::jsonb, skill_principal=$5,
                       total_skills=$6, estado_run=$7, email=$9, telefono=$10
                       WHERE id_recurso=$8 RETURNING *""",
                    t.nombre, t.nivel, t.silo_especialidad,
                    json.dumps(t.skills_json, ensure_ascii=False),
                    t.skill_principal, len(t.skills_json),
                    t.estado_run or "DISPONIBLE", id_recurso,
                    t.email, t.telefono,
                )
                if row is None:
                    raise HTTPException(status_code=404, detail=f"Técnico {id_recurso} no encontrado")
                return serialize(row)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"DB error in PUT /team/tecnicos: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"id_recurso": id_recurso, "_mock": True}


@app.put("/cartera/proyectos")
async def update_proyecto(p: ProyectoUpdate):
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """UPDATE cartera_build SET
                       nombre_proyecto=$1, prioridad_estrategica=$2,
                       estado=$3, horas_estimadas=$4, skills_requeridas=$5,
                       fecha_ultima_modificacion=NOW()
                       WHERE id_proyecto=$6 RETURNING *""",
                    p.nombre, p.prioridad, p.estado,
                    p.horas_estimadas, p.skill_requerida, p.id_proyecto,
                )
                if row is None:
                    raise HTTPException(status_code=404, detail=f"Proyecto {p.id_proyecto} no encontrado")
                return serialize(row)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"DB error in PUT /cartera/proyectos: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"id_proyecto": p.id_proyecto, "_mock": True}


@app.post("/asignar/tecnico")
async def asignar_tecnico(body: AsignarTecnico):
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """UPDATE pmo_staff_skills
                       SET estado_run=$1, carga_actual=$2
                       WHERE id_recurso=$3""",
                    body.estado, body.carga_actual, body.id_tecnico,
                )
                return {"ok": True, "id_recurso": body.id_tecnico, "estado_run": body.estado}
        except Exception as e:
            logger.warning(f"DB error in POST /asignar/tecnico: {e}")
    return {"ok": True, "id_recurso": body.id_tecnico, "estado_run": body.estado, "_mock": True}


class AsignarTecnicoTarea(BaseModel):
    task_id: str
    id_recurso: str
    ticket_id: str = ""


@app.post("/asignar/tecnico/tarea")
async def asignar_tecnico_tarea(req: AsignarTecnicoTarea):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE kanban_tareas SET id_tecnico = $1
                WHERE id = $2
            """, req.id_recurso, req.task_id)
            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Tarea no encontrada")
            horas = await conn.fetchval(
                "SELECT COALESCE(horas_estimadas, 2) FROM kanban_tareas WHERE id = $1", req.task_id)
            await conn.execute("""
                UPDATE pmo_staff_skills SET carga_actual = LEAST(carga_actual + $1, 200)
                WHERE id_recurso = $2
            """, int(horas or 2), req.id_recurso)
            if req.ticket_id:
                await conn.execute("""
                    UPDATE incidencias_run SET tecnico_asignado = $1, timestamp_asignacion = now()
                    WHERE ticket_id = $2 AND tecnico_asignado IS NULL
                """, req.id_recurso, req.ticket_id)
            # Auto-crear sala de chat para tech dashboard
            try:
                tarea_info = await conn.fetchrow(
                    "SELECT titulo, tipo FROM kanban_tareas WHERE id = $1", req.task_id)
                nombre_tecnico = await conn.fetchval(
                    "SELECT nombre FROM pmo_staff_skills WHERE id_recurso = $1", req.id_recurso)
                tipo_sala = 'run' if req.ticket_id else 'build'
                ref_id = req.ticket_id if req.ticket_id else req.task_id
                sala_nombre = f"{ref_id} · {tarea_info['titulo'][:80]}" if tarea_info else ref_id
                sala_id = await conn.fetchval("""
                    INSERT INTO tech_chat_salas (tipo, id_referencia, nombre)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (tipo, id_referencia) DO UPDATE SET activa = TRUE
                    RETURNING id
                """, tipo_sala, ref_id, sala_nombre)
                if sala_id:
                    await conn.execute("""
                        INSERT INTO tech_chat_mensajes (id_sala, id_autor, rol_autor, mensaje)
                        VALUES ($1, $2, 'agente', $3)
                    """, sala_id, 'AG-002',
                        f"Asignada a {nombre_tecnico or req.id_recurso}.")
            except Exception:
                pass  # Non-critical
            # Hook: notificación al técnico asignado
            try:
                tech_user = await conn.fetchval(
                    "SELECT id_usuario FROM rbac_usuarios WHERE id_recurso=$1", req.id_recurso)
                if tech_user:
                    tit = tarea_info['titulo'][:100] if tarea_info else req.task_id
                    await crear_notificacion(
                        conn, tech_user, 'asignacion',
                        f'Nueva tarea asignada: {tit}',
                        f'Se te ha asignado la tarea {req.task_id}.',
                        'tarea', req.task_id)
            except Exception:
                pass
            return {"ok": True, "task_id": req.task_id, "id_recurso": req.id_recurso}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdateTaskMeta(BaseModel):
    task_id: str
    meta: dict


@app.post("/kanban/tareas/meta")
async def update_task_meta(req: UpdateTaskMeta):
    """Merge metadata into task description JSON"""
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            meta_json = json.dumps(req.meta, ensure_ascii=False)
            await conn.execute("""
                UPDATE kanban_tareas
                SET descripcion = (COALESCE(descripcion::jsonb, '{}'::jsonb) || $1::jsonb)::text
                WHERE id = $2
            """, meta_json, req.task_id)
            return {"ok": True, "task_id": req.task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class IncidenciaLive(BaseModel):
    ticket_id: str
    incidencia_detectada: str
    prioridad: str = "P4"
    sla_horas: float = 48
    canal_entrada: str = ""
    reportado_por: str = ""
    servicio_afectado: str = ""
    impacto_negocio: str = ""


@app.post("/incidencias/live")
async def crear_incidencia_live(req: IncidenciaLive):
    """
    DEPRECATED desde Deuda A.3 / F-ARQ02-05 (2026-04-09).

    Post-trigger F2.1, esta ruta es redundante: el trigger
    trg_run_to_live_insert ya crea la fila live al insertar en
    incidencias_run con datos más completos y precisos. El endpoint
    se mantiene como no-op idempotente (ON CONFLICT DO NOTHING) para
    consumidores externos legacy. El frontend ya no la invoca desde
    el flujo del formulario ITSM (itsmSubmitAndPipeline).
    """
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            # ARQ-02 F2.1 — el ticket debe existir en incidencias_run primero.
            # La FK + trigger AFTER INSERT ya crearon la fila en live, este
            # endpoint queda como no-op idempotente defensivo (ON CONFLICT DO
            # NOTHING absorbe la fila duplicada).
            exists = await conn.fetchval(
                "SELECT 1 FROM incidencias_run WHERE ticket_id = $1",
                req.ticket_id,
            )
            if not exists:
                raise HTTPException(
                    status_code=404,
                    detail=f"Ticket {req.ticket_id} no existe en incidencias_run. "
                           f"El panel live solo puede mostrar tickets ya creados en run."
                )
            sla_int = int(req.sla_horas)
            await conn.execute("""
                INSERT INTO incidencias_live
                (ticket_id, incidencia_detectada, prioridad, sla_horas, estado,
                 fecha_limite, canal_entrada, reportado_por, servicio_afectado, impacto_negocio)
                VALUES ($1, $2, $3, $4, 'IN_PROGRESS',
                 now() + make_interval(hours => $5), $6, $7, $8, $9)
                ON CONFLICT (ticket_id) DO NOTHING
            """, req.ticket_id, req.incidencia_detectada, req.prioridad,
                req.sla_horas, sla_int, req.canal_entrada, req.reportado_por,
                req.servicio_afectado, req.impacto_negocio)
            return {"ok": True, "ticket_id": req.ticket_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidencias/live")
async def listar_incidencias_live():
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM incidencias_live
                ORDER BY
                  CASE prioridad WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 4 END,
                  fecha_creacion DESC
            """)
            # H1: enriquecer incidencias_live con sla_horas REAL por prioridad
        # Mapeo estándar ITIL: P1=4h, P2=8h, P3=24h, P4=48h
        SLA_POR_PRIORIDAD = {'P1': 4, 'P2': 8, 'P3': 24, 'P4': 48}
        result_live = []
        for r in rows:
            d = dict(r)
            # 1) Intentar leer sla_limite real de incidencias_run
            sla_val = None
            if d.get('ticket_id'):
                sla_val = await conn.fetchval(
                    "SELECT sla_limite FROM incidencias_run WHERE ticket_id = $1",
                    d['ticket_id']
                )
            # 2) Si hay sla_limite numérico válido, usarlo
            if sla_val is not None and float(sla_val) > 0 and float(sla_val) < 200:
                d['sla_horas'] = float(sla_val)
            else:
                # 3) Fallback por prioridad (P1=4, P2=8, P3=24, P4=48)
                prio = (d.get('prioridad_ia') or d.get('prioridad') or 'P3').upper()
                d['sla_horas'] = SLA_POR_PRIORIDAD.get(prio, 24)
            # Mapear prioridad_ia -> prioridad para frontend
            if 'prioridad' not in d or not d.get('prioridad'):
                d['prioridad'] = d.get('prioridad_ia', 'P3')
            result_live.append(d)
            return result_live
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/incidencias/live/{ticket_id}")
async def cerrar_incidencia_live(ticket_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM incidencias_live WHERE ticket_id = $1", ticket_id)
            return {"ok": True, "deleted": ticket_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/incidencias/live/{ticket_id}/progreso")
async def actualizar_progreso_live(ticket_id: str, progreso: int = 0, tareas_completadas: int = 0, total_tareas: int = 0):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE incidencias_live
                SET progreso_pct = $2, tareas_completadas = $3, total_tareas = $4
                WHERE ticket_id = $1
            """, ticket_id, progreso, tareas_completadas, total_tareas)
            return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/directorio/buscar")
async def buscar_directorio(area: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id_directivo, nombre_completo, cargo, area, email, telefono
                FROM directorio_corporativo
                WHERE activo = true AND (
                    area ILIKE '%' || $1 || '%'
                    OR cargo ILIKE '%' || $1 || '%'
                    OR bio ILIKE '%' || $1 || '%'
                )
                ORDER BY nivel_organizativo ASC LIMIT 3
            """, area)
            return [dict(r) for r in rows]
    except Exception:
        return []


@app.post("/buffer/actualizar")
async def buffer_actualizar(body: BufferUpdate):
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE cartera_build SET estado='PAUSADO_POR_RIESGO_P1' WHERE id_proyecto=$1",
                    body.id_proyecto,
                )
                return {"ok": True, "id_proyecto": body.id_proyecto, "nuevo_estado": "PAUSADO_POR_RIESGO_P1"}
        except Exception as e:
            logger.warning(f"DB error in POST /buffer/actualizar: {e}")
    return {"ok": True, "id_proyecto": body.id_proyecto, "nuevo_estado": "PAUSADO_POR_RIESGO_P1", "_mock": True}


@app.post("/proyectos/crear")
async def crear_proyecto(proj: ProyectoCreate):
    proj_id = "PRJ" + str(uuid.uuid4())[:6].upper() + " - [PMO-NEW]"
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """INSERT INTO cartera_build
                       (id_proyecto, nombre_proyecto, prioridad_estrategica, estado,
                        horas_estimadas, skills_requeridas)
                       VALUES ($1,$2,$3,$4,$5,$6) RETURNING *""",
                    proj_id, proj.nombre, proj.prioridad,
                    proj.estado, proj.horas_estimadas, proj.skill_requerida,
                )
                return serialize(row)
        except Exception as e:
            logger.warning(f"DB error in POST /proyectos/crear: {e}")
    return {
        "id_proyecto": proj_id,
        "nombre_proyecto": proj.nombre,
        "prioridad_estrategica": proj.prioridad,
        "estado": proj.estado,
        "horas_estimadas": proj.horas_estimadas,
        "skills_requeridas": proj.skill_requerida,
        "_mock": True,
    }


# ── PMO Governance ───────────────────────────────────────────────────────────

@app.get("/pmo/managers")
async def get_pms(include_inactive: bool = False):
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                # F2: ocultar PMs inactivos (PM-001..PM-015 huérfanos) salvo override admin
                if include_inactive:
                    rows = await conn.fetch("SELECT * FROM pmo_project_managers ORDER BY nombre")
                else:
                    rows = await conn.fetch("SELECT * FROM pmo_project_managers WHERE activo = TRUE ORDER BY nombre")
                # C2: Estado PM dinámico per-schema
                result_pms = []
                for r in rows:
                    d = serialize(r)
                    pm_id = d.get('id_pm', '')
                    pm_nombre = d.get('nombre', '')
                    proj_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM pmo_governance_scoring "
                        "WHERE (id_pm = $1 OR id_pm = $2) "
                        "AND gate_status NOT IN ('COMPLETED','CERRADO')",
                        pm_id, pm_nombre
                    ) or 0
                    if proj_count >= 3:
                        d['estado'] = 'SOBRECARGADO'
                    elif proj_count == 2:
                        d['estado'] = 'CERCA_LIMITE'
                    elif proj_count == 1:
                        d['estado'] = 'ASIGNADO'
                    else:
                        d['estado'] = 'DISPONIBLE'
                    d['proyectos_activos'] = proj_count
                    d['carga'] = min(proj_count * 25, 100)
                    result_pms.append(d)
                return result_pms
        except Exception as e:
            logger.warning(f"DB error in /pmo/managers: {e}")
    return []


class PMCreate(BaseModel):
    id_pm: str
    nombre: str
    nivel: str
    especialidad: str
    skills_json: List[str] = []
    skill_principal: Optional[str] = None
    estado: Optional[str] = "DISPONIBLE"
    max_proyectos: int = 3
    email: Optional[str] = None
    telefono: Optional[str] = None
    certificaciones: List[str] = []


class PMUpdate(BaseModel):
    nombre: str
    nivel: str
    especialidad: str
    skills_json: List[str] = []
    skill_principal: Optional[str] = None
    estado: Optional[str] = "DISPONIBLE"
    max_proyectos: int = 3
    email: Optional[str] = None
    telefono: Optional[str] = None
    certificaciones: List[str] = []


@app.post("/pmo/managers")
async def create_pm(p: PMCreate):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO pmo_project_managers
                   (id_pm,nombre,nivel,especialidad,skills_json,skill_principal,
                    total_skills,estado,max_proyectos,email,telefono,certificaciones)
                VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9,$10,$11,$12)
                ON CONFLICT (id_pm) DO NOTHING RETURNING *""",
                p.id_pm, p.nombre, p.nivel, p.especialidad,
                json.dumps(p.skills_json), p.skill_principal, len(p.skills_json),
                p.estado, p.max_proyectos, p.email, p.telefono, p.certificaciones,
            )
            if not row:
                raise HTTPException(status_code=409, detail=f"PM {p.id_pm} ya existe")
            return serialize(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/pmo/managers/{id_pm}")
async def update_pm(id_pm: str, p: PMUpdate):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE pmo_project_managers SET
                   nombre=$1,nivel=$2,especialidad=$3,skills_json=$4::jsonb,
                   skill_principal=$5,total_skills=$6,estado=$7,max_proyectos=$8,
                   email=$9,telefono=$10,certificaciones=$11
                WHERE id_pm=$12 RETURNING *""",
                p.nombre, p.nivel, p.especialidad,
                json.dumps(p.skills_json), p.skill_principal, len(p.skills_json),
                p.estado, p.max_proyectos, p.email, p.telefono, p.certificaciones, id_pm,
            )
            if not row:
                raise HTTPException(status_code=404)
            return serialize(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pmo/governance")
async def get_governance():
    pool = get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT g.*, p.nombre_proyecto, pm.nombre as pm_nombre
                FROM pmo_governance_scoring g
                LEFT JOIN cartera_build p ON g.id_proyecto = p.id_proyecto
                LEFT JOIN pmo_project_managers pm ON g.id_pm = pm.id_pm
                ORDER BY g.total_score DESC
            """)
            return [serialize(r) for r in rows]
    except Exception as e:
        logger.warning(f"DB error in /pmo/governance: {e}")
        return []


@app.get("/pmo/governance/dashboard")
async def governance_dashboard():
    pool = get_pool()
    if not pool:
        return {}
    try:
        async with pool.acquire() as conn:
            total_pms = await conn.fetchval("SELECT COUNT(*) FROM pmo_project_managers")
            # P3-v2: PMs DISTINTOS con proyectos activos (via governance_scoring)
            asignados = await conn.fetchval(
                "SELECT COUNT(DISTINCT g.id_pm) FROM pmo_governance_scoring g "
                "WHERE g.id_pm IS NOT NULL AND g.gate_status NOT IN ('COMPLETED','CERRADO')"
            ) or 0
            # P3-v2: PMs sobrecargados (>=3 proyectos activos en governance)
            sobrecargados_rows = await conn.fetch(
                "SELECT id_pm, COUNT(*) as cnt FROM pmo_governance_scoring "
                "WHERE id_pm IS NOT NULL AND gate_status NOT IN ('COMPLETED','CERRADO') "
                "GROUP BY id_pm HAVING COUNT(*) >= 3"
            )
            sobrecargados = len(sobrecargados_rows)
            total_gov = await conn.fetchval("SELECT COUNT(*) FROM pmo_governance_scoring")
            avg_score = await conn.fetchval("SELECT AVG(total_score) FROM pmo_governance_scoring")
            avg_compliance = await conn.fetchval("SELECT AVG(compliance_pct) FROM pmo_governance_scoring")
            by_gate = await conn.fetch("SELECT gate_status, COUNT(*) as cnt FROM pmo_governance_scoring GROUP BY gate_status")
            by_gate_phase = await conn.fetch("SELECT current_gate, COUNT(*) as cnt FROM pmo_governance_scoring GROUP BY current_gate ORDER BY current_gate")
            total_changes = await conn.fetchval("SELECT SUM(change_requests) FROM pmo_governance_scoring")
            approved_changes = await conn.fetchval("SELECT SUM(change_approved) FROM pmo_governance_scoring")
            # P3-v2: Métricas per-schema
            proyectos_activos = await conn.fetchval(
                "SELECT COUNT(*) FROM cartera_build WHERE estado NOT IN ('cerrado')"
            ) or 0
            carga_media_pm = 0
            if asignados > 0 and proyectos_activos > 0:
                carga_media_pm = round(proyectos_activos / max(1, asignados) * 25, 1)
            return {
                "total_pms": total_pms or 0,
                "pms_asignados": asignados or 0,
                "pms_sobrecargados": sobrecargados or 0,
                "total_proyectos_gobernados": total_gov or 0,
                "avg_scoring": round(float(avg_score or 0), 1),
                "avg_compliance": round(float(avg_compliance or 0), 1),
                "by_gate_status": {r['gate_status']: r['cnt'] for r in by_gate},
                "by_gate_phase": {r['current_gate']: r['cnt'] for r in by_gate_phase},
                "total_change_requests": int(total_changes or 0),
                "change_approval_rate": round(int(approved_changes or 0) / max(1, int(total_changes or 1)) * 100, 1),
                "proyectos_activos_schema": proyectos_activos,
                "carga_media_pm": carga_media_pm,
            }
    except Exception as e:
        logger.warning(f"governance dashboard error: {e}")
        return {}


# ── Run Incident Plans (Buffer persistente) ──────────────────────────────────

@app.get("/run/plans")
async def get_run_plans():
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM itsm_form_drafts ORDER BY created_at DESC")
                return [serialize(r) for r in rows]
        except Exception as e:
            logger.warning(f"DB error in GET /run/plans: {e}")
    return []


class RunPlanCreate(BaseModel):
    id: Optional[str] = None
    ticket_id: Optional[str] = None
    nombre: str
    prioridad: str = "P3"
    area: Optional[str] = None
    sla_horas: Optional[float] = None
    plan_data: dict = {}


@app.post("/run/plans")
async def create_run_plan(p: RunPlanCreate):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            # Deuda A.1 / F-ARQ02-09: SEQUENCE atómica reemplaza uuid4().hex[:4]
            plan_id = p.id or await conn.fetchval("SELECT generar_draft_id()")
            row = await conn.fetchrow(
                """INSERT INTO itsm_form_drafts (id,ticket_id,nombre,prioridad,area,sla_horas,plan_data)
                VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb)
                ON CONFLICT (id) DO UPDATE SET plan_data=EXCLUDED.plan_data, nombre=EXCLUDED.nombre
                RETURNING *""",
                plan_id, p.ticket_id, p.nombre, p.prioridad, p.area, p.sla_horas,
                json.dumps(p.plan_data, ensure_ascii=False),
            )
            return serialize(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/run/plans/{plan_id}")
async def delete_run_plan(plan_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            result = await conn.execute("DELETE FROM itsm_form_drafts WHERE id=$1", plan_id)
            if result == "DELETE 0":
                raise HTTPException(status_code=404)
            return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Build Project Plans (Buffer persistente) ─────────────────────────────────

@app.get("/build/plans")
async def get_build_plans():
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM build_project_plans ORDER BY created_at DESC")
                return [serialize(r) for r in rows]
        except Exception as e:
            logger.warning(f"DB error in GET /build/plans: {e}")
    return []


class BuildPlanCreate(BaseModel):
    id: Optional[str] = None
    id_proyecto: Optional[str] = None
    nombre: str
    presupuesto: float = 0
    duracion_semanas: int = 20
    prioridad: str = "Media"
    plan_data: dict = {}


@app.post("/build/plans")
async def create_build_plan(p: BuildPlanCreate):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    plan_id = p.id or ("BLD-" + datetime.now().strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:4].upper())
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO build_project_plans (id,id_proyecto,nombre,presupuesto,duracion_semanas,prioridad,plan_data)
                VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb)
                ON CONFLICT (id) DO UPDATE SET plan_data=EXCLUDED.plan_data, nombre=EXCLUDED.nombre
                RETURNING *""",
                plan_id, p.id_proyecto, p.nombre, p.presupuesto, p.duracion_semanas, p.prioridad,
                json.dumps(p.plan_data, ensure_ascii=False),
            )
            return serialize(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/build/plans/{plan_id}")
async def get_build_plan(plan_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM build_project_plans WHERE id = $1", plan_id)
            if not row:
                raise HTTPException(status_code=404, detail="Plan not found")
            return serialize(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/build/plans/{plan_id}")
async def delete_build_plan(plan_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            result = await conn.execute("DELETE FROM build_project_plans WHERE id=$1", plan_id)
            if result == "DELETE 0":
                raise HTTPException(status_code=404)
            return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Pipeline Sessions (estado persistente) ─────────────────────────────────

@app.post("/pipeline/sessions")
async def save_pipeline_session(body: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    session_id = body.get("id") or str(uuid.uuid4())
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO pipeline_sessions (id, nombre_proyecto, estado, pausa_actual, pipeline_data, business_case, session_id, tiempo_acumulado_ms, coste_acumulado, agentes_completados)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, $9, $10::jsonb)
                ON CONFLICT (id) DO UPDATE SET
                    estado = $3, pausa_actual = $4, pipeline_data = $5::jsonb,
                    tiempo_acumulado_ms = $8, coste_acumulado = $9,
                    agentes_completados = $10::jsonb, updated_at = now()
            """, session_id, body.get("nombre", ""), body.get("estado", "EN_PROGRESO"),
                body.get("pausa_actual", 0),
                json.dumps(body.get("pipeline_data", {}), ensure_ascii=False, default=str),
                json.dumps(body.get("business_case", {}), ensure_ascii=False, default=str),
                body.get("session_id", ""),
                body.get("tiempo_ms", 0), float(body.get("coste", 0)),
                json.dumps(body.get("agentes_completados", [])))
        return {"id": session_id, "status": "saved"}
    except Exception as e:
        logger.warning(f"Error saving pipeline session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline/sessions")
async def list_pipeline_sessions():
    pool = get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, nombre_proyecto, estado, pausa_actual, tiempo_acumulado_ms, coste_acumulado, agentes_completados, created_at, updated_at
                FROM pipeline_sessions
                WHERE estado != 'LANZADO'
                ORDER BY updated_at DESC LIMIT 20
            """)
            return [serialize(r) for r in rows]
    except Exception as e:
        logger.warning(f"Error listing pipeline sessions: {e}")
        return []


@app.get("/pipeline/sessions/{sid}")
async def get_pipeline_session(sid: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM pipeline_sessions WHERE id = $1", sid)
            if not row:
                raise HTTPException(status_code=404, detail="Session not found")
            return serialize(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/pipeline/sessions/{sid}")
async def delete_pipeline_session(sid: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM pipeline_sessions WHERE id = $1", sid)
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/sessions/{sid}/populate")
async def populate_build_tables(sid: str):
    """Lee pipeline_data de una sesión y rellena las tablas BUILD individuales."""
    import json as _json
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)

    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM pipeline_sessions WHERE id = $1", sid)
        if not row:
            raise HTTPException(404, "Sesión no encontrada")

        pd = row["pipeline_data"]
        if isinstance(pd, str):
            pd = _json.loads(pd)

        id_proyecto = sid
        stats = {"subtasks": 0, "risks": 0, "stakeholders": 0, "sprints": 0, "sprint_items": 0, "quality_gates": 0}

        # Clean previous data for this project (idempotent re-run)
        for tbl in ['build_subtasks', 'build_risks', 'build_stakeholders', 'build_sprint_items', 'build_sprints', 'build_quality_gates']:
            await conn.execute(f"DELETE FROM {tbl} WHERE id_proyecto = $1", id_proyecto)

        def safe_parse(raw):
            if not raw:
                return None
            if isinstance(raw, dict):
                return raw
            if isinstance(raw, str):
                try:
                    clean = raw.replace("```json", "").replace("```", "").strip()
                    first = clean.find("{")
                    last = clean.rfind("}")
                    if first >= 0 and last > first:
                        return _json.loads(clean[first:last+1])
                    return _json.loads(clean)
                except Exception as e1:
                    # Retry with strict=False and encoding cleanup
                    # Retry: fix truncated JSON
                    try:
                        clean2 = raw.replace("```json", "").replace("```", "").strip()
                        f2 = clean2.find("{")
                        if f2 >= 0:
                            snippet = clean2[f2:]
                            try:
                                return _json.loads(snippet)
                            except _json.JSONDecodeError as je:
                                # Truncate before error, strip trailing comma, close all brackets
                                pos = je.pos if je.pos else len(snippet)
                                # Walk back to find last complete value
                                trunc = snippet[:pos]
                                # Remove trailing partial value
                                for ch in ['"', ',', ':', ' ', '\n', '\r', '\t']:
                                    trunc = trunc.rstrip(ch)
                                # Ensure arrays and objects are closed
                                ob = trunc.count('{') - trunc.count('}')
                                oa = trunc.count('[') - trunc.count(']')
                                trunc += ']' * max(0, oa) + '}' * max(0, ob)
                                return _json.loads(trunc)
                    except Exception as e2:
                        logger.warning(f"safe_parse retry fail: {e1} / {e2}")
                    return None
            return None

        # ── 1. SUBTASKS ──
        try:
            st = safe_parse(pd.get("subtasksResult"))
            if st:
                sbt = st.get("subtasks_by_task") or st.get("subtasks") or {}
                if isinstance(sbt, dict):
                    for task_id, items in sbt.items():
                        if not isinstance(items, list):
                            continue
                        for idx, item in enumerate(items):
                            if not isinstance(item, dict):
                                continue
                            await conn.execute("""
                                INSERT INTO build_subtasks (id_proyecto, id_tarea_padre, orden, titulo,
                                    descripcion_tecnica, tecnologia, skill_requerido,
                                    horas_estimadas, story_points)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                ON CONFLICT DO NOTHING
                            """, id_proyecto, task_id, idx + 1,
                                (item.get("titulo") or "")[:200],
                                (item.get("descripcion_tecnica") or "")[:500],
                                (item.get("tecnologia") or "")[:100],
                                (item.get("skill_requerido") or item.get("skill") or "")[:100],
                                float(item.get("horas_estimadas") or 0),
                                int(item.get("story_points") or 0))
                            stats["subtasks"] += 1
        except Exception as e:
            logger.warning(f"populate subtasks error: {e}")

        # ── 2. RISKS ──
        try:
            rk = safe_parse(pd.get("risksResult"))
            if rk:
                risks = rk.get("risks") or rk.get("riesgos") or []
                if isinstance(risks, list):
                    for r in risks:
                        if not isinstance(r, dict):
                            continue
                        await conn.execute("""
                            INSERT INTO build_risks (id_proyecto, descripcion,
                                probabilidad, impacto, categoria,
                                plan_mitigacion, plan_contingencia, responsable, trigger_evento)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            ON CONFLICT DO NOTHING
                        """, id_proyecto,
                            (r.get("descripcion") or "")[:500],
                            int(r.get("probabilidad") or 3),
                            int(r.get("impacto") or 3),
                            (r.get("categoria") or "Técnico")[:100],
                            (r.get("plan_mitigacion") or "")[:500],
                            (r.get("plan_contingencia") or "")[:500],
                            (r.get("responsable") or "")[:100],
                            (r.get("trigger_evento") or r.get("trigger") or "")[:500])
                        stats["risks"] += 1
        except Exception as e:
            logger.warning(f"populate risks error: {e}")

        # ── 3. STAKEHOLDERS ──
        try:
            sk = safe_parse(pd.get("stakeholdersResult"))
            if sk:
                stks = sk.get("stakeholders") or sk.get("interesados") or []
                if isinstance(stks, list):
                    for s in stks:
                        if not isinstance(s, dict):
                            continue
                        await conn.execute("""
                            INSERT INTO build_stakeholders (id_proyecto, nombre,
                                cargo, area, nivel_poder, nivel_interes,
                                estrategia, rol_raci, frecuencia_comunicacion, canal)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                            ON CONFLICT DO NOTHING
                        """, id_proyecto,
                            (s.get("nombre") or "")[:200],
                            (s.get("cargo") or "")[:200],
                            (s.get("area") or "")[:100],
                            int(s.get("nivel_poder") or s.get("poder") or 3),
                            int(s.get("nivel_interes") or s.get("interes") or 3),
                            (s.get("estrategia") or "Monitorizar")[:200],
                            (s.get("raci") or s.get("rol_raci") or "I")[:10],
                            (s.get("frecuencia_comunicacion") or s.get("frecuencia") or "Mensual")[:50],
                            (s.get("canal") or "Email")[:50])
                        stats["stakeholders"] += 1
        except Exception as e:
            logger.warning(f"populate stakeholders error: {e}")

        # ── 4. SPRINTS + SPRINT ITEMS ──
        try:
            pl = safe_parse(pd.get("planResult"))
            if pl:
                sprints = pl.get("sprints") or []
                if isinstance(sprints, list):
                    for sp in sprints:
                        if not isinstance(sp, dict):
                            continue
                        sprint_num = int(sp.get("numero") or 0)
                        sprint_id = f"{id_proyecto}-S{sprint_num}"
                        await conn.execute("""
                            INSERT INTO build_sprints (id, id_proyecto, sprint_number,
                                nombre, sprint_goal, story_points_planificados)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT DO NOTHING
                        """, sprint_id, id_proyecto, sprint_num,
                            f"Sprint {sprint_num}",
                            (sp.get("goal") or "")[:200],
                            int(sp.get("story_points") or 0))
                        stats["sprints"] += 1

                        items = sp.get("items") or sp.get("backlog") or []
                        if isinstance(items, list):
                            for idx, it in enumerate(items):
                                if not isinstance(it, dict):
                                    continue
                                item_key = it.get("id") or f"PROJ-{sprint_num:02d}{idx+1:02d}"
                                await conn.execute("""
                                    INSERT INTO build_sprint_items (id_proyecto, id_sprint,
                                        sprint_number, item_key, tipo, titulo, descripcion,
                                        silo, prioridad, story_points, subtareas_total)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                    ON CONFLICT DO NOTHING
                                """, id_proyecto, sprint_id, sprint_num,
                                    item_key[:50],
                                    (it.get("tipo") or "TASK")[:50],
                                    (it.get("titulo") or it.get("nombre") or "")[:200],
                                    (it.get("descripcion") or "")[:500],
                                    (it.get("silo") or "")[:100],
                                    (it.get("prioridad") or "Media")[:50],
                                    int(it.get("story_points") or it.get("pts") or 0),
                                    int(it.get("subtareas_total") or 0))
                                stats["sprint_items"] += 1
        except Exception as e:
            logger.warning(f"populate sprints error: {e}")

        # ── 5. QUALITY GATES ──
        try:
            qg = safe_parse(pd.get("qualityResult"))
            if qg:
                gates = qg.get("gates") or qg.get("quality_gates") or []
                if isinstance(gates, list):
                    for g in gates:
                        if not isinstance(g, dict):
                            continue
                        await conn.execute("""
                            INSERT INTO build_quality_gates (id_proyecto, fase,
                                gate_name, criterios_json, checklist_json,
                                responsable_qa, estado)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            ON CONFLICT DO NOTHING
                        """, id_proyecto,
                            (g.get("fase") or g.get("gate") or "")[:20],
                            (g.get("gate_name") or g.get("nombre") or "")[:200],
                            _json.dumps(g.get("criterios") or []),
                            _json.dumps(g.get("checklist") or []),
                            (g.get("responsable_qa") or "")[:100],
                            (g.get("estado") or "PENDING")[:50])
                        stats["quality_gates"] += 1
        except Exception as e:
            logger.warning(f"populate quality_gates error: {e}")

    return {"ok": True, "id_proyecto": id_proyecto, "stats": stats}


# =============================================
# BUILD PIPELINE v2.0 — Endpoints
# =============================================

# --- BUILD SUBTASKS (AG-013 Task Decomposer) ---

@app.get("/build/subtasks/{id_proyecto}")
async def get_build_subtasks(id_proyecto: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM build_subtasks WHERE id_proyecto = $1 ORDER BY id_tarea_padre, orden",
            id_proyecto)
        return [dict(r) for r in rows]


@app.post("/build/subtasks")
async def create_build_subtasks(data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        subtasks = data.get("subtasks", [])
        created = []
        for st in subtasks:
            row = await conn.fetchrow("""
                INSERT INTO build_subtasks (id_proyecto, id_tarea_padre, titulo,
                    descripcion_tecnica, tecnologia, componente, integracion_con,
                    horas_estimadas, skill_requerido, criterio_exito, orden, story_points)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                RETURNING *
            """, data.get("id_proyecto"), st.get("id_tarea_padre"), st.get("titulo"),
                st.get("descripcion_tecnica"), st.get("tecnologia"), st.get("componente"),
                st.get("integracion_con"), st.get("horas_estimadas", 0),
                st.get("skill_requerido"), st.get("criterio_exito"),
                st.get("orden", 0), st.get("story_points", 0))
            created.append(dict(row))
        return {"ok": True, "count": len(created), "subtasks": created}


@app.delete("/build/subtasks/{subtask_id}")
async def delete_build_subtask(subtask_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM build_subtasks WHERE id = $1", subtask_id)
        return {"deleted": True}


# --- BUILD RISKS (AG-014 Risk Analyzer) ---

@app.get("/build/risks/{id_proyecto}")
async def get_build_risks(id_proyecto: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM build_risks WHERE id_proyecto = $1 ORDER BY score DESC",
            id_proyecto)
        return [dict(r) for r in rows]


@app.post("/build/risks")
async def create_build_risks(data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        risks = data.get("risks", [])
        created = []
        for rk in risks:
            row = await conn.fetchrow("""
                INSERT INTO build_risks (id_proyecto, descripcion, categoria,
                    probabilidad, impacto, plan_mitigacion, plan_contingencia,
                    responsable, trigger_evento, estado)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                RETURNING *
            """, data.get("id_proyecto"), rk.get("descripcion"), rk.get("categoria", "Técnico"),
                rk.get("probabilidad", 3), rk.get("impacto", 3),
                rk.get("plan_mitigacion"), rk.get("plan_contingencia"),
                rk.get("responsable"), rk.get("trigger_evento"),
                rk.get("estado", "ABIERTO"))
            created.append(dict(row))
        return {"ok": True, "count": len(created), "risks": created}


@app.put("/build/risks/{risk_id}")
async def update_build_risk(risk_id: str, data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        sets = []
        vals = [risk_id]
        idx = 2
        for field in ["descripcion", "categoria", "probabilidad", "impacto",
                       "plan_mitigacion", "plan_contingencia", "responsable",
                       "trigger_evento", "estado"]:
            if field in data:
                sets.append(f"{field} = ${idx}")
                vals.append(data[field])
                idx += 1
        if sets:
            await conn.execute(
                f"UPDATE build_risks SET {', '.join(sets)} WHERE id = $1", *vals)
        row = await conn.fetchrow("SELECT * FROM build_risks WHERE id = $1", risk_id)
        return dict(row) if row else {"error": "not found"}


@app.delete("/build/risks/{risk_id}")
async def delete_build_risk(risk_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM build_risks WHERE id = $1", risk_id)
        return {"deleted": True}


# --- BUILD STAKEHOLDERS (AG-015 Stakeholder Map) ---

@app.get("/build/stakeholders/{id_proyecto}")
async def get_build_stakeholders(id_proyecto: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT * FROM build_stakeholders WHERE id_proyecto = $1
               ORDER BY nivel_poder DESC, nivel_interes DESC""",
            id_proyecto)
        return [dict(r) for r in rows]


@app.post("/build/stakeholders")
async def create_build_stakeholders(data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        stakeholders = data.get("stakeholders", [])
        created = []
        for sh in stakeholders:
            row = await conn.fetchrow("""
                INSERT INTO build_stakeholders (id_proyecto, nombre, cargo, area,
                    nivel_poder, nivel_interes, estrategia, rol_raci,
                    frecuencia_comunicacion, canal, id_directivo)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                RETURNING *
            """, data.get("id_proyecto"), sh.get("nombre"), sh.get("cargo"),
                sh.get("area"), sh.get("nivel_poder", 3), sh.get("nivel_interes", 3),
                sh.get("estrategia", "Monitorizar"), sh.get("rol_raci", "I"),
                sh.get("frecuencia_comunicacion", "Mensual"),
                sh.get("canal", "Email"), sh.get("id_directivo"))
            created.append(dict(row))
        return {"ok": True, "count": len(created), "stakeholders": created}


@app.delete("/build/stakeholders/{stakeholder_id}")
async def delete_build_stakeholder(stakeholder_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM build_stakeholders WHERE id = $1", stakeholder_id)
        return {"deleted": True}


# --- BUILD QUALITY GATES (AG-017 Quality Gate) ---

@app.get("/build/quality-gates/{id_proyecto}")
async def get_build_quality_gates(id_proyecto: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM build_quality_gates WHERE id_proyecto = $1 ORDER BY fase",
            id_proyecto)
        return [dict(r) for r in rows]


@app.post("/build/quality-gates")
async def create_build_quality_gates(data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        gates = data.get("gates", [])
        created = []
        for gt in gates:
            row = await conn.fetchrow("""
                INSERT INTO build_quality_gates (id_proyecto, fase, gate_name,
                    criterios_json, checklist_json, dod_json, responsable_qa, estado)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                RETURNING *
            """, data.get("id_proyecto"), gt.get("fase"), gt.get("gate_name"),
                json.dumps(gt.get("criterios", [])),
                json.dumps(gt.get("checklist", [])),
                json.dumps(gt.get("dod", [])),
                gt.get("responsable_qa"), gt.get("estado", "PENDING"))
            created.append(dict(row))
        return {"ok": True, "count": len(created), "gates": created}


@app.put("/build/quality-gates/{gate_id}")
async def update_build_quality_gate(gate_id: str, data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        sets = []
        vals = [gate_id]
        idx = 2
        for field in ["estado", "responsable_qa", "fecha_revision", "notas"]:
            if field in data:
                sets.append(f"{field} = ${idx}")
                vals.append(data[field])
                idx += 1
        for jfield in ["criterios_json", "checklist_json", "dod_json"]:
            if jfield in data:
                sets.append(f"{jfield} = ${idx}")
                vals.append(json.dumps(data[jfield]))
                idx += 1
        if sets:
            await conn.execute(
                f"UPDATE build_quality_gates SET {', '.join(sets)} WHERE id = $1", *vals)
        row = await conn.fetchrow("SELECT * FROM build_quality_gates WHERE id = $1", gate_id)
        return dict(row) if row else {"error": "not found"}


# --- BUILD LIVE (Sidebar proyectos vivos) ---

@app.get("/build/live")
async def get_build_live():
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM build_live ORDER BY fecha_inicio DESC")
        return [dict(r) for r in rows]


@app.post("/build/live")
async def create_build_live(data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO build_live (id_proyecto, nombre, pm_asignado, prioridad,
                estado, fecha_fin_prevista, total_tareas, total_sprints,
                presupuesto_bac, risk_score, gate_actual, story_points_total)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            ON CONFLICT (id_proyecto) DO NOTHING
            RETURNING *
        """, data.get("id_proyecto"), data.get("nombre"), data.get("pm_asignado"),
            data.get("prioridad", "Media"), data.get("estado", "PLANIFICACION"),
            data.get("fecha_fin_prevista"), data.get("total_tareas", 0),
            data.get("total_sprints", 16), data.get("presupuesto_bac", 0),
            data.get("risk_score", 0), data.get("gate_actual", "G2-PLANIFICACION"),
            data.get("story_points_total", 0))
        return dict(row) if row else {"ok": True, "exists": True}


@app.put("/build/live/{id_proyecto}/progreso")
async def update_build_live_progress(id_proyecto: str, data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        sets = []
        vals = [id_proyecto]
        idx = 2
        for field in ["progreso_pct", "tareas_completadas", "sprint_actual",
                       "presupuesto_consumido", "gate_actual", "estado",
                       "story_points_completados", "velocity_media"]:
            if field in data:
                sets.append(f"{field} = ${idx}")
                vals.append(data[field])
                idx += 1
        if sets:
            await conn.execute(
                f"UPDATE build_live SET {', '.join(sets)} WHERE id_proyecto = $1", *vals)
        row = await conn.fetchrow("SELECT * FROM build_live WHERE id_proyecto = $1", id_proyecto)
        return dict(row) if row else {"error": "not found"}


@app.delete("/build/live/{id_proyecto}")
async def delete_build_live(id_proyecto: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM build_live WHERE id_proyecto = $1", id_proyecto)
        return {"deleted": True}


# --- BUILD SPRINTS (Scrum framework) ---

@app.get("/build/sprints/{id_proyecto}")
async def get_build_sprints(id_proyecto: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM build_sprints WHERE id_proyecto = $1 ORDER BY sprint_number",
            id_proyecto)
        return [dict(r) for r in rows]


@app.post("/build/sprints")
async def create_build_sprints(data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        sprints = data.get("sprints", [])
        created = []
        for sp in sprints:
            row = await conn.fetchrow("""
                INSERT INTO build_sprints (id_proyecto, sprint_number, nombre,
                    sprint_goal, fecha_inicio, fecha_fin,
                    story_points_planificados, estado)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                RETURNING *
            """, data.get("id_proyecto"), sp.get("sprint_number"),
                sp.get("nombre"), sp.get("sprint_goal"),
                sp.get("fecha_inicio"), sp.get("fecha_fin"),
                sp.get("story_points_planificados", 0),
                sp.get("estado", "PLANIFICADO"))
            created.append(dict(row))
        return {"ok": True, "count": len(created), "sprints": created}


@app.put("/build/sprints/{sprint_id}")
async def update_build_sprint(sprint_id: str, data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        sets = []
        vals = [sprint_id]
        idx = 2
        for field in ["estado", "story_points_completados", "velocity", "notas_retro"]:
            if field in data:
                sets.append(f"{field} = ${idx}")
                vals.append(data[field])
                idx += 1
        if "burndown_data" in data:
            sets.append(f"burndown_data = ${idx}")
            vals.append(json.dumps(data["burndown_data"]))
            idx += 1
        if sets:
            await conn.execute(
                f"UPDATE build_sprints SET {', '.join(sets)} WHERE id = $1", *vals)
        row = await conn.fetchrow("SELECT * FROM build_sprints WHERE id = $1", sprint_id)
        return dict(row) if row else {"error": "not found"}


# --- BUILD SPRINT ITEMS (Scrum board items) ---

@app.get("/build/sprint-items/{id_proyecto}")
async def get_build_sprint_items(id_proyecto: str, sprint_number: int = None):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        if sprint_number:
            rows = await conn.fetch(
                """SELECT * FROM build_sprint_items
                   WHERE id_proyecto = $1 AND sprint_number = $2
                   ORDER BY orden_backlog""",
                id_proyecto, sprint_number)
        else:
            rows = await conn.fetch(
                "SELECT * FROM build_sprint_items WHERE id_proyecto = $1 ORDER BY orden_backlog",
                id_proyecto)
        return [dict(r) for r in rows]


@app.post("/build/sprint-items")
async def create_build_sprint_items(data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        items = data.get("items", [])
        created = []
        for it in items:
            row = await conn.fetchrow("""
                INSERT INTO build_sprint_items (id_proyecto, id_sprint, sprint_number,
                    item_key, tipo, titulo, descripcion, silo, prioridad,
                    story_points, estado, id_tecnico, nombre_tecnico,
                    subtareas_total, id_tarea_padre, horas_estimadas,
                    criterios_aceptacion, dod_checklist, orden_backlog)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19)
                RETURNING *
            """, data.get("id_proyecto"), it.get("id_sprint"), it.get("sprint_number"),
                it.get("item_key"), it.get("tipo", "TASK"), it.get("titulo"),
                it.get("descripcion"), it.get("silo"), it.get("prioridad", "Media"),
                it.get("story_points", 0), it.get("estado", "TODO"),
                it.get("id_tecnico"), it.get("nombre_tecnico"),
                it.get("subtareas_total", 0), it.get("id_tarea_padre"),
                it.get("horas_estimadas", 0),
                json.dumps(it.get("criterios_aceptacion", [])),
                json.dumps(it.get("dod_checklist", [])),
                it.get("orden_backlog", 0))
            created.append(dict(row))
        return {"ok": True, "count": len(created), "items": created}


@app.put("/build/sprint-items/{item_id}")
async def update_build_sprint_item(item_id: str, data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        sets = []
        vals = [item_id]
        idx = 2
        for field in ["estado", "id_tecnico", "nombre_tecnico", "sprint_number",
                       "subtareas_completadas", "horas_reales", "bloqueador",
                       "prioridad", "story_points"]:
            if field in data:
                sets.append(f"{field} = ${idx}")
                vals.append(data[field])
                idx += 1
        for jfield in ["criterios_aceptacion", "dod_checklist"]:
            if jfield in data:
                sets.append(f"{jfield} = ${idx}")
                vals.append(json.dumps(data[jfield]))
                idx += 1
        if sets:
            await conn.execute(
                f"UPDATE build_sprint_items SET {', '.join(sets)} WHERE id = $1", *vals)
        row = await conn.fetchrow("SELECT * FROM build_sprint_items WHERE id = $1", item_id)
        return dict(row) if row else {"error": "not found"}


@app.delete("/build/sprint-items/{item_id}")
async def delete_build_sprint_item(item_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM build_sprint_items WHERE id = $1", item_id)
        return {"deleted": True}


# --- PM CANDIDATES (AG-006 mejorado) ---

@app.get("/pmo/managers/candidates")
async def get_pm_candidates(skills: str = "", prioridad: str = "Media"):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id_pm, nombre, nivel, especialidad, skills_json,
                   estado, max_proyectos, certificaciones,
                   scoring_promedio, proyectos_completados, proyectos_activos,
                   tasa_exito, carga_actual, email, telefono
            FROM pmo_project_managers
            WHERE activo = TRUE
            AND estado IN ('DISPONIBLE', 'ASIGNADO')
            AND proyectos_activos < max_proyectos
            ORDER BY tasa_exito DESC, carga_actual ASC
            LIMIT 5
        """)
        return [dict(r) for r in rows]


# --- ADVISOR CHAT (AG-018 Governance Advisor) ---

@app.post("/build/advisor/chat")
async def build_advisor_chat(data: dict):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    session_id = data.get("session_id", "")
    message = data.get("message", "")
    context = data.get("context", {})
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO agent_conversations (session_id, agent_id, agent_name,
                role, content, metadata)
            VALUES ($1, 'AG-018', 'Governance Advisor', 'user', $2, $3)
        """, session_id, message, json.dumps(context))
    system_prompt = "Eres AG-018 Governance Advisor de Cognitive PMO.\n" \
        "Tu rol es asistir al gobernador durante las pausas de gobernanza del pipeline BUILD.\n\n" \
        "CONTEXTO ACTUAL DEL PROYECTO:\n" + json.dumps(context, indent=2, ensure_ascii=False) + "\n\n" \
        "REGLAS:\n- Responde en español profesional pero cercano\n" \
        "- Usa datos reales del contexto (no inventes)\n" \
        "- Sé conciso pero completo (máx 200 palabras)\n" \
        "- Si no sabes algo, dilo claramente"
    try:
        from llm_provider import get_provider
        provider = get_provider("anthropic")
        resp = await provider.create_message(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": message}]
        )
        reply = resp.text or "Error al procesar"
    except Exception as e:
        reply = f"Error de conexión con AG-018: {str(e)}"
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO agent_conversations (session_id, agent_id, agent_name,
                role, content)
            VALUES ($1, 'AG-018', 'Governance Advisor', 'assistant', $2)
        """, session_id, reply)
    return {"reply": reply, "agent": "AG-018", "session_id": session_id}


@app.get("/build/advisor/history/{session_id}")
async def get_advisor_history(session_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT role, content, created_at FROM agent_conversations
            WHERE session_id = $1 AND agent_id = 'AG-018'
            ORDER BY created_at ASC
        """, session_id)
        return [dict(r) for r in rows]


# ── Presupuestos ─────────────────────────────────────────────────────────────

class PresupuestoCreate(BaseModel):
    id_presupuesto: str
    id_proyecto: str
    nombre_presupuesto: str
    version: int = 1
    estado: str = "BORRADOR"
    responsable: str
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    moneda: str = "EUR"
    horas_internas: float = 0
    tarifa_hora_interna: float = 85.0
    proveedores_externos: List[Dict] = []
    opex_licencias_sw: float = 0
    opex_cloud_infra: float = 0
    opex_mantenimiento: float = 0
    opex_consumibles: float = 0
    opex_formacion: float = 0
    opex_otros: float = 0
    capex_hardware: float = 0
    capex_equipamiento: float = 0
    capex_infraestructura: float = 0
    capex_software: float = 0
    capex_otros: float = 0
    rrhh_reclutamiento: float = 0
    rrhh_formacion: float = 0
    rrhh_hr_admin: float = 0
    rrhh_viajes_dietas: float = 0
    rrhh_otros: float = 0
    reserva_contingencia_pct: float = 10.0
    reserva_gestion_pct: float = 5.0
    aprobado_por: Optional[str] = None
    notas: Optional[str] = None

class PresupuestoUpdate(PresupuestoCreate):
    pass

def _pres_totals(p: PresupuestoCreate):
    tl = round(p.horas_internas * p.tarifa_hora_interna, 2)
    tp = round(sum(x.get("total", 0) for x in p.proveedores_externos), 2)
    to = round(p.opex_licencias_sw + p.opex_cloud_infra + p.opex_mantenimiento + p.opex_consumibles + p.opex_formacion + p.opex_otros, 2)
    tc = round(p.capex_hardware + p.capex_equipamiento + p.capex_infraestructura + p.capex_software + p.capex_otros, 2)
    tr = round(p.rrhh_reclutamiento + p.rrhh_formacion + p.rrhh_hr_admin + p.rrhh_viajes_dietas + p.rrhh_otros, 2)
    sub = tl + tp + to + tc + tr
    tres = round(sub * (p.reserva_contingencia_pct + p.reserva_gestion_pct) / 100, 2)
    bac = round(sub + tres, 2)
    return tl, tp, to, tc, tr, tres, bac

@app.get("/presupuestos")
async def get_presupuestos():
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                        SELECT p.*, cb.nombre_proyecto
                        FROM presupuestos p
                        LEFT JOIN cartera_build cb ON p.id_proyecto = cb.id_proyecto
                        ORDER BY p.created_at DESC
                    """)
                return [serialize(r) for r in rows]
        except Exception as e:
            logger.warning(f"DB error in GET /presupuestos: {e}")
    return []

@app.post("/presupuestos")
async def crear_presupuesto(p: PresupuestoCreate):
    tl, tp, to, tc, tr, tres, bac = _pres_totals(p)
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """INSERT INTO presupuestos (
                        id_presupuesto,id_proyecto,nombre_presupuesto,version,estado,responsable,
                        fecha_inicio,fecha_fin,moneda,horas_internas,tarifa_hora_interna,
                        proveedores_externos,
                        opex_licencias_sw,opex_cloud_infra,opex_mantenimiento,opex_consumibles,opex_formacion,opex_otros,
                        capex_hardware,capex_equipamiento,capex_infraestructura,capex_software,capex_otros,
                        rrhh_reclutamiento,rrhh_formacion,rrhh_hr_admin,rrhh_viajes_dietas,rrhh_otros,
                        reserva_contingencia_pct,reserva_gestion_pct,
                        total_labor,total_proveedores,total_opex,total_capex,total_rrhh,total_reservas,bac_total,
                        aprobado_por,notas
                    ) VALUES (
                        $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12::jsonb,
                        $13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,
                        $24,$25,$26,$27,$28,$29,$30,$31,$32,$33,$34,$35,$36,$37,$38,$39
                    ) ON CONFLICT (id_presupuesto) DO NOTHING RETURNING *""",
                    p.id_presupuesto, p.id_proyecto, p.nombre_presupuesto, p.version, p.estado, p.responsable,
                    date.fromisoformat(p.fecha_inicio) if p.fecha_inicio else None,
                    date.fromisoformat(p.fecha_fin) if p.fecha_fin else None,
                    p.moneda, p.horas_internas, p.tarifa_hora_interna,
                    json.dumps(p.proveedores_externos),
                    p.opex_licencias_sw, p.opex_cloud_infra, p.opex_mantenimiento, p.opex_consumibles, p.opex_formacion, p.opex_otros,
                    p.capex_hardware, p.capex_equipamiento, p.capex_infraestructura, p.capex_software, p.capex_otros,
                    p.rrhh_reclutamiento, p.rrhh_formacion, p.rrhh_hr_admin, p.rrhh_viajes_dietas, p.rrhh_otros,
                    p.reserva_contingencia_pct, p.reserva_gestion_pct,
                    tl, tp, to, tc, tr, tres, bac, p.aprobado_por, p.notas,
                )
                if row is None:
                    raise HTTPException(status_code=409, detail=f"ID {p.id_presupuesto} ya existe")
                return serialize(row)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"DB error in POST /presupuestos: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"id_presupuesto": p.id_presupuesto, "bac_total": bac, "_mock": True}

@app.put("/presupuestos/{id_presupuesto}")
async def update_presupuesto(id_presupuesto: str, p: PresupuestoUpdate):
    tl, tp, to, tc, tr, tres, bac = _pres_totals(p)
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """UPDATE presupuestos SET
                        id_proyecto=$2,nombre_presupuesto=$3,version=$4,estado=$5,responsable=$6,
                        fecha_inicio=$7,fecha_fin=$8,moneda=$9,horas_internas=$10,tarifa_hora_interna=$11,
                        proveedores_externos=$12::jsonb,
                        opex_licencias_sw=$13,opex_cloud_infra=$14,opex_mantenimiento=$15,opex_consumibles=$16,opex_formacion=$17,opex_otros=$18,
                        capex_hardware=$19,capex_equipamiento=$20,capex_infraestructura=$21,capex_software=$22,capex_otros=$23,
                        rrhh_reclutamiento=$24,rrhh_formacion=$25,rrhh_hr_admin=$26,rrhh_viajes_dietas=$27,rrhh_otros=$28,
                        reserva_contingencia_pct=$29,reserva_gestion_pct=$30,
                        total_labor=$31,total_proveedores=$32,total_opex=$33,total_capex=$34,total_rrhh=$35,total_reservas=$36,bac_total=$37,
                        aprobado_por=$38,notas=$39,updated_at=NOW()
                    WHERE id_presupuesto=$1 RETURNING *""",
                    id_presupuesto, p.id_proyecto, p.nombre_presupuesto, p.version, p.estado, p.responsable,
                    date.fromisoformat(p.fecha_inicio) if p.fecha_inicio else None,
                    date.fromisoformat(p.fecha_fin) if p.fecha_fin else None,
                    p.moneda, p.horas_internas, p.tarifa_hora_interna,
                    json.dumps(p.proveedores_externos),
                    p.opex_licencias_sw, p.opex_cloud_infra, p.opex_mantenimiento, p.opex_consumibles, p.opex_formacion, p.opex_otros,
                    p.capex_hardware, p.capex_equipamiento, p.capex_infraestructura, p.capex_software, p.capex_otros,
                    p.rrhh_reclutamiento, p.rrhh_formacion, p.rrhh_hr_admin, p.rrhh_viajes_dietas, p.rrhh_otros,
                    p.reserva_contingencia_pct, p.reserva_gestion_pct,
                    tl, tp, to, tc, tr, tres, bac, p.aprobado_por, p.notas,
                )
                if row is None:
                    raise HTTPException(status_code=404, detail=f"Presupuesto {id_presupuesto} no encontrado")
                return serialize(row)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"DB error in PUT /presupuestos: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"id_presupuesto": id_presupuesto, "_mock": True}

@app.delete("/presupuestos/{id_presupuesto}")
async def delete_presupuesto(id_presupuesto: str):
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                result = await conn.execute("DELETE FROM presupuestos WHERE id_presupuesto=$1", id_presupuesto)
                if result == "DELETE 0":
                    raise HTTPException(status_code=404, detail=f"Presupuesto {id_presupuesto} no encontrado")
                return {"ok": True}
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"DB error in DELETE /presupuestos: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True, "_mock": True}


# ── Flowise ELIMINADO — Ahora se usan agentes nativos Claude (agents/) ──


# ── Documentación Repositorio ──────────────────────────────────────────────

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

DOC_DEPARTAMENTOS = [
    {"silo":"BUILD","departamentos":["IT_Development","IT_Architecture","PMO_BUILD","QA","DevOps"]},
    {"silo":"RUN","departamentos":["IT_Operations","IT_Support","IT_Security","PMO_RUN","NOC"]},
    {"silo":"TRANSVERSAL","departamentos":["Gobernanza_General","RRHH","Formacion","Legal","Compliance"]},
]

DOC_FOLDER_STRUCTURE = {
    "BUILD": {"Proyectos":[],"Gobernanza":["Metodologias","Standards","Templates"],"Departamentos":["IT_Development","IT_Architecture","PMO_BUILD"]},
    "RUN": {"Incidencias":["Procedimientos","Runbooks","Postmortems"],"Gobernanza":["SLA","Compliance","Audits"],"Departamentos":["IT_Operations","IT_Support","PMO_RUN"]},
    "TRANSVERSAL": {"Gobernanza_General":[],"Formacion":[],"Herramientas":[]},
}


@app.get("/documentacion")
async def get_documentacion(
    tipo: Optional[str] = None, silo: Optional[str] = None,
    departamento: Optional[str] = None, search: Optional[str] = None,
    proyecto_id: Optional[str] = None, limit: int = 100, offset: int = 0,
):
    pool = get_pool()
    if not pool: return {"docs":[],"total":0}
    clauses, params = ["activo=true"], []
    if tipo: params.append(tipo); clauses.append(f"tipo=${len(params)}")
    if silo: params.append(silo); clauses.append(f"silo=${len(params)}")
    if departamento: params.append(departamento); clauses.append(f"departamento=${len(params)}")
    if proyecto_id: params.append(proyecto_id); clauses.append(f"proyecto_id=${len(params)}")
    if search: params.append(f"%{search}%"); clauses.append(f"(titulo ILIKE ${len(params)} OR descripcion ILIKE ${len(params)} OR array_to_string(tags,',') ILIKE ${len(params)})")
    where = "WHERE " + " AND ".join(clauses)
    async with pool.acquire() as conn:
        total = await conn.fetchval(f"SELECT COUNT(*) FROM documentacion_repositorio {where}", *params)
        params.extend([limit, offset])
        rows = await conn.fetch(
            f"SELECT * FROM documentacion_repositorio {where} ORDER BY fecha_creacion DESC LIMIT ${len(params)-1} OFFSET ${len(params)}",
            *params)
        return {"docs": [serialize(r) for r in rows], "total": total}


class DocCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    tipo: str = "proyecto"
    silo: str = "BUILD"
    departamento: Optional[str] = None
    proyecto_id: Optional[str] = None
    incidencia_id: Optional[str] = None
    archivo_nombre: Optional[str] = None
    archivo_size: int = 0
    mime_type: Optional[str] = None
    archivo_tipo: Optional[str] = None
    tags: List[str] = []
    creado_por: Optional[str] = None
    drive_share_url: Optional[str] = None


@app.post("/documentacion")
async def create_documento(doc: DocCreate):
    pool = get_pool()
    if not pool: raise HTTPException(status_code=503)
    # Build drive folder path
    folder = f"CognitivePMO_Documentacion/{{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}}"
    if doc.departamento: folder += f"/{doc.departamento}"
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO documentacion_repositorio
                (titulo,descripcion,tipo,silo,departamento,proyecto_id,incidencia_id,
                 archivo_nombre,archivo_size,mime_type,archivo_tipo,tags,creado_por,
                 drive_folder_path,drive_share_url)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15) RETURNING *""",
                doc.titulo, doc.descripcion, doc.tipo, doc.silo, doc.departamento,
                doc.proyecto_id, doc.incidencia_id,
                doc.archivo_nombre, doc.archivo_size, doc.mime_type, doc.archivo_tipo,
                doc.tags, doc.creado_por, folder, doc.drive_share_url,
            )
            return serialize(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/documentacion/{doc_id}")
async def update_documento(doc_id: int, doc: DocCreate):
    pool = get_pool()
    if not pool: raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE documentacion_repositorio SET
                titulo=$2,descripcion=$3,tipo=$4,silo=$5,departamento=$6,
                proyecto_id=$7,tags=$8,creado_por=$9,fecha_actualizacion=NOW(),
                version=version+1
                WHERE id=$1 AND activo=true RETURNING *""",
                doc_id, doc.titulo, doc.descripcion, doc.tipo, doc.silo,
                doc.departamento, doc.proyecto_id, doc.tags, doc.creado_por,
            )
            if not row: raise HTTPException(status_code=404)
            return serialize(row)
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documentacion/{doc_id}")
async def delete_documento(doc_id: int):
    pool = get_pool()
    if not pool: raise HTTPException(status_code=503)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE documentacion_repositorio SET activo=false, fecha_actualizacion=NOW() WHERE id=$1 RETURNING id",
            doc_id)
        if not row: raise HTTPException(status_code=404)
        return {"ok": True}


@app.get("/documentacion/departamentos")
async def get_departamentos():
    return DOC_DEPARTAMENTOS


@app.get("/documentacion/estructura")
async def get_estructura():
    return DOC_FOLDER_STRUCTURE


@app.get("/documentacion/stats")
async def get_doc_stats():
    pool = get_pool()
    if not pool: return {}
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM documentacion_repositorio WHERE activo=true")
        by_silo = await conn.fetch("SELECT silo, COUNT(*) as cnt FROM documentacion_repositorio WHERE activo=true GROUP BY silo")
        by_tipo = await conn.fetch("SELECT tipo, COUNT(*) as cnt FROM documentacion_repositorio WHERE activo=true GROUP BY tipo")
        by_depto = await conn.fetch("SELECT departamento, COUNT(*) as cnt FROM documentacion_repositorio WHERE activo=true AND departamento IS NOT NULL GROUP BY departamento ORDER BY cnt DESC LIMIT 10")
        return {
            "total": total or 0,
            "by_silo": {r['silo']:r['cnt'] for r in by_silo},
            "by_tipo": {r['tipo']:r['cnt'] for r in by_tipo},
            "by_departamento": {r['departamento']:r['cnt'] for r in by_depto},
        }


# ── Dev Tools ──────────────────────────────────────────────────────────────

@app.get("/dev/tables")
async def dev_list_tables():
    pool = get_pool()
    if not pool: return []
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT t.table_name,
                   pg_size_pretty(pg_total_relation_size(quote_ident(t.table_name))) as size,
                   (SELECT COUNT(*) FROM information_schema.columns c WHERE c.table_name=t.table_name AND c.table_schema='public') as col_count,
                   s.n_live_tup as row_count
            FROM information_schema.tables t
            LEFT JOIN pg_stat_user_tables s ON s.relname=t.table_name
            WHERE t.table_schema='public' AND t.table_type='BASE TABLE'
            ORDER BY t.table_name""")
        return [dict(r) for r in rows]


@app.get("/dev/tables/{table_name}/schema")
async def dev_table_schema(table_name: str):
    pool = get_pool()
    if not pool: return []
    async with pool.acquire() as conn:
        cols = await conn.fetch("""
            SELECT column_name, data_type, character_maximum_length,
                   is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name=$1
            ORDER BY ordinal_position""", table_name)
        constraints = await conn.fetch("""
            SELECT conname, contype, pg_get_constraintdef(c.oid) as definition
            FROM pg_constraint c JOIN pg_class t ON c.conrelid=t.oid
            WHERE t.relname=$1""", table_name)
        indexes = await conn.fetch("""
            SELECT indexname, indexdef FROM pg_indexes
            WHERE tablename=$1 AND schemaname='public'""", table_name)
        return {"columns": [dict(r) for r in cols], "constraints": [dict(r) for r in constraints], "indexes": [dict(r) for r in indexes]}


@app.get("/dev/tables/{table_name}/data")
async def dev_table_data(table_name: str, limit: int = 50, offset: int = 0):
    pool = get_pool()
    if not pool: return {"rows":[],"total":0}
    # Sanitize table name
    import re
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise HTTPException(status_code=400, detail="Invalid table name")
    async with pool.acquire() as conn:
        total = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        rows = await conn.fetch(f"SELECT * FROM {table_name} LIMIT $1 OFFSET $2", limit, offset)
        return {"rows": [serialize(r) for r in rows], "total": total}


class DevSQLQuery(BaseModel):
    sql: str

@app.post("/dev/sql")
async def dev_execute_sql(q: DevSQLQuery):
    pool = get_pool()
    if not pool: raise HTTPException(status_code=503)
    sql = q.sql.strip()
    is_select = sql.upper().startswith('SELECT') or sql.upper().startswith('WITH')
    try:
        async with pool.acquire() as conn:
            if is_select:
                rows = await conn.fetch(sql)
                return {"type":"query","rows":[serialize(r) for r in rows],"count":len(rows)}
            else:
                result = await conn.execute(sql)
                return {"type":"execute","result":str(result),"count":0}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/dev/files")
async def dev_list_files():
    import glob
    base = os.path.dirname(__file__)
    files = []
    for pattern in ['*.py','*.txt','*.sql','*.yml','*.yaml','*.json','*.conf','*.env']:
        for f in glob.glob(os.path.join(base, '**', pattern), recursive=True):
            rel = os.path.relpath(f, base)
            size = os.path.getsize(f)
            files.append({"path": rel, "size": size, "lines": sum(1 for _ in open(f, errors='ignore'))})
    return sorted(files, key=lambda x: x['path'])


@app.get("/dev/files/{file_path:path}")
async def dev_read_file(file_path: str):
    import re
    base = os.path.dirname(__file__)
    full = os.path.normpath(os.path.join(base, file_path))
    if not full.startswith(base):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.isfile(full):
        raise HTTPException(status_code=404, detail="File not found")
    with open(full, 'r', errors='replace') as f:
        return {"path": file_path, "content": f.read(), "size": os.path.getsize(full)}


@app.get("/dev/context")
async def dev_technical_context():
    """Generate full technical context document."""
    pool = get_pool()
    tables_info = []
    if pool:
        async with pool.acquire() as conn:
            tables = await conn.fetch("""
                SELECT t.table_name FROM information_schema.tables t
                WHERE t.table_schema='public' AND t.table_type='BASE TABLE' ORDER BY t.table_name""")
            for t in tables:
                tn = t['table_name']
                cols = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns WHERE table_schema='public' AND table_name=$1
                    ORDER BY ordinal_position""", tn)
                cnt = await conn.fetchval(f"SELECT COUNT(*) FROM {tn}")
                tables_info.append({"name":tn,"rows":cnt,"columns":[dict(c) for c in cols]})
    # Build endpoints list
    import re
    base_dir = os.path.dirname(__file__)
    endpoints = []
    for fpath in [os.path.join(base_dir, 'main.py'), os.path.join(base_dir, 'war_room_api.py')]:
        try:
            with open(fpath) as f:
                for line in f:
                    m = re.match(r'@(?:app|war_room_app)\.(get|post|put|delete)\("([^"]+)"', line)
                    if m:
                        endpoints.append({"method":m.group(1).upper(),"path":m.group(2),"file":os.path.basename(fpath)})
        except: pass
    return {
        "project": "Cognitive PMO",
        "version": "2.0",
        "author": "Jose Antonio Martinez Victoria",
        "stack": {"backend":"FastAPI + asyncpg","frontend":"Vanilla JS SPA","db":"PostgreSQL","agents":"Flowise + Claude Sonnet 4","infra":"Docker Compose on local postgres"},
        "tables": tables_info,
        "endpoints": endpoints,
        "total_endpoints": len(endpoints),
        "total_tables": len(tables_info),
        "services": [
            {"name":"API","port":8088,"tech":"FastAPI"},
            {"name":"Frontend","port":3030,"tech":"nginx:alpine"},
            {"name":"Flowise","port":3000,"tech":"Flowise AI"},
            {"name":"PostgreSQL","port":5432,"tech":"PostgreSQL 15"},
        ],
    }


# ── Agents Module ──────────────────────────────────────────────────────────
from agents.router import router as agents_router
app.include_router(agents_router)

from agents.sync_worker import sync_loop
from agents.task_advisor_worker import task_advisor_loop

@app.on_event("startup")
async def start_workers():
    import asyncio
    pool = get_pool()
    if pool:
        asyncio.create_task(sync_loop(pool))
        asyncio.create_task(task_advisor_loop(pool))

# ============================================================================
# CAB — Gabinete de Cambios (CRUD Propuestas + Periodos + Ventanas + Alertas)
# ============================================================================

@app.get("/cab/periodos")
async def cab_list_periodos():
    async with get_pool().acquire() as conn:
        rows = await conn.fetch("SELECT * FROM calendario_periodos_demanda ORDER BY fecha_inicio")
        results = []
        for r in rows:
            d = dict(r)
            for k, v in d.items():
                if hasattr(v, 'isoformat'):
                    d[k] = v.isoformat()
            results.append(d)
        return results


@app.get("/cab/propuestas")
async def cab_list_propuestas(periodo: str = None, estado: str = None):
    query = ("SELECT id,periodo,numero_propuesta,estado,generado_por,fecha_generacion,"
             "cambios_aplicados,cambios_rechazados,revisado_por "
             "FROM cmdb_change_proposals")
    conds, args, idx = [], [], 1
    if periodo:
        conds.append(f"periodo=${idx}")
        args.append(periodo)
        idx += 1
    if estado:
        conds.append(f"estado=${idx}")
        args.append(estado)
        idx += 1
    if conds:
        query += " WHERE " + " AND ".join(conds)
    query += " ORDER BY fecha_generacion DESC LIMIT 50"
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(query, *args)
        results = []
        for r in rows:
            d = dict(r)
            for k, v in d.items():
                if hasattr(v, 'isoformat'):
                    d[k] = v.isoformat()
            results.append(d)
        return results


@app.get("/cab/propuestas/{propuesta_id}")
async def cab_get_propuesta(propuesta_id: str):
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM cmdb_change_proposals WHERE id=$1::uuid", propuesta_id)
        if not row:
            return JSONResponse({"error": "No encontrada"}, status_code=404)
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        return d


@app.post("/cab/propuestas/{propuesta_id}/aprobar")
async def cab_aprobar(propuesta_id: str, request: Request):
    body = await request.json()
    revisado_por = body.get("revisado_por", "admin")
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM cmdb_change_proposals WHERE id=$1::uuid", propuesta_id)
        if not row:
            return JSONResponse({"error": "No encontrada"}, status_code=404)
        propuesta = (row["propuesta_json"] if isinstance(row["propuesta_json"], dict)
                     else json.loads(row["propuesta_json"]))
        cambios = propuesta.get("cambios_propuestos", [])
        insertados = 0
        for c in cambios:
            v = c.get("ventana_final") or c.get("ventana_recomendada", {})
            if not c.get("id_activo") or not v:
                continue
            await conn.execute(
                "INSERT INTO cmdb_change_windows "
                "(id_activo,nombre_ventana,periodo,dias_semana,hora_inicio,hora_fin,"
                "duracion_minutos,tipos_cambio_permitidos,riesgo_estimado,score_confianza,"
                "valido_hasta,id_propuesta,aprobado_por,fecha_aprobacion) "
                "VALUES ($1,$2,$3,$4,$5::time,$6::time,$7,$8,$9,$10,"
                "(CURRENT_DATE+INTERVAL '90 days')::date,$11::uuid,$12,now())",
                int(c["id_activo"]) if str(c["id_activo"]).isdigit() else 0,
                c.get("activo_nombre", f"Ventana {c['id_activo']}"),
                row["periodo"],
                v.get("dias", ["sabado", "domingo"]),
                v.get("hora_inicio", "23:00"),
                v.get("hora_fin", "07:00"),
                v.get("duracion_horas", 8) * 60 if v.get("duracion_horas") else 480,
                c.get("tipos_cambio_permitidos", ["Patch", "Mantenimiento"]),
                c.get("riesgo", "MEDIO"),
                float(c.get("score_confianza", 0.80)),
                propuesta_id, revisado_por)
            insertados += 1
        await conn.execute(
            "UPDATE cmdb_change_proposals SET estado='APLICADO',revisado_por=$1,"
            "fecha_revision=now(),notas_revision=$2,cambios_aplicados=$3,"
            "updated_at=now() WHERE id=$4::uuid",
            revisado_por, body.get("notas", ""), insertados, propuesta_id)
        return {"status": "OK", "propuesta_id": propuesta_id,
                "ventanas_insertadas": insertados, "estado": "APLICADO"}


@app.post("/cab/propuestas/{propuesta_id}/rechazar")
async def cab_rechazar(propuesta_id: str, request: Request):
    body = await request.json()
    async with get_pool().acquire() as conn:
        await conn.execute(
            "UPDATE cmdb_change_proposals SET estado='RECHAZADO',revisado_por=$1,"
            "fecha_revision=now(),notas_revision=$2,updated_at=now() WHERE id=$3::uuid",
            body.get("revisado_por", "admin"),
            body.get("motivo_rechazo", ""), propuesta_id)
    return {"status": "OK", "propuesta_id": propuesta_id, "estado": "RECHAZADO"}


@app.get("/cab/ventanas")
async def cab_list_ventanas(id_activo: int = None, periodo: str = None):
    query = ("SELECT cw.*,a.codigo,a.nombre as activo_nombre,a.criticidad "
             "FROM cmdb_change_windows cw "
             "JOIN cmdb_activos a ON a.id_activo=cw.id_activo "
             "WHERE cw.estado='ACTIVA'")
    args, idx = [], 1
    if id_activo:
        query += f" AND cw.id_activo=${idx}"
        args.append(id_activo)
        idx += 1
    if periodo:
        query += f" AND cw.periodo=${idx}"
        args.append(periodo)
        idx += 1
    query += " ORDER BY a.criticidad,a.codigo"
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(query, *args)
        results = []
        for r in rows:
            d = dict(r)
            for k, v in d.items():
                if hasattr(v, 'isoformat'):
                    d[k] = v.isoformat()
            results.append(d)
        return results


@app.get("/cab/alertas")
async def cab_alertas_activas():
    """Alertas CAB activas (para mostrar en gov-run y gov-build)"""
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM intelligent_alerts "
            "WHERE source_agent='AG-011' AND status='ACTIVE' "
            "ORDER BY severity DESC, created_at DESC LIMIT 20")
        results = []
        for r in rows:
            d = dict(r)
            for k, v in d.items():
                if hasattr(v, 'isoformat'):
                    d[k] = v.isoformat()
            results.append(d)
        return results


# ============================================================================
# CAB — CRUD Completo para operatividad total
# ============================================================================

# ── PERIODOS: Crear, Editar, Borrar, Detalle ──

@app.post("/cab/periodos")
async def cab_crear_periodo(request: Request):
    body = await request.json()
    nombre = body.get("nombre_periodo")
    if not nombre:
        return JSONResponse({"error": "nombre_periodo requerido"}, status_code=400)
    pool = get_pool()
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT count(*) FROM calendario_periodos_demanda WHERE nombre_periodo=$1", nombre)
        if exists > 0:
            return JSONResponse({"error": f"Periodo {nombre} ya existe"}, status_code=409)
        row = await conn.fetchrow("""
            INSERT INTO calendario_periodos_demanda (nombre_periodo, fecha_inicio, fecha_fin,
                impacto_estimado, carga_pico_esperada_pct, activos_afectados, notas, created_by)
            VALUES ($1, $2::date, $3::date, $4, $5, $6, $7, $8)
            RETURNING id, nombre_periodo, fecha_inicio, fecha_fin, impacto_estimado
        """, nombre, body.get("fecha_inicio"), body.get("fecha_fin"),
            body.get("impacto_estimado", "ALTO"), int(body.get("carga_pico_esperada_pct", 80)),
            body.get("activos_afectados", []), body.get("notas", ""),
            body.get("created_by", "admin"))
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        return d


@app.get("/cab/periodos/{periodo_id}")
async def cab_get_periodo(periodo_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM calendario_periodos_demanda WHERE id=$1::uuid", periodo_id)
        if not row:
            return JSONResponse({"error": "No encontrado"}, status_code=404)
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        return d


@app.put("/cab/periodos/{periodo_id}")
async def cab_editar_periodo(periodo_id: str, request: Request):
    body = await request.json()
    sets, args, idx = [], [], 1
    for field in ["nombre_periodo", "fecha_inicio", "fecha_fin", "impacto_estimado",
                   "carga_pico_esperada_pct", "activos_afectados", "notas"]:
        if field in body:
            sets.append(f"{field}=${idx}")
            val = body[field]
            if field == "carga_pico_esperada_pct":
                val = int(val)
            args.append(val)
            idx += 1
    if not sets:
        return JSONResponse({"error": "No hay campos para actualizar"}, status_code=400)
    sets.append("updated_at=now()")
    args.append(periodo_id)
    query = f"UPDATE calendario_periodos_demanda SET {','.join(sets)} WHERE id=${idx}::uuid RETURNING id, nombre_periodo"
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        if not row:
            return JSONResponse({"error": "Periodo no encontrado"}, status_code=404)
        return dict(row)


@app.delete("/cab/periodos/{periodo_id}")
async def cab_borrar_periodo(periodo_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM calendario_periodos_demanda WHERE id=$1::uuid", periodo_id)
        return {"status": "OK", "deleted": periodo_id}


# ── VENTANAS: Detalle, Editar, Cancelar ──

@app.get("/cab/ventanas/{ventana_id}")
async def cab_get_ventana(ventana_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT cw.*, a.codigo, a.nombre as activo_nombre, a.criticidad, a.capa,
                   a.entorno, a.propietario, a.responsable_tecnico, a.estado_ciclo
            FROM cmdb_change_windows cw
            JOIN cmdb_activos a ON a.id_activo = cw.id_activo
            WHERE cw.id = $1::uuid
        """, ventana_id)
        if not row:
            return JSONResponse({"error": "No encontrada"}, status_code=404)
        result = dict(row)
        for k, v in result.items():
            if hasattr(v, 'isoformat'):
                result[k] = v.isoformat()
        deps = await conn.fetch("""
            SELECT a2.codigo, a2.nombre, a2.criticidad, r.tipo_relacion
            FROM cmdb_relaciones r
            JOIN cmdb_activos a2 ON a2.id_activo = r.id_activo_destino
            WHERE r.id_activo_origen = $1
        """, row["id_activo"])
        result["dependencias"] = [dict(d) for d in deps]
        incs = await conn.fetch("""
            SELECT ticket_id, prioridad_ia, estado, incidencia_detectada
            FROM incidencias_run
            WHERE ci_afectado = $1 AND estado IN ('QUEUED','EN_CURSO','ESCALADO')
        """, row.get("codigo", ""))
        result["incidencias_activas"] = [dict(i) for i in incs]
        hist = await conn.fetch("""
            SELECT mes, carga_promedio_pct, carga_maxima_pct, patron_diario
            FROM cmdb_demand_history WHERE id_activo = $1 ORDER BY mes DESC LIMIT 3
        """, row["id_activo"])
        hist_list = []
        for h in hist:
            hd = dict(h)
            for k, v in hd.items():
                if hasattr(v, 'isoformat'):
                    hd[k] = v.isoformat()
            hist_list.append(hd)
        result["historico_reciente"] = hist_list
        return result


@app.put("/cab/ventanas/{ventana_id}")
async def cab_editar_ventana(ventana_id: str, request: Request):
    body = await request.json()
    sets, args, idx = [], [], 1
    for field in ["dias_semana", "hora_inicio", "hora_fin", "duracion_minutos",
                   "tipos_cambio_permitidos", "restricciones", "riesgo_estimado",
                   "score_confianza", "estado", "nombre_ventana"]:
        if field in body:
            sets.append(f"{field}=${idx}")
            val = body[field]
            if field == "score_confianza":
                val = float(val)
            if field == "duracion_minutos":
                val = int(val)
            args.append(val)
            idx += 1
    if not sets:
        return JSONResponse({"error": "No hay campos"}, status_code=400)
    sets.append("updated_at=now()")
    args.append(ventana_id)
    query = f"UPDATE cmdb_change_windows SET {','.join(sets)} WHERE id=${idx}::uuid RETURNING id, nombre_ventana, estado"
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        if not row:
            return JSONResponse({"error": "Ventana no encontrada"}, status_code=404)
        return dict(row)


@app.delete("/cab/ventanas/{ventana_id}")
async def cab_borrar_ventana(ventana_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE cmdb_change_windows SET estado='CANCELADA', updated_at=now() WHERE id=$1::uuid",
            ventana_id)
        return {"status": "OK", "ventana_id": ventana_id, "estado": "CANCELADA"}


# ── PROPUESTAS: Editar, Editar cambio individual ──

@app.put("/cab/propuestas/{propuesta_id}")
async def cab_editar_propuesta(propuesta_id: str, request: Request):
    body = await request.json()
    sets, args, idx = [], [], 1
    for field in ["notas_revision", "revisado_por", "estado"]:
        if field in body:
            sets.append(f"{field}=${idx}")
            args.append(body[field])
            idx += 1
    if not sets:
        return JSONResponse({"error": "No hay campos"}, status_code=400)
    sets.append("updated_at=now()")
    sets.append("fecha_revision=now()")
    args.append(propuesta_id)
    query = f"UPDATE cmdb_change_proposals SET {','.join(sets)} WHERE id=${idx}::uuid RETURNING id, estado"
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        if not row:
            return JSONResponse({"error": "No encontrada"}, status_code=404)
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        return d


@app.post("/cab/propuestas/{propuesta_id}/editar-cambio")
async def cab_editar_cambio_individual(propuesta_id: str, request: Request):
    body = await request.json()
    id_activo = body.get("id_activo")
    if not id_activo:
        return JSONResponse({"error": "id_activo requerido"}, status_code=400)
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT propuesta_json FROM cmdb_change_proposals WHERE id=$1::uuid", propuesta_id)
        if not row:
            return JSONResponse({"error": "No encontrada"}, status_code=404)
        prop = (row["propuesta_json"] if isinstance(row["propuesta_json"], dict)
                else json.loads(row["propuesta_json"]))
        cambios = prop.get("cambios_propuestos", [])
        updated = False
        for c in cambios:
            if str(c.get("id_activo")) == str(id_activo):
                if "ventana_editada" in body:
                    c["ventana_final"] = body["ventana_editada"]
                if "tipos_cambio_permitidos" in body:
                    c["tipos_cambio_permitidos"] = body["tipos_cambio_permitidos"]
                if "riesgo" in body:
                    c["riesgo"] = body["riesgo"]
                if "notas" in body:
                    c["notas_edicion"] = body["notas"]
                c["editado_por_humano"] = True
                updated = True
                break
        if not updated:
            return JSONResponse({"error": f"Activo {id_activo} no encontrado en propuesta"},
                                status_code=404)
        prop["cambios_propuestos"] = cambios
        await conn.execute("""
            UPDATE cmdb_change_proposals SET propuesta_json=$1::jsonb,
                cambios_editados=cambios_editados+1, updated_at=now()
            WHERE id=$2::uuid
        """, json.dumps(prop, default=str), propuesta_id)
        return {"status": "OK", "activo_editado": id_activo}


# ── ALERTAS: Detalle, Reconocer/Resolver ──

@app.get("/cab/alertas/{alerta_id}")
async def cab_get_alerta(alerta_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM intelligent_alerts WHERE id=$1", alerta_id)
        if not row:
            return JSONResponse({"error": "No encontrada"}, status_code=404)
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        return d


@app.put("/cab/alertas/{alerta_id}")
async def cab_actualizar_alerta(alerta_id: str, request: Request):
    body = await request.json()
    nuevo_estado = body.get("status")
    if nuevo_estado not in ("ACKNOWLEDGED", "RESOLVED", "SUPPRESSED", "ESCALATED"):
        return JSONResponse({"error": "Estado no valido"}, status_code=400)
    pool = get_pool()
    async with pool.acquire() as conn:
        sets = ["status=$1"]
        args = [nuevo_estado]
        idx = 2
        if nuevo_estado == "ACKNOWLEDGED":
            sets.append(f"acknowledged_by=${idx}")
            args.append(body.get("acknowledged_by", "admin"))
            idx += 1
            sets.append("acknowledged_at=now()")
        elif nuevo_estado == "RESOLVED":
            sets.append("resolved_at=now()")
            sets.append(f"acknowledged_by=${idx}")
            args.append(body.get("acknowledged_by", "admin"))
            idx += 1
        args.append(alerta_id)
        query = f"UPDATE intelligent_alerts SET {','.join(sets)} WHERE id=${idx} RETURNING id, status"
        row = await conn.fetchrow(query, *args)
        if not row:
            return JSONResponse({"error": "No encontrada"}, status_code=404)
        return dict(row)


# ── ACTIVOS: Selector agrupado para modales ──

@app.get("/cab/activos-selector")
async def cab_activos_selector():
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id_activo, codigo, nombre, criticidad, capa, entorno, estado_ciclo
            FROM cmdb_activos
            WHERE estado_ciclo IN ('OPERATIVO','DEGRADADO','MANTENIMIENTO')
            ORDER BY entorno, capa, criticidad, nombre
        """)
        result = {}
        for r in rows:
            env = r["entorno"]
            capa = r["capa"]
            if env not in result:
                result[env] = {"total": 0, "capas": {}}
            if capa not in result[env]["capas"]:
                result[env]["capas"][capa] = []
            result[env]["capas"][capa].append({
                "id": r["id_activo"], "codigo": r["codigo"],
                "nombre": r["nombre"], "criticidad": r["criticidad"]
            })
            result[env]["total"] += 1
        return result


# ── Notificaciones ────────────────────────────────────────────────────────

@app.get("/api/notificaciones")
async def get_notificaciones(leidas: Optional[str] = None, user: Optional[UserInfo] = Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "No autenticado")
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        if leidas == "false":
            rows = await conn.fetch(
                "SELECT * FROM tech_notificaciones WHERE id_usuario=$1 AND leida=FALSE ORDER BY created_at DESC LIMIT 50",
                user.id_usuario)
        elif leidas == "true":
            rows = await conn.fetch(
                "SELECT * FROM tech_notificaciones WHERE id_usuario=$1 AND leida=TRUE ORDER BY created_at DESC LIMIT 50",
                user.id_usuario)
        else:
            rows = await conn.fetch(
                "SELECT * FROM tech_notificaciones WHERE id_usuario=$1 ORDER BY created_at DESC LIMIT 50",
                user.id_usuario)
        return [dict(r) for r in rows]


@app.put("/api/notificaciones/{nid}/leer")
async def marcar_leida(nid: int, user: Optional[UserInfo] = Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "No autenticado")
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE tech_notificaciones SET leida=TRUE WHERE id=$1 AND id_usuario=$2", nid, user.id_usuario)
        return {"ok": True}


@app.put("/api/notificaciones/leer-todas")
async def marcar_todas_leidas(user: Optional[UserInfo] = Depends(get_current_user)):
    if not user:
        raise HTTPException(401, "No autenticado")
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        cnt = await conn.execute(
            "UPDATE tech_notificaciones SET leida=TRUE WHERE id_usuario=$1 AND leida=FALSE", user.id_usuario)
        return {"ok": True, "actualizadas": cnt.split()[-1] if cnt else 0}


async def crear_notificacion(conn, id_usuario: int, tipo: str, titulo: str, mensaje: str,
                              referencia_tipo: str = None, referencia_id: str = None):
    """Helper to create a notification for a user."""
    await conn.execute("""
        INSERT INTO tech_notificaciones (id_usuario, tipo, titulo, mensaje, referencia_tipo, referencia_id)
        VALUES ($1, $2, $3, $4, $5, $6)
    """, id_usuario, tipo, titulo, mensaje, referencia_tipo, referencia_id)


# ── Kanban Global — Flow Metrics ──────────────────────────────────────────

@app.get("/api/kanban/tareas")
async def kanban_tareas_global():
    """Devuelve TODAS las tareas (RUN+BUILD) normalizadas para el Kanban global.
    Schema común: {id, tipo, pri, titulo, estado, sla, deadline, tecnico, depto, agente_origen, deps[], pct, ci, proyecto, sprint, columna_origen}.
    AG-004 Buffer Gatekeeper marca cruces RUN↔BUILD via deps[].
    """
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    pri_map = {"Crítica": "p1", "Alta": "p2", "Media": "p3", "Baja": "p4"}
    def map_estado(columna, id_tecnico):
        if columna == 'Completado':
            return 'resuelta'
        if columna == 'Bloqueado':
            return 'pte_tercero'
        if columna in ('En Progreso', 'Code Review', 'Testing', 'Despliegue'):
            return 'en_curso'
        if not id_tecnico:
            return 'unassigned'
        return 'asignada'

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT k.id, k.titulo, k.tipo, k.prioridad, k.columna, k.id_tecnico,
                   k.id_proyecto, k.id_incidencia, k.bloqueador,
                   k.horas_estimadas, k.horas_reales, k.fecha_creacion,
                   k.fecha_inicio_ejecucion, k.fecha_cierre,
                   p.nombre AS tecnico_nombre, p.silo_especialidad AS depto, p.carga_actual,
                   ir.ticket_id AS run_ticket, ir.sla_limite AS sla_horas, ir.timestamp_creacion AS run_creada,
                   cb.id_proyecto AS prj_id, cb.nombre_proyecto AS prj_nombre,
                   cb.horas_estimadas AS prj_horas, cb.fecha_creacion AS prj_creada
            FROM kanban_tareas k
            LEFT JOIN pmo_staff_skills p ON k.id_tecnico = p.id_recurso
            LEFT JOIN incidencias_run ir ON k.id_incidencia = ir.ticket_id
            LEFT JOIN cartera_build cb ON k.id_proyecto = cb.id_proyecto
            ORDER BY k.fecha_creacion DESC
            LIMIT 500
        """)

        # Construir índice id→tarea para resolver deps
        out = []
        by_id = {}
        for r in rows:
            estado = map_estado(r['columna'], r['id_tecnico'])
            pct = 0
            if r['horas_estimadas'] and float(r['horas_estimadas']) > 0:
                pct = min(100, int(float(r['horas_reales'] or 0) / float(r['horas_estimadas']) * 100))
            elif estado == 'resuelta':
                pct = 100
            elif estado == 'en_curso':
                pct = 50
            # SLA / deadline
            sla_seg = None
            deadline_iso = None
            from datetime import timezone, timedelta
            if r['tipo'] == 'RUN' and r['sla_horas']:
                creada = r['run_creada'] or r['fecha_creacion']
                if creada:
                    if creada.tzinfo is None:
                        creada = creada.replace(tzinfo=timezone.utc)
                    fin = creada.timestamp() + (float(r['sla_horas']) * 3600)
                    sla_seg = int(fin - datetime.now(timezone.utc).timestamp())
            if r['tipo'] == 'BUILD' and r['prj_creada'] and r['prj_horas']:
                # deadline aproximado: creación + (horas_estimadas / 8h por día laboral)
                base = r['prj_creada']
                if base.tzinfo is None:
                    base = base.replace(tzinfo=timezone.utc)
                dias = max(1, int(float(r['prj_horas']) / 8))
                deadline_iso = (base + timedelta(days=dias)).date().isoformat()
            tecnico = None
            if r['id_tecnico']:
                tecnico = {
                    "id": r['id_tecnico'],
                    "nombre": r['tecnico_nombre'] or r['id_tecnico'],
                    "carga": r['carga_actual'] or 0,
                }
            tarea = {
                "id": r['id'],
                "tipo": r['tipo'],  # RUN | BUILD
                "pri": pri_map.get(r['prioridad'], 'p3'),
                "titulo": r['titulo'],
                "estado": estado,
                "sla_seg": sla_seg,
                "deadline": deadline_iso,
                "tecnico": tecnico,
                "depto": r['depto'] or 'Sin asignar',
                "agente_origen": "AG-002" if r['tipo'] == 'RUN' else "AG-013",
                "deps": [],
                "pct": pct,
                "ci": r['run_ticket'],
                "proyecto": {"id": r['prj_id'], "nombre": r['prj_nombre']} if r['prj_id'] else None,
                "sprint": None,
                "columna_origen": r['columna'],
                "bloqueador": r['bloqueador'],
            }
            out.append(tarea)
            by_id[r['id']] = tarea

        # AG-004 Buffer Gatekeeper: detectar deps cruzadas RUN↔BUILD
        # Heurística: si una RUN crítica/alta toca un CI presente en una BUILD activa, se cruzan.
        # Para datos reales: usar bloqueador como referencia textual al ID destino.
        for t in out:
            if t.get('bloqueador'):
                # Buscar IDs de tareas mencionadas en el campo bloqueador
                txt = str(t['bloqueador'])
                for other_id in by_id:
                    if other_id != t['id'] and other_id in txt:
                        t['deps'].append({"target_id": other_id, "tipo": "bloquea_a", "agente": "AG-004"})

        return {
            "tareas": out,
            "total": len(out),
            "by_estado": {est: sum(1 for t in out if t['estado'] == est)
                          for est in ['unassigned', 'asignada', 'en_curso', 'pte_tercero', 'resuelta']},
        }


# ── Bus de eventos kanban → agentes (FASE 6) ──
# Patrón: si no existe event_bus, persistimos eventos como notas en
# tech_chat_mensajes vía sala dedicada del agente destino (zona congelada:
# solo INSERT, no se modifica lógica interna del agente).
async def _kb_notify_agent(conn, agent_code: str, evento: str, payload: dict):
    """Notifica un evento a un agente. agent_code: 'AG-004', 'AG-014', etc.
    Usa tech_chat_salas tipo='run' con id_referencia='BUS-{agent_code}' como buzón.
    """
    try:
        ref = f"BUS-{agent_code}"
        sala_id = await conn.fetchval(
            """INSERT INTO tech_chat_salas (tipo, id_referencia, nombre)
               VALUES ('run', $1, $2) ON CONFLICT (tipo, id_referencia)
               DO UPDATE SET activa=TRUE RETURNING id""",
            ref, f"Bus de eventos · {agent_code}")
        msg = f"[{evento}] {json.dumps(payload, ensure_ascii=False)}"
        await conn.execute(
            """INSERT INTO tech_chat_mensajes (id_sala, id_autor, rol_autor, mensaje)
               VALUES ($1, 'KANBAN-BUS', 'agente', $2)""",
            sala_id, msg)
        logger.info(f"event_bus → {agent_code}: {evento} ({payload.get('task_id','?')})")
    except Exception as e:
        logger.warning(f"No se pudo notificar a {agent_code}: {e}")


# Mapeo estado lógico → columna kanban_tareas
_KB_ESTADO_TO_COLUMNA = {
    "unassigned": "Backlog",
    "asignada": "Análisis",
    "en_curso": "En Progreso",
    "pte_tercero": "Bloqueado",
    "resuelta": "Completado",
}
# Matriz de transiciones permitidas (estado_origen → set de destinos)
_KB_TRANSICIONES = {
    "unassigned":  {"asignada", "pte_tercero"},
    "asignada":    {"en_curso", "pte_tercero", "unassigned"},
    "en_curso":    {"pte_tercero", "resuelta", "asignada"},
    "pte_tercero": {"en_curso", "asignada", "resuelta"},
    "resuelta":    {"en_curso"},  # solo se puede reabrir
}


def _kb_estado_actual(columna: str, id_tecnico: Optional[str]) -> str:
    if columna == 'Completado': return 'resuelta'
    if columna == 'Bloqueado': return 'pte_tercero'
    if columna in ('En Progreso', 'Code Review', 'Testing', 'Despliegue'): return 'en_curso'
    if not id_tecnico: return 'unassigned'
    return 'asignada'


class KanbanEstadoUpdate(BaseModel):
    estado: str


@app.patch("/api/kanban/tareas/{task_id}")
async def kanban_patch_estado(task_id: str, body: KanbanEstadoUpdate):
    """Cambia el estado lógico de una tarea (DnD entre columnas).
    Valida transición, persiste columna + fechas + nota sys automática en tech_chat_mensajes.
    """
    nuevo = body.estado
    if nuevo not in _KB_ESTADO_TO_COLUMNA:
        raise HTTPException(400, f"Estado inválido: {nuevo}")
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        old = await conn.fetchrow("SELECT * FROM kanban_tareas WHERE id=$1", task_id)
        if not old:
            raise HTTPException(404, "Tarea no encontrada")
        actual = _kb_estado_actual(old['columna'], old['id_tecnico'])
        if actual == nuevo:
            return {"ok": True, "task_id": task_id, "estado": actual, "noop": True}
        permitidos = _KB_TRANSICIONES.get(actual, set())
        if nuevo not in permitidos:
            raise HTTPException(409, f"Transición no permitida: {actual} → {nuevo}. Permitidas: {sorted(permitidos)}")
        nueva_col = _KB_ESTADO_TO_COLUMNA[nuevo]
        fe = old['fecha_inicio_ejecucion']
        fc = old['fecha_cierre']
        if nuevo == 'en_curso' and not fe:
            fe = datetime.now()
        if nuevo == 'resuelta':
            fc = datetime.now()
            if not fe:
                fe = datetime.now()
        if nuevo != 'resuelta' and old['columna'] == 'Completado':
            fc = None  # reabrir
        hist = old['historial_columnas'] or []
        if isinstance(hist, str):
            hist = json.loads(hist)
        hist.append({"columna": nueva_col, "estado": nuevo, "timestamp": datetime.now().isoformat()})
        await conn.execute(
            """UPDATE kanban_tareas SET columna=$2, fecha_inicio_ejecucion=$3, fecha_cierre=$4,
               historial_columnas=$5::jsonb WHERE id=$1""",
            task_id, nueva_col, fe, fc, json.dumps(hist))
        # Nota sys automática en tech_chat_mensajes (zona congelada: solo INSERT)
        try:
            tipo_sala = 'run' if old['tipo'] == 'RUN' else 'build'
            ref = old['id_incidencia'] or old['id_proyecto'] or task_id
            sala_id = await conn.fetchval(
                """INSERT INTO tech_chat_salas (tipo, id_referencia, nombre)
                   VALUES ($1,$2,$3) ON CONFLICT (tipo,id_referencia) DO UPDATE SET activa=TRUE
                   RETURNING id""",
                tipo_sala, ref, f"{ref} · {(old['titulo'] or '')[:80]}")
            await conn.execute(
                """INSERT INTO tech_chat_mensajes (id_sala, id_autor, rol_autor, mensaje)
                   VALUES ($1,$2,'agente',$3)""",
                sala_id, 'AG-SYS', f"Tarea movida {actual} → {nuevo} (columna: {old['columna']} → {nueva_col})")
        except Exception as e:
            logger.warning(f"No se pudo crear nota sys para {task_id}: {e}")
        # ── Hooks de eventos a agentes (FASE 6) ──
        # AG-004 Buffer Gatekeeper: cuando una tarea pasa a pte_tercero,
        # el buffer debe re-evaluar dependencias cruzadas y posiblemente
        # pausar tareas BUILD que dependan del CI bloqueado.
        if nuevo == 'pte_tercero':
            await _kb_notify_agent(conn, 'AG-004', 'TASK_BLOCKED', {
                "task_id": task_id, "tipo": old['tipo'], "from": actual,
                "id_incidencia": old['id_incidencia'], "id_proyecto": old['id_proyecto'],
                "bloqueador": old['bloqueador'],
            })
        # AG-014 Risk Predictor: cuando una RUN entra en SLA warn/danger
        # (calculado por el endpoint global), notificar para que pueda
        # disparar escalado o re-priorización. Aquí lo activamos al pasar
        # a en_curso (es cuando empieza a consumir SLA real).
        if nuevo == 'en_curso' and old['tipo'] == 'RUN':
            sla_horas = await conn.fetchval(
                "SELECT sla_limite FROM incidencias_run WHERE ticket_id=$1",
                old['id_incidencia']) if old['id_incidencia'] else None
            if sla_horas and float(sla_horas) <= 4:  # Umbral warn
                await _kb_notify_agent(conn, 'AG-014', 'SLA_RISK', {
                    "task_id": task_id, "ticket": old['id_incidencia'],
                    "sla_horas": float(sla_horas), "severity": "WARN" if float(sla_horas) > 1 else "DANGER",
                })
        return {"ok": True, "task_id": task_id, "estado": nuevo, "columna": nueva_col}


@app.get("/api/kanban/tareas/{task_id}/detalle")
async def kanban_tarea_detalle(task_id: str):
    """Detalle completo: tarea + tiempos + subtareas + notas tipificadas."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        r = await conn.fetchrow("""
            SELECT k.*, p.nombre AS tecnico_nombre, p.silo_especialidad AS depto, p.carga_actual,
                   ir.ticket_id AS run_ticket, ir.sla_limite AS sla_horas, ir.timestamp_creacion AS run_creada,
                   cb.id_proyecto AS prj_id, cb.nombre_proyecto AS prj_nombre
            FROM kanban_tareas k
            LEFT JOIN pmo_staff_skills p ON k.id_tecnico = p.id_recurso
            LEFT JOIN incidencias_run ir ON k.id_incidencia = ir.ticket_id
            LEFT JOIN cartera_build cb ON k.id_proyecto = cb.id_proyecto
            WHERE k.id=$1
        """, task_id)
        if not r:
            raise HTTPException(404, "Tarea no encontrada")

        # Tiempos de ciclo
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        def _to_utc(dt):
            if dt is None: return None
            if dt.tzinfo is None: return dt.replace(tzinfo=timezone.utc)
            return dt
        creada = _to_utc(r['fecha_creacion'])
        inicio = _to_utc(r['fecha_inicio_ejecucion'])
        cierre = _to_utc(r['fecha_cierre'])
        # En espera: creación → primera asignación (proxy: hasta inicio_ejecucion o ahora)
        if inicio:
            espera_min = int((inicio - creada).total_seconds() / 60) if creada else 0
        else:
            espera_min = int((now_utc - creada).total_seconds() / 60) if creada else 0
        # Activo: inicio → cierre (o ahora)
        if inicio:
            ref_fin = cierre or now_utc
            activo_min = int((ref_fin - inicio).total_seconds() / 60)
        else:
            activo_min = 0
        def _fmt_dur(m):
            if m < 60: return f"{m} min"
            h = m // 60
            mm = m % 60
            return f"{h}h {mm}m" if mm else f"{h}h"
        def _fmt_hhmm(dt):
            if not dt: return "—"
            return dt.strftime("%H:%M")

        # Subtareas
        subtareas = []
        if r['tipo'] == 'BUILD':
            sub_rows = await conn.fetch(
                "SELECT id, titulo, estado, horas_estimadas, criterio_exito FROM build_subtasks WHERE id_tarea_padre=$1 ORDER BY orden", task_id)
            for s in sub_rows:
                est = (s['estado'] or 'PENDIENTE').upper()
                tag = 'todo'
                tag_lbl = 'Pendiente'
                if est in ('COMPLETADA', 'COMPLETADO', 'DONE'):
                    tag = 'done'; tag_lbl = '✓ Completada'
                elif est in ('EN_PROGRESO', 'EN PROGRESO', 'DOING', 'EN_CURSO'):
                    tag = 'doing'; tag_lbl = '⚡ En curso'
                subtareas.append({
                    "id": s['id'], "titulo": s['titulo'], "tag": tag, "tag_lbl": tag_lbl,
                    "horas": float(s['horas_estimadas'] or 0), "nota": s['criterio_exito'] or '',
                })

        # Notas: leer de tech_chat_mensajes via sala (tipo+ref)
        notas = []
        try:
            tipo_sala = 'run' if r['tipo'] == 'RUN' else 'build'
            ref = r['id_incidencia'] or r['id_proyecto'] or task_id
            sala_id = await conn.fetchval(
                "SELECT id FROM tech_chat_salas WHERE tipo=$1 AND id_referencia=$2", tipo_sala, ref)
            if sala_id:
                msg_rows = await conn.fetch(
                    "SELECT id_autor, rol_autor, mensaje, created_at FROM tech_chat_mensajes WHERE id_sala=$1 ORDER BY created_at ASC LIMIT 200",
                    sala_id)
                for m in msg_rows:
                    autor = m['id_autor'] or '?'
                    rol = m['rol_autor']
                    if rol == 'agente':
                        if autor.startswith('AG-SYS') or 'SYSTEM' in autor.upper():
                            cls = 'sys'; lbl = 'Sistema'
                        elif 'SLA' in autor.upper() or 'MONITOR' in autor.upper():
                            cls = 'alert'; lbl = '⚠ '+autor
                        else:
                            cls = 'ag'; lbl = '⬢ '+autor
                    else:
                        cls = ''; lbl = autor
                    notas.append({
                        "cls": cls, "autor": lbl, "mensaje": m['mensaje'],
                        "time": m['created_at'].strftime("%H:%M:%S") if m['created_at'] else '',
                    })
        except Exception as e:
            logger.warning(f"No se pudieron cargar notas para {task_id}: {e}")

        # Sintetizar notas desde historial_columnas (P95 FASE 10 fix)
        # para tareas que no tienen entradas en tech_chat_mensajes
        try:
            hist = r['historial_columnas']
            if isinstance(hist, str):
                hist = json.loads(hist)
            if hist and isinstance(hist, list) and not notas:
                for h in hist:
                    ts = h.get('timestamp', '')
                    col = h.get('columna', '?')
                    est = h.get('estado', '')
                    time_str = ''
                    if ts:
                        try:
                            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                            time_str = dt.strftime("%d/%m %H:%M")
                        except Exception:
                            time_str = ts[:16]
                    msg = f"Transición a columna {col}" + (f" (estado: {est})" if est else "")
                    notas.append({
                        "cls": "sys",
                        "autor": "Sistema · historial",
                        "mensaje": msg,
                        "time": time_str,
                    })
        except Exception as e:
            logger.warning(f"No se pudo sintetizar historial para {task_id}: {e}")

        # Descripción: kanban_tareas.descripcion
        descripcion = r['descripcion'] if 'descripcion' in r.keys() and r['descripcion'] else None

        # SLA segundos restantes (igual que /api/kanban/tareas)
        sla_seg = None
        if r['tipo'] == 'RUN' and r['sla_horas']:
            base_sla = r['run_creada'] or r['fecha_creacion']
            if base_sla:
                if base_sla.tzinfo is None:
                    base_sla = base_sla.replace(tzinfo=timezone.utc)
                fin_sla = base_sla.timestamp() + (float(r['sla_horas']) * 3600)
                sla_seg = int(fin_sla - now_utc.timestamp())

        # Dependencias (heurística por bloqueador)
        deps = []
        if r['bloqueador']:
            txt = str(r['bloqueador'])
            ids_match = re.findall(r'(KT-[A-Z0-9-]+|INC-[A-Z0-9-]+|PRJ-?\d+|BLD-[A-Z0-9-]+)', txt)
            for did in ids_match:
                if did != task_id:
                    deps.append({"target_id": did, "tipo": "bloqueado_por", "agente": "AG-004"})

        # Construir respuesta
        return {
            "id": r['id'],
            "tipo": r['tipo'],
            "titulo": r['titulo'],
            "descripcion": descripcion,
            "prioridad": r['prioridad'],
            "estado_logico": _kb_estado_actual(r['columna'], r['id_tecnico']),
            "columna": r['columna'],
            "tecnico": ({"id": r['id_tecnico'], "nombre": r['tecnico_nombre'], "carga": r['carga_actual'] or 0,
                         "departamento": r['depto']}
                        if r['id_tecnico'] else None),
            "depto": r['depto'] or 'Sin asignar',
            "ci": r['run_ticket'],
            "proyecto": ({"id": r['prj_id'], "nombre": r['prj_nombre']} if r['prj_id'] else None),
            "horas_estimadas": float(r['horas_estimadas'] or 0),
            "horas_reales": float(r['horas_reales'] or 0),
            "fecha_creacion": creada.isoformat() if creada else None,
            "sla_seg": sla_seg,
            "bloqueador": r['bloqueador'],
            "deps": deps,
            "tiempos": {
                "en_espera": _fmt_dur(espera_min),
                "asignacion": _fmt_hhmm(inicio) if inicio else _fmt_hhmm(creada),
                "primer_toque": _fmt_hhmm(inicio) if inicio else "—",
                "activo": _fmt_dur(activo_min),
            },
            "subtareas": subtareas,
            "notas": notas,
            "agente_origen": "AG-002" if r['tipo'] == 'RUN' else "AG-013",
        }


# ── Kanban: departamentos / técnicos / asignación cascada (P95 FASE 10) ──

@app.get("/api/kanban/departamentos")
async def kanban_departamentos():
    """Lista de departamentos (silos) disponibles para asignación."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT DISTINCT silo_especialidad
            FROM pmo_staff_skills
            WHERE silo_especialidad IS NOT NULL
            ORDER BY silo_especialidad
        """)
        return [r['silo_especialidad'] for r in rows]


@app.get("/api/kanban/tecnicos")
async def kanban_tecnicos_por_dpto(departamento: Optional[str] = None):
    """Técnicos del departamento solicitado, con su carga actual."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        if departamento:
            rows = await conn.fetch("""
                SELECT id_recurso, nombre, nivel, carga_actual, estado_run
                FROM pmo_staff_skills
                WHERE silo_especialidad = $1 AND estado_run NOT IN ('BAJA','VACACIONES')
                ORDER BY carga_actual ASC, nombre ASC
            """, departamento)
        else:
            rows = await conn.fetch("""
                SELECT id_recurso, nombre, nivel, carga_actual, estado_run, silo_especialidad
                FROM pmo_staff_skills
                WHERE estado_run NOT IN ('BAJA','VACACIONES')
                ORDER BY silo_especialidad, carga_actual ASC LIMIT 200
            """)
        return [dict(r) for r in rows]


class KanbanAsignacion(BaseModel):
    departamento: Optional[str] = None
    id_tecnico: Optional[str] = None


@app.patch("/api/kanban/tareas/{task_id}/asignacion")
async def kanban_patch_asignacion(task_id: str, body: KanbanAsignacion):
    """Cambia la asignación de técnico (y por extensión, departamento) de una tarea.
    Inserta nota sys automática en tech_chat_mensajes con detalle del cambio.
    """
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        old = await conn.fetchrow(
            "SELECT id, titulo, tipo, id_tecnico, id_incidencia, id_proyecto FROM kanban_tareas WHERE id=$1",
            task_id)
        if not old:
            raise HTTPException(404, "Tarea no encontrada")

        # Validar técnico si se proporciona
        tec_info = None
        if body.id_tecnico:
            tec_info = await conn.fetchrow(
                "SELECT id_recurso, nombre, silo_especialidad, carga_actual FROM pmo_staff_skills WHERE id_recurso=$1",
                body.id_tecnico)
            if not tec_info:
                raise HTTPException(400, f"Técnico no encontrado: {body.id_tecnico}")
            # Si se proporciona departamento, debe coincidir con el silo del técnico
            if body.departamento and body.departamento != tec_info['silo_especialidad']:
                raise HTTPException(400, f"El técnico {body.id_tecnico} no pertenece al dpto {body.departamento} (silo real: {tec_info['silo_especialidad']})")

        # Actualizar id_tecnico en kanban_tareas
        nuevo_tec_id = body.id_tecnico  # puede ser None (desasignar)
        await conn.execute(
            "UPDATE kanban_tareas SET id_tecnico=$2 WHERE id=$1",
            task_id, nuevo_tec_id)

        # Sincronizar carga del técnico (suma horas estimadas pendientes)
        try:
            await _sync_tecnico_estado(conn, nuevo_tec_id)
            if old['id_tecnico'] and old['id_tecnico'] != nuevo_tec_id:
                await _sync_tecnico_estado(conn, old['id_tecnico'])
        except Exception:
            pass

        # Insertar nota sys en tech_chat_mensajes
        try:
            tipo_sala = 'run' if old['tipo'] == 'RUN' else 'build'
            ref = old['id_incidencia'] or old['id_proyecto'] or task_id
            sala_id = await conn.fetchval(
                """INSERT INTO tech_chat_salas (tipo, id_referencia, nombre)
                   VALUES ($1,$2,$3) ON CONFLICT (tipo,id_referencia) DO UPDATE SET activa=TRUE
                   RETURNING id""",
                tipo_sala, ref, f"{ref} · {(old['titulo'] or '')[:80]}")
            if tec_info:
                msg = f"Tarea asignada a {tec_info['nombre']} ({tec_info['silo_especialidad']})"
            else:
                msg = "Tarea desasignada (sin técnico)"
            await conn.execute(
                """INSERT INTO tech_chat_mensajes (id_sala, id_autor, rol_autor, mensaje)
                   VALUES ($1,'AG-SYS','agente',$2)""",
                sala_id, msg)
        except Exception as e:
            logger.warning(f"No se pudo crear nota sys de asignación para {task_id}: {e}")

        return {
            "ok": True,
            "task_id": task_id,
            "id_tecnico": nuevo_tec_id,
            "tecnico": {
                "id": tec_info['id_recurso'],
                "nombre": tec_info['nombre'],
                "departamento": tec_info['silo_especialidad'],
                "carga": tec_info['carga_actual'] or 0,
            } if tec_info else None,
        }


# ── Kanban WIP limits (P95 FASE 9) ────────────────────────────────────────
# Tabla kanban_wip_limits: límite máximo de tareas por columna lógica.
# Si no hay registro o limite IS NULL, la columna no tiene límite (∞).

_KB_WIP_VALID_COLS = {'unassigned', 'asignada', 'en_curso', 'pte_tercero', 'resuelta'}


class KanbanWipLimit(BaseModel):
    limite: Optional[int] = None  # None = sin límite


@app.get("/api/kanban/wip-limits")
async def kanban_wip_limits_get():
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT columna, limite, updated_at FROM kanban_wip_limits")
        result = {r['columna']: {"limite": r['limite'], "updated_at": r['updated_at'].isoformat() if r['updated_at'] else None} for r in rows}
        # Asegurar que las 5 columnas estén presentes (con limite=None si no hay registro)
        for c in _KB_WIP_VALID_COLS:
            if c not in result:
                result[c] = {"limite": None, "updated_at": None}
        return result


@app.put("/api/kanban/wip-limits/{columna}")
async def kanban_wip_limits_put(columna: str, body: KanbanWipLimit):
    if columna not in _KB_WIP_VALID_COLS:
        raise HTTPException(400, f"Columna inválida: {columna}. Permitidas: {sorted(_KB_WIP_VALID_COLS)}")
    if body.limite is not None and body.limite < 0:
        raise HTTPException(400, "El límite debe ser >= 0 o null")
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO kanban_wip_limits (columna, limite, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (columna) DO UPDATE SET limite=EXCLUDED.limite, updated_at=NOW()
        """, columna, body.limite)
        return {"ok": True, "columna": columna, "limite": body.limite}


@app.get("/api/kanban/export-pdf")
async def kanban_export_pdf(tipo: Optional[str] = None, prioridad: Optional[str] = None):
    """Snapshot PDF del estado actual del kanban global.
    Incluye: KPIs flow-metrics + 5 columnas resumidas + top 10 tareas críticas.
    Usa reportlab (verificado en requirements). filters opcionales aplican a las tareas.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.enums import TA_LEFT
    except ImportError:
        raise HTTPException(500, "reportlab no disponible. Instalar: pip install reportlab")

    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        # Obtener métricas (mismo cálculo que /flow-metrics, simplificado)
        total = await conn.fetchval("SELECT COUNT(*) FROM kanban_tareas")
        completadas_30d = await conn.fetchval(
            "SELECT COUNT(*) FROM kanban_tareas WHERE columna='Completado' AND fecha_cierre >= NOW() - INTERVAL '30 days'")
        wip = await conn.fetchval("SELECT COUNT(*) FROM kanban_tareas WHERE columna NOT IN ('Backlog','Completado')")
        bloqueadas = await conn.fetchval("SELECT COUNT(*) FROM kanban_tareas WHERE columna='Bloqueado'")
        lead_time = await conn.fetchval("""
            SELECT COALESCE(AVG(EXTRACT(EPOCH FROM (fecha_cierre - fecha_creacion))/3600), 0)
            FROM kanban_tareas WHERE columna='Completado' AND fecha_cierre >= NOW() - INTERVAL '30 days'
        """) or 0

        # Obtener tareas (con filtros opcionales)
        where = []
        params = []
        if tipo and tipo.upper() in ('RUN', 'BUILD'):
            params.append(tipo.upper()); where.append(f"tipo=${len(params)}")
        pri_map = {"p1": "Crítica", "p2": "Alta", "p3": "Media", "p4": "Baja"}
        if prioridad and prioridad.lower() in pri_map:
            params.append(pri_map[prioridad.lower()]); where.append(f"prioridad=${len(params)}")
        wsql = ("WHERE " + " AND ".join(where)) if where else ""
        rows = await conn.fetch(f"SELECT id, tipo, prioridad, columna, titulo, id_tecnico FROM kanban_tareas {wsql}", *params)

        # Distribución por columna lógica (5 estados)
        def estado_of(col, tec):
            if col == 'Completado': return 'Resuelta'
            if col == 'Bloqueado': return 'Pte. tercero'
            if col in ('En Progreso', 'Code Review', 'Testing', 'Despliegue'): return 'En curso'
            if not tec: return 'Sin asignar'
            return 'Asignada'
        col_counts = {'Sin asignar':0,'Asignada':0,'En curso':0,'Pte. tercero':0,'Resuelta':0}
        for r in rows:
            col_counts[estado_of(r['columna'], r['id_tecnico'])] += 1

        # Top 10 tareas críticas (P1/P2 no resueltas)
        criticas = await conn.fetch(f"""
            SELECT k.id, k.tipo, k.prioridad, k.titulo, k.columna,
                   p.nombre AS tecnico_nombre
            FROM kanban_tareas k
            LEFT JOIN pmo_staff_skills p ON k.id_tecnico = p.id_recurso
            WHERE k.prioridad IN ('Crítica','Alta') AND k.columna != 'Completado'
            {(' AND ' + ' AND '.join(where)) if where else ''}
            ORDER BY CASE k.prioridad WHEN 'Crítica' THEN 0 WHEN 'Alta' THEN 1 ELSE 2 END,
                     k.fecha_creacion DESC LIMIT 10
        """, *params)

    # Construir el PDF en memoria
    import io
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0d1117'), spaceAfter=4)
    h2 = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#39d2c0'), spaceAfter=6, spaceBefore=10)
    p_small = ParagraphStyle('ps', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#6e7681'))
    p_norm = ParagraphStyle('pn', parent=styles['Normal'], fontSize=9, leading=11)

    story = []
    story.append(Paragraph("Cognitive PMO — Kanban Global", h1))
    story.append(Paragraph(f"Snapshot generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", p_small))
    if tipo or prioridad:
        f_lbl = []
        if tipo: f_lbl.append(f"tipo={tipo}")
        if prioridad: f_lbl.append(f"prioridad={prioridad}")
        story.append(Paragraph(f"Filtros: {' · '.join(f_lbl)}", p_small))
    story.append(Spacer(1, 8))

    # KPIs
    story.append(Paragraph("Métricas de flujo (ventana 30 días)", h2))
    kpi_data = [
        ['Total tareas', 'Completadas', 'Throughput/sem', 'Lead Time', 'WIP', 'Bloqueadas'],
        [str(total or 0), str(completadas_30d or 0), f"{round((completadas_30d or 0)/4.3,1)}",
         f"{round(float(lead_time),1)}h", str(wip or 0), str(bloqueadas or 0)],
    ]
    t = Table(kpi_data, colWidths=[30*mm]*6)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1c2128')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#8b949e')),
        ('FONTSIZE', (0,0), (-1,0), 7),
        ('FONTSIZE', (0,1), (-1,1), 13),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,1), (-1,1), colors.HexColor('#58a6ff')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#30363d')),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#30363d')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # 5 columnas resumidas
    story.append(Paragraph("Distribución por estado", h2))
    col_data = [['Estado','Tareas']] + [[k, str(v)] for k,v in col_counts.items()]
    t2 = Table(col_data, colWidths=[100*mm, 30*mm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1c2128')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#8b949e')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#30363d')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f6f8fa')]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t2)
    story.append(Spacer(1, 12))

    # Top 10 críticas
    story.append(Paragraph(f"Top {len(criticas)} tareas críticas (P1/P2 no resueltas)", h2))
    crit_data = [['#','Tipo','Prio','ID','Título','Columna','Técnico']]
    for i, c in enumerate(criticas, 1):
        title = (c['titulo'] or '')[:55] + ('…' if c['titulo'] and len(c['titulo']) > 55 else '')
        crit_data.append([str(i), c['tipo'], c['prioridad'], c['id'][:18], title, c['columna'], (c['tecnico_nombre'] or '—')[:18]])
    t3 = Table(crit_data, colWidths=[8*mm, 14*mm, 14*mm, 30*mm, 65*mm, 22*mm, 27*mm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1c2128')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#8b949e')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#30363d')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f6f8fa')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t3)

    story.append(Spacer(1, 18))
    story.append(Paragraph("Cognitive PMO · TFM Jose Antonio Martínez Victoria", p_small))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    from fastapi.responses import Response
    fname = f"kanban-snapshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@app.get("/api/kanban/flow-metrics")
async def kanban_flow_metrics():
    """Métricas Kanban transversales (RUN+BUILD) para panel de flujo. Ventana 30 días."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        # Totales globales (no solo 30d)
        total = await conn.fetchval("SELECT COUNT(*) FROM kanban_tareas")
        # Completadas en 30d
        completadas = await conn.fetchval("""
            SELECT COUNT(*) FROM kanban_tareas
            WHERE columna='Completado' AND fecha_cierre >= NOW() - INTERVAL '30 days'
        """)
        # Throughput / semana (completadas / 4.3)
        throughput = round((completadas or 0) / 4.3, 1)
        # Lead Time medio (h): fecha_creacion → fecha_cierre
        lead_time = await conn.fetchval("""
            SELECT COALESCE(AVG(EXTRACT(EPOCH FROM (fecha_cierre - fecha_creacion))/3600), 0)
            FROM kanban_tareas
            WHERE columna='Completado' AND fecha_cierre >= NOW() - INTERVAL '30 days'
              AND fecha_cierre IS NOT NULL AND fecha_creacion IS NOT NULL
        """)
        # Cycle Time medio (h): fecha_inicio_ejecucion → fecha_cierre
        cycle_time = await conn.fetchval("""
            SELECT COALESCE(AVG(EXTRACT(EPOCH FROM (fecha_cierre - fecha_inicio_ejecucion))/3600), 0)
            FROM kanban_tareas
            WHERE columna='Completado' AND fecha_cierre >= NOW() - INTERVAL '30 days'
              AND fecha_cierre IS NOT NULL AND fecha_inicio_ejecucion IS NOT NULL
        """)
        flow_eff = round(float(cycle_time) / float(lead_time) * 100, 1) if lead_time and float(lead_time) > 0 else 0.0

        # WIP: tareas en curso (no Backlog ni Completado)
        wip = await conn.fetchval("""
            SELECT COUNT(*) FROM kanban_tareas
            WHERE columna NOT IN ('Backlog','Completado')
        """)
        bloqueadas = await conn.fetchval("""
            SELECT COUNT(*) FROM kanban_tareas WHERE columna='Bloqueado'
        """)

        # CFD: 30 puntos diarios. Para cada día, snapshot del estado de cada tarea
        # creada antes del día y no cerrada antes del día.
        cfd_rows = await conn.fetch("""
            WITH dias AS (
                SELECT generate_series(NOW()::date - INTERVAL '29 days', NOW()::date, INTERVAL '1 day')::date AS dia
            )
            SELECT d.dia,
                   COUNT(*) FILTER (WHERE k.columna='Backlog') AS backlog,
                   COUNT(*) FILTER (WHERE k.columna='Análisis') AS analisis,
                   COUNT(*) FILTER (WHERE k.columna='En Progreso') AS en_progreso,
                   COUNT(*) FILTER (WHERE k.columna IN ('Code Review','Testing')) AS review_test,
                   COUNT(*) FILTER (WHERE k.columna='Despliegue') AS deploy,
                   COUNT(*) FILTER (WHERE k.columna='Completado') AS completado,
                   COUNT(*) AS total
            FROM dias d
            LEFT JOIN kanban_tareas k
              ON k.fecha_creacion::date <= d.dia
              AND (k.fecha_cierre IS NULL OR k.fecha_cierre::date > d.dia OR k.columna != 'Completado')
            GROUP BY d.dia ORDER BY d.dia
        """)
        cfd = [{"dia": r['dia'].isoformat(), "backlog": r['backlog'], "analisis": r['analisis'],
                "en_progreso": r['en_progreso'], "review_test": r['review_test'],
                "deploy": r['deploy'], "completado": r['completado'], "total": r['total']} for r in cfd_rows]

        # Control chart: cada tarea completada en 30d con su lead time
        cc_rows = await conn.fetch("""
            SELECT fecha_cierre::date AS dia,
                   EXTRACT(EPOCH FROM (fecha_cierre - fecha_creacion))/3600 AS lt_h,
                   id, titulo
            FROM kanban_tareas
            WHERE columna='Completado' AND fecha_cierre >= NOW() - INTERVAL '30 days'
              AND fecha_cierre IS NOT NULL AND fecha_creacion IS NOT NULL
            ORDER BY fecha_cierre
        """)
        control_chart = [{"dia": r['dia'].isoformat(), "lt_h": round(float(r['lt_h']), 1),
                          "id": r['id'], "titulo": r['titulo']} for r in cc_rows]
        # UCL = avg + 3*stdev (aproximado: max observado * 1.2 si pocos datos)
        if control_chart:
            lts = [c['lt_h'] for c in control_chart]
            avg_lt = sum(lts) / len(lts)
            if len(lts) > 1:
                var = sum((x - avg_lt) ** 2 for x in lts) / len(lts)
                std = var ** 0.5
                ucl = round(avg_lt + 3 * std, 1)
            else:
                ucl = round(avg_lt * 2, 1)
        else:
            ucl = 0
            avg_lt = 0

        # Distribución WIP
        dist_tipo = await conn.fetch("""
            SELECT tipo, COUNT(*) AS cnt FROM kanban_tareas
            WHERE columna NOT IN ('Backlog','Completado') GROUP BY tipo
        """)
        dist_prio = await conn.fetch("""
            SELECT prioridad, COUNT(*) AS cnt FROM kanban_tareas
            WHERE columna NOT IN ('Backlog','Completado') GROUP BY prioridad
        """)
        # Departamento desde silo del técnico
        dist_dept = await conn.fetch("""
            SELECT COALESCE(p.silo_especialidad,'Sin asignar') AS dept, COUNT(*) AS cnt
            FROM kanban_tareas k
            LEFT JOIN pmo_staff_skills p ON k.id_tecnico = p.id_recurso
            WHERE k.columna NOT IN ('Backlog','Completado')
            GROUP BY dept ORDER BY cnt DESC
        """)
        wip_dist = {
            "por_tipo": {r['tipo']: r['cnt'] for r in dist_tipo},
            "por_prioridad": {r['prioridad']: r['cnt'] for r in dist_prio},
            "por_dept": [{"dept": r['dept'], "cnt": r['cnt']} for r in dist_dept],
        }

        return {
            "total": total or 0,
            "completadas": completadas or 0,
            "throughput": throughput,
            "leadTime": round(float(lead_time or 0), 1),
            "cycleTime": round(float(cycle_time or 0), 1),
            "flowEff": flow_eff,
            "cfd": cfd,
            "controlChart": control_chart,
            "ucl": ucl,
            "avgLt": round(avg_lt, 1),
            "wipDist": wip_dist,
            "wip": wip or 0,
            "bloqueadas": bloqueadas or 0,
            "ventana_dias": 30,
        }


# ── P100 Gantt F4: PATCH gantt metadata en descripcion ─────────────────────

class GanttPatch(BaseModel):
    titulo: Optional[str] = None
    id_tecnico: Optional[str] = None
    columna: Optional[str] = None
    prioridad: Optional[str] = None
    horas_estimadas: Optional[float] = None
    gantt: Optional[dict] = None


@app.patch("/api/pm/gantt/tarea/{task_id}")
async def pm_gantt_patch_tarea(task_id: str, body: GanttPatch):
    """Update kanban task fields + merge gantt metadata into descripcion."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            exists = await conn.fetchval(
                "SELECT id FROM kanban_tareas WHERE id = $1", task_id)
            if not exists:
                raise HTTPException(404, f"Tarea {task_id} no encontrada")

            # Native column updates
            sets = []
            vals = [task_id]  # $1
            idx = 2
            if body.titulo is not None:
                sets.append(f"titulo = ${idx}"); vals.append(body.titulo); idx += 1
            if body.id_tecnico is not None:
                sets.append(f"id_tecnico = ${idx}"); vals.append(body.id_tecnico); idx += 1
            if body.columna is not None:
                sets.append(f"columna = ${idx}"); vals.append(body.columna); idx += 1
            if body.prioridad is not None:
                sets.append(f"prioridad = ${idx}"); vals.append(body.prioridad); idx += 1
            if body.horas_estimadas is not None:
                sets.append(f"horas_estimadas = ${idx}"); vals.append(body.horas_estimadas); idx += 1

            if sets:
                sql = f"UPDATE kanban_tareas SET {', '.join(sets)} WHERE id = $1"
                await conn.execute(sql, *vals)

            # Gantt metadata merge into descripcion JSONB
            if body.gantt:
                gantt_json = json.dumps({"gantt": body.gantt})
                await conn.execute(
                    "UPDATE kanban_tareas "
                    "SET descripcion = (COALESCE(descripcion,'{}')::jsonb || $1::jsonb)::text "
                    "WHERE id = $2",
                    gantt_json, task_id)

            # Audit trail: append to descripcion->'historial'
            changes = {k: v for k, v in body.dict().items() if v is not None}
            if changes:
                entry = json.dumps({"ts": datetime.now().isoformat(), "user": "PM-016", "changes": changes})
                await conn.execute(
                    "UPDATE kanban_tareas SET descripcion = jsonb_set("
                    "  COALESCE(descripcion,'{}')::jsonb,"
                    "  '{historial}',"
                    "  COALESCE((COALESCE(descripcion,'{}')::jsonb)->'historial','[]'::jsonb) || $1::jsonb"
                    ")::text WHERE id = $2",
                    entry, task_id)

            return {"ok": True, "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Gantt patch error: {e}")
        raise HTTPException(500, str(e))


# ── F1 helper: traducir 'PM-XXX' (legacy varchar) → id_usuario INTEGER ──
async def _resolve_pm_id(conn, pm_id: str) -> int:
    """FASE 1: cartera_build.id_pm_usuario migrado a INTEGER FK rbac_usuarios.
    Los endpoints siguen aceptando 'PM-XXX' por compatibilidad frontend (P98).
    404 si el PM no tiene rbac link (huérfanos PM-001..PM-015 hasta Fase 2)."""
    if pm_id and isinstance(pm_id, str) and pm_id.startswith('PM-'):
        val = await conn.fetchval("SELECT compartido.fn_map_pm_code_to_rbac($1)", pm_id)
    else:
        try:
            val = int(pm_id)
        except (TypeError, ValueError):
            val = None
    if val is None:
        raise HTTPException(status_code=404, detail=f"PM no encontrado en RBAC: {pm_id}")
    return val


# ── P100 Gantt F2: Endpoint datos Gantt ────────────────────────────────────

@app.get("/api/pm/gantt")
async def pm_gantt(pm_id: str = "PM-016"):
    """Datos Gantt: proyectos + tareas con fechas planificadas."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            pm_id_int = await _resolve_pm_id(conn, pm_id)

            # Projects
            prj_rows = await conn.fetch(
                "SELECT id_proyecto, nombre_proyecto FROM cartera_build "
                "WHERE id_pm_usuario = $1 ORDER BY id_proyecto", pm_id_int)
            prj_ids = [r['id_proyecto'] for r in prj_rows]
            if not prj_ids:
                return {"proyectos": [], "tareas": [], "tecnicos_pool": []}

            # Color palette per project
            colors = ['#58a6ff','#3fb950','#f85149','#d29922','#bc8cff',
                      '#39d2c0','#f778ba','#79c0ff','#7ee787','#ffa657',
                      '#d2a8ff','#56d4dd']

            proyectos = []
            for i, r in enumerate(prj_rows):
                n_tareas = await conn.fetchval(
                    "SELECT COUNT(*) FROM kanban_tareas WHERE id_proyecto = $1", r['id_proyecto']) or 0
                proyectos.append({
                    "id": r['id_proyecto'], "nombre": r['nombre_proyecto'],
                    "color": colors[i % len(colors)], "n_tareas": n_tareas,
                })

            # Tasks
            task_rows = await conn.fetch("""
                SELECT k.id, k.titulo, k.id_proyecto, k.id_tecnico,
                       k.columna, k.prioridad, k.horas_estimadas,
                       k.fecha_creacion, k.descripcion
                FROM kanban_tareas k
                WHERE k.id_proyecto = ANY($1)
                ORDER BY k.id_proyecto, k.fecha_creacion
            """, prj_ids)

            today = date.today()
            tareas = []
            for r in task_rows:
                # Parse gantt metadata from descripcion JSONB (text column)
                desc = {}
                fuente = 'derived'
                if r['descripcion']:
                    try:
                        desc = json.loads(r['descripcion']) if isinstance(r['descripcion'], str) else r['descripcion']
                    except:
                        pass

                gantt_meta = desc.get('gantt', {}) if isinstance(desc, dict) else {}

                h_est = float(r['horas_estimadas'] or 1)
                fc = r['fecha_creacion']
                fc_date = fc.date() if hasattr(fc, 'date') else (fc or today)

                if gantt_meta and gantt_meta.get('start'):
                    inicio = gantt_meta['start']
                    fin = gantt_meta.get('end') or str(fc_date + timedelta(days=max(1, int(h_est / 8))))
                    fuente = 'stored'
                else:
                    inicio = str(fc_date)
                    dur_days = max(1, int(h_est / 8 + 0.99))
                    fin = str(fc_date + timedelta(days=dur_days))

                # % completado from columna
                col_pct = {'Backlog': 0, 'Análisis': 10, 'En Progreso': 40,
                           'Code Review': 60, 'Testing': 75, 'Despliegue': 90,
                           'Bloqueado': 30, 'Completado': 100, 'Done': 100}
                pct = gantt_meta.get('pct', col_pct.get(r['columna'], 0))

                # Predecessors
                pred = gantt_meta.get('pred', [])
                if isinstance(pred, str):
                    pred = [pred] if pred else []

                # Technician name
                tec_nombre = None
                if r['id_tecnico']:
                    tec_nombre = await conn.fetchval(
                        "SELECT nombre FROM compartido.pmo_staff_skills WHERE id_recurso = $1",
                        r['id_tecnico'])

                tareas.append({
                    "id": r['id'], "titulo": r['titulo'],
                    "id_proyecto": r['id_proyecto'],
                    "id_tecnico": r['id_tecnico'] or '',
                    "tecnico_nombre": tec_nombre or r['id_tecnico'] or '',
                    "columna": r['columna'], "prioridad": r['prioridad'],
                    "horas_estimadas": h_est,
                    "inicio": inicio, "fin": fin,
                    "pct_completado": pct,
                    "predecesoras": pred,
                    "fuente_fechas": fuente,
                    "historial": (desc.get('historial', []) if isinstance(desc, dict) else [])[-5:],
                })

            # Technician pool (for reassignment dropdown)
            month_start = today.replace(day=1)
            pool_rows = await conn.fetch("""
                SELECT s.id_recurso, s.nombre, s.skill_principal,
                       COALESCE(h.total_h, 0) AS carga_h
                FROM compartido.pmo_staff_skills s
                LEFT JOIN (
                    SELECT id_tecnico, SUM(horas) AS total_h
                    FROM primitiva.horas_imputadas
                    WHERE fecha >= $1
                    GROUP BY id_tecnico
                ) h ON h.id_tecnico = s.id_recurso
                ORDER BY s.nombre
            """, month_start)

            tecnicos_pool = [{"id": r['id_recurso'], "nombre": r['nombre'],
                              "skill": r['skill_principal'] or '',
                              "carga_actual_h": round(float(r['carga_h']), 1)}
                             for r in pool_rows]

            return {
                "proyectos": proyectos,
                "tareas": tareas,
                "tecnicos_pool": tecnicos_pool,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Gantt error: {e}")
        raise HTTPException(500, str(e))


# ── PM Dashboard — Pulido v3 F2: Ficha 360 ────────────────────────────────

@app.get("/api/pm/team/tecnico/{id_tecnico}/ficha-360")
async def pm_tecnico_ficha_360(id_tecnico: str, pm_id: str = "PM-016"):
    """Ficha 360 del técnico: KPIs + sparkline + proyectos con detalle."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            pm_id_int = await _resolve_pm_id(conn, pm_id)

            staff = await conn.fetchrow(
                "SELECT nombre, nivel, silo_especialidad, skill_principal, skills_json, email, telefono "
                "FROM compartido.pmo_staff_skills WHERE id_recurso = $1", id_tecnico)
            if not staff:
                raise HTTPException(404, f"Técnico {id_tecnico} no encontrado")

            today = date.today()
            month_start = today.replace(day=1)
            seed_val = int(hashlib.md5(id_tecnico.encode()).hexdigest()[:8], 16) % 100

            # ── KPIs ──
            horas_mes = await conn.fetchval(
                "SELECT COALESCE(SUM(horas), 0) FROM primitiva.horas_imputadas "
                "WHERE id_tecnico = $1 AND fecha >= $2", id_tecnico, month_start)
            horas_mes = round(float(horas_mes), 1)

            # Projects of this PM where tech participates
            pm_prj_ids = [r['id_proyecto'] for r in await conn.fetch(
                "SELECT id_proyecto FROM cartera_build WHERE id_pm_usuario = $1", pm_id_int)]

            num_proyectos = await conn.fetchval(
                "SELECT COUNT(DISTINCT id_proyecto) FROM kanban_tareas "
                "WHERE id_tecnico = $1 AND id_proyecto = ANY($2)", id_tecnico, pm_prj_ids) or 0

            carga_pct = round(horas_mes / 160 * 100)
            coste_hora = round(45 + seed_val * 0.3, 2)

            # ── Sparkline 12 weeks ──
            twelve_weeks_ago = today - timedelta(weeks=12)
            sparkline_rows = await conn.fetch(
                "SELECT semana_iso, SUM(horas) AS total "
                "FROM primitiva.horas_imputadas "
                "WHERE id_tecnico = $1 AND fecha >= $2 "
                "GROUP BY semana_iso ORDER BY semana_iso",
                id_tecnico, twelve_weeks_ago)
            sparkline = [{"semana_iso": r['semana_iso'], "horas": round(float(r['total']), 1)}
                         for r in sparkline_rows]

            # ── Tareas activas totales ──
            # ── Tareas activas + liberación estimada ──
            active_tasks = await conn.fetch(
                "SELECT horas_estimadas, fecha_creacion FROM kanban_tareas "
                "WHERE id_tecnico = $1 AND columna NOT IN ('Completado','Done','Backlog')",
                id_tecnico)
            total_tareas_activas = len(active_tasks)

            if total_tareas_activas == 0:
                liberacion = {"tipo": "libre", "fecha": None, "dias_hasta": 0,
                              "horas_restantes": 0, "num_tareas_activas": 0}
            else:
                import math
                horas_rest = sum(float(t['horas_estimadas'] or 0) for t in active_tasks)
                max_fc = max((t['fecha_creacion'] for t in active_tasks if t['fecha_creacion']),
                             default=datetime.now())
                if hasattr(max_fc, 'date'):
                    max_fc = max_fc.date()
                dias_hasta = math.ceil(horas_rest / 8) if horas_rest > 0 else 1
                fecha_lib = max_fc + timedelta(days=dias_hasta)
                liberacion = {"tipo": "estimada", "fecha": str(fecha_lib),
                              "dias_hasta": dias_hasta, "horas_restantes": round(horas_rest, 1),
                              "num_tareas_activas": total_tareas_activas}
            ultima_imputacion = await conn.fetchval(
                "SELECT MAX(fecha) FROM primitiva.horas_imputadas WHERE id_tecnico = $1",
                id_tecnico)

            # ── Proyectos con detalle ──
            prj_rows = await conn.fetch(
                "SELECT h.id_proyecto, cb.nombre_proyecto, "
                "SUM(h.horas) AS horas_imputadas, COUNT(*) AS num_imputaciones, "
                "MAX(h.fecha) AS ultima_imputacion "
                "FROM primitiva.horas_imputadas h "
                "JOIN cartera_build cb ON h.id_proyecto = cb.id_proyecto "
                "WHERE h.id_tecnico = $1 AND cb.id_pm_usuario = $2 "
                "GROUP BY h.id_proyecto, cb.nombre_proyecto "
                "ORDER BY horas_imputadas DESC",
                id_tecnico, pm_id_int)

            proyectos = []
            for r in prj_rows:
                pid = r['id_proyecto']
                h_imp = round(float(r['horas_imputadas']), 1)
                pct_cons = round(h_imp / 160 * 100)

                # Tareas activas por columna para este proyecto
                tareas_cols = await conn.fetch(
                    "SELECT columna, COUNT(*) AS cnt FROM kanban_tareas "
                    "WHERE id_tecnico = $1 AND id_proyecto = $2 "
                    "AND columna NOT IN ('Completado','Done','Backlog') "
                    "GROUP BY columna ORDER BY cnt DESC",
                    id_tecnico, pid)

                proyectos.append({
                    "id_proyecto": pid,
                    "nombre": r['nombre_proyecto'],
                    "horas_imputadas": h_imp,
                    "capacidad_asignable": 160,
                    "pct_consumido": pct_cons,
                    "num_imputaciones": r['num_imputaciones'],
                    "ultima_imputacion": str(r['ultima_imputacion']) if r['ultima_imputacion'] else None,
                    "tareas_activas": [{"columna": t['columna'], "count": t['cnt']} for t in tareas_cols],
                })

            return {
                "id_tecnico": id_tecnico,
                "nombre": staff['nombre'],
                "nivel": staff['nivel'],
                "silo": staff['silo_especialidad'],
                "skill_principal": staff['skill_principal'],
                "skills": (json.loads(staff['skills_json']) if isinstance(staff['skills_json'], str) else staff['skills_json']) if staff['skills_json'] else [],
                "kpis": {
                    "carga_pct": carga_pct,
                    "horas_mes": horas_mes,
                    "num_proyectos": int(num_proyectos),
                    "coste_hora": coste_hora,
                },
                "sparkline_12w": sparkline,
                "total_tareas_activas": total_tareas_activas,
                "ultima_imputacion": str(ultima_imputacion) if ultima_imputacion else None,
                "proyectos": proyectos,
                "liberacion": liberacion,
            }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Ficha 360 error: {e}")
        raise HTTPException(500, str(e))


# ── PM Dashboard — Pulido v3 F3: Kanban técnico ───────────────────────────

@app.get("/api/pm/team/tecnico/{id_tecnico}/kanban")
async def pm_tecnico_kanban(id_tecnico: str):
    """Tareas kanban del técnico con campos extraídos del JSONB descripcion."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            rows = await conn.fetch("""
                SELECT id, titulo, tipo, prioridad, columna,
                       id_proyecto, id_incidencia,
                       horas_estimadas, horas_reales,
                       fecha_creacion, fecha_inicio_ejecucion, fecha_cierre,
                       descripcion::text AS descripcion_raw
                FROM kanban_tareas
                WHERE id_tecnico = $1
                ORDER BY
                  CASE columna
                    WHEN 'Backlog' THEN 0
                    WHEN 'Análisis' THEN 1
                    WHEN 'En Progreso' THEN 2
                    WHEN 'Code Review' THEN 3
                    WHEN 'Testing' THEN 4
                    WHEN 'Despliegue' THEN 5
                    WHEN 'Bloqueado' THEN 6
                    WHEN 'Completado' THEN 7
                  END,
                  CASE prioridad
                    WHEN 'Crítica' THEN 0 WHEN 'Alta' THEN 1
                    WHEN 'Media' THEN 2 ELSE 3
                  END,
                  fecha_creacion DESC
            """, id_tecnico)

            columnas_set = set()
            tareas = []
            for r in rows:
                columnas_set.add(r['columna'])
                # Parse JSONB description
                desc = {}
                try:
                    if r['descripcion_raw']:
                        desc = json.loads(r['descripcion_raw'])
                except:
                    pass

                checklist = desc.get('checklist', [])
                instrucciones = desc.get('instrucciones', [])

                tareas.append({
                    "id": r['id'],
                    "titulo": r['titulo'],
                    "tipo": r['tipo'],
                    "prioridad": r['prioridad'],
                    "columna": r['columna'],
                    "id_proyecto": r['id_proyecto'] or '',
                    "id_incidencia": r['id_incidencia'] or '',
                    "horas_estimadas": float(r['horas_estimadas'] or 0),
                    "horas_reales": float(r['horas_reales'] or 0),
                    "fecha_creacion": r['fecha_creacion'].isoformat() if r['fecha_creacion'] else None,
                    "fecha_inicio_ejecucion": r['fecha_inicio_ejecucion'].isoformat() if r['fecha_inicio_ejecucion'] else None,
                    "fecha_cierre": r['fecha_cierre'].isoformat() if r['fecha_cierre'] else None,
                    "skill_requerida": desc.get('skill_requerida', ''),
                    "silo": desc.get('silo', ''),
                    "checklist_total": len(checklist) if isinstance(checklist, list) else 0,
                    "instrucciones_total": len(instrucciones) if isinstance(instrucciones, list) else 0,
                    "descripcion_full": desc,
                })

            return {
                "id_tecnico": id_tecnico,
                "columnas_existentes": sorted(columnas_set),
                "tareas": tareas,
            }
    except Exception as e:
        logger.warning(f"Kanban tecnico error: {e}")
        raise HTTPException(500, str(e))


# ── PM Dashboard — Pulido v3 F4: Salas compartidas PM↔Técnico ──────────────

@app.get("/api/pm/team/tecnico/{id_tecnico}/salas-compartidas")
async def pm_tecnico_salas_compartidas(id_tecnico: str, pm_id: str = "PM-016"):
    """Salas de chat donde PM y técnico coinciden via proyectos compartidos."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            pm_id_int = await _resolve_pm_id(conn, pm_id)

            # Projects where PM is owner AND tech has tasks
            shared_prjs = await conn.fetch("""
                SELECT DISTINCT cb.id_proyecto, cb.nombre_proyecto,
                       COUNT(k.id) AS num_tareas
                FROM cartera_build cb
                JOIN kanban_tareas k ON k.id_proyecto = cb.id_proyecto
                WHERE cb.id_pm_usuario = $1 AND k.id_tecnico = $2
                GROUP BY cb.id_proyecto, cb.nombre_proyecto
            """, pm_id_int, id_tecnico)

            # Also get incidencias where tech has kanban tasks linked
            shared_incs = await conn.fetch("""
                SELECT DISTINCT k.id_incidencia, COUNT(k.id) AS num_tareas
                FROM kanban_tareas k
                WHERE k.id_tecnico = $1 AND k.id_incidencia IS NOT NULL
                  AND k.id_incidencia != ''
                GROUP BY k.id_incidencia
            """, id_tecnico)

            salas = []

            # BUILD salas (by project)
            for r in shared_prjs:
                pid = r['id_proyecto']
                sala = await conn.fetchrow(
                    "SELECT id, nombre FROM tech_chat_salas "
                    "WHERE id_referencia = $1 AND activa = true LIMIT 1", pid)
                if not sala:
                    continue
                sid = sala['id']
                num_msgs = await conn.fetchval(
                    "SELECT COUNT(*) FROM tech_chat_mensajes WHERE id_sala = $1", sid) or 0
                last = await conn.fetchrow(
                    "SELECT mensaje, created_at FROM tech_chat_mensajes "
                    "WHERE id_sala = $1 ORDER BY created_at DESC LIMIT 1", sid)
                salas.append({
                    "id_sala": sid,
                    "tipo": "build",
                    "id_referencia": pid,
                    "titulo_referencia": r['nombre_proyecto'],
                    "num_mensajes": num_msgs,
                    "ultimo_mensaje_at": last['created_at'].isoformat() if last and last['created_at'] else None,
                    "ultimo_mensaje_preview": (last['mensaje'][:60] if last and last['mensaje'] else None),
                    "compartido_porque": f"El técnico tiene {r['num_tareas']} tareas en este proyecto",
                })

            # RUN salas (by incidencia)
            for r in shared_incs:
                inc_id = r['id_incidencia']
                sala = await conn.fetchrow(
                    "SELECT id, nombre FROM tech_chat_salas "
                    "WHERE id_referencia = $1 AND activa = true AND tipo = 'run' LIMIT 1", inc_id)
                if not sala:
                    continue
                sid = sala['id']
                num_msgs = await conn.fetchval(
                    "SELECT COUNT(*) FROM tech_chat_mensajes WHERE id_sala = $1", sid) or 0
                last = await conn.fetchrow(
                    "SELECT mensaje, created_at FROM tech_chat_mensajes "
                    "WHERE id_sala = $1 ORDER BY created_at DESC LIMIT 1", sid)
                salas.append({
                    "id_sala": sid,
                    "tipo": "run",
                    "id_referencia": inc_id,
                    "titulo_referencia": sala['nombre'] or inc_id,
                    "num_mensajes": num_msgs,
                    "ultimo_mensaje_at": last['created_at'].isoformat() if last and last['created_at'] else None,
                    "ultimo_mensaje_preview": (last['mensaje'][:60] if last and last['mensaje'] else None),
                    "compartido_porque": f"El técnico tiene {r['num_tareas']} tareas vinculadas",
                })

            # Sort by last activity
            salas.sort(key=lambda s: s.get('ultimo_mensaje_at') or '', reverse=True)

            return {"id_tecnico": id_tecnico, "salas": salas}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Salas compartidas error: {e}")
        raise HTTPException(500, str(e))


# ── PM Dashboard — Pulido v2: Detalle técnico + Detalle proyecto ───────────

@app.get("/api/pm/team/tecnico/{id_tecnico}/detalle")
async def pm_tecnico_detalle(id_tecnico: str, pm_id: str = "PM-016"):
    """Pulido v2: Detalle completo de un técnico del pool del PM."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            pm_id_int = await _resolve_pm_id(conn, pm_id)
            staff = await conn.fetchrow(
                "SELECT * FROM compartido.pmo_staff_skills WHERE id_recurso = $1", id_tecnico)
            if not staff:
                raise HTTPException(404, f"Técnico {id_tecnico} no encontrado")
            sd = dict(staff)
            seed_val = int(hashlib.md5(id_tecnico.encode()).hexdigest()[:8], 16) % 100

            # Projects of this PM where this tech participates
            pm_prjs = await conn.fetch(
                "SELECT DISTINCT k.id_proyecto, cb.nombre_proyecto "
                "FROM kanban_tareas k "
                "JOIN cartera_build cb ON k.id_proyecto = cb.id_proyecto "
                "WHERE k.id_tecnico = $1 AND cb.id_pm_usuario = $2", id_tecnico, pm_id_int)
            prj_list = [{"id_proyecto": r['id_proyecto'], "nombre": r['nombre_proyecto'],
                         "pct_dedicacion": min(40, round(100 / max(len(pm_prjs), 1)))} for r in pm_prjs]

            # Hours this month
            today = date.today()
            month_start = today.replace(day=1)
            horas_mes = await conn.fetchval(
                "SELECT COALESCE(SUM(horas), 0) FROM primitiva.horas_imputadas "
                "WHERE id_tecnico = $1 AND fecha >= $2", id_tecnico, month_start)
            horas_mes = round(float(horas_mes), 1)
            carga_pct = round(horas_mes / 160 * 100)

            # Sparkline 12 weeks
            sparkline = []
            for w in range(12, 0, -1):
                w_start = today - timedelta(weeks=w)
                w_end = w_start + timedelta(days=7)
                h = await conn.fetchval(
                    "SELECT COALESCE(SUM(horas), 0) FROM primitiva.horas_imputadas "
                    "WHERE id_tecnico = $1 AND fecha >= $2 AND fecha < $3",
                    id_tecnico, w_start, w_end)
                sparkline.append({"semana": f"S{w_start.isocalendar()[1]}", "horas": round(float(h), 1)})

            # Active kanban tasks
            tareas = await conn.fetch(
                "SELECT id, titulo, columna, id_proyecto, horas_estimadas, created_at "
                "FROM kanban_tareas WHERE id_tecnico = $1 "
                "AND columna NOT IN ('Completado','Done','Backlog') ORDER BY created_at DESC", id_tecnico)
            tareas_list = [{"id": r['id'], "titulo": r['titulo'][:50], "columna": r['columna'],
                            "id_proyecto": r['id_proyecto'] or '', "horas_est": float(r['horas_estimadas'] or 0)}
                           for r in tareas]

            # Skills from skills_json
            skills_raw = sd.get('skills_json', [])
            skills = skills_raw if isinstance(skills_raw, list) else []

            # SINTETICO: manager, ausencias, disponibilidad
            managers = ["María García", "Carlos López", "Ana Fernández", "Pedro Ruiz"]
            manager = managers[seed_val % len(managers)]

            disponibilidad = []
            for w in range(4):
                w_date = today + timedelta(weeks=w)
                libre = max(0, 100 - carga_pct + (seed_val + w * 7) % 20 - 10)
                disponibilidad.append({"semana": f"S{w_date.isocalendar()[1]}", "pct_libre": min(100, libre)})

            ausencias = []
            if seed_val % 3 == 0:
                aus_start = today + timedelta(days=14 + seed_val % 20)
                ausencias.append({"tipo": "Vacaciones", "desde": str(aus_start),
                                   "hasta": str(aus_start + timedelta(days=5 + seed_val % 5)),
                                   "estado": "Aprobada"})

            return {
                "id_tecnico": id_tecnico,
                "nombre": sd.get('nombre', ''),
                "nivel": sd.get('nivel', ''),
                "silo": sd.get('silo_especialidad', ''),
                "skill_principal": sd.get('skill_principal', ''),
                "email": sd.get('email', ''),
                "telefono": sd.get('telefono', ''),
                "manager": manager,
                "fecha_alta": str(sd.get('fecha_alta', '')) if sd.get('fecha_alta') else None,
                "kpis": {
                    "carga_pct": carga_pct,
                    "horas_mes": horas_mes,
                    "num_proyectos": len(pm_prjs),
                    "coste_hora": round(45 + seed_val * 0.3, 2),
                },
                "skills": skills,
                "sparkline": sparkline,
                "tareas_activas": tareas_list,
                "disponibilidad": disponibilidad,
                "ausencias": ausencias,
                "proyectos": prj_list,
            }
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"PM tecnico detalle error: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/pm/project/{id_proyecto}/detalle")
async def pm_project_detalle(id_proyecto: str):
    """Pulido v2: Detalle enriquecido de un proyecto para modal."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            prj = await conn.fetchrow(
                "SELECT * FROM cartera_build WHERE id_proyecto = $1", id_proyecto)
            if not prj:
                raise HTTPException(404, f"Proyecto {id_proyecto} no encontrado")
            pd = dict(prj)
            seed_val = int(hashlib.md5(id_proyecto.encode()).hexdigest()[:8], 16) % 100

            # Presupuesto
            pres = await conn.fetchrow(
                "SELECT * FROM presupuestos WHERE id_proyecto = $1 ORDER BY version DESC LIMIT 1", id_proyecto)
            bac = float(pres['bac_total']) if pres and pres['bac_total'] else float(pd.get('horas_estimadas', 100)) * 110

            # Dates
            today = date.today()
            fi = pd.get('fecha_inicio') or (pres['fecha_inicio'] if pres and pres.get('fecha_inicio') else None)
            ff = pd.get('fecha_fin_plan') or (pres['fecha_fin'] if pres and pres.get('fecha_fin') else None)
            if hasattr(fi, 'date'): fi = fi.date()
            if hasattr(ff, 'date'): ff = ff.date()
            if not fi: fi = today - timedelta(days=180)
            if not ff: ff = fi + timedelta(days=180)
            total_days = max((ff - fi).days, 1)
            elapsed = max(min((today - fi).days, total_days), 0)
            pct_time = elapsed / total_days

            pct_avance = int(pd.get('pct_avance') or 0) / 100
            ac = float(pd.get('ac') or 0)

            # EVM
            pv = round(bac * pct_time, 2)
            ev = round(bac * pct_avance, 2)
            if ac <= 0:
                ac = round(ev * (0.85 + seed_val / 100 * 0.3), 2) if ev > 0 else round(pv * 0.3, 2)
            cpi = round(ev / ac, 3) if ac > 0 else 1.0
            spi = round(ev / pv, 3) if pv > 0 else 1.0

            # Estimated end date from SPI
            if spi > 0 and spi != 1.0:
                remaining_work = 1.0 - pct_avance
                days_remaining = round(remaining_work * total_days / spi)
                fecha_fin_est = today + timedelta(days=days_remaining)
            else:
                fecha_fin_est = ff
            dias_restantes = (ff - today).days

            # BAC breakdown (from presupuestos or synthetic)
            if pres:
                capex = float(pres.get('total_capex') or 0)
                opex = float(pres.get('total_opex') or 0)
                labor = float(pres.get('total_labor') or 0)
                proveedores = float(pres.get('total_proveedores') or 0)
                rrhh = float(pres.get('total_rrhh') or 0)
                reservas = float(pres.get('total_reservas') or 0)
            else:
                capex = round(bac * 0.25, 2)
                opex = round(bac * 0.15, 2)
                labor = round(bac * 0.35, 2)
                proveedores = round(bac * 0.15, 2)
                rrhh = round(bac * 0.05, 2)
                reservas = round(bac * 0.05, 2)

            bac_desglose = {
                "capex": capex, "opex": opex, "labor": labor,
                "proveedores": proveedores, "rrhh": rrhh, "reservas": reservas,
                "internos": labor + rrhh, "externos": proveedores + capex,
            }

            # Hitos (7)
            hitos_labels = [
                (0.0, "Kick-off · Charter"), (0.15, "Análisis requisitos"),
                (0.30, "Diseño arquitectura"), (0.50, "Desarrollo core"),
                (0.70, "Testing integración"), (0.85, "UAT · Pre-producción"),
                (1.0, "Go-live · Cierre"),
            ]
            hitos = []
            for pct_h, nombre_h in hitos_labels:
                fecha_h = fi + timedelta(days=int(total_days * pct_h))
                completado = pct_avance >= pct_h
                hitos.append({"nombre": nombre_h, "fecha_objetivo": str(fecha_h),
                              "estado": "COMPLETADO" if completado else ("EN_CURSO" if abs(pct_avance - pct_h) < 0.1 else "PENDIENTE"),
                              "responsable": pd.get('responsable_asignado') or 'PM-016'})

            # Riesgos top 3
            risk_rows = await conn.fetch(
                "SELECT descripcion, probabilidad, impacto, score, plan_mitigacion, responsable "
                "FROM build_risks WHERE id_proyecto = $1 ORDER BY score DESC LIMIT 3", id_proyecto)
            if not risk_rows:
                riesgos = [
                    {"descripcion": "Retraso proveedor externo", "score": 12, "mitigacion": "Seguimiento semanal", "owner": "PM"},
                    {"descripcion": "Rotación personal clave", "score": 10, "mitigacion": "Documentación cruzada", "owner": "RRHH"},
                    {"descripcion": "Cambio regulatorio", "score": 8, "mitigacion": "Vigilancia normativa", "owner": "Legal"},
                ]
            else:
                riesgos = [{"descripcion": r['descripcion'][:60], "score": float(r['score']),
                            "mitigacion": (r['plan_mitigacion'] or '')[:60], "owner": r['responsable'] or 'PM'} for r in risk_rows]

            # SINTETICO: Identificación
            sponsors = ["Director General IT", "CIO", "VP Operaciones", "Director Digital"]
            resp_negocio = ["Jefe Área Banca Comercial", "Resp. Operaciones", "Dir. Riesgos", "Resp. Compliance"]

            # SINTETICO: Histórico cambios scope
            cambios_scope = []
            for i in range(2 + seed_val % 2):
                fecha_c = fi + timedelta(days=30 + i * 45 + seed_val % 20)
                motivos = ["Ampliación funcional por regulación DORA", "Reducción scope módulo reporting",
                           "Inclusión migración datos legacy", "Ajuste timeline por dependencia externa"]
                impactos = ["+15% BAC, +3 semanas", "-8% BAC, sin impacto fecha",
                            "+20% BAC, +4 semanas", "Sin impacto BAC, +2 semanas"]
                cambios_scope.append({"fecha": str(fecha_c), "motivo": motivos[i % len(motivos)],
                                       "impacto": impactos[i % len(impactos)],
                                       "aprobado_por": "Comité de cambios"})

            # SINTETICO: Documentación
            docs = [
                {"nombre": "Project Charter", "tipo": "Charter", "fecha": str(fi), "estado": "Aprobado"},
                {"nombre": "Plan de Proyecto", "tipo": "Plan", "fecha": str(fi + timedelta(days=15)), "estado": "Vigente"},
                {"nombre": "Registro de Riesgos", "tipo": "Riesgos", "fecha": str(fi + timedelta(days=20)), "estado": "Actualizado"},
                {"nombre": "Plan de Calidad", "tipo": "QA", "fecha": str(fi + timedelta(days=25)), "estado": "Vigente"},
                {"nombre": "Acta de Cierre", "tipo": "Cierre", "fecha": str(ff), "estado": "Pendiente" if pct_avance < 1.0 else "Firmado"},
            ]

            # F1: resolver PM dinámicamente desde cartera_build.id_pm_usuario (INTEGER)
            pm_display = "Sin PM asignado"
            if pd.get('id_pm_usuario'):
                pm_row = await conn.fetchrow(
                    "SELECT u.nombre_completo, pm.id_pm "
                    "FROM compartido.rbac_usuarios u "
                    "LEFT JOIN compartido.pmo_project_managers pm ON pm.id_usuario_rbac = u.id_usuario "
                    "WHERE u.id_usuario = $1", pd['id_pm_usuario'])
                if pm_row:
                    pm_display = pm_row['nombre_completo']
                    if pm_row['id_pm']:
                        pm_display = f"{pm_display} ({pm_row['id_pm']})"

            return {
                "proyecto": {
                    "id": pd['id_proyecto'], "nombre": pd['nombre_proyecto'],
                    "estado": pd.get('estado', ''), "prioridad": pd.get('prioridad_estrategica', ''),
                    "silo": pd.get('perfil_requerido') or pd.get('skills_requeridas', '')[:30] or 'IT General',
                    "tipo": "BUILD",
                },
                "identificacion": {
                    "sponsor": sponsors[seed_val % len(sponsors)],
                    "responsable_negocio": resp_negocio[seed_val % len(resp_negocio)],
                    "pm": pm_display,
                },
                "fechas": {
                    "inicio": str(fi), "fin_plan": str(ff),
                    "fin_estimado_spi": str(fecha_fin_est),
                    "dias_restantes": dias_restantes,
                    "pct_tiempo": round(pct_time * 100, 1),
                    "pct_avance": round(pct_avance * 100, 1),
                    "desviacion": "OK" if abs(pct_time - pct_avance) < 0.1 else ("ALERTA" if pct_time > pct_avance else "ADELANTADO"),
                },
                "evm": {
                    "bac": bac, "pv": pv, "ev": ev, "ac": ac,
                    "cpi": cpi, "spi": spi,
                    "eac": round(bac / cpi, 2) if cpi > 0 else bac * 2,
                    "vac": round(bac - (bac / cpi if cpi > 0 else bac * 2), 2),
                },
                "bac_desglose": bac_desglose,
                "hitos": hitos,
                "riesgos": riesgos,
                "cambios_scope": cambios_scope,
                "documentacion": docs,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"PM project detalle error: {e}")
        raise HTTPException(500, str(e))


# ── PM Dashboard — Fase D (Equipo del PM) ──────────────────────────────────

@app.get("/api/pm/dashboard/team")
async def pm_dashboard_team(pm_id: str = "PM-016"):
    """Equipo agregado del PM: técnicos únicos en todos sus proyectos."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            pm_id_int = await _resolve_pm_id(conn, pm_id)

            # Projects of this PM
            pm_projects = await conn.fetch(
                "SELECT id_proyecto, nombre_proyecto FROM cartera_build WHERE id_pm_usuario = $1",
                pm_id_int)
            if not pm_projects:
                return []
            prj_ids = [r['id_proyecto'] for r in pm_projects]
            prj_names = {r['id_proyecto']: r['nombre_proyecto'] for r in pm_projects}

            # Distinct technicians across all PM projects
            tech_rows = await conn.fetch("""
                SELECT k.id_tecnico,
                       array_agg(DISTINCT k.id_proyecto) AS proyectos
                FROM kanban_tareas k
                WHERE k.id_proyecto = ANY($1) AND k.id_tecnico IS NOT NULL
                GROUP BY k.id_tecnico
                ORDER BY COUNT(DISTINCT k.id_proyecto) DESC, k.id_tecnico
            """, prj_ids)

            today = date.today()
            month_start = today.replace(day=1)
            result = []

            for row in tech_rows:
                tid = row['id_tecnico']
                tech_prjs = row['proyectos']
                n_proy = len(tech_prjs)

                # Staff info
                staff = await conn.fetchrow(
                    "SELECT nombre, skill_principal, silo_especialidad, nivel "
                    "FROM compartido.pmo_staff_skills WHERE id_recurso = $1", tid)
                nombre = staff['nombre'] if staff else tid
                skill = staff['skill_principal'] if staff else ''
                silo = staff['silo_especialidad'] if staff else ''
                nivel = staff['nivel'] if staff else ''

                # Hours this month
                horas_mes = await conn.fetchval(
                    "SELECT COALESCE(SUM(horas), 0) FROM primitiva.horas_imputadas "
                    "WHERE id_tecnico = $1 AND fecha >= $2", tid, month_start)
                horas_mes = round(float(horas_mes), 1)

                # Estimated dedication per project (~40% each, realistic for PM projects)
                pct_per_proj = min(40, round(100 / max(n_proy, 1), 0))
                total_pct = pct_per_proj * n_proy
                capacidad_h = 160  # Fixed FTE capacity

                # Load state based on actual hours vs capacity
                load_pct = round(horas_mes / capacidad_h * 100, 0)
                if load_pct > 100:
                    estado_carga = 'SOBRECARGA'
                elif load_pct > 85:
                    estado_carga = 'AJUSTADO'
                else:
                    estado_carga = 'OK'

                # Conflict: >2 projects (combined dedication exceeds realistic capacity)
                conflicto = n_proy > 2

                # Project details
                proyectos_detail = []
                for pid in tech_prjs:
                    proyectos_detail.append({
                        "id_proyecto": pid,
                        "nombre": prj_names.get(pid, pid),
                        "pct_dedicacion_estimado": pct_per_proj,
                    })

                result.append({
                    "id_tecnico": tid,
                    "nombre": nombre,
                    "skill": skill,
                    "silo": silo,
                    "nivel": nivel,
                    "num_proyectos": n_proy,
                    "proyectos": proyectos_detail,
                    "horas_imputadas_mes": horas_mes,
                    "horas_estimadas_mes": capacidad_h,
                    "carga_pct": load_pct,
                    "estado_carga": estado_carga,
                    "conflicto": conflicto,
                })

            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"PM dashboard team error: {e}")
        raise HTTPException(500, str(e))


# ── PM Dashboard — Fase B/C (Shell + Mis Proyectos) ────────────────────────
# Schema: primitiva (sin scope multi-escenario)

@app.get("/api/pm/dashboard/projects")
async def pm_dashboard_projects(pm_id: str = "PM-016"):
    """Lista proyectos del PM con EVM precalculado para el dashboard."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            pm_id_int = await _resolve_pm_id(conn, pm_id)
            rows = await conn.fetch(
                "SELECT cb.*, p.bac_total, p.fecha_inicio AS p_fecha_inicio, p.fecha_fin AS p_fecha_fin "
                "FROM cartera_build cb "
                "LEFT JOIN presupuestos p ON cb.id_proyecto = p.id_proyecto "
                "WHERE cb.id_pm_usuario = $1 ORDER BY cb.id_proyecto", pm_id_int)
            today = date.today()
            result = []
            for r in rows:
                d = dict(r)
                bac = float(d.get('bac_total') or d.get('horas_estimadas', 100) * 110)
                pct_avance = int(d.get('pct_avance') or 0)
                ac_val = float(d.get('ac') or 0)
                fi = d.get('fecha_inicio') or d.get('p_fecha_inicio') or d.get('fecha_creacion')
                ff = d.get('fecha_fin_plan') or d.get('p_fecha_fin')
                if hasattr(fi, 'date'):
                    fi = fi.date()
                if hasattr(ff, 'date'):
                    ff = ff.date()
                if not fi:
                    fi = today - timedelta(days=180)
                if not ff:
                    ff = fi + timedelta(days=180)
                total_d = max((ff - fi).days, 1)
                elapsed = max(min((today - fi).days, total_d), 0)
                pct_time = round(elapsed / total_d * 100, 1)
                ev = bac * pct_avance / 100
                pv = bac * elapsed / total_d
                cpi = round(ev / ac_val, 2) if ac_val > 0 else (1.0 if pct_avance == 0 else 0)
                spi = round(ev / pv, 2) if pv > 0 else (1.0 if pct_avance == 0 else 0)

                # Team (quick count)
                team_rows = await conn.fetch(
                    "SELECT DISTINCT k.id_tecnico, s.nombre "
                    "FROM kanban_tareas k LEFT JOIN compartido.pmo_staff_skills s ON k.id_tecnico=s.id_recurso "
                    "WHERE k.id_proyecto=$1 AND k.id_tecnico IS NOT NULL LIMIT 8", d['id_proyecto'])

                # Next milestone
                proximo_hito = None
                hitos_syn = [
                    (0.25, "Kick-off"), (0.50, "Diseño"), (0.75, "Dev+Test"), (1.0, "Go-live")
                ]
                for pct_h, nombre_h in hitos_syn:
                    fecha_h = fi + timedelta(days=int(total_d * pct_h))
                    if fecha_h >= today:
                        proximo_hito = {"nombre": nombre_h, "fecha": str(fecha_h), "dias_para": (fecha_h - today).days}
                        break
                if not proximo_hito and hitos_syn:
                    fecha_h = ff
                    proximo_hito = {"nombre": "Go-live", "fecha": str(fecha_h), "dias_para": (fecha_h - today).days}

                result.append({
                    "id_proyecto": d['id_proyecto'],
                    "nombre_proyecto": d['nombre_proyecto'],
                    "estado": d.get('estado', ''),
                    "prioridad": d.get('prioridad_estrategica', 'Media'),
                    "bac": bac,
                    "pct_avance": pct_avance,
                    "pct_tiempo": pct_time,
                    "cpi": cpi,
                    "spi": spi,
                    "team": [{"nombre": t['nombre'] or t['id_tecnico']} for t in team_rows],
                    "proximo_hito": proximo_hito,
                })
            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"PM dashboard projects error: {e}")
        raise HTTPException(500, str(e))


# ── PM Dashboard — Fase F (Chat War Room) ──────────────────────────────────

@app.get("/api/pm/chat/rooms")
async def pm_chat_rooms(pm_id: str = "PM-016"):
    """Fase F: Lista de salas de chat del PM (una por proyecto)."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            pm_id_int = await _resolve_pm_id(conn, pm_id)
            projects = await conn.fetch(
                "SELECT id_proyecto, nombre_proyecto, estado FROM cartera_build "
                "WHERE id_pm_usuario = $1 ORDER BY id_proyecto", pm_id_int)
            rooms = []
            for prj in projects:
                pid = prj['id_proyecto']
                sala = await conn.fetchrow(
                    "SELECT id, nombre FROM tech_chat_salas "
                    "WHERE id_referencia = $1 AND activa = true LIMIT 1", pid)
                if not sala:
                    sala = await conn.fetchrow(
                        "INSERT INTO tech_chat_salas (tipo, id_referencia, nombre, activa) "
                        "VALUES ('build', $1, $2, true) RETURNING id, nombre",
                        pid, f"{pid} — {prj['nombre_proyecto'][:50]}")
                sid = sala['id']
                total_msgs = await conn.fetchval(
                    "SELECT COUNT(*) FROM tech_chat_mensajes WHERE id_sala = $1", sid) or 0
                last_msg = await conn.fetchrow(
                    "SELECT m.mensaje, m.id_autor, m.created_at, "
                    "COALESCE(pm.nombre, s.nombre, m.id_autor) AS autor_nombre "
                    "FROM tech_chat_mensajes m "
                    "LEFT JOIN compartido.pmo_project_managers pm ON m.id_autor = pm.id_pm "
                    "LEFT JOIN compartido.pmo_staff_skills s ON m.id_autor = s.id_recurso "
                    "WHERE m.id_sala = $1 ORDER BY m.created_at DESC LIMIT 1", sid)
                participants = await conn.fetchval(
                    "SELECT COUNT(DISTINCT id_autor) FROM tech_chat_mensajes WHERE id_sala = $1", sid) or 0
                rooms.append({
                    "id_sala": sid,
                    "id_proyecto": pid,
                    "nombre_proyecto": prj['nombre_proyecto'],
                    "estado_proyecto": prj['estado'],
                    "num_mensajes": total_msgs,
                    "num_participantes": participants,
                    "num_no_leidos": max(0, (hash(pid) % 5) - 2),  # synthetic 0-2
                    "ultimo_mensaje": {
                        "texto": last_msg['mensaje'][:80] if last_msg else None,
                        "autor": last_msg['autor_nombre'] if last_msg else None,
                        "timestamp": last_msg['created_at'].isoformat() if last_msg and last_msg['created_at'] else None,
                    } if last_msg else None,
                })
            rooms.sort(key=lambda r: r['ultimo_mensaje']['timestamp'] if r.get('ultimo_mensaje') and r['ultimo_mensaje'].get('timestamp') else '', reverse=True)
            return rooms
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"PM chat rooms error: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/pm/chat/room/{id_sala}/messages")
async def pm_chat_room_messages(id_sala: int, limit: int = 100):
    """Fase F: Hilo de mensajes de una sala."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            msgs = await conn.fetch(
                "SELECT m.id, m.id_autor, m.rol_autor, m.mensaje, m.created_at, "
                "COALESCE(pm.nombre, s.nombre, m.id_autor) AS autor_nombre "
                "FROM tech_chat_mensajes m "
                "LEFT JOIN compartido.pmo_project_managers pm ON m.id_autor = pm.id_pm "
                "LEFT JOIN compartido.pmo_staff_skills s ON m.id_autor = s.id_recurso "
                "WHERE m.id_sala = $1 ORDER BY m.created_at ASC LIMIT $2", id_sala, limit)
            return [{"id": r['id'], "autor_id": r['id_autor'], "autor_nombre": r['autor_nombre'],
                     "autor_rol": r['rol_autor'], "texto": r['mensaje'],
                     "timestamp": r['created_at'].isoformat() if r['created_at'] else None} for r in msgs]
    except Exception as e:
        logger.warning(f"PM chat room messages error: {e}")
        raise HTTPException(500, str(e))


class PMChatRoomMessage(BaseModel):
    autor_id: str = "PM-016"
    texto: str


@app.post("/api/pm/chat/room/{id_sala}/send")
async def pm_chat_room_send(id_sala: int, body: PMChatRoomMessage):
    """Fase F: Enviar mensaje a una sala."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")
            msg = await conn.fetchrow(
                "INSERT INTO tech_chat_mensajes (id_sala, id_autor, rol_autor, mensaje) "
                "VALUES ($1, $2, 'pm', $3) RETURNING id, created_at",
                id_sala, body.autor_id, body.texto)
            nombre = await conn.fetchval(
                "SELECT nombre FROM compartido.pmo_project_managers WHERE id_pm = $1", body.autor_id)
            return {"id": msg['id'], "timestamp": msg['created_at'].isoformat() if msg['created_at'] else None,
                    "autor_nombre": nombre or body.autor_id}
    except Exception as e:
        logger.warning(f"PM chat room send error: {e}")
        raise HTTPException(500, str(e))


# ── PM Dashboard — Fase E (Seguimiento PMBOK Full) ─────────────────────────

@app.get("/api/pm/project/{id_proyecto}/pmbok-full")
async def pm_project_pmbok_full(id_proyecto: str):
    """Fase E: PMBOK cockpit completo — 8 secciones en una llamada."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")

            # ── Proyecto base ──
            prj = await conn.fetchrow(
                "SELECT * FROM cartera_build WHERE id_proyecto = $1", id_proyecto)
            if not prj:
                raise HTTPException(404, f"Proyecto {id_proyecto} no encontrado")
            prj_d = dict(prj)

            # ── Presupuesto ──
            pres = await conn.fetchrow(
                "SELECT bac_total, fecha_inicio, fecha_fin FROM presupuestos "
                "WHERE id_proyecto = $1 ORDER BY version DESC LIMIT 1", id_proyecto)

            bac = float(pres['bac_total']) if pres and pres['bac_total'] else float(prj_d.get('horas_estimadas', 100)) * 110
            fi = prj_d.get('fecha_inicio') or (pres['fecha_inicio'] if pres and pres.get('fecha_inicio') else None)
            ff = prj_d.get('fecha_fin_plan') or (pres['fecha_fin'] if pres and pres.get('fecha_fin') else None)
            if hasattr(fi, 'date'): fi = fi.date()
            if hasattr(ff, 'date'): ff = ff.date()
            today = date.today()
            if not fi: fi = today - timedelta(days=180)
            if not ff: ff = fi + timedelta(days=180)
            total_days = max((ff - fi).days, 1)
            elapsed = max(min((today - fi).days, total_days), 0)
            pct_time = elapsed / total_days

            db_avance = prj_d.get('pct_avance')
            pct_avance = int(db_avance) / 100 if db_avance and int(db_avance) > 0 else 0

            db_ac = prj_d.get('ac')
            seed_val = int(hashlib.md5(id_proyecto.encode()).hexdigest()[:8], 16) % 100

            # ── EVM ──
            pv = round(bac * pct_time, 2)
            ev = round(bac * pct_avance, 2)
            ac = round(float(db_ac), 2) if db_ac and float(db_ac) > 0 else round(ev * (0.85 + seed_val / 100 * 0.3), 2)
            cpi = round(ev / ac, 3) if ac > 0 else 1.0
            spi = round(ev / pv, 3) if pv > 0 else 1.0
            cv = round(ev - ac, 2)
            sv = round(ev - pv, 2)
            eac = round(bac / cpi, 2) if cpi > 0 else bac * 2
            etc_val = round(eac - ac, 2)
            vac = round(bac - eac, 2)
            if cpi >= 1.0:
                interp = f"Proyecto dentro de presupuesto (CPI={cpi}). Ahorro estimado: {abs(vac):,.0f}€"
            elif cpi >= 0.9:
                interp = f"Desviación moderada (CPI={cpi}). Sobrecostará ~{abs(vac):,.0f}€"
            else:
                interp = f"Sobrecostes significativos (CPI={cpi}). EAC: {eac:,.0f}€ vs BAC: {bac:,.0f}€"

            evm = {"pv": pv, "ev": ev, "ac": ac, "cpi": cpi, "spi": spi,
                   "cv": cv, "sv": sv, "eac": eac, "etc": etc_val, "vac": vac,
                   "interpretacion": interp}

            # ── EVM Curve-S (12 semanas) — SINTETICO ──
            evm_curve = []
            for w in range(12, 0, -1):
                w_date = today - timedelta(weeks=w)
                w_elapsed = max(min((w_date - fi).days, total_days), 0)
                w_pct_time = w_elapsed / total_days
                # Avance progresivo (sigmoid-like)
                w_avance = pct_avance * min(1.0, w_pct_time / max(pct_time, 0.01))
                w_pv = round(bac * w_pct_time, 0)
                w_ev = round(bac * w_avance, 0)
                # AC with noise
                noise = 1.0 + (hash(f"{id_proyecto}-{w}") % 20 - 10) / 100
                w_ac = round(w_ev / max(cpi, 0.5) * noise, 0) if w_ev > 0 else round(w_pv * 0.2, 0)
                iso_week = w_date.isocalendar()[1]
                evm_curve.append({"semana": f"S{iso_week}", "pv": w_pv, "ev": w_ev, "ac": w_ac})

            # ── Calidad ──
            total_tasks = await conn.fetchval(
                "SELECT COUNT(*) FROM kanban_tareas WHERE id_proyecto = $1", id_proyecto) or 0
            done_tasks = await conn.fetchval(
                "SELECT COUNT(*) FROM kanban_tareas WHERE id_proyecto = $1 "
                "AND columna IN ('Completado','Done')", id_proyecto) or 0
            defectos_abiertos = max(0, total_tasks - done_tasks)
            defectos_cerrados = done_tasks
            ratio_calidad = round(done_tasks / max(total_tasks, 1) * 100, 1) if total_tasks > 0 else round(pct_avance * 85 + 10, 1)
            tasa_retrabajo = round(max(0, 100 - ratio_calidad) * 0.3, 1)
            # SINTETICO: top defectos
            defect_types = ["Fallo integración API", "Error validación datos", "Timeout en carga masiva",
                            "UI no responsive en móvil", "Pérdida de sesión LDAP", "Error cálculo fiscal",
                            "Deadlock en transacciones", "Memory leak en batch"]
            defectos_top = [{"id": f"DEF-{i+1:03d}", "descripcion": defect_types[(seed_val + i) % len(defect_types)],
                             "severidad": ["Crítica", "Alta", "Media", "Baja"][(seed_val + i) % 4]}
                            for i in range(min(5, defectos_abiertos))]

            calidad = {"defectos_abiertos": defectos_abiertos, "defectos_cerrados": defectos_cerrados,
                       "ratio_calidad": min(ratio_calidad, 100), "total_entregables": max(total_tasks, 1),
                       "tasa_retrabajo": tasa_retrabajo, "defectos_top": defectos_top}

            # ── Riesgos ──
            risk_rows = await conn.fetch(
                "SELECT id, descripcion, probabilidad, impacto, score, plan_mitigacion, responsable "
                "FROM build_risks WHERE id_proyecto = $1 ORDER BY score DESC", id_proyecto)
            if risk_rows:
                riesgos = [{"id": r['id'][:12], "descripcion": r['descripcion'], "probabilidad": r['probabilidad'],
                            "impacto": r['impacto'], "score": float(r['score']),
                            "mitigacion": r['plan_mitigacion'], "owner": r['responsable'] or ''} for r in risk_rows]
            else:
                # SINTETICO
                risk_templates = [
                    ("Retraso proveedor externo", 3, 4, "Penalización contractual + seguimiento semanal"),
                    ("Rotación personal clave", 2, 5, "Documentación cruzada + backup conocimiento"),
                    ("Cambio regulatorio inesperado", 2, 4, "Vigilancia normativa + buffer scope"),
                    ("Integración legacy fallida", 4, 3, "PoC temprana + plan contingencia rollback"),
                    ("Sobrecarga equipo técnico", 3, 3, "Monitorizar carga + refuerzo externo"),
                    ("Requisitos inestables", 4, 4, "Sprint 0 validación + change control"),
                    ("Brecha seguridad en testing", 2, 5, "Pentest previo + checklist OWASP"),
                ]
                riesgos = []
                for i, (desc, p, im, mit) in enumerate(risk_templates[:5 + seed_val % 3]):
                    p_adj = max(1, min(5, p + (seed_val + i) % 3 - 1))
                    im_adj = max(1, min(5, im + (seed_val + i + 2) % 3 - 1))
                    riesgos.append({"id": f"R-{i+1:03d}", "descripcion": desc,
                                    "probabilidad": p_adj, "impacto": im_adj,
                                    "score": p_adj * im_adj, "mitigacion": mit,
                                    "owner": ["Jefe Proyecto", "Arquitecto", "QA Lead", "Sponsor"][(seed_val + i) % 4]})
                riesgos.sort(key=lambda r: -r['score'])

            # ── Cronograma / Hitos ──
            hitos_labels = [
                (0.0, "Kick-off · Charter"), (0.15, "Análisis requisitos"),
                (0.30, "Diseño arquitectura"), (0.50, "Desarrollo core"),
                (0.70, "Testing integración"), (0.85, "UAT + Pre-producción"),
                (1.0, "Go-live · Cierre"),
            ]
            hitos = []
            for pct_h, nombre_h in hitos_labels:
                fecha_h = fi + timedelta(days=int(total_days * pct_h))
                completado = pct_avance >= pct_h
                hitos.append({"nombre": nombre_h, "fecha_objetivo": str(fecha_h),
                              "fecha_real": str(fecha_h) if completado else None,
                              "dias_para": (fecha_h - today).days,
                              "estado": "COMPLETADO" if completado else ("EN_CURSO" if abs(pct_avance - pct_h) < 0.1 else "PENDIENTE"),
                              "responsable": prj_d.get('responsable_asignado') or ''})

            # SINTETICO: camino crítico
            critico_tareas = [
                "Definición arquitectura", "Desarrollo módulo core", "Integración sistemas legacy",
                "Migración datos producción", "Testing E2E", "Despliegue producción",
            ]
            camino_critico = []
            for i, tarea in enumerate(critico_tareas):
                pct_t = (i + 1) / len(critico_tareas)
                fecha_t = fi + timedelta(days=int(total_days * pct_t))
                holgura = 0 if i in (1, 2, 4) else (seed_val % 5 + 1) * (i + 1)
                camino_critico.append({"tarea": tarea, "fecha_fin": str(fecha_t),
                                       "holgura_dias": holgura, "en_critico": holgura == 0})

            cronograma = {"hitos": hitos, "camino_critico": camino_critico}

            # ── Imputaciones ──
            total_horas = await conn.fetchval(
                "SELECT COALESCE(SUM(horas), 0) FROM primitiva.horas_imputadas "
                "WHERE id_proyecto = $1", id_proyecto)
            total_horas = round(float(total_horas), 1)

            top_imp = await conn.fetch(
                "SELECT h.id_tecnico, s.nombre, SUM(h.horas) as total_h "
                "FROM primitiva.horas_imputadas h "
                "LEFT JOIN compartido.pmo_staff_skills s ON h.id_tecnico = s.id_recurso "
                "WHERE h.id_proyecto = $1 GROUP BY h.id_tecnico, s.nombre "
                "ORDER BY total_h DESC LIMIT 5", id_proyecto)

            serie_sem = await conn.fetch(
                "SELECT semana_iso, SUM(horas) as total "
                "FROM primitiva.horas_imputadas WHERE id_proyecto = $1 "
                "GROUP BY semana_iso ORDER BY semana_iso DESC LIMIT 8", id_proyecto)

            horas_estimadas_proy = float(prj_d.get('horas_estimadas', 0) or 0)
            imputaciones = {
                "total_horas_proyecto": total_horas,
                "horas_estimadas": horas_estimadas_proy,
                "top_imputadores": [{"tecnico": r['nombre'] or r['id_tecnico'],
                                      "horas": round(float(r['total_h']), 1)} for r in top_imp],
                "serie_semanal": [{"semana": f"S{r['semana_iso']}",
                                    "horas": round(float(r['total']), 1)} for r in serie_sem],
            }

            # ── Stakeholders — SINTETICO por silo ──
            sth_rows = await conn.fetch(
                "SELECT nombre, cargo, nivel_poder, nivel_interes, estrategia, rol_raci "
                "FROM build_stakeholders WHERE id_proyecto = $1 "
                "ORDER BY nivel_poder DESC", id_proyecto)
            if sth_rows:
                stakeholders = [{"nombre": r['nombre'], "rol": r['cargo'] or '',
                                 "poder": r['nivel_poder'], "interes": r['nivel_interes'],
                                 "estrategia": r['estrategia'] or ''} for r in sth_rows]
            else:
                silo = prj_d.get('perfil_requerido') or prj_d.get('skills_requeridas') or 'IT'
                stakeholders = [
                    {"nombre": "Director General IT", "rol": "Sponsor", "poder": 5, "interes": 3, "estrategia": "Mantener satisfecho"},
                    {"nombre": "CIO", "rol": "Executive Sponsor", "poder": 5, "interes": 4, "estrategia": "Gestionar de cerca"},
                    {"nombre": "Resp. Área Negocio", "rol": "Product Owner", "poder": 3, "interes": 5, "estrategia": "Gestionar de cerca"},
                    {"nombre": "Jefe Operaciones", "rol": "Beneficiario", "poder": 4, "interes": 4, "estrategia": "Gestionar de cerca"},
                    {"nombre": "Compliance Officer", "rol": "Auditor", "poder": 4, "interes": 2, "estrategia": "Mantener satisfecho"},
                    {"nombre": "Arquitecto Jefe", "rol": "Technical Lead", "poder": 2, "interes": 5, "estrategia": "Mantener informado"},
                    {"nombre": "QA Manager", "rol": "Quality Gate", "poder": 2, "interes": 4, "estrategia": "Mantener informado"},
                    {"nombre": "Usuarios finales", "rol": "End Users", "poder": 1, "interes": 3, "estrategia": "Monitorizar"},
                ]

            # ── Nivel riesgo agregado ──
            avg_risk = round(sum(r['score'] for r in riesgos) / max(len(riesgos), 1), 1) if riesgos else 0

            return {
                "proyecto": {
                    "id": prj_d['id_proyecto'], "nombre": prj_d['nombre_proyecto'],
                    "estado": prj_d.get('estado', ''), "prioridad": prj_d.get('prioridad_estrategica', ''),
                    "bac": bac, "pct_avance": round(pct_avance * 100, 1), "pct_tiempo": round(pct_time * 100, 1),
                    "fecha_inicio": str(fi), "fecha_fin": str(ff),
                },
                "evm": evm,
                "evm_curve": evm_curve,
                "calidad": calidad,
                "riesgos": riesgos,
                "cronograma": cronograma,
                "imputaciones": imputaciones,
                "stakeholders": stakeholders,
                "riesgo_nivel": avg_risk,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"PM pmbok-full error: {e}")
        raise HTTPException(500, str(e))


# ── PM Dashboard — Fase E/F legacy (Seguimiento PMBOK + Chat) ──────────────

@app.get("/api/pm/project/{id_proyecto}/pmbok")
async def pm_project_pmbok(id_proyecto: str):
    """A1: Seguimiento PMBOK completo de un proyecto."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")

            # ── Proyecto base ──
            prj = await conn.fetchrow(
                "SELECT * FROM cartera_build WHERE id_proyecto = $1", id_proyecto)
            if not prj:
                raise HTTPException(404, f"Proyecto {id_proyecto} no encontrado")
            prj_d = dict(prj)

            # ── Presupuesto (BAC) ──
            pres = await conn.fetchrow(
                "SELECT bac_total, total_labor, total_proveedores, total_opex, "
                "total_capex, fecha_inicio, fecha_fin FROM presupuestos "
                "WHERE id_proyecto = $1 ORDER BY version DESC LIMIT 1", id_proyecto)

            bac = float(pres['bac_total']) if pres and pres['bac_total'] else float(prj_d.get('horas_estimadas', 100)) * 110
            # Dates: prefer cartera_build fields, then presupuestos, then defaults
            fecha_inicio = prj_d.get('fecha_inicio') or (pres['fecha_inicio'] if pres and pres.get('fecha_inicio') else None)
            if not fecha_inicio:
                fc = prj_d.get('fecha_creacion')
                fecha_inicio = fc.date() if hasattr(fc, 'date') else (fc or datetime.now().date())
            fecha_fin = prj_d.get('fecha_fin_plan') or (pres['fecha_fin'] if pres and pres.get('fecha_fin') else None)
            if not fecha_fin:
                fecha_fin = fecha_inicio + timedelta(days=180) if isinstance(fecha_inicio, date) else date.today() + timedelta(days=180)

            # ── Governance scoring ──
            gov = await conn.fetchrow(
                "SELECT * FROM pmo_governance_scoring WHERE id_proyecto = $1", id_proyecto)

            # ── EVM — SINTETICO si no hay datos reales ──
            today = date.today()
            if isinstance(fecha_inicio, datetime):
                fecha_inicio = fecha_inicio.date()
            if isinstance(fecha_fin, datetime):
                fecha_fin = fecha_fin.date()
            total_days = max((fecha_fin - fecha_inicio).days, 1)
            elapsed_days = max(min((today - fecha_inicio).days, total_days), 0)
            pct_time = elapsed_days / total_days

            # Task counts (needed for calidad + avance)
            total_tasks = await conn.fetchval(
                "SELECT COUNT(*) FROM kanban_tareas WHERE id_proyecto = $1", id_proyecto) or 0
            done_tasks = await conn.fetchval(
                "SELECT COUNT(*) FROM kanban_tareas WHERE id_proyecto = $1 "
                "AND columna IN ('Completado','Done')", id_proyecto) or 0

            # Real pct_avance from cartera_build, fallback to kanban
            db_avance = prj_d.get('pct_avance')
            if db_avance and int(db_avance) > 0:
                pct_avance = int(db_avance) / 100
            else:
                pct_avance = done_tasks / max(total_tasks, 1)

            # EVM calculations — use real AC if available, else synthetic
            pv = round(bac * pct_time, 2)
            ev = round(bac * pct_avance, 2)
            seed_val = int(hashlib.md5(id_proyecto.encode()).hexdigest()[:8], 16) % 100
            db_ac = prj_d.get('ac')
            if db_ac and float(db_ac) > 0:
                ac = round(float(db_ac), 2)
            else:
                cost_factor = 0.85 + (seed_val / 100) * 0.3
                ac = round(ev * cost_factor, 2) if ev > 0 else round(pv * 0.3, 2)

            cpi = round(ev / ac, 3) if ac > 0 else 1.0
            spi = round(ev / pv, 3) if pv > 0 else 1.0
            cv = round(ev - ac, 2)
            sv = round(ev - pv, 2)
            eac = round(bac / cpi, 2) if cpi > 0 else bac * 2
            etc_val = round(eac - ac, 2)
            vac = round(bac - eac, 2)

            if cpi >= 1.0:
                interp = f"Proyecto dentro de presupuesto (CPI={cpi}). Ahorro estimado: {abs(vac):,.0f}€"
            elif cpi >= 0.9:
                interp = f"Proyecto con desviación moderada (CPI={cpi}). Sobrecostará ~{abs(vac):,.0f}€"
            else:
                interp = f"Proyecto con sobrecostes significativos (CPI={cpi}). EAC: {eac:,.0f}€ vs BAC: {bac:,.0f}€"

            evm = {
                "pv": pv, "ev": ev, "ac": ac,
                "cpi": cpi, "spi": spi, "cv": cv, "sv": sv,
                "eac": eac, "etc": etc_val, "vac": vac,
                "interpretacion": interp,
            }

            # ── Calidad (build_quality_gates) ──
            qg_total = await conn.fetchval(
                "SELECT COUNT(*) FROM build_quality_gates WHERE id_proyecto = $1", id_proyecto) or 0
            qg_passed = await conn.fetchval(
                "SELECT COUNT(*) FROM build_quality_gates WHERE id_proyecto = $1 "
                "AND estado IN ('APROBADO','aprobado','PASSED','passed')", id_proyecto) or 0
            # SINTETICO: defectos y retrabajo
            defectos = max(0, total_tasks - done_tasks)
            ratio_calidad = round(qg_passed / max(qg_total, 1) * 100, 1) if qg_total > 0 else round(pct_avance * 85 + 10, 1)
            tasa_retrabajo = round(max(0, 100 - ratio_calidad) * 0.3, 1)

            calidad = {
                "defectos_abiertos": defectos,
                "total_entregables": max(qg_total, total_tasks),
                "ratio_calidad": min(ratio_calidad, 100),
                "tasa_retrabajo": tasa_retrabajo,
            }

            # ── Riesgos (build_risks) ──
            risk_rows = await conn.fetch(
                "SELECT id, descripcion, probabilidad, impacto, score, "
                "plan_mitigacion, estado FROM build_risks WHERE id_proyecto = $1 "
                "ORDER BY score DESC", id_proyecto)
            if risk_rows:
                riesgos = [dict(r) for r in risk_rows]
            else:
                # SINTETICO: riesgos placeholder
                riesgos = [
                    {"id": "R-SYN-001", "descripcion": "Retraso en entrega de proveedor externo",
                     "probabilidad": 3, "impacto": 4, "score": 12,
                     "plan_mitigacion": "Seguimiento semanal con proveedor, penalización contractual",
                     "estado": "ABIERTO"},
                    {"id": "R-SYN-002", "descripcion": "Rotación de personal clave del equipo",
                     "probabilidad": 2, "impacto": 5, "score": 10,
                     "plan_mitigacion": "Documentación cruzada, backup de conocimiento",
                     "estado": "ABIERTO"},
                ]

            # ── Hitos (build_sprints como proxy) ──
            sprint_rows = await conn.fetch(
                "SELECT id, nombre, fecha_inicio, fecha_fin, estado, "
                "story_points_planificados, story_points_completados "
                "FROM build_sprints WHERE id_proyecto = $1 ORDER BY sprint_number", id_proyecto)
            if sprint_rows:
                hitos = []
                for s in sprint_rows:
                    dias_para = (s['fecha_fin'] - today).days if s['fecha_fin'] else None
                    hitos.append({
                        "nombre": s['nombre'] or s['id'],
                        "fecha_objetivo": str(s['fecha_fin']) if s['fecha_fin'] else None,
                        "fecha_real": str(s['fecha_fin']) if s['estado'] in ('DONE','COMPLETADO','completado') else None,
                        "dias_para": dias_para,
                        "estado": s['estado'],
                        "responsable": prj_d.get('responsable_asignado', ''),
                    })
            else:
                # SINTETICO: hitos basados en timeline
                hitos = []
                for i, (pct_h, nombre_h) in enumerate([
                    (0.25, "Kick-off + Análisis"), (0.50, "Diseño completado"),
                    (0.75, "Desarrollo + Testing"), (1.0, "Go-live")
                ]):
                    fecha_h = fecha_inicio + timedelta(days=int(total_days * pct_h))
                    hitos.append({
                        "nombre": nombre_h, "fecha_objetivo": str(fecha_h),
                        "fecha_real": str(fecha_h) if pct_time >= pct_h else None,
                        "dias_para": (fecha_h - today).days,
                        "estado": "COMPLETADO" if pct_time >= pct_h else "PENDIENTE",
                        "responsable": prj_d.get('responsable_asignado', ''),
                    })

            # ── Imputaciones (horas_imputadas si existe, fallback kanban) ──
            has_imput = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                "WHERE table_name='horas_imputadas' AND table_schema='primitiva')")
            if has_imput:
                # Real data from horas_imputadas
                week_data = await conn.fetch(
                    "SELECT h.id_tecnico, s.nombre, SUM(h.horas) as total_h "
                    "FROM primitiva.horas_imputadas h "
                    "LEFT JOIN compartido.pmo_staff_skills s ON h.id_tecnico = s.id_recurso "
                    "WHERE h.id_proyecto = $1 AND h.fecha >= CURRENT_DATE - INTERVAL '7 days' "
                    "GROUP BY h.id_tecnico, s.nombre ORDER BY total_h DESC", id_proyecto)
                semana_actual = [{"tecnico_id": r['id_tecnico'], "nombre": r['nombre'] or r['id_tecnico'],
                                  "horas": round(float(r['total_h']), 1)} for r in week_data]

                weeks_summary = await conn.fetch(
                    "SELECT semana_iso, SUM(horas) as total "
                    "FROM primitiva.horas_imputadas WHERE id_proyecto = $1 "
                    "GROUP BY semana_iso ORDER BY semana_iso DESC LIMIT 4", id_proyecto)
                ultimas_4 = [{"semana": f"S{r['semana_iso']}", "total_horas": round(float(r['total']), 1)}
                             for r in weeks_summary]

                top3_rows = await conn.fetch(
                    "SELECT h.id_tecnico, s.nombre, SUM(h.horas) as total_h "
                    "FROM primitiva.horas_imputadas h "
                    "LEFT JOIN compartido.pmo_staff_skills s ON h.id_tecnico = s.id_recurso "
                    "WHERE h.id_proyecto = $1 "
                    "GROUP BY h.id_tecnico, s.nombre ORDER BY total_h DESC LIMIT 3", id_proyecto)
                top3 = [{"nombre": r['nombre'] or r['id_tecnico'],
                         "horas_acumuladas": round(float(r['total_h']), 1)} for r in top3_rows]
            else:
                # Fallback: kanban horas
                week_tasks = await conn.fetch(
                    "SELECT k.id_tecnico, s.nombre, k.horas_reales "
                    "FROM kanban_tareas k LEFT JOIN compartido.pmo_staff_skills s "
                    "ON k.id_tecnico = s.id_recurso "
                    "WHERE k.id_proyecto = $1 AND k.horas_reales > 0 "
                    "ORDER BY k.horas_reales DESC", id_proyecto)
                semana_actual = [{"tecnico_id": r['id_tecnico'], "nombre": r['nombre'] or r['id_tecnico'],
                                  "horas": float(r['horas_reales'])} for r in week_tasks[:10]]
                top3 = [{"nombre": r['nombre'] or r['id_tecnico'],
                         "horas_acumuladas": float(r['horas_reales'])} for r in week_tasks[:3]]
                total_horas = sum(float(r['horas_reales'] or 0) for r in week_tasks)
                ultimas_4 = [{"semana": f"S{i}", "total_horas": round(total_horas / 4 * (0.8 + i * 0.1), 1)}
                             for i in range(1, 5)]

            imputaciones = {
                "semana_actual": semana_actual,
                "ultimas_4_semanas": ultimas_4,
                "top3_tecnicos": top3,
            }

            # ── Stakeholders ──
            sth_rows = await conn.fetch(
                "SELECT nombre, cargo, estrategia, rol_raci, frecuencia_comunicacion "
                "FROM build_stakeholders WHERE id_proyecto = $1 ORDER BY nivel_poder DESC", id_proyecto)
            if sth_rows:
                stakeholders = [{"nombre": r['nombre'], "rol": r['cargo'] or r['rol_raci'],
                                 "ultima_comunicacion": str(today - timedelta(days=seed_val % 14)),
                                 "proxima_reunion": str(today + timedelta(days=7 if r['frecuencia_comunicacion'] == 'Semanal' else 14))}
                                for r in sth_rows]
            else:
                # SINTETICO
                stakeholders = [
                    {"nombre": "Director Área", "rol": "Sponsor",
                     "ultima_comunicacion": str(today - timedelta(days=3)),
                     "proxima_reunion": str(today + timedelta(days=7))},
                    {"nombre": "Responsable Negocio", "rol": "Product Owner",
                     "ultima_comunicacion": str(today - timedelta(days=1)),
                     "proxima_reunion": str(today + timedelta(days=3))},
                ]

            return {
                "proyecto": {
                    "id": prj_d['id_proyecto'], "nombre": prj_d['nombre_proyecto'],
                    "estado": prj_d.get('estado', ''), "prioridad": prj_d.get('prioridad_estrategica', ''),
                    "bac": bac, "fecha_inicio": str(fecha_inicio), "fecha_fin_plan": str(fecha_fin),
                    "pct_avance": round(pct_avance * 100, 1), "pct_tiempo": round(pct_time * 100, 1),
                },
                "evm": evm,
                "calidad": calidad,
                "riesgos": riesgos,
                "hitos": hitos,
                "imputaciones": imputaciones,
                "stakeholders": stakeholders,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"PM pmbok error: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/pm/project/{id_proyecto}/team")
async def pm_project_team(id_proyecto: str):
    """A2: Equipo asignado a un proyecto específico."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")

            # Verificar que el proyecto existe
            prj = await conn.fetchval(
                "SELECT id_proyecto FROM cartera_build WHERE id_proyecto = $1", id_proyecto)
            if not prj:
                raise HTTPException(404, f"Proyecto {id_proyecto} no encontrado")

            # Técnicos en kanban_tareas de este proyecto
            rows = await conn.fetch("""
                SELECT DISTINCT k.id_tecnico,
                       s.nombre, s.silo_especialidad AS silo, s.nivel,
                       COUNT(*) FILTER (WHERE k.columna NOT IN ('Completado','Done','Backlog')) AS tareas_activas,
                       COALESCE(SUM(k.horas_reales), 0) AS horas_imputadas
                FROM kanban_tareas k
                LEFT JOIN compartido.pmo_staff_skills s ON k.id_tecnico = s.id_recurso
                WHERE k.id_proyecto = $1 AND k.id_tecnico IS NOT NULL
                GROUP BY k.id_tecnico, s.nombre, s.silo_especialidad, s.nivel
                ORDER BY tareas_activas DESC, horas_imputadas DESC
            """, id_proyecto)

            result = []
            for r in rows:
                # Ocupación total: contar tareas activas en TODOS sus proyectos
                total_active = await conn.fetchval(
                    "SELECT COUNT(*) FROM kanban_tareas "
                    "WHERE id_tecnico = $1 AND columna NOT IN ('Completado','Done','Backlog')",
                    r['id_tecnico']) or 0
                ocu_pct = min(total_active * 20, 100)  # ~20% por tarea activa
                result.append({
                    "tecnico_id": r['id_tecnico'],
                    "nombre": r['nombre'] or r['id_tecnico'],
                    "silo": r['silo'] or '',
                    "nivel": r['nivel'] or '',
                    "tareas_activas_proyecto": int(r['tareas_activas']),
                    "horas_imputadas_mes": round(float(r['horas_imputadas']), 1),
                    "ocupacion_total_pct": ocu_pct,
                })
            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"PM project team error: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/pm/chat/{id_proyecto}/messages")
async def pm_chat_messages(id_proyecto: str):
    """A3: Histórico del chat war-room del proyecto."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")

            # Buscar sala existente
            sala = await conn.fetchrow(
                "SELECT id, nombre FROM tech_chat_salas "
                "WHERE id_referencia = $1 AND activa = true LIMIT 1", id_proyecto)

            if not sala:
                # Auto-crear sala on first access
                sala_nombre = f"{id_proyecto} - War Room PM"
                sala = await conn.fetchrow(
                    "INSERT INTO tech_chat_salas (tipo, id_referencia, nombre, activa) "
                    "VALUES ('build', $1, $2, true) RETURNING id, nombre",
                    id_proyecto, sala_nombre)

            sala_id = sala['id']

            # Obtener mensajes
            msgs = await conn.fetch(
                "SELECT m.id, m.id_autor, m.rol_autor, m.mensaje, m.created_at, "
                "COALESCE(pm.nombre, s.nombre, m.id_autor) AS autor_nombre "
                "FROM tech_chat_mensajes m "
                "LEFT JOIN compartido.pmo_project_managers pm ON m.id_autor = pm.id_pm "
                "LEFT JOIN compartido.pmo_staff_skills s ON m.id_autor = s.id_recurso "
                "WHERE m.id_sala = $1 ORDER BY m.created_at ASC LIMIT 100", sala_id)

            return [
                {
                    "id": r['id'], "autor_nombre": r['autor_nombre'],
                    "autor_rol": r['rol_autor'], "texto": r['mensaje'],
                    "created_at": r['created_at'].isoformat() if r['created_at'] else None,
                }
                for r in msgs
            ]
    except Exception as e:
        logger.warning(f"PM chat messages error: {e}")
        raise HTTPException(500, str(e))


class PMChatMessage(BaseModel):
    texto: str


@app.post("/api/pm/chat/{id_proyecto}/send")
async def pm_chat_send(id_proyecto: str, body: PMChatMessage):
    """A4: Enviar mensaje al chat war-room del proyecto."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB pool no disponible")
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET search_path = primitiva, compartido, public")

            # Buscar sala (o crearla)
            sala = await conn.fetchrow(
                "SELECT id FROM tech_chat_salas "
                "WHERE id_referencia = $1 AND activa = true LIMIT 1", id_proyecto)
            if not sala:
                sala = await conn.fetchrow(
                    "INSERT INTO tech_chat_salas (tipo, id_referencia, nombre, activa) "
                    "VALUES ('build', $1, $2, true) RETURNING id",
                    id_proyecto, f"{id_proyecto} - War Room PM")
            sala_id = sala['id']

            # Insertar mensaje (autor = PM-016 por defecto, rol = pm)
            autor_id = "PM-016"  # TODO: extraer de auth/session
            msg = await conn.fetchrow(
                "INSERT INTO tech_chat_mensajes (id_sala, id_autor, rol_autor, mensaje) "
                "VALUES ($1, $2, 'pm', $3) RETURNING id, created_at",
                sala_id, autor_id, body.texto)

            # Nombre del autor
            pm_nombre = await conn.fetchval(
                "SELECT nombre FROM compartido.pmo_project_managers WHERE id_pm = $1", autor_id)

            return {
                "id": msg['id'], "autor_nombre": pm_nombre or autor_id,
                "autor_rol": "pm", "texto": body.texto,
                "created_at": msg['created_at'].isoformat() if msg['created_at'] else None,
            }
    except Exception as e:
        logger.warning(f"PM chat send error: {e}")
        raise HTTPException(500, str(e))


# ── ARQ-04: LLM Provider Config API ───────────────────────────────────────

# Seguridad F5b: hash de contraseña de autor (NUNCA texto plano)
_LLM_AUTHOR_HASH = "9b8d684facf0905d6ed2dd439f9bc23d9c9e758124ba1413218763a0ea8f8371"
_LLM_PROTECTED = {"anthropic", "openai"}
_llm_unlock_tokens: Dict[str, dict] = {}
_SENSITIVE_KEYS = {"api_key", "oauth_token", "access_token", "refresh_token", "secret"}


@app.post("/api/llm/auth/unlock")
async def llm_auth_unlock(request: Request):
    """Valida contraseña de autor server-side. Devuelve token temporal."""
    body = await request.json()
    password = body.get("password", "")
    provider = body.get("provider", "")
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    if pwd_hash != _LLM_AUTHOR_HASH:
        return JSONResponse(status_code=403, content={"error": "Contraseña incorrecta"})
    token = secrets.token_hex(32)
    _llm_unlock_tokens[provider] = {"token": token, "expires": _time.time() + 3600}
    return {"ok": True, "token": token, "provider": provider, "expires_in": 3600}


@app.get("/api/llm/providers")
async def list_llm_providers():
    """Lista providers LLM configurados (keys ocultas)."""
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, provider_name, display_name, auth_type,
                   is_active, is_default, config_json,
                   created_at, updated_at
            FROM primitiva.llm_provider_config
            ORDER BY is_default DESC, provider_name
        """)
        result = []
        for r in rows:
            d = dict(r)
            # Ocultar campos sensibles del config_json
            if d.get("config_json"):
                cfg = json.loads(d["config_json"]) if isinstance(d["config_json"], str) else dict(d["config_json"])
                for key in _SENSITIVE_KEYS:
                    if key in cfg:
                        val = str(cfg[key])
                        cfg[key] = "••••••" + val[-4:] if len(val) > 4 else "••••••"
                d["config_json"] = cfg
            result.append(d)
        return result


@app.post("/api/llm/providers")
async def upsert_llm_provider(data: dict):
    """Crear o actualizar un provider LLM."""
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    name = data.get("provider_name", "").strip().lower()
    if not name:
        raise HTTPException(status_code=400, detail="provider_name requerido")
    display = data.get("display_name", name.title())
    auth_type = data.get("auth_type", "api_key")
    is_active = data.get("is_active", True)
    config_json = json.dumps(data.get("config_json", {}))
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO primitiva.llm_provider_config
                (provider_name, display_name, auth_type, is_active, config_json, updated_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, NOW())
            ON CONFLICT (provider_name) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                auth_type = EXCLUDED.auth_type,
                is_active = EXCLUDED.is_active,
                config_json = EXCLUDED.config_json,
                updated_at = NOW()
            RETURNING id, provider_name, display_name, auth_type, is_active, is_default
        """, name, display, auth_type, is_active, config_json)
        return dict(row)


@app.put("/api/llm/providers/{provider_id}/activate")
async def activate_llm_provider(provider_id: int, request: Request):
    """Marcar un provider como default. Providers protegidos requieren token."""
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, provider_name FROM primitiva.llm_provider_config WHERE id = $1", provider_id)
        if not row:
            raise HTTPException(status_code=404, detail="Provider no encontrado")
        provider_name = row["provider_name"]
        # Verificar token para providers protegidos
        if provider_name in _LLM_PROTECTED:
            auth_token = request.headers.get("X-LLM-Unlock-Token", "")
            unlock = _llm_unlock_tokens.get(provider_name, {})
            if not unlock or unlock["token"] != auth_token or _time.time() > unlock.get("expires", 0):
                return JSONResponse(status_code=403, content={
                    "error": "Restricción de autor: Jose Antonio Martínez Victoria — Este proveedor requiere autorización"
                })
        await conn.execute("""
            UPDATE primitiva.llm_provider_config SET is_default = FALSE, updated_at = NOW()
        """)
        await conn.execute("""
            UPDATE primitiva.llm_provider_config
            SET is_default = TRUE, is_active = TRUE, updated_at = NOW()
            WHERE id = $1
        """, provider_id)
        result = await conn.fetchrow(
            "SELECT id, provider_name, display_name, is_default FROM primitiva.llm_provider_config WHERE id = $1",
            provider_id)
        return dict(result)


# ── Monitorización: audit page-view ───────────────────────────────────────

@app.post("/api/audit/page-view")
async def audit_page_view(request: Request):
    """Recibe pings de navegación del frontend para el resumen diario."""
    try:
        body = await request.json()
        seccion = body.get("seccion", "desconocido")
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() \
             or (request.client.host if request.client else "")
        pool = get_pool()
        if pool:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO primitiva.audit_log
                    (evento, ip_address, seccion, endpoint, metodo)
                    VALUES ('page_view', $1, $2, '/api/audit/page-view', 'POST')
                """, ip, seccion)
    except Exception:
        pass
    return {"ok": True}


@app.post("/api/audit/login")
async def audit_login_event(request: Request):
    """Registra login en audit_log (llamado desde auth.py indirectamente)."""
    try:
        body = await request.json()
        pool = get_pool()
        if pool:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO primitiva.audit_log
                    (evento, usuario_id, usuario_nombre, ip_address, user_agent, seccion)
                    VALUES ('login', $1, $2, $3, $4, 'login')
                """, body.get("usuario_id"), body.get("usuario_nombre"),
                     body.get("ip"), body.get("user_agent"))
    except Exception:
        pass
    return {"ok": True}


# ── War Room Cognitivo (Sub-App) ───────────────────────────────────────────
from war_room_api import war_room_app
app.mount("/cognitive", war_room_app)

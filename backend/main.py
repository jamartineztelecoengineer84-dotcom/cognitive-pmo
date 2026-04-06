import os
import json
import uuid
import logging
from datetime import datetime, date
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
from models import (
    ProyectoCreate,
    IncidenciaCreate,
    AsignarTecnico,
    BufferUpdate,
    KanbanTareaCreate,
)
from rbac_api import router as rbac_router
from cmdb_api import router as cmdb_router
from db_loader import router as db_loader_router
from tech_routes import router as tech_router
from tech_terminal_ws import router as tech_terminal_router
from tech_copiloto import router as tech_copiloto_router
from auth import get_current_user, UserInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── DB Config ──────────────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "192.168.1.49")
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
    sql_files = ["init.sql", "rbac_schema.sql", "cmdb_schema.sql", "cmdb_seed_extra.sql", "cmdb_ips_seed.sql", "cmdb_costes_schema.sql", "agents_migrations.sql"]
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
    yield
    await close_pool()


app = FastAPI(title="Cognitive PMO API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── RBAC Router ───────────────────────────────────────────────────────────
app.include_router(rbac_router)
app.include_router(cmdb_router)
app.include_router(db_loader_router)
app.include_router(tech_router)
app.include_router(tech_terminal_router)
app.include_router(tech_copiloto_router)


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
                rows = await conn.fetch("SELECT * FROM pmo_staff_skills ORDER BY nombre")
                return [serialize(r) for r in rows]
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
                return [serialize(r) for r in rows]
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
    inc_id = "INC-" + datetime.now().strftime("%Y") + "-" + str(uuid.uuid4())[:4].upper()
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
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
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
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
            return [dict(r) for r in rows]
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
async def get_pms():
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM pmo_project_managers ORDER BY nombre")
                return [serialize(r) for r in rows]
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
            asignados = await conn.fetchval("SELECT COUNT(*) FROM pmo_project_managers WHERE estado='ASIGNADO'")
            sobrecargados = await conn.fetchval("SELECT COUNT(*) FROM pmo_project_managers WHERE estado='SOBRECARGADO'")
            total_gov = await conn.fetchval("SELECT COUNT(*) FROM pmo_governance_scoring")
            avg_score = await conn.fetchval("SELECT AVG(total_score) FROM pmo_governance_scoring")
            avg_compliance = await conn.fetchval("SELECT AVG(compliance_pct) FROM pmo_governance_scoring")
            by_gate = await conn.fetch("SELECT gate_status, COUNT(*) as cnt FROM pmo_governance_scoring GROUP BY gate_status")
            by_gate_phase = await conn.fetch("SELECT current_gate, COUNT(*) as cnt FROM pmo_governance_scoring GROUP BY current_gate ORDER BY current_gate")
            total_changes = await conn.fetchval("SELECT SUM(change_requests) FROM pmo_governance_scoring")
            approved_changes = await conn.fetchval("SELECT SUM(change_approved) FROM pmo_governance_scoring")
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
                rows = await conn.fetch("SELECT * FROM run_incident_plans ORDER BY created_at DESC")
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
    plan_id = p.id or ("RUN-" + datetime.now().strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:4].upper())
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO run_incident_plans (id,ticket_id,nombre,prioridad,area,sla_horas,plan_data)
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
            result = await conn.execute("DELETE FROM run_incident_plans WHERE id=$1", plan_id)
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
            WHERE estado IN ('DISPONIBLE', 'ASIGNADO')
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
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    system_prompt = "Eres AG-018 Governance Advisor de Cognitive PMO.\n" \
        "Tu rol es asistir al gobernador durante las pausas de gobernanza del pipeline BUILD.\n\n" \
        "CONTEXTO ACTUAL DEL PROYECTO:\n" + json.dumps(context, indent=2, ensure_ascii=False) + "\n\n" \
        "REGLAS:\n- Responde en español profesional pero cercano\n" \
        "- Usa datos reales del contexto (no inventes)\n" \
        "- Sé conciso pero completo (máx 200 palabras)\n" \
        "- Si no sabes algo, dilo claramente"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1000,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": message}]
                })
            result = resp.json()
            reply = result.get("content", [{}])[0].get("text", "Error al procesar")
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
                rows = await conn.fetch("SELECT * FROM presupuestos ORDER BY created_at DESC")
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
        "stack": {"backend":"FastAPI + asyncpg","frontend":"Vanilla JS SPA","db":"PostgreSQL","agents":"Flowise + Claude Sonnet 4","infra":"Docker Compose on NasJose 192.168.1.49"},
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


# ── War Room Cognitivo (Sub-App) ───────────────────────────────────────────
from war_room_api import war_room_app
app.mount("/cognitive", war_room_app)

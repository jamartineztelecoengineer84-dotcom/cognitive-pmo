import os
import json
import uuid
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

import psycopg2
import httpx
import psycopg2.extras
from fastapi import FastAPI, HTTPException
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

# ── War Room Cognitivo (Sub-App) ───────────────────────────────────────────
from war_room_api import war_room_app
app.mount("/cognitive", war_room_app)

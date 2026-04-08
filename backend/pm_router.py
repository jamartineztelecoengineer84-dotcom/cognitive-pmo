"""
P98 FASE 3 — Router /api/pm/* (Vista PMO · scope MIS_PROYECTOS).

4 endpoints GET filtrados por id_pm_usuario = current_user.id_usuario:
  /my-projects   — proyectos del PM con CPI/SPI calculados
  /my-timeline   — hitos sintéticos G0-G5 distribuidos en cada proyecto
  /my-resources  — humanos (vía kanban_tareas.id_tecnico) + agentes (TODO)
  /my-kpis       — agregados financieros + flags RBAC económico

NOTA: las fórmulas CPI/SPI son las mismas que v_p96_build_portfolio
(definidas en SQL con CASE) para mantener un único origen de verdad.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import logging

from auth import get_current_user, UserInfo
from database import get_pool

logger = logging.getLogger(__name__)

pm_router = APIRouter(prefix="/api/pm", tags=["pm"])

# TODO(F6): allowlist PMO_* a verificar aquí también para defensa en profundidad.
# Por ahora el filtro es por id_pm_usuario = current_user.id_usuario, lo cual
# es suficiente — otros roles devolverán lista vacía, no 403.


# ─────────────────────────────────────────────────────────────────────
# SQL — comparte la misma fórmula CPI/SPI que v_p96_build_portfolio
# ─────────────────────────────────────────────────────────────────────
_PROJECTS_SQL = """
SELECT
  bl.id_proyecto, bl.nombre, bl.silo, bl.estado, bl.prioridad, bl.gate_actual,
  bl.presupuesto_bac, bl.presupuesto_consumido, bl.risk_score, bl.progreso_pct,
  bl.sprint_actual, bl.total_sprints, bl.story_points_total,
  bl.story_points_completados, bl.velocity_media, bl.ai_lead,
  bl.fecha_inicio, bl.fecha_fin_prevista,
  CASE
    WHEN bl.presupuesto_consumido > 0
    THEN ROUND(bl.presupuesto_bac * bl.progreso_pct::numeric / 100.0
               / bl.presupuesto_consumido, 2)
    ELSE 1.00
  END AS cpi,
  CASE
    WHEN bl.presupuesto_bac > 0
     AND bl.fecha_inicio IS NOT NULL
     AND bl.fecha_fin_prevista IS NOT NULL
     AND bl.fecha_fin_prevista > bl.fecha_inicio
    THEN ROUND(
      bl.progreso_pct::numeric / 100.0
      / NULLIF(EXTRACT(epoch FROM now() - bl.fecha_inicio::timestamptz)
               / NULLIF(EXTRACT(epoch FROM bl.fecha_fin_prevista - bl.fecha_inicio), 0), 0),
      2)
    ELSE 1.00
  END AS spi
FROM build_live bl
WHERE bl.id_pm_usuario = $1
ORDER BY bl.presupuesto_bac DESC NULLS LAST, bl.id_proyecto
"""


def _row_to_project(r):
    return {
        "id_proyecto": r["id_proyecto"],
        "nombre": r["nombre"],
        "silo": r["silo"],
        "estado": r["estado"],
        "prioridad": r["prioridad"],
        "gate_actual": r["gate_actual"],
        "presupuesto_bac": float(r["presupuesto_bac"] or 0),
        "presupuesto_consumido": float(r["presupuesto_consumido"] or 0),
        "risk_score": float(r["risk_score"] or 0),
        "progreso_pct": r["progreso_pct"] or 0,
        "sprint_actual": r["sprint_actual"],
        "total_sprints": r["total_sprints"],
        "story_points_total": r["story_points_total"],
        "story_points_completados": r["story_points_completados"],
        "velocity_media": float(r["velocity_media"] or 0),
        "ai_lead": bool(r["ai_lead"]),
        "fecha_inicio": r["fecha_inicio"].isoformat() if r["fecha_inicio"] else None,
        "fecha_fin_prevista": r["fecha_fin_prevista"].isoformat() if r["fecha_fin_prevista"] else None,
        "cpi": float(r["cpi"]) if r["cpi"] is not None else 1.0,
        "spi": float(r["spi"]) if r["spi"] is not None else 1.0,
    }


# ─────────────────────────────────────────────────────────────────────
# GET /api/pm/my-projects
# ─────────────────────────────────────────────────────────────────────
@pm_router.get("/my-projects")
async def my_projects(user: UserInfo = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        rows = await conn.fetch(_PROJECTS_SQL, user.id_usuario)
    return [_row_to_project(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────
# GET /api/pm/my-timeline — hitos sintéticos G0-G5 por proyecto
# ─────────────────────────────────────────────────────────────────────
_GATES = ["G0", "G1", "G2", "G3", "G4", "G5"]
_GATE_LABELS = {
    "G0": "Inicio · Charter",
    "G1": "Diseño · Arquitectura",
    "G2": "Build · Construcción",
    "G3": "Test · QA",
    "G4": "Deploy · Producción",
    "G5": "Cierre · Lecciones",
}


def _build_timeline(proj):
    """Genera hitos sintéticos G0-G5 distribuidos uniformemente en el rango temporal."""
    fi_iso = proj["fecha_inicio"]
    ff_iso = proj["fecha_fin_prevista"]
    if not fi_iso or not ff_iso:
        return []
    fi = datetime.fromisoformat(fi_iso)
    ff = datetime.fromisoformat(ff_iso)
    total = (ff - fi).days
    if total <= 0:
        return []
    gate_actual = proj.get("gate_actual") or "G0"
    hitos = []
    for i, g in enumerate(_GATES):
        # 6 hitos repartidos: G0 = inicio, G5 = fin, resto interpolados
        offset = round(total * i / (len(_GATES) - 1))
        fecha = fi + timedelta(days=offset)
        if g == gate_actual:
            tipo = "actual"
        elif _GATES.index(g) < _GATES.index(gate_actual) if gate_actual in _GATES else False:
            tipo = "completado"
        else:
            tipo = "pendiente"
        hitos.append({
            "fecha": fecha.date().isoformat(),
            "label": _GATE_LABELS[g],
            "tipo": tipo,
        })
    return hitos


@pm_router.get("/my-timeline")
async def my_timeline(user: UserInfo = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        rows = await conn.fetch(_PROJECTS_SQL, user.id_usuario)
    out = []
    for r in rows:
        p = _row_to_project(r)
        out.append({
            "id_proyecto": p["id_proyecto"],
            "nombre": p["nombre"],
            "fecha_inicio": p["fecha_inicio"],
            "fecha_fin_prevista": p["fecha_fin_prevista"],
            "gate_actual": p["gate_actual"],
            "hitos": _build_timeline(p),
        })
    return out


# ─────────────────────────────────────────────────────────────────────
# GET /api/pm/my-resources
# ─────────────────────────────────────────────────────────────────────
_RESOURCES_SQL = """
SELECT
  u.id_usuario, u.nombre_completo, u.email, r.code AS role_code,
  ARRAY_AGG(DISTINCT bl.id_proyecto) AS proyectos,
  COUNT(DISTINCT k.id) AS tareas_count,
  COALESCE(SUM(k.horas_estimadas), 0) AS horas_estimadas,
  COALESCE(SUM(k.horas_reales), 0) AS horas_reales
FROM build_live bl
JOIN kanban_tareas k ON k.id_proyecto = bl.id_proyecto
JOIN rbac_usuarios u ON u.id_recurso = k.id_tecnico
JOIN rbac_roles r ON r.id_role = u.id_role
WHERE bl.id_pm_usuario = $1
GROUP BY u.id_usuario, u.nombre_completo, u.email, r.code
ORDER BY tareas_count DESC
"""


@pm_router.get("/my-resources")
async def my_resources(user: UserInfo = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        rows = await conn.fetch(_RESOURCES_SQL, user.id_usuario)
    humans = [{
        "id": r["id_usuario"],
        "nombre": r["nombre_completo"],
        "email": r["email"],
        "rol": r["role_code"],
        "proyectos": list(r["proyectos"] or []),
        "tareas": r["tareas_count"],
        "horas_estimadas": float(r["horas_estimadas"] or 0),
        "horas_reales": float(r["horas_reales"] or 0),
    } for r in rows]
    # TODO(P98 F3.1): cuando agent_conversations tenga FK id_proyecto poblada,
    # agregar agentes IA por proyecto. Por ahora devolvemos lista vacía.
    return {"humans": humans, "agents": []}


# ─────────────────────────────────────────────────────────────────────
# GET /api/pm/my-kpis
# ─────────────────────────────────────────────────────────────────────
@pm_router.get("/my-kpis")
async def my_kpis(user: UserInfo = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        rows = await conn.fetch(_PROJECTS_SQL, user.id_usuario)

    projs = [_row_to_project(r) for r in rows]
    n = len(projs)
    total_bac = sum(p["presupuesto_bac"] for p in projs)
    total_cons = sum(p["presupuesto_consumido"] for p in projs)

    # CPI/SPI medio ponderado por BAC
    if total_bac > 0:
        cpi_pond = sum(p["cpi"] * p["presupuesto_bac"] for p in projs) / total_bac
        spi_pond = sum(p["spi"] * p["presupuesto_bac"] for p in projs) / total_bac
    else:
        cpi_pond = 1.0
        spi_pond = 1.0

    return {
        "total_projects": n,
        "total_bac": round(total_bac, 2),
        "total_consumido": round(total_cons, 2),
        "cpi_medio_ponderado": round(cpi_pond, 3),
        "spi_medio_ponderado": round(spi_pond, 3),
        "proyectos_en_riesgo": sum(1 for p in projs if (p["risk_score"] or 0) > 0.6),
        "proyectos_retraso": sum(1 for p in projs if p["spi"] < 0.95),
        "capex_ratio": 0.0,   # TODO(P98 F3.1): build_live no tiene flag CAPEX/OPEX
        "opex_ratio": 0.0,    # TODO(P98 F3.1)
        "ver_salario_ind": False,    # PMO_* nunca ven salarios individuales (RGPD)
        "silos": sorted({p["silo"] for p in projs if p["silo"]}),
    }

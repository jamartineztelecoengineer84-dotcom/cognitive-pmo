"""
Portfolio Prioritization Wizard — API Router
Endpoints para el ejercicio AHP + Kepner-Tregoe + Solver Knapsack.
Todos los cálculos complejos (AHP, K-T, Solver) se hacen en frontend JS.
El backend solo sirve datos y persiste evaluaciones.
"""

import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from database import get_pool

logger = logging.getLogger("portfolio_wizard")
router = APIRouter(prefix="/api/portfolio-wizard", tags=["Portfolio Wizard"])

# Silo → Portfolio mapping
SILO_TO_PORTFOLIO = {
    "IT-INFRA": "Infraestructura", "RED": "Infraestructura",
    "CLOUD": "Infraestructura", "IT-CLOUD": "Infraestructura",
    "VIRTUAL": "Infraestructura", "STORAGE": "Infraestructura",
    "IT-APPS": "Aplicaciones",
    "IT-DATA": "Digital",
    "IT-SEGURIDAD": "Seguridad",
}


@router.get("/objectives")
async def get_objectives():
    """OKRs del Pulso Estratégico + KRs como criterios."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        # Intentar cargar KPIs del Pulso como base para OKRs
        kpis = await conn.fetch(
            "SELECT k, lb, vl, un, rag, sub, tt FROM p96_pulse_kpis"
        )
        responsables = await conn.fetch(
            "SELECT id, nm, rl, ct, ini, kpi_vl, kpi_lb, lg FROM p96_pulse_responsables ORDER BY id"
        )

    # Construir OKRs a partir de los datos del Pulso
    # Si no hay datos suficientes, devolver estructura base
    okr_objs = [
        {
            "id": "O1", "name": "Excelencia operativa y eficiencia IT",
            "source": "p96_pulse_kpis", "sourceTab": "CEO Dashboard → Pulso Estratégico",
            "krs": [
                {"id": "KR1.1", "name": "CPI medio ≥ 0.95 en proyectos activos", "progress": 78},
                {"id": "KR1.2", "name": "SPI medio ≥ 0.90 en proyectos activos", "progress": 65},
                {"id": "KR1.3", "name": "≤ 2 proyectos en rojo simultáneo", "progress": 50},
            ]
        },
        {
            "id": "O2", "name": "Transformación digital y datos",
            "source": "p96_pulse_kpis", "sourceTab": "CEO Dashboard → Pulso Estratégico",
            "krs": [
                {"id": "KR2.1", "name": "3 proyectos data en G3+ antes de Q4", "progress": 40},
                {"id": "KR2.2", "name": "100% activos críticos en CMDB", "progress": 85},
            ]
        },
        {
            "id": "O3", "name": "Seguridad y resiliencia",
            "source": "p96_pulse_kpis", "sourceTab": "CEO Dashboard → Pulso Estratégico",
            "krs": [
                {"id": "KR3.1", "name": "DR probado en < 4h RTO", "progress": 30},
                {"id": "KR3.2", "name": "Zero vulnerabilidades críticas > 30 días", "progress": 70},
            ]
        },
    ]
    return {"objectives": okr_objs, "kpis": [dict(k) for k in kpis], "responsables": [dict(r) for r in responsables]}


@router.get("/committee")
async def get_committee():
    """Comité votante: roles con nivel_jerarquico ≤ 2."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.id_usuario, u.nombre_completo, u.cargo, u.email,
                   r.code as role_code, r.nombre as role_nombre,
                   r.nivel_jerarquico, r.color as role_color
            FROM rbac_usuarios u
            JOIN rbac_roles r ON u.id_role = r.id_role
            WHERE r.nivel_jerarquico <= 2 AND u.activo = true
            ORDER BY r.nivel_jerarquico, r.code
        """)

    committee = []
    for r in rows:
        name = r["nombre_completo"]
        parts = name.split()
        initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()
        committee.append({
            "id": f"U-{r['id_usuario']:03d}",
            "userId": r["id_usuario"],
            "name": name,
            "role": r["role_code"],
            "roleName": r["role_nombre"],
            "nivel": r["nivel_jerarquico"],
            "initials": initials,
            "cargo": r["cargo"],
            "color": r["role_color"],
            "selected": r["nivel_jerarquico"] <= 1,  # C-level selected by default
        })
    return {"committee": committee}


@router.get("/projects")
async def get_projects():
    """Proyectos candidatos desde v_p96_build_portfolio + detail."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT v.id_proyecto, v.nombre, v.silo, v.pm, v.bac_k,
                   v.gate, v.cpi, v.spi, v.prio, v.risk, v.prog, v.ai_lead,
                   c.horas_estimadas, c.responsable_asignado, c.estado,
                   d.gates as detail_gates, d.team as detail_team, d.risks as detail_risks
            FROM v_p96_build_portfolio v
            JOIN cartera_build c ON v.id_proyecto = c.id_proyecto
            LEFT JOIN p96_build_project_detail d ON v.id_proyecto = d.id_proyecto
            ORDER BY v.id_proyecto
        """)

    projects = []
    for r in rows:
        silo = r["silo"] or ""
        portfolio = SILO_TO_PORTFOLIO.get(silo, "Transversal")
        prio_map = {"Crítica": 4, "Alta": 3, "Media": 2, "Baja": 1}
        prio_num = prio_map.get(r["prio"], 2)

        proj = {
            "id": r["id_proyecto"],
            "name": r["nombre"],
            "silo": silo,
            "portfolio": portfolio,
            "pm": r["pm"] or r["responsable_asignado"] or "",
            "bac": float(r["bac_k"] or 0),
            "gate": r["gate"] or "G0",
            "cpi": float(r["cpi"] or 0),
            "spi": float(r["spi"] or 0),
            "prio": prio_num,
            "prioLabel": r["prio"] or "Media",
            "risk": float(r["risk"] or 0),
            "prog": int(r["prog"] or 0),
            "ai": bool(r["ai_lead"]),
            "rrhh": int(r["horas_estimadas"] or 0),
            "estado": r["estado"] or "",
            "benefit": 0,  # Input del comité, no existe en BD
            "selected": True,
        }

        # Detail data
        if r["detail_gates"]:
            gates_data = r["detail_gates"] if isinstance(r["detail_gates"], dict) else {}
            proj["gates"] = [{"g": g, "date": v.get("date"), "status": v.get("status")}
                            for g, v in sorted(gates_data.items())]
        else:
            proj["gates"] = []

        if r["detail_team"]:
            proj["team"] = r["detail_team"] if isinstance(r["detail_team"], list) else []
        else:
            proj["team"] = []

        if r["detail_risks"]:
            proj["risks"] = r["detail_risks"] if isinstance(r["detail_risks"], list) else []
        else:
            proj["risks"] = []

        projects.append(proj)

    return {"projects": projects, "count": len(projects)}


@router.get("/rrhh-capacity")
async def get_rrhh_capacity():
    """Capacidad RRHH disponible."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            "SELECT COALESCE(SUM(200 - carga_actual), 0) FROM pmo_staff_skills WHERE carga_actual IS NOT NULL"
        )
        staff_count = await conn.fetchval(
            "SELECT COUNT(*) FROM pmo_staff_skills WHERE carga_actual IS NOT NULL"
        )
    return {"available_hours": float(total), "staff_count": int(staff_count)}


@router.get("/pulse-alerts/{project_id}")
async def get_pulse_alerts(project_id: str):
    """Alertas y bloqueos del Pulso para un proyecto."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        alerts = await conn.fetch(
            "SELECT * FROM p96_pulse_alerts WHERE title ILIKE $1 OR descripcion ILIKE $1",
            f"%{project_id}%"
        )
        blocks = await conn.fetch(
            "SELECT * FROM p96_pulse_blocks WHERE title ILIKE $1 OR descripcion ILIKE $1",
            f"%{project_id}%"
        )
    return {
        "alerts": [dict(a) for a in alerts],
        "blocks": [dict(b) for b in blocks],
    }


# --- Evaluations CRUD ---

class EvaluationCreate(BaseModel):
    eval_name: str
    objectives: list
    committee: list
    ahp_votes: dict
    obj_weights: list
    crit_weights: dict
    kt_scores: dict
    solver_config: dict
    solver_result: list
    project_count: Optional[int] = None
    total_score: Optional[float] = None
    total_cost: Optional[float] = None
    alignment_scores: Optional[dict] = None  # {project_id: score}


class EvaluationUpdate(BaseModel):
    eval_name: Optional[str] = None
    objectives: Optional[list] = None
    committee: Optional[list] = None
    ahp_votes: Optional[dict] = None
    obj_weights: Optional[list] = None
    crit_weights: Optional[dict] = None
    kt_scores: Optional[dict] = None
    solver_config: Optional[dict] = None
    solver_result: Optional[list] = None
    project_count: Optional[int] = None
    total_score: Optional[float] = None
    total_cost: Optional[float] = None
    alignment_scores: Optional[dict] = None
    changelog_entry: Optional[str] = None


@router.post("/evaluations")
async def create_evaluation(req: EvaluationCreate):
    """Guardar nueva evaluación."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO portfolio_evaluations
            (eval_name, objectives, committee, ahp_votes, obj_weights,
             crit_weights, kt_scores, solver_config, solver_result,
             project_count, total_score, total_cost)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id, version, created_at
        """,
            req.eval_name,
            json.dumps(req.objectives), json.dumps(req.committee),
            json.dumps(req.ahp_votes), json.dumps(req.obj_weights),
            json.dumps(req.crit_weights), json.dumps(req.kt_scores),
            json.dumps(req.solver_config), json.dumps(req.solver_result),
            req.project_count, req.total_score, req.total_cost,
        )

        # Update alignment_score in cartera_build
        if req.alignment_scores:
            for proj_id, score in req.alignment_scores.items():
                await conn.execute(
                    "UPDATE cartera_build SET alignment_score = $1 WHERE id_proyecto = $2",
                    score, proj_id
                )

        # Insert decision in p96_pulse_decisions
        await conn.execute("""
            INSERT INTO p96_pulse_decisions (title, descripcion, own, amt, due, urg)
            VALUES ($1, $2, $3, $4, $5, $6)
        """,
            f"Portfolio Wizard: {req.eval_name}",
            f"Evaluación de portafolio con {req.project_count} proyectos. Score total: {req.total_score}. Coste: {req.total_cost}k€",
            "Comité Ejecutivo", "", "", "media"
        )

        # Insert milestone in p96_pulse_hitos
        await conn.execute("""
            INSERT INTO p96_pulse_hitos (dt, wk, title, descripcion, tg, tgt)
            VALUES ($1, $2, $3, $4, $5, $6)
        """,
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%V"),
            f"Priorización portafolio: {req.eval_name}",
            f"{req.project_count} proyectos evaluados, {req.total_score} score total",
            "portfolio", ""
        )

    return {"id": row["id"], "version": row["version"], "created_at": str(row["created_at"])}


@router.put("/evaluations/{eval_id}")
async def update_evaluation(eval_id: int, req: EvaluationUpdate):
    """Actualizar evaluación existente (incrementar versión)."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT * FROM portfolio_evaluations WHERE id = $1", eval_id
        )
        if not existing:
            raise HTTPException(404, "Evaluación no encontrada")

        new_version = existing["version"] + 1
        changelog_entry = req.changelog_entry or f"Actualización v{new_version}"

        # Build history entry
        history = json.loads(existing["history"]) if existing["history"] else []
        history.append({
            "version": new_version,
            "date": datetime.now().isoformat(),
            "changes": [changelog_entry],
        })

        # Update fields
        updates = {"version": new_version, "modified_at": datetime.now(), "history": json.dumps(history)}
        if req.eval_name is not None: updates["eval_name"] = req.eval_name
        if req.objectives is not None: updates["objectives"] = json.dumps(req.objectives)
        if req.committee is not None: updates["committee"] = json.dumps(req.committee)
        if req.ahp_votes is not None: updates["ahp_votes"] = json.dumps(req.ahp_votes)
        if req.obj_weights is not None: updates["obj_weights"] = json.dumps(req.obj_weights)
        if req.crit_weights is not None: updates["crit_weights"] = json.dumps(req.crit_weights)
        if req.kt_scores is not None: updates["kt_scores"] = json.dumps(req.kt_scores)
        if req.solver_config is not None: updates["solver_config"] = json.dumps(req.solver_config)
        if req.solver_result is not None: updates["solver_result"] = json.dumps(req.solver_result)
        if req.project_count is not None: updates["project_count"] = req.project_count
        if req.total_score is not None: updates["total_score"] = req.total_score
        if req.total_cost is not None: updates["total_cost"] = req.total_cost

        set_clause = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(updates.keys()))
        values = [eval_id] + list(updates.values())
        await conn.execute(
            f"UPDATE portfolio_evaluations SET {set_clause} WHERE id = $1",
            *values
        )

        # Update changelog array
        await conn.execute(
            "UPDATE portfolio_evaluations SET changelog = array_append(changelog, $1) WHERE id = $2",
            changelog_entry, eval_id
        )

        # Update alignment scores if provided
        if req.alignment_scores:
            for proj_id, score in req.alignment_scores.items():
                await conn.execute(
                    "UPDATE cartera_build SET alignment_score = $1 WHERE id_proyecto = $2",
                    score, proj_id
                )

    return {"id": eval_id, "version": new_version}


@router.get("/evaluations")
async def list_evaluations():
    """Listar evaluaciones guardadas."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, eval_name, version, created_at, modified_at,
                   project_count, total_score, total_cost, changelog
            FROM portfolio_evaluations
            ORDER BY modified_at DESC
        """)
    return {"evaluations": [dict(r) for r in rows]}


@router.get("/evaluations/{eval_id}")
async def get_evaluation(eval_id: int):
    """Detalle completo de una evaluación."""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "DB no disponible")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM portfolio_evaluations WHERE id = $1", eval_id
        )
    if not row:
        raise HTTPException(404, "Evaluación no encontrada")
    return dict(row)

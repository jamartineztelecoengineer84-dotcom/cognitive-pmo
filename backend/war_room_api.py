"""
war_room_api.py — Sub-app FastAPI para el War Room Cognitivo
Cognitive PMO — Plataforma de Gestión Predictiva
Autor: Jose Antonio Martínez Victoria
"""
import os
import json
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from database import get_pool

logger = logging.getLogger(__name__)

war_room_app = FastAPI(title="Cognitive PMO War Room", version="1.0")


# ── Helpers ────────────────────────────────────────────────────────────────
def _serialize(row: Any) -> dict:
    if row is None:
        return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, (datetime, date)):
            d[k] = v.isoformat()
    return d


# ══════════════════════════════════════════════════════════════════════════
# ALERTAS INTELIGENTES (AG-012)
# ══════════════════════════════════════════════════════════════════════════

class AlertCreate(BaseModel):
    alert_type: str
    severity: str
    title: str
    description: str
    source_agent: str
    affected_entities: dict = {}
    trigger_condition: dict = {}
    recommended_actions: list = []
    correlation_id: Optional[str] = None
    parent_alert_id: Optional[str] = None
    ttl_hours: int = 24


@war_room_app.post("/alerts")
async def create_alert(a: AlertCreate):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO intelligent_alerts
                    (alert_type,severity,title,description,source_agent,
                     affected_entities,trigger_condition,recommended_actions,
                     correlation_id,parent_alert_id,ttl_hours)
                VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8::jsonb,$9,$10,$11)
                RETURNING *""",
                a.alert_type, a.severity, a.title, a.description, a.source_agent,
                json.dumps(a.affected_entities), json.dumps(a.trigger_condition),
                json.dumps(a.recommended_actions),
                a.correlation_id, a.parent_alert_id, a.ttl_hours,
            )
            return _serialize(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@war_room_app.get("/alerts")
async def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50),
):
    pool = get_pool()
    if not pool:
        return []
    clauses, params = [], []
    if status:
        params.append(status)
        clauses.append(f"status=${len(params)}")
    if severity:
        params.append(severity)
        clauses.append(f"severity=${len(params)}")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(limit)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM intelligent_alerts {where} ORDER BY created_at DESC LIMIT ${len(params)}",
            *params,
        )
        return [_serialize(r) for r in rows]


@war_room_app.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, acknowledged_by: str = Query("PMO Manager")):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE intelligent_alerts SET status='ACKNOWLEDGED',
               acknowledged_by=$2, acknowledged_at=NOW()
               WHERE id=$1 RETURNING *""",
            alert_id, acknowledged_by,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        return _serialize(row)


@war_room_app.put("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE intelligent_alerts SET status='RESOLVED', resolved_at=NOW()
               WHERE id=$1 RETURNING *""",
            alert_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        return _serialize(row)


@war_room_app.get("/alerts/summary")
async def alerts_summary():
    pool = get_pool()
    if not pool:
        return {}
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT severity, status, COUNT(*) as cnt
               FROM intelligent_alerts GROUP BY severity, status"""
        )
        total = await conn.fetchval("SELECT COUNT(*) FROM intelligent_alerts WHERE status='ACTIVE'")
        crit = await conn.fetchval("SELECT COUNT(*) FROM intelligent_alerts WHERE status='ACTIVE' AND severity='CRITICAL'")
        return {
            "active_total": total or 0,
            "active_critical": crit or 0,
            "breakdown": [dict(r) for r in rows],
        }


@war_room_app.get("/alerts/correlations")
async def alert_correlations():
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT correlation_id, COUNT(*) as cnt,
                      array_agg(id) as alert_ids,
                      MAX(severity) as max_severity
               FROM intelligent_alerts
               WHERE correlation_id IS NOT NULL AND status='ACTIVE'
               GROUP BY correlation_id HAVING COUNT(*)>1
               ORDER BY cnt DESC"""
        )
        return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════════
# COMPLIANCE AUDITS (AG-008)
# ══════════════════════════════════════════════════════════════════════════

class AuditCreate(BaseModel):
    audit_type: str
    entity_type: str
    entity_id: str
    severity: str
    finding: str
    recommendation: Optional[str] = None
    evidence: dict = {}
    assignee: Optional[str] = None
    due_date: Optional[str] = None


@war_room_app.post("/audits")
async def create_audit(a: AuditCreate):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO compliance_audits
                    (audit_type,entity_type,entity_id,severity,finding,
                     recommendation,evidence,assignee,due_date)
                VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8,$9) RETURNING *""",
                a.audit_type, a.entity_type, a.entity_id, a.severity, a.finding,
                a.recommendation, json.dumps(a.evidence), a.assignee,
                date.fromisoformat(a.due_date) if a.due_date else None,
            )
            return _serialize(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@war_room_app.get("/audits")
async def list_audits(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    audit_type: Optional[str] = Query(None),
    limit: int = Query(50),
):
    pool = get_pool()
    if not pool:
        return []
    clauses, params = [], []
    if status:
        params.append(status)
        clauses.append(f"status=${len(params)}")
    if severity:
        params.append(severity)
        clauses.append(f"severity=${len(params)}")
    if audit_type:
        params.append(audit_type)
        clauses.append(f"audit_type=${len(params)}")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(limit)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM compliance_audits {where} ORDER BY created_at DESC LIMIT ${len(params)}",
            *params,
        )
        return [_serialize(r) for r in rows]


@war_room_app.put("/audits/{audit_id}")
async def update_audit(audit_id: str, status: str = Query(...)):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    resolved = "NOW()" if status == "RESOLVED" else "NULL"
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"""UPDATE compliance_audits SET status=$2, updated_at=NOW(),
                resolved_at={'NOW()' if status=='RESOLVED' else 'resolved_at'}
                WHERE id=$1 RETURNING *""",
            audit_id, status,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Auditoría no encontrada")
        return _serialize(row)


@war_room_app.get("/compliance/dashboard")
async def compliance_dashboard():
    pool = get_pool()
    if not pool:
        return {}
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM compliance_audits")
        open_c = await conn.fetchval("SELECT COUNT(*) FROM compliance_audits WHERE status='OPEN'")
        crit = await conn.fetchval("SELECT COUNT(*) FROM compliance_audits WHERE status='OPEN' AND severity='CRITICAL'")
        by_type = await conn.fetch(
            "SELECT audit_type, COUNT(*) as cnt FROM compliance_audits WHERE status='OPEN' GROUP BY audit_type"
        )
        by_sev = await conn.fetch(
            "SELECT severity, COUNT(*) as cnt FROM compliance_audits WHERE status='OPEN' GROUP BY severity"
        )
        return {
            "total": total or 0,
            "open": open_c or 0,
            "critical_open": crit or 0,
            "by_type": [dict(r) for r in by_type],
            "by_severity": [dict(r) for r in by_sev],
        }


# ══════════════════════════════════════════════════════════════════════════
# POST-MORTEM (AG-009)
# ══════════════════════════════════════════════════════════════════════════

class PostMortemCreate(BaseModel):
    incident_id: str
    incident_priority: str
    title: str
    timeline: list = []
    root_cause: str
    root_cause_category: Optional[str] = None
    impact_assessment: dict = {}
    corrective_actions: list = []
    preventive_actions: list = []
    lessons_learned: list = []
    mttr_minutes: Optional[int] = None
    mtta_minutes: Optional[int] = None
    sla_breached: bool = False
    agents_involved: list = []
    resources_involved: list = []
    projects_impacted: list = []


@war_room_app.post("/postmortem")
async def create_postmortem(p: PostMortemCreate):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO postmortem_reports
                    (incident_id,incident_priority,title,timeline,root_cause,
                     root_cause_category,impact_assessment,corrective_actions,
                     preventive_actions,lessons_learned,mttr_minutes,mtta_minutes,
                     sla_breached,agents_involved,resources_involved,projects_impacted)
                VALUES ($1,$2,$3,$4::jsonb,$5,$6,$7::jsonb,$8::jsonb,$9::jsonb,$10,
                        $11,$12,$13,$14,$15,$16) RETURNING *""",
                p.incident_id, p.incident_priority, p.title,
                json.dumps(p.timeline), p.root_cause, p.root_cause_category,
                json.dumps(p.impact_assessment), json.dumps(p.corrective_actions),
                json.dumps(p.preventive_actions), p.lessons_learned,
                p.mttr_minutes, p.mtta_minutes, p.sla_breached,
                p.agents_involved, p.resources_involved, p.projects_impacted,
            )
            return _serialize(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@war_room_app.get("/postmortem")
async def list_postmortem(
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50),
):
    pool = get_pool()
    if not pool:
        return []
    clauses, params = [], []
    if priority:
        params.append(priority)
        clauses.append(f"incident_priority=${len(params)}")
    if category:
        params.append(category)
        clauses.append(f"root_cause_category=${len(params)}")
    if status:
        params.append(status)
        clauses.append(f"review_status=${len(params)}")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(limit)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM postmortem_reports {where} ORDER BY created_at DESC LIMIT ${len(params)}",
            *params,
        )
        return [_serialize(r) for r in rows]


@war_room_app.get("/postmortem/{pm_id}")
async def get_postmortem(pm_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM postmortem_reports WHERE id=$1", pm_id)
        if not row:
            raise HTTPException(status_code=404, detail="Post-mortem no encontrado")
        return _serialize(row)


@war_room_app.put("/postmortem/{pm_id}/approve")
async def approve_postmortem(pm_id: str, approved_by: str = Query("PMO Director")):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE postmortem_reports SET review_status='APPROVED',
               approved_by=$2, updated_at=NOW() WHERE id=$1 RETURNING *""",
            pm_id, approved_by,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Post-mortem no encontrado")
        return _serialize(row)


@war_room_app.get("/postmortem/patterns")
async def postmortem_patterns():
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT root_cause_category, COUNT(*) as occurrences,
                      AVG(mttr_minutes) as avg_mttr,
                      SUM(CASE WHEN sla_breached THEN 1 ELSE 0 END) as sla_breaches
               FROM postmortem_reports
               WHERE root_cause_category IS NOT NULL
               GROUP BY root_cause_category ORDER BY occurrences DESC"""
        )
        return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════════
# SIMULACIONES WHAT-IF (AG-010)
# ══════════════════════════════════════════════════════════════════════════

class SimulationRun(BaseModel):
    simulation_name: str
    scenario_type: str
    input_params: dict = {}
    baseline_snapshot: dict = {}
    simulation_result: dict = {}
    risk_score: float = 50.0
    confidence_level: float = 0.7
    recommendations: list = []
    affected_projects: list = []
    affected_resources: list = []
    kpi_deltas: dict = {}


@war_room_app.post("/simulation/run")
async def run_simulation(s: SimulationRun):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO whatif_simulations
                    (simulation_name,scenario_type,input_params,baseline_snapshot,
                     simulation_result,risk_score,confidence_level,recommendations,
                     affected_projects,affected_resources,kpi_deltas)
                VALUES ($1,$2,$3::jsonb,$4::jsonb,$5::jsonb,$6,$7,$8,$9,$10,$11::jsonb)
                RETURNING *""",
                s.simulation_name, s.scenario_type,
                json.dumps(s.input_params), json.dumps(s.baseline_snapshot),
                json.dumps(s.simulation_result), s.risk_score, s.confidence_level,
                s.recommendations, s.affected_projects, s.affected_resources,
                json.dumps(s.kpi_deltas),
            )
            return _serialize(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@war_room_app.get("/simulation")
async def list_simulations(
    scenario_type: Optional[str] = Query(None),
    limit: int = Query(50),
):
    pool = get_pool()
    if not pool:
        return []
    if scenario_type:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM whatif_simulations WHERE scenario_type=$1 ORDER BY created_at DESC LIMIT $2",
                scenario_type, limit,
            )
    else:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM whatif_simulations ORDER BY created_at DESC LIMIT $1", limit
            )
    return [_serialize(r) for r in rows]


@war_room_app.get("/simulation/{sim_id}")
async def get_simulation(sim_id: str):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM whatif_simulations WHERE id=$1", sim_id)
        if not row:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")
        return _serialize(row)


# ══════════════════════════════════════════════════════════════════════════
# WAR ROOM SESSIONS
# ══════════════════════════════════════════════════════════════════════════

class SessionCreate(BaseModel):
    session_name: str
    session_type: str
    participants: list = []
    context: dict = {}


@war_room_app.post("/warroom/sessions")
async def create_session(s: SessionCreate):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO war_room_sessions
                    (session_name,session_type,participants,context)
                VALUES ($1,$2,$3::jsonb,$4::jsonb) RETURNING *""",
                s.session_name, s.session_type,
                json.dumps(s.participants), json.dumps(s.context),
            )
            return _serialize(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@war_room_app.get("/warroom/sessions")
async def list_sessions(status: Optional[str] = Query(None)):
    pool = get_pool()
    if not pool:
        return []
    if status:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM war_room_sessions WHERE status=$1 ORDER BY started_at DESC", status
            )
    else:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM war_room_sessions ORDER BY started_at DESC LIMIT 50"
            )
    return [_serialize(r) for r in rows]


@war_room_app.put("/warroom/sessions/{session_id}/close")
async def close_session(session_id: str, summary: str = Query("")):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE war_room_sessions SET status='CLOSED', summary=$2, closed_at=NOW()
               WHERE id=$1 RETURNING *""",
            session_id, summary,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        return _serialize(row)


@war_room_app.post("/warroom/sessions/{session_id}/message")
async def session_message(session_id: str, agent_id: str = Query(...), content: str = Query(...)):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")
    async with pool.acquire() as conn:
        # Verify session exists
        sess = await conn.fetchval("SELECT id FROM war_room_sessions WHERE id=$1", session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        row = await conn.fetchrow(
            """INSERT INTO agent_conversations
                (session_id,agent_id,agent_name,role,content)
            VALUES ($1,$2,$3,'user',$4) RETURNING *""",
            session_id, agent_id, _agent_name(agent_id), content,
        )
        return _serialize(row)


@war_room_app.get("/warroom/sessions/{session_id}/transcript")
async def session_transcript(session_id: str):
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM agent_conversations WHERE session_id=$1 ORDER BY created_at",
            session_id,
        )
        return [_serialize(r) for r in rows]


@war_room_app.get("/warroom/dashboard")
async def warroom_dashboard():
    pool = get_pool()
    if not pool:
        return {}
    async with pool.acquire() as conn:
        alertas = await conn.fetchval("SELECT COUNT(*) FROM intelligent_alerts WHERE status='ACTIVE'")
        criticas = await conn.fetchval("SELECT COUNT(*) FROM intelligent_alerts WHERE status='ACTIVE' AND severity='CRITICAL'")
        audits = await conn.fetchval("SELECT COUNT(*) FROM compliance_audits WHERE status='OPEN'")
        pms = await conn.fetchval("SELECT COUNT(*) FROM postmortem_reports WHERE review_status='DRAFT'")
        sims = await conn.fetchval("SELECT COUNT(*) FROM whatif_simulations WHERE created_at > NOW() - INTERVAL '7 days'")
        sessions = await conn.fetchval("SELECT COUNT(*) FROM war_room_sessions WHERE status='ACTIVE'")
        return {
            "alertas_activas": alertas or 0,
            "alertas_criticas": criticas or 0,
            "auditorias_pendientes": audits or 0,
            "postmortems_pendientes": pms or 0,
            "simulaciones_semana": sims or 0,
            "sesiones_activas": sessions or 0,
        }


# ══════════════════════════════════════════════════════════════════════════
# CHAT MULTI-AGENTE + HISTORIAL
# ══════════════════════════════════════════════════════════════════════════

class ChatMessage(BaseModel):
    session_id: Optional[str] = None
    agent_id: str
    message: str


AGENT_NAMES = {
    "AG-001": "Dispatcher ITIL",
    "AG-002": "Resource Manager RUN",
    "AG-003": "Demand Forecaster",
    "AG-004": "Buffer Gatekeeper",
    "AG-005": "Estratega PMO",
    "AG-006": "Resource Manager BUILD",
    "AG-007": "Planificador PMBOK",
    "AG-008": "Compliance Auditor",
    "AG-009": "Post-Mortem Engine",
    "AG-010": "Scenario Simulator",
    "AG-012": "Alert Correlator",
    "CLIPY": "Clipy - Asistente de Desarrollo",
}


def _agent_name(agent_id: str) -> str:
    return AGENT_NAMES.get(agent_id, agent_id)


@war_room_app.post("/chat")
async def chat(msg: ChatMessage):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="DB no disponible")

    session_id = msg.session_id or str(datetime.now().strftime("%Y%m%d%H%M%S"))
    agent_name = _agent_name(msg.agent_id)

    # Save user message
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO agent_conversations
                (session_id,agent_id,agent_name,role,content)
            VALUES ($1,$2,$3,'user',$4)""",
            session_id, msg.agent_id, agent_name, msg.message,
        )

    # Try Anthropic API if available
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key and api_key.startswith("sk-ant-"):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            from agent_prompts import AGENT_SYSTEM_PROMPTS, AGENT_TEMPERATURES

            # Get context from DB
            context_data = await _build_agent_context(msg.agent_id)

            # Get recent history
            async with pool.acquire() as conn:
                hist_rows = await conn.fetch(
                    """SELECT role, content FROM agent_conversations
                       WHERE session_id=$1 ORDER BY created_at DESC LIMIT 20""",
                    session_id,
                )

            messages = []
            for r in reversed(list(hist_rows)):
                messages.append({"role": r["role"], "content": r["content"]})

            # Add context to last message
            if context_data and messages:
                messages[-1]["content"] = f"[CONTEXTO ACTUAL]\n{context_data}\n\n{messages[-1]['content']}"

            system_prompt = AGENT_SYSTEM_PROMPTS.get(msg.agent_id, "Eres un asistente de la Cognitive PMO.")
            temperature = AGENT_TEMPERATURES.get(msg.agent_id, 0.3)

            t0 = datetime.now()
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                system=system_prompt,
                messages=messages,
                max_tokens=4096,
                temperature=temperature,
            )
            latency = int((datetime.now() - t0).total_seconds() * 1000)
            reply = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens

            # Save assistant response
            async with pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO agent_conversations
                        (session_id,agent_id,agent_name,role,content,tokens_used,latency_ms,model_used)
                    VALUES ($1,$2,$3,'assistant',$4,$5,$6,'claude-sonnet-4-20250514')""",
                    session_id, msg.agent_id, agent_name, reply, tokens, latency,
                )

            return {
                "session_id": session_id,
                "agent_id": msg.agent_id,
                "agent_name": agent_name,
                "response": reply,
                "tokens_used": tokens,
                "latency_ms": latency,
                "model": "claude-sonnet-4-20250514",
            }
        except ImportError:
            logger.warning("anthropic package not installed, using mock response")
        except Exception as e:
            logger.warning(f"Anthropic API error: {e}")

    # Mock response when API key not available
    mock_responses = {
        "AG-008": f"[AG-008 Compliance Auditor] He analizado tu consulta. Revisando marcos normativos ITIL4, PMBOK7, GDPR, DORA y BCE/CNMV. Para activar respuestas reales de Claude, configura ANTHROPIC_API_KEY.",
        "AG-009": f"[AG-009 Post-Mortem Engine] Aplicando metodología 5 Whys + Ishikawa para analizar la incidencia. Necesito ANTHROPIC_API_KEY para análisis profundo con IA.",
        "AG-010": f"[AG-010 Scenario Simulator] Preparando simulación What-If. Configura ANTHROPIC_API_KEY para ejecutar escenarios con IA generativa.",
        "AG-012": f"[AG-012 Alert Correlator] Correlando señales del ecosistema. Activa ANTHROPIC_API_KEY para correlación inteligente con Claude.",
    }
    reply = mock_responses.get(
        msg.agent_id,
        f"[{msg.agent_id} {agent_name}] Mensaje recibido. Configura ANTHROPIC_API_KEY para respuestas con IA."
    )

    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO agent_conversations
                (session_id,agent_id,agent_name,role,content,model_used)
            VALUES ($1,$2,$3,'assistant',$4,'mock')""",
            session_id, msg.agent_id, agent_name, reply,
        )

    return {
        "session_id": session_id,
        "agent_id": msg.agent_id,
        "agent_name": agent_name,
        "response": reply,
        "tokens_used": 0,
        "latency_ms": 0,
        "model": "mock",
    }


@war_room_app.get("/chat/history/{session_id}")
async def chat_history(session_id: str):
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM agent_conversations WHERE session_id=$1 ORDER BY created_at",
            session_id,
        )
        return [_serialize(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════════
# MÉTRICAS DE AGENTES
# ══════════════════════════════════════════════════════════════════════════

@war_room_app.get("/metrics/agents")
async def all_agent_metrics():
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT * FROM agent_performance_metrics
               ORDER BY metric_date DESC, agent_id LIMIT 100"""
        )
        return [_serialize(r) for r in rows]


@war_room_app.get("/metrics/agents/{agent_id}")
async def agent_metrics(agent_id: str):
    pool = get_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM agent_performance_metrics WHERE agent_id=$1 ORDER BY metric_date DESC LIMIT 30",
            agent_id,
        )
        return [_serialize(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════════
# HELPER: Build context for agent
# ══════════════════════════════════════════════════════════════════════════

async def _build_agent_context(agent_id: str) -> str:
    pool = get_pool()
    if not pool:
        return ""
    parts = []
    try:
        async with pool.acquire() as conn:
            # Get active alerts count
            alerts = await conn.fetchval("SELECT COUNT(*) FROM intelligent_alerts WHERE status='ACTIVE'")
            parts.append(f"Alertas activas: {alerts or 0}")
            # Get open audits
            audits = await conn.fetchval("SELECT COUNT(*) FROM compliance_audits WHERE status='OPEN'")
            parts.append(f"Auditorías pendientes: {audits or 0}")
            # Get project count
            projects = await conn.fetchval("SELECT COUNT(*) FROM cartera_build")
            parts.append(f"Proyectos en cartera: {projects or 0}")
            # Get staff count
            staff = await conn.fetchval("SELECT COUNT(*) FROM pmo_staff_skills")
            parts.append(f"Técnicos en pool: {staff or 0}")
    except Exception as e:
        logger.warning(f"Error building context: {e}")
    return "\n".join(parts)

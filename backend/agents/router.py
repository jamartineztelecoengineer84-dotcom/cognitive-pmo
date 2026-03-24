import asyncio
import json
import re
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from agents.config import AGENT_CONFIGS
from agents.engine import AgentEngine
from agents.spawner import SpawnableEngine, SPAWNABLE_AGENTS
from database import get_pool

router = APIRouter(prefix="/agents", tags=["agents"])


def _sse(payload: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


class InvokeRequest(BaseModel):
    message: str
    session_id: Optional[str] = ""


@router.post("/{agent_id}/invoke")
async def invoke_agent(agent_id: str, body: InvokeRequest):
    """Invoca un agente individual (con spawning si configurado)"""
    if agent_id not in AGENT_CONFIGS:
        raise HTTPException(404, f"Agent {agent_id} not configured")
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "Database not available")
    config = AGENT_CONFIGS[agent_id]

    # Check if agent has spawning configured
    if agent_id in SPAWNABLE_AGENTS:
        spawn_config = SPAWNABLE_AGENTS[agent_id]
        spawner = SpawnableEngine(
            config=config,
            db_pool=pool,
            director_prompt=spawn_config["director_prompt"],
            worker_prompt_template=spawn_config["worker_prompt_template"],
            merger_prompt=spawn_config.get("merger_prompt", ""),
            max_workers=spawn_config.get("max_workers", 8),
            worker_max_tokens=spawn_config.get("worker_max_tokens", 4096),
            programmatic_merge=spawn_config.get("programmatic_merge", False),
            merge_function=spawn_config.get("merge_function"),
        )
        result_data = await spawner.invoke(
            body.message, body.session_id or ""
        )
        return {
            "agent_id": agent_id,
            "response": result_data["response"],
            "spawning_info": result_data["spawning_info"]
        }

    # Normal (non-spawnable) agent
    engine = AgentEngine(config, pool)
    result = await engine.invoke(
        user_msg=body.message,
        session_id=body.session_id or ""
    )
    return {"agent_id": agent_id, "response": result}


@router.get("/")
async def list_agents():
    """Lista todos los agentes configurados"""
    return [
        {
            "agent_id": c.agent_id,
            "agent_name": c.agent_name,
            "model": c.model,
            "tools_count": len(c.tools),
        }
        for c in AGENT_CONFIGS.values()
    ]


# ═══════════════════════════════════════════════════════════════
# Helpers para extraer datos reales de la BD tras la cadena
# ═══════════════════════════════════════════════════════════════

async def _fetch_latest_incident(pool, session_id, dispatcher_text):
    """Busca la incidencia más reciente creada por AG-001"""
    import re as _re
    ticket_match = _re.search(r'(INC-[\w-]+)', dispatcher_text or '')
    ticket_id = ticket_match.group(1) if ticket_match else None
    if ticket_id:
        row = await pool.fetchrow("""
            SELECT ticket_id, incidencia_detectada, prioridad_ia, categoria,
                   sla_limite, area_afectada, impacto_negocio, servicio_afectado,
                   ci_afectado, tecnico_asignado, estado, urgencia, impacto
            FROM incidencias_run WHERE ticket_id = $1
        """, ticket_id)
        if row:
            d = dict(row)
            for k, v in d.items():
                if hasattr(v, 'isoformat'):
                    d[k] = v.isoformat()
            return d
    # Fallback: latest incident
    row = await pool.fetchrow("""
        SELECT ticket_id, incidencia_detectada, prioridad_ia, categoria,
               sla_limite, area_afectada, impacto_negocio, servicio_afectado,
               ci_afectado, tecnico_asignado, estado
        FROM incidencias_run WHERE agente_origen = 'AG-001'
        ORDER BY timestamp_creacion DESC LIMIT 1
    """)
    if row:
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        return d
    return {}


async def _fetch_incident_tasks(pool, ticket_id):
    """Busca las tareas kanban vinculadas a un ticket"""
    if not ticket_id:
        return []
    rows = await pool.fetch("""
        SELECT kt.id, kt.titulo, kt.descripcion, kt.prioridad, kt.columna,
               kt.id_tecnico, kt.horas_estimadas, kt.id_incidencia,
               s.nombre as tecnico_nombre, s.nivel as tecnico_nivel,
               s.silo_especialidad as tecnico_silo, s.carga_actual as tecnico_carga
        FROM kanban_tareas kt
        LEFT JOIN pmo_staff_skills s ON kt.id_tecnico = s.id_recurso
        WHERE kt.id_incidencia = $1
        ORDER BY kt.fecha_creacion ASC
    """, ticket_id)
    result = []
    for r in rows:
        d = dict(r)
        # Parse skill from descripcion JSON
        try:
            desc = __import__('json').loads(d.get('descripcion') or '{}')
            d['skill'] = desc.get('skill_requerida', '')
        except Exception:
            d['skill'] = ''
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        result.append(d)
    return result


# ═══════════════════════════════════════════════════════════════
# CHAIN RUN: Dispatcher → Resource Manager → Buffer (si necesario)
# ═══════════════════════════════════════════════════════════════

@router.post("/run/chain")
async def run_chain(body: InvokeRequest):
    """Cadena RUN completa: AG-001 → AG-002 → AG-004 (si necesario)"""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "Database not available")
    session_id = body.session_id or str(uuid4())
    agents_used = []

    # AG-001 Dispatcher
    e1 = AgentEngine(AGENT_CONFIGS["AG-001"], pool)
    r1 = await e1.invoke(body.message, session_id)
    agents_used.append("AG-001")

    # Fetch real tasks from DB to pass exact IDs to AG-002
    dispatcher_incident = await _fetch_latest_incident(pool, session_id, r1)
    dispatcher_tasks = await _fetch_incident_tasks(pool, dispatcher_incident.get('ticket_id', ''))
    task_list = "\n".join([
        f"- task_id: {t['id']}  titulo: {t['titulo']}  skill: {t.get('skill','')}  columna: {t['columna']}"
        for t in dispatcher_tasks
    ]) if dispatcher_tasks else "No se encontraron tareas en la BD"

    # AG-002 Resource Manager RUN (contexto truncado para reducir costes)
    e2 = AgentEngine(AGENT_CONFIGS["AG-002"], pool)
    r2 = await e2.invoke(
        f"TICKET: {dispatcher_incident.get('ticket_id','')}\n"
        f"TAREAS (usa estos task_id EXACTOS):\n{task_list}\n\n"
        f"Contexto:\n{r1[:1000]}",
        session_id
    )
    agents_used.append("AG-002")

    # Detectar si necesita Buffer Gatekeeper
    needs_buffer = ("needs_buffer" in r2.lower() or
                    "sin técnicos libres" in r2.lower() or
                    "no hay técnicos" in r2.lower() or
                    "todos ocupados" in r2.lower())

    if needs_buffer and "AG-004" in AGENT_CONFIGS:
        e4 = AgentEngine(AGENT_CONFIGS["AG-004"], pool)
        r4 = await e4.invoke(
            f"Escalado. Sin técnicos libres.\nTicket: {dispatcher_incident.get('ticket_id','')}\n{r2[:1500]}",
            session_id
        )
        agents_used.append("AG-004")
        incident = await _fetch_latest_incident(pool, session_id, r1)
        tasks = await _fetch_incident_tasks(pool, incident.get('ticket_id',''))
        return {
            "chain": "RUN",
            "agents": agents_used,
            "result": r4,
            "dispatcher_result": r1,
            "session_id": session_id,
            "buffer_activated": True,
            "incident": incident,
            "tasks": tasks,
        }

    # Fetch actual incident and tasks from DB
    incident = await _fetch_latest_incident(pool, session_id, r1)
    tasks = await _fetch_incident_tasks(pool, incident.get('ticket_id',''))

    return {
        "chain": "RUN",
        "agents": agents_used,
        "result": r2,
        "dispatcher_result": r1,
        "session_id": session_id,
        "buffer_activated": False,
        "incident": incident,
        "tasks": tasks,
    }


# ═══════════════════════════════════════════════════════════════
# CHAIN RUN SSE: Real-time streaming visualization
# ═══════════════════════════════════════════════════════════════

@router.get("/run/chain/stream")
async def run_chain_stream(
    message: str = Query(...),
    session_id: str = Query(default=""),
    token: str = Query(default=""),
):
    """SSE endpoint for real-time RUN chain visualization"""
    pool = get_pool()
    if not pool:
        async def error_gen():
            yield _sse({"event": "error", "message": "DB not available"})
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    if not session_id:
        session_id = str(uuid4())

    async def event_generator():
        try:
            # === AG-001 DISPATCHER ===
            yield _sse({"event": "agent_start", "agent_id": "AG-001", "agent_name": "Dispatcher", "color": "#3b82f6"})
            await asyncio.sleep(0.1)

            yield _sse({"event": "tool_call", "agent_id": "AG-001", "tool": "query_catalogo", "input": message[:80]})

            e1 = AgentEngine(AGENT_CONFIGS["AG-001"], pool)
            r1 = await e1.invoke(message, session_id)

            # Parse dispatcher result for field updates
            priority = "P3"
            sla = 24
            for p in ["P1", "P2", "P3", "P4"]:
                if p in r1:
                    priority = p
                    break
            sla_map = {"P1": 4, "P2": 8, "P3": 24, "P4": 48}
            sla = sla_map.get(priority, 24)

            yield _sse({"event": "field_update", "field": "priority", "value": priority})
            yield _sse({"event": "field_update", "field": "sla", "value": sla})

            now = datetime.now()
            deadline = now + timedelta(hours=sla)
            yield _sse({"event": "sla_started", "priority": priority, "sla_hours": sla, "start": now.isoformat(), "deadline": deadline.isoformat()})

            # Extract tasks from response
            tasks = []
            dash_chars = "-\u2013\u2014"
            task_matches = re.findall(r"(KT-[\w-]+)\s*[" + dash_chars + r"]\s*(.+?)(?:\n|$)", r1)
            for tid, title in task_matches:
                title_clean = re.sub(r"\*+|\(.*?\)", "", title).strip()
                tasks.append({"task_id": tid, "titulo": title_clean})
                yield _sse({"event": "task_created", "task_id": tid, "titulo": title_clean, "priority": priority})
                await asyncio.sleep(0.3)

            # Extract ticket_id
            ticket_match = re.search(r"(INC-[\w-]+)", r1)
            ticket_id = ticket_match.group(1) if ticket_match else "INC-UNKNOWN"

            yield _sse({"event": "field_update", "field": "ticket_id", "value": ticket_id})
            yield _sse({"event": "agent_complete", "agent_id": "AG-001", "response_preview": r1[:200]})

            # === AG-002 RESOURCE MANAGER ===
            yield _sse({"event": "agent_start", "agent_id": "AG-002", "agent_name": "Resource Manager", "color": "#8b5cf6"})
            yield _sse({"event": "tool_call", "agent_id": "AG-002", "tool": "query_staff_by_skill", "input": "Searching technicians..."})

            e2 = AgentEngine(AGENT_CONFIGS["AG-002"], pool)
            ag2_prompt = "Resultado del Dispatcher. Busca t\u00e9cnicos y as\u00edgnalos:\n\n" + r1
            r2 = await e2.invoke(ag2_prompt, session_id)

            # Parse technician assignments
            tech_pattern = r"(KT-[\w-]+).*?(?:Asignado|asignado)[:\s]*(\w[\w\s]+?)\s*\((FTE-\d+)\)\s*[" + dash_chars + r"]\s*(N\d)"
            tech_matches = re.findall(tech_pattern, r2)
            for tid, name, fte, level in tech_matches:
                yield _sse({"event": "technician_assigned", "task_id": tid, "tecnico": name.strip(), "id_recurso": fte, "nivel": level})
                await asyncio.sleep(0.3)

            # Check if buffer needed
            buffer_keywords = [
                "needs_buffer",
                "sin t\u00e9cnicos",
                "no hay t\u00e9cnicos",
                "todos ocupados",
                "no se encontraron",
            ]
            needs_buffer = any(k in r2.lower() for k in buffer_keywords)

            if not needs_buffer:
                yield _sse({"event": "agent_complete", "agent_id": "AG-002", "response_preview": r2[:200]})
                yield _sse({"event": "agent_skip", "agent_id": "AG-004", "reason": "No requerido - t\u00e9cnicos asignados correctamente"})
            else:
                yield _sse({"event": "agent_complete", "agent_id": "AG-002", "response_preview": r2[:200], "escalated": True})

                # === AG-004 BUFFER ===
                yield _sse({"event": "agent_start", "agent_id": "AG-004", "agent_name": "Buffer Gatekeeper", "color": "#f59e0b"})

                if "AG-004" in AGENT_CONFIGS:
                    e4 = AgentEngine(AGENT_CONFIGS["AG-004"], pool)
                    ag4_prompt = "Escalado del Resource Manager:\n\n" + r2
                    r4 = await e4.invoke(ag4_prompt, session_id)
                    yield _sse({"event": "buffer_options", "response": r4[:500]})
                    yield _sse({"event": "agent_complete", "agent_id": "AG-004", "response_preview": r4[:200]})
                    r2 = r4  # Use buffer result as final

            # Kanban update
            yield _sse({"event": "kanban_update", "tasks": tasks})

            # Chain complete
            agents_used = ["AG-001", "AG-002"] + (["AG-004"] if needs_buffer else [])
            yield _sse({"event": "chain_complete", "ticket_id": ticket_id, "priority": priority, "agents_used": agents_used, "session_id": session_id})

        except Exception as e:
            yield _sse({"event": "error", "message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ═══════════════════════════════════════════════════════════════
# CHAIN BUILD: Estratega → Res.Mgr PMO (con ciclo) → Planificador
# ═══════════════════════════════════════════════════════════════

@router.post("/build/chain")
async def build_chain(body: InvokeRequest):
    """Cadena BUILD completa: AG-005 → AG-006 → AG-007"""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "Database not available")
    session_id = body.session_id or str(uuid4())
    agents_used = []

    # AG-005 Estratega
    e5 = AgentEngine(AGENT_CONFIGS["AG-005"], pool)
    r5 = await e5.invoke(body.message, session_id)
    agents_used.append("AG-005")

    # AG-006 Resource Manager PMO (contexto truncado)
    e6 = AgentEngine(AGENT_CONFIGS["AG-006"], pool)
    r6 = await e6.invoke(
        f"Plan del Estratega (resumen):\n{r5[:1500]}",
        session_id
    )
    agents_used.append("AG-006")

    # Ciclo si gap crítico
    if "cycle_back" in r6.lower():
        e5b = AgentEngine(AGENT_CONFIGS["AG-005"], pool)
        r5b = await e5b.invoke(
            f"Ajustar tareas por gaps:\n{r6[:1500]}",
            session_id
        )
        agents_used.append("AG-005-cycle")
        e6b = AgentEngine(AGENT_CONFIGS["AG-006"], pool)
        r6 = await e6b.invoke(f"Plan ajustado:\n{r5b[:1500]}", session_id)
        agents_used.append("AG-006-cycle")

    # AG-007 Planificador (contexto compacto)
    e7 = AgentEngine(AGENT_CONFIGS["AG-007"], pool)
    full_context = (
        f"PROYECTO:\n{body.message[:500]}\n\n"
        f"EDT (AG-005):\n{r5[:1500]}\n\n"
        f"EQUIPO (AG-006):\n{r6[:1000]}\n\n"
        f"INSTRUCCIÓN: Usa calc_critical_path, generate_gantt_mermaid, create_kanban_cards fase 1."
    )
    r7 = await e7.invoke(full_context, session_id)
    agents_used.append("AG-007")

    # Fetch structured data from DB
    structured = {}
    try:
        plan_row = await pool.fetchrow("""
            SELECT * FROM build_project_plans
            ORDER BY created_at DESC LIMIT 1
        """)
        if plan_row:
            plan = dict(plan_row)
            plan_data = plan.get('plan_data', {})
            if isinstance(plan_data, str):
                plan_data = json.loads(plan_data)
            for k, v in plan.items():
                if hasattr(v, 'isoformat'):
                    plan[k] = v.isoformat()
            structured['plan'] = {
                'plan_id': plan.get('id', ''),
                'id_proyecto': plan.get('id_proyecto', ''),
                'nombre': plan.get('nombre', ''),
                'presupuesto': float(plan.get('presupuesto', 0) or 0),
                'duracion_semanas': plan.get('duracion_semanas', 0),
                'prioridad': plan.get('prioridad', ''),
                'plan_data': plan_data
            }

            task_rows = await pool.fetch("""
                SELECT id, titulo, columna, id_tecnico, horas_estimadas, descripcion
                FROM kanban_tareas
                WHERE id_proyecto = $1
                ORDER BY fecha_creacion DESC LIMIT 20
            """, plan.get('id_proyecto', ''))
            structured['tasks'] = []
            for r in task_rows:
                d = dict(r)
                for k2, v2 in d.items():
                    if hasattr(v2, 'isoformat'):
                        d[k2] = v2.isoformat()
                structured['tasks'].append(d)

            if plan_data.get('equipo'):
                structured['team'] = plan_data['equipo']
            else:
                tech_ids = list(set([dict(r).get('id_tecnico') for r in task_rows if dict(r).get('id_tecnico')]))
                if tech_ids:
                    tech_rows = await pool.fetch("""
                        SELECT id_recurso, nombre, nivel, silo_especialidad, carga_actual, skill_principal
                        FROM pmo_staff_skills WHERE id_recurso = ANY($1::text[])
                    """, tech_ids)
                    structured['team'] = [dict(r) for r in tech_rows]
    except Exception as e:
        structured['error'] = str(e)

    return {
        "chain": "BUILD",
        "agents": agents_used,
        "result": r7,
        "session_id": session_id,
        "structured": structured,
    }


# ═══════════════════════════════════════════════════════════════
# DEMAND FORECASTER (manual trigger)
# ═══════════════════════════════════════════════════════════════

@router.post("/forecast/run")
async def run_forecast():
    """Ejecuta el Demand Forecaster manualmente"""
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "Database not available")
    if "AG-003" not in AGENT_CONFIGS:
        raise HTTPException(404, "AG-003 not configured")
    engine = AgentEngine(AGENT_CONFIGS["AG-003"], pool)
    result = await engine.invoke(
        "Genera el informe de predicción de demanda trimestral. "
        "Analiza tendencias, predice carga de las próximas 12 semanas, "
        "y recomienda acciones de contratación o optimización por silo.",
        session_id=f"forecast-{__import__('datetime').datetime.now().strftime('%Y%m%d')}"
    )
    return {"agent": "AG-003", "forecast": result}

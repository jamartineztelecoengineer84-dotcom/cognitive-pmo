"""
COGNITIVE PMO — Tech Copiloto IA
Endpoint que consulta la BD + llama a Claude API para responder preguntas del técnico.
NO es un agente. Es un endpoint aislado.
"""

import os
import re
import json
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from database import get_pool
from auth import get_current_user, UserInfo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tech/copiloto", tags=["Tech Copiloto"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """Eres el copiloto IA de Cognitive PMO. Ayudas a técnicos de BCC Bank con información de la CMDB, CAB, incidencias y proyectos.

Reglas:
- Responde de forma concisa y técnica
- Si tienes datos de la BD, úsalos y cítalos
- Si no tienes datos suficientes, dilo claramente
- Formato: usa markdown ligero (negritas, listas, código inline)
- Máximo 250 palabras
- Incluye recomendaciones accionables cuando sea posible
- No inventes datos que no estén en el contexto proporcionado"""


class CopilotoRequest(BaseModel):
    pregunta: str
    contexto_tipo: Optional[str] = None  # 'run' | 'build' | None
    contexto_id: Optional[str] = None


async def _get_id_recurso(user: UserInfo) -> str:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id_recurso FROM rbac_usuarios WHERE id_usuario = $1", user.id_usuario)
    if not row or not row["id_recurso"]:
        raise HTTPException(status_code=403, detail="Usuario sin recurso técnico vinculado")
    return row["id_recurso"]


async def _load_context(pregunta: str, contexto_tipo: str, contexto_id: str, id_recurso: str) -> dict:
    """Load relevant DB data based on question and context."""
    pool = get_pool()
    if not pool:
        return {"error": "DB no disponible"}

    data = {"fuentes": []}
    pregunta_lower = pregunta.lower()

    async with pool.acquire() as conn:
        # Context-specific data
        if contexto_tipo == "run" and contexto_id:
            inc = await conn.fetchrow(
                "SELECT * FROM incidencias_run WHERE ticket_id = $1", contexto_id)
            if inc:
                data["incidencia"] = dict(inc)
                data["fuentes"].append("incidencias_run")

                # CMDB for CI
                if inc["ci_afectado"]:
                    ci = await conn.fetchrow("""
                        SELECT * FROM cmdb_activos WHERE nombre = $1 OR codigo = $1
                    """, inc["ci_afectado"])
                    if ci:
                        data["ci"] = dict(ci)
                        data["fuentes"].append("cmdb_activos")

                # Kanban tasks
                tareas = await conn.fetch(
                    "SELECT id, titulo, columna, prioridad FROM kanban_tareas WHERE id_incidencia = $1",
                    contexto_id)
                if tareas:
                    data["tareas_kanban"] = [dict(t) for t in tareas]

        elif contexto_tipo == "build" and contexto_id:
            tarea = await conn.fetchrow("""
                SELECT k.*, c.nombre_proyecto FROM kanban_tareas k
                LEFT JOIN cartera_build c ON k.id_proyecto = c.id_proyecto
                WHERE k.id = $1
            """, contexto_id)
            if tarea:
                data["tarea"] = dict(tarea)
                data["fuentes"].append("kanban_tareas")

        # Keyword-based data loading
        # CI/Server mentions
        ci_patterns = re.findall(r'(?:SRV|APP|VM|DR|NET|FW|NAS|DMZ|PT)[-\w]+', pregunta, re.IGNORECASE)
        ci_names = re.findall(r'(?:CORE-DB|API-GW|PG-REPL|DMZ-LB|SAN-)[-\w]+', pregunta, re.IGNORECASE)
        ci_search = ci_patterns + ci_names

        for ci_term in ci_search[:3]:
            ci = await conn.fetchrow("""
                SELECT a.*, i.direccion_ip, i.hostname
                FROM cmdb_activos a
                LEFT JOIN cmdb_ips i ON a.id_activo = i.id_activo
                WHERE a.codigo ILIKE $1 OR a.nombre ILIKE $1
                LIMIT 1
            """, f"%{ci_term}%")
            if ci:
                data.setdefault("cmdb_activos", []).append(dict(ci))
                data["fuentes"].append("cmdb_activos")

                # Dependencies
                deps = await conn.fetch("""
                    SELECT r.tipo_relacion, r.criticidad,
                           a2.codigo, a2.nombre, a2.tipo, a2.estado_ciclo
                    FROM cmdb_relaciones r
                    JOIN cmdb_activos a2 ON r.id_activo_destino = a2.id_activo
                    WHERE r.id_activo_origen = $1
                    UNION ALL
                    SELECT r.tipo_relacion || ' (inversa)', r.criticidad,
                           a2.codigo, a2.nombre, a2.tipo, a2.estado_ciclo
                    FROM cmdb_relaciones r
                    JOIN cmdb_activos a2 ON r.id_activo_origen = a2.id_activo
                    WHERE r.id_activo_destino = $1
                """, ci["id_activo"])
                if deps:
                    data.setdefault("dependencias", []).extend([dict(d) for d in deps])
                    data["fuentes"].append("cmdb_relaciones")

        # CAB/Changes
        if any(w in pregunta_lower for w in ["cab", "cambio", "change", "chg", "ventana"]):
            hace_30d = datetime.now() - timedelta(days=30)
            cambios = await conn.fetch("""
                SELECT id_cambio, tipo_cambio, descripcion, realizado_por, fecha
                FROM cmdb_cambios
                WHERE fecha > $1
                ORDER BY fecha DESC LIMIT 10
            """, hace_30d)
            if cambios:
                data["cambios_recientes"] = [dict(c) for c in cambios]
                data["fuentes"].append("cmdb_cambios")

            proposals = await conn.fetch("""
                SELECT * FROM cmdb_change_proposals ORDER BY created_at DESC LIMIT 5
            """)
            if proposals:
                data["propuestas_cab"] = [dict(p) for p in proposals]
                data["fuentes"].append("cmdb_change_proposals")

        # Similar incidents
        if any(w in pregunta_lower for w in ["similar", "histor", "anterior", "pasad", "previo"]):
            # Get current incident title for similarity search
            titulo_buscar = ""
            if "incidencia" in data:
                titulo_buscar = data["incidencia"].get("incidencia_detectada", "")[:50]
            elif contexto_id:
                titulo_buscar = contexto_id

            if titulo_buscar:
                similares = await conn.fetch("""
                    SELECT ticket_id, incidencia_detectada, prioridad_ia, estado,
                           ci_afectado, tiempo_resolucion_minutos, timestamp_creacion
                    FROM incidencias_run
                    WHERE estado IN ('RESUELTO', 'CERRADO')
                    ORDER BY timestamp_creacion DESC LIMIT 10
                """)
                if similares:
                    data["incidencias_similares"] = [dict(s) for s in similares]
                    data["fuentes"].append("incidencias_run (historial)")

        # SLA
        if any(w in pregunta_lower for w in ["sla", "rendimiento", "kpi", "métr", "puntuacion"]):
            val = await conn.fetch("""
                SELECT * FROM tech_valoracion_mensual
                WHERE id_recurso = $1
                ORDER BY mes DESC LIMIT 3
            """, id_recurso)
            if val:
                data["valoracion_mensual"] = [dict(v) for v in val]
                data["fuentes"].append("tech_valoracion_mensual")

        # Postmortem
        if any(w in pregunta_lower for w in ["postmortem", "lecciones", "root cause", "causa raíz"]):
            pm = await conn.fetch("""
                SELECT * FROM postmortem_reports ORDER BY created_at DESC LIMIT 5
            """)
            if pm:
                data["postmortems"] = [dict(p) for p in pm]
                data["fuentes"].append("postmortem_reports")

    # Deduplicate fuentes
    data["fuentes"] = list(set(data["fuentes"]))
    return data


async def _call_claude(pregunta: str, contexto_json: str, nombre_tecnico: str, id_recurso: str) -> str:
    """Call Claude API with context."""
    if not ANTHROPIC_API_KEY:
        return "⚠️ API key de Anthropic no configurada. Configura ANTHROPIC_API_KEY en las variables de entorno."

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        user_msg = f"""Pregunta del técnico {nombre_tecnico} ({id_recurso}):
{pregunta}

Datos de la BD de Cognitive PMO:
{contexto_json}"""

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        return response.content[0].text

    except Exception as e:
        logger.error(f"Copiloto Claude API error: {e}")
        return f"⚠️ Error al consultar Claude API: {str(e)[:100]}"


@router.post("/chat")
async def copiloto_chat(
    body: CopilotoRequest,
    user: Optional[UserInfo] = Depends(get_current_user),
):
    """Endpoint del copiloto IA. Consulta BD + Claude API."""
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    id_recurso = await _get_id_recurso(user)

    if not body.pregunta.strip():
        raise HTTPException(status_code=400, detail="Pregunta vacía")

    # Load context from DB
    contexto = await _load_context(
        body.pregunta, body.contexto_tipo, body.contexto_id, id_recurso)

    fuentes = contexto.pop("fuentes", [])

    # Serialize context (handle datetimes)
    contexto_json = json.dumps(contexto, indent=2, default=str, ensure_ascii=False)

    # Truncate if too large (keep under 4KB for prompt)
    if len(contexto_json) > 4000:
        contexto_json = contexto_json[:4000] + "\n... (truncado)"

    # Get technician name
    pool = get_pool()
    nombre = id_recurso
    if pool:
        async with pool.acquire() as conn:
            nombre = await conn.fetchval(
                "SELECT nombre FROM pmo_staff_skills WHERE id_recurso = $1", id_recurso) or id_recurso

    # Call Claude
    respuesta = await _call_claude(body.pregunta, contexto_json, nombre, id_recurso)

    return {
        "respuesta": respuesta,
        "fuentes": fuentes,
        "contexto_tipo": body.contexto_tipo,
        "contexto_id": body.contexto_id,
    }

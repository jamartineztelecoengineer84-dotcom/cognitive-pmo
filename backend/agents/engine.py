import anthropic
import re
import time
import json
import logging
from uuid import uuid4
from agents.config import AgentConfig
from agents.tools import TOOL_REGISTRY

log = logging.getLogger("agents.engine")

# Deuda B.1 / F-ARQ02-12: el shell ITSM (post-A.2) prefija el user_msg con
# "TICKET: INC-NNNNNN-YYYYMMDD\n..." cuando ya creó el ticket vía POST
# /incidencias antes de invocar al agente. _log lo extrae para poblar
# agent_conversations.ticket_id sin tocar la firma de invoke().
_TICKET_RE = re.compile(r'^TICKET:\s*(INC-\d{6}-\d{8})')


class AgentEngine:
    def __init__(self, config: AgentConfig, db_pool):
        self.config = config
        self.db = db_pool
        self.client = anthropic.AsyncAnthropic()

    async def invoke(self, user_msg: str, session_id: str = "") -> str:
        """Ejecuta el agente con ciclo tool_use. Máx 10 iteraciones."""
        messages = await self._load_history(session_id)
        messages.append({"role": "user", "content": user_msg})
        t0 = time.monotonic()
        total_tokens = 0
        final = ""

        all_text_parts = []

        for iteration in range(10):
            resp = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=self.config.system_prompt,
                tools=self.config.tools,
                messages=messages
            )
            total_tokens += resp.usage.input_tokens + resp.usage.output_tokens

            text_parts = []
            tool_calls = []
            for block in resp.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block)

            if text_parts:
                all_text_parts.extend(text_parts)

            if not tool_calls:
                final = "\n".join(all_text_parts)
                break

            # Hay tool_use — ejecutar tools y devolver resultados
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for tc in tool_calls:
                log.info(f"[{self.config.agent_id}] tool: {tc.name}({tc.input})")
                fn = TOOL_REGISTRY.get(tc.name)
                if fn is None:
                    result = {"error": f"Tool {tc.name} not found in registry"}
                    log.error(f"Tool not found: {tc.name}")
                else:
                    try:
                        result = await fn(self.db, **tc.input)
                    except Exception as e:
                        result = {"error": str(e)}
                        log.error(f"Tool {tc.name} failed: {e}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": json.dumps(result, default=str, ensure_ascii=False)
                })
            messages.append({"role": "user", "content": tool_results})

        if not final.strip():
            if all_text_parts:
                final = "\n".join(all_text_parts)
            else:
                final = "Agente completó sus operaciones. Datos guardados en BD."

        latency = int((time.monotonic() - t0) * 1000)
        log.info(f"[{self.config.agent_id}] completed in {latency}ms, {total_tokens} tokens")
        await self._log(session_id, user_msg, final, total_tokens, latency)
        return final

    async def _load_history(self, session_id: str) -> list:
        """Carga historial de conversación para contexto"""
        if not session_id or not self.db:
            return []
        try:
            rows = await self.db.fetch("""
                SELECT role, content FROM agent_conversations
                WHERE session_id = $1 AND agent_id = $2
                ORDER BY created_at ASC LIMIT 20
            """, session_id, self.config.agent_id)
            return [{"role": r["role"], "content": r["content"]} for r in rows]
        except Exception as e:
            log.warning(f"Could not load history: {e}")
            return []

    async def _log(self, session_id: str, user_msg: str, response: str,
                   tokens: int, latency: int):
        """Registra conversación y métricas en PostgreSQL"""
        if not self.db:
            return
        if not session_id:
            session_id = str(uuid4())

        try:
            # Deuda B.1 / F-ARQ02-12: derivar ticket_id del prefijo TICKET:
            # del shell ITSM A.2. EXISTS guard para no crear fantasmas (la
            # columna es soft, sin FK — el guard preserva test_ningun_ticket_id_fantasma).
            m = _TICKET_RE.match(user_msg or "")
            ticket_id = await self.db.fetchval(
                "SELECT ticket_id FROM incidencias_run WHERE ticket_id=$1",
                m.group(1),
            ) if m else None

            # Log conversación (user + assistant)
            for role, content in [("user", user_msg), ("assistant", response)]:
                if content:
                    await self.db.execute("""
                        INSERT INTO agent_conversations
                        (session_id, agent_id, agent_name, role, content,
                         tokens_used, model_used, latency_ms, ticket_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """, session_id, self.config.agent_id, self.config.agent_name,
                        role, content, tokens, self.config.model, latency, ticket_id)

            # Log métricas (upsert por agente+fecha)
            await self.db.execute("""
                INSERT INTO agent_performance_metrics
                (id, agent_id, metric_date, total_invocations, avg_latency_ms,
                 total_tokens_consumed)
                VALUES ($1, $2, CURRENT_DATE, 1, $3, $4)
                ON CONFLICT (agent_id, metric_date) DO UPDATE SET
                    total_invocations = agent_performance_metrics.total_invocations + 1,
                    avg_latency_ms = (agent_performance_metrics.avg_latency_ms + $3) / 2,
                    total_tokens_consumed = agent_performance_metrics.total_tokens_consumed + $4
            """, str(uuid4()), self.config.agent_id, latency, tokens)
        except Exception as e:
            log.warning(f"Could not log agent metrics: {e}")

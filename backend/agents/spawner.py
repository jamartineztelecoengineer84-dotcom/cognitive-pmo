"""
Agent Spawner — Patrón Director/Workers/Merger para agentes que generan
outputs proporcionales al tamaño del proyecto.

Uso: Los agentes AG-005, AG-013 y AG-007 usan este sistema.
El endpoint /agents/{agent_id}/invoke detecta si el agente tiene spawning
configurado y usa SpawnableEngine en vez de AgentEngine normal.
"""
import asyncio
import time
import json
import logging
from typing import List, Dict, Any, Optional
from agents.config import AgentConfig, load_prompt, AGENT_CONFIGS
from agents.engine import AgentEngine

log = logging.getLogger("agents.spawner")


_HAIKU_MODEL = "claude-haiku-4-5-20251001"

# Tarifas USD por millón de tokens (para estimación de costes)
_COST_RATES = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_create": 3.75},
    _HAIKU_MODEL:               {"input": 0.80, "output": 4.0,  "cache_read": 0.08, "cache_create": 1.0},
    # OpenAI models (ARQ-04)
    "gpt-4.1":                  {"input": 2.0,  "output": 8.0,  "cache_read": 0.50, "cache_create": 0.0},
    "gpt-4o-mini":              {"input": 0.15, "output": 0.60, "cache_read": 0.0,  "cache_create": 0.0},
    # ChatGPT Codex via Plus subscription — zero marginal cost (ARQ-04 F6b)
    "gpt-5.4":                  {"input": 0.0,  "output": 0.0,  "cache_read": 0.0,  "cache_create": 0.0},
    # Ollama local models — zero cost (ARQ-04)
    "llama3:8b":                {"input": 0.0,  "output": 0.0,  "cache_read": 0.0,  "cache_create": 0.0},
    "gemma3:1b":                {"input": 0.0,  "output": 0.0,  "cache_read": 0.0,  "cache_create": 0.0},
}


class SpawnableEngine:
    """Motor de agente con capacidad de spawning Director/Workers/Merger."""

    def __init__(self, config: AgentConfig, db_pool,
                 director_prompt: str,
                 worker_prompt_template: str,
                 merger_prompt: str,
                 max_workers: int = 8,
                 worker_max_tokens: int = 4096,
                 programmatic_merge: bool = False,
                 merge_function=None,
                 worker_model: str = None):
        self.config = config
        self.db = db_pool
        self.director_prompt = director_prompt
        self.worker_prompt_template = worker_prompt_template
        self.merger_prompt = merger_prompt
        self.max_workers = max_workers
        self.worker_max_tokens = worker_max_tokens
        self.programmatic_merge = programmatic_merge
        self.merge_function = merge_function
        self.worker_model = worker_model or self.config.model

    async def invoke(self, user_msg: str, session_id: str = "",
                     progress_callback=None) -> dict:
        """
        Ejecuta el ciclo Director -> Workers -> Merger.

        progress_callback: async function(event_type, data) para notificar.
        event_type: 'director_start', 'director_done', 'worker_start',
                    'worker_done', 'merger_start', 'merger_done'

        Returns: {
            "response": str (JSON final fusionado),
            "spawning_info": {
                "num_workers": int,
                "worker_results": [...],
                "director_time_ms": int,
                "workers_time_ms": int,
                "merger_time_ms": int,
                "total_time_ms": int
            }
        }
        """
        t_total = time.monotonic()
        spawning_info = {"num_workers": 0, "worker_results": []}
        # Acumuladores de tokens por rol
        cost_tracker = {
            "director": {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "model": self.config.model},
            "workers":  {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "model": self.worker_model},
            "merger":   {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "model": self.config.model},
        }

        # === FASE 1: DIRECTOR ===
        if progress_callback:
            await progress_callback("director_start", {
                "agent_id": self.config.agent_id
            })

        t_dir = time.monotonic()
        director_config = AgentConfig(
            agent_id=f"{self.config.agent_id}-DIR",
            agent_name=f"{self.config.agent_name} Director",
            system_prompt=self.director_prompt,
            tools=self.config.tools,
            model=self.config.model,
            max_tokens=4096,
            temperature=self.config.temperature,
            cache_system=True,
        )
        director_engine = AgentEngine(director_config, self.db)
        director_result = await director_engine.invoke(user_msg, session_id + "-DIR")
        cost_tracker["director"]["input"] += director_engine.last_input_tokens
        cost_tracker["director"]["output"] += director_engine.last_output_tokens
        cost_tracker["director"]["cache_read"] += director_engine.last_cache_read_tokens
        cost_tracker["director"]["cache_create"] += director_engine.last_cache_creation_tokens

        work_items = self._parse_director_output(director_result)
        spawning_info["director_time_ms"] = int((time.monotonic() - t_dir) * 1000)

        if progress_callback:
            await progress_callback("director_done", {
                "agent_id": self.config.agent_id,
                "num_workers": len(work_items),
                "items": [w.get("nombre", f"Worker {i+1}") for i, w in enumerate(work_items)],
                "time_ms": spawning_info["director_time_ms"]
            })

        if not work_items:
            log.warning(f"[{self.config.agent_id}] Director no genero work items, usando output directo")
            self._log_cost_summary(cost_tracker, spawning_info)
            return {
                "response": director_result,
                "spawning_info": spawning_info
            }

        # === FASE 2: WORKERS EN PARALELO ===
        num_workers = min(len(work_items), self.max_workers)
        spawning_info["num_workers"] = num_workers

        if progress_callback:
            await progress_callback("workers_start", {
                "agent_id": self.config.agent_id,
                "num_workers": num_workers
            })

        t_workers = time.monotonic()
        worker_tasks = []
        for i, work_item in enumerate(work_items[:num_workers]):
            worker_tasks.append(
                self._run_worker(i, work_item, director_result,
                                 session_id, progress_callback)
            )

        worker_results = await asyncio.gather(*worker_tasks, return_exceptions=True)

        valid_results = []
        for i, result in enumerate(worker_results):
            if isinstance(result, Exception):
                log.error(f"[{self.config.agent_id}-W{i+1}] Worker fallo: {result}")
                spawning_info["worker_results"].append({
                    "index": i, "status": "error", "error": str(result)
                })
            else:
                # result es dict {text, input_tokens, output_tokens, ...}
                text = result["text"] if isinstance(result, dict) else result
                cost_tracker["workers"]["input"] += result.get("input_tokens", 0) if isinstance(result, dict) else 0
                cost_tracker["workers"]["output"] += result.get("output_tokens", 0) if isinstance(result, dict) else 0
                cost_tracker["workers"]["cache_read"] += result.get("cache_read_tokens", 0) if isinstance(result, dict) else 0
                cost_tracker["workers"]["cache_create"] += result.get("cache_creation_tokens", 0) if isinstance(result, dict) else 0
                valid_results.append({"index": i, "result": text})
                spawning_info["worker_results"].append({
                    "index": i, "status": "ok",
                    "chars": len(text) if isinstance(text, str) else 0
                })

        spawning_info["workers_time_ms"] = int((time.monotonic() - t_workers) * 1000)

        # === FASE 3: MERGER ===
        if self.programmatic_merge and self.merge_function:
            if progress_callback:
                await progress_callback("merger_start", {
                    "agent_id": self.config.agent_id,
                    "valid_workers": len(valid_results),
                    "total_workers": num_workers,
                    "mode": "programmatic"
                })
            t_merger = time.monotonic()
            try:
                final_result = self.merge_function(user_msg, director_result, valid_results)
                spawning_info["merger_time_ms"] = int((time.monotonic() - t_merger) * 1000)
                spawning_info["total_time_ms"] = int((time.monotonic() - t_total) * 1000)
                spawning_info["merger_mode"] = "programmatic"
                if progress_callback:
                    await progress_callback("merger_done", {
                        "agent_id": self.config.agent_id,
                        "total_time_ms": spawning_info["total_time_ms"],
                        "mode": "programmatic"
                    })
                self._log_cost_summary(cost_tracker, spawning_info)
                return {"response": final_result, "spawning_info": spawning_info}
            except Exception as e:
                log.error(f"[{self.config.agent_id}] Programmatic merge failed: {e}, falling back to LLM merger")

        # LLM Merger fallback
        if progress_callback:
            await progress_callback("merger_start", {
                "agent_id": self.config.agent_id,
                "valid_workers": len(valid_results),
                "total_workers": num_workers
            })

        t_merger = time.monotonic()
        merger_config = AgentConfig(
            agent_id=f"{self.config.agent_id}-MRG",
            agent_name=f"{self.config.agent_name} Merger",
            system_prompt=self.merger_prompt or "Fusiona los resultados de los workers en un JSON unico. Devuelve SOLO JSON.",
            tools=self.config.tools,
            model=self.config.model,
            max_tokens=8192,
            temperature=0.2,
            cache_system=True,
        )
        merger_engine = AgentEngine(merger_config, self.db)
        merger_input = self._build_merger_input(user_msg, director_result, valid_results)
        final_result = await merger_engine.invoke(merger_input, session_id + "-MRG")
        cost_tracker["merger"]["input"] += merger_engine.last_input_tokens
        cost_tracker["merger"]["output"] += merger_engine.last_output_tokens
        cost_tracker["merger"]["cache_read"] += merger_engine.last_cache_read_tokens
        cost_tracker["merger"]["cache_create"] += merger_engine.last_cache_creation_tokens

        spawning_info["merger_time_ms"] = int((time.monotonic() - t_merger) * 1000)
        spawning_info["total_time_ms"] = int((time.monotonic() - t_total) * 1000)

        if progress_callback:
            await progress_callback("merger_done", {
                "agent_id": self.config.agent_id,
                "total_time_ms": spawning_info["total_time_ms"]
            })

        self._log_cost_summary(cost_tracker, spawning_info)
        return {"response": final_result, "spawning_info": spawning_info}

    def _log_cost_summary(self, cost_tracker: dict, spawning_info: dict):
        """Loggea resumen de tokens y coste estimado por rol."""
        total_cost = 0.0
        lines = [f"[{self.config.agent_id}] === COST SUMMARY ==="]
        for role, data in cost_tracker.items():
            model = data["model"]
            rates = _COST_RATES.get(model, _COST_RATES["claude-sonnet-4-20250514"])
            inp_cost = (data["input"] / 1_000_000) * rates["input"]
            out_cost = (data["output"] / 1_000_000) * rates["output"]
            cache_r_cost = (data["cache_read"] / 1_000_000) * rates["cache_read"]
            cache_c_cost = (data["cache_create"] / 1_000_000) * rates["cache_create"]
            role_cost = inp_cost + out_cost + cache_r_cost + cache_c_cost
            total_cost += role_cost
            lines.append(
                f"  {role:10s} | model={model.split('-')[1][:6]:6s} | "
                f"in={data['input']:6d} out={data['output']:6d} "
                f"cache_r={data['cache_read']:5d} cache_c={data['cache_create']:5d} | "
                f"${role_cost:.4f}"
            )
        lines.append(f"  {'TOTAL':10s} | ${total_cost:.4f}")
        lines.append(f"  time={spawning_info.get('total_time_ms', 0)}ms "
                      f"workers={spawning_info.get('num_workers', 0)}")
        log.info("\n".join(lines))

    async def _run_worker(self, index: int, work_item: dict,
                          director_context: str, session_id: str,
                          progress_callback=None) -> str:
        """Ejecuta un worker efimero para un item especifico."""
        worker_id = f"{self.config.agent_id}-W{index + 1}"

        if progress_callback:
            await progress_callback("worker_start", {
                "worker_id": worker_id,
                "item_name": work_item.get("nombre", f"Item {index + 1}")
            })

        t_w = time.monotonic()

        worker_prompt = self.worker_prompt_template.replace(
            "{{WORK_ITEM}}", json.dumps(work_item, ensure_ascii=False)
        ).replace(
            "{{WORKER_INDEX}}", str(index + 1)
        ).replace(
            "{{TOTAL_WORKERS}}", str(self.max_workers)
        )

        worker_config = AgentConfig(
            agent_id=worker_id,
            agent_name=f"{self.config.agent_name} Worker {index + 1}",
            system_prompt=worker_prompt,
            tools=self.config.tools,
            model=self.worker_model,
            max_tokens=self.worker_max_tokens,
            temperature=0.1,
            cache_system=True,
        )

        worker_engine = AgentEngine(worker_config, self.db)
        result = await worker_engine.invoke(
            f"CONTEXTO DEL DIRECTOR:\n{director_context}\n\n"
            f"TU TAREA ESPECIFICA:\n{json.dumps(work_item, ensure_ascii=False)}",
            session_id + f"-W{index + 1}"
        )

        elapsed = int((time.monotonic() - t_w) * 1000)

        if progress_callback:
            await progress_callback("worker_done", {
                "worker_id": worker_id,
                "time_ms": elapsed,
                "chars": len(result) if isinstance(result, str) else 0
            })

        log.info(f"[{worker_id}] Completado en {elapsed}ms")
        return {
            "text": result,
            "input_tokens": worker_engine.last_input_tokens,
            "output_tokens": worker_engine.last_output_tokens,
            "cache_read_tokens": worker_engine.last_cache_read_tokens,
            "cache_creation_tokens": worker_engine.last_cache_creation_tokens,
        }

    def _parse_director_output(self, director_result: str) -> List[dict]:
        """
        Parsea el output del director para extraer los work items.
        Busca arrays conocidos en el JSON del director.
        """
        try:
            clean = director_result.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            first = clean.find("{")
            last = clean.rfind("}")
            if first >= 0 and last > first:
                parsed = json.loads(clean[first:last + 1])
                for key in ["work_items", "fases", "lotes", "batches", "items", "phases"]:
                    if key in parsed and isinstance(parsed[key], list):
                        return parsed[key]
                if "edt" in parsed and "fases" in parsed.get("edt", {}):
                    return parsed["edt"]["fases"]
        except Exception as e:
            log.error(f"Error parseando director output: {e}")
        return []

    def _build_merger_input(self, original_msg: str, director_result: str,
                            worker_results: List[dict]) -> str:
        """Construye el mensaje para el merger con todos los resultados."""
        parts = [
            "SOLICITUD ORIGINAL:",
            original_msg[:2000],
            "\nESTRUCTURA DEL DIRECTOR:",
            director_result[:3000],
            f"\nRESULTADOS DE {len(worker_results)} WORKERS:"
        ]
        for wr in worker_results:
            idx = wr["index"]
            result = wr["result"]
            parts.append(f"\n--- WORKER {idx + 1} ---")
            parts.append(result[:4000] if isinstance(result, str) else json.dumps(result)[:4000])

        parts.append("\nINSTRUCCION: Fusiona todos los resultados en un JSON unico y coherente. "
                     "Ajusta dependencias entre fases/items. Devuelve SOLO JSON valido.")
        return "\n".join(parts)


# === FUNCIONES DE MERGE PROGRAMÁTICO ===

def _extract_json_block(raw: str, marker: str = None) -> dict:
    """Extract JSON from text that may contain narrative + JSON, possibly truncated."""
    if not raw or not isinstance(raw, str):
        return raw if isinstance(raw, dict) else {}
    clean = raw.strip()

    # Strategy 1: find marker key and walk back to enclosing {
    if marker:
        idx = clean.find(f'"{marker}"')
        if idx >= 0:
            depth = 0
            start = idx
            for i in range(idx - 1, -1, -1):
                if clean[i] == '}':
                    depth += 1
                elif clean[i] == '{':
                    if depth == 0:
                        start = i
                        break
                    depth -= 1
            # Try to find matching close
            depth = 0
            for i in range(start, len(clean)):
                if clean[i] == '{':
                    depth += 1
                elif clean[i] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(clean[start:i + 1])
                        except json.JSONDecodeError:
                            break

            # Strategy 1b: JSON is truncated — repair by closing open braces/brackets
            fragment = clean[start:]
            repaired = _repair_truncated_json(fragment)
            if repaired:
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    pass

    # Strategy 2: last } to matching {
    last_close = clean.rfind("}")
    if last_close >= 0:
        depth = 0
        for i in range(last_close, -1, -1):
            if clean[i] == '}':
                depth += 1
            elif clean[i] == '{':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(clean[i:last_close + 1])
                    except json.JSONDecodeError:
                        break

    # Strategy 3: repair from first { to end
    first_brace = clean.find("{")
    if first_brace >= 0:
        fragment = clean[first_brace:]
        repaired = _repair_truncated_json(fragment)
        if repaired:
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

    return {}


def _repair_truncated_json(fragment: str) -> str:
    """Attempt to repair truncated JSON by closing open braces/brackets and strings."""
    if not fragment:
        return None
    # Remove trailing incomplete value (after last : with no closing)
    # Find last complete key-value pair
    s = fragment.rstrip()
    # Close any open string
    in_string = False
    escape = False
    for ch in s:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
    if in_string:
        s += '"'

    # Remove trailing incomplete value after last comma or colon
    # Find last valid closing character
    last_valid = len(s) - 1
    while last_valid > 0 and s[last_valid] not in ']}",0123456789nulltruefalse':
        last_valid -= 1
    # Trim to last valid JSON token ending
    for i in range(len(s) - 1, max(0, len(s) - 50), -1):
        if s[i] in '}]':
            last_valid = i
            break
        elif s[i] == ',':
            last_valid = i - 1
            break
    s = s[:last_valid + 1]

    # Count open braces/brackets and close them
    opens = 0
    open_brackets = 0
    in_str = False
    esc = False
    for ch in s:
        if esc:
            esc = False
            continue
        if ch == '\\':
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
        if not in_str:
            if ch == '{':
                opens += 1
            elif ch == '}':
                opens -= 1
            elif ch == '[':
                open_brackets += 1
            elif ch == ']':
                open_brackets -= 1

    s += ']' * max(0, open_brackets)
    s += '}' * max(0, opens)
    return s if s else None


def merge_ag013_subtasks(original_msg: str, director_result: str, worker_results: list) -> str:
    """Merge programático para AG-013: concatena subtasks_by_task de cada worker."""
    merged = {"subtasks_by_task": {}, "total_subtasks": 0, "tecnologias_detectadas": []}
    techs = set()
    log.info(f"[AG-013-MERGE] Recibidos {len(worker_results)} resultados de workers")
    for i, wr in enumerate(worker_results):
        try:
            raw = wr.get("result", "")
            log.info(f"[AG-013-MERGE] Worker {i}: type={type(raw).__name__}, len={len(str(raw))}, has_subtasks_by_task={'subtasks_by_task' in str(raw)}")
            if isinstance(raw, dict):
                data = raw
            else:
                data = _extract_json_block(str(raw), "subtasks_by_task")
            sbt = data.get("subtasks_by_task", {})
            log.info(f"[AG-013-MERGE] Worker {i}: extracted {len(sbt)} task groups")
            for tid, subtasks in sbt.items():
                if tid not in merged["subtasks_by_task"]:
                    merged["subtasks_by_task"][tid] = []
                if isinstance(subtasks, list):
                    merged["subtasks_by_task"][tid].extend(subtasks)
                    merged["total_subtasks"] += len(subtasks)
            for t in data.get("tecnologias_detectadas", []):
                techs.add(t)
        except Exception as e:
            log.warning(f"merge_ag013: error parsing worker {i} result: {e}")
    merged["tecnologias_detectadas"] = sorted(list(techs))
    merged["total_tareas_cubiertas"] = len(merged["subtasks_by_task"])
    log.info(f"[AG-013-MERGE] Final: {merged['total_subtasks']} subtasks across {merged['total_tareas_cubiertas']} tasks")
    return json.dumps(merged, ensure_ascii=False)


def merge_ag007_sprints(original_msg: str, director_result: str, worker_results: list) -> str:
    """Merge programático para AG-007: concatena sprints y renumera."""
    all_sprints = []
    total_sp = 0
    item_counter = 1
    sprint_counter = 1
    log.info(f"[AG-007-MERGE] Recibidos {len(worker_results)} resultados de workers")
    for wr in worker_results:
        try:
            raw = wr.get("result", "")
            if isinstance(raw, dict):
                data = raw
            else:
                data = _extract_json_block(str(raw), "sprints")
            for sprint in data.get("sprints", []):
                sprint["numero"] = sprint_counter
                sprint_counter += 1
                for item in sprint.get("items", []):
                    item["id"] = f"PROJ-{item_counter:03d}"
                    item_counter += 1
                total_sp += sprint.get("story_points", 0)
                all_sprints.append(sprint)
        except Exception as e:
            log.warning(f"merge_ag007: error parsing worker result: {e}")
    dir_strategy = {}
    try:
        dir_data = _extract_json_block(director_result, "estrategia") if isinstance(director_result, str) else (director_result or {})
        dir_strategy = dir_data.get("estrategia", {})
    except Exception:
        pass
    log.info(f"[AG-007-MERGE] Final: {len(all_sprints)} sprints, {total_sp} SP")
    result = {
        "sprints": all_sprints,
        "total_story_points": total_sp,
        "velocidad_media": dir_strategy.get("velocidad_estimada", 38),
        "num_sprints": len(all_sprints),
        "gantt_mermaid": "",
        "ruta_critica": dir_strategy.get("gantt_params", {"semanas": 41, "holgura": 4}),
        "ceremonias": [
            {"nombre": "Sprint Planning", "cuando": "Lunes S1", "duracion": "2h"},
            {"nombre": "Daily Standup", "cuando": "Diario 9:15", "duracion": "15min"},
            {"nombre": "Sprint Review", "cuando": "Viernes S2", "duracion": "1h"},
            {"nombre": "Retrospectiva", "cuando": "Viernes S2", "duracion": "1h"},
            {"nombre": "Backlog Grooming", "cuando": "Miercoles", "duracion": "1h"}
        ]
    }
    return json.dumps(result, ensure_ascii=False)


# === REGISTRO DE AGENTES SPAWNABLES ===
# Se configura en config.py — dict para lookup
SPAWNABLE_AGENTS: Dict[str, dict] = {}

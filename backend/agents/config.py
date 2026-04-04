from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any


@dataclass(frozen=True)
class AgentConfig:
    agent_id: str
    agent_name: str
    system_prompt: str
    tools: List[Dict[str, Any]]
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 2048
    temperature: float = 0.3


def load_prompt(filename: str) -> str:
    """Carga system prompt desde fichero .txt"""
    path = Path(__file__).parent / "prompts" / filename
    return path.read_text(encoding="utf-8")


# Se irá llenando en cada fase
AGENT_CONFIGS: Dict[str, AgentConfig] = {}


from agents.tools import (
    QUERY_CATALOGO_SCHEMA, CREATE_INCIDENT_SCHEMA, CREATE_TASKS_SCHEMA,
    QUERY_STAFF_BY_SKILL_SCHEMA, ASSIGN_TECHNICIAN_SCHEMA,
    QUERY_BUILD_ASSIGNMENTS_SCHEMA, FIND_N4_SILO_FALLBACK_SCHEMA,
    WRITE_GOVERNANCE_TX_SCHEMA,
    DECOMPOSE_PMBOK_SCHEMA, ASSIGN_SKILLS_TO_TASKS_SCHEMA,
    CREATE_BUILD_PROJECT_SCHEMA,
    FORM_TEAM_SCHEMA, NOTIFY_GOVERNANCE_SCHEMA,
    CALC_CRITICAL_PATH_SCHEMA, GENERATE_GANTT_MERMAID_SCHEMA,
    CREATE_KANBAN_CARDS_SCHEMA,
    QUERY_CMDB_ACTIVO_SCHEMA, QUERY_CMDB_IPS_SCHEMA,
    QUERY_CMDB_RELACIONES_SCHEMA, QUERY_CMDB_SOFTWARE_SCHEMA,
    ENRICH_KANBAN_CARD_SCHEMA,
    RUN_PROPHET_SCHEMA, QUERY_CAPACITY_SCHEMA, STORE_FORECAST_SCHEMA,
    CREATE_BUDGET_SCHEMA,
    QUERY_DIRECTORIO_SCHEMA,
    # BUILD v2.0 tools
    DECOMPOSE_SUBTASKS_SCHEMA, ANALYZE_RISKS_SCHEMA,
    QUERY_POSTMORTEM_PATTERNS_SCHEMA, MAP_STAKEHOLDERS_SCHEMA,
    QUERY_PM_CANDIDATES_SCHEMA, CALC_ROI_SCHEMA,
    CALC_EVM_BASELINE_SCHEMA, DEFINE_QUALITY_GATES_SCHEMA,
    QUERY_SIMILAR_PROJECTS_SCHEMA,
    # AG-011 CAB tools
    QUERY_CALENDARIO_PERIODOS_SCHEMA, QUERY_DEMAND_HISTORY_SCHEMA,
    QUERY_CHANGE_WINDOWS_SCHEMA, QUERY_CAB_CONTEXTO_BUILD_SCHEMA,
    QUERY_CAB_CONTEXTO_RUN_SCHEMA, CREATE_CHANGE_PROPOSAL_SCHEMA,
    CREATE_CAB_ALERTS_SCHEMA,
)

AGENT_CONFIGS["AG-001"] = AgentConfig(
    agent_id="AG-001",
    agent_name="Dispatcher",
    system_prompt=load_prompt("ag001_dispatcher.txt"),
    tools=[QUERY_CATALOGO_SCHEMA, CREATE_INCIDENT_SCHEMA, CREATE_TASKS_SCHEMA],
    max_tokens=1500,
)

AGENT_CONFIGS["AG-002"] = AgentConfig(
    agent_id="AG-002",
    agent_name="Resource Manager RUN",
    system_prompt=load_prompt("ag002_resource_mgr_run.txt"),
    tools=[QUERY_STAFF_BY_SKILL_SCHEMA, ASSIGN_TECHNICIAN_SCHEMA, QUERY_DIRECTORIO_SCHEMA],
    max_tokens=1500,
)

AGENT_CONFIGS["AG-004"] = AgentConfig(
    agent_id="AG-004",
    agent_name="Buffer Gatekeeper",
    system_prompt=load_prompt("ag004_buffer_gatekeeper.txt"),
    tools=[
        QUERY_BUILD_ASSIGNMENTS_SCHEMA, FIND_N4_SILO_FALLBACK_SCHEMA,
        WRITE_GOVERNANCE_TX_SCHEMA, ASSIGN_TECHNICIAN_SCHEMA,
        QUERY_STAFF_BY_SKILL_SCHEMA,
    ],
    max_tokens=2048,
)

AGENT_CONFIGS["AG-005"] = AgentConfig(
    agent_id="AG-005",
    agent_name="Estratega EDT/WBS",
    system_prompt=load_prompt("ag005_estratega.txt"),
    tools=[
        DECOMPOSE_PMBOK_SCHEMA, ASSIGN_SKILLS_TO_TASKS_SCHEMA,
        CREATE_BUILD_PROJECT_SCHEMA,
    ],
    max_tokens=8192,
)

AGENT_CONFIGS["AG-013"] = AgentConfig(
    agent_id="AG-013",
    agent_name="Task Decomposer",
    system_prompt=load_prompt("ag013_task_decomposer.txt"),
    tools=[
        DECOMPOSE_SUBTASKS_SCHEMA, QUERY_CMDB_ACTIVO_SCHEMA,
        QUERY_CMDB_SOFTWARE_SCHEMA, QUERY_CMDB_RELACIONES_SCHEMA,
    ],
    max_tokens=4096,
)

AGENT_CONFIGS["AG-014"] = AgentConfig(
    agent_id="AG-014",
    agent_name="Risk Analyzer",
    system_prompt=load_prompt("ag014_risk_analyzer.txt"),
    tools=[
        ANALYZE_RISKS_SCHEMA, QUERY_POSTMORTEM_PATTERNS_SCHEMA,
    ],
    max_tokens=2048,
)

AGENT_CONFIGS["AG-015"] = AgentConfig(
    agent_id="AG-015",
    agent_name="Stakeholder Map",
    system_prompt=load_prompt("ag015_stakeholder_map.txt"),
    tools=[
        MAP_STAKEHOLDERS_SCHEMA, QUERY_DIRECTORIO_SCHEMA,
    ],
    max_tokens=2048,
)

AGENT_CONFIGS["AG-006"] = AgentConfig(
    agent_id="AG-006",
    agent_name="Resource Manager PMO",
    system_prompt=load_prompt("ag006_resource_mgr_pmo.txt"),
    tools=[
        QUERY_PM_CANDIDATES_SCHEMA, QUERY_STAFF_BY_SKILL_SCHEMA,
        FORM_TEAM_SCHEMA, NOTIFY_GOVERNANCE_SCHEMA,
    ],
    max_tokens=2048,
)

AGENT_CONFIGS["AG-016"] = AgentConfig(
    agent_id="AG-016",
    agent_name="Cost Analyzer",
    system_prompt=load_prompt("ag016_cost_analyzer.txt"),
    tools=[
        CALC_ROI_SCHEMA, CALC_EVM_BASELINE_SCHEMA, CREATE_BUDGET_SCHEMA,
    ],
    max_tokens=8192,
)

AGENT_CONFIGS["AG-007"] = AgentConfig(
    agent_id="AG-007",
    agent_name="Planificador",
    system_prompt=load_prompt("ag007_planificador.txt"),
    tools=[
        CALC_CRITICAL_PATH_SCHEMA, GENERATE_GANTT_MERMAID_SCHEMA,
        CREATE_KANBAN_CARDS_SCHEMA, CREATE_BUILD_PROJECT_SCHEMA,
        CREATE_BUDGET_SCHEMA,
    ],
    max_tokens=8192,
)

AGENT_CONFIGS["AG-017"] = AgentConfig(
    agent_id="AG-017",
    agent_name="Quality Gate",
    system_prompt=load_prompt("ag017_quality_gate.txt"),
    tools=[
        DEFINE_QUALITY_GATES_SCHEMA, ENRICH_KANBAN_CARD_SCHEMA,
    ],
    max_tokens=2048,
)

AGENT_CONFIGS["AG-018"] = AgentConfig(
    agent_id="AG-018",
    agent_name="Governance Advisor",
    system_prompt=load_prompt("ag018_governance_advisor.txt"),
    tools=[
        QUERY_SIMILAR_PROJECTS_SCHEMA, QUERY_DIRECTORIO_SCHEMA,
        QUERY_CMDB_ACTIVO_SCHEMA, QUERY_POSTMORTEM_PATTERNS_SCHEMA,
        QUERY_STAFF_BY_SKILL_SCHEMA,
    ],
    max_tokens=1000,
)

AGENT_CONFIGS["AG-011"] = AgentConfig(
    agent_id="AG-011",
    agent_name="CAB Generator (Gabinete de Cambios)",
    system_prompt=load_prompt("ag011_director.txt"),
    tools=[
        QUERY_CALENDARIO_PERIODOS_SCHEMA, QUERY_DEMAND_HISTORY_SCHEMA,
        QUERY_CHANGE_WINDOWS_SCHEMA, QUERY_CAB_CONTEXTO_BUILD_SCHEMA,
        QUERY_CAB_CONTEXTO_RUN_SCHEMA, CREATE_CHANGE_PROPOSAL_SCHEMA,
        CREATE_CAB_ALERTS_SCHEMA,
    ],
    max_tokens=2048,
)

AGENT_CONFIGS["AG-012"] = AgentConfig(
    agent_id="AG-012",
    agent_name="Task Advisor",
    system_prompt=load_prompt("ag012_task_advisor.txt"),
    tools=[
        QUERY_CMDB_ACTIVO_SCHEMA, QUERY_CMDB_IPS_SCHEMA,
        QUERY_CMDB_RELACIONES_SCHEMA, QUERY_CMDB_SOFTWARE_SCHEMA,
        ENRICH_KANBAN_CARD_SCHEMA,
    ],
    max_tokens=1500,
)

AGENT_CONFIGS["AG-003"] = AgentConfig(
    agent_id="AG-003",
    agent_name="Demand Forecaster",
    system_prompt=load_prompt("ag003_demand_forecaster.txt"),
    tools=[RUN_PROPHET_SCHEMA, QUERY_CAPACITY_SCHEMA, STORE_FORECAST_SCHEMA],
    max_tokens=2048,
    temperature=0.2,
)

# =============================================
# BUILD PIPELINE v2.0 — Orden de ejecución
# =============================================

BUILD_PIPELINE_ORDER = [
    "AG-005",   # 1. Genera EDT/WBS
    # PAUSA 1: Gobernador revisa EDT + Acta + Alcance
    "AG-013",   # 2. Descompone en subtareas técnicas
    # PAUSA 2: Gobernador revisa subtareas
    "AG-014",   # 3a. Analiza riesgos (paralelo con AG-015)
    "AG-015",   # 3b. Mapea stakeholders (paralelo con AG-014)
    # PAUSA 3: Gobernador revisa riesgos + stakeholders
    "AG-006",   # 4. Propone PMs + forma equipo
    # PAUSA 4: Gobernador selecciona PM + revisa equipo
    "AG-016",   # 5a. Calcula presupuesto + ROI + EVM
    "AG-007",   # 5b. Genera Gantt + sprints + backlog
    "AG-017",   # 6. Define quality gates + DoD
    # RESULTADO: Proyecto listo para lanzar
]

BUILD_ADVISOR = "AG-018"  # Disponible durante las 4 pausas

# =============================================
# CONFIGURACIÓN DE SPAWNING (Director/Workers/Merger)
# =============================================
from agents.spawner import SPAWNABLE_AGENTS, merge_ag013_subtasks, merge_ag007_sprints

# AG-005: LLM merger (necesita generar Acta+Alcance+meta_negocio coherente)
SPAWNABLE_AGENTS["AG-005"] = {
    "director_prompt": load_prompt("ag005_director.txt"),
    "worker_prompt_template": load_prompt("ag005_worker.txt"),
    "merger_prompt": load_prompt("ag005_merger.txt"),
    "max_workers": 6,
    "worker_max_tokens": 4096,
}

# AG-013: merger LLM (los workers mezclan texto narrativo con JSON)
SPAWNABLE_AGENTS["AG-013"] = {
    "director_prompt": load_prompt("ag013_director.txt"),
    "worker_prompt_template": load_prompt("ag013_worker.txt"),
    "merger_prompt": load_prompt("ag013_merger.txt"),
    "max_workers": 6,
    "worker_max_tokens": 6144,
}

# AG-007: merge PROGRAMÁTICO (concatenar sprints + renumerar — sin llamar a Claude)
SPAWNABLE_AGENTS["AG-007"] = {
    "director_prompt": load_prompt("ag007_director.txt"),
    "worker_prompt_template": load_prompt("ag007_worker.txt"),
    "merger_prompt": "",
    "max_workers": 6,
    "worker_max_tokens": 3072,
    "programmatic_merge": True,
    "merge_function": merge_ag007_sprints,
}

# AG-011: CAB Generator — LLM merger (consolida propuestas de 6 workers)
SPAWNABLE_AGENTS["AG-011"] = {
    "director_prompt": load_prompt("ag011_director.txt"),
    "worker_prompt_template": load_prompt("ag011_worker.txt"),
    "merger_prompt": load_prompt("ag011_merger.txt"),
    "max_workers": 6,
    "worker_max_tokens": 2048,
}

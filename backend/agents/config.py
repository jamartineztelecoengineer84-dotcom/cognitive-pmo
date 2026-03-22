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
    agent_name="Estratega",
    system_prompt=load_prompt("ag005_estratega.txt"),
    tools=[
        DECOMPOSE_PMBOK_SCHEMA, ASSIGN_SKILLS_TO_TASKS_SCHEMA,
        CREATE_BUILD_PROJECT_SCHEMA,
    ],
    max_tokens=2048,
)

AGENT_CONFIGS["AG-006"] = AgentConfig(
    agent_id="AG-006",
    agent_name="Resource Manager PMO",
    system_prompt=load_prompt("ag006_resource_mgr_pmo.txt"),
    tools=[
        QUERY_STAFF_BY_SKILL_SCHEMA, FORM_TEAM_SCHEMA,
        NOTIFY_GOVERNANCE_SCHEMA,
    ],
    max_tokens=2048,
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

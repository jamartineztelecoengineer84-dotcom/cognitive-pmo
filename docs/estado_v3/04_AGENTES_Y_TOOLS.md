# 04 — Agentes IA y Tools

**Motor IA:** Claude (Anthropic API)  
**Modelo:** claude-sonnet-4-20250514  
**Total agentes:** 14  
**Total tools:** 35  
**Generado:** 2026-04-01

---

## 1. Agent Configs (config.py)

| Agent ID | Name | Tools | max_tokens | Spawning |
|----------|------|-------|-----------|----------|
| AG-001 | Dispatcher | query_catalogo, create_incident, create_tasks | 1500 | No |
| AG-002 | Resource Manager RUN | query_staff_by_skill, assign_technician, query_directorio | 1500 | No |
| AG-003 | Demand Forecaster | run_prophet, query_capacity, store_forecast | 2048 | No |
| AG-004 | Buffer Gatekeeper | query_build_assignments, find_n4_silo_fallback, write_governance_tx, assign_technician, query_staff_by_skill | 2048 | No |
| AG-005 | Estratega EDT/WBS | decompose_pmbok, assign_skills_to_tasks, create_build_project | 8192 | Yes (Director/6 Workers/LLM Merger) |
| AG-006 | Resource Manager PMO | query_pm_candidates, query_staff_by_skill, form_team, notify_governance | 2048 | No |
| AG-007 | Planificador | calc_critical_path, generate_gantt_mermaid, create_kanban_cards, create_build_project, create_budget | 8192 | Yes (Director/6 Workers/Programmatic Merger) |
| AG-012 | Task Advisor | query_cmdb_activo, query_cmdb_ips, query_cmdb_relaciones, query_cmdb_software, enrich_kanban_card | 1500 | No |
| AG-013 | Task Decomposer | decompose_subtasks, query_cmdb_activo, query_cmdb_software, query_cmdb_relaciones | 4096 | Yes (Director/6 Workers/LLM Merger) |
| AG-014 | Risk Analyzer | analyze_risks, query_postmortem_patterns | 2048 | No |
| AG-015 | Stakeholder Map | map_stakeholders, query_directorio | 2048 | No |
| AG-016 | Cost Analyzer | calc_roi, calc_evm_baseline, create_budget | 8192 | No |
| AG-017 | Quality Gate | define_quality_gates, enrich_kanban_card | 2048 | No |
| AG-018 | Governance Advisor | query_similar_projects, query_directorio, query_cmdb_activo, query_postmortem_patterns, query_staff_by_skill | 1000 | No |

---

## 2. Pipeline RUN (3 agentes secuenciales)

```
AG-001 (Dispatcher) → AG-002 (Resource Manager) → AG-004 (Buffer Gatekeeper)
```

---

## 3. Pipeline BUILD (9 agentes + 4 pausas de gobernanza)

```
AG-005 (Estratega EDT/WBS)
  → PAUSA 1: Gobernador revisa EDT + Acta + Alcance
AG-013 (Task Decomposer)
  → PAUSA 2: Gobernador revisa subtareas
AG-014 (Risk Analyzer) || AG-015 (Stakeholder Map)  [parallel]
  → PAUSA 3: Gobernador revisa riesgos + stakeholders
AG-006 (Resource Manager PMO)
  → PAUSA 4: Gobernador selecciona PM + revisa equipo
AG-016 (Cost Analyzer)
AG-007 (Planificador)
AG-017 (Quality Gate)
  → RESULTADO: Proyecto listo para lanzar
```

**BUILD_ADVISOR** = AG-018 (disponible durante las 4 pausas)

---

## 4. Spawning Configuration

| Agente | Merger | Descripcion |
|--------|--------|-------------|
| AG-005 | LLM merger | Director → up to 6 Workers → Claude Merger para Acta+Alcance+meta_negocio |
| AG-013 | LLM merger | Director → up to 6 Workers → Claude Merger para subtasks JSON |
| AG-007 | Programmatic merge | Director → up to 6 Workers → merge_ag007_sprints (concatenar sprints + renumerar) |

---

## 5. TOOL_REGISTRY (35 tools)

### 5.1 tools.py (30 tools)

| Tool | Descripcion |
|------|-------------|
| query_catalogo | Query catalogo_incidencias by keyword |
| create_incident | Insert into incidencias_run |
| create_tasks | Create kanban_tareas for an incident |
| query_staff_by_skill | Find technicians by skill match |
| assign_technician | Assign technician to incident/task |
| query_build_assignments | Check technician BUILD assignments |
| find_n4_silo_fallback | Find N4 backup technician |
| write_governance_tx | Write to gobernanza_transacciones |
| decompose_pmbok | Generate EDT/WBS from project description |
| assign_skills_to_tasks | Map skills to EDT tasks |
| create_build_project | Insert into cartera_build |
| form_team | Form project team from staff |
| notify_governance | Create governance notification |
| calc_critical_path | Calculate critical path from tasks |
| generate_gantt_mermaid | Generate Gantt in Mermaid format |
| create_kanban_cards | Create kanban cards from sprint items |
| run_prophet | Run demand forecast (Prophet-like) |
| query_capacity | Query team capacity metrics |
| store_forecast | Save forecast results |
| create_budget | Create/update presupuestos |
| query_directorio | Search directorio_corporativo |
| decompose_subtasks | Create build_subtasks from EDT tasks |
| analyze_risks | Generate build_risks matrix |
| query_postmortem_patterns | Search postmortem_reports for patterns |
| map_stakeholders | Create build_stakeholders from directorio |
| query_pm_candidates | Find available PMs |
| calc_roi | Calculate ROI/TIR/VAN |
| calc_evm_baseline | Calculate EVM baseline (BAC/PV) |
| define_quality_gates | Create build_quality_gates G0-G5 |
| query_similar_projects | Find similar past projects |

### 5.2 tools_cmdb.py (5 tools)

| Tool | Descripcion |
|------|-------------|
| query_cmdb_activo | Search cmdb_activos by keyword/category |
| query_cmdb_ips | Search cmdb_ips |
| query_cmdb_relaciones | Get asset relationships |
| query_cmdb_software | Search cmdb_software |
| enrich_kanban_card | Add technical context to kanban card |

---

## 6. Agent Prompts

| Archivo | Tamano | Rol |
|---------|--------|-----|
| ag001_dispatcher.txt | 3.5KB | "Eres AG-001 Dispatcher, el clasificador de incidencias..." |
| ag002_resource_mgr_run.txt | 2.7KB | "Eres AG-002 Resource Manager RUN..." |
| ag003_demand_forecaster.txt | 1.3KB | "Eres AG-003 Demand Forecaster..." |
| ag004_buffer_gatekeeper.txt | 1.4KB | "Eres AG-004 Buffer Gatekeeper, el arbitro entre RUN y BUILD..." |
| ag005_director.txt | 2.4KB | Director prompt for spawning |
| ag005_estratega.txt | 3.5KB | "Eres AG-005 Estratega PMO... MISION: estructura completa del proyecto" |
| ag005_merger.txt | 2.3KB | Merger prompt for EDT fusion |
| ag005_worker.txt | 1.8KB | Worker for one phase of EDT |
| ag006_resource_mgr_pmo.txt | 1.5KB | "Eres AG-006 Resource Manager PMO..." |
| ag007_director.txt | 1.7KB | Director for sprint planning |
| ag007_merger.txt | 2.4KB | Merger for sprint fusion |
| ag007_planificador.txt | 1.6KB | "Eres AG-007 Planificador... PROCESO CRITICO — PARALELIZACION" |
| ag007_worker.txt | 2.0KB | Worker for one sprint phase |
| ag012_task_advisor.txt | 3.7KB | "Eres AG-012 Task Advisor, genera instrucciones MASCADAS" |
| ag013_director.txt | 1.3KB | Director for task decomposition |
| ag013_merger.txt | 1.6KB | Merger for subtask JSON |
| ag013_task_decomposer.txt | 2.2KB | "Eres AG-013 Task Decomposer... 3-5 subtareas TECNICAS" |
| ag013_worker.txt | 2.0KB | Worker for one task batch |
| ag014_risk_analyzer.txt | 2.5KB | "Eres AG-014 Risk Analyzer... matriz de riesgos PMBOK" |
| ag015_stakeholder_map.txt | 2.0KB | "Eres AG-015 Stakeholder Map... directorio corporativo real" |
| ag016_cost_analyzer.txt | 2.3KB | "Eres AG-016 Cost Analyzer... presupuesto con equipo real" |
| ag017_quality_gate.txt | 1.5KB | "Eres AG-017 Quality Gate... gates G0-G5, DoD" |
| ag018_governance_advisor.txt | 1.3KB | "Eres AG-018 Governance Advisor... durante pausas" |

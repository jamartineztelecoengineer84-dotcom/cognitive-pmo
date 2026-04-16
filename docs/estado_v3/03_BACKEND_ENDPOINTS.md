# 03 --- Backend Endpoints

**Framework:** FastAPI (Python)  
**Puerto:** 8088  
**Total endpoints:** ~130  
**Generado:** 2026-04-01

---

## Resumen por dominio

| Fichero | Prefijo | Dominio | Endpoints |
|---------|---------|---------|-----------|
| `main.py` | `/` | Core PMO (cartera, kanban, incidencias, team, build, run, presupuestos, docs, dev) | 88 |
| `agents/router.py` | `/agents` | Agentes IA (invoke, pipelines RUN/BUILD, forecast) | 6 |
| `cmdb_api.py` | `/cmdb` | CMDB infraestructura (activos, VLANs, IPs, software, costes) | 22 |
| `rbac_api.py` | `/` | Auth, RBAC, directorio corporativo | 16 |
| **Total** | | | **~132** |

---

## 1. main.py --- Core PMO

### 1.1 Health

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/health` | Health check con estado de conexion DB | -- (SELECT 1) |

### 1.2 Cartera de Proyectos

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/cartera/proyectos` | Listar todos los proyectos ordenados por prioridad | `cartera_build` R |
| PUT | `/cartera/proyectos` | Actualizar nombre, prioridad, estado y horas de un proyecto | `cartera_build` W |
| POST | `/proyectos/crear` | Crear nuevo proyecto con ID auto-generado PRJ-xxx | `cartera_build` W |

### 1.3 Disponibilidad y Equipo

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/disponibilidad/global` | Tecnicos con estado DISPONIBLE | `pmo_staff_skills` R |
| GET | `/team/tecnicos` | Listar todos los tecnicos | `pmo_staff_skills` R |
| POST | `/team/tecnicos` | Crear tecnico nuevo | `pmo_staff_skills` W |
| PUT | `/team/tecnicos/{id_recurso}` | Actualizar datos de un tecnico | `pmo_staff_skills` W |
| POST | `/asignar/tecnico` | Cambiar estado y carga de un tecnico | `pmo_staff_skills` W |
| POST | `/asignar/tecnico/tarea` | Asignar tecnico a tarea kanban (actualiza carga y ticket) | `kanban_tareas` W, `pmo_staff_skills` W, `incidencias_run` W |

### 1.4 Kanban

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/kanban/tareas` | Listar tareas con JOIN a nombre de tecnico | `kanban_tareas` R, `pmo_staff_skills` R |
| POST | `/kanban/tareas` | Crear tarea con ID KT-YYYYMMDD-NNN y auto-fechas | `kanban_tareas` W |
| PUT | `/kanban/tareas/{task_id}` | Actualizar tarea completa (campos, historial columnas, fechas) | `kanban_tareas` W |
| PUT | `/kanban/tareas/{task_id}/mover` | Mover tarea a otra columna con auto-gestion de fechas | `kanban_tareas` W |
| DELETE | `/kanban/tareas/{task_id}` | Eliminar tarea y re-sincronizar estado tecnico | `kanban_tareas` W, `pmo_staff_skills` W |
| GET | `/kanban/metricas` | Metricas: throughput, lead/cycle time, CFD, flow efficiency | `kanban_tareas` R |
| POST | `/kanban/tareas/meta` | Merge metadata JSON en descripcion de tarea | `kanban_tareas` W |

### 1.5 Prediccion de Demanda

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/prediccion/demanda` | Forecast lineal simple (12 meses hist + 6 meses prediccion) | -- (calculo in-memory) |

### 1.6 Incidencias (ITSM)

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/catalogo/incidencias` | Catalogo maestro de tipos de incidencia | `catalogo_incidencias` R |
| GET | `/incidencias` | Listar incidencias RUN con filtro por estado | `incidencias_run` R |
| POST | `/incidencias` | Crear incidencia ITSM con ID INC-YYYY-xxxx | `incidencias_run` W |

### 1.7 Incidencias Live (Sidebar tiempo real)

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| POST | `/incidencias/live` | Crear incidencia live con SLA y fecha limite auto | `incidencias_live` W |
| GET | `/incidencias/live` | Listar incidencias live ordenadas por prioridad | `incidencias_live` R |
| DELETE | `/incidencias/live/{ticket_id}` | Eliminar/cerrar incidencia live | `incidencias_live` W |
| PUT | `/incidencias/live/{ticket_id}/progreso` | Actualizar progreso porcentual de incidencia live | `incidencias_live` W |

### 1.8 Directorio (busqueda rapida)

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/directorio/buscar` | Buscar contactos por area/cargo/bio (top 3) | `directorio_corporativo` R |

### 1.9 Buffer

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| POST | `/buffer/actualizar` | Pausar proyecto por riesgo P1 | `cartera_build` W |

### 1.10 PMO Governance

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/pmo/managers` | Listar project managers | `pmo_project_managers` R |
| POST | `/pmo/managers` | Crear project manager | `pmo_project_managers` W |
| PUT | `/pmo/managers/{id_pm}` | Actualizar project manager | `pmo_project_managers` W |
| GET | `/pmo/managers/candidates` | PMs disponibles con capacidad libre (top 5 por tasa exito) | `pmo_project_managers` R |
| GET | `/pmo/governance` | Scoring de gobernanza con JOIN a proyecto y PM | `pmo_governance_scoring` R, `cartera_build` R, `pmo_project_managers` R |
| GET | `/pmo/governance/dashboard` | Dashboard agregado: PMs, scoring medio, compliance, gates | `pmo_project_managers` R, `pmo_governance_scoring` R |

### 1.11 RUN Incident Plans

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/run/plans` | Listar planes de incidencia persistidos | `run_incident_plans` R |
| POST | `/run/plans` | Crear/actualizar plan de incidencia (upsert) | `run_incident_plans` W |
| DELETE | `/run/plans/{plan_id}` | Eliminar plan de incidencia | `run_incident_plans` W |

### 1.12 BUILD Project Plans

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/build/plans` | Listar planes de proyecto BUILD | `build_project_plans` R |
| POST | `/build/plans` | Crear/actualizar plan de proyecto (upsert) | `build_project_plans` W |
| GET | `/build/plans/{plan_id}` | Obtener plan individual | `build_project_plans` R |
| DELETE | `/build/plans/{plan_id}` | Eliminar plan de proyecto | `build_project_plans` W |

### 1.13 Pipeline Sessions

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| POST | `/pipeline/sessions` | Guardar/actualizar estado de sesion pipeline (upsert) | `pipeline_sessions` W |
| GET | `/pipeline/sessions` | Listar sesiones recientes (excl. LANZADO, top 20) | `pipeline_sessions` R |
| GET | `/pipeline/sessions/{sid}` | Obtener sesion pipeline completa | `pipeline_sessions` R |
| DELETE | `/pipeline/sessions/{sid}` | Eliminar sesion pipeline | `pipeline_sessions` W |
| POST | `/pipeline/sessions/{sid}/populate` | Parsear pipeline_data y poblar tablas BUILD individuales | `pipeline_sessions` R, `build_subtasks` W, `build_risks` W, `build_stakeholders` W, `build_sprints` W, `build_sprint_items` W, `build_quality_gates` W |

### 1.14 BUILD Pipeline v2.0 --- Subtasks

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/build/subtasks/{id_proyecto}` | Listar subtareas de un proyecto | `build_subtasks` R |
| POST | `/build/subtasks` | Crear subtareas en lote | `build_subtasks` W |
| DELETE | `/build/subtasks/{subtask_id}` | Eliminar subtarea | `build_subtasks` W |

### 1.15 BUILD Pipeline v2.0 --- Risks

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/build/risks/{id_proyecto}` | Listar riesgos de un proyecto (por score desc) | `build_risks` R |
| POST | `/build/risks` | Crear riesgos en lote | `build_risks` W |
| PUT | `/build/risks/{risk_id}` | Actualizar riesgo (campos dinamicos) | `build_risks` W |
| DELETE | `/build/risks/{risk_id}` | Eliminar riesgo | `build_risks` W |

### 1.16 BUILD Pipeline v2.0 --- Stakeholders

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/build/stakeholders/{id_proyecto}` | Listar stakeholders por poder/interes descendente | `build_stakeholders` R |
| POST | `/build/stakeholders` | Crear stakeholders en lote | `build_stakeholders` W |
| DELETE | `/build/stakeholders/{stakeholder_id}` | Eliminar stakeholder | `build_stakeholders` W |

### 1.17 BUILD Pipeline v2.0 --- Quality Gates

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/build/quality-gates/{id_proyecto}` | Listar quality gates de un proyecto | `build_quality_gates` R |
| POST | `/build/quality-gates` | Crear quality gates en lote | `build_quality_gates` W |
| PUT | `/build/quality-gates/{gate_id}` | Actualizar gate (estado, criterios, checklist, DoD) | `build_quality_gates` W |

### 1.18 BUILD Live (Sidebar proyectos activos)

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/build/live` | Listar proyectos BUILD activos | `build_live` R |
| POST | `/build/live` | Registrar proyecto en sidebar live | `build_live` W |
| PUT | `/build/live/{id_proyecto}/progreso` | Actualizar progreso, sprint actual, presupuesto, gate | `build_live` W |
| DELETE | `/build/live/{id_proyecto}` | Eliminar proyecto de sidebar live | `build_live` W |

### 1.19 BUILD Pipeline v2.0 --- Sprints (Scrum)

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/build/sprints/{id_proyecto}` | Listar sprints de un proyecto | `build_sprints` R |
| POST | `/build/sprints` | Crear sprints en lote | `build_sprints` W |
| PUT | `/build/sprints/{sprint_id}` | Actualizar sprint (estado, velocity, burndown, retro) | `build_sprints` W |

### 1.20 BUILD Pipeline v2.0 --- Sprint Items

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/build/sprint-items/{id_proyecto}` | Listar items de sprint (filtro opcional por sprint_number) | `build_sprint_items` R |
| POST | `/build/sprint-items` | Crear items de sprint en lote | `build_sprint_items` W |
| PUT | `/build/sprint-items/{item_id}` | Actualizar item (estado, tecnico, story points, bloqueador) | `build_sprint_items` W |
| DELETE | `/build/sprint-items/{item_id}` | Eliminar item de sprint | `build_sprint_items` W |

### 1.21 Advisor Chat (AG-018 Governance Advisor)

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| POST | `/build/advisor/chat` | Chat con agente AG-018 via Claude API (guarda historial) | `agent_conversations` W |
| GET | `/build/advisor/history/{session_id}` | Historial de conversacion del advisor por sesion | `agent_conversations` R |

### 1.22 Presupuestos

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/presupuestos` | Listar todos los presupuestos | `presupuestos` R |
| POST | `/presupuestos` | Crear presupuesto con calculo automatico de totales y BAC | `presupuestos` W |
| PUT | `/presupuestos/{id_presupuesto}` | Actualizar presupuesto completo con recalculo BAC | `presupuestos` W |
| DELETE | `/presupuestos/{id_presupuesto}` | Eliminar presupuesto | `presupuestos` W |

### 1.23 Documentacion Repositorio

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/documentacion` | Buscar documentos con filtros (tipo, silo, depto, texto) | `documentacion_repositorio` R |
| POST | `/documentacion` | Crear registro de documento con ruta Drive auto | `documentacion_repositorio` W |
| PUT | `/documentacion/{doc_id}` | Actualizar documento (incrementa version) | `documentacion_repositorio` W |
| DELETE | `/documentacion/{doc_id}` | Soft-delete de documento (activo=false) | `documentacion_repositorio` W |
| GET | `/documentacion/departamentos` | Lista estatica de silos y departamentos | -- (constante) |
| GET | `/documentacion/estructura` | Estructura de carpetas por silo | -- (constante) |
| GET | `/documentacion/stats` | Estadisticas: totales por silo, tipo y departamento | `documentacion_repositorio` R |

### 1.24 Dev Tools

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/dev/tables` | Listar todas las tablas con tamano y row count | `information_schema` R, `pg_stat_user_tables` R |
| GET | `/dev/tables/{table_name}/schema` | Schema de tabla: columnas, constraints, indices | `information_schema` R, `pg_constraint` R, `pg_indexes` R |
| GET | `/dev/tables/{table_name}/data` | Leer datos de cualquier tabla (paginado) | `{table_name}` R |
| POST | `/dev/sql` | Ejecutar SQL arbitrario (SELECT o DML) | -- (cualquier tabla) |
| GET | `/dev/files` | Listar ficheros del backend con tamano y lineas | -- (filesystem) |
| GET | `/dev/files/{file_path:path}` | Leer contenido de fichero del backend | -- (filesystem) |
| GET | `/dev/context` | Generar contexto tecnico completo (tablas + endpoints + stack) | `information_schema` R |

---

## 2. agents/router.py --- Agentes IA (prefijo `/agents`)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/agents/` | Listar todos los agentes configurados (id, nombre, modelo, tools) |
| POST | `/agents/{agent_id}/invoke` | Invocar agente individual (con spawning si configurado) |
| POST | `/agents/run/chain` | Pipeline RUN completo: AG-001 Dispatcher -> AG-002 Resource Manager -> AG-004 Buffer (si necesario). Retorna incidencia y tareas reales de BD |
| GET | `/agents/run/chain/stream` | SSE stream del pipeline RUN con eventos en tiempo real (agent_start, tool_call, task_created, technician_assigned, sla_started, chain_complete) |
| POST | `/agents/build/chain` | Pipeline BUILD completo: AG-005 Estratega -> AG-006 Resource Manager PMO (con ciclo si gap) -> AG-007 Planificador. Retorna plan estructurado |
| POST | `/agents/forecast/run` | Ejecutar AG-003 Demand Forecaster manualmente (prediccion trimestral por silo) |

---

## 3. cmdb_api.py --- CMDB Infraestructura (prefijo `/cmdb`)

### 3.1 Dashboard

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/cmdb/dashboard` | Dashboard agregado: totales, por capa/estado/criticidad, costes | `cmdb_activos` R, `cmdb_vlans` R, `cmdb_ips` R, `cmdb_software` R, `cmdb_relaciones` R |

### 3.2 Activos (CIs)

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/cmdb/activos` | Listar activos con filtros (capa, tipo, criticidad, entorno, search) | `cmdb_activos` R, `cmdb_categorias` R |
| GET | `/cmdb/activos/{id_activo}` | Detalle de activo con dependencias, IPs y software instalado | `cmdb_activos` R, `cmdb_relaciones` R, `cmdb_ips` R, `cmdb_software` R |
| POST | `/cmdb/activos` | Crear activo CI | `cmdb_activos` W |
| PUT | `/cmdb/activos/{id_activo}` | Actualizar activo (campos dinamicos) | `cmdb_activos` W |

### 3.3 Categorias

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/cmdb/categorias` | Listar categorias de activos | `cmdb_categorias` R |

### 3.4 Relaciones / Dependencias

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/cmdb/relaciones` | Listar relaciones entre activos con nombres | `cmdb_relaciones` R, `cmdb_activos` R |
| POST | `/cmdb/relaciones` | Crear relacion entre dos activos | `cmdb_relaciones` W |

### 3.5 VLANs

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/cmdb/vlans` | Listar VLANs con conteo de IPs asignadas | `cmdb_vlans` R, `cmdb_ips` R |
| POST | `/cmdb/vlans` | Crear VLAN | `cmdb_vlans` W |
| PUT | `/cmdb/vlans/{id_vlan}` | Actualizar VLAN | `cmdb_vlans` W |
| DELETE | `/cmdb/vlans/{id_vlan}` | Eliminar VLAN | `cmdb_vlans` W |

### 3.6 IPs

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/cmdb/ips` | Listar IPs con filtros (vlan, estado, search) y JOIN a activo | `cmdb_ips` R, `cmdb_vlans` R, `cmdb_activos` R |
| POST | `/cmdb/ips` | Crear registro IP | `cmdb_ips` W |
| PUT | `/cmdb/ips/{id_ip}` | Actualizar IP | `cmdb_ips` W |
| DELETE | `/cmdb/ips/{id_ip}` | Eliminar IP | `cmdb_ips` W |

### 3.7 Software

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/cmdb/software` | Listar software ordenado por critico_negocio | `cmdb_software` R |

### 3.8 Mapa de Impacto

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/cmdb/impacto/{id_activo}` | Analisis de impacto en cascada (BFS recursivo, max 5 niveles) | `cmdb_relaciones` R, `cmdb_activos` R |

### 3.9 Compliance

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/cmdb/compliance` | Health check: SW obsoleto, activos sin responsable, degradados, certs | `cmdb_software` R, `cmdb_activos` R |

### 3.10 Costes

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/cmdb/costes` | Listar costes con filtros (categoria, tipo, activo, proyecto) | `cmdb_costes` R, `cmdb_activos` R |
| POST | `/cmdb/costes` | Crear registro de coste | `cmdb_costes` W |
| PUT | `/cmdb/costes/{id_coste}` | Actualizar coste | `cmdb_costes` W |
| DELETE | `/cmdb/costes/{id_coste}` | Eliminar coste | `cmdb_costes` W |
| GET | `/cmdb/costes/dashboard` | Dashboard de costes: CAPEX/OPEX, por categoria, por proyecto | `cmdb_costes` R |

---

## 4. rbac_api.py --- Auth, RBAC y Directorio

### 4.1 Autenticacion

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| POST | `/auth/login` | Login con email/password, devuelve JWT + permisos | `rbac_usuarios` R, `rbac_sesiones` W, `rbac_audit_log` W |
| GET | `/auth/me` | Obtener usuario autenticado actual | -- (desde JWT) |
| POST | `/auth/logout` | Invalidar sesion activa | `rbac_sesiones` W, `rbac_audit_log` W |
| POST | `/auth/cambiar-password` | Cambiar contrasena propia (requiere actual) | `rbac_usuarios` W |

### 4.2 Roles

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/rbac/roles` | Listar roles con conteo de permisos y usuarios | `rbac_roles` R, `rbac_role_permisos` R, `rbac_usuarios` R |
| GET | `/rbac/roles/{role_id}/permisos` | Permisos asignados a un rol | `rbac_role_permisos` R, `rbac_permisos` R |
| POST | `/rbac/roles` | Crear rol | `rbac_roles` W |
| PUT | `/rbac/roles/{role_id}` | Actualizar rol (nombre, nivel, color, activo) | `rbac_roles` W |
| PUT | `/rbac/roles/{role_id}/permisos` | Reemplazar permisos de un rol (delete + insert batch) | `rbac_role_permisos` W, `rbac_audit_log` W |
| DELETE | `/rbac/roles/{role_id}` | Eliminar rol (solo si no tiene usuarios activos) | `rbac_roles` W |

### 4.3 Permisos

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/rbac/permisos` | Listar todos los permisos del sistema | `rbac_permisos` R |

### 4.4 Usuarios

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/rbac/usuarios` | Listar usuarios con filtros (rol, depto, search, activo) | `rbac_usuarios` R, `rbac_roles` R |
| POST | `/rbac/usuarios` | Crear usuario con rol y password hasheado | `rbac_usuarios` W |
| PUT | `/rbac/usuarios/{user_id}` | Actualizar usuario (nombre, rol, depto, cargo, activo) | `rbac_usuarios` W |
| POST | `/rbac/usuarios/{user_id}/reset-password` | Reset password a "12345" con flag requiere_cambio | `rbac_usuarios` W |

### 4.5 Audit Log

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/rbac/audit` | Consultar log de auditoria con filtros (accion, email, resultado) | `rbac_audit_log` R |

### 4.6 Directorio Corporativo

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/directorio` | Listar directivos con filtros (nivel, area) y jerarquia | `directorio_corporativo` R |
| GET | `/directorio/organigrama` | Arbol jerarquico del organigrama completo | `directorio_corporativo` R |
| GET | `/directorio/stats` | Estadisticas: por nivel, area, ubicacion | `directorio_corporativo` R |

### 4.7 RBAC Dashboard

| Metodo | Ruta | Descripcion | Tabla(s) |
|--------|------|-------------|----------|
| GET | `/rbac/dashboard` | Dashboard agregado: usuarios, roles, permisos, logins recientes | `rbac_usuarios` R, `rbac_roles` R, `rbac_permisos` R, `rbac_audit_log` R |

---

## Tablas referenciadas (resumen)

| Tabla | Dominio | Accedida desde |
|-------|---------|----------------|
| `cartera_build` | Cartera proyectos | main.py |
| `pmo_staff_skills` | Equipo tecnico | main.py |
| `kanban_tareas` | Tablero kanban | main.py, agents/router.py |
| `catalogo_incidencias` | Catalogo ITSM | main.py |
| `incidencias_run` | Incidencias RUN | main.py, agents/router.py |
| `incidencias_live` | Incidencias en tiempo real | main.py |
| `directorio_corporativo` | Organigrama | main.py, rbac_api.py |
| `pmo_project_managers` | Project managers | main.py |
| `pmo_governance_scoring` | Scoring gobernanza | main.py |
| `run_incident_plans` | Planes incidencia RUN | main.py |
| `build_project_plans` | Planes proyecto BUILD | main.py, agents/router.py |
| `pipeline_sessions` | Estado pipelines | main.py |
| `build_subtasks` | Subtareas BUILD | main.py |
| `build_risks` | Riesgos BUILD | main.py |
| `build_stakeholders` | Stakeholders BUILD | main.py |
| `build_quality_gates` | Quality gates BUILD | main.py |
| `build_live` | Proyectos BUILD activos | main.py |
| `build_sprints` | Sprints Scrum | main.py |
| `build_sprint_items` | Items de sprint | main.py |
| `agent_conversations` | Historial advisor IA | main.py |
| `presupuestos` | Presupuestos proyecto | main.py |
| `documentacion_repositorio` | Repositorio docs | main.py |
| `cmdb_activos` | Activos CI | cmdb_api.py |
| `cmdb_categorias` | Categorias CMDB | cmdb_api.py |
| `cmdb_relaciones` | Dependencias CI | cmdb_api.py |
| `cmdb_vlans` | VLANs red | cmdb_api.py |
| `cmdb_ips` | Direcciones IP | cmdb_api.py |
| `cmdb_software` | Inventario software | cmdb_api.py |
| `cmdb_costes` | Costes infra | cmdb_api.py |
| `rbac_usuarios` | Usuarios sistema | rbac_api.py |
| `rbac_roles` | Roles RBAC | rbac_api.py |
| `rbac_permisos` | Permisos RBAC | rbac_api.py |
| `rbac_role_permisos` | Asignacion rol-permiso | rbac_api.py |
| `rbac_sesiones` | Sesiones activas | rbac_api.py |
| `rbac_audit_log` | Log auditoria | rbac_api.py |

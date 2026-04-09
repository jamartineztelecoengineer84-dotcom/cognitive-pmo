# ARQ-03 F0 — Recon e inventario para reparto de tablas (5 mundos)

**Fecha**: 2026-04-09
**Commit actual**: `3ae2012da28dcf53eecfd42348c4754405519687`
**Tag previo más reciente**: `F-ARQ02-20-done`
**Modo**: SOLO LECTURA. No se ha modificado nada en BD ni en código. Único artefacto generado: este documento.

---

## 1) Inventario de tablas en `public` (Tarea 1)

**Total: 69 tablas** (orden por tamaño DESC)

```
            tabla            |   tamano   | filas_estimadas | comentario
-----------------------------+------------+-----------------+----------
 agent_conversations         | 4848 kB    |            1648 |
 catalogo_incidencias        | 3872 kB    |            7259 |
 cmdb_demand_history         | 2104 kB    |            2376 |
 kanban_tareas               | 1200 kB    |             332 |
 pmo_staff_skills            | 776 kB     |             150 |
 build_project_plans         | 368 kB     |              46 |
 pipeline_sessions           | 336 kB     |               8 |
 cmdb_activos                | 328 kB     |             226 |
 rbac_sesiones               | 328 kB     |             642 |
 directorio_corporativo      | 272 kB     |             479 |
 rbac_usuarios               | 256 kB     |             181 |
 rbac_audit_log              | 224 kB     |             647 |
 incidencias_run             | 176 kB     |              34 |
 build_risks                 | 176 kB     |             154 |
 documentacion_repositorio   | 168 kB     |              -1 |
 presupuestos                | 144 kB     |              50 |
 build_stakeholders          | 144 kB     |             210 |
 build_sprint_items          | 144 kB     |             174 |
 intelligent_alerts          | 136 kB     |              -1 |
 cmdb_change_windows         | 128 kB     |              -1 |
 build_subtasks              | 128 kB     |             160 |
 gobernanza_transacciones    | 128 kB     |              -1 |
 cartera_build               | 128 kB     |              46 | Universo backlog histórico escrito por agentes IA. id_proyecto ~ ^PRJ0[0-9]{3}$. NO TOCAR desde scenario engine.
 rbac_role_permisos          | 128 kB     |             883 |
 pmo_governance_scoring      | 120 kB     |              -1 |
 agent_performance_metrics   | 120 kB     |             220 |
 compliance_audits           | 112 kB     |              -1 |
 itsm_form_drafts            | 104 kB     |              61 |
 cmdb_ips                    | 104 kB     |             111 |
 cmdb_change_proposals       | 96 kB      |              -1 |
 build_live                  | 96 kB      |              60 | Universo LIVE operativo. id_proyecto ~ ^PRJ-[A-Z]{3}[0-9]+$. Scenario engine SOLO con prefijos PRJ-SCA/SCB/SCC/SCD.
 pmo_project_managers        | 96 kB      |              25 |
 tech_chat_mensajes          | 88 kB      |             101 |
 calendario_periodos_demanda | 80 kB      |              -1 |
 rbac_permisos               | 80 kB      |              75 |
 postmortem_reports          | 80 kB      |              -1 |
 catalogo_skills             | 80 kB      |             100 |
 build_quality_gates         | 72 kB      |              54 |
 tech_valoracion_mensual     | 72 kB      |             110 |
 incidencias_live            | 64 kB      |               2 |
 build_sprints               | 64 kB      |              51 |
 war_room_sessions           | 64 kB      |              -1 |
 whatif_simulations          | 64 kB      |              -1 |
 tech_terminal_log           | 64 kB      |              -1 |
 tech_notificaciones         | 64 kB      |              -1 |
 cmdb_relaciones             | 56 kB      |              55 |
 rbac_roles                  | 48 kB      |              -1 |
 cmdb_vlans                  | 48 kB      |              -1 |
 cmdb_categorias             | 40 kB      |              -1 |
 cmdb_change_approvals       | 40 kB      |              -1 |
 tech_chat_salas             | 40 kB      |              19 |
 p96_pulse_hitos             | 32 kB      |              -1 |
 cmdb_costes                 | 32 kB      |              -1 |
 tech_adjuntos               | 32 kB      |              -1 |
 p96_pulse_blocks            | 32 kB      |              -1 |
 p96_pulse_decisions         | 32 kB      |              -1 |
 p96_pulse_responsables      | 32 kB      |              -1 |
 p96_strategy_frameworks     | 32 kB      |              -1 |
 p96_governors               | 32 kB      |              -1 |
 p96_run_layers              | 32 kB      |              -1 |
 p96_run_matrix              | 32 kB      |              -1 |
 p96_run_crits               | 32 kB      |              -1 |
 p96_build_project_detail    | 32 kB      |              -1 |
 p96_pulse_kpis              | 32 kB      |              -1 |
 p96_pulse_alerts            | 32 kB      |              -1 |
 kanban_wip_limits           | 24 kB      |              -1 |
 cmdb_software               | 24 kB      |              -1 |
 cmdb_cambios                | 16 kB      |              -1 |
 cmdb_activo_software        | 8192 bytes |              -1 |
```

> Las filas con `-1` son tablas sin estadísticas vacías o nunca analizadas (`ANALYZE` no se ha corrido). El campo `comentario` solo está poblado en `build_live` y `cartera_build` con guards documentados.

---

## 2) Grafo de FKs en `public` (Tarea 2)

**Total: 30 FKs**, agrupado por `tabla_origen`:

```
       tabla_origen       |      col_origen      |     tabla_destino      | col_destino  | on_delete
--------------------------+----------------------+------------------------+--------------+-----------
 build_live               | id_pm_usuario        | rbac_usuarios          | id_usuario   | a (NO ACTION)
 cartera_build            | responsable_asignado | pmo_staff_skills       | id_recurso   | a
 cmdb_activo_software     | id_activo            | cmdb_activos           | id_activo    | c (CASCADE)
 cmdb_activo_software     | id_software          | cmdb_software          | id_software  | c
 cmdb_activos             | id_categoria         | cmdb_categorias        | id_categoria | a
 cmdb_cambios             | id_activo            | cmdb_activos           | id_activo    | a
 cmdb_change_approvals    | id_propuesta         | cmdb_change_proposals  | id           | a
 cmdb_costes              | id_activo            | cmdb_activos           | id_activo    | a
 cmdb_ips                 | id_activo            | cmdb_activos           | id_activo    | a
 cmdb_ips                 | id_vlan              | cmdb_vlans             | id_vlan      | a
 cmdb_relaciones          | id_activo_destino    | cmdb_activos           | id_activo    | c
 cmdb_relaciones          | id_activo_origen     | cmdb_activos           | id_activo    | c
 directorio_corporativo   | reporta_a            | directorio_corporativo | id_directivo | a (self-FK)
 gobernanza_transacciones | fte_afectado         | pmo_staff_skills       | id_recurso   | a
 gobernanza_transacciones | id_proyecto          | cartera_build          | id_proyecto  | a
 incidencias_live         | ticket_id            | incidencias_run        | ticket_id    | c
 incidencias_run          | id_catalogo          | catalogo_incidencias   | id_catalogo  | a
 incidencias_run          | tecnico_asignado     | pmo_staff_skills       | id_recurso   | a
 kanban_tareas            | id_incidencia        | incidencias_run        | ticket_id    | c (D.1 F-ARQ02-18)
 kanban_tareas            | id_tecnico           | pmo_staff_skills       | id_recurso   | a
 p96_run_matrix           | crit                 | p96_run_crits          | k            | a
 p96_run_matrix           | layer                | p96_run_layers         | k            | a
 pmo_governance_scoring   | id_pm                | pmo_project_managers   | id_pm        | a
 pmo_project_managers     | id_usuario_rbac      | rbac_usuarios          | id_usuario   | a
 rbac_role_permisos       | id_permiso           | rbac_permisos          | id_permiso   | c
 rbac_role_permisos       | id_role              | rbac_roles             | id_role      | c
 rbac_sesiones            | id_usuario           | rbac_usuarios          | id_usuario   | c
 rbac_usuarios            | id_role              | rbac_roles             | id_role      | a
 tech_chat_mensajes       | id_sala              | tech_chat_salas        | id           | c
 tech_notificaciones      | id_usuario           | rbac_usuarios          | id_usuario   | a
```

---

## 3) Grep `public.` en código (Tarea 3a)

**Total: 6 coincidencias**, todas en `to_regclass()` para guards de migración (NO son referencias hardcoded a esquema, son introspección):

```
database/arq02_fase4_rename_itsm_form_drafts.sql:26:  IF to_regclass('public.run_incident_plans') IS NULL THEN
database/arq02_fase4_rename_itsm_form_drafts.sql:29:  IF to_regclass('public.itsm_form_drafts') IS NOT NULL THEN
database/arq02_fase3_drop_zombie_incidencias.sql:23:  IF to_regclass('public.incidencias') IS NOT NULL THEN
backend/tests/test_arq02_f3_drop_zombie.py:26:            return await c.fetchval("SELECT to_regclass('public.incidencias')")
backend/tests/test_arq02_f4_itsm_drafts.py:43:            old = await c.fetchval("SELECT to_regclass('public.run_incident_plans')")
backend/tests/test_arq02_f4_itsm_drafts.py:44:            new = await c.fetchval("SELECT to_regclass('public.itsm_form_drafts')")
```

**Análisis**: las 6 son guards seguros. Las 3 SQL son migraciones cerradas (F3/F4) que ya no se reejecutan. Las 3 Python son tests que verifican que las migraciones cerraron correctamente. **Ninguna afecta al refactor ARQ-03**: si el search_path está bien configurado, los 6 sites siguen funcionando porque `to_regclass` resuelve absoluto si se le da el namespace.

## 3) Grep `search_path` en código (Tarea 3b)

**Total: 0 coincidencias**.

```
(vacío)
```

**Análisis**: nadie en el código fija `search_path` explícitamente. Postgres usa el default (`"$user", public`), por lo que toda query asume implícitamente que las tablas están en `public`. **Esto es la principal restricción para ARQ-03**: cualquier movimiento de tablas a esquemas distintos requerirá o bien:
- (a) `SET search_path` por sesión/conexión
- (b) Cualificar todas las queries con `schema.tabla`
- (c) Crear vistas en `public` que apunten a los esquemas reales (estrategia menos invasiva)

---

## 4) Clasificación final por tabla (Tarea 4)

**Convenciones**:
- **A** = compartido (1 sola copia, sirve a primitiva + 4 bancos)
- **B** = duplicado por escenario (5 copias, una por mundo)
- **C** = dudoso (revisar antes de migrar)

| # | tabla | caja | razón |
|---|---|---|---|
| 1 | agent_conversations | **B** | logs operativos del banco — cada banco tiene sus conversaciones |
| 2 | agent_performance_metrics | **B** | métricas runtime de los agentes ejecutando para ese banco |
| 3 | build_live | **B** | proyectos del banco |
| 4 | build_project_plans | **B** | drafts ITSM del banco |
| 5 | build_quality_gates | **B** | gates por proyecto del banco |
| 6 | build_risks | **B** | riesgos por proyecto del banco |
| 7 | build_sprint_items | **B** | items de sprint del banco |
| 8 | build_sprints | **B** | sprints del banco |
| 9 | build_stakeholders | **B** | stakeholders del banco |
| 10 | build_subtasks | **B** | subtasks técnicas del banco |
| 11 | calendario_periodos_demanda | **C** | 5 períodos master (Q4, comercio elec...). Propuesta: **A**. Razón: el calendario fiscal/comercial español es universal; los 4 bancos comparten ventanas de alta demanda. Si un banco tuviera periodos propios, se promociona a B. |
| 12 | cartera_build | **B** | backlog histórico del banco (FK a pmo_staff_skills será cross-caja) |
| 13 | catalogo_incidencias | **A** | master 7259 entradas — knowledge base universal de tipos de incidencia bancaria, no cambia entre bancos |
| 14 | catalogo_skills | **A** | master 100 skills — taxonomía universal |
| 15 | cmdb_activo_software | **B** | software instalado en CIs del banco |
| 16 | cmdb_activos | **B** | inventario CMDB del banco |
| 17 | cmdb_cambios | **B** | historial cambios CIs del banco |
| 18 | cmdb_categorias | **A** | master 32 categorías (Servidor, BBDD, Firewall...) — taxonomía universal |
| 19 | cmdb_change_approvals | **B** | aprobaciones CAB del banco |
| 20 | cmdb_change_proposals | **B** | propuestas CAB generadas por AG-011 para el banco |
| 21 | cmdb_change_windows | **C** | 40 ventanas master, pero TIENE columna `id_activo` que es FK lógica a cmdb_activos (B). Propuesta: **B**. Razón estructural: las ventanas se definen POR activo del banco, no son universales. Aunque el seed actual aparezca como "master", su semántica es por-banco. |
| 22 | cmdb_costes | **B** | costes CIs del banco |
| 23 | cmdb_demand_history | **B** | histórico Prophet del banco (input forecast) |
| 24 | cmdb_ips | **B** | direccionamiento IP del banco |
| 25 | cmdb_relaciones | **B** | grafo de dependencias CIs del banco |
| 26 | cmdb_software | **B** | catálogo software instalado del banco |
| 27 | cmdb_vlans | **B** | VLANs del banco |
| 28 | compliance_audits | **B** | auditorías compliance del banco |
| 29 | directorio_corporativo | **B** | 479 directivos del banco — cada banco tiene SU organigrama; self-FK `reporta_a` se queda dentro de B |
| 30 | documentacion_repositorio | **A** | docs del producto Cognitive PMO (master, no por banco) |
| 31 | gobernanza_transacciones | **B** | log transacciones gobernanza del banco |
| 32 | incidencias_live | **B** | vista operativa incidentes del banco |
| 33 | incidencias_run | **B** | cola RUN incidentes del banco |
| 34 | intelligent_alerts | **B** | alertas correladas del banco (AG-012) |
| 35 | itsm_form_drafts | **B** | drafts ITSM del banco |
| 36 | kanban_tareas | **B** | tareas operativas del banco (RUN+BUILD) |
| 37 | kanban_wip_limits | **C** | configuración límites WIP. Propuesta: **A**. Razón: son límites del modelo Kanban universal (Backlog max 50, En Progreso max 8...), no específicos por banco. Si un banco quiere overrides, se promociona a B. |
| 38 | p96_build_project_detail | **B** | vista materializada por proyecto del banco |
| 39 | p96_governors | **A** | configuración del modelo P96 (governors universales) |
| 40 | p96_pulse_alerts | **B** | alertas Pulse del banco |
| 41 | p96_pulse_blocks | **B** | bloques Pulse del banco |
| 42 | p96_pulse_decisions | **B** | decisiones Pulse del banco |
| 43 | p96_pulse_hitos | **B** | hitos Pulse del banco |
| 44 | p96_pulse_kpis | **B** | KPIs Pulse del banco |
| 45 | p96_pulse_responsables | **B** | responsables Pulse del banco |
| 46 | p96_run_crits | **A** | matriz criticidad universal (3 niveles del modelo P96) |
| 47 | p96_run_layers | **A** | capas universales del modelo P96 |
| 48 | p96_run_matrix | **A** | matriz cruzada (FKs internas a A) |
| 49 | p96_strategy_frameworks | **A** | frameworks estratégicos master (SAFe, PMBOK, etc.) |
| 50 | pipeline_sessions | **C** | 8 sesiones del pipeline RUN/BUILD del operador. Propuesta: **A**. Razón: son sesiones del operador del Cognitive PMO (no del banco final), por tanto compartidas. Si cada banco quisiera trazabilidad propia se promociona a B. |
| 51 | pmo_governance_scoring | **B** | scoring por proyecto del banco (FK a pmo_project_managers cross-caja) |
| 52 | pmo_project_managers | **A** | 25 PMs pool único compartido entre bancos |
| 53 | pmo_staff_skills | **A** | 150 técnicos pool único compartido entre bancos |
| 54 | postmortem_reports | **B** | post-mortems del banco (AG-009) |
| 55 | presupuestos | **B** | presupuestos del banco (CAPEX/OPEX/RRHH) |
| 56 | rbac_audit_log | **A** | log auditoría del operador (1 sola copia para todo el sistema) |
| 57 | rbac_permisos | **A** | catálogo permisos universal |
| 58 | rbac_role_permisos | **A** | mapping role↔permiso universal |
| 59 | rbac_roles | **A** | 23 roles del operador |
| 60 | rbac_sesiones | **A** | sesiones de login del operador |
| 61 | rbac_usuarios | **A** | 181 usuarios pool único del operador |
| 62 | tech_adjuntos | **B** | adjuntos técnicos del banco |
| 63 | tech_chat_mensajes | **B** | mensajes chat técnico del banco |
| 64 | tech_chat_salas | **B** | salas chat técnico del banco |
| 65 | tech_notificaciones | **B** | notificaciones técnicas del banco (FK rbac_usuarios cross-caja) |
| 66 | tech_terminal_log | **B** | logs terminal técnico del banco |
| 67 | tech_valoracion_mensual | **B** | valoraciones mensuales del banco |
| 68 | war_room_sessions | **B** | sesiones war room del banco |
| 69 | whatif_simulations | **B** | simulaciones what-if del banco (AG-010) |

**Totales**:
- **Caja A (compartido)**: **17 tablas**
- **Caja B (por escenario)**: **48 tablas**
- **Caja C (dudosas)**: **4 tablas**

---

## 5) Tablas en Caja C — propuesta razonada

### C-1 — `calendario_periodos_demanda` → propuesta **A**
- **5 filas** con períodos tipo `PERIODO_ALTA_DEMANDA_Q4`, `PICO_COMERCIO_ELECTRONICO`, etc.
- Estos períodos son del **calendario fiscal/comercial español**, universales para los 4 bancos
- Las fechas Q4, picos navideños, mantenimientos verano son cross-banco
- Si un banco específico quisiera períodos personalizados (ej. campaña marketing propia), entonces promocionar a B
- **Sin FK saliente, sin FK entrante** → migración a A trivial

### C-2 — `cmdb_change_windows` → propuesta **B**
- **40 ventanas master**, pero contiene `id_activo integer NOT NULL` (FK lógica, sin enforcement) a `cmdb_activos`
- Si `cmdb_activos` se duplica por banco (B), las ventanas TAMBIÉN se duplican porque cada activo del banco tiene su ventana
- El seed actual parece "master" pero estructuralmente es por-activo
- **Si se queda en A, hay que romper la columna `id_activo`** (lo cual destruye la semántica)
- Mejor mover a B y mantener la integridad referencial intra-caja

### C-3 — `kanban_wip_limits` → propuesta **A**
- Tabla pequeña (24 KB, sin filas estimadas — probablemente 0-10 filas)
- Configuración del modelo Kanban universal (límite por columna)
- No tiene FK ni dependencias visibles
- Defaults compartidos para los 4 bancos. Si un banco quiere override → promocionar a B con un fallback a A

### C-4 — `pipeline_sessions` → propuesta **A**
- 8 filas (336 KB grandes — probablemente cada fila tiene mucho jsonb de estado)
- Sesiones del **operador** del Cognitive PMO (no del cliente bancario final)
- Trazan ejecuciones de pipelines RUN/BUILD del propio sistema
- Si cada banco quisiera su histórico de sesiones, se promociona a B
- Por defecto, **una sola copia compartida** para el operador del producto

---

## 6) Alertas FK cross-cajas (Tarea 8)

> Una FK `B → B` o `A → A` no es problema (la integridad se mantiene dentro del esquema). Una FK `B → A` requiere decisión: el origen B vivirá en N copias (1 por banco) pero todas apuntarán a la misma fila destino A. Esto es **funcional sólo si**:
> 1. El esquema A está accesible desde el esquema B (search_path o cualificación), Y
> 2. Las constraints FK pueden cruzar esquemas en Postgres (sí lo permiten)
>
> Una FK `A → B` sería **problema mayor**: una fila en el esquema compartido apuntando a una fila en un esquema específico de banco. Esto rompería la independencia entre mundos.

### 6.1 — FKs `B → A` (8 alertas — funcionales pero requieren decisión)

| # | origen (B) | destino (A) | columna | on_delete | impacto |
|---|---|---|---|---|---|
| 1 | `cartera_build.responsable_asignado` | `pmo_staff_skills.id_recurso` | id_recurso | NO ACTION | OK — los 150 técnicos son pool compartido |
| 2 | `incidencias_run.id_catalogo` | `catalogo_incidencias.id_catalogo` | id_catalogo | NO ACTION | OK — catálogo 7259 entradas master |
| 3 | `incidencias_run.tecnico_asignado` | `pmo_staff_skills.id_recurso` | id_recurso | NO ACTION | OK — técnicos compartidos |
| 4 | `gobernanza_transacciones.fte_afectado` | `pmo_staff_skills.id_recurso` | id_recurso | NO ACTION | OK — técnicos compartidos |
| 5 | `kanban_tareas.id_tecnico` | `pmo_staff_skills.id_recurso` | id_recurso | NO ACTION | OK — técnicos compartidos |
| 6 | `pmo_governance_scoring.id_pm` | `pmo_project_managers.id_pm` | id_pm | NO ACTION | OK — 25 PMs compartidos |
| 7 | `cmdb_activos.id_categoria` | `cmdb_categorias.id_categoria` | id_categoria | NO ACTION | OK — categorías master 32 entradas |
| 8 | `build_live.id_pm_usuario` | `rbac_usuarios.id_usuario` | id_usuario | NO ACTION | OK — usuarios RBAC compartidos |
| 9 | `tech_notificaciones.id_usuario` | `rbac_usuarios.id_usuario` | id_usuario | NO ACTION | OK — usuarios RBAC compartidos |

**Total alertas B→A**: **9** (todas en `NO ACTION`, ninguna `CASCADE`).

### 6.2 — FKs `A → B`

**Total: 0** ✅. Ninguna tabla compartida apunta a una tabla por-escenario. Esto significa que el esquema A es **autocontenido** y los esquemas B nunca afectarán la integridad de A. Ideal para la migración.

### 6.3 — FKs internas

- **Caja A → A**: 7 FKs (rbac_role_permisos×2, rbac_usuarios, rbac_sesiones, pmo_project_managers→rbac_usuarios, p96_run_matrix×2). Todas se preservan dentro del esquema compartido.
- **Caja B → B**: 13 FKs (cmdb_activo_software×2, cmdb_cambios, cmdb_change_approvals, cmdb_costes, cmdb_ips×2, cmdb_relaciones×2, gobernanza_transacciones→cartera_build, incidencias_live→incidencias_run, kanban_tareas→incidencias_run, tech_chat_mensajes→tech_chat_salas, directorio_corporativo→directorio_corporativo). Todas se preservan dentro de cada esquema de banco.

### 6.4 — Gobernanza on_delete

- **CASCADE (`c`)**: 9 FKs — todas son intra-caja (B→B o A→A). NO hay CASCADE cross-caja, lo cual es seguro: borrar una fila A nunca cascadea silenciosamente a un B.
- **NO ACTION (`a`)**: 21 FKs — incluye las 9 cross-caja, todas con `NO ACTION` que es lo correcto para refs compartidas.

---

## 7) Restricciones técnicas detectadas para ARQ-03

1. **`search_path` no se fija en ningún sitio del código** (0 grep matches). Toda query asume `public` implícito. Esto significa que **el día que muevas tablas a otros esquemas, todas las queries actuales rompen** salvo que:
   - (a) Configures `search_path` a nivel de role/database (`ALTER ROLE jose_admin SET search_path = banco_x, compartido, public`)
   - (b) Crees vistas en `public` que apunten a los esquemas reales (estrategia menos invasiva, mantiene compat con código existente)
   - (c) Cualifiques todas las queries del backend (refactor masivo, no recomendado)

2. **Las 6 referencias `public.X` en SQL/Python son `to_regclass()` para guards de migración cerrada**. No bloquean el refactor pero sí hay que mantenerlas: si una tabla se mueve, `to_regclass('public.X')` devolverá NULL aunque la tabla siga existiendo en otro esquema.

3. **Cross-caja FKs B→A son 9, todas en NO ACTION**. Postgres permite FK cross-schema sin problemas. La estrategia "schema A compartido + 5 schemas B (uno por mundo)" es viable.

4. **Cero FK A→B**, lo que confirma que la caja compartida es estructuralmente independiente y se puede migrar primera sin tocar nada de los bancos.

5. **`directorio_corporativo` tiene self-FK** (`reporta_a` → `id_directivo`). Si va a B, todo el árbol jerárquico se duplica por banco — coherente con que cada banco tiene SU organigrama.

---

## 8) Resumen ejecutivo

| Concepto | Valor |
|---|---|
| Total tablas en `public` | **69** |
| Caja A (compartido) | **17** (24.6%) |
| Caja B (por escenario) | **48** (69.6%) |
| Caja C (dudosas) | **4** (5.8%) |
| Total FKs | **30** |
| FKs cross-caja `B → A` | **9** |
| FKs cross-caja `A → B` | **0** ✅ |
| FKs intra Caja A | **7** |
| FKs intra Caja B | **13** |
| Self-FKs | **1** (`directorio_corporativo`) |
| Refs `public.` en código | **6** (todas `to_regclass`, no críticas) |
| Refs `search_path` en código | **0** ⚠ (riesgo principal del refactor) |

**Próximos pasos sugeridos para F1**:
1. Decidir las 4 tablas Caja C (recomendaciones en sec 5)
2. Diseñar estrategia de `search_path` (recomendado: ALTER ROLE + vistas en public como puente)
3. Crear esquemas físicos `compartido`, `mundo_primitiva`, `mundo_banco_a/b/c/d`
4. Plan de migración: primero la Caja A (sin dependencias salientes), luego clonar 5× la Caja B
5. Verificar que las 9 FKs `B→A` siguen funcionando cross-schema

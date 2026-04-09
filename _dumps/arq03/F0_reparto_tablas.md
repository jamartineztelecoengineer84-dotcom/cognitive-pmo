# ARQ-03 F0 — Contrato de reparto de tablas (firmado)

**Fecha:** 2026-04-09
**Commit base:** 3ae2012da28dcf53eecfd42348c4754405519687
**Tag previo:** F-ARQ02-20-done
**Validado por:** Jose Antonio Martínez Victoria
**Estado:** CERRADO. Este documento es el contrato que F1 debe cumplir.

## 1. Objetivo

Mover las 69 tablas actuales de `public` a dos esquemas:
- `compartido` — pool/catálogos únicos para los 5 mundos
- `primitiva` — esquema operativo original (retrocompatibilidad)

Más adelante (F2+) se clonará `primitiva` en `sc_iberico`, `sc_litoral`,
`sc_norte`, `sc_piloto0` manteniendo las FKs cross-schema a `compartido`.

## 2. Estrategia de migración (cero cambios de código en F1)

```sql
-- Paso 1: crear esquemas
CREATE SCHEMA compartido;
CREATE SCHEMA primitiva;

-- Paso 2: mover cada tabla a su esquema destino
ALTER TABLE public.pmo_staff_skills SET SCHEMA compartido;
ALTER TABLE public.incidencias_run  SET SCHEMA primitiva;
-- ... (68 más)

-- Paso 3: configurar search_path por rol
ALTER ROLE jose_admin SET search_path = primitiva, compartido, public;
```

Con esto el backend sigue escribiendo `SELECT * FROM incidencias_run`
sin saber que ahora vive en `primitiva`. PostgreSQL resuelve el nombre
contra el primer esquema del search_path que lo contenga.

## 3. Caja A — compartido (18 tablas)

| Tabla | Justificación |
|---|---|
| pmo_staff_skills | Pool 150 técnicos único para los 5 mundos |
| pmo_project_managers | Pool 25 PMs único |
| rbac_usuarios | 175 usuarios pool único |
| rbac_roles | 23 roles estáticos |
| rbac_permisos | Catálogo estático |
| rbac_role_permisos | Matriz estática |
| rbac_sesiones | Sesiones globales por usuario |
| rbac_audit_log | Auditoría global (decisión: TODO RBAC en compartido) |
| catalogo_incidencias | Catálogo estático |
| catalogo_skills | Catálogo estático |
| cmdb_categorias | Taxonomía universal de CIs |
| documentacion_repositorio | Referencia estática |
| p96_governors | Config estática RBAC económico |
| p96_run_layers | Config estática marco RUN |
| p96_run_crits | Config estática criterios |
| p96_run_matrix | Config estática matriz |
| p96_strategy_frameworks | Config estática marcos |
| calendario_periodos_demanda | Calendario fiscal/comercial español universal |

Total A: **18 tablas**

## 4. Caja B — por escenario (51 tablas)

Se mantienen en `primitiva` en F1 y se clonarán por esquema banco en F2+.

**Familias completas:**
- `incidencias_*` (run + live)
- `build_*` (live, subtasks, risks, stakeholders, quality_gates, sprints, sprint_items, project_plans)
- `cmdb_*` excepto categorías (activos, relaciones, change_windows)
- `kanban_*` (tareas, wip_limits) — **wip_limits movida a B por decisión del usuario**
- `agent_conversations`, `itsm_form_drafts`
- `tech_chat_*`, `tech_notificaciones`
- `p96_pulse_*`, `p96_build_project_detail`
- `gobernanza_transacciones`, `pmo_governance_scoring`
- `whatif_*`, `war_room_*`, `compliance_*`, `postmortem_*`
- `intelligent_alerts`, `cartera_build`, `directorio_corporativo`
- `presupuestos`, `pipeline_sessions`

Total B: **51 tablas**

## 5. Caja C — resuelta (0 dudosas pendientes)

| Tabla | Decisión final | Motivo |
|---|---|---|
| calendario_periodos_demanda | A | Calendario fiscal universal |
| cmdb_change_windows | B | FK a cmdb_activos (B) |
| pipeline_sessions | B | Sesiones del operador en contexto de banco |
| kanban_wip_limits | B | Decisión del usuario: cada banco puede tener WIP distinto para discriminar saturación |

## 6. FKs cross-caja B→A (9, todas NO ACTION)

Al hacer ALTER TABLE SET SCHEMA, PostgreSQL cualifica automáticamente
las FKs. Las 9 quedarán como `primitiva.B.col → compartido.A.col`
sin necesidad de DROP/CREATE manual.

| # | Origen B | → | Destino A |
|---|---|---|---|
| 1 | cartera_build.responsable_asignado | → | pmo_staff_skills.id_recurso |
| 2 | incidencias_run.id_catalogo | → | catalogo_incidencias.id_catalogo |
| 3 | incidencias_run.tecnico_asignado | → | pmo_staff_skills.id_recurso |
| 4 | gobernanza_transacciones.fte_afectado | → | pmo_staff_skills.id_recurso |
| 5 | kanban_tareas.id_tecnico | → | pmo_staff_skills.id_recurso |
| 6 | pmo_governance_scoring.id_pm | → | pmo_project_managers.id_pm |
| 7 | cmdb_activos.id_categoria | → | cmdb_categorias.id_categoria |
| 8 | build_live.id_pm_usuario | → | rbac_usuarios.id_usuario |
| 9 | tech_notificaciones.id_usuario | → | rbac_usuarios.id_usuario |

FKs A→B: **0** (Caja A es autocontenida y puede moverse primero sin romper nada).

## 7. Puntos de riesgo para F1 (6 matches de public. en código)

Los 6 sites son BENIGNOS (todos `to_regclass`), pero UNO requiere
actualización defensiva:

| # | Fichero:línea | Tipo | Acción F1 |
|---|---|---|---|
| 1 | database/arq02_fase4_rename_itsm_form_drafts.sql:26 | Migración cerrada | Ninguna (histórico) |
| 2 | database/arq02_fase4_rename_itsm_form_drafts.sql:29 | Migración cerrada | Ninguna (histórico) |
| 3 | database/arq02_fase3_drop_zombie_incidencias.sql:23 | Migración cerrada | Ninguna (histórico) |
| 4 | backend/tests/test_arq02_f3_drop_zombie.py:26 | Test zombie DROP | Ninguna (asserta NULL) |
| 5 | backend/tests/test_arq02_f4_itsm_drafts.py:43 | Test rename old | Ninguna (asserta NULL) |
| 6 | backend/tests/test_arq02_f4_itsm_drafts.py:44 | Test rename new | **ACTUALIZAR F1** |

El test 6 hace `assert to_regclass('public.itsm_form_drafts') IS NOT NULL`.
Tras mover la tabla a `primitiva`, esto devolvería NULL y rompería el test.
Cambio en F1: reemplazar literal `'public.itsm_form_drafts'` por
`'primitiva.itsm_form_drafts'` o eliminar el namespace para que busque
por search_path.

## 8. search_path del código

- Matches actuales: **0**
- Conclusión: el backend NUNCA fija search_path, todas las queries
  asumen public implícito. La estrategia ALTER ROLE del §2 resuelve
  esto sin tocar una sola línea de Python.

En F3, el middleware HTTP que lea `X-Scenario` sobrescribirá el
search_path por transacción con `SET LOCAL`.

## 9. Criterio de entrada a F1

- [x] F0_recon.md generado
- [x] Clasificación 18+51+0 firmada (corregida en F2.0, ver §12)
- [x] Estrategia ALTER ROLE acordada
- [x] Grep public. verificado (6/6 benignos)
- [x] Riesgo test F-ARQ02-20 identificado
- [x] Contrato F0_reparto_tablas.md firmado

## 10. Zonas congeladas durante F1

- 0 cambios en backend/scenario_engine.py (F4)
- 0 cambios en middleware de conexión (F3)
- 0 creación de esquemas sc_* (F2+)
- 0 cambios en endpoints HTTP

F1 solo crea `compartido` + `primitiva`, mueve tablas con ALTER TABLE,
configura ALTER ROLE, actualiza el único test afectado, y verifica que
la suite pasa 88/0.

## 12. Errata y correcciones

- 2026-04-09 F2.0: corregido typo de Caja B de 50 → 51. El conteo real
  es 48 tablas puras Caja B del recon + 3 de Caja C que fueron asignadas
  a B (cmdb_change_windows, pipeline_sessions, kanban_wip_limits) = 51.
  El F0_recon.md no tenía el error, solo el contrato firmado.

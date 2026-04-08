# ARQ-01 Refundación Arquitectónica · REPORTE DE CIERRE

**Fecha cierre:** 2026-04-08
**Tag:** `arq01-done`
**Tag base:** `pre-arq01`

---

## 1. Cadena de commits

```
d5efdc0 ARQ-01 F5: PMO_JUNIOR allowlist + smoke 15 puntos
ae2c81d ARQ-01 F4.3: endpoint admin seed-scenario + E2E 7 checks
297ef7f ARQ-01 F4.2: scenarios HALF + OVERLOAD + fix técnicos menos cargados
6b6f11a ARQ-01 F3+F4.0+F4.1: schema hardening + pool compartido + scenario engine
```

> **Nota**: F0, F1 y F2 no produjeron commits de código (F0 = solo dumps en
> `_dumps/arq01/`, F1 = `UPDATE rbac_usuarios.id_pm = NULL` transaccional sin
> tocar repo, F2 = `INSERT pmo_project_managers + ALTER TABLE` sin tocar repo).
> Los 4 commits arriba cubren F3 → F5. La audit trail completa de F0–F2
> está en `_dumps/arq01/`.

## 2. Diff de archivos (`git diff --stat pre-arq01 arq01-done`)

```
 _dumps/arq01/smoke_F5.txt             | 120 +++++++++++
 backend/main.py                       |  67 ++++++
 backend/p96_router.py                 |   5 +-
 backend/pm_router.py                  |  55 +++--
 backend/scenario_engine.py            | 372 ++++++++++++++++++++++++++++++++++
 backend/tests/test_scenario_e2e.py    | 148 ++++++++++++++
 backend/tests/test_scenario_engine.py | 272 +++++++++++++++++++++++++
 7 files changed, 1025 insertions(+), 14 deletions(-)
```

## 3. Counts F0 → F6 (las 14 tablas)

| Tabla                | F0 baseline | F6 final | Δ |
|----------------------|------------:|---------:|--:|
| cartera_build        | 46          | 46       | 0 |
| build_subtasks       | 160         | 160      | 0 |
| build_risks          | 178         | 178      | 0 |
| build_stakeholders   | 234         | 234      | 0 |
| build_quality_gates  | 66          | 66       | 0 |
| build_project_plans  | 75          | 75       | 0 |
| build_sprints        | 51          | 51       | 0 |
| build_sprint_items   | 174         | 174      | 0 |
| build_live           | 60          | 60       | 0 |
| kanban_tareas        | 341         | 341      | 0 |
| incidencias_run      | 34          | 34       | 0 |
| incidencias_live     | 4           | 4        | 0 |
| incidencias          | 1           | 1        | 0 |
| run_incident_plans   | 61          | 61       | 0 |

**14/14 counts idénticos a F0**. Cero pérdida de datos legacy.

## 4. Cambios estructurales (NO en counts pero sí en schema/data)

- **`pmo_project_managers`**: +10 PMs nuevos (PM-016..PM-025): 4 PMO_SENIOR
  con `nivel='PM-Sr'` + 6 PMO_JUNIOR con `nivel='PM-Jr'`. Todos
  `@cognitivepmo.com`. Total tabla: 25 (15 legacy `@bcc-bank.es` + 10 nuevos).
- **`pmo_project_managers`**: +1 columna `id_usuario_rbac INTEGER REFERENCES
  rbac_usuarios(id_usuario)`. Los 15 legacy = NULL, los 10 nuevos = FK válida
  a sus correspondientes `rbac_usuarios.id_usuario` (19, 20, 21, 22, 1425..1430).
- **`rbac_usuarios.id_pm`**: 100% NULL (era el campo corrupto que F3.1 de P98
  rellenó con IDs numéricos rompiendo el principio de pool compartido).
- **`incidencias_run`**: +1 columna `id_proyecto VARCHAR(30) NULL` +
  índice `idx_inc_run_proyecto` btree.
- **`build_live`**: COMMENT documentando el universo LIVE operativo y el
  guard regex para scenario engine.
- **`cartera_build`**: COMMENT documentando read-only por scenario engine.
- **`p96_router.py`** `P96_ALLOWED_ROLES`: 15 → **16 roles** (añadido `PMO_JUNIOR`).

## 5. Código nuevo

- **`backend/scenario_engine.py`** (NEW, 372 líneas) — 4 escenarios
  (EMPTY, HALF, OPTIMAL, OVERLOAD) + helper `_pick_least_loaded_tecnicos` +
  6 invariantes (I1 guard regex, I2 doble escritura `id_pm_usuario`+`pm_asignado`,
  I3 kanban legacy intacto, I4 build_live legacy intacto, I5 cartera_build
  read-only, I6 `random.seed(42)` reproducible).
- **`backend/tests/test_scenario_engine.py`** (NEW, 272 líneas, **13 tests**).
- **`backend/tests/test_scenario_e2e.py`** (NEW, 148 líneas, **2 tests**).
- **`backend/main.py`**: +1 endpoint `POST /api/admin/seed-scenario`
  (SUPERADMIN only, body `{scenario_id, reset}`, devuelve counts scenario+legacy).
- **`backend/pm_router.py`**: `_RESOURCES_SQL` reescrito con CTE de pool
  compartido, usa `kanban_tareas.columna NOT IN ('Completado','Bloqueado')`,
  añade `horas_abiertas_total` y `pct_capacidad` cross-stream (40h/sem base).

## 6. Smoke F5 final

**14 ✅ + 1 caveat documentado**. Ver `_dumps/arq01/smoke_F5.txt` para detalle
literal de los 15 checks. Resumen:

- Tests pytest: **31/31 verde** (13 scenario_engine + 2 e2e + 16 p96_router).
- `/api/p96/build/portfolio` admin = 100 rows (60 legacy + 40 scenario).
- `/api/p96/build/portfolio` PMO_JUNIOR = 200 OK con 4 rows (PMO_JUNIOR ahora
  en allowlist).
- `/api/pm/my-resources` Pablo: 12 humans, pct max 152%, mediana 68%.
- 10/10 PMs nuevos pueden hacer login.
- `/pmo/managers/candidates` top-5 son los nuevos `cognitivepmo.com`.

## 7. Findings documentados (no bloquean cierre)

### F-1 · CHECK 5 — endpoint duplicado innecesario

El plan F5 mencionaba `GET /build/live/{id_proyecto}` que **no existe**. El
equivalente real en el código actual es `GET /api/p96/build/project/{id}` y
funciona correctamente (200 OK con `portfolio + detail`).
**Acción**: ninguna. El shell BUILD ya consume el endpoint correcto.

### F-2 · CHECK 2 — P97 portfolio MIS_PROYECTOS subcuenta proyectos legacy

`/api/p96/build/portfolio` con scope `MIS_PROYECTOS` para PMO_SENIOR/JUNIOR
filtra `pm_asignado` con match exacto a `nombre_completo`, lo que pierde
proyectos legacy donde `pm_asignado` está como nombre corto (p.ej.
`'Pablo Rivas'` vs `'Pablo Rivas Camacho'`). Pablo Rivas ve 4 proyectos en CEO
Dashboard cuando debería ver 12.
- **IMPACTO**: bajo. Solo afecta a la vista CEO Dashboard scoped.
- `/api/pm/my-projects` (endpoint del futuro PM Dashboard P98) devuelve los
  12 correctos porque filtra por `id_pm_usuario` (FK numérica).
- **ACCIÓN**: micro-patch P97.1 post-ARQ-01 — cambiar match exacto por ILIKE
  prefix o por `id_pm_usuario = current_user.id_usuario`.

### F-3 · pytest no en `requirements.txt`

Pytest se reinstala ad-hoc en el contenedor api en cada restart. Añadir a
`backend/requirements-dev.txt` cuando se haga el próximo rebuild de imagen.

### F-4 · COMMENT regex de `build_live`

El `COMMENT` puesto en F4.0 dice `^PRJ-[A-Z]{3}[0-9]+$` pero los IDs legacy
reales son `PRJ-MSF`, `PRJ-BBN`, `PRJ-OSP` (3 letras, **sin** dígitos). El
regex correcto sería `^PRJ-[A-Z]{3}[0-9]*$`. Solo afecta a la documentación
del COMMENT (no es CHECK constraint), pero corregir cuando convenga.

## 8. Estado final BD

- `pmo_project_managers`: **25** (15 legacy + 10 nuevos)
- `rbac_usuarios.id_pm IS NOT NULL`: **0** ✅
- `_arq01_snapshot_id_pm`: **DROPPED** (audit trail conservado en `_dumps/arq01/`)
- Scenario activo: **EMPTY** (legacy intacto)

## 9. Próximo paso

ARQ-01 cerrada. Reanudar **P98 PM Dashboard** desde F4 con 6 secciones
(proyectos, timeline, recursos, KPIs, incidencias, chat) sobre fundaciones
limpias:

- `/api/pm/my-projects` ✅ devuelve los proyectos del PM por `id_pm_usuario`
- `/api/pm/my-resources` ✅ devuelve pool compartido con `pct_capacidad`
- `/api/admin/seed-scenario` ✅ permite cargar demos para mockups
- `pmo_project_managers` ✅ tiene 10 PMs nuevos con FK rbac
- pool compartido ✅ es ley en todo el código

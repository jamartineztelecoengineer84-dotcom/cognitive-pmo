# RBAC Audit — 2026-04-15

**Alcance:** lectura pura de BBDD (`cognitive_pmo` @ postgres-pmo) y frontend. Sin cambios.
**BBDD:** schema `compartido` (rbac), `primitiva` (cartera/build_live), `sc_norte/iberico/litoral/piloto0` (escenarios).

---

## 1. ROLES DEFINIDOS

Query: `SELECT * FROM compartido.rbac_roles ORDER BY nivel_jerarquico, code;`

⚠️ La tabla `rbac_roles` **no tiene** columnas `scope_default` ni `ver_salario_ind`. Esos conceptos solo existen hardcoded en el frontend (`bgRoleProfiles` en `frontend/p96/index.html`). Aquí reporto las columnas que sí hay.

| code | nombre | nivel | activo | descripción |
|---|---|---|---|---|
| SUPERADMIN | Super Administrador | 0 | ✓ | Acceso total al sistema. Dios mode. |
| CEO | Chief Executive Officer | 1 | ✓ | Dirección general. Dashboard ejecutivo y reportes estratégicos. |
| CFO | Chief Financial Officer | 1 | ✓ | Dirección financiera. Presupuestos y control de costes. |
| CIO | Chief Information Officer | 1 | ✓ | Dirección de información. Gobernanza TI y compliance. |
| CISO | Chief Information Security Officer | 1 | ✓ | Dirección de seguridad. Auditorías, compliance y war room. |
| CTO | Chief Technology Officer | 1 | ✓ | Dirección tecnológica. Visión completa técnica. |
| VP_ENGINEERING | VP of Engineering | 2 | ✓ | Gestión técnica global. |
| VP_OPERATIONS | VP of Operations | 2 | ✓ | RUN y disponibilidad. |
| VP_PMO | VP of PMO | 2 | ✓ | Gobernanza de proyectos y portfolio. |
| DIRECTOR_DATA | Director de Datos | 3 | ✓ | Datos y BBDD. |
| DIRECTOR_INFRA | Director de Infraestructura | 3 | ✓ | Infra y redes. |
| DIRECTOR_IT | Director de IT | 3 | ✓ | Gestión de equipos y recursos. |
| DIRECTOR_SEC | Director de Seguridad | 3 | ✓ | Ciberseguridad. Incidentes. |
| AUDITOR | Auditor / Compliance | 4 | ✓ | Solo lectura + compliance. |
| PMO_SENIOR | PMO Senior / Program Manager | 4 | ✓ | Gobernanza, presupuestos, riesgos. |
| DEVOPS_LEAD | DevOps Lead | 5 | ✓ | CI/CD, IaC. |
| PMO_JUNIOR | PMO Junior / Project Manager | 5 | ✓ | Kanban y seguimiento. |
| QA_LEAD | QA Lead | 5 | ✓ | Testing, compliance técnica. |
| TEAM_LEAD | Team Lead / Jefe de Equipo | 5 | ✓ | Líder técnico de silo. |
| TECH_SENIOR | Técnico Senior (N3-N4) | 6 | ✓ | Resolución avanzada. |
| TECH_JUNIOR | Técnico Junior (N1-N2) | 7 | ✓ | Operaciones y soporte. |
| OBSERVADOR | Observador / Stakeholder | 8 | ✓ | Solo lectura. |
| READONLY | Solo Lectura | 9 | ✓ | Mínimo. |

**Total: 23 roles activos.**

---

## 2. USUARIOS EN BBDD

Query: `SELECT id_usuario, email, nombre_completo, r.code, u.id_recurso, u.id_pm, u.id_directivo, u.departamento, u.activo FROM rbac_usuarios u JOIN rbac_roles r ORDER BY r.nivel_jerarquico, u.nombre_completo;`

**Total: 181 usuarios activos. Distribución:**

| Rol | Nivel | # usuarios |
|---|---|---|
| SUPERADMIN | 0 | 1 |
| CEO | 1 | 1 |
| CFO | 1 | 1 |
| CIO | 1 | 1 |
| CISO | 1 | 1 |
| CTO | 1 | 1 |
| VP_ENGINEERING | 2 | 1 |
| VP_OPERATIONS | 2 | 1 |
| VP_PMO | 2 | 1 |
| DIRECTOR_DATA | 3 | 1 |
| DIRECTOR_INFRA | 3 | 1 |
| DIRECTOR_IT | 3 | **6** ⚠️ |
| DIRECTOR_SEC | 3 | 1 |
| AUDITOR | 4 | 1 |
| PMO_SENIOR | 4 | 4 |
| DEVOPS_LEAD | 5 | 1 |
| PMO_JUNIOR | 5 | 6 |
| QA_LEAD | 5 | 1 |
| TEAM_LEAD | 5 | 8 |
| TECH_SENIOR | 6 | 52 |
| TECH_JUNIOR | 7 | 89 |
| OBSERVADOR | 8 | 1 |
| READONLY | 9 | **0** ⚠️ |

### Listados clave (C-level + VP + PMO)

**C-level / VP (9 usuarios):**

| id | email | nombre | rol |
|---|---|---|---|
| 1 | admin | Administrador del Sistema | SUPERADMIN |
| 2 | alejandro.vidal@cognitivepmo.com | Alejandro Vidal Montero | CEO |
| 3 | carmen.delgado@cognitivepmo.com | Carmen Delgado Ríos | CTO |
| 7 | miguelangel.ruiz@cognitivepmo.com | Miguel Ángel Ruiz Portillo | VP_ENGINEERING |
| 8 | patricia.lopez@cognitivepmo.com | Patricia López de la Fuente | VP_OPERATIONS |
| 9 | gonzalo.fernandez@cognitivepmo.com | Gonzalo Fernández-Vega | VP_PMO |
| — | (CFO, CIO, CISO — 3 usuarios no enumerados arriba) | — | — |

**DIRECTOR_IT (6 — sospechoso, rol pensado como singular):**

| id | nombre | departamento |
|---|---|---|
| 10 | Laura Sanz Bermejo | Backend Engineering |
| 11 | Sergio Morales Pinto | Frontend Engineering |
| 17 | Ricardo Soto Mendoza | Soporte IT |
| 18 | Beatriz Castaño Villar | Sistemas Windows |
| 23 | Alberto Lozano Mejía | NOC |
| 24 | Inés García-Cano Duarte | SOC |

**PMOs (VP_PMO + PMO_SENIOR + PMO_JUNIOR = 11 usuarios):**

| id | nombre | rol | departamento | id_recurso | id_pm |
|---|---|---|---|---|---|
| 9 | Gonzalo Fernández-Vega | VP_PMO | PMO Corporativa | — | — |
| 19 | Pablo Rivas Camacho | PMO_SENIOR | PMO - Infraestructura | — | — |
| 20 | Cristina Vega Salinas | PMO_SENIOR | PMO - Aplicaciones | — | — |
| 21 | Daniel Prieto Gallardo | PMO_SENIOR | PMO - Seguridad | — | — |
| 22 | Lucía Romero Ibarra | PMO_SENIOR | PMO - Digital | — | — |
| 1425 | Inés Carmona Ruiz | PMO_JUNIOR | PMO | — | — |
| 1426 | Marta Núñez Herrera | PMO_JUNIOR | PMO | — | — |
| 1427 | Sergio Mateos Lara | PMO_JUNIOR | PMO | — | — |
| 1428 | Nuria Beltrán Ortega | PMO_JUNIOR | PMO | — | — |
| 1429 | Hugo Ramos Castillo | PMO_JUNIOR | PMO | — | — |
| 1430 | Rubén Ortiz Delgado | PMO_JUNIOR | PMO | — | — |

🔴 **Todos los PMOs tienen `id_recurso` y `id_pm` vacíos en `rbac_usuarios`.** El enlace a `pmo_project_managers.id_pm='PM-XX'` solo existe vía `pmo_project_managers.id_usuario_rbac` (back-link).

**Técnicos (149 usuarios) — muestreo:**

| rol | # | departamentos detectados |
|---|---|---|
| TECH_SENIOR | 52 | Backend, BBDD, DevOps, Frontend, Redes, Soporte |
| TECH_JUNIOR | 89 | Backend, BBDD, Frontend, QA, Seguridad, Soporte, Windows |
| TEAM_LEAD | 8 | Backend Engineering, DevOps, Redes, Seguridad IT, Soporte IT |

Listado completo omitido por volumen (149 filas) — disponible vía `SELECT u.id_usuario, u.nombre_completo, r.code, u.departamento FROM rbac_usuarios u JOIN rbac_roles r USING(id_role) WHERE r.code IN ('TECH_SENIOR','TECH_JUNIOR','TEAM_LEAD') ORDER BY r.code, u.nombre_completo;`

---

## 3. MAPEO SCOPES

⚠️ **No existen las tablas `rbac_scopes` ni `rbac_silo_map`.** Esquema `compartido` contiene solo: `rbac_audit_log, rbac_permisos, rbac_role_permisos, rbac_roles, rbac_sesiones, rbac_usuarios`.

**Lo que sí existe — scoping de facto:**

- **`rbac_permisos`**: (id_permiso, code, modulo, accion, descripcion, criticidad) — granularidad recurso/acción, sin dimensión silo.
- **`rbac_role_permisos`**: M:N rol↔permiso. SUPERADMIN tiene todos.
- **`pmo_staff_skills.silo_especialidad`** (varchar): silo técnico por *recurso*, no por rol (Backend, Frontend, DevOps, BBDD, Redes, Seguridad, Soporte, QA, Windows).
- **`rbac_usuarios.departamento`**: cadena libre que actúa de pseudo-silo para perfiles no-técnicos.

**Reglas scope/RGPD hardcoded en frontend** (`frontend/p96/index.html:1905` — `bgRoleProfiles`):

| rol | scope (UI) | ver salarios ind (UI) |
|---|---|---|
| SUPERADMIN | TODOS+ | ✓ |
| CEO | TODOS | 🔒 No |
| CFO | TODOS | ✓ |
| CTO | TODOS técnico | 🔒 No |
| CISO | Seguridad+SOC | 🔒 No |
| VP_OPERATIONS | RUN | 🔒 No |
| VP_ENGINEERING | BUILD | 🔒 No |
| DIRECTOR_INFRA/SEC/DATA/IT | su silo | 🔒 No |
| PMO_SENIOR | cartera | 🔒 No |
| TEAM_LEAD | equipo propio | 🔒 No |
| TECH_* | kanban personal | 🔒 No |
| AUDITOR | TODOS lectura | 🔒 No |

**Hallazgo:** no hay fuente de verdad en BBDD para "qué silos ve cada rol". Todo vive en JS del cliente → no auditable, no enforceable server-side.

---

## 4. ROUTING POST-LOGIN POR ROL

Fuente: `frontend/index.html` `p97RouteAfterLogin()` (post-fix BUG-LOGIN-01) + `demoLogin(email, target)`.

### Routing programático (`p97RouteAfterLogin`)

```
P96_ROLES = {CEO, CFO, CIO, CTO, CISO, VP_ENGINEERING, VP_OPERATIONS, VP_PMO,
             DIRECTOR_INFRA, DIRECTOR_SEC, DIRECTOR_DATA, DIRECTOR_IT,
             PMO_SENIOR, AUDITOR}
→ /p96/  (dashboard ejecutivo transversal)

TECH_SENIOR / TECH_JUNIOR → /tech-dashboard.html

resto (incl. SUPERADMIN ← post-fix) → showApp() / shell estándar con tabs
```

### Tabla rol → landing

| rol | landing | tabs/shell |
|---|---|---|
| SUPERADMIN | `/` (showApp) | shell estándar (RUN/BUILD/KANBAN/PROJECTS/BUDGET/TEAM GOV/PMO GOV/WAR ROOM) |
| CEO | `/p96/` | dashboard ejecutivo (KPIs, gobernadores, storytelling) |
| CFO | `/p96/` | dashboard ejecutivo |
| CIO | `/p96/` | dashboard ejecutivo |
| CTO | `/p96/` | dashboard ejecutivo |
| CISO | `/p96/` | dashboard ejecutivo |
| VP_ENGINEERING | `/p96/` | dashboard ejecutivo |
| VP_OPERATIONS | `/p96/` | dashboard ejecutivo |
| VP_PMO | `/p96/` | dashboard ejecutivo |
| DIRECTOR_INFRA | `/p96/` | dashboard ejecutivo |
| DIRECTOR_SEC | `/p96/` | dashboard ejecutivo |
| DIRECTOR_DATA | `/p96/` | dashboard ejecutivo |
| DIRECTOR_IT | `/p96/` | dashboard ejecutivo |
| PMO_SENIOR | `/p96/` | dashboard ejecutivo |
| AUDITOR | `/p96/` | dashboard ejecutivo |
| PMO_JUNIOR | `/` (showApp) | shell estándar |
| DEVOPS_LEAD | `/` (showApp) | shell estándar |
| QA_LEAD | `/` (showApp) | shell estándar |
| TEAM_LEAD | `/` (showApp) | shell estándar |
| TECH_SENIOR | `/tech-dashboard.html` | dashboard técnico (kanban personal) |
| TECH_JUNIOR | `/tech-dashboard.html` | dashboard técnico |
| OBSERVADOR | `/` (showApp) | shell estándar |
| READONLY | `/` (showApp) | shell estándar |

### Overrides del login demo (`demoLogin(email, target)`)

El login demo ignora `p97RouteAfterLogin()` si `target` es `gov-run`, `gov-build` o `tech`. Atajos hardcoded en las 7 cards:

| card demo | target | landing real |
|---|---|---|
| Alejandro Vidal (CEO) | `index` | `/p96/` vía p97 |
| Carmen Delgado (CTO) | `index` | `/p96/` vía p97 |
| Patricia López (VP Ops) | `gov-run` | `/gov-run.html` (directo, salta p97) |
| Miguel Á. Ruiz (VP Eng) | `gov-build` | `/gov-build.html` (directo, salta p97) |
| Pablo Rivas (PMO Sr) | `index` | `/p96/` vía p97 |
| Sandra Ortega (Tech Sr) | `tech` | `/tech-dashboard.html` (directo) |
| Adriana Suárez (Tech Jr) | `tech` | `/tech-dashboard.html` (directo) |

⚠️ Inconsistencia: Patricia López (VP_OPERATIONS) vía demoLogin cae en `/gov-run.html`, pero vía login normal caería en `/p96/`. Mismo patrón para Miguel Á. Ruiz con BUILD.

---

## 5. PMs — ANÁLISIS ESPECÍFICO

### Conteos

- **Usuarios PMO en `rbac_usuarios`:** 11 (1 VP_PMO + 4 PMO_SENIOR + 6 PMO_JUNIOR).
- **Filas en `compartido.pmo_project_managers`:** **25** (PM-001…PM-025).
- **Proyectos en `primitiva.cartera_build`:** 46 total · 34 con `id_pm_usuario` NULL · 12 asignados (todos a `PM-016`).
- **Filas en `primitiva.build_live`:** 61 · 60 con `id_pm_usuario` (integer) · 1 NULL.

### Distribución `cartera_build.id_pm_usuario` (varchar)

| id_pm_usuario | # proyectos |
|---|---|
| `PM-016` | 12 |
| NULL | 34 |

### Distribución `build_live.id_pm_usuario` (integer)

| id_pm_usuario (= rbac.id_usuario) | nombre | # rows |
|---|---|---|
| 19 | Pablo Rivas Camacho (PMO_SENIOR) | 8 |
| 20 | Cristina Vega Salinas (PMO_SENIOR) | 8 |
| 21 | Daniel Prieto Gallardo (PMO_SENIOR) | 8 |
| 22 | Lucía Romero Ibarra (PMO_SENIOR) | 8 |
| 1425 | Inés Carmona (PMO_JUNIOR) | 5 |
| 1426 | Marta Núñez (PMO_JUNIOR) | 5 |
| 1427 | Sergio Mateos (PMO_JUNIOR) | 5 |
| 1428 | Nuria Beltrán (PMO_JUNIOR) | 5 |
| 1429 | Hugo Ramos (PMO_JUNIOR) | 4 |
| 1430 | Rubén Ortiz (PMO_JUNIOR) | 4 |
| NULL | — | 1 |

### PMs huérfanos (en `pmo_project_managers` sin link RBAC)

🔴 **15 PMs huérfanos (PM-001 a PM-015)** con `id_usuario_rbac = NULL`. **No pueden hacer login.** Aun así algunos aparecen con `proyectos_activos > 0`:

| id_pm | nombre | proyectos_activos | id_usuario_rbac |
|---|---|---|---|
| PM-001 | Elena Rodríguez Vega | 1 | ⚠️ NULL |
| PM-002 | Miguel Ángel Torres López | 4 | ⚠️ NULL |
| PM-003 | Carmen Jiménez Navarro | 5 | ⚠️ NULL |
| PM-004 | Roberto Martín Sánchez | 3 | ⚠️ NULL |
| PM-005 | Ana Belén García Moreno | 4 | ⚠️ NULL |
| PM-006 | Francisco Javier Ruiz Ortega | 1 | ⚠️ NULL |
| PM-007 | Laura Fernández Castro | 3 | ⚠️ NULL |
| PM-008 | David Sánchez Herrera | 2 | ⚠️ NULL |
| PM-009 | María José López Díaz | 0 | ⚠️ NULL |
| PM-010 | Carlos Alberto Pérez Molina | 2 | ⚠️ NULL |
| PM-011 | Isabel Moreno Gutiérrez | 10 | ⚠️ NULL |
| PM-012 | Alejandro Navarro Blanco | 4 | ⚠️ NULL |
| PM-013 | Sofía Martínez Ramos | 5 | ⚠️ NULL |
| PM-014 | Raúl Gómez Serrano | 2 | ⚠️ NULL |
| PM-015 | Patricia Vázquez Luna | 0 | ⚠️ NULL |

### Referencias FK cruzadas

🔴 **FK rota `cartera_build.id_pm_usuario='PM-016'` → no existe en `rbac_usuarios.id_recurso` ni en `id_pm`** (0 filas). El único punto donde `PM-016` resuelve a una persona es `pmo_project_managers.id_pm`, pero esa tabla no está enlazada por FK a `cartera_build`.

### PMs sin proyectos asignados en cartera (10)

PM-017…PM-025 (todos con `id_usuario_rbac` válido, pero 0 proyectos en `cartera_build`). Sí aparecen en `build_live`. ⚠️ **Desalineación cartera_build ↔ build_live.**

### PMs activos (pueden login) sin uso

PM-016 (Pablo Rivas) es el único con proyectos en `cartera_build` (12). Los demás PMs con RBAC (PM-017…PM-025) solo figuran en `build_live` con 4-8 proyectos cada uno.

### Técnicos con `id_pm` — piedra fundamental

✅ **0 técnicos** (TECH_SENIOR, TECH_JUNIOR, TEAM_LEAD) tienen `id_pm` no-NULL. Pool compartido preservado.

### PMs huérfanos a la inversa (PMs en rbac sin referencia en build)

- VP_PMO Gonzalo Fernández-Vega (id=9): no aparece como `id_pm_usuario` en cartera_build ni build_live. Esperado (es VP, no gestor directo).

### Incoherencia de tipos

- `cartera_build.id_pm_usuario` = `VARCHAR(20)` con valores tipo `'PM-016'`.
- `build_live.id_pm_usuario` = integer con FK a `rbac_usuarios.id_usuario`.
- **Misma columna, nombre idéntico, tipos y semánticas distintos.** Imposible hacer UNION/JOIN directo.

---

## 6. INCONSISTENCIAS DETECTADAS

- 🔴 **Dos sistemas de ID para PM coexistiendo sin puente**:
  - `cartera_build.id_pm_usuario` varchar `'PM-XXX'` → apunta a `pmo_project_managers.id_pm`.
  - `build_live.id_pm_usuario` integer → apunta a `rbac_usuarios.id_usuario`.
  - Misma columna de negocio, dos dominios. Sin vista unificada.
- 🔴 **15 PMs huérfanos** (`PM-001`…`PM-015`) con `id_usuario_rbac=NULL` → personas ficticias no loguables. 44 de los 46 proyectos en `cartera_build` acabarían colgando de estos si se respetasen sus `proyectos_activos`.
- 🔴 **34 de 46 proyectos** en `cartera_build` tienen `id_pm_usuario` NULL (74 %).
- 🔴 **`rbac_usuarios.id_pm` y `id_recurso` vacíos en todos los PMOs**. La trazabilidad rol↔gestión es unidireccional (solo desde `pmo_project_managers.id_usuario_rbac`).
- 🔴 **No existe `rbac_scopes` ni `rbac_silo_map`.** Reglas de scope viven únicamente en JS (`bgRoleProfiles`). No auditable server-side.
- 🔴 **`rbac_roles` sin `scope_default` ni `ver_salario_ind`.** El user asumía que existían; no es el caso.
- 🟠 **DIRECTOR_IT tiene 6 usuarios**. El nombre del rol sugiere singular; si la intención era 1 por área, faltan sub-roles (DIRECTOR_BACKEND, DIRECTOR_FRONTEND, etc.) o el rol debería renombrarse a algo plural.
- 🟠 **READONLY sin usuarios** (0). Rol creado pero no usado.
- 🟠 **Demo login bypass**: VP_OPERATIONS y VP_ENGINEERING demo caen en `/gov-run.html` y `/gov-build.html` respectivamente, pero su ruta "oficial" (`p97RouteAfterLogin`) es `/p96/`. Dos experiencias distintas para el mismo rol según puerta de entrada.
- 🟠 **Email de SUPERADMIN es `admin`** (sin dominio). Rompe el formato uniforme `*.*@cognitivepmo.com` del resto.
- 🟢 **Nombres**: 0 duplicados en `rbac_usuarios.nombre_completo`. El caso "Alex Núñez" estaba solo en JS, ya corregido.
- 🟢 **`id_recurso` duplicados**: 0.
- 🟢 **Usuarios inactivos**: 0.
- 🟢 **Técnicos con `id_pm`**: 0 (piedra fundamental íntegra).
- 🟢 **Roles sin usuarios (además de READONLY)**: ninguno.
- 🟢 **Usuarios con `rol_code` inexistente**: 0 (FK garantiza integridad).

---

## 7. COMPARATIVA LOGIN DEMO vs REALIDAD

Las 7 cards del login demo (`frontend/index.html:1675-1701`) vs `rbac_usuarios`:

| card demo | rol demo | existe en rbac (id, rol, activo) | coincide landing? |
|---|---|---|---|
| Alejandro Vidal | CEO | ✅ id=2 · CEO · activo | ✅ card→`/p96/` ≡ p97→`/p96/` |
| Carmen Delgado | CTO | ✅ id=3 · CTO · activo | ✅ card→`/p96/` ≡ p97→`/p96/` |
| Patricia López | VP Operations | ✅ id=8 · VP_OPERATIONS · activo | ⚠️ card→`/gov-run.html` ≠ p97→`/p96/` |
| Miguel Á. Ruiz | VP Engineering | ✅ id=7 · VP_ENGINEERING · activo | ⚠️ card→`/gov-build.html` ≠ p97→`/p96/` |
| Pablo Rivas | PMO Senior | ✅ id=19 · PMO_SENIOR · activo | ✅ card→`/p96/` ≡ p97→`/p96/` |
| Sandra Ortega | Técnico Senior N3 | ✅ id=33 · TECH_SENIOR · activo | ✅ card→`/tech-dashboard.html` ≡ p97 |
| Adriana Suárez | Técnico Junior N2 | ✅ id=86 · TECH_JUNIOR · activo | ✅ card→`/tech-dashboard.html` ≡ p97 |

**7/7 usuarios existen y están activos.** Desajuste solo en Patricia López y Miguel Á. Ruiz: el demo atajo los lleva al governance directo, el login normal al dashboard ejecutivo — dos experiencias distintas por rol.

---

## Apéndice — Queries reproducibles

```sql
-- Sección 1: roles
SELECT code, nombre, nivel_jerarquico, activo, descripcion
FROM compartido.rbac_roles ORDER BY nivel_jerarquico, code;

-- Sección 2: usuarios por rol
SELECT r.code, COUNT(u.id_usuario)
FROM compartido.rbac_roles r
LEFT JOIN compartido.rbac_usuarios u ON u.id_role=r.id_role AND u.activo
GROUP BY r.code, r.nivel_jerarquico
ORDER BY r.nivel_jerarquico, r.code;

-- Sección 5: PMs huérfanos
SELECT id_pm, nombre, proyectos_activos
FROM compartido.pmo_project_managers
WHERE id_usuario_rbac IS NULL ORDER BY id_pm;

-- Sección 5: distribución cartera_build
SELECT id_pm_usuario, COUNT(*)
FROM primitiva.cartera_build
GROUP BY id_pm_usuario ORDER BY 2 DESC;

-- Sección 5: FK check
SELECT COUNT(*) FROM compartido.rbac_usuarios
WHERE id_recurso='PM-016' OR id_pm='PM-016';  -- → 0

-- Sección 6: técnicos con id_pm
SELECT COUNT(*) FROM compartido.rbac_usuarios u
JOIN compartido.rbac_roles r USING(id_role)
WHERE r.code IN ('TECH_SENIOR','TECH_JUNIOR','TEAM_LEAD')
  AND u.id_pm IS NOT NULL AND u.id_pm <> '';  -- → 0
```

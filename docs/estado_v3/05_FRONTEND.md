# 05 — Frontend

**Generado:** 2026-04-01  
**Líneas index.html:** 15.780  
**Archivos HTML:** 3 (+ 3 backups)

---

## Archivos HTML

| Archivo | Tamaño | Descripción |
|---------|--------|-------------|
| `index.html` | 1.1 MB (15.780 líneas) | App principal — Dirección (visión 360°) |
| `gov-run.html` | 40 KB | Panel Coordinador RUN (ITSM + técnicos + Kanban) |
| `gov-build.html` | 36 KB | Panel Coordinador BUILD (PMO + técnicos + Scrum) |
| `index.html.backup_pausa` | backup | Backup pre-pausas |
| `index.html.backup_v36` | backup | Backup v3.6 |
| `index.html.backup_v40_backend` | backup | Backup v4.0-backend |
| `nginx.conf.backup` | backup | Backup nginx config |
| `login-bg.png` | imagen | Fondo de pantalla de login |

---

## Arquitectura Multi-Rol (v5.0)

```
index.html → Dirección (visión 360°, todas las pestañas)
gov-run.html → Coordinador RUN (ITSM + técnicos + Kanban + iframe pipeline)
gov-build.html → Coordinador BUILD (PMO + técnicos + Scrum + iframe pipeline)
```

Los gobernadores abren `index.html` en un iframe con:
- URL: `/index.html?token=XXX#auto-run` o `#auto-build`
- Token del padre pasado via URL para evitar login
- Modo gobernador (`gov-mode` CSS class) oculta todo excepto pipeline

---

## Mapa de Funciones Clave (index.html)

### Funciones Críticas (NO TOCAR)

| Función | Línea | Riesgo | Descripción |
|---------|-------|--------|-------------|
| `authFetch` | 3777 | ALTO | Fetch autenticado con token JWT |
| `executeRunPipeline` | 5595 | ALTO | Pipeline RUN completo (SSE + 3 agentes) |
| `executeBuildPipeline` | 7479 | ALTO | Pipeline BUILD completo (SSE + 9 agentes + 4 pausas) |
| `executePipeline` | 11192 | ALTO | Dispatcher que llama a executeRun/BuildPipeline |
| `savePipelineState` | 7251 | ALTO | Guarda sesión pipeline en BD |
| `showBuildPause` | 8526 | ALTO | Renderiza pausas 1-4 con toda la UI interactiva |
| `showBuildFinalScreen` | 10316 | ALTO | Pantalla final BUILD con Scrum board |
| `itsmSubmitAndPipeline` | 5117 | ALTO | Registra incidencia ITSM + lanza pipeline RUN |
| `buildSubmitAndPipeline` | 5439 | ALTO | Registra proyecto + lanza pipeline BUILD |

### Funciones Pipeline BUILD

| Función | Línea | Descripción |
|---------|-------|-------------|
| `renderPipelineStepsHeader` | 7370 | Header de pasos del pipeline con navegación |
| `navigateToPipelineStep` | 7440 | Navega entre pausas P1-P4 |
| `showBuildPauseReadOnly` | 7454 | Muestra pausa en modo solo lectura |
| `loadBuildLiveSessions` | 7290 | Carga sesiones BUILD activas |
| `resumePipelineSession` | 7324 | Resume pipeline desde sesión guardada |
| `renderBuildCascadeIdle` | 6822 | Renderiza cascada BUILD en idle |
| `renderBuildPipelineBar` | 6885 | Barra de progreso pipeline |
| `activateBuildAgent` | 6944 | Activa agente en pipeline visual |
| `completeBuildAgent` | 6954 | Marca agente como completado |
| `setAgentSpawningState` | 6970 | Estado spawning Director/Workers/Merger |
| `renderAdvisorChat` | 7994 | Chat con AG-018 Governance Advisor |
| `sendAdvisorMessage` | 8062 | Envía mensaje al advisor |

### Funciones de Datos

| Función | Línea | Descripción |
|---------|-------|-------------|
| `loadTeam` | 4255 | Carga 150 técnicos |
| `loadProjects` | 4382 | Carga 46 proyectos |
| `loadKanban` | 4487 | Carga 493 tareas kanban |
| `renderKanban` | 4503 | Renderiza tablero kanban |
| `loadBuildLive` | 6265 | Carga proyectos BUILD activos |
| `loadActiveIncidents` | 6312 | Carga incidencias activas sidebar |
| `loadItsmCatalog` | 5030 | Carga catálogo 61 tipos incidencias |
| `loadBudgets` | 12126 | Carga presupuestos |
| `loadGovernance` | 12538 | Carga PMO governance |
| `loadWarRoom` | 12996 | Carga War Room |
| `loadDocs` | 13512 | Carga documentación |

### Funciones UI/UX

| Función | Línea | Descripción |
|---------|-------|-------------|
| `showPage` | 4057 | Navegación entre páginas (RUN/BUILD/TEAM/etc.) |
| `showToast` | 11696 | Muestra notificación toast |
| `fmOpen` / `fmClose` | 11729-11730 | Abre/cierra modales |
| `toggleTheme` | 14960 | Dark/light theme toggle |
| `doLogin` | 3789 | Login con hash SHA-256 |
| `doLogout` | 3839 | Logout |
| `checkExistingSession` | 4007 | Verifica sesión existente |

### Funciones Modo Gobernador (v5.0 - NEW)

| Función | Línea | Descripción |
|---------|-------|-------------|
| `hideGovPanels` | 15702 | Oculta paneles por ID interno en modo gobernador |
| Auto-launch IIFE | 15663 | Detecta #auto-run/#auto-build, inyecta token, lanza pipeline |

### Funciones CMDB

| Función | Línea | Descripción |
|---------|-------|-------------|
| `loadCmdbDashboard` | 13882 | Dashboard CMDB |
| `loadCmdbInventario` | 13938 | Inventario activos |
| `loadCmdbVlans` | 14128 | Gestión VLANs |
| `loadCmdbIps` | 14276 | Gestión IPs |
| `loadCmdbSoftware` | 14455 | Inventario software |
| `loadCmdbCostes` | 14482 | Gestión costes IT |
| `loadCmdbCompliance` | 14697 | Compliance dashboard |

### Funciones RBAC

| Función | Línea | Descripción |
|---------|-------|-------------|
| `loadRbacUsers` | 15129 | Lista usuarios RBAC |
| `loadRbacRolesPanel` | 15314 | Panel roles con permisos |
| `loadRbacAudit` | 15543 | Log de auditoría |
| `loadRbacOrg` | 15571 | Organigrama |

### Funciones DevTools

| Función | Línea | Descripción |
|---------|-------|-------------|
| `loadDevTables` | 14749 | Explorador de tablas BD |
| `devRunSQL` | 14794 | Ejecutar SQL directo |
| `loadDevFiles` | 14820 | Explorador de archivos |
| `loadDevContext` | 14858 | Contexto para LLM |

---

## Páginas del SPA (index.html)

| ID | Tab | Descripción |
|----|-----|-------------|
| `page-run` | RUN | Pipeline ITSM + formulario + incidencias activas |
| `page-build` | BUILD | Pipeline PMO + formulario proyecto + BUILD LIVE |
| `page-team` | TEAM GOV | Directorio 150 técnicos + dashboard |
| `page-governance` | GOVERNANCE | PMO Governance + PMs + Scoring + Gates |
| `page-projects` | PROJECTS | Base de datos 46 proyectos |
| `page-kanban` | KANBAN | Tablero 8 columnas + métricas CFD |
| `page-budget` | BUDGET | Presupuestos CAPEX/OPEX |
| `page-warroom` | WAR ROOM | Crisis + Alerts + Compliance + Simulations |
| `page-docs` | DOCS | Repositorio documentación |
| `page-cmdb` | CMDB | Activos + VLANs + IPs + Software + Costes |
| `page-devtools` | DEVTOOLS | SQL Explorer + Files + Context |

---

## Total de funciones JavaScript

**~280 funciones** definidas en index.html (grep `function [a-zA-Z]`).

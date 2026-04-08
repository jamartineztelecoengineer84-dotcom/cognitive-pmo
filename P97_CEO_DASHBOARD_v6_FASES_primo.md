# P97 — CEO Dashboard v6 · Fases

Integración del mockup CEO Dashboard v6 (frontend independiente) con el sistema
Cognitive PMO real (BD PostgreSQL + backend FastAPI + RBAC económico).

---

## Estado de fases

| Fase  | Estado | Descripción                                                |
|-------|--------|------------------------------------------------------------|
| F0    | ✅      | Recon — verificar mockup, paths NAS, tablas existentes      |
| F1    | ✅      | BD schema — 12 tablas `p96_*` + 3 vistas                    |
| F2    | ✅      | Seed — 60 proyectos reales (cleanup `build_live`)           |
| F3    | ✅      | Backend — 14 endpoints `/api/p96/*` + RBAC econ embebido    |
| F4    | ✅      | Nginx — `location ^~ /p96/` (root, no alias)                |
| F5    | ✅      | Cableado — loaders + adapters camelCase↔snake_case          |
| F5.2  | ✅      | Fix — `bgRunMatrix` cascade (TDZ + 3 bugs encadenados)      |
| F6    | ✅      | Routing — allowlist + `/api/me` + hydrate + logout          |
| F7    | ✅      | Tests — pytest 16/16 verde (smoke + RBAC econ)              |
| F8    | ✅      | Smoke E2E + cierre P97 (este)                               |

---

## CIERRE P97 — 2026-04-08

P97 cerrado. CEO Dashboard v6 totalmente integrado con BD real, RBAC económico,
routing post-login con allowlist, hydrate desde shell y logout funcional.

### Commits clave del cierre

- `ce00fe8` — v5.2.28 — F6: routing post-login + /api/me + allowlist + p96Logout
- `0b4a386` — fix(p96): null-check bg-modal-overlay listener
- `87b6c38` — F7: smoke + RBAC econ tests para /api/p96/* y /api/me (16/16 verde)
- _commit de release v5.3.0 + tag `p97-done` (F8)_

### Métricas finales

- **BD**: 12 tablas `p96_*` + 3 vistas, 60 proyectos, 15 gobernadores
- **Backend**: 14 endpoints `/api/p96/*` + `/api/me` enriquecido
- **RBAC econ**: 23 roles mapeados, allowlist `/p96/` = 15 roles (niveles 0-4)
- **Tests**: 16/16 pytest verdes (0.25s)
- **Frontend**: mockup `/p96/` cableado a backend real con auth JWT

### Zonas congeladas respetadas

- `authFetch`, `executeRunPipeline`, `executeBuildPipeline`, `savePipelineState`
- `renderPipelineStepsHeader`, `navigateToPipelineStep`, `bgToggleTheme`
- Funciones `bgRender*` del mockup (sólo se inyectaron loaders + adapters)

# Changelog

## v5.3.0 — 2026-04-08 — P97 CEO Dashboard v6 integrado

- BD: 12 tablas `p96_*` + 3 vistas (60 proyectos reales)
- Backend: 14 endpoints `/api/p96/*` + `/api/me` con RBAC económico (23 roles)
- Frontend: mockup CEO Dashboard v6 integrado en `/p96/` con login real, hydrate, logout y allowlist
- Routing post-login: 15 roles ejecutivos → `/p96/`, TECH_* → `/tech-dashboard.html`, resto → shell
- Tests: 16 tests pytest (smoke + RBAC económico) verdes
- Bugfixes: `/api/me` 500→401 sin token, `bg-modal-overlay` null-check

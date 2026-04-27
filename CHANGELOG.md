# Changelog

Registro de hitos del proyecto (formato basado en [Keep a Changelog](https://keepachangelog.com/)).

## [Unreleased]

- Migración del frontend vanilla a SvelteKit
- OpenTelemetry tracing end-to-end
- Vector DB (pgvector) para embeddings persistentes en RAG
- Integración bidireccional con Plane (issues sync)

## [v6.0] — 2026-04

### Added — Gestor documental con RAG
- API REST con 14 endpoints (`/api/doc/*`)
- Agente AG-DOC integrado con Ollama (gemma3:1b) para Q&A sobre 750+ documentos
- Frontend `/doc/` con búsqueda + chat + preview
- Agente Excel/CSV con openpyxl + LLM local
- Seed de 752 documentos sintéticos en `primitiva.documentacion_repositorio`

## [v5.3] — 2026-04

### Added — CEO Dashboard v6 (P97)
- 12 tablas `p96_*` + 3 vistas materializadas (60 proyectos)
- Endpoints `/api/p96/*` con RBAC económico (23 roles)
- Login + hydrate + routing por rol (15 ejecutivos → CEO, TECH_* → tech dashboard)
- 16 tests pytest verdes (smoke + RBAC)

## [v5.2] — 2026-03

### Added — Portfolio Prioritization Wizard
- Wizard de 4 fases para priorización ponderada de portfolio
- Integración como pestaña del CEO Dashboard
- Decomposición automática de subtareas vía LLM (Anthropic Claude)

## [v5.1] — 2026-03

### Added — Producción readiness
- Sistema de monitorización (4 pilares: Resend + audit log + alertas + status page)
- Backups automáticos diarios con retención
- Rate limiting por endpoint (slowapi)
- Health checks Docker

## [v5.0] — 2026-02

### Added — Arquitectura multi-schema
- Refactor a multi-schema PostgreSQL (RBAC + tenancy lógica)
- CMDB completa con costes y cobertura de monitorización
- Forecasting con Prophet sobre series históricas

## [v4.x] — 2026-01

### Added — Foundation
- FastAPI + asyncpg + multi-agent system
- Frontend vanilla con tema oscuro/claro
- 60+ endpoints REST iniciales
- Datos sintéticos de organización demo (~600 empleados, ~150 aplicaciones)

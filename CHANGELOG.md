# Changelog

Project milestone log (format inspired by [Keep a Changelog](https://keepachangelog.com/)).

## [Unreleased]

- Migrate vanilla frontend to SvelteKit
- End-to-end OpenTelemetry tracing
- Vector DB (pgvector) for persistent RAG embeddings
- Bidirectional Plane integration (issue sync)

## [v6.0] — 2026-04

### Added — Document manager with RAG
- REST API with 14 endpoints (`/api/doc/*`)
- AG-DOC agent integrated with Ollama (gemma3:1b) for Q&A over 750+ documents
- `/doc/` frontend with search + chat + preview
- Excel/CSV agent with openpyxl + local LLM
- Seed of 752 synthetic documents into `primitiva.documentacion_repositorio`

## [v5.3] — 2026-04

### Added — CEO Dashboard v6 (P97)
- 12 `p96_*` tables + 3 materialized views (60 projects)
- `/api/p96/*` endpoints with economic RBAC (23 roles)
- Login + hydrate + role-based routing (15 executives → CEO, TECH_* → tech dashboard)
- 16 green pytest tests (smoke + RBAC)

## [v5.2] — 2026-03

### Added — Portfolio Prioritization Wizard
- 4-phase wizard for weighted portfolio prioritization
- Integrated as a CEO Dashboard tab
- Automatic subtask decomposition via LLM (Anthropic Claude)

## [v5.1] — 2026-03

### Added — Production readiness
- Monitoring system (4 pillars: Resend + audit log + alerts + status page)
- Automated daily backups with retention
- Per-endpoint rate limiting (slowapi)
- Docker health checks

## [v5.0] — 2026-02

### Added — Multi-schema architecture
- Refactor to multi-schema PostgreSQL (RBAC + logical tenancy)
- Full CMDB with cost analysis and monitoring coverage
- Forecasting with Prophet over historical series

## [v4.x] — 2026-01

### Added — Foundation
- FastAPI + asyncpg + multi-agent system
- Vanilla frontend with dark/light theme
- 60+ initial REST endpoints
- Synthetic data for the demo organization (~600 employees, ~150 applications)

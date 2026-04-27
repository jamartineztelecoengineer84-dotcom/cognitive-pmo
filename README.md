# Cognitive PMO

> Full-stack PMO platform with AI agents — portfolio governance, RAG-based document manager, executive dashboards, and capacity forecasting.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL 15](https://img.shields.io/badge/postgres-15-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](https://docs.docker.com/compose/)

---

## Overview

**Cognitive PMO** is a full-stack platform that automates the Project Management Office of a mid-sized technology organization. It combines:

- **Portfolio governance** (prioritization, global kanban, intake-to-delivery flow)
- **AI agents** for specialized tasks (task advisor, document agent, automatic subtask decomposition)
- **RAG-based document manager** over 750+ documents
- **Executive dashboards** (CEO, CIO, CISO, CFO, CTO views)
- **Capacity forecasting** with Prophet
- **Integrated CMDB** with cost analysis and monitoring coverage
- **RBAC + audit log** with email notifications

Built as a use case for a demo bank (~600 employees, 100% synthetic data) to showcase cloud-native architecture, LLM integration, and modern observability practices.

---

## Tech stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11 · FastAPI · asyncpg · Pydantic v2 |
| **Frontend** | Vanilla HTML/JS · nginx · dark/light theme · 12+ dashboard views |
| **Database** | PostgreSQL 15 · multi-schema (RBAC + logical tenancy) |
| **AI / LLMs** | Anthropic Claude API · local Ollama (gemma3) · Flowise for orchestration |
| **Forecasting** | Prophet (Meta) for capacity and demand prediction |
| **Email** | Resend API · transactional templates |
| **Infrastructure** | Docker Compose · APScheduler · slowapi (rate limiting) |
| **Documents** | PyPDF2 · python-docx · openpyxl · ReportLab |
| **Deployment** | On-premise VPS · automated daily backups · status page |

---

## Key features

### 🤖 Multi-agent system
A central router orchestrates specialized agents (`router.py`, `spawner.py`):
- **Task Advisor** — analyzes a project plan and suggests subtask decomposition
- **Document Agent (AG-DOC)** — searches, summarizes, and answers questions over the corporate document repository
- **Excel/CSV Agent** — extracts and analyzes tabular data (openpyxl + local LLM)
- **Sync Worker** — processes events in the background

### 📊 Executive dashboards
Pre-built views tailored to C-level roles:
- **CEO Dashboard** (P97) — portfolio, financial KPIs, governance alerts
- **CIO Dashboard** — CMDB health, monitoring coverage, technical risks
- **CISO Dashboard** — RBAC audits, compliance, audit log
- **CFO Dashboard** — cost-per-application, budget vs actual, OPEX forecast

### 📚 Document manager with RAG
- Indexes 750+ documents from the corporate repository (PDF, DOCX, XLSX, TXT)
- Asynchronous ingestion pipeline with metadata extraction
- Natural-language Q&A through an LLM-backed agent

### 📈 Portfolio Prioritization Wizard
A 4-phase wizard that prioritizes portfolio projects using weighted criteria (business value, risk, strategic alignment, available capacity).

### 🛡️ Production-ready
- Per-endpoint rate limiting
- Automated daily backups with retention
- Public status page with health checks
- Transactional email (Resend) for alerts and notifications
- Full audit log of RBAC actions

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  nginx :3030          (frontend, static SPA-like)           │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────────────────────────┐
│  FastAPI :8088    (REST API · 100+ endpoints)               │
│   ├─ auth / RBAC                                            │
│   ├─ portfolio · CMDB · documents · forecasting             │
│   └─ Multi-agent router ──┐                                 │
└────────────┬──────────────┼──────────────┬──────────────────┘
             │              │              │
             │              │              │
┌────────────▼──┐   ┌───────▼────────┐   ┌─▼─────────────────┐
│ PostgreSQL 15 │   │ Anthropic API  │   │ Ollama / Flowise  │
│ (multi-schema)│   │ (Claude)       │   │ (local LLMs)      │
└───────────────┘   └────────────────┘   └───────────────────┘
```

---

## Quickstart

### Requirements
- Docker + Docker Compose
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com/))
- (Optional) Resend API key for email

### Install

```bash
git clone https://github.com/jamartineztelecoengineer84-dotcom/cognitive-pmo.git
cd cognitive-pmo

# Copy and fill in environment variables
cp .env.example .env
$EDITOR .env   # set DB_PASSWORD, ANTHROPIC_API_KEY, etc.

# Bring up all services
docker compose up -d

# Initialize schema and seeds (synthetic data)
docker compose exec postgres psql -U "$DB_USER" -d cognitive_pmo \
  -f /app/backend/init.sql
```

Once running:
- Frontend: <http://localhost:3030>
- API: <http://localhost:8088/docs> (auto-generated Swagger UI)

---

## Repository layout

```
cognitive-pmo/
├── backend/                  # FastAPI app
│   ├── main.py                 # entry-point
│   ├── auth.py · authz.py      # RBAC + audit log
│   ├── agents/                 # multi-agent system
│   │   ├── router.py · spawner.py
│   │   ├── task_advisor_worker.py
│   │   └── prompts/
│   ├── jobs/                   # APScheduler jobs (backup, alerts)
│   ├── migrations/             # versioned SQL DDL by phase
│   ├── *_schema.sql            # schemas (cmdb, rbac, tech_dashboard, ...)
│   └── requirements.txt
├── frontend/                 # nginx + vanilla HTML/JS
│   ├── index.html              # CEO Dashboard (main shell)
│   ├── gov-build.html          # Build view (project intake)
│   ├── gov-run.html            # Run view (delivery)
│   ├── gov-kanban-global.html  # cross-portfolio kanban
│   ├── doc/                    # document manager UI
│   └── nginx.conf
├── database/                 # phase-specific architecture migrations
├── seeds/                    # synthetic data to populate the demo
├── disenos-html/             # design iterations (mockups)
├── docs/                     # audits, roadmap, post-mortems
├── docker-compose.yml
├── .env.example
└── LICENSE
```

---

## Use cases worth highlighting

1. **Automated subtask decomposition with LLM**
   The task advisor agent analyzes a project description and proposes subtasks, dependencies, and estimates. Fast iteration vs manual planning.
2. **RAG over corporate documentation**
   The user asks "what is our log retention policy according to DOC-RBAC-2025?" and the agent returns the answer with citations to the relevant repository documents.
3. **Team capacity forecasting**
   Prophet runs on historical person-hours-per-team series and predicts saturation 4–8 weeks in advance → input to the CIO/CFO Dashboard.
4. **Portfolio Prioritization Wizard**
   Weighted prioritization wizard with scenario simulation (Black Friday, product launch, budget restriction).

---

## Engineering practices

- **Database-first migrations.** Every architecture phase has idempotent versioned SQL DDL under `database/` and `backend/migrations/`. Re-runnable thanks to `IF NOT EXISTS` guards and validation triggers.
- **Async I/O end-to-end.** FastAPI + `asyncpg` with a connection pool — no blocking calls in critical endpoints.
- **RBAC with audit log.** Every mutation goes through `authz.py` and `require_permission(...)` decorators, and is recorded in `audit_log` with user + IP + timestamp.
- **Rate limiting + circuit breakers.** `slowapi` policies per endpoint, especially on LLM-backed routes for cost control.
- **Reproducible synthetic data.** Deterministic seeds in `seeds/seed_sc_*.sql` allow standing the demo up from scratch in under 5 minutes.
- **Pytest test suite** covering known technical debt (`backend/tests/test_arq02_*` and `test_deuda*`) — 30+ tests covering critical migrations and idempotency.
- **CI-friendly.** No hidden state: `docker compose down -v && docker compose up -d`, plus `docker compose exec api python seed_documentos.py`, and the demo is at 100%.

## Roadmap

- [ ] Migrate vanilla frontend to SvelteKit
- [ ] End-to-end OpenTelemetry tracing (FastAPI + asyncpg + Anthropic)
- [ ] Vector DB (pgvector) for persistent RAG embeddings
- [ ] Bidirectional integration with self-hosted Plane (issue sync)
- [ ] E2E tests with Playwright

---

## Disclaimer

All data shipped in seeds and migrations is **100% synthetic**. Names, emails (`@cognitivepmo.com`, `@bcc-bank.es`), applications, costs, and metrics are fictional. The project is inspired by the day-to-day operations of a PMO at a mid-sized financial organization, but contains no information about any real customer, employee, or system.

---

## Author

**Jose Antonio Martinez Victoria** — Telecommunications engineer · Architecture · Technology project management
GitHub: [@jamartineztelecoengineer84-dotcom](https://github.com/jamartineztelecoengineer84-dotcom)

## License

MIT — see [LICENSE](LICENSE).

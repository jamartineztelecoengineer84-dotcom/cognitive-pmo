# Cognitive PMO

> Plataforma de gestión PMO con agentes de IA — gobernanza de portfolio, gestor documental con RAG, dashboards ejecutivos y forecasting de capacidad.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL 15](https://img.shields.io/badge/postgres-15-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](https://docs.docker.com/compose/)

---

## Resumen

**Cognitive PMO** es una plataforma full-stack que automatiza la oficina de gestión de proyectos (PMO) de una organización tecnológica de tamaño medio. Combina:

- **Gestión de portfolio** (priorización, kanban global, gobernanza)
- **Agentes de IA** especializados (asesor de tareas, generador de documentos, decomposición automática de subtareas)
- **Gestor documental con RAG** sobre 750+ documentos
- **Dashboards ejecutivos** (CEO, CIO, CISO, CFO, CTO)
- **Forecasting de capacidad** con Prophet
- **CMDB integrada** con análisis de costes y cobertura de monitorización
- **RBAC + audit log** con notificaciones por email

Construido como caso de uso de un banco-demo (~600 empleados, datos 100% sintéticos) para demostrar arquitectura cloud-native, integración con LLMs y prácticas modernas de observabilidad.

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| **Backend** | Python 3.11 · FastAPI · asyncpg · Pydantic v2 |
| **Frontend** | HTML/JS vanilla · nginx · Tema oscuro/claro · 12+ vistas tipo dashboard |
| **Base de datos** | PostgreSQL 15 · multi-schema (RBAC + tenancy lógica) |
| **IA / LLMs** | Anthropic Claude API · Ollama local (gemma3) · Flowise para orquestación |
| **Forecasting** | Prophet (Meta) para predicción de capacidad y demanda |
| **Email** | Resend API · plantillas transaccionales |
| **Infraestructura** | Docker Compose · APScheduler · slowapi (rate limiting) |
| **Documentos** | PyPDF2 · python-docx · openpyxl · ReportLab |
| **Despliegue** | VPS on-premise · backups automáticos diarios · status page |

---

## Características destacadas

### 🤖 Sistema multi-agente
Router central que orquesta agentes especializados (`router.py`, `spawner.py`):
- **Task Advisor** — analiza el plan del proyecto y sugiere descomposición de subtareas
- **Document Agent (AG-DOC)** — busca, resume y compone respuestas sobre el repositorio documental
- **Excel/CSV Agent** — extrae y analiza datos tabulares (openpyxl + LLM local)
- **Sync Worker** — procesa eventos en background

### 📊 Dashboards ejecutivos
Vistas pre-construidas para roles C-level:
- **CEO Dashboard** (P97) — portfolio, KPIs financieros, alertas de gobernanza
- **CIO Dashboard** — health del CMDB, cobertura, riesgos técnicos
- **CISO Dashboard** — auditorías RBAC, cumplimiento, audit log
- **CFO Dashboard** — costes por aplicación, presupuesto vs real, forecast OPEX

### 📚 Gestor documental con RAG
- Indexa 750+ documentos del repositorio corporativo (PDF, DOCX, XLSX, TXT)
- Pipeline asíncrono de ingesta con metadatos
- Consulta natural mediante agente con LLM

### 📈 Portfolio Prioritization Wizard
Wizard de 4 fases para priorizar proyectos del portfolio aplicando criterios ponderados (valor de negocio, riesgo, alineación estratégica, capacidad disponible).

### 🛡️ Producción-ready
- Rate limiting por endpoint
- Backups automáticos diarios + retención
- Status page pública con health checks
- Email transaccional (Resend) para alertas + notificaciones
- Audit log completo de acciones RBAC

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│  nginx :3030          (frontend, static SPA-like)           │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────────────────────────┐
│  FastAPI :8088    (REST API · 100+ endpoints)               │
│   ├─ auth/RBAC                                              │
│   ├─ portfolio · CMDB · documental · forecasting            │
│   └─ Multi-agent router ──┐                                 │
└────────────┬──────────────┼──────────────┬──────────────────┘
             │              │              │
             │              │              │
┌────────────▼──┐   ┌───────▼────────┐   ┌─▼─────────────┐
│ PostgreSQL 15 │   │ Anthropic API  │   │ Ollama / Flowise│
│ (multi-schema)│   │ (Claude)       │   │ (LLMs locales)  │
└───────────────┘   └────────────────┘   └─────────────────┘
```

---

## Quickstart

### Requisitos
- Docker + Docker Compose
- Una API key de Anthropic ([console.anthropic.com](https://console.anthropic.com/))
- (Opcional) API key de Resend para emails

### Instalación

```bash
git clone https://github.com/jamartineztelecoengineer84-dotcom/cognitive-pmo.git
cd cognitive-pmo

# Copiar y rellenar variables de entorno
cp .env.example .env
$EDITOR .env   # rellena DB_PASSWORD, ANTHROPIC_API_KEY, etc.

# Levantar todos los servicios
docker compose up -d

# Inicializar el schema y los seeds (datos sintéticos)
docker compose exec postgres psql -U "$DB_USER" -d cognitive_pmo \
  -f /app/backend/init.sql
```

Una vez levantado:
- Frontend: <http://localhost:3030>
- API: <http://localhost:8088/docs> (Swagger UI auto-generada)

---

## Estructura del repositorio

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
│   ├── migrations/             # SQL DDL versionado por fase
│   ├── *_schema.sql            # schemas (cmdb, rbac, tech_dashboard, ...)
│   └── requirements.txt
├── frontend/                 # nginx + HTML/JS vanilla
│   ├── index.html              # CEO Dashboard (shell principal)
│   ├── gov-build.html          # vista Build (project intake)
│   ├── gov-run.html            # vista Run (delivery)
│   ├── gov-kanban-global.html  # kanban transversal
│   ├── doc/                    # gestor documental UI
│   └── nginx.conf
├── database/                 # migraciones específicas por fase de arquitectura
├── seeds/                    # datos sintéticos para popular la demo
├── disenos-html/             # iteraciones de diseño (mockups)
├── docs/                     # auditorías, roadmap, post-mortems
├── docker-compose.yml
├── .env.example
└── LICENSE
```

---

## Casos de uso destacados

1. **Decomposición automática de subtareas con LLM**
   El task advisor agent analiza la descripción de un proyecto y propone subtareas, dependencias y estimaciones. Iteración rápida frente a planificación manual.
2. **RAG sobre documentación corporativa**
   El usuario pregunta "¿cuál es nuestra política de retención de logs según la DOC-RBAC-2025?" y el agente devuelve la respuesta citando los documentos relevantes del repositorio.
3. **Forecasting de capacidad de equipo**
   Prophet sobre series históricas de horas-persona-mes por equipo predice saturación con 4-8 semanas de antelación → input al CIO/CFO Dashboard.
4. **Portfolio Prioritization Wizard**
   Wizard de priorización ponderada con simulación de escenarios (Black Friday, lanzamiento de producto, restricción de presupuesto).

---

## Engineering practices

- **Database-first migrations.** Cada fase de arquitectura tiene SQL DDL idempotente versionado bajo `database/` y `backend/migrations/`. Re-ejecutables con `IF NOT EXISTS` y triggers de validación.
- **Async I/O end-to-end.** FastAPI + `asyncpg` con pool, sin bloqueos en endpoints críticos.
- **RBAC con audit log.** Toda mutación atraviesa `authz.py`, decoradores `require_permission(...)`, y queda registrada en `audit_log` con usuario + IP + timestamp.
- **Rate limiting + circuit breakers.** `slowapi` con políticas por endpoint, especialmente en endpoints LLM-backed para controlar coste.
- **Datos sintéticos reproducibles.** Seeds determinísticos en `seeds/seed_sc_*.sql` permiten levantar la demo desde cero en <5 min.
- **Tests pytest** sobre la deuda técnica conocida del proyecto (carpeta `backend/tests/test_arq02_*` y `test_deuda*`) — 30+ tests cubriendo migraciones críticas e idempotencia.
- **CI-friendly.** Sin estado oculto: `docker compose down -v && docker compose up -d` + un `docker compose exec api python seed_documentos.py` y la demo está al 100%.

## Roadmap

- [ ] Migración del frontend vanilla a SvelteKit
- [ ] OpenTelemetry tracing end-to-end (FastAPI + asyncpg + Anthropic)
- [ ] Vector DB (pgvector) para RAG con embeddings persistentes
- [ ] Integración con Plane self-hosted vía API REST (gestión de issues bidirectional)
- [ ] Tests E2E con Playwright

---

## Disclaimer

Todos los datos incluidos en seeds y migraciones son **100% sintéticos**. Los nombres de personas, emails (`@cognitivepmo.com`, `@bcc-bank.es`), aplicaciones, costes y métricas son ficticios. El proyecto se inspira en la operativa real de un PMO en una organización financiera de tamaño medio, pero no contiene información de ningún cliente, empleado o sistema real.

---

## Autor

**Jose Antonio Martinez Victoria** — Ingeniero de telecomunicaciones · Arquitectura · Gestión de proyectos tecnológicos
GitHub: [@jamartineztelecoengineer84-dotcom](https://github.com/jamartineztelecoengineer84-dotcom)

## Licencia

MIT — ver [LICENSE](LICENSE).

# 01 — Resumen General

**Fecha de generación:** 2026-04-01  
**Versión actual:** v5.0  
**Último commit:** `cfe67dd v5.0 — Arquitectura Multi-Rol: Gobernadores RUN y BUILD`

---

## Qué es Cognitive PMO

Cognitive PMO es una plataforma de gobernanza IT para BCC Bank que combina gestión operativa (ITSM/RUN) y gestión de proyectos (PMO/BUILD) con 14 agentes de IA basados en Claude. La plataforma gestiona 150 técnicos, 46 proyectos, un CMDB con 148 activos, y automatiza el triaje de incidencias, la planificación de proyectos con metodología PMBOK/Scrum, y la gobernanza multi-rol mediante 3 vistas diferenciadas (Dirección, Coordinador RUN, Coordinador BUILD).

---

## Git Log Completo

```
cfe67dd v5.0 — Arquitectura Multi-Rol: Gobernadores RUN y BUILD
11cf44e v4.3 - Fix tabs pantalla final + Quality Gates visual + safeParsePipelineData mejorado + build-pause-area dinámico
ffc0dd3 v4.2 - Fix nginx invertido + savePipelineState x10 + navegación P1-P5 + CSS steps header
f361763 v4.1 - Agent Spawning + Mega-Optimización + UX Pausas interactivas
74a2b1c v4.0 — Pipeline BUILD v2.0: 9 agentes + 4 pausas + Scrum + Advisor + BUILD LIVE sidebar
b4b2180 v4.0-backend — 14 agentes + 30 tools + 7 tablas BUILD v2.0
23e2f19 v3.6 - Panel lateral LIVE + Semaforo operativo + Contacto negocio
304f642 Cognitive PMO v3.5 - Pipeline RUN completo + Directorio Negocio
88b8d9b Cognitive PMO v3.4 - TFM Master Dirección Estratégica de Proyectos (UCAM)
```

---

## Estructura de Archivos

```
./backend/agent_prompts.py
./backend/agents/__init__.py
./backend/agents/config.py
./backend/agents/engine.py
./backend/agents/prompts/ag001_dispatcher.txt
./backend/agents/prompts/ag002_resource_mgr_run.txt
./backend/agents/prompts/ag003_demand_forecaster.txt
./backend/agents/prompts/ag004_buffer_gatekeeper.txt
./backend/agents/prompts/ag005_director.txt
./backend/agents/prompts/ag005_estratega.txt
./backend/agents/prompts/ag005_merger.txt
./backend/agents/prompts/ag005_worker.txt
./backend/agents/prompts/ag006_resource_mgr_pmo.txt
./backend/agents/prompts/ag007_director.txt
./backend/agents/prompts/ag007_merger.txt
./backend/agents/prompts/ag007_planificador.txt
./backend/agents/prompts/ag007_worker.txt
./backend/agents/prompts/ag012_task_advisor.txt
./backend/agents/prompts/ag013_director.txt
./backend/agents/prompts/ag013_merger.txt
./backend/agents/prompts/ag013_task_decomposer.txt
./backend/agents/prompts/ag013_worker.txt
./backend/agents/prompts/ag014_risk_analyzer.txt
./backend/agents/prompts/ag015_stakeholder_map.txt
./backend/agents/prompts/ag016_cost_analyzer.txt
./backend/agents/prompts/ag017_quality_gate.txt
./backend/agents/prompts/ag018_governance_advisor.txt
./backend/agents/router.py
./backend/agents/spawner.py
./backend/agents/sync_worker.py
./backend/agents/task_advisor_worker.py
./backend/agents/tools_cmdb.py
./backend/agents/tools.py
./backend/auth.py
./backend/cmdb_api.py
./backend/cmdb_costes_schema.sql
./backend/cmdb_ips_seed.sql
./backend/cmdb_schema.sql
./backend/cmdb_seed_extra.sql
./backend/database.py
./backend/db_loader.py
./backend/Dockerfile
./backend/init-admin-user.sql
./backend/init.sql
./backend/main.py
./backend/models.py
./backend/rbac_api.py
./backend/rbac_schema.sql
./backend/requirements.txt
./backend/war_room_api.py
./BD_cajamar_v4.sql
./docker-compose.yml
./.env
./frontend/gov-build.html
./frontend/gov-run.html
./frontend/index.html
./frontend/index.html.backup_pausa
./frontend/index.html.backup_v36
./frontend/index.html.backup_v40_backend
./frontend/login-bg.png
./frontend/nginx.conf
./frontend/nginx.conf.backup
./.gitignore
```

---

## Docker Compose

```yaml
version: '3.9'
services:
  api:
    build: ./backend
    ports:
      - "8088:8088"
    env_file: .env
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"
  frontend:
    image: nginx:alpine
    ports:
      - "3030:80"
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
      - ./frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - api
    restart: unless-stopped
```

**Nota:** PostgreSQL (`postgres-pmo`) corre como contenedor externo, no en este compose.

---

## Nginx Config

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # ─── ARCHIVOS ESTÁTICOS ───
    location ~* \.(html|css|js|ico|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot|map|json|txt|md)$ {
        try_files $uri =404;
        expires 1h;
        add_header Cache-Control "public, no-transform";
    }

    # ─── FLOWISE PROXY (prefijo /api/) ───
    location /api/ {
        proxy_pass http://api:8088/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 600s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 600s;
    }

    # ─── TODO LO DEMÁS → BACKEND ───
    location / {
        proxy_pass http://api:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 600s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 600s;
        client_max_body_size 500M;

        # Si el backend devuelve 404, sirve index.html (SPA fallback)
        proxy_intercept_errors on;
        error_page 404 = /index.html;
    }
}
```

---

## Variables de Entorno

```
DB_HOST=***
DB_PORT=***
DB_NAME=***
DB_USER=***
DB_PASSWORD=***
API_PORT=***
FRONTEND_PORT=***
FLOWISE_URL=***
ANTHROPIC_API_KEY=***
```

# Cognitive PMO v4.2 — Release Candidate TFM

## Requisitos
- Docker + Docker Compose
- Clave API de Anthropic (claude-sonnet-4-20250514)

## Despliegue rapido

### 1. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tu API key de Anthropic y passwords de PostgreSQL
nano .env
```

### 2. Levantar los servicios (BD vacia con estructura)
```bash
docker compose up -d
# Esperar ~15 segundos a que PostgreSQL cree las tablas
docker compose logs db | tail -5
```

### 3. Cargar los datos
```bash
# Cargar TODOS los datos de golpe:
./cargar_datos.sh

# O cargar tablas especificas:
./cargar_datos.sh pmo_staff_skills
./cargar_datos.sh cartera_build
./cargar_datos.sh catalogo_incidencias
```

### 4. Verificar
```bash
# Backend
curl http://localhost:8088/health

# Frontend
# Abrir en navegador: http://IP_DEL_SERVIDOR:3030
```

## Arquitectura
- **Frontend**: http://IP:3030 (nginx - vanilla JS SPA)
- **Backend API**: http://IP:8088 (FastAPI + asyncpg)
- **PostgreSQL**: localhost:5432 (46 tablas)
- **Agentes IA**: 14 agentes Claude Sonnet 4 (requiere ANTHROPIC_API_KEY)

## Estructura de archivos
```
cognitive-pmo-v4.2/
├── docker-compose.yml      # Orquestacion (con PostgreSQL incluido)
├── .env.example             # Variables de entorno (copiar a .env)
├── db_schema.sql            # Estructura de BD (se carga automaticamente)
├── db_data.sql              # TODOS los datos (carga manual con script)
├── db_tables/               # Datos por tabla individual
│   ├── pmo_staff_skills.sql
│   ├── cartera_build.sql
│   ├── catalogo_incidencias.sql
│   └── ... (46 archivos)
├── cargar_datos.sh          # Script de carga de datos
├── backend/                 # FastAPI + agentes IA
│   ├── main.py
│   ├── agents/
│   │   ├── config.py
│   │   ├── engine.py
│   │   ├── spawner.py
│   │   ├── tools.py
│   │   └── prompts/*.txt
│   └── ...
├── frontend/                # SPA vanilla JS
│   ├── index.html
│   └── nginx.conf
└── README.md
```

## Notas
- La BD arranca VACIA (solo estructura). Los datos se cargan con el script.
- El pipeline BUILD cuesta ~0.33 USD por ejecucion (API Anthropic).
- El pipeline RUN cuesta ~0.08 USD por ejecucion.
- Sin ANTHROPIC_API_KEY los agentes no funcionan, pero el resto de la app si.

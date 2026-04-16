# 02 — Base de Datos

**Motor:** PostgreSQL 15  
**Nombre:** cognitive_pmo  
**Total tablas:** 46  
**Generado:** 2026-04-01

---

## Inventario completo de tablas

| # | Tabla | Dominio | Filas |
|---|-------|---------|------:|
| 1 | `rbac_usuarios` | Auth/RBAC | 175 |
| 2 | `rbac_roles` | Auth/RBAC | 23 |
| 3 | `rbac_permisos` | Auth/RBAC | 87 |
| 4 | `rbac_role_permisos` | Auth/RBAC | 883 |
| 5 | `rbac_sesiones` | Auth/RBAC | 42 |
| 6 | `rbac_audit_log` | Auth/RBAC | 63 |
| 7 | `catalogo_incidencias` | RUN (ITSM) | 4575 |
| 8 | `catalogo_skills` | RUN (ITSM) | 100 |
| 9 | `incidencias` | RUN (ITSM) | 1 |
| 10 | `incidencias_run` | RUN (ITSM) | 69 |
| 11 | `incidencias_live` | RUN (ITSM) | 4 |
| 12 | `run_incident_plans` | RUN (ITSM) | 61 |
| 13 | `cartera_build` | BUILD (PMO) | 46 |
| 14 | `build_project_plans` | BUILD (PMO) | 74 |
| 15 | `build_subtasks` | BUILD (PMO) | 120 |
| 16 | `build_risks` | BUILD (PMO) | 154 |
| 17 | `build_stakeholders` | BUILD (PMO) | 210 |
| 18 | `build_quality_gates` | BUILD (PMO) | 60 |
| 19 | `build_sprints` | BUILD (PMO) | 35 |
| 20 | `build_sprint_items` | BUILD (PMO) | 99 |
| 21 | `build_live` | BUILD (PMO) | 5 |
| 22 | `kanban_tareas` | Kanban | 493 |
| 23 | `cmdb_activos` | CMDB | 148 |
| 24 | `cmdb_categorias` | CMDB | 32 |
| 25 | `cmdb_relaciones` | CMDB | 55 |
| 26 | `cmdb_software` | CMDB | 30 |
| 27 | `cmdb_ips` | CMDB | 111 |
| 28 | `cmdb_vlans` | CMDB | 23 |
| 29 | `cmdb_costes` | CMDB | 40 |
| 30 | `cmdb_activo_software` | CMDB | 0 |
| 31 | `cmdb_cambios` | CMDB | 0 |
| 32 | `pmo_staff_skills` | PMO/Governance | 150 |
| 33 | `pmo_project_managers` | PMO/Governance | 15 |
| 34 | `pmo_governance_scoring` | PMO/Governance | 46 |
| 35 | `presupuestos` | PMO/Governance | 59 |
| 36 | `directorio_corporativo` | PMO/Governance | 479 |
| 37 | `gobernanza_transacciones` | PMO/Governance | 0 |
| 38 | `pipeline_sessions` | PMO/Governance | 3 |
| 39 | `war_room_sessions` | War Room | 3 |
| 40 | `intelligent_alerts` | War Room | 10 |
| 41 | `compliance_audits` | War Room | 10 |
| 42 | `postmortem_reports` | War Room | 4 |
| 43 | `whatif_simulations` | War Room | 2 |
| 44 | `agent_conversations` | Agents | 1428 |
| 45 | `agent_performance_metrics` | Agents | 142 |
| 46 | `documentacion_repositorio` | Docs | 23 |

**Total filas:** ~10.248

---

## 1. Auth / RBAC (6 tablas)

Sistema de autenticacion y control de acceso basado en roles.

### 1.1 rbac_usuarios (175 filas)

Usuarios del sistema con vinculacion a recurso tecnico, PM o directivo.

```sql
CREATE TABLE public.rbac_usuarios (
    id_usuario integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    nombre_completo character varying(200) NOT NULL,
    avatar_url character varying(500),
    id_role integer,
    id_recurso character varying(20),
    id_pm character varying(20),
    id_directivo character varying(20),
    departamento character varying(100),
    cargo character varying(150),
    telefono character varying(30),
    ultimo_login timestamp without time zone,
    login_count integer DEFAULT 0,
    activo boolean DEFAULT true,
    requiere_cambio_password boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);
-- PK: id_usuario
-- UNIQUE: email
```

### 1.2 rbac_roles (23 filas)

Roles con nivel jerarquico para herencia de permisos.

```sql
CREATE TABLE public.rbac_roles (
    id_role integer NOT NULL,
    code character varying(50) NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    nivel_jerarquico integer DEFAULT 0 NOT NULL,
    color character varying(7) DEFAULT '#6B7280',
    icono character varying(50) DEFAULT 'shield',
    activo boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now()
);
-- PK: id_role
-- UNIQUE: code
```

### 1.3 rbac_permisos (87 filas)

Permisos granulares por modulo y accion.

```sql
CREATE TABLE public.rbac_permisos (
    id_permiso integer NOT NULL,
    code character varying(100) NOT NULL,
    modulo character varying(50) NOT NULL,
    accion character varying(30) NOT NULL,
    descripcion text,
    criticidad character varying(10) DEFAULT 'MEDIA',
    CONSTRAINT rbac_permisos_accion_check CHECK (accion IN
        ('ver','crear','editar','eliminar','aprobar','exportar','ejecutar','admin')),
    CONSTRAINT rbac_permisos_criticidad_check CHECK (criticidad IN
        ('BAJA','MEDIA','ALTA','CRITICA'))
);
-- PK: id_permiso
-- UNIQUE: code
```

### 1.4 rbac_role_permisos (883 filas)

Tabla de cruce rol-permiso (N:M).

```sql
CREATE TABLE public.rbac_role_permisos (
    id_role integer NOT NULL,
    id_permiso integer NOT NULL
);
-- PK: (id_role, id_permiso)
```

### 1.5 rbac_sesiones (42 filas)

Sesiones activas con token hash y TTL.

```sql
CREATE TABLE public.rbac_sesiones (
    id_sesion integer NOT NULL,
    id_usuario integer,
    token_hash character varying(255) NOT NULL,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp without time zone DEFAULT now(),
    expires_at timestamp without time zone NOT NULL,
    activa boolean DEFAULT true
);
-- PK: id_sesion
```

### 1.6 rbac_audit_log (63 filas)

Traza de auditoria de todas las acciones del sistema.

```sql
CREATE TABLE public.rbac_audit_log (
    id_log integer NOT NULL,
    id_usuario integer,
    email character varying(255),
    accion character varying(50) NOT NULL,
    modulo character varying(50),
    recurso character varying(200),
    detalle jsonb DEFAULT '{}',
    ip_address character varying(45),
    resultado character varying(20) DEFAULT 'OK',
    "timestamp" timestamp without time zone DEFAULT now(),
    CONSTRAINT rbac_audit_log_resultado_check CHECK (resultado IN ('OK','DENEGADO','ERROR'))
);
-- PK: id_log
```

---

## 2. RUN / ITSM (6 tablas)

Gestion de incidencias con clasificacion IA, SLA y planes de resolucion.

### 2.1 catalogo_incidencias (4575 filas)

61 tipos unicos de incidencia con skills requeridas, SLA y prioridad sugerida.

```sql
CREATE TABLE public.catalogo_incidencias (
    id_catalogo integer NOT NULL,
    incidencia text NOT NULL,
    total_skills_requeridas integer DEFAULT 0,
    complejidad character varying(20) NOT NULL,
    skills_requeridas jsonb DEFAULT '[]' NOT NULL,
    prioridad_sugerida character varying(5) DEFAULT 'P3',
    nivel_minimo character varying(10) DEFAULT 'N2',
    sla_objetivo_horas numeric(5,1),
    area_afectada text,
    CONSTRAINT catalogo_incidencias_complejidad_check CHECK (complejidad IN
        ('Simple','Media','Compleja'))
);
-- PK: id_catalogo
-- INDEX: idx_catalogo_trgm GIN (incidencia gin_trgm_ops)
```

### 2.2 catalogo_skills (100 filas)

Catalogo maestro de skills tecnicas organizadas por silo.

```sql
CREATE TABLE public.catalogo_skills (
    id_skill integer NOT NULL,
    nombre_skill character varying(100) NOT NULL,
    categoria character varying(50) NOT NULL,
    silo character varying(50) NOT NULL
);
-- PK: id_skill
-- UNIQUE: nombre_skill
```

### 2.3 incidencias (1 fila)

Tabla legacy de incidencias (sustituida por incidencias_run).

```sql
CREATE TABLE public.incidencias (
    id_incidencia character varying NOT NULL,
    descripcion text,
    prioridad character varying,
    categoria character varying,
    estado character varying DEFAULT 'QUEUED',
    sla_limite character varying,
    tecnico_asignado character varying,
    fecha_creacion timestamp without time zone DEFAULT now(),
    flag_build_vs_run boolean DEFAULT false,
    impacto_negocio character varying
);
-- PK: id_incidencia
```

### 2.4 incidencias_run (69 filas)

Incidencias ITSM con campos ITIL4 completos.

```sql
CREATE TABLE public.incidencias_run (
    ticket_id character varying(30) NOT NULL,
    incidencia_detectada text NOT NULL,
    id_catalogo integer,
    prioridad_ia character varying(5) NOT NULL,
    categoria character varying(100),
    estado character varying(30) DEFAULT 'QUEUED',
    sla_limite numeric(5,1),
    tecnico_asignado character varying(20),
    impacto_negocio text,
    area_afectada text,
    flag_reasignacion boolean DEFAULT false,
    timestamp_creacion timestamp without time zone DEFAULT now(),
    timestamp_asignacion timestamp without time zone,
    timestamp_resolucion timestamp without time zone,
    tiempo_resolucion_minutos integer,
    agente_origen character varying(20) DEFAULT 'AG-001',
    urgencia character varying(10) DEFAULT 'Media',
    impacto character varying(10) DEFAULT 'Medio',
    canal_entrada character varying(30) DEFAULT 'Portal ITSM',
    reportado_por character varying(100),
    servicio_afectado character varying(100),
    ci_afectado character varying(100),
    notas_adicionales text,
    CONSTRAINT incidencias_run_estado_check CHECK (estado IN
        ('QUEUED','EN_CURSO','ESCALADO','RESUELTO','CERRADO')),
    CONSTRAINT incidencias_run_prioridad_ia_check CHECK (prioridad_ia IN
        ('P1','P2','P3','P4'))
);
-- PK: ticket_id
```

### 2.5 incidencias_live (4 filas)

Incidencias activas en curso con seguimiento en tiempo real.

```sql
CREATE TABLE public.incidencias_live (
    ticket_id character varying NOT NULL,
    incidencia_detectada text NOT NULL,
    prioridad character varying DEFAULT 'P4' NOT NULL,
    categoria character varying,
    estado character varying DEFAULT 'IN_PROGRESS',
    sla_horas numeric DEFAULT 48,
    tecnico_asignado character varying,
    area_afectada text,
    fecha_creacion timestamp without time zone DEFAULT now(),
    fecha_limite timestamp without time zone,
    progreso_pct integer DEFAULT 0,
    total_tareas integer DEFAULT 0,
    tareas_completadas integer DEFAULT 0,
    agente_origen character varying DEFAULT 'AG-001',
    canal_entrada character varying,
    reportado_por character varying,
    servicio_afectado character varying,
    impacto_negocio character varying,
    notas text
);
-- PK: ticket_id
```

### 2.6 run_incident_plans (61 filas)

Planes de resolucion generados por IA para incidencias.

```sql
CREATE TABLE public.run_incident_plans (
    id character varying(30) NOT NULL,
    ticket_id character varying(30),
    nombre text NOT NULL,
    prioridad character varying(5) DEFAULT 'P3',
    area character varying(30),
    sla_horas numeric(5,1),
    plan_data jsonb DEFAULT '{}' NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);
-- PK: id
```

---

## 3. BUILD / PMO (9 tablas)

Pipeline de proyectos con planificacion IA, Scrum, riesgos y quality gates.

### 3.1 cartera_build (46 filas)

Portafolio de proyectos con estados y prioridad estrategica.

```sql
CREATE TABLE public.cartera_build (
    id_proyecto character varying(30) NOT NULL,
    nombre_proyecto text NOT NULL,
    prioridad_estrategica character varying(20) NOT NULL,
    horas_estimadas integer NOT NULL,
    skills_requeridas text,
    horas_por_skill text,
    estado character varying(30) DEFAULT 'Standby',
    perfil_requerido text,
    responsable_asignado character varying(20),
    horas_base integer,
    fecha_creacion timestamp without time zone DEFAULT now(),
    fecha_ultima_modificacion timestamp without time zone DEFAULT now(),
    motivo_pausa text,
    historial_estados jsonb DEFAULT '[]',
    CONSTRAINT cartera_build_estado_check CHECK (estado IN
        ('Standby','En analisis','pendiente','en revision','Aprobado',
         'en ejecucion','en cierre','cerrado','PAUSADO_POR_RIESGO_P1')),
    CONSTRAINT cartera_build_prioridad_estrategica_check CHECK (prioridad_estrategica IN
        ('Critica','Alta','Media','Baja'))
);
-- PK: id_proyecto
-- INDEX: idx_cartera_estado, idx_cartera_prioridad, idx_cartera_responsable
-- TRIGGER: fn_registrar_cambio_estado() ON UPDATE
```

### 3.2 build_project_plans (74 filas)

Planes de proyecto generados por IA (plan_data JSONB).

```sql
CREATE TABLE public.build_project_plans (
    id character varying(30) NOT NULL,
    id_proyecto character varying(30),
    nombre text NOT NULL,
    presupuesto numeric(12,2) DEFAULT 0,
    duracion_semanas integer DEFAULT 20,
    prioridad character varying(20) DEFAULT 'Media',
    plan_data jsonb DEFAULT '{}' NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);
-- PK: id
-- INDEX: idx_bpp_proyecto (id_proyecto)
```

### 3.3 build_subtasks (120 filas)

Subtareas tecnicas generadas por AG-013 con skills y componentes.

```sql
CREATE TABLE public.build_subtasks (
    id character varying DEFAULT gen_random_uuid()::text NOT NULL,
    id_proyecto character varying NOT NULL,
    id_tarea_padre character varying NOT NULL,
    titulo text NOT NULL,
    descripcion_tecnica text,
    tecnologia character varying,
    componente character varying,
    integracion_con character varying,
    horas_estimadas numeric DEFAULT 0,
    skill_requerido character varying,
    criterio_exito text,
    orden integer DEFAULT 0,
    story_points integer DEFAULT 0,
    estado character varying DEFAULT 'PENDIENTE',
    created_at timestamp without time zone DEFAULT now()
);
-- PK: id
```

### 3.4 build_risks (154 filas)

Matriz de riesgos generada por AG-014 con probabilidad x impacto.

```sql
CREATE TABLE public.build_risks (
    id character varying DEFAULT gen_random_uuid()::text NOT NULL,
    id_proyecto character varying NOT NULL,
    descripcion text NOT NULL,
    categoria character varying DEFAULT 'Tecnico' NOT NULL,
    probabilidad integer DEFAULT 3,
    impacto integer DEFAULT 3,
    score numeric GENERATED ALWAYS AS (probabilidad * impacto) STORED,
    plan_mitigacion text,
    plan_contingencia text,
    responsable character varying,
    trigger_evento text,
    estado character varying DEFAULT 'ABIERTO',
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT build_risks_impacto_check CHECK (impacto BETWEEN 1 AND 5),
    CONSTRAINT build_risks_probabilidad_check CHECK (probabilidad BETWEEN 1 AND 5)
);
-- PK: id
```

### 3.5 build_stakeholders (210 filas)

Mapa de stakeholders generado por AG-015 con poder/interes y RACI.

```sql
CREATE TABLE public.build_stakeholders (
    id character varying DEFAULT gen_random_uuid()::text NOT NULL,
    id_proyecto character varying NOT NULL,
    nombre character varying NOT NULL,
    cargo character varying,
    area character varying,
    nivel_poder integer DEFAULT 3,
    nivel_interes integer DEFAULT 3,
    estrategia character varying DEFAULT 'Monitorizar',
    rol_raci character varying DEFAULT 'I',
    frecuencia_comunicacion character varying DEFAULT 'Mensual',
    canal character varying DEFAULT 'Email',
    id_directivo character varying,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT build_stakeholders_nivel_interes_check CHECK (nivel_interes BETWEEN 1 AND 5),
    CONSTRAINT build_stakeholders_nivel_poder_check CHECK (nivel_poder BETWEEN 1 AND 5)
);
-- PK: id
```

### 3.6 build_quality_gates (60 filas)

Quality gates por fase generados por AG-017 con criterios y DoD.

```sql
CREATE TABLE public.build_quality_gates (
    id character varying DEFAULT gen_random_uuid()::text NOT NULL,
    id_proyecto character varying NOT NULL,
    fase character varying NOT NULL,
    gate_name character varying NOT NULL,
    criterios_json jsonb DEFAULT '[]',
    checklist_json jsonb DEFAULT '[]',
    dod_json jsonb DEFAULT '[]',
    responsable_qa character varying,
    estado character varying DEFAULT 'PENDING',
    fecha_revision date,
    notas text,
    created_at timestamp without time zone DEFAULT now()
);
-- PK: id
```

### 3.7 build_sprints (35 filas)

Sprints Scrum generados por AG-007 con burndown y velocity.

```sql
CREATE TABLE public.build_sprints (
    id character varying DEFAULT gen_random_uuid()::text NOT NULL,
    id_proyecto character varying NOT NULL,
    sprint_number integer NOT NULL,
    nombre character varying,
    sprint_goal text,
    fecha_inicio date,
    fecha_fin date,
    story_points_planificados integer DEFAULT 0,
    story_points_completados integer DEFAULT 0,
    estado character varying DEFAULT 'PLANIFICADO',
    burndown_data jsonb DEFAULT '[]',
    velocity integer DEFAULT 0,
    notas_retro text,
    created_at timestamp without time zone DEFAULT now()
);
-- PK: id
```

### 3.8 build_sprint_items (99 filas)

Items de backlog asignados a sprints con story points y DoD.

```sql
CREATE TABLE public.build_sprint_items (
    id character varying DEFAULT gen_random_uuid()::text NOT NULL,
    id_proyecto character varying NOT NULL,
    id_sprint character varying,
    sprint_number integer,
    item_key character varying NOT NULL,
    tipo character varying DEFAULT 'TASK',
    titulo text NOT NULL,
    descripcion text,
    silo character varying,
    prioridad character varying DEFAULT 'Media',
    story_points integer DEFAULT 0,
    estado character varying DEFAULT 'TODO',
    id_tecnico character varying,
    nombre_tecnico character varying,
    subtareas_total integer DEFAULT 0,
    subtareas_completadas integer DEFAULT 0,
    id_tarea_padre character varying,
    horas_estimadas numeric DEFAULT 0,
    horas_reales numeric DEFAULT 0,
    criterios_aceptacion jsonb DEFAULT '[]',
    dod_checklist jsonb DEFAULT '[]',
    bloqueador text,
    orden_backlog integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now()
);
-- PK: id
```

### 3.9 build_live (5 filas)

Dashboard de proyectos activos con metricas EVM y Scrum en tiempo real.

```sql
CREATE TABLE public.build_live (
    id_proyecto character varying NOT NULL,
    nombre text NOT NULL,
    pm_asignado character varying,
    prioridad character varying DEFAULT 'Media',
    estado character varying DEFAULT 'PLANIFICACION',
    fecha_inicio timestamp without time zone DEFAULT now(),
    fecha_fin_prevista timestamp without time zone,
    progreso_pct integer DEFAULT 0,
    total_tareas integer DEFAULT 0,
    tareas_completadas integer DEFAULT 0,
    sprint_actual integer DEFAULT 1,
    total_sprints integer DEFAULT 16,
    presupuesto_bac numeric DEFAULT 0,
    presupuesto_consumido numeric DEFAULT 0,
    risk_score numeric DEFAULT 0,
    gate_actual character varying DEFAULT 'G2-PLANIFICACION',
    story_points_total integer DEFAULT 0,
    story_points_completados integer DEFAULT 0,
    velocity_media numeric DEFAULT 0
);
-- PK: id_proyecto
```

---

## 4. Kanban (1 tabla)

Tablero Kanban unificado para tareas BUILD y RUN.

### 4.1 kanban_tareas (493 filas)

```sql
CREATE TABLE public.kanban_tareas (
    id character varying(30) NOT NULL,
    titulo text NOT NULL,
    descripcion text,
    tipo character varying(10) NOT NULL,
    prioridad character varying(10) NOT NULL,
    columna character varying(30) DEFAULT 'Backlog' NOT NULL,
    id_tecnico character varying(20),
    id_proyecto character varying(30),
    id_incidencia character varying(30),
    bloqueador text,
    horas_estimadas numeric(6,1) DEFAULT 0,
    horas_reales numeric(6,1) DEFAULT 0,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    fecha_inicio_ejecucion timestamp with time zone,
    fecha_cierre timestamp with time zone,
    historial_columnas jsonb DEFAULT '[]',
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT kanban_tareas_columna_check CHECK (columna IN
        ('Backlog','Analisis','En Progreso','Code Review','Testing',
         'Despliegue','Bloqueado','Completado')),
    CONSTRAINT kanban_tareas_prioridad_check CHECK (prioridad IN
        ('Critica','Alta','Media','Baja')),
    CONSTRAINT kanban_tareas_tipo_check CHECK (tipo IN ('RUN','BUILD'))
);
-- PK: id
```

---

## 5. CMDB (9 tablas)

Configuration Management Database con activos, red, software y costes.

### 5.1 cmdb_activos (148 filas)

Activos IT con ciclo de vida, criticidad y especificaciones JSONB.

```sql
CREATE TABLE public.cmdb_activos (
    id_activo integer NOT NULL,
    codigo character varying(30) NOT NULL,
    nombre character varying(200) NOT NULL,
    id_categoria integer,
    capa character varying(30) NOT NULL,
    tipo character varying(80) NOT NULL,
    subtipo character varying(80),
    estado_ciclo character varying(20) DEFAULT 'OPERATIVO',
    criticidad character varying(10) DEFAULT 'MEDIA',
    entorno character varying(20) DEFAULT 'PRODUCCION',
    ubicacion character varying(100),
    propietario character varying(100),
    responsable_tecnico character varying(100),
    proveedor character varying(100),
    fabricante character varying(100),
    modelo character varying(100),
    version character varying(50),
    serial_number character varying(100),
    fecha_adquisicion date,
    fecha_fin_soporte date,
    fecha_fin_vida date,
    coste_adquisicion numeric(12,2) DEFAULT 0,
    coste_mensual numeric(10,2) DEFAULT 0,
    id_proyecto character varying(50),
    notas text,
    tags text[] DEFAULT '{}',
    especificaciones jsonb DEFAULT '{}',
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT cmdb_activos_capa_check CHECK (capa IN
        ('INFRAESTRUCTURA','APLICACION','RED','SEGURIDAD','NEGOCIO','SOPORTE')),
    CONSTRAINT cmdb_activos_criticidad_check CHECK (criticidad IN
        ('CRITICA','ALTA','MEDIA','BAJA')),
    CONSTRAINT cmdb_activos_entorno_check CHECK (entorno IN
        ('PRODUCCION','PREPRODUCCION','DESARROLLO','STAGING','DR','LAB')),
    CONSTRAINT cmdb_activos_estado_ciclo_check CHECK (estado_ciclo IN
        ('DISCOVERY','PLANIFICADO','DESPLEGANDO','OPERATIVO','DEGRADADO','MANTENIMIENTO','RETIRADO'))
);
-- PK: id_activo
-- UNIQUE: codigo
-- INDEX: idx_cmdb_activos_capa, idx_cmdb_activos_criticidad,
--         idx_cmdb_activos_estado, idx_cmdb_activos_proyecto, idx_cmdb_activos_tipo
```

### 5.2 cmdb_categorias (32 filas)

Categorias de activos por capa tecnologica.

```sql
CREATE TABLE public.cmdb_categorias (
    id_categoria integer NOT NULL,
    nombre character varying(100) NOT NULL,
    capa character varying(30) NOT NULL,
    icono character varying(50) DEFAULT 'server',
    color character varying(7) DEFAULT '#6B7280',
    CONSTRAINT cmdb_categorias_capa_check CHECK (capa IN
        ('INFRAESTRUCTURA','APLICACION','RED','SEGURIDAD','NEGOCIO','SOPORTE'))
);
-- PK: id_categoria
-- UNIQUE: nombre
```

### 5.3 cmdb_relaciones (55 filas)

Relaciones entre activos (dependencias, conexiones, proteccion).

```sql
CREATE TABLE public.cmdb_relaciones (
    id_relacion integer NOT NULL,
    id_activo_origen integer,
    id_activo_destino integer,
    tipo_relacion character varying(30) NOT NULL,
    descripcion character varying(200),
    criticidad character varying(10) DEFAULT 'MEDIA',
    CONSTRAINT cmdb_relaciones_tipo_relacion_check CHECK (tipo_relacion IN
        ('DEPENDE_DE','EJECUTA_EN','CONECTA_A','PROTEGE_A','RESPALDA_A',
         'MONITORIZA','PARTE_DE','SIRVE_A'))
);
-- PK: id_relacion
-- INDEX: idx_cmdb_relaciones_destino (id_activo_destino)
```

### 5.4 cmdb_software (30 filas)

Inventario de software con licencias y estado.

```sql
CREATE TABLE public.cmdb_software (
    id_software integer NOT NULL,
    nombre character varying(150) NOT NULL,
    version character varying(50),
    editor character varying(100),
    tipo_licencia character varying(30),
    num_licencias integer DEFAULT 0,
    licencias_usadas integer DEFAULT 0,
    coste_anual numeric(10,2) DEFAULT 0,
    fecha_renovacion date,
    estado character varying(15) DEFAULT 'ACTIVO',
    critico_negocio boolean DEFAULT false,
    CONSTRAINT cmdb_software_estado_check CHECK (estado IN
        ('ACTIVO','OBSOLETO','SIN_SOPORTE','EVALUACION','RETIRADO')),
    CONSTRAINT cmdb_software_tipo_licencia_check CHECK (tipo_licencia IN
        ('OPEN_SOURCE','COMERCIAL','SUSCRIPCION','FREEMIUM','CUSTOM','INTERNA'))
);
-- PK: id_software
```

### 5.5 cmdb_ips (111 filas)

Gestion de direcciones IP con asignacion a VLANs y activos.

```sql
CREATE TABLE public.cmdb_ips (
    id_ip integer NOT NULL,
    direccion_ip character varying(15) NOT NULL,
    id_vlan integer,
    id_activo integer,
    hostname character varying(100),
    tipo character varying(20) DEFAULT 'ESTATICA',
    estado character varying(15) DEFAULT 'ASIGNADA',
    mac_address character varying(17),
    puerto_switch character varying(30),
    notas character varying(200),
    ultima_vista timestamp without time zone DEFAULT now(),
    CONSTRAINT cmdb_ips_estado_check CHECK (estado IN
        ('LIBRE','ASIGNADA','RESERVADA','CONFLICTO')),
    CONSTRAINT cmdb_ips_tipo_check CHECK (tipo IN
        ('ESTATICA','DHCP','RESERVADA','VIRTUAL','VIP'))
);
-- PK: id_ip
-- UNIQUE: direccion_ip
-- INDEX: idx_cmdb_ips_activo, idx_cmdb_ips_vlan
```

### 5.6 cmdb_vlans (23 filas)

Gestion de VLANs con subredes y ocupacion.

```sql
CREATE TABLE public.cmdb_vlans (
    id_vlan integer NOT NULL,
    vlan_id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    subred character varying(18) NOT NULL,
    mascara character varying(15) DEFAULT '255.255.255.0',
    gateway character varying(15),
    entorno character varying(20) DEFAULT 'PRODUCCION',
    ubicacion character varying(100),
    estado character varying(15) DEFAULT 'ACTIVA',
    proposito character varying(50),
    total_ips integer DEFAULT 0,
    ips_usadas integer DEFAULT 0,
    CONSTRAINT cmdb_vlans_estado_check CHECK (estado IN
        ('ACTIVA','RESERVADA','DESACTIVADA'))
);
-- PK: id_vlan
-- UNIQUE: vlan_id
```

### 5.7 cmdb_costes (40 filas)

Costes IT con desglose CAPEX/OPEX y periodicidad.

```sql
CREATE TABLE public.cmdb_costes (
    id_coste integer NOT NULL,
    id_activo integer,
    concepto character varying(200) NOT NULL,
    categoria character varying(30),
    tipo character varying(10),
    importe numeric(12,2) NOT NULL,
    moneda character varying(3) DEFAULT 'EUR',
    periodicidad character varying(15) DEFAULT 'MENSUAL',
    fecha_inicio date,
    fecha_fin date,
    proveedor character varying(100),
    centro_coste character varying(50),
    id_proyecto character varying(50),
    notas text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT cmdb_costes_categoria_check CHECK (categoria IN
        ('HARDWARE','SOFTWARE','CLOUD','LICENCIAS','MANTENIMIENTO',
         'SOPORTE','RRHH','CONSULTORIA','FORMACION','OTROS')),
    CONSTRAINT cmdb_costes_periodicidad_check CHECK (periodicidad IN
        ('UNICO','MENSUAL','TRIMESTRAL','ANUAL')),
    CONSTRAINT cmdb_costes_tipo_check CHECK (tipo IN ('CAPEX','OPEX'))
);
-- PK: id_coste
```

### 5.8 cmdb_activo_software (0 filas)

Tabla de cruce activo-software (N:M).

```sql
CREATE TABLE public.cmdb_activo_software (
    id_activo integer NOT NULL,
    id_software integer NOT NULL,
    version_instalada character varying(50),
    fecha_instalacion date DEFAULT CURRENT_DATE
);
-- PK: (id_activo, id_software)
```

### 5.9 cmdb_cambios (0 filas)

Log de cambios sobre activos CMDB.

```sql
CREATE TABLE public.cmdb_cambios (
    id_cambio integer NOT NULL,
    id_activo integer,
    tipo_cambio character varying(30) NOT NULL,
    descripcion text,
    realizado_por character varying(100),
    fecha timestamp without time zone DEFAULT now(),
    datos_antes jsonb,
    datos_despues jsonb
);
-- PK: id_cambio
```

---

## 6. PMO / Governance (7 tablas)

Recursos humanos, scoring de proyectos, presupuestos y directorio corporativo.

### 6.1 pmo_staff_skills (150 filas)

150 tecnicos con skills, nivel (N1-N4), silo y carga de trabajo.

```sql
CREATE TABLE public.pmo_staff_skills (
    id_recurso character varying(20) NOT NULL,
    nombre text NOT NULL,
    nivel character varying(10) NOT NULL,
    silo_especialidad character varying(50) NOT NULL,
    total_skills integer DEFAULT 0,
    skills_json jsonb DEFAULT '[]' NOT NULL,
    skill_principal character varying(100),
    carga_actual integer DEFAULT 0,
    estado_run character varying(20) DEFAULT 'DISPONIBLE',
    fecha_alta date DEFAULT CURRENT_DATE,
    fecha_ultima_asignacion timestamp without time zone,
    incidencias_resueltas integer DEFAULT 0,
    email character varying(100),
    telefono character varying(20),
    CONSTRAINT pmo_staff_skills_carga_actual_check CHECK (carga_actual BETWEEN 0 AND 200),
    CONSTRAINT pmo_staff_skills_estado_run_check CHECK (estado_run IN
        ('DISPONIBLE','OCUPADO','GUARDIA','BAJA','VACACIONES')),
    CONSTRAINT pmo_staff_skills_nivel_check CHECK (nivel IN ('N1','N2','N3','N4')),
    CONSTRAINT pmo_staff_skills_silo_especialidad_check CHECK (silo_especialidad IN
        ('Frontend','Soporte','Redes','Windows','Backend','QA','DevOps','Seguridad','BBDD'))
);
-- PK: id_recurso
-- FUNCTION: buscar_tecnico_por_skill(p_skill, p_nivel_minimo)
```

### 6.2 pmo_project_managers (15 filas)

Project Managers con certificaciones, scoring y capacidad.

```sql
CREATE TABLE public.pmo_project_managers (
    id_pm character varying(20) NOT NULL,
    nombre text NOT NULL,
    nivel character varying(10) NOT NULL,
    especialidad character varying(50) NOT NULL,
    skills_json jsonb DEFAULT '[]' NOT NULL,
    skill_principal character varying(100),
    total_skills integer DEFAULT 0,
    estado character varying(20) DEFAULT 'DISPONIBLE',
    max_proyectos integer DEFAULT 3,
    email character varying(100),
    telefono character varying(20),
    certificaciones text[] DEFAULT '{}',
    fecha_alta date DEFAULT CURRENT_DATE,
    scoring_promedio numeric(4,2) DEFAULT 0,
    proyectos_completados integer DEFAULT 0,
    proyectos_activos integer DEFAULT 0,
    tasa_exito numeric(5,2) DEFAULT 100.00,
    carga_actual integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT pmo_project_managers_carga_actual_check CHECK (carga_actual BETWEEN 0 AND 200),
    CONSTRAINT pmo_project_managers_estado_check CHECK (estado IN
        ('DISPONIBLE','ASIGNADO','SOBRECARGADO','BAJA','VACACIONES')),
    CONSTRAINT pmo_project_managers_nivel_check CHECK (nivel IN
        ('PM-Jr','PM-Sr','PM-Lead','PM-Dir'))
);
-- PK: id_pm
```

### 6.3 pmo_governance_scoring (46 filas)

Scoring de proyectos con ROI, riesgo, capacidad, EVM y gates.

```sql
CREATE TABLE public.pmo_governance_scoring (
    id character varying(50) DEFAULT gen_random_uuid()::text NOT NULL,
    id_proyecto character varying(30) NOT NULL,
    id_pm character varying(20),
    roi_score numeric(4,2) DEFAULT 0,
    risk_score numeric(4,2) DEFAULT 0,
    capacity_score numeric(4,2) DEFAULT 0,
    strategic_value numeric(4,2) DEFAULT 0,
    total_score numeric(4,2) DEFAULT 0,
    gate_status character varying(20) DEFAULT 'PENDING',
    current_gate character varying(20) DEFAULT 'G0-IDEA',
    gate_history jsonb DEFAULT '[]',
    change_requests integer DEFAULT 0,
    change_approved integer DEFAULT 0,
    compliance_pct numeric(5,2) DEFAULT 0,
    last_review_date date,
    next_review_date date,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    roi_esperado numeric DEFAULT 0,
    payback_meses integer DEFAULT 0,
    tir numeric DEFAULT 0,
    van numeric DEFAULT 0,
    evm_bac numeric DEFAULT 0,
    evm_pv_json jsonb DEFAULT '[]',
    total_sprints integer DEFAULT 0,
    story_points_total integer DEFAULT 0,
    CONSTRAINT pmo_governance_scoring_capacity_score_check CHECK (capacity_score BETWEEN 0 AND 10),
    CONSTRAINT pmo_governance_scoring_gate_status_check CHECK (gate_status IN
        ('PENDING','APPROVED','HOLD','REJECTED','COMPLETED')),
    CONSTRAINT pmo_governance_scoring_risk_score_check CHECK (risk_score BETWEEN 0 AND 10),
    CONSTRAINT pmo_governance_scoring_roi_score_check CHECK (roi_score BETWEEN 0 AND 10),
    CONSTRAINT pmo_governance_scoring_strategic_value_check CHECK (strategic_value BETWEEN 0 AND 10)
);
-- PK: id
```

### 6.4 presupuestos (59 filas)

Presupuestos de proyecto con desglose CAPEX/OPEX/RRHH y BAC.

```sql
CREATE TABLE public.presupuestos (
    id_presupuesto character varying(30) NOT NULL,
    id_proyecto character varying(100) NOT NULL,
    nombre_presupuesto character varying(200) NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    estado character varying(20) DEFAULT 'BORRADOR' NOT NULL,
    responsable character varying(100) NOT NULL,
    fecha_inicio date,
    fecha_fin date,
    moneda character varying(3) DEFAULT 'EUR' NOT NULL,
    horas_internas numeric(10,2) DEFAULT 0 NOT NULL,
    tarifa_hora_interna numeric(10,2) DEFAULT 85.00 NOT NULL,
    proveedores_externos jsonb DEFAULT '[]' NOT NULL,
    opex_licencias_sw numeric(12,2) DEFAULT 0 NOT NULL,
    opex_cloud_infra numeric(12,2) DEFAULT 0 NOT NULL,
    opex_mantenimiento numeric(12,2) DEFAULT 0 NOT NULL,
    opex_consumibles numeric(12,2) DEFAULT 0 NOT NULL,
    opex_formacion numeric(12,2) DEFAULT 0 NOT NULL,
    opex_otros numeric(12,2) DEFAULT 0 NOT NULL,
    capex_hardware numeric(12,2) DEFAULT 0 NOT NULL,
    capex_equipamiento numeric(12,2) DEFAULT 0 NOT NULL,
    capex_infraestructura numeric(12,2) DEFAULT 0 NOT NULL,
    capex_software numeric(12,2) DEFAULT 0 NOT NULL,
    capex_otros numeric(12,2) DEFAULT 0 NOT NULL,
    rrhh_reclutamiento numeric(12,2) DEFAULT 0 NOT NULL,
    rrhh_formacion numeric(12,2) DEFAULT 0 NOT NULL,
    rrhh_hr_admin numeric(12,2) DEFAULT 0 NOT NULL,
    rrhh_viajes_dietas numeric(12,2) DEFAULT 0 NOT NULL,
    rrhh_otros numeric(12,2) DEFAULT 0 NOT NULL,
    reserva_contingencia_pct numeric(5,2) DEFAULT 10.0 NOT NULL,
    reserva_gestion_pct numeric(5,2) DEFAULT 5.0 NOT NULL,
    total_labor numeric(12,2) DEFAULT 0 NOT NULL,
    total_proveedores numeric(12,2) DEFAULT 0 NOT NULL,
    total_opex numeric(12,2) DEFAULT 0 NOT NULL,
    total_capex numeric(12,2) DEFAULT 0 NOT NULL,
    total_rrhh numeric(12,2) DEFAULT 0 NOT NULL,
    total_reservas numeric(12,2) DEFAULT 0 NOT NULL,
    bac_total numeric(12,2) DEFAULT 0 NOT NULL,
    aprobado_por character varying(100),
    fecha_aprobacion date,
    notas text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT presupuestos_estado_check CHECK (estado IN
        ('BORRADOR','EN_REVISION','APROBADO','CERRADO','RECHAZADO'))
);
-- PK: id_presupuesto
```

### 6.5 directorio_corporativo (479 filas)

Directorio de directivos con jerarquia organizativa.

```sql
CREATE TABLE public.directorio_corporativo (
    id_directivo character varying(20) NOT NULL,
    nombre_completo character varying(200) NOT NULL,
    cargo character varying(150) NOT NULL,
    nivel_organizativo character varying(30) NOT NULL,
    area character varying(100) NOT NULL,
    reporta_a character varying(20),
    email character varying(255) NOT NULL,
    telefono character varying(30),
    ubicacion character varying(100) DEFAULT 'Madrid HQ',
    fecha_incorporacion date DEFAULT CURRENT_DATE,
    activo boolean DEFAULT true,
    bio text,
    linkedin character varying(255),
    foto_url character varying(500),
    CONSTRAINT directorio_corporativo_nivel_organizativo_check CHECK (nivel_organizativo IN
        ('C-LEVEL','VP','DIRECTOR','SUBDIRECTOR','GERENTE','COORDINADOR','JEFE_EQUIPO'))
);
-- PK: id_directivo
-- UNIQUE: email
```

### 6.6 gobernanza_transacciones (0 filas)

Traza de auditoria de todas las decisiones de gobernanza.

```sql
CREATE TABLE public.gobernanza_transacciones (
    id_transaccion character varying(30) NOT NULL,
    tipo_accion character varying(30) NOT NULL,
    id_proyecto character varying(30),
    fte_afectado character varying(20),
    estado_anterior character varying(30),
    estado_nuevo character varying(30),
    motivo text,
    agente_origen character varying(20) NOT NULL,
    datos_contexto jsonb DEFAULT '{}',
    timestamp_ejecucion timestamp without time zone DEFAULT now(),
    usuario_db character varying(30) DEFAULT 'jose_admin',
    pending_sync jsonb DEFAULT '[]',
    depth integer DEFAULT 1,
    correlation_id character varying,
    retry_count integer DEFAULT 0,
    sync_status character varying DEFAULT 'PENDIENTE',
    CONSTRAINT gobernanza_transacciones_tipo_accion_check CHECK (tipo_accion IN
        ('PAUSA_PROYECTO','REANUDACION_PROYECTO','ASIGNACION_RECURSO',
         'LIBERACION_RECURSO','FREEZE_PERIOD','CAMBIO_ESTADO',
         'CREACION_PROYECTO','REASIGNACION_RECURSO','ASIGNACION_P1_CRITICA',
         'ASIGNACION_TECNICO','ESCALACION_BUFFER','SKILL_GAP',
         'TEAM_ADJUSTMENT','SUPERVISOR_ASSIGNED','REPLANIFICACION_PROYECTO'))
);
-- PK: id_transaccion
```

### 6.7 pipeline_sessions (3 filas)

Sesiones del pipeline BUILD con estado, agentes completados y coste.

```sql
CREATE TABLE public.pipeline_sessions (
    id character varying DEFAULT gen_random_uuid()::text NOT NULL,
    nombre_proyecto character varying DEFAULT '' NOT NULL,
    estado character varying DEFAULT 'EN_PROGRESO',
    pausa_actual integer DEFAULT 0,
    pipeline_data jsonb DEFAULT '{}' NOT NULL,
    business_case jsonb DEFAULT '{}',
    session_id character varying DEFAULT '',
    tiempo_acumulado_ms integer DEFAULT 0,
    coste_acumulado numeric DEFAULT 0,
    agentes_completados jsonb DEFAULT '[]',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);
-- PK: id
```

---

## 7. War Room (5 tablas)

Sala de crisis, alertas inteligentes, compliance, postmortem y simulaciones.

### 7.1 war_room_sessions (3 filas)

Sesiones de crisis, planificacion o revision.

```sql
CREATE TABLE public.war_room_sessions (
    id character varying(50) DEFAULT gen_random_uuid()::text NOT NULL,
    session_name character varying(200) NOT NULL,
    session_type character varying(30) NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE',
    participants jsonb DEFAULT '[]',
    context jsonb DEFAULT '{}',
    summary text,
    decisions jsonb DEFAULT '[]',
    started_at timestamp with time zone DEFAULT now(),
    closed_at timestamp with time zone,
    CONSTRAINT war_room_sessions_session_type_check CHECK (session_type IN
        ('CRISIS_P1','PLANNING','REVIEW','SIMULATION','AUDIT','AD_HOC')),
    CONSTRAINT war_room_sessions_status_check CHECK (status IN
        ('ACTIVE','PAUSED','CLOSED','ARCHIVED'))
);
-- PK: id
```

### 7.2 intelligent_alerts (10 filas)

Alertas generadas por agentes IA con severidad y acciones recomendadas.

```sql
CREATE TABLE public.intelligent_alerts (
    id character varying(50) DEFAULT gen_random_uuid()::text NOT NULL,
    alert_type character varying(50) NOT NULL,
    severity character varying(10) NOT NULL,
    title character varying(300) NOT NULL,
    description text NOT NULL,
    source_agent character varying(10) NOT NULL,
    affected_entities jsonb DEFAULT '{}' NOT NULL,
    trigger_condition jsonb DEFAULT '{}' NOT NULL,
    recommended_actions jsonb DEFAULT '[]',
    auto_resolved boolean DEFAULT false,
    acknowledged_by character varying(100),
    acknowledged_at timestamp with time zone,
    resolved_at timestamp with time zone,
    status character varying(20) DEFAULT 'ACTIVE',
    correlation_id character varying(50),
    parent_alert_id character varying(50),
    ttl_hours integer DEFAULT 24,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT intelligent_alerts_alert_type_check CHECK (alert_type IN
        ('SLA_RISK','OVERALLOCATION','SKILL_GAP','FREEZE_RECOMMENDED',
         'BUDGET_OVERRUN','MILESTONE_RISK','BURNOUT_RISK',
         'COMPLIANCE_BREACH','CASCADE_FAILURE','CAPACITY_THRESHOLD')),
    CONSTRAINT intelligent_alerts_severity_check CHECK (severity IN
        ('CRITICAL','HIGH','MEDIUM','LOW')),
    CONSTRAINT intelligent_alerts_status_check CHECK (status IN
        ('ACTIVE','ACKNOWLEDGED','RESOLVED','ESCALATED','SUPPRESSED'))
);
-- PK: id
-- INDEX: idx_alert_severity, idx_alert_source, idx_alert_status, idx_alert_type
```

### 7.3 compliance_audits (10 filas)

Hallazgos de auditoria de compliance generados por AG-008.

```sql
CREATE TABLE public.compliance_audits (
    id character varying(50) DEFAULT gen_random_uuid()::text NOT NULL,
    audit_type character varying(50) NOT NULL,
    entity_type character varying(30) NOT NULL,
    entity_id character varying(100) NOT NULL,
    severity character varying(10) NOT NULL,
    finding text NOT NULL,
    recommendation text,
    evidence jsonb DEFAULT '{}',
    status character varying(20) DEFAULT 'OPEN',
    assignee character varying(100),
    due_date date,
    resolved_at timestamp with time zone,
    created_by character varying(20) DEFAULT 'AG-008',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT compliance_audits_audit_type_check CHECK (audit_type IN
        ('ITIL4_SLA','PMBOK7_DELIVERABLE','GDPR_DATA','BCE_REGULATORY',
         'ISO27001_SECURITY','CNMV_REPORTING','DORA_RESILIENCE')),
    CONSTRAINT compliance_audits_severity_check CHECK (severity IN
        ('CRITICAL','HIGH','MEDIUM','LOW','INFO')),
    CONSTRAINT compliance_audits_status_check CHECK (status IN
        ('OPEN','IN_PROGRESS','RESOLVED','ACCEPTED','WAIVED'))
);
-- PK: id
-- INDEX: idx_audit_severity, idx_audit_status, idx_audit_type
```

### 7.4 postmortem_reports (4 filas)

Informes postmortem con timeline, root cause y acciones correctivas.

```sql
CREATE TABLE public.postmortem_reports (
    id character varying(50) DEFAULT gen_random_uuid()::text NOT NULL,
    incident_id character varying(50) NOT NULL,
    incident_priority character varying(5) NOT NULL,
    title character varying(300) NOT NULL,
    timeline jsonb DEFAULT '[]' NOT NULL,
    root_cause text NOT NULL,
    root_cause_category character varying(50),
    impact_assessment jsonb DEFAULT '{}' NOT NULL,
    corrective_actions jsonb DEFAULT '[]' NOT NULL,
    preventive_actions jsonb DEFAULT '[]' NOT NULL,
    lessons_learned text[] DEFAULT '{}',
    mttr_minutes integer,
    mtta_minutes integer,
    sla_breached boolean DEFAULT false,
    agents_involved character varying(10)[] DEFAULT '{}',
    resources_involved character varying(20)[] DEFAULT '{}',
    projects_impacted character varying(50)[] DEFAULT '{}',
    review_status character varying(20) DEFAULT 'DRAFT',
    approved_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT postmortem_reports_review_status_check CHECK (review_status IN
        ('DRAFT','REVIEW','APPROVED','ARCHIVED'))
);
-- PK: id
```

### 7.5 whatif_simulations (2 filas)

Simulaciones what-if con parametros, resultado y recomendaciones.

```sql
CREATE TABLE public.whatif_simulations (
    id character varying(50) DEFAULT gen_random_uuid()::text NOT NULL,
    simulation_name character varying(200) NOT NULL,
    scenario_type character varying(50) NOT NULL,
    input_params jsonb DEFAULT '{}' NOT NULL,
    baseline_snapshot jsonb DEFAULT '{}' NOT NULL,
    simulation_result jsonb DEFAULT '{}' NOT NULL,
    risk_score numeric(5,2) DEFAULT 0,
    confidence_level numeric(3,2) DEFAULT 0.7,
    recommendations text[] DEFAULT '{}',
    affected_projects character varying(50)[] DEFAULT '{}',
    affected_resources character varying(20)[] DEFAULT '{}',
    kpi_deltas jsonb DEFAULT '{}',
    created_by character varying(100) DEFAULT 'AG-010',
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT whatif_simulations_confidence_level_check CHECK (confidence_level BETWEEN 0 AND 1),
    CONSTRAINT whatif_simulations_risk_score_check CHECK (risk_score BETWEEN 0 AND 100),
    CONSTRAINT whatif_simulations_scenario_type_check CHECK (scenario_type IN
        ('RESOURCE_REALLOCATION','PROJECT_DELAY','P1_CASCADE','BUDGET_CUT',
         'TEAM_SCALING','FREEZE_PERIOD','SKILL_GAP','VENDOR_FAILURE','REGULATORY_CHANGE'))
);
-- PK: id
```

---

## 8. Agents (2 tablas)

Historial de conversaciones y metricas de rendimiento de los agentes IA.

### 8.1 agent_conversations (1428 filas)

Historial completo de mensajes de los agentes con tokens y latencia.

```sql
CREATE TABLE public.agent_conversations (
    id character varying(50) DEFAULT gen_random_uuid()::text NOT NULL,
    session_id character varying(50) DEFAULT gen_random_uuid()::text NOT NULL,
    agent_id character varying(10) NOT NULL,
    agent_name character varying(100) NOT NULL,
    role character varying(20) NOT NULL,
    content text NOT NULL,
    tokens_used integer DEFAULT 0,
    model_used character varying(50) DEFAULT 'claude-sonnet-4-20250514',
    latency_ms integer DEFAULT 0,
    metadata jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT agent_conversations_role_check CHECK (role IN
        ('user','assistant','system','tool'))
);
-- PK: id
```

### 8.2 agent_performance_metrics (142 filas)

KPIs diarios por agente: invocaciones, latencia, tokens, tasa de exito.

```sql
CREATE TABLE public.agent_performance_metrics (
    id character varying(50) DEFAULT gen_random_uuid()::text NOT NULL,
    agent_id character varying(10) NOT NULL,
    metric_date date DEFAULT CURRENT_DATE NOT NULL,
    total_invocations integer DEFAULT 0,
    avg_latency_ms numeric(10,2) DEFAULT 0,
    total_tokens_consumed bigint DEFAULT 0,
    success_rate numeric(5,2) DEFAULT 100.00,
    error_count integer DEFAULT 0,
    decisions_made integer DEFAULT 0,
    escalations_triggered integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now()
);
-- PK: id
-- UNIQUE: (agent_id, metric_date)
```

---

## 9. Docs (1 tabla)

Repositorio documental vinculado a proyectos e incidencias.

### 9.1 documentacion_repositorio (23 filas)

```sql
CREATE TABLE public.documentacion_repositorio (
    id integer NOT NULL,
    titulo character varying(255) NOT NULL,
    descripcion text,
    tipo character varying(50) NOT NULL,
    silo character varying(15) NOT NULL,
    departamento character varying(100),
    proyecto_id character varying(30),
    incidencia_id character varying(30),
    drive_file_id character varying(100),
    drive_folder_path character varying(500),
    drive_share_url character varying(500),
    mime_type character varying(100),
    archivo_nombre character varying(255),
    archivo_size integer DEFAULT 0,
    archivo_tipo character varying(10),
    tags text[] DEFAULT '{}',
    version integer DEFAULT 1,
    fecha_creacion timestamp with time zone DEFAULT now(),
    fecha_actualizacion timestamp with time zone DEFAULT now(),
    creado_por character varying(100),
    activo boolean DEFAULT true,
    CONSTRAINT documentacion_repositorio_silo_check CHECK (silo IN
        ('BUILD','RUN','TRANSVERSAL')),
    CONSTRAINT documentacion_repositorio_tipo_check CHECK (tipo IN
        ('proyecto','incidencia','gobernanza','formacion','herramienta','plantilla'))
);
-- PK: id
```

---

## Vistas materializadas

La base de datos incluye 4 vistas auxiliares:

| Vista | Descripcion |
|-------|------------|
| `view_disponibilidad_global` | Disponibilidad de tecnicos con incidencias y proyectos activos |
| `vista_audit_gobernanza` | Traza de gobernanza con nombres de proyecto y tecnico |
| `vista_carga_por_silo` | Carga media y disponibilidad agrupada por silo y nivel |
| `vista_portafolio_build` | Resumen del portafolio por estado y prioridad |
| `vista_proyectos_riesgo` | Proyectos pausados por riesgo P1 o sin responsable |
| `vista_serie_temporal_incidencias` | Serie temporal diaria de incidencias para forecasting |

## Funciones almacenadas

| Funcion | Tipo | Descripcion |
|---------|------|------------|
| `buscar_tecnico_por_skill(p_skill, p_nivel_minimo)` | RETURNS TABLE | Busca tecnicos disponibles por skill con scoring compuesto |
| `fn_registrar_cambio_estado()` | TRIGGER | Registra automaticamente cambios de estado en historial_estados (cartera_build) |

## Extension habilitada

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- Busqueda por similitud trigram en catalogo_incidencias
```

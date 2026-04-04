--
-- PostgreSQL database dump
--

\restrict pqkMpgHPStZNsafY1qkT5e27O1FUkq82c5FfsCEwdeJG30e7Y7kWLHtdVdDwJcV

-- Dumped from database version 15.16 (Debian 15.16-1.pgdg13+1)
-- Dumped by pg_dump version 15.17 (Debian 15.17-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: buscar_tecnico_por_skill(text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.buscar_tecnico_por_skill(p_skill text, p_nivel_minimo text DEFAULT 'N2'::text) RETURNS TABLE(id_recurso character varying, nombre text, nivel character varying, silo_especialidad character varying, carga_actual integer, estado_run character varying, match_score integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT s.id_recurso, s.nombre, s.nivel, s.silo_especialidad,
           s.carga_actual, s.estado_run,
           (CASE WHEN s.skills_json @> to_jsonb(p_skill)::jsonb THEN 100 ELSE 0 END + 
            CASE s.nivel WHEN 'N4' THEN 40 WHEN 'N3' THEN 30 WHEN 'N2' THEN 20 WHEN 'N1' THEN 10 END -
            s.carga_actual) as match_score
    FROM pmo_staff_skills s
    WHERE s.estado_run = 'DISPONIBLE'
      AND s.nivel >= p_nivel_minimo
      AND s.skills_json @> to_jsonb(p_skill)::jsonb
    ORDER BY match_score DESC
    LIMIT 10;
END;
$$;


--
-- Name: fn_registrar_cambio_estado(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_registrar_cambio_estado() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado THEN
        NEW.historial_estados = OLD.historial_estados || 
            jsonb_build_object(
                'estado_anterior', OLD.estado,
                'estado_nuevo', NEW.estado,
                'timestamp', NOW()::TEXT,
                'motivo', COALESCE(NEW.motivo_pausa, 'Cambio de estado')
            );
        NEW.fecha_ultima_modificacion = NOW();
    END IF;
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agent_conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agent_conversations (
    id character varying(50) DEFAULT (gen_random_uuid())::text NOT NULL,
    session_id character varying(50) DEFAULT (gen_random_uuid())::text NOT NULL,
    agent_id character varying(10) NOT NULL,
    agent_name character varying(100) NOT NULL,
    role character varying(20) NOT NULL,
    content text NOT NULL,
    tokens_used integer DEFAULT 0,
    model_used character varying(50) DEFAULT 'claude-sonnet-4-20250514'::character varying,
    latency_ms integer DEFAULT 0,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT agent_conversations_role_check CHECK (((role)::text = ANY ((ARRAY['user'::character varying, 'assistant'::character varying, 'system'::character varying, 'tool'::character varying])::text[])))
);


--
-- Name: agent_performance_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agent_performance_metrics (
    id character varying(50) DEFAULT (gen_random_uuid())::text NOT NULL,
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


--
-- Name: build_live; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.build_live (
    id_proyecto character varying NOT NULL,
    nombre text NOT NULL,
    pm_asignado character varying,
    prioridad character varying DEFAULT 'Media'::character varying,
    estado character varying DEFAULT 'PLANIFICACION'::character varying,
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
    gate_actual character varying DEFAULT 'G2-PLANIFICACION'::character varying,
    story_points_total integer DEFAULT 0,
    story_points_completados integer DEFAULT 0,
    velocity_media numeric DEFAULT 0
);


--
-- Name: build_project_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.build_project_plans (
    id character varying(30) NOT NULL,
    id_proyecto character varying(30),
    nombre text NOT NULL,
    presupuesto numeric(12,2) DEFAULT 0,
    duracion_semanas integer DEFAULT 20,
    prioridad character varying(20) DEFAULT 'Media'::character varying,
    plan_data jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: build_quality_gates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.build_quality_gates (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    id_proyecto character varying NOT NULL,
    fase character varying NOT NULL,
    gate_name character varying NOT NULL,
    criterios_json jsonb DEFAULT '[]'::jsonb,
    checklist_json jsonb DEFAULT '[]'::jsonb,
    dod_json jsonb DEFAULT '[]'::jsonb,
    responsable_qa character varying,
    estado character varying DEFAULT 'PENDING'::character varying,
    fecha_revision date,
    notas text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: build_risks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.build_risks (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    id_proyecto character varying NOT NULL,
    descripcion text NOT NULL,
    categoria character varying DEFAULT 'Técnico'::character varying NOT NULL,
    probabilidad integer DEFAULT 3,
    impacto integer DEFAULT 3,
    score numeric GENERATED ALWAYS AS ((probabilidad * impacto)) STORED,
    plan_mitigacion text,
    plan_contingencia text,
    responsable character varying,
    trigger_evento text,
    estado character varying DEFAULT 'ABIERTO'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT build_risks_impacto_check CHECK (((impacto >= 1) AND (impacto <= 5))),
    CONSTRAINT build_risks_probabilidad_check CHECK (((probabilidad >= 1) AND (probabilidad <= 5)))
);


--
-- Name: build_sprint_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.build_sprint_items (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    id_proyecto character varying NOT NULL,
    id_sprint character varying,
    sprint_number integer,
    item_key character varying NOT NULL,
    tipo character varying DEFAULT 'TASK'::character varying,
    titulo text NOT NULL,
    descripcion text,
    silo character varying,
    prioridad character varying DEFAULT 'Media'::character varying,
    story_points integer DEFAULT 0,
    estado character varying DEFAULT 'TODO'::character varying,
    id_tecnico character varying,
    nombre_tecnico character varying,
    subtareas_total integer DEFAULT 0,
    subtareas_completadas integer DEFAULT 0,
    id_tarea_padre character varying,
    horas_estimadas numeric DEFAULT 0,
    horas_reales numeric DEFAULT 0,
    criterios_aceptacion jsonb DEFAULT '[]'::jsonb,
    dod_checklist jsonb DEFAULT '[]'::jsonb,
    bloqueador text,
    orden_backlog integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: build_sprints; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.build_sprints (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    id_proyecto character varying NOT NULL,
    sprint_number integer NOT NULL,
    nombre character varying,
    sprint_goal text,
    fecha_inicio date,
    fecha_fin date,
    story_points_planificados integer DEFAULT 0,
    story_points_completados integer DEFAULT 0,
    estado character varying DEFAULT 'PLANIFICADO'::character varying,
    burndown_data jsonb DEFAULT '[]'::jsonb,
    velocity integer DEFAULT 0,
    notas_retro text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: build_stakeholders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.build_stakeholders (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    id_proyecto character varying NOT NULL,
    nombre character varying NOT NULL,
    cargo character varying,
    area character varying,
    nivel_poder integer DEFAULT 3,
    nivel_interes integer DEFAULT 3,
    estrategia character varying DEFAULT 'Monitorizar'::character varying,
    rol_raci character varying DEFAULT 'I'::character varying,
    frecuencia_comunicacion character varying DEFAULT 'Mensual'::character varying,
    canal character varying DEFAULT 'Email'::character varying,
    id_directivo character varying,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT build_stakeholders_nivel_interes_check CHECK (((nivel_interes >= 1) AND (nivel_interes <= 5))),
    CONSTRAINT build_stakeholders_nivel_poder_check CHECK (((nivel_poder >= 1) AND (nivel_poder <= 5)))
);


--
-- Name: build_subtasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.build_subtasks (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
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
    estado character varying DEFAULT 'PENDIENTE'::character varying,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: cartera_build; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cartera_build (
    id_proyecto character varying(30) NOT NULL,
    nombre_proyecto text NOT NULL,
    prioridad_estrategica character varying(20) NOT NULL,
    horas_estimadas integer NOT NULL,
    skills_requeridas text,
    horas_por_skill text,
    estado character varying(30) DEFAULT 'Standby'::character varying,
    perfil_requerido text,
    responsable_asignado character varying(20),
    horas_base integer,
    fecha_creacion timestamp without time zone DEFAULT now(),
    fecha_ultima_modificacion timestamp without time zone DEFAULT now(),
    motivo_pausa text,
    historial_estados jsonb DEFAULT '[]'::jsonb,
    CONSTRAINT cartera_build_estado_check CHECK (((estado)::text = ANY ((ARRAY['Standby'::character varying, 'En analisis'::character varying, 'pendiente'::character varying, 'en revision'::character varying, 'Aprobado'::character varying, 'en ejecucion'::character varying, 'en cierre'::character varying, 'cerrado'::character varying, 'PAUSADO_POR_RIESGO_P1'::character varying])::text[]))),
    CONSTRAINT cartera_build_prioridad_estrategica_check CHECK (((prioridad_estrategica)::text = ANY ((ARRAY['Crítica'::character varying, 'Alta'::character varying, 'Media'::character varying, 'Baja'::character varying])::text[])))
);


--
-- Name: catalogo_incidencias; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.catalogo_incidencias (
    id_catalogo integer NOT NULL,
    incidencia text NOT NULL,
    total_skills_requeridas integer DEFAULT 0,
    complejidad character varying(20) NOT NULL,
    skills_requeridas jsonb DEFAULT '[]'::jsonb NOT NULL,
    prioridad_sugerida character varying(5) DEFAULT 'P3'::character varying,
    nivel_minimo character varying(10) DEFAULT 'N2'::character varying,
    sla_objetivo_horas numeric(5,1),
    area_afectada text,
    CONSTRAINT catalogo_incidencias_complejidad_check CHECK (((complejidad)::text = ANY ((ARRAY['Simple'::character varying, 'Media'::character varying, 'Compleja'::character varying])::text[])))
);


--
-- Name: catalogo_incidencias_id_catalogo_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.catalogo_incidencias_id_catalogo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: catalogo_incidencias_id_catalogo_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.catalogo_incidencias_id_catalogo_seq OWNED BY public.catalogo_incidencias.id_catalogo;


--
-- Name: catalogo_skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.catalogo_skills (
    id_skill integer NOT NULL,
    nombre_skill character varying(100) NOT NULL,
    categoria character varying(50) NOT NULL,
    silo character varying(50) NOT NULL
);


--
-- Name: catalogo_skills_id_skill_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.catalogo_skills_id_skill_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: catalogo_skills_id_skill_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.catalogo_skills_id_skill_seq OWNED BY public.catalogo_skills.id_skill;


--
-- Name: cmdb_activo_software; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cmdb_activo_software (
    id_activo integer NOT NULL,
    id_software integer NOT NULL,
    version_instalada character varying(50),
    fecha_instalacion date DEFAULT CURRENT_DATE
);


--
-- Name: cmdb_activos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cmdb_activos (
    id_activo integer NOT NULL,
    codigo character varying(30) NOT NULL,
    nombre character varying(200) NOT NULL,
    id_categoria integer,
    capa character varying(30) NOT NULL,
    tipo character varying(80) NOT NULL,
    subtipo character varying(80),
    estado_ciclo character varying(20) DEFAULT 'OPERATIVO'::character varying,
    criticidad character varying(10) DEFAULT 'MEDIA'::character varying,
    entorno character varying(20) DEFAULT 'PRODUCCION'::character varying,
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
    tags text[] DEFAULT '{}'::text[],
    especificaciones jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT cmdb_activos_capa_check CHECK (((capa)::text = ANY ((ARRAY['INFRAESTRUCTURA'::character varying, 'APLICACION'::character varying, 'RED'::character varying, 'SEGURIDAD'::character varying, 'NEGOCIO'::character varying, 'SOPORTE'::character varying])::text[]))),
    CONSTRAINT cmdb_activos_criticidad_check CHECK (((criticidad)::text = ANY ((ARRAY['CRITICA'::character varying, 'ALTA'::character varying, 'MEDIA'::character varying, 'BAJA'::character varying])::text[]))),
    CONSTRAINT cmdb_activos_entorno_check CHECK (((entorno)::text = ANY ((ARRAY['PRODUCCION'::character varying, 'PREPRODUCCION'::character varying, 'DESARROLLO'::character varying, 'STAGING'::character varying, 'DR'::character varying, 'LAB'::character varying])::text[]))),
    CONSTRAINT cmdb_activos_estado_ciclo_check CHECK (((estado_ciclo)::text = ANY ((ARRAY['DISCOVERY'::character varying, 'PLANIFICADO'::character varying, 'DESPLEGANDO'::character varying, 'OPERATIVO'::character varying, 'DEGRADADO'::character varying, 'MANTENIMIENTO'::character varying, 'RETIRADO'::character varying])::text[])))
);


--
-- Name: cmdb_activos_id_activo_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cmdb_activos_id_activo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cmdb_activos_id_activo_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cmdb_activos_id_activo_seq OWNED BY public.cmdb_activos.id_activo;


--
-- Name: cmdb_cambios; Type: TABLE; Schema: public; Owner: -
--

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


--
-- Name: cmdb_cambios_id_cambio_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cmdb_cambios_id_cambio_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cmdb_cambios_id_cambio_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cmdb_cambios_id_cambio_seq OWNED BY public.cmdb_cambios.id_cambio;


--
-- Name: cmdb_categorias; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cmdb_categorias (
    id_categoria integer NOT NULL,
    nombre character varying(100) NOT NULL,
    capa character varying(30) NOT NULL,
    icono character varying(50) DEFAULT 'server'::character varying,
    color character varying(7) DEFAULT '#6B7280'::character varying,
    CONSTRAINT cmdb_categorias_capa_check CHECK (((capa)::text = ANY ((ARRAY['INFRAESTRUCTURA'::character varying, 'APLICACION'::character varying, 'RED'::character varying, 'SEGURIDAD'::character varying, 'NEGOCIO'::character varying, 'SOPORTE'::character varying])::text[])))
);


--
-- Name: cmdb_categorias_id_categoria_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cmdb_categorias_id_categoria_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cmdb_categorias_id_categoria_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cmdb_categorias_id_categoria_seq OWNED BY public.cmdb_categorias.id_categoria;


--
-- Name: cmdb_costes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cmdb_costes (
    id_coste integer NOT NULL,
    id_activo integer,
    concepto character varying(200) NOT NULL,
    categoria character varying(30),
    tipo character varying(10),
    importe numeric(12,2) NOT NULL,
    moneda character varying(3) DEFAULT 'EUR'::character varying,
    periodicidad character varying(15) DEFAULT 'MENSUAL'::character varying,
    fecha_inicio date,
    fecha_fin date,
    proveedor character varying(100),
    centro_coste character varying(50),
    id_proyecto character varying(50),
    notas text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT cmdb_costes_categoria_check CHECK (((categoria)::text = ANY ((ARRAY['HARDWARE'::character varying, 'SOFTWARE'::character varying, 'CLOUD'::character varying, 'LICENCIAS'::character varying, 'MANTENIMIENTO'::character varying, 'SOPORTE'::character varying, 'RRHH'::character varying, 'CONSULTORIA'::character varying, 'FORMACION'::character varying, 'OTROS'::character varying])::text[]))),
    CONSTRAINT cmdb_costes_periodicidad_check CHECK (((periodicidad)::text = ANY ((ARRAY['UNICO'::character varying, 'MENSUAL'::character varying, 'TRIMESTRAL'::character varying, 'ANUAL'::character varying])::text[]))),
    CONSTRAINT cmdb_costes_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['CAPEX'::character varying, 'OPEX'::character varying])::text[])))
);


--
-- Name: cmdb_costes_id_coste_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cmdb_costes_id_coste_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cmdb_costes_id_coste_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cmdb_costes_id_coste_seq OWNED BY public.cmdb_costes.id_coste;


--
-- Name: cmdb_ips; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cmdb_ips (
    id_ip integer NOT NULL,
    direccion_ip character varying(15) NOT NULL,
    id_vlan integer,
    id_activo integer,
    hostname character varying(100),
    tipo character varying(20) DEFAULT 'ESTATICA'::character varying,
    estado character varying(15) DEFAULT 'ASIGNADA'::character varying,
    mac_address character varying(17),
    puerto_switch character varying(30),
    notas character varying(200),
    ultima_vista timestamp without time zone DEFAULT now(),
    CONSTRAINT cmdb_ips_estado_check CHECK (((estado)::text = ANY ((ARRAY['LIBRE'::character varying, 'ASIGNADA'::character varying, 'RESERVADA'::character varying, 'CONFLICTO'::character varying])::text[]))),
    CONSTRAINT cmdb_ips_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['ESTATICA'::character varying, 'DHCP'::character varying, 'RESERVADA'::character varying, 'VIRTUAL'::character varying, 'VIP'::character varying])::text[])))
);


--
-- Name: cmdb_ips_id_ip_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cmdb_ips_id_ip_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cmdb_ips_id_ip_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cmdb_ips_id_ip_seq OWNED BY public.cmdb_ips.id_ip;


--
-- Name: cmdb_relaciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cmdb_relaciones (
    id_relacion integer NOT NULL,
    id_activo_origen integer,
    id_activo_destino integer,
    tipo_relacion character varying(30) NOT NULL,
    descripcion character varying(200),
    criticidad character varying(10) DEFAULT 'MEDIA'::character varying,
    CONSTRAINT cmdb_relaciones_tipo_relacion_check CHECK (((tipo_relacion)::text = ANY ((ARRAY['DEPENDE_DE'::character varying, 'EJECUTA_EN'::character varying, 'CONECTA_A'::character varying, 'PROTEGE_A'::character varying, 'RESPALDA_A'::character varying, 'MONITORIZA'::character varying, 'PARTE_DE'::character varying, 'SIRVE_A'::character varying])::text[])))
);


--
-- Name: cmdb_relaciones_id_relacion_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cmdb_relaciones_id_relacion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cmdb_relaciones_id_relacion_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cmdb_relaciones_id_relacion_seq OWNED BY public.cmdb_relaciones.id_relacion;


--
-- Name: cmdb_software; Type: TABLE; Schema: public; Owner: -
--

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
    estado character varying(15) DEFAULT 'ACTIVO'::character varying,
    critico_negocio boolean DEFAULT false,
    CONSTRAINT cmdb_software_estado_check CHECK (((estado)::text = ANY ((ARRAY['ACTIVO'::character varying, 'OBSOLETO'::character varying, 'SIN_SOPORTE'::character varying, 'EVALUACION'::character varying, 'RETIRADO'::character varying])::text[]))),
    CONSTRAINT cmdb_software_tipo_licencia_check CHECK (((tipo_licencia)::text = ANY ((ARRAY['OPEN_SOURCE'::character varying, 'COMERCIAL'::character varying, 'SUSCRIPCION'::character varying, 'FREEMIUM'::character varying, 'CUSTOM'::character varying, 'INTERNA'::character varying])::text[])))
);


--
-- Name: cmdb_software_id_software_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cmdb_software_id_software_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cmdb_software_id_software_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cmdb_software_id_software_seq OWNED BY public.cmdb_software.id_software;


--
-- Name: cmdb_vlans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cmdb_vlans (
    id_vlan integer NOT NULL,
    vlan_id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    subred character varying(18) NOT NULL,
    mascara character varying(15) DEFAULT '255.255.255.0'::character varying,
    gateway character varying(15),
    entorno character varying(20) DEFAULT 'PRODUCCION'::character varying,
    ubicacion character varying(100),
    estado character varying(15) DEFAULT 'ACTIVA'::character varying,
    proposito character varying(50),
    total_ips integer DEFAULT 0,
    ips_usadas integer DEFAULT 0,
    CONSTRAINT cmdb_vlans_estado_check CHECK (((estado)::text = ANY ((ARRAY['ACTIVA'::character varying, 'RESERVADA'::character varying, 'DESACTIVADA'::character varying])::text[])))
);


--
-- Name: cmdb_vlans_id_vlan_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cmdb_vlans_id_vlan_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cmdb_vlans_id_vlan_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cmdb_vlans_id_vlan_seq OWNED BY public.cmdb_vlans.id_vlan;


--
-- Name: compliance_audits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.compliance_audits (
    id character varying(50) DEFAULT (gen_random_uuid())::text NOT NULL,
    audit_type character varying(50) NOT NULL,
    entity_type character varying(30) NOT NULL,
    entity_id character varying(100) NOT NULL,
    severity character varying(10) NOT NULL,
    finding text NOT NULL,
    recommendation text,
    evidence jsonb DEFAULT '{}'::jsonb,
    status character varying(20) DEFAULT 'OPEN'::character varying,
    assignee character varying(100),
    due_date date,
    resolved_at timestamp with time zone,
    created_by character varying(20) DEFAULT 'AG-008'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT compliance_audits_audit_type_check CHECK (((audit_type)::text = ANY ((ARRAY['ITIL4_SLA'::character varying, 'PMBOK7_DELIVERABLE'::character varying, 'GDPR_DATA'::character varying, 'BCE_REGULATORY'::character varying, 'ISO27001_SECURITY'::character varying, 'CNMV_REPORTING'::character varying, 'DORA_RESILIENCE'::character varying])::text[]))),
    CONSTRAINT compliance_audits_severity_check CHECK (((severity)::text = ANY ((ARRAY['CRITICAL'::character varying, 'HIGH'::character varying, 'MEDIUM'::character varying, 'LOW'::character varying, 'INFO'::character varying])::text[]))),
    CONSTRAINT compliance_audits_status_check CHECK (((status)::text = ANY ((ARRAY['OPEN'::character varying, 'IN_PROGRESS'::character varying, 'RESOLVED'::character varying, 'ACCEPTED'::character varying, 'WAIVED'::character varying])::text[])))
);


--
-- Name: directorio_corporativo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.directorio_corporativo (
    id_directivo character varying(20) NOT NULL,
    nombre_completo character varying(200) NOT NULL,
    cargo character varying(150) NOT NULL,
    nivel_organizativo character varying(30) NOT NULL,
    area character varying(100) NOT NULL,
    reporta_a character varying(20),
    email character varying(255) NOT NULL,
    telefono character varying(30),
    ubicacion character varying(100) DEFAULT 'Madrid HQ'::character varying,
    fecha_incorporacion date DEFAULT CURRENT_DATE,
    activo boolean DEFAULT true,
    bio text,
    linkedin character varying(255),
    foto_url character varying(500),
    CONSTRAINT directorio_corporativo_nivel_organizativo_check CHECK (((nivel_organizativo)::text = ANY ((ARRAY['C-LEVEL'::character varying, 'VP'::character varying, 'DIRECTOR'::character varying, 'SUBDIRECTOR'::character varying, 'GERENTE'::character varying, 'COORDINADOR'::character varying, 'JEFE_EQUIPO'::character varying])::text[])))
);


--
-- Name: documentacion_repositorio; Type: TABLE; Schema: public; Owner: -
--

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
    tags text[] DEFAULT '{}'::text[],
    version integer DEFAULT 1,
    fecha_creacion timestamp with time zone DEFAULT now(),
    fecha_actualizacion timestamp with time zone DEFAULT now(),
    creado_por character varying(100),
    activo boolean DEFAULT true,
    CONSTRAINT documentacion_repositorio_silo_check CHECK (((silo)::text = ANY ((ARRAY['BUILD'::character varying, 'RUN'::character varying, 'TRANSVERSAL'::character varying])::text[]))),
    CONSTRAINT documentacion_repositorio_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['proyecto'::character varying, 'incidencia'::character varying, 'gobernanza'::character varying, 'formacion'::character varying, 'herramienta'::character varying, 'plantilla'::character varying])::text[])))
);


--
-- Name: documentacion_repositorio_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.documentacion_repositorio_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: documentacion_repositorio_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.documentacion_repositorio_id_seq OWNED BY public.documentacion_repositorio.id;


--
-- Name: gobernanza_transacciones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gobernanza_transacciones (
    id_transaccion character varying(30) NOT NULL,
    tipo_accion character varying(30) NOT NULL,
    id_proyecto character varying(30),
    fte_afectado character varying(20),
    estado_anterior character varying(30),
    estado_nuevo character varying(30),
    motivo text,
    agente_origen character varying(20) NOT NULL,
    datos_contexto jsonb DEFAULT '{}'::jsonb,
    timestamp_ejecucion timestamp without time zone DEFAULT now(),
    usuario_db character varying(30) DEFAULT 'jose_admin'::character varying,
    pending_sync jsonb DEFAULT '[]'::jsonb,
    depth integer DEFAULT 1,
    correlation_id character varying,
    retry_count integer DEFAULT 0,
    sync_status character varying DEFAULT 'PENDIENTE'::character varying,
    CONSTRAINT gobernanza_transacciones_tipo_accion_check CHECK (((tipo_accion)::text = ANY ((ARRAY['PAUSA_PROYECTO'::character varying, 'REANUDACION_PROYECTO'::character varying, 'ASIGNACION_RECURSO'::character varying, 'LIBERACION_RECURSO'::character varying, 'FREEZE_PERIOD'::character varying, 'CAMBIO_ESTADO'::character varying, 'CREACION_PROYECTO'::character varying, 'REASIGNACION_RECURSO'::character varying, 'ASIGNACION_P1_CRITICA'::character varying, 'ASIGNACION_TECNICO'::character varying, 'ESCALACION_BUFFER'::character varying, 'SKILL_GAP'::character varying, 'TEAM_ADJUSTMENT'::character varying, 'SUPERVISOR_ASSIGNED'::character varying, 'REPLANIFICACION_PROYECTO'::character varying])::text[])))
);


--
-- Name: incidencias; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.incidencias (
    id_incidencia character varying NOT NULL,
    descripcion text,
    prioridad character varying,
    categoria character varying,
    estado character varying DEFAULT 'QUEUED'::character varying,
    sla_limite character varying,
    tecnico_asignado character varying,
    fecha_creacion timestamp without time zone DEFAULT now(),
    flag_build_vs_run boolean DEFAULT false,
    impacto_negocio character varying
);


--
-- Name: incidencias_live; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.incidencias_live (
    ticket_id character varying NOT NULL,
    incidencia_detectada text NOT NULL,
    prioridad character varying DEFAULT 'P4'::character varying NOT NULL,
    categoria character varying,
    estado character varying DEFAULT 'IN_PROGRESS'::character varying,
    sla_horas numeric DEFAULT 48,
    tecnico_asignado character varying,
    area_afectada text,
    fecha_creacion timestamp without time zone DEFAULT now(),
    fecha_limite timestamp without time zone,
    progreso_pct integer DEFAULT 0,
    total_tareas integer DEFAULT 0,
    tareas_completadas integer DEFAULT 0,
    agente_origen character varying DEFAULT 'AG-001'::character varying,
    canal_entrada character varying,
    reportado_por character varying,
    servicio_afectado character varying,
    impacto_negocio character varying,
    notas text
);


--
-- Name: incidencias_run; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.incidencias_run (
    ticket_id character varying(30) NOT NULL,
    incidencia_detectada text NOT NULL,
    id_catalogo integer,
    prioridad_ia character varying(5) NOT NULL,
    categoria character varying(100),
    estado character varying(30) DEFAULT 'QUEUED'::character varying,
    sla_limite numeric(5,1),
    tecnico_asignado character varying(20),
    impacto_negocio text,
    area_afectada text,
    flag_reasignacion boolean DEFAULT false,
    timestamp_creacion timestamp without time zone DEFAULT now(),
    timestamp_asignacion timestamp without time zone,
    timestamp_resolucion timestamp without time zone,
    tiempo_resolucion_minutos integer,
    agente_origen character varying(20) DEFAULT 'AG-001'::character varying,
    urgencia character varying(10) DEFAULT 'Media'::character varying,
    impacto character varying(10) DEFAULT 'Medio'::character varying,
    canal_entrada character varying(30) DEFAULT 'Portal ITSM'::character varying,
    reportado_por character varying(100),
    servicio_afectado character varying(100),
    ci_afectado character varying(100),
    notas_adicionales text,
    CONSTRAINT incidencias_run_estado_check CHECK (((estado)::text = ANY ((ARRAY['QUEUED'::character varying, 'EN_CURSO'::character varying, 'ESCALADO'::character varying, 'RESUELTO'::character varying, 'CERRADO'::character varying])::text[]))),
    CONSTRAINT incidencias_run_prioridad_ia_check CHECK (((prioridad_ia)::text = ANY ((ARRAY['P1'::character varying, 'P2'::character varying, 'P3'::character varying, 'P4'::character varying])::text[])))
);


--
-- Name: intelligent_alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.intelligent_alerts (
    id character varying(50) DEFAULT (gen_random_uuid())::text NOT NULL,
    alert_type character varying(50) NOT NULL,
    severity character varying(10) NOT NULL,
    title character varying(300) NOT NULL,
    description text NOT NULL,
    source_agent character varying(10) NOT NULL,
    affected_entities jsonb DEFAULT '{}'::jsonb NOT NULL,
    trigger_condition jsonb DEFAULT '{}'::jsonb NOT NULL,
    recommended_actions jsonb DEFAULT '[]'::jsonb,
    auto_resolved boolean DEFAULT false,
    acknowledged_by character varying(100),
    acknowledged_at timestamp with time zone,
    resolved_at timestamp with time zone,
    status character varying(20) DEFAULT 'ACTIVE'::character varying,
    correlation_id character varying(50),
    parent_alert_id character varying(50),
    ttl_hours integer DEFAULT 24,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT intelligent_alerts_alert_type_check CHECK (((alert_type)::text = ANY ((ARRAY['SLA_RISK'::character varying, 'OVERALLOCATION'::character varying, 'SKILL_GAP'::character varying, 'FREEZE_RECOMMENDED'::character varying, 'BUDGET_OVERRUN'::character varying, 'MILESTONE_RISK'::character varying, 'BURNOUT_RISK'::character varying, 'COMPLIANCE_BREACH'::character varying, 'CASCADE_FAILURE'::character varying, 'CAPACITY_THRESHOLD'::character varying])::text[]))),
    CONSTRAINT intelligent_alerts_severity_check CHECK (((severity)::text = ANY ((ARRAY['CRITICAL'::character varying, 'HIGH'::character varying, 'MEDIUM'::character varying, 'LOW'::character varying])::text[]))),
    CONSTRAINT intelligent_alerts_status_check CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'ACKNOWLEDGED'::character varying, 'RESOLVED'::character varying, 'ESCALATED'::character varying, 'SUPPRESSED'::character varying])::text[])))
);


--
-- Name: kanban_tareas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kanban_tareas (
    id character varying(30) NOT NULL,
    titulo text NOT NULL,
    descripcion text,
    tipo character varying(10) NOT NULL,
    prioridad character varying(10) NOT NULL,
    columna character varying(30) DEFAULT 'Backlog'::character varying NOT NULL,
    id_tecnico character varying(20),
    id_proyecto character varying(30),
    id_incidencia character varying(30),
    bloqueador text,
    horas_estimadas numeric(6,1) DEFAULT 0,
    horas_reales numeric(6,1) DEFAULT 0,
    fecha_creacion timestamp with time zone DEFAULT now() NOT NULL,
    fecha_inicio_ejecucion timestamp with time zone,
    fecha_cierre timestamp with time zone,
    historial_columnas jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT kanban_tareas_columna_check CHECK (((columna)::text = ANY ((ARRAY['Backlog'::character varying, 'Análisis'::character varying, 'En Progreso'::character varying, 'Code Review'::character varying, 'Testing'::character varying, 'Despliegue'::character varying, 'Bloqueado'::character varying, 'Completado'::character varying])::text[]))),
    CONSTRAINT kanban_tareas_prioridad_check CHECK (((prioridad)::text = ANY ((ARRAY['Crítica'::character varying, 'Alta'::character varying, 'Media'::character varying, 'Baja'::character varying])::text[]))),
    CONSTRAINT kanban_tareas_tipo_check CHECK (((tipo)::text = ANY ((ARRAY['RUN'::character varying, 'BUILD'::character varying])::text[])))
);


--
-- Name: pipeline_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pipeline_sessions (
    id character varying DEFAULT (gen_random_uuid())::text NOT NULL,
    nombre_proyecto character varying DEFAULT ''::character varying NOT NULL,
    estado character varying DEFAULT 'EN_PROGRESO'::character varying,
    pausa_actual integer DEFAULT 0,
    pipeline_data jsonb DEFAULT '{}'::jsonb NOT NULL,
    business_case jsonb DEFAULT '{}'::jsonb,
    session_id character varying DEFAULT ''::character varying,
    tiempo_acumulado_ms integer DEFAULT 0,
    coste_acumulado numeric DEFAULT 0,
    agentes_completados jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: pmo_governance_scoring; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pmo_governance_scoring (
    id character varying(50) DEFAULT (gen_random_uuid())::text NOT NULL,
    id_proyecto character varying(30) NOT NULL,
    id_pm character varying(20),
    roi_score numeric(4,2) DEFAULT 0,
    risk_score numeric(4,2) DEFAULT 0,
    capacity_score numeric(4,2) DEFAULT 0,
    strategic_value numeric(4,2) DEFAULT 0,
    total_score numeric(4,2) DEFAULT 0,
    gate_status character varying(20) DEFAULT 'PENDING'::character varying,
    current_gate character varying(20) DEFAULT 'G0-IDEA'::character varying,
    gate_history jsonb DEFAULT '[]'::jsonb,
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
    evm_pv_json jsonb DEFAULT '[]'::jsonb,
    total_sprints integer DEFAULT 0,
    story_points_total integer DEFAULT 0,
    CONSTRAINT pmo_governance_scoring_capacity_score_check CHECK (((capacity_score >= (0)::numeric) AND (capacity_score <= (10)::numeric))),
    CONSTRAINT pmo_governance_scoring_gate_status_check CHECK (((gate_status)::text = ANY ((ARRAY['PENDING'::character varying, 'APPROVED'::character varying, 'HOLD'::character varying, 'REJECTED'::character varying, 'COMPLETED'::character varying])::text[]))),
    CONSTRAINT pmo_governance_scoring_risk_score_check CHECK (((risk_score >= (0)::numeric) AND (risk_score <= (10)::numeric))),
    CONSTRAINT pmo_governance_scoring_roi_score_check CHECK (((roi_score >= (0)::numeric) AND (roi_score <= (10)::numeric))),
    CONSTRAINT pmo_governance_scoring_strategic_value_check CHECK (((strategic_value >= (0)::numeric) AND (strategic_value <= (10)::numeric)))
);


--
-- Name: pmo_project_managers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pmo_project_managers (
    id_pm character varying(20) NOT NULL,
    nombre text NOT NULL,
    nivel character varying(10) NOT NULL,
    especialidad character varying(50) NOT NULL,
    skills_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    skill_principal character varying(100),
    total_skills integer DEFAULT 0,
    estado character varying(20) DEFAULT 'DISPONIBLE'::character varying,
    max_proyectos integer DEFAULT 3,
    email character varying(100),
    telefono character varying(20),
    certificaciones text[] DEFAULT '{}'::text[],
    fecha_alta date DEFAULT CURRENT_DATE,
    scoring_promedio numeric(4,2) DEFAULT 0,
    proyectos_completados integer DEFAULT 0,
    proyectos_activos integer DEFAULT 0,
    tasa_exito numeric(5,2) DEFAULT 100.00,
    carga_actual integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT pmo_project_managers_carga_actual_check CHECK (((carga_actual >= 0) AND (carga_actual <= 200))),
    CONSTRAINT pmo_project_managers_estado_check CHECK (((estado)::text = ANY ((ARRAY['DISPONIBLE'::character varying, 'ASIGNADO'::character varying, 'SOBRECARGADO'::character varying, 'BAJA'::character varying, 'VACACIONES'::character varying])::text[]))),
    CONSTRAINT pmo_project_managers_nivel_check CHECK (((nivel)::text = ANY ((ARRAY['PM-Jr'::character varying, 'PM-Sr'::character varying, 'PM-Lead'::character varying, 'PM-Dir'::character varying])::text[])))
);


--
-- Name: pmo_staff_skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pmo_staff_skills (
    id_recurso character varying(20) NOT NULL,
    nombre text NOT NULL,
    nivel character varying(10) NOT NULL,
    silo_especialidad character varying(50) NOT NULL,
    total_skills integer DEFAULT 0,
    skills_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    skill_principal character varying(100),
    carga_actual integer DEFAULT 0,
    estado_run character varying(20) DEFAULT 'DISPONIBLE'::character varying,
    fecha_alta date DEFAULT CURRENT_DATE,
    fecha_ultima_asignacion timestamp without time zone,
    incidencias_resueltas integer DEFAULT 0,
    email character varying(100),
    telefono character varying(20),
    CONSTRAINT pmo_staff_skills_carga_actual_check CHECK (((carga_actual >= 0) AND (carga_actual <= 200))),
    CONSTRAINT pmo_staff_skills_estado_run_check CHECK (((estado_run)::text = ANY ((ARRAY['DISPONIBLE'::character varying, 'OCUPADO'::character varying, 'GUARDIA'::character varying, 'BAJA'::character varying, 'VACACIONES'::character varying])::text[]))),
    CONSTRAINT pmo_staff_skills_nivel_check CHECK (((nivel)::text = ANY ((ARRAY['N1'::character varying, 'N2'::character varying, 'N3'::character varying, 'N4'::character varying])::text[]))),
    CONSTRAINT pmo_staff_skills_silo_especialidad_check CHECK (((silo_especialidad)::text = ANY ((ARRAY['Frontend'::character varying, 'Soporte'::character varying, 'Redes'::character varying, 'Windows'::character varying, 'Backend'::character varying, 'QA'::character varying, 'DevOps'::character varying, 'Seguridad'::character varying, 'BBDD'::character varying])::text[])))
);


--
-- Name: postmortem_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.postmortem_reports (
    id character varying(50) DEFAULT (gen_random_uuid())::text NOT NULL,
    incident_id character varying(50) NOT NULL,
    incident_priority character varying(5) NOT NULL,
    title character varying(300) NOT NULL,
    timeline jsonb DEFAULT '[]'::jsonb NOT NULL,
    root_cause text NOT NULL,
    root_cause_category character varying(50),
    impact_assessment jsonb DEFAULT '{}'::jsonb NOT NULL,
    corrective_actions jsonb DEFAULT '[]'::jsonb NOT NULL,
    preventive_actions jsonb DEFAULT '[]'::jsonb NOT NULL,
    lessons_learned text[] DEFAULT '{}'::text[],
    mttr_minutes integer,
    mtta_minutes integer,
    sla_breached boolean DEFAULT false,
    agents_involved character varying(10)[] DEFAULT '{}'::character varying[],
    resources_involved character varying(20)[] DEFAULT '{}'::character varying[],
    projects_impacted character varying(50)[] DEFAULT '{}'::character varying[],
    review_status character varying(20) DEFAULT 'DRAFT'::character varying,
    approved_by character varying(100),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT postmortem_reports_review_status_check CHECK (((review_status)::text = ANY ((ARRAY['DRAFT'::character varying, 'REVIEW'::character varying, 'APPROVED'::character varying, 'ARCHIVED'::character varying])::text[])))
);


--
-- Name: presupuestos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.presupuestos (
    id_presupuesto character varying(30) NOT NULL,
    id_proyecto character varying(100) NOT NULL,
    nombre_presupuesto character varying(200) NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    estado character varying(20) DEFAULT 'BORRADOR'::character varying NOT NULL,
    responsable character varying(100) NOT NULL,
    fecha_inicio date,
    fecha_fin date,
    moneda character varying(3) DEFAULT 'EUR'::character varying NOT NULL,
    horas_internas numeric(10,2) DEFAULT 0 NOT NULL,
    tarifa_hora_interna numeric(10,2) DEFAULT 85.00 NOT NULL,
    proveedores_externos jsonb DEFAULT '[]'::jsonb NOT NULL,
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
    CONSTRAINT presupuestos_estado_check CHECK (((estado)::text = ANY ((ARRAY['BORRADOR'::character varying, 'EN_REVISION'::character varying, 'APROBADO'::character varying, 'CERRADO'::character varying, 'RECHAZADO'::character varying])::text[])))
);


--
-- Name: rbac_audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_audit_log (
    id_log integer NOT NULL,
    id_usuario integer,
    email character varying(255),
    accion character varying(50) NOT NULL,
    modulo character varying(50),
    recurso character varying(200),
    detalle jsonb DEFAULT '{}'::jsonb,
    ip_address character varying(45),
    resultado character varying(20) DEFAULT 'OK'::character varying,
    "timestamp" timestamp without time zone DEFAULT now(),
    CONSTRAINT rbac_audit_log_resultado_check CHECK (((resultado)::text = ANY ((ARRAY['OK'::character varying, 'DENEGADO'::character varying, 'ERROR'::character varying])::text[])))
);


--
-- Name: rbac_audit_log_id_log_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rbac_audit_log_id_log_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rbac_audit_log_id_log_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rbac_audit_log_id_log_seq OWNED BY public.rbac_audit_log.id_log;


--
-- Name: rbac_permisos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_permisos (
    id_permiso integer NOT NULL,
    code character varying(100) NOT NULL,
    modulo character varying(50) NOT NULL,
    accion character varying(30) NOT NULL,
    descripcion text,
    criticidad character varying(10) DEFAULT 'MEDIA'::character varying,
    CONSTRAINT rbac_permisos_accion_check CHECK (((accion)::text = ANY ((ARRAY['ver'::character varying, 'crear'::character varying, 'editar'::character varying, 'eliminar'::character varying, 'aprobar'::character varying, 'exportar'::character varying, 'ejecutar'::character varying, 'admin'::character varying])::text[]))),
    CONSTRAINT rbac_permisos_criticidad_check CHECK (((criticidad)::text = ANY ((ARRAY['BAJA'::character varying, 'MEDIA'::character varying, 'ALTA'::character varying, 'CRITICA'::character varying])::text[])))
);


--
-- Name: rbac_permisos_id_permiso_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rbac_permisos_id_permiso_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rbac_permisos_id_permiso_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rbac_permisos_id_permiso_seq OWNED BY public.rbac_permisos.id_permiso;


--
-- Name: rbac_role_permisos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_role_permisos (
    id_role integer NOT NULL,
    id_permiso integer NOT NULL
);


--
-- Name: rbac_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rbac_roles (
    id_role integer NOT NULL,
    code character varying(50) NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    nivel_jerarquico integer DEFAULT 0 NOT NULL,
    color character varying(7) DEFAULT '#6B7280'::character varying,
    icono character varying(50) DEFAULT 'shield'::character varying,
    activo boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: rbac_roles_id_role_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rbac_roles_id_role_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rbac_roles_id_role_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rbac_roles_id_role_seq OWNED BY public.rbac_roles.id_role;


--
-- Name: rbac_sesiones; Type: TABLE; Schema: public; Owner: -
--

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


--
-- Name: rbac_sesiones_id_sesion_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rbac_sesiones_id_sesion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rbac_sesiones_id_sesion_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rbac_sesiones_id_sesion_seq OWNED BY public.rbac_sesiones.id_sesion;


--
-- Name: rbac_usuarios; Type: TABLE; Schema: public; Owner: -
--

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


--
-- Name: rbac_usuarios_id_usuario_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rbac_usuarios_id_usuario_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rbac_usuarios_id_usuario_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rbac_usuarios_id_usuario_seq OWNED BY public.rbac_usuarios.id_usuario;


--
-- Name: run_incident_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.run_incident_plans (
    id character varying(30) NOT NULL,
    ticket_id character varying(30),
    nombre text NOT NULL,
    prioridad character varying(5) DEFAULT 'P3'::character varying,
    area character varying(30),
    sla_horas numeric(5,1),
    plan_data jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: seq_txn; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.seq_txn
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: view_disponibilidad_global; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.view_disponibilidad_global AS
 SELECT s.id_recurso,
    s.nombre,
    s.nivel,
    s.silo_especialidad,
    s.skill_principal,
    s.carga_actual,
    s.estado_run,
    s.skills_json,
    s.total_skills,
    COALESCE(( SELECT count(*) AS count
           FROM public.incidencias_run i
          WHERE (((i.tecnico_asignado)::text = (s.id_recurso)::text) AND ((i.estado)::text = ANY ((ARRAY['QUEUED'::character varying, 'EN_CURSO'::character varying])::text[])))), (0)::bigint) AS incidencias_activas,
    COALESCE(( SELECT count(*) AS count
           FROM public.cartera_build c
          WHERE (((c.responsable_asignado)::text = (s.id_recurso)::text) AND ((c.estado)::text = 'en ejecucion'::text))), (0)::bigint) AS proyectos_activos
   FROM public.pmo_staff_skills s;


--
-- Name: vista_audit_gobernanza; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vista_audit_gobernanza AS
 SELECT g.id_transaccion,
    g.tipo_accion,
    g.timestamp_ejecucion,
    g.agente_origen,
    c.nombre_proyecto,
    c.prioridad_estrategica,
    s.nombre AS nombre_tecnico,
    g.estado_anterior,
    g.estado_nuevo,
    g.motivo
   FROM ((public.gobernanza_transacciones g
     LEFT JOIN public.cartera_build c ON (((g.id_proyecto)::text = (c.id_proyecto)::text)))
     LEFT JOIN public.pmo_staff_skills s ON (((g.fte_afectado)::text = (s.id_recurso)::text)))
  ORDER BY g.timestamp_ejecucion DESC;


--
-- Name: vista_carga_por_silo; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vista_carga_por_silo AS
 SELECT pmo_staff_skills.silo_especialidad,
    pmo_staff_skills.nivel,
    count(*) AS total_tecnicos,
    round(avg(pmo_staff_skills.carga_actual), 1) AS carga_media,
    sum(
        CASE
            WHEN ((pmo_staff_skills.estado_run)::text = 'DISPONIBLE'::text) THEN 1
            ELSE 0
        END) AS disponibles,
    sum(
        CASE
            WHEN ((pmo_staff_skills.estado_run)::text = 'OCUPADO'::text) THEN 1
            ELSE 0
        END) AS ocupados
   FROM public.pmo_staff_skills
  GROUP BY pmo_staff_skills.silo_especialidad, pmo_staff_skills.nivel
  ORDER BY pmo_staff_skills.silo_especialidad, pmo_staff_skills.nivel;


--
-- Name: vista_portafolio_build; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vista_portafolio_build AS
 SELECT cartera_build.estado,
    cartera_build.prioridad_estrategica,
    count(*) AS total_proyectos,
    sum(cartera_build.horas_estimadas) AS horas_totales,
    count(cartera_build.responsable_asignado) AS con_responsable
   FROM public.cartera_build
  GROUP BY cartera_build.estado, cartera_build.prioridad_estrategica
  ORDER BY cartera_build.prioridad_estrategica, cartera_build.estado;


--
-- Name: vista_proyectos_riesgo; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vista_proyectos_riesgo AS
 SELECT cartera_build.id_proyecto,
    cartera_build.nombre_proyecto,
    cartera_build.prioridad_estrategica,
    cartera_build.estado,
    cartera_build.responsable_asignado,
    cartera_build.motivo_pausa
   FROM public.cartera_build
  WHERE (((cartera_build.estado)::text = 'PAUSADO_POR_RIESGO_P1'::text) OR (((cartera_build.estado)::text = 'en ejecucion'::text) AND (cartera_build.responsable_asignado IS NULL)));


--
-- Name: vista_serie_temporal_incidencias; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vista_serie_temporal_incidencias AS
 SELECT date(incidencias_run.timestamp_creacion) AS ds,
    count(*) AS y
   FROM public.incidencias_run
  GROUP BY (date(incidencias_run.timestamp_creacion))
  ORDER BY (date(incidencias_run.timestamp_creacion));


--
-- Name: war_room_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.war_room_sessions (
    id character varying(50) DEFAULT (gen_random_uuid())::text NOT NULL,
    session_name character varying(200) NOT NULL,
    session_type character varying(30) NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE'::character varying,
    participants jsonb DEFAULT '[]'::jsonb,
    context jsonb DEFAULT '{}'::jsonb,
    summary text,
    decisions jsonb DEFAULT '[]'::jsonb,
    started_at timestamp with time zone DEFAULT now(),
    closed_at timestamp with time zone,
    CONSTRAINT war_room_sessions_session_type_check CHECK (((session_type)::text = ANY ((ARRAY['CRISIS_P1'::character varying, 'PLANNING'::character varying, 'REVIEW'::character varying, 'SIMULATION'::character varying, 'AUDIT'::character varying, 'AD_HOC'::character varying])::text[]))),
    CONSTRAINT war_room_sessions_status_check CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'PAUSED'::character varying, 'CLOSED'::character varying, 'ARCHIVED'::character varying])::text[])))
);


--
-- Name: whatif_simulations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.whatif_simulations (
    id character varying(50) DEFAULT (gen_random_uuid())::text NOT NULL,
    simulation_name character varying(200) NOT NULL,
    scenario_type character varying(50) NOT NULL,
    input_params jsonb DEFAULT '{}'::jsonb NOT NULL,
    baseline_snapshot jsonb DEFAULT '{}'::jsonb NOT NULL,
    simulation_result jsonb DEFAULT '{}'::jsonb NOT NULL,
    risk_score numeric(5,2) DEFAULT 0,
    confidence_level numeric(3,2) DEFAULT 0.7,
    recommendations text[] DEFAULT '{}'::text[],
    affected_projects character varying(50)[] DEFAULT '{}'::character varying[],
    affected_resources character varying(20)[] DEFAULT '{}'::character varying[],
    kpi_deltas jsonb DEFAULT '{}'::jsonb,
    created_by character varying(100) DEFAULT 'AG-010'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT whatif_simulations_confidence_level_check CHECK (((confidence_level >= (0)::numeric) AND (confidence_level <= (1)::numeric))),
    CONSTRAINT whatif_simulations_risk_score_check CHECK (((risk_score >= (0)::numeric) AND (risk_score <= (100)::numeric))),
    CONSTRAINT whatif_simulations_scenario_type_check CHECK (((scenario_type)::text = ANY ((ARRAY['RESOURCE_REALLOCATION'::character varying, 'PROJECT_DELAY'::character varying, 'P1_CASCADE'::character varying, 'BUDGET_CUT'::character varying, 'TEAM_SCALING'::character varying, 'FREEZE_PERIOD'::character varying, 'SKILL_GAP'::character varying, 'VENDOR_FAILURE'::character varying, 'REGULATORY_CHANGE'::character varying])::text[])))
);


--
-- Name: catalogo_incidencias id_catalogo; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalogo_incidencias ALTER COLUMN id_catalogo SET DEFAULT nextval('public.catalogo_incidencias_id_catalogo_seq'::regclass);


--
-- Name: catalogo_skills id_skill; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalogo_skills ALTER COLUMN id_skill SET DEFAULT nextval('public.catalogo_skills_id_skill_seq'::regclass);


--
-- Name: cmdb_activos id_activo; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_activos ALTER COLUMN id_activo SET DEFAULT nextval('public.cmdb_activos_id_activo_seq'::regclass);


--
-- Name: cmdb_cambios id_cambio; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_cambios ALTER COLUMN id_cambio SET DEFAULT nextval('public.cmdb_cambios_id_cambio_seq'::regclass);


--
-- Name: cmdb_categorias id_categoria; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_categorias ALTER COLUMN id_categoria SET DEFAULT nextval('public.cmdb_categorias_id_categoria_seq'::regclass);


--
-- Name: cmdb_costes id_coste; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_costes ALTER COLUMN id_coste SET DEFAULT nextval('public.cmdb_costes_id_coste_seq'::regclass);


--
-- Name: cmdb_ips id_ip; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_ips ALTER COLUMN id_ip SET DEFAULT nextval('public.cmdb_ips_id_ip_seq'::regclass);


--
-- Name: cmdb_relaciones id_relacion; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_relaciones ALTER COLUMN id_relacion SET DEFAULT nextval('public.cmdb_relaciones_id_relacion_seq'::regclass);


--
-- Name: cmdb_software id_software; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_software ALTER COLUMN id_software SET DEFAULT nextval('public.cmdb_software_id_software_seq'::regclass);


--
-- Name: cmdb_vlans id_vlan; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_vlans ALTER COLUMN id_vlan SET DEFAULT nextval('public.cmdb_vlans_id_vlan_seq'::regclass);


--
-- Name: documentacion_repositorio id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentacion_repositorio ALTER COLUMN id SET DEFAULT nextval('public.documentacion_repositorio_id_seq'::regclass);


--
-- Name: rbac_audit_log id_log; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_audit_log ALTER COLUMN id_log SET DEFAULT nextval('public.rbac_audit_log_id_log_seq'::regclass);


--
-- Name: rbac_permisos id_permiso; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permisos ALTER COLUMN id_permiso SET DEFAULT nextval('public.rbac_permisos_id_permiso_seq'::regclass);


--
-- Name: rbac_roles id_role; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_roles ALTER COLUMN id_role SET DEFAULT nextval('public.rbac_roles_id_role_seq'::regclass);


--
-- Name: rbac_sesiones id_sesion; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_sesiones ALTER COLUMN id_sesion SET DEFAULT nextval('public.rbac_sesiones_id_sesion_seq'::regclass);


--
-- Name: rbac_usuarios id_usuario; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_usuarios ALTER COLUMN id_usuario SET DEFAULT nextval('public.rbac_usuarios_id_usuario_seq'::regclass);


--
-- Name: agent_conversations agent_conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_conversations
    ADD CONSTRAINT agent_conversations_pkey PRIMARY KEY (id);


--
-- Name: agent_performance_metrics agent_performance_metrics_agent_id_metric_date_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_performance_metrics
    ADD CONSTRAINT agent_performance_metrics_agent_id_metric_date_key UNIQUE (agent_id, metric_date);


--
-- Name: agent_performance_metrics agent_performance_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_performance_metrics
    ADD CONSTRAINT agent_performance_metrics_pkey PRIMARY KEY (id);


--
-- Name: build_live build_live_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_live
    ADD CONSTRAINT build_live_pkey PRIMARY KEY (id_proyecto);


--
-- Name: build_project_plans build_project_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_project_plans
    ADD CONSTRAINT build_project_plans_pkey PRIMARY KEY (id);


--
-- Name: build_quality_gates build_quality_gates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_quality_gates
    ADD CONSTRAINT build_quality_gates_pkey PRIMARY KEY (id);


--
-- Name: build_risks build_risks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_risks
    ADD CONSTRAINT build_risks_pkey PRIMARY KEY (id);


--
-- Name: build_sprint_items build_sprint_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_sprint_items
    ADD CONSTRAINT build_sprint_items_pkey PRIMARY KEY (id);


--
-- Name: build_sprints build_sprints_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_sprints
    ADD CONSTRAINT build_sprints_pkey PRIMARY KEY (id);


--
-- Name: build_stakeholders build_stakeholders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_stakeholders
    ADD CONSTRAINT build_stakeholders_pkey PRIMARY KEY (id);


--
-- Name: build_subtasks build_subtasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.build_subtasks
    ADD CONSTRAINT build_subtasks_pkey PRIMARY KEY (id);


--
-- Name: cartera_build cartera_build_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cartera_build
    ADD CONSTRAINT cartera_build_pkey PRIMARY KEY (id_proyecto);


--
-- Name: catalogo_incidencias catalogo_incidencias_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalogo_incidencias
    ADD CONSTRAINT catalogo_incidencias_pkey PRIMARY KEY (id_catalogo);


--
-- Name: catalogo_skills catalogo_skills_nombre_skill_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalogo_skills
    ADD CONSTRAINT catalogo_skills_nombre_skill_key UNIQUE (nombre_skill);


--
-- Name: catalogo_skills catalogo_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalogo_skills
    ADD CONSTRAINT catalogo_skills_pkey PRIMARY KEY (id_skill);


--
-- Name: cmdb_activo_software cmdb_activo_software_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_activo_software
    ADD CONSTRAINT cmdb_activo_software_pkey PRIMARY KEY (id_activo, id_software);


--
-- Name: cmdb_activos cmdb_activos_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_activos
    ADD CONSTRAINT cmdb_activos_codigo_key UNIQUE (codigo);


--
-- Name: cmdb_activos cmdb_activos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_activos
    ADD CONSTRAINT cmdb_activos_pkey PRIMARY KEY (id_activo);


--
-- Name: cmdb_cambios cmdb_cambios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_cambios
    ADD CONSTRAINT cmdb_cambios_pkey PRIMARY KEY (id_cambio);


--
-- Name: cmdb_categorias cmdb_categorias_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_categorias
    ADD CONSTRAINT cmdb_categorias_nombre_key UNIQUE (nombre);


--
-- Name: cmdb_categorias cmdb_categorias_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_categorias
    ADD CONSTRAINT cmdb_categorias_pkey PRIMARY KEY (id_categoria);


--
-- Name: cmdb_costes cmdb_costes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_costes
    ADD CONSTRAINT cmdb_costes_pkey PRIMARY KEY (id_coste);


--
-- Name: cmdb_ips cmdb_ips_direccion_ip_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_ips
    ADD CONSTRAINT cmdb_ips_direccion_ip_key UNIQUE (direccion_ip);


--
-- Name: cmdb_ips cmdb_ips_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_ips
    ADD CONSTRAINT cmdb_ips_pkey PRIMARY KEY (id_ip);


--
-- Name: cmdb_relaciones cmdb_relaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_relaciones
    ADD CONSTRAINT cmdb_relaciones_pkey PRIMARY KEY (id_relacion);


--
-- Name: cmdb_software cmdb_software_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_software
    ADD CONSTRAINT cmdb_software_pkey PRIMARY KEY (id_software);


--
-- Name: cmdb_vlans cmdb_vlans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_vlans
    ADD CONSTRAINT cmdb_vlans_pkey PRIMARY KEY (id_vlan);


--
-- Name: cmdb_vlans cmdb_vlans_vlan_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_vlans
    ADD CONSTRAINT cmdb_vlans_vlan_id_key UNIQUE (vlan_id);


--
-- Name: compliance_audits compliance_audits_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.compliance_audits
    ADD CONSTRAINT compliance_audits_pkey PRIMARY KEY (id);


--
-- Name: directorio_corporativo directorio_corporativo_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.directorio_corporativo
    ADD CONSTRAINT directorio_corporativo_email_key UNIQUE (email);


--
-- Name: directorio_corporativo directorio_corporativo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.directorio_corporativo
    ADD CONSTRAINT directorio_corporativo_pkey PRIMARY KEY (id_directivo);


--
-- Name: documentacion_repositorio documentacion_repositorio_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentacion_repositorio
    ADD CONSTRAINT documentacion_repositorio_pkey PRIMARY KEY (id);


--
-- Name: gobernanza_transacciones gobernanza_transacciones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gobernanza_transacciones
    ADD CONSTRAINT gobernanza_transacciones_pkey PRIMARY KEY (id_transaccion);


--
-- Name: incidencias_live incidencias_live_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incidencias_live
    ADD CONSTRAINT incidencias_live_pkey PRIMARY KEY (ticket_id);


--
-- Name: incidencias incidencias_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incidencias
    ADD CONSTRAINT incidencias_pkey PRIMARY KEY (id_incidencia);


--
-- Name: incidencias_run incidencias_run_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incidencias_run
    ADD CONSTRAINT incidencias_run_pkey PRIMARY KEY (ticket_id);


--
-- Name: intelligent_alerts intelligent_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intelligent_alerts
    ADD CONSTRAINT intelligent_alerts_pkey PRIMARY KEY (id);


--
-- Name: kanban_tareas kanban_tareas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kanban_tareas
    ADD CONSTRAINT kanban_tareas_pkey PRIMARY KEY (id);


--
-- Name: pipeline_sessions pipeline_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pipeline_sessions
    ADD CONSTRAINT pipeline_sessions_pkey PRIMARY KEY (id);


--
-- Name: pmo_governance_scoring pmo_governance_scoring_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pmo_governance_scoring
    ADD CONSTRAINT pmo_governance_scoring_pkey PRIMARY KEY (id);


--
-- Name: pmo_project_managers pmo_project_managers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pmo_project_managers
    ADD CONSTRAINT pmo_project_managers_pkey PRIMARY KEY (id_pm);


--
-- Name: pmo_staff_skills pmo_staff_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pmo_staff_skills
    ADD CONSTRAINT pmo_staff_skills_pkey PRIMARY KEY (id_recurso);


--
-- Name: postmortem_reports postmortem_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.postmortem_reports
    ADD CONSTRAINT postmortem_reports_pkey PRIMARY KEY (id);


--
-- Name: presupuestos presupuestos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.presupuestos
    ADD CONSTRAINT presupuestos_pkey PRIMARY KEY (id_presupuesto);


--
-- Name: rbac_audit_log rbac_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_audit_log
    ADD CONSTRAINT rbac_audit_log_pkey PRIMARY KEY (id_log);


--
-- Name: rbac_permisos rbac_permisos_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permisos
    ADD CONSTRAINT rbac_permisos_code_key UNIQUE (code);


--
-- Name: rbac_permisos rbac_permisos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_permisos
    ADD CONSTRAINT rbac_permisos_pkey PRIMARY KEY (id_permiso);


--
-- Name: rbac_role_permisos rbac_role_permisos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_permisos
    ADD CONSTRAINT rbac_role_permisos_pkey PRIMARY KEY (id_role, id_permiso);


--
-- Name: rbac_roles rbac_roles_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_roles
    ADD CONSTRAINT rbac_roles_code_key UNIQUE (code);


--
-- Name: rbac_roles rbac_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_roles
    ADD CONSTRAINT rbac_roles_pkey PRIMARY KEY (id_role);


--
-- Name: rbac_sesiones rbac_sesiones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_sesiones
    ADD CONSTRAINT rbac_sesiones_pkey PRIMARY KEY (id_sesion);


--
-- Name: rbac_usuarios rbac_usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_usuarios
    ADD CONSTRAINT rbac_usuarios_email_key UNIQUE (email);


--
-- Name: rbac_usuarios rbac_usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_usuarios
    ADD CONSTRAINT rbac_usuarios_pkey PRIMARY KEY (id_usuario);


--
-- Name: run_incident_plans run_incident_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.run_incident_plans
    ADD CONSTRAINT run_incident_plans_pkey PRIMARY KEY (id);


--
-- Name: war_room_sessions war_room_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.war_room_sessions
    ADD CONSTRAINT war_room_sessions_pkey PRIMARY KEY (id);


--
-- Name: whatif_simulations whatif_simulations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.whatif_simulations
    ADD CONSTRAINT whatif_simulations_pkey PRIMARY KEY (id);


--
-- Name: idx_alert_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alert_severity ON public.intelligent_alerts USING btree (severity);


--
-- Name: idx_alert_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alert_source ON public.intelligent_alerts USING btree (source_agent);


--
-- Name: idx_alert_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alert_status ON public.intelligent_alerts USING btree (status);


--
-- Name: idx_alert_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alert_type ON public.intelligent_alerts USING btree (alert_type);


--
-- Name: idx_audit_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_severity ON public.compliance_audits USING btree (severity);


--
-- Name: idx_audit_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_status ON public.compliance_audits USING btree (status);


--
-- Name: idx_audit_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_type ON public.compliance_audits USING btree (audit_type);


--
-- Name: idx_bpp_proyecto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bpp_proyecto ON public.build_project_plans USING btree (id_proyecto);


--
-- Name: idx_cartera_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cartera_estado ON public.cartera_build USING btree (estado);


--
-- Name: idx_cartera_prioridad; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cartera_prioridad ON public.cartera_build USING btree (prioridad_estrategica);


--
-- Name: idx_cartera_responsable; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cartera_responsable ON public.cartera_build USING btree (responsable_asignado);


--
-- Name: idx_catalogo_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_catalogo_trgm ON public.catalogo_incidencias USING gin (incidencia public.gin_trgm_ops);


--
-- Name: idx_cmdb_activos_capa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cmdb_activos_capa ON public.cmdb_activos USING btree (capa);


--
-- Name: idx_cmdb_activos_criticidad; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cmdb_activos_criticidad ON public.cmdb_activos USING btree (criticidad);


--
-- Name: idx_cmdb_activos_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cmdb_activos_estado ON public.cmdb_activos USING btree (estado_ciclo);


--
-- Name: idx_cmdb_activos_proyecto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cmdb_activos_proyecto ON public.cmdb_activos USING btree (id_proyecto);


--
-- Name: idx_cmdb_activos_tipo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cmdb_activos_tipo ON public.cmdb_activos USING btree (tipo);


--
-- Name: idx_cmdb_ips_activo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cmdb_ips_activo ON public.cmdb_ips USING btree (id_activo);


--
-- Name: idx_cmdb_ips_vlan; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cmdb_ips_vlan ON public.cmdb_ips USING btree (id_vlan);


--
-- Name: idx_cmdb_relaciones_destino; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cmdb_relaciones_destino ON public.cmdb_relaciones USING btree (id_activo_destino);


--
-- Name: idx_cmdb_relaciones_origen; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cmdb_relaciones_origen ON public.cmdb_relaciones USING btree (id_activo_origen);


--
-- Name: idx_conv_agent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_agent ON public.agent_conversations USING btree (agent_id);


--
-- Name: idx_conv_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_created ON public.agent_conversations USING btree (created_at DESC);


--
-- Name: idx_conv_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_session ON public.agent_conversations USING btree (session_id);


--
-- Name: idx_directorio_area; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_directorio_area ON public.directorio_corporativo USING btree (area);


--
-- Name: idx_directorio_reporta; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_directorio_reporta ON public.directorio_corporativo USING btree (reporta_a);


--
-- Name: idx_doc_activo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_doc_activo ON public.documentacion_repositorio USING btree (activo);


--
-- Name: idx_doc_depto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_doc_depto ON public.documentacion_repositorio USING btree (departamento);


--
-- Name: idx_doc_proyecto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_doc_proyecto ON public.documentacion_repositorio USING btree (proyecto_id);


--
-- Name: idx_doc_silo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_doc_silo ON public.documentacion_repositorio USING btree (silo);


--
-- Name: idx_doc_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_doc_tags ON public.documentacion_repositorio USING gin (tags);


--
-- Name: idx_doc_tipo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_doc_tipo ON public.documentacion_repositorio USING btree (tipo);


--
-- Name: idx_gov_gate; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gov_gate ON public.pmo_governance_scoring USING btree (gate_status);


--
-- Name: idx_gov_pm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gov_pm ON public.pmo_governance_scoring USING btree (id_pm);


--
-- Name: idx_gov_proyecto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gov_proyecto ON public.pmo_governance_scoring USING btree (id_proyecto);


--
-- Name: idx_gov_tx_sync; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gov_tx_sync ON public.gobernanza_transacciones USING btree (sync_status) WHERE ((sync_status)::text = ANY ((ARRAY['PENDIENTE'::character varying, 'EN_PROCESO'::character varying])::text[]));


--
-- Name: idx_inc_complejidad; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inc_complejidad ON public.catalogo_incidencias USING btree (complejidad);


--
-- Name: idx_inc_prioridad; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inc_prioridad ON public.catalogo_incidencias USING btree (prioridad_sugerida);


--
-- Name: idx_inc_run_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inc_run_estado ON public.incidencias_run USING btree (estado);


--
-- Name: idx_inc_run_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inc_run_fecha ON public.incidencias_run USING btree (timestamp_creacion);


--
-- Name: idx_inc_run_prioridad; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inc_run_prioridad ON public.incidencias_run USING btree (prioridad_ia);


--
-- Name: idx_inc_run_tecnico; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inc_run_tecnico ON public.incidencias_run USING btree (tecnico_asignado);


--
-- Name: idx_inc_skills_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inc_skills_gin ON public.catalogo_incidencias USING gin (skills_requeridas);


--
-- Name: idx_kanban_columna; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_kanban_columna ON public.kanban_tareas USING btree (columna);


--
-- Name: idx_kanban_incidencia; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_kanban_incidencia ON public.kanban_tareas USING btree (id_incidencia);


--
-- Name: idx_kanban_proyecto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_kanban_proyecto ON public.kanban_tareas USING btree (id_proyecto);


--
-- Name: idx_kanban_recent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_kanban_recent ON public.kanban_tareas USING btree (fecha_creacion DESC);


--
-- Name: idx_kanban_tecnico; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_kanban_tecnico ON public.kanban_tareas USING btree (id_tecnico);


--
-- Name: idx_kanban_tipo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_kanban_tipo ON public.kanban_tareas USING btree (tipo);


--
-- Name: idx_pipeline_sessions_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pipeline_sessions_estado ON public.pipeline_sessions USING btree (estado, updated_at DESC);


--
-- Name: idx_pm_especialidad; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pm_especialidad ON public.pmo_project_managers USING btree (especialidad);


--
-- Name: idx_pm_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pm_estado ON public.pmo_project_managers USING btree (estado);


--
-- Name: idx_pm_incident; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pm_incident ON public.postmortem_reports USING btree (incident_id);


--
-- Name: idx_pm_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pm_priority ON public.postmortem_reports USING btree (incident_priority);


--
-- Name: idx_pres_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pres_estado ON public.presupuestos USING btree (estado);


--
-- Name: idx_pres_proyecto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pres_proyecto ON public.presupuestos USING btree (id_proyecto);


--
-- Name: idx_pres_responsable; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pres_responsable ON public.presupuestos USING btree (responsable);


--
-- Name: idx_rbac_audit_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rbac_audit_timestamp ON public.rbac_audit_log USING btree ("timestamp");


--
-- Name: idx_rbac_audit_usuario; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rbac_audit_usuario ON public.rbac_audit_log USING btree (id_usuario);


--
-- Name: idx_rbac_sesiones_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rbac_sesiones_token ON public.rbac_sesiones USING btree (token_hash);


--
-- Name: idx_rbac_sesiones_usuario; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rbac_sesiones_usuario ON public.rbac_sesiones USING btree (id_usuario);


--
-- Name: idx_rbac_usuarios_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rbac_usuarios_email ON public.rbac_usuarios USING btree (email);


--
-- Name: idx_rbac_usuarios_recurso; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rbac_usuarios_recurso ON public.rbac_usuarios USING btree (id_recurso);


--
-- Name: idx_rbac_usuarios_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rbac_usuarios_role ON public.rbac_usuarios USING btree (id_role);


--
-- Name: idx_rip_ticket; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rip_ticket ON public.run_incident_plans USING btree (ticket_id);


--
-- Name: idx_sim_risk; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sim_risk ON public.whatif_simulations USING btree (risk_score DESC);


--
-- Name: idx_sim_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sim_type ON public.whatif_simulations USING btree (scenario_type);


--
-- Name: idx_staff_carga; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_staff_carga ON public.pmo_staff_skills USING btree (carga_actual);


--
-- Name: idx_staff_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_staff_estado ON public.pmo_staff_skills USING btree (estado_run);


--
-- Name: idx_staff_nivel; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_staff_nivel ON public.pmo_staff_skills USING btree (nivel);


--
-- Name: idx_staff_silo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_staff_silo ON public.pmo_staff_skills USING btree (silo_especialidad);


--
-- Name: idx_staff_skills_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_staff_skills_gin ON public.pmo_staff_skills USING gin (skills_json);


--
-- Name: idx_txn_agente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_txn_agente ON public.gobernanza_transacciones USING btree (agente_origen);


--
-- Name: idx_txn_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_txn_fecha ON public.gobernanza_transacciones USING btree (timestamp_ejecucion);


--
-- Name: idx_txn_fte; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_txn_fte ON public.gobernanza_transacciones USING btree (fte_afectado);


--
-- Name: idx_txn_proyecto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_txn_proyecto ON public.gobernanza_transacciones USING btree (id_proyecto);


--
-- Name: idx_txn_tipo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_txn_tipo ON public.gobernanza_transacciones USING btree (tipo_accion);


--
-- Name: idx_wr_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wr_status ON public.war_room_sessions USING btree (status);


--
-- Name: idx_wr_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wr_type ON public.war_room_sessions USING btree (session_type);


--
-- Name: cartera_build trg_cambio_estado_proyecto; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_cambio_estado_proyecto BEFORE UPDATE ON public.cartera_build FOR EACH ROW EXECUTE FUNCTION public.fn_registrar_cambio_estado();


--
-- Name: cartera_build cartera_build_responsable_asignado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cartera_build
    ADD CONSTRAINT cartera_build_responsable_asignado_fkey FOREIGN KEY (responsable_asignado) REFERENCES public.pmo_staff_skills(id_recurso);


--
-- Name: cmdb_activo_software cmdb_activo_software_id_activo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_activo_software
    ADD CONSTRAINT cmdb_activo_software_id_activo_fkey FOREIGN KEY (id_activo) REFERENCES public.cmdb_activos(id_activo) ON DELETE CASCADE;


--
-- Name: cmdb_activo_software cmdb_activo_software_id_software_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_activo_software
    ADD CONSTRAINT cmdb_activo_software_id_software_fkey FOREIGN KEY (id_software) REFERENCES public.cmdb_software(id_software) ON DELETE CASCADE;


--
-- Name: cmdb_activos cmdb_activos_id_categoria_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_activos
    ADD CONSTRAINT cmdb_activos_id_categoria_fkey FOREIGN KEY (id_categoria) REFERENCES public.cmdb_categorias(id_categoria);


--
-- Name: cmdb_cambios cmdb_cambios_id_activo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_cambios
    ADD CONSTRAINT cmdb_cambios_id_activo_fkey FOREIGN KEY (id_activo) REFERENCES public.cmdb_activos(id_activo);


--
-- Name: cmdb_costes cmdb_costes_id_activo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_costes
    ADD CONSTRAINT cmdb_costes_id_activo_fkey FOREIGN KEY (id_activo) REFERENCES public.cmdb_activos(id_activo);


--
-- Name: cmdb_ips cmdb_ips_id_activo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_ips
    ADD CONSTRAINT cmdb_ips_id_activo_fkey FOREIGN KEY (id_activo) REFERENCES public.cmdb_activos(id_activo);


--
-- Name: cmdb_ips cmdb_ips_id_vlan_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_ips
    ADD CONSTRAINT cmdb_ips_id_vlan_fkey FOREIGN KEY (id_vlan) REFERENCES public.cmdb_vlans(id_vlan);


--
-- Name: cmdb_relaciones cmdb_relaciones_id_activo_destino_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_relaciones
    ADD CONSTRAINT cmdb_relaciones_id_activo_destino_fkey FOREIGN KEY (id_activo_destino) REFERENCES public.cmdb_activos(id_activo) ON DELETE CASCADE;


--
-- Name: cmdb_relaciones cmdb_relaciones_id_activo_origen_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cmdb_relaciones
    ADD CONSTRAINT cmdb_relaciones_id_activo_origen_fkey FOREIGN KEY (id_activo_origen) REFERENCES public.cmdb_activos(id_activo) ON DELETE CASCADE;


--
-- Name: directorio_corporativo directorio_corporativo_reporta_a_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.directorio_corporativo
    ADD CONSTRAINT directorio_corporativo_reporta_a_fkey FOREIGN KEY (reporta_a) REFERENCES public.directorio_corporativo(id_directivo);


--
-- Name: gobernanza_transacciones gobernanza_transacciones_fte_afectado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gobernanza_transacciones
    ADD CONSTRAINT gobernanza_transacciones_fte_afectado_fkey FOREIGN KEY (fte_afectado) REFERENCES public.pmo_staff_skills(id_recurso);


--
-- Name: gobernanza_transacciones gobernanza_transacciones_id_proyecto_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gobernanza_transacciones
    ADD CONSTRAINT gobernanza_transacciones_id_proyecto_fkey FOREIGN KEY (id_proyecto) REFERENCES public.cartera_build(id_proyecto);


--
-- Name: incidencias_run incidencias_run_id_catalogo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incidencias_run
    ADD CONSTRAINT incidencias_run_id_catalogo_fkey FOREIGN KEY (id_catalogo) REFERENCES public.catalogo_incidencias(id_catalogo);


--
-- Name: incidencias_run incidencias_run_tecnico_asignado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.incidencias_run
    ADD CONSTRAINT incidencias_run_tecnico_asignado_fkey FOREIGN KEY (tecnico_asignado) REFERENCES public.pmo_staff_skills(id_recurso);


--
-- Name: kanban_tareas kanban_tareas_id_tecnico_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kanban_tareas
    ADD CONSTRAINT kanban_tareas_id_tecnico_fkey FOREIGN KEY (id_tecnico) REFERENCES public.pmo_staff_skills(id_recurso);


--
-- Name: pmo_governance_scoring pmo_governance_scoring_id_pm_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pmo_governance_scoring
    ADD CONSTRAINT pmo_governance_scoring_id_pm_fkey FOREIGN KEY (id_pm) REFERENCES public.pmo_project_managers(id_pm);


--
-- Name: rbac_role_permisos rbac_role_permisos_id_permiso_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_permisos
    ADD CONSTRAINT rbac_role_permisos_id_permiso_fkey FOREIGN KEY (id_permiso) REFERENCES public.rbac_permisos(id_permiso) ON DELETE CASCADE;


--
-- Name: rbac_role_permisos rbac_role_permisos_id_role_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_role_permisos
    ADD CONSTRAINT rbac_role_permisos_id_role_fkey FOREIGN KEY (id_role) REFERENCES public.rbac_roles(id_role) ON DELETE CASCADE;


--
-- Name: rbac_sesiones rbac_sesiones_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_sesiones
    ADD CONSTRAINT rbac_sesiones_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.rbac_usuarios(id_usuario) ON DELETE CASCADE;


--
-- Name: rbac_usuarios rbac_usuarios_id_role_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rbac_usuarios
    ADD CONSTRAINT rbac_usuarios_id_role_fkey FOREIGN KEY (id_role) REFERENCES public.rbac_roles(id_role);


--
-- PostgreSQL database dump complete
--

\unrestrict pqkMpgHPStZNsafY1qkT5e27O1FUkq82c5FfsCEwdeJG30e7Y7kWLHtdVdDwJcV


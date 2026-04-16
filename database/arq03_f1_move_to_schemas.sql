-- =====================================================================
-- ARQ-03 F1 — Mover public → compartido + primitiva
-- Atómico. Un fallo deshace todo.
-- Ver _dumps/arq03/F0_reparto_tablas.md (contrato firmado)
--     _dumps/arq03/F1_preflight.md (verificación pre-move)
--
-- Conteo real (corregido del typo del contrato F0):
--   18 tablas Caja A → compartido
--   51 tablas Caja B → primitiva   (NO 50 como decía el contrato)
--   3 secuencias huérfanas → primitiva
--   7 funciones del proyecto (1 → compartido, 6 → primitiva)
--   12 vistas (2 → compartido, 10 → primitiva)
-- =====================================================================

BEGIN;

-- Lock de tabla de metadatos para serialización
LOCK TABLE pg_catalog.pg_namespace IN SHARE MODE;

-- 1) Esquemas
CREATE SCHEMA IF NOT EXISTS compartido;
CREATE SCHEMA IF NOT EXISTS primitiva;

COMMENT ON SCHEMA compartido IS 'ARQ-03: pool/catálogos únicos para los 5 mundos';
COMMENT ON SCHEMA primitiva  IS 'ARQ-03: mundo primitivo, plantilla de los bancos';

-- 2) search_path local para que las verificaciones siguientes funcionen
SET LOCAL search_path = primitiva, compartido, public;

-- ════════════════════════════════════════════════════════════════════
-- 3) Tablas Caja A → compartido (18)
-- ════════════════════════════════════════════════════════════════════
ALTER TABLE public.pmo_staff_skills            SET SCHEMA compartido;
ALTER TABLE public.pmo_project_managers        SET SCHEMA compartido;
ALTER TABLE public.rbac_usuarios               SET SCHEMA compartido;
ALTER TABLE public.rbac_roles                  SET SCHEMA compartido;
ALTER TABLE public.rbac_permisos               SET SCHEMA compartido;
ALTER TABLE public.rbac_role_permisos          SET SCHEMA compartido;
ALTER TABLE public.rbac_sesiones               SET SCHEMA compartido;
ALTER TABLE public.rbac_audit_log              SET SCHEMA compartido;
ALTER TABLE public.catalogo_incidencias        SET SCHEMA compartido;
ALTER TABLE public.catalogo_skills             SET SCHEMA compartido;
ALTER TABLE public.cmdb_categorias             SET SCHEMA compartido;
ALTER TABLE public.documentacion_repositorio   SET SCHEMA compartido;
ALTER TABLE public.p96_governors               SET SCHEMA compartido;
ALTER TABLE public.p96_run_layers              SET SCHEMA compartido;
ALTER TABLE public.p96_run_crits               SET SCHEMA compartido;
ALTER TABLE public.p96_run_matrix              SET SCHEMA compartido;
ALTER TABLE public.p96_strategy_frameworks     SET SCHEMA compartido;
ALTER TABLE public.calendario_periodos_demanda SET SCHEMA compartido;

-- ════════════════════════════════════════════════════════════════════
-- 4) Tablas Caja B → primitiva (51)
-- ════════════════════════════════════════════════════════════════════
-- 4.a) Familia incidencias (2)
ALTER TABLE public.incidencias_run             SET SCHEMA primitiva;
ALTER TABLE public.incidencias_live            SET SCHEMA primitiva;

-- 4.b) Familia build (8)
ALTER TABLE public.build_live                  SET SCHEMA primitiva;
ALTER TABLE public.build_subtasks              SET SCHEMA primitiva;
ALTER TABLE public.build_risks                 SET SCHEMA primitiva;
ALTER TABLE public.build_stakeholders          SET SCHEMA primitiva;
ALTER TABLE public.build_quality_gates         SET SCHEMA primitiva;
ALTER TABLE public.build_sprints               SET SCHEMA primitiva;
ALTER TABLE public.build_sprint_items          SET SCHEMA primitiva;
ALTER TABLE public.build_project_plans         SET SCHEMA primitiva;

-- 4.c) Familia CMDB (12 — todas excepto cmdb_categorias que es A)
ALTER TABLE public.cmdb_activos                SET SCHEMA primitiva;
ALTER TABLE public.cmdb_relaciones             SET SCHEMA primitiva;
ALTER TABLE public.cmdb_change_windows         SET SCHEMA primitiva;
ALTER TABLE public.cmdb_ips                    SET SCHEMA primitiva;
ALTER TABLE public.cmdb_vlans                  SET SCHEMA primitiva;
ALTER TABLE public.cmdb_software               SET SCHEMA primitiva;
ALTER TABLE public.cmdb_activo_software        SET SCHEMA primitiva;
ALTER TABLE public.cmdb_cambios                SET SCHEMA primitiva;
ALTER TABLE public.cmdb_costes                 SET SCHEMA primitiva;
ALTER TABLE public.cmdb_change_proposals       SET SCHEMA primitiva;
ALTER TABLE public.cmdb_change_approvals       SET SCHEMA primitiva;
ALTER TABLE public.cmdb_demand_history         SET SCHEMA primitiva;

-- 4.d) Familia kanban (2)
ALTER TABLE public.kanban_tareas               SET SCHEMA primitiva;
ALTER TABLE public.kanban_wip_limits           SET SCHEMA primitiva;

-- 4.e) Familia agentes (2)
ALTER TABLE public.agent_conversations         SET SCHEMA primitiva;
ALTER TABLE public.agent_performance_metrics   SET SCHEMA primitiva;

-- 4.f) Familia ITSM (1)
ALTER TABLE public.itsm_form_drafts            SET SCHEMA primitiva;

-- 4.g) Familia tech (6)
ALTER TABLE public.tech_chat_salas             SET SCHEMA primitiva;
ALTER TABLE public.tech_chat_mensajes          SET SCHEMA primitiva;
ALTER TABLE public.tech_notificaciones         SET SCHEMA primitiva;
ALTER TABLE public.tech_terminal_log           SET SCHEMA primitiva;
ALTER TABLE public.tech_adjuntos               SET SCHEMA primitiva;
ALTER TABLE public.tech_valoracion_mensual     SET SCHEMA primitiva;

-- 4.h) Familia gobernanza (2)
ALTER TABLE public.gobernanza_transacciones    SET SCHEMA primitiva;
ALTER TABLE public.pmo_governance_scoring      SET SCHEMA primitiva;

-- 4.i) Familia simulación (2)
ALTER TABLE public.whatif_simulations          SET SCHEMA primitiva;
ALTER TABLE public.war_room_sessions           SET SCHEMA primitiva;

-- 4.j) Familia compliance (2)
ALTER TABLE public.compliance_audits           SET SCHEMA primitiva;
ALTER TABLE public.postmortem_reports          SET SCHEMA primitiva;

-- 4.k) Sueltas operativas (5)
ALTER TABLE public.intelligent_alerts          SET SCHEMA primitiva;
ALTER TABLE public.cartera_build               SET SCHEMA primitiva;
ALTER TABLE public.directorio_corporativo     SET SCHEMA primitiva;
ALTER TABLE public.presupuestos                SET SCHEMA primitiva;
ALTER TABLE public.pipeline_sessions           SET SCHEMA primitiva;

-- 4.l) Familia p96 pulse + detail (7)
ALTER TABLE public.p96_pulse_kpis              SET SCHEMA primitiva;
ALTER TABLE public.p96_pulse_alerts            SET SCHEMA primitiva;
ALTER TABLE public.p96_pulse_blocks            SET SCHEMA primitiva;
ALTER TABLE public.p96_pulse_decisions         SET SCHEMA primitiva;
ALTER TABLE public.p96_pulse_responsables      SET SCHEMA primitiva;
ALTER TABLE public.p96_pulse_hitos             SET SCHEMA primitiva;
ALTER TABLE public.p96_build_project_detail    SET SCHEMA primitiva;

-- ════════════════════════════════════════════════════════════════════
-- 5) Secuencias huérfanas → primitiva (3)
-- ════════════════════════════════════════════════════════════════════
ALTER SEQUENCE public.inc_ticket_seq           SET SCHEMA primitiva;
ALTER SEQUENCE public.itsm_draft_seq           SET SCHEMA primitiva;
ALTER SEQUENCE public.seq_txn                  SET SCHEMA primitiva;

-- ════════════════════════════════════════════════════════════════════
-- 6) Funciones del proyecto (7) — 1 compartido, 6 primitiva
-- ════════════════════════════════════════════════════════════════════
ALTER FUNCTION public.buscar_tecnico_por_skill(text, text)
  SET SCHEMA compartido;  -- usa pmo_staff_skills (A)

ALTER FUNCTION public.generar_ticket_id()              SET SCHEMA primitiva;
ALTER FUNCTION public.generar_draft_id()               SET SCHEMA primitiva;
ALTER FUNCTION public.fn_registrar_cambio_estado()     SET SCHEMA primitiva;
ALTER FUNCTION public.fn_validar_ventana_cambio(integer, timestamp without time zone, character varying)
  SET SCHEMA primitiva;
ALTER FUNCTION public.trigger_run_to_live_insert()     SET SCHEMA primitiva;
ALTER FUNCTION public.trigger_run_to_live_update()     SET SCHEMA primitiva;

-- ════════════════════════════════════════════════════════════════════
-- 7) Vistas (12) — 2 compartido, 10 primitiva
-- ════════════════════════════════════════════════════════════════════
ALTER VIEW public.vista_carga_por_silo          SET SCHEMA compartido;
ALTER VIEW public.v_proxima_ejecucion_gabinete  SET SCHEMA compartido;

ALTER VIEW public.agent_conversations_cobertura SET SCHEMA primitiva;
ALTER VIEW public.v_cambios_pendientes_aplicar  SET SCHEMA primitiva;
ALTER VIEW public.v_p96_build_portfolio         SET SCHEMA primitiva;
ALTER VIEW public.v_p96_run_cis                 SET SCHEMA primitiva;
ALTER VIEW public.v_p96_run_incidents           SET SCHEMA primitiva;
ALTER VIEW public.view_disponibilidad_global    SET SCHEMA primitiva;
ALTER VIEW public.vista_audit_gobernanza        SET SCHEMA primitiva;
ALTER VIEW public.vista_portafolio_build        SET SCHEMA primitiva;
ALTER VIEW public.vista_proyectos_riesgo        SET SCHEMA primitiva;
ALTER VIEW public.vista_serie_temporal_incidencias SET SCHEMA primitiva;

-- ════════════════════════════════════════════════════════════════════
-- 8) search_path por rol (afecta a conexiones NUEVAS)
-- ════════════════════════════════════════════════════════════════════
ALTER ROLE jose_admin SET search_path = primitiva, compartido, public;

-- ════════════════════════════════════════════════════════════════════
-- 9) Verificaciones dentro de la misma transacción
-- ════════════════════════════════════════════════════════════════════
DO $$
DECLARE
  n_public_tablas  int;
  n_comp_tablas    int;
  n_prim_tablas    int;
  n_public_seq     int;
  n_prim_seq       int;
  n_public_fn      int;
  n_public_trgm    int;
  n_public_views   int;
BEGIN
  SELECT count(*) INTO n_public_tablas
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relkind='r';

  SELECT count(*) INTO n_comp_tablas
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='compartido' AND c.relkind='r';

  SELECT count(*) INTO n_prim_tablas
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='primitiva' AND c.relkind='r';

  SELECT count(*) INTO n_public_seq
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relkind='S';

  SELECT count(*) INTO n_prim_seq
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='primitiva' AND c.relkind='S';

  SELECT count(*) INTO n_public_fn
    FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
    WHERE n.nspname='public' AND p.prolang <> (SELECT oid FROM pg_language WHERE lanname='c');

  SELECT count(*) INTO n_public_trgm
    FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
    WHERE n.nspname='public' AND p.prolang = (SELECT oid FROM pg_language WHERE lanname='c');

  SELECT count(*) INTO n_public_views
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relkind IN ('v','m');

  RAISE NOTICE 'public tablas=%, compartido tablas=%, primitiva tablas=%',
    n_public_tablas, n_comp_tablas, n_prim_tablas;
  RAISE NOTICE 'public seq=%, primitiva seq=%', n_public_seq, n_prim_seq;
  RAISE NOTICE 'public fn proyecto=%, public fn pg_trgm=%', n_public_fn, n_public_trgm;
  RAISE NOTICE 'public views=%', n_public_views;

  IF n_public_tablas <> 0 THEN
    RAISE EXCEPTION 'F1 FALLA: quedan % tablas en public (deberían ser 0)', n_public_tablas;
  END IF;
  IF n_comp_tablas <> 18 THEN
    RAISE EXCEPTION 'F1 FALLA: compartido tiene % tablas (esperadas 18)', n_comp_tablas;
  END IF;
  IF n_prim_tablas <> 51 THEN
    RAISE EXCEPTION 'F1 FALLA: primitiva tiene % tablas (esperadas 51)', n_prim_tablas;
  END IF;
  IF n_public_fn <> 0 THEN
    RAISE EXCEPTION 'F1 FALLA: quedan % funciones del proyecto en public', n_public_fn;
  END IF;
  IF n_public_views <> 0 THEN
    RAISE EXCEPTION 'F1 FALLA: quedan % vistas en public', n_public_views;
  END IF;
  IF n_public_trgm < 20 THEN
    RAISE EXCEPTION 'F1 FALLA: pg_trgm parece incompleta (% funciones C)', n_public_trgm;
  END IF;

  RAISE NOTICE '── F1 VERIFICACIÓN OK ──';
END $$;

COMMIT;

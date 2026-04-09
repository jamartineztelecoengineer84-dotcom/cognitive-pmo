-- =====================================================================
-- ARQ-03 F2.0 — Mover funciones del proyecto de primitiva a compartido
-- Motivo: permitir que cualquier esquema escenario (sc_*) las invoque
--         resolviendo por search_path. Single source of truth.
-- Atómico: un fallo deshace todo.
--
-- Signatures verificadas con pg_get_function_identity_arguments en
-- F2.0 PASO 1 (2026-04-09).
-- =====================================================================

BEGIN;

LOCK TABLE pg_catalog.pg_namespace IN SHARE MODE;

-- Mover las 6 funciones de primitiva a compartido
ALTER FUNCTION primitiva.generar_ticket_id()                       SET SCHEMA compartido;
ALTER FUNCTION primitiva.generar_draft_id()                        SET SCHEMA compartido;
ALTER FUNCTION primitiva.fn_registrar_cambio_estado()              SET SCHEMA compartido;
ALTER FUNCTION primitiva.fn_validar_ventana_cambio(integer, timestamp without time zone, character varying)
                                                                   SET SCHEMA compartido;
ALTER FUNCTION primitiva.trigger_run_to_live_insert()              SET SCHEMA compartido;
ALTER FUNCTION primitiva.trigger_run_to_live_update()              SET SCHEMA compartido;

-- Verificaciones
DO $$
DECLARE
  n_prim int;
  n_comp int;
BEGIN
  SELECT count(*) INTO n_prim
    FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
    JOIN pg_language l ON l.oid=p.prolang
    WHERE n.nspname='primitiva' AND l.lanname IN ('plpgsql','sql');

  SELECT count(*) INTO n_comp
    FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
    JOIN pg_language l ON l.oid=p.prolang
    WHERE n.nspname='compartido' AND l.lanname IN ('plpgsql','sql');

  RAISE NOTICE 'funciones primitiva=%, compartido=%', n_prim, n_comp;

  IF n_prim <> 0 THEN
    RAISE EXCEPTION 'F2.0 FALLA: quedan % funciones en primitiva', n_prim;
  END IF;
  IF n_comp <> 7 THEN
    RAISE EXCEPTION 'F2.0 FALLA: compartido tiene % funciones (esperadas 7)', n_comp;
  END IF;

  RAISE NOTICE '── F2.0 VERIFICACIÓN OK ──';
END $$;

COMMIT;

-- ARQ-02 F4 — rename run_incident_plans → itsm_form_drafts
-- Fase: ARQ-02 F4
-- Fecha: 2026-04-08
-- Commit: <pendiente, rellenar en F6>
--
-- La tabla run_incident_plans era engañosamente nombrada: contiene el
-- catálogo ITSM (61 filas RUN-CAT-NNN seed inicial) Y los drafts del
-- formulario del shell (N filas RUN-YYYYMMDD-HEX). El nombre correcto
-- es itsm_form_drafts. Contrato API intacto: los 3 endpoints
-- /run/plans* siguen con la misma URL, mismo body, mismo behavior.
--
-- Cleanup pre-rename: elimina los drafts drift de los smokes F1.4+F2.3
-- que no fueron limpiados en los rollbacks anteriores (F-ARQ02-08
-- descubierta en F4.0: el shell llama POST /run/plans en paralelo a
-- POST /incidencias, sin coordinarse, y los rollbacks de F1.4/F2.3 solo
-- limpiaron incidencias_run/live).
--
-- Idempotente: guards en pre-checks que abortan si la tabla ya fue
-- renombrada o si hay FKs imprevistas.

BEGIN;

-- Guard 1: tabla origen existe, destino no existe
DO $$
BEGIN
  IF to_regclass('public.run_incident_plans') IS NULL THEN
    RAISE EXCEPTION 'run_incident_plans no existe — ya renombrada?';
  END IF;
  IF to_regclass('public.itsm_form_drafts') IS NOT NULL THEN
    RAISE EXCEPTION 'itsm_form_drafts ya existe — conflicto de rename';
  END IF;
END $$;

-- Guard 2: cero FKs apuntando a run_incident_plans
DO $$
DECLARE fk_count INT;
BEGIN
  SELECT COUNT(*) INTO fk_count
  FROM information_schema.referential_constraints rc
  JOIN information_schema.constraint_column_usage ccu
    ON rc.constraint_name = ccu.constraint_name
  WHERE ccu.table_name = 'run_incident_plans';
  IF fk_count > 0 THEN
    RAISE EXCEPTION '% FKs apuntan a run_incident_plans (esperaba 0)', fk_count;
  END IF;
END $$;

-- Cleanup drift: drafts del shell de los smokes F1.4+F2.3
DELETE FROM run_incident_plans
WHERE id ~ '^RUN-2026[0-9]{4}-[A-F0-9]{4}$';

-- Rename tabla + índices para coherencia
ALTER TABLE run_incident_plans RENAME TO itsm_form_drafts;
ALTER INDEX run_incident_plans_pkey RENAME TO itsm_form_drafts_pkey;
ALTER INDEX idx_rip_ticket RENAME TO idx_itsm_drafts_ticket;

COMMIT;

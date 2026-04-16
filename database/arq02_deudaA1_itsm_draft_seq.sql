-- ARQ-02 Deuda A · A.1 — F-ARQ02-09: SEQUENCE atómica para itsm_form_drafts.id
-- Fase: Deuda A.1
-- Fecha: 2026-04-09
-- Commit: <pendiente, rellenar al consolidar>
--
-- Reemplaza el patrón legacy uuid4().hex[:4] que usa POST /run/plans para
-- generar plan_id (RUN-YYYYMMDD-HEX) por una SEQUENCE PostgreSQL atómica
-- + función envolvente generar_draft_id() que devuelve el formato nuevo
-- RUN-NNNNNN-YYYYMMDD (mismo patrón que generar_ticket_id() de F1.0).
--
-- Idempotente: CREATE SEQUENCE IF NOT EXISTS + CREATE OR REPLACE FUNCTION.
-- Re-aplicable sin daño.

BEGIN;

CREATE SEQUENCE IF NOT EXISTS itsm_draft_seq
  START WITH 1
  INCREMENT BY 1
  NO MAXVALUE
  NO CYCLE;

CREATE OR REPLACE FUNCTION generar_draft_id() RETURNS varchar AS $$
  SELECT 'RUN-' || lpad(nextval('itsm_draft_seq')::text, 6, '0')
              || '-' || to_char(current_date, 'YYYYMMDD');
$$ LANGUAGE SQL;

COMMIT;

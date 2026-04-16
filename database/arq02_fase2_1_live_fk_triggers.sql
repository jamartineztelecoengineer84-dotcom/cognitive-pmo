-- ARQ-02 F2.1 — incidencias_live FK + triggers run→live
-- Fase: ARQ-02 F2.1
-- Fecha: 2026-04-08
-- Commit: <pendiente, rellenar en F6>
--
-- Establece que incidencias_live ⊆ incidencias_run mediante FK con ON DELETE
-- CASCADE + ON UPDATE CASCADE, y mantiene la sincronización automática vía
-- 2 triggers AFTER ROW en incidencias_run:
--
--   - trg_run_to_live_insert: cuando se inserta un ticket con estado abierto
--     (QUEUED|EN_CURSO|ESCALADO), crea automáticamente la fila correspondiente
--     en incidencias_live con estado='IN_PROGRESS' (semántica UI hardcoded).
--
--   - trg_run_to_live_update: cuando un ticket cambia campos no-UI, propaga a
--     live. Si pasa a RESUELTO/CERRADO, borra de live. Si reabre (RESUELTO →
--     QUEUED), recrea la fila vía fallback IF NOT FOUND.
--
-- Las columnas UI (progreso_pct, total_tareas, tareas_completadas) NUNCA son
-- tocadas por los triggers — siguen siendo escribibles solo vía
-- PUT /incidencias/live/{id}/progreso desde el frontend.
--
-- Idempotente y re-ejecutable: usa CREATE OR REPLACE FUNCTION,
-- DROP TRIGGER IF EXISTS, y guards condicionales en ALTER/ADD CONSTRAINT.

BEGIN;

-- ─── ALTER tipo (idempotente) ───
DO $$
BEGIN
  IF (
    SELECT format_type(atttypid, atttypmod)
    FROM pg_attribute
    WHERE attrelid = 'incidencias_live'::regclass
      AND attname = 'ticket_id'
  ) <> 'character varying(30)' THEN
    ALTER TABLE incidencias_live ALTER COLUMN ticket_id TYPE varchar(30);
  END IF;
END $$;

-- ─── ADD CONSTRAINT FK (idempotente) ───
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'incidencias_live_ticket_id_fkey'
      AND conrelid = 'incidencias_live'::regclass
  ) THEN
    ALTER TABLE incidencias_live
      ADD CONSTRAINT incidencias_live_ticket_id_fkey
      FOREIGN KEY (ticket_id) REFERENCES incidencias_run(ticket_id)
      ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;

-- ─── trigger_run_to_live_insert ───
CREATE OR REPLACE FUNCTION trigger_run_to_live_insert() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.estado IN ('QUEUED','EN_CURSO','ESCALADO') THEN
    INSERT INTO incidencias_live (
      ticket_id, incidencia_detectada, prioridad, categoria, estado,
      sla_horas, tecnico_asignado, area_afectada, fecha_creacion, fecha_limite,
      agente_origen, canal_entrada, reportado_por, servicio_afectado,
      impacto_negocio, notas
    ) VALUES (
      NEW.ticket_id, NEW.incidencia_detectada, NEW.prioridad_ia, NEW.categoria,
      'IN_PROGRESS',
      NEW.sla_limite, NEW.tecnico_asignado, NEW.area_afectada,
      NEW.timestamp_creacion,
      NEW.timestamp_creacion + make_interval(hours => NEW.sla_limite::int),
      COALESCE(NEW.agente_origen, 'AG-001'),
      NEW.canal_entrada, NEW.reportado_por, NEW.servicio_afectado,
      NEW.impacto_negocio, NEW.notas_adicionales
    ) ON CONFLICT (ticket_id) DO NOTHING;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_run_to_live_insert ON incidencias_run;
CREATE TRIGGER trg_run_to_live_insert
  AFTER INSERT ON incidencias_run
  FOR EACH ROW EXECUTE FUNCTION trigger_run_to_live_insert();

-- ─── trigger_run_to_live_update (con fallback INSERT para reapertura) ───
CREATE OR REPLACE FUNCTION trigger_run_to_live_update() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.estado IN ('RESUELTO','CERRADO') THEN
    DELETE FROM incidencias_live WHERE ticket_id = NEW.ticket_id;
  ELSIF NEW.estado IN ('QUEUED','EN_CURSO','ESCALADO') THEN
    UPDATE incidencias_live SET
      incidencia_detectada = NEW.incidencia_detectada,
      prioridad            = NEW.prioridad_ia,
      categoria            = NEW.categoria,
      sla_horas            = NEW.sla_limite,
      tecnico_asignado     = NEW.tecnico_asignado,
      area_afectada        = NEW.area_afectada,
      fecha_limite         = NEW.timestamp_creacion + make_interval(hours => NEW.sla_limite::int),
      servicio_afectado    = NEW.servicio_afectado,
      impacto_negocio      = NEW.impacto_negocio,
      notas                = NEW.notas_adicionales
      -- NO se tocan: estado, progreso_pct, total_tareas, tareas_completadas
    WHERE ticket_id = NEW.ticket_id;
    IF NOT FOUND THEN
      INSERT INTO incidencias_live (
        ticket_id, incidencia_detectada, prioridad, categoria, estado,
        sla_horas, tecnico_asignado, area_afectada, fecha_creacion, fecha_limite,
        agente_origen, canal_entrada, reportado_por, servicio_afectado,
        impacto_negocio, notas
      ) VALUES (
        NEW.ticket_id, NEW.incidencia_detectada, NEW.prioridad_ia, NEW.categoria,
        'IN_PROGRESS',
        NEW.sla_limite, NEW.tecnico_asignado, NEW.area_afectada,
        NEW.timestamp_creacion,
        NEW.timestamp_creacion + make_interval(hours => NEW.sla_limite::int),
        COALESCE(NEW.agente_origen, 'AG-001'),
        NEW.canal_entrada, NEW.reportado_por, NEW.servicio_afectado,
        NEW.impacto_negocio, NEW.notas_adicionales
      ) ON CONFLICT (ticket_id) DO NOTHING;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_run_to_live_update ON incidencias_run;
CREATE TRIGGER trg_run_to_live_update
  AFTER UPDATE ON incidencias_run
  FOR EACH ROW EXECUTE FUNCTION trigger_run_to_live_update();

COMMIT;

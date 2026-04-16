-- ARQ-02 F5.1 — agent_conversations.ticket_id (SOFT, sin FK)
-- Fase: ARQ-02 F5.1
-- Fecha: 2026-04-09
-- Commit: <pendiente, rellenar en F6>
--
-- Añade una columna soft ticket_id (varchar(30) NULL, sin FK) a
-- agent_conversations + índice parcial. El backfill heurístico desde
-- el campo content (regex INC-YYYYMMDD-HEX → mapeo F1) se ejecuta en
-- el script bash envolvente arq02_fase5_run.sh, no aquí, porque usa
-- meta-comandos \copy de psql que no son SQL puro.
--
-- Idempotente: ALTER protegido por IF NOT EXISTS check, índice usa
-- CREATE INDEX IF NOT EXISTS.

-- F5.1.a: ALTER idempotente
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'agent_conversations' AND column_name = 'ticket_id'
  ) THEN
    ALTER TABLE agent_conversations ADD COLUMN ticket_id varchar(30) NULL;
    RAISE NOTICE 'F5.1.a: columna ticket_id añadida';
  ELSE
    RAISE NOTICE 'F5.1.a: columna ticket_id ya existe, skip';
  END IF;
END $$;

-- F5.1.d: Índice parcial idempotente
CREATE INDEX IF NOT EXISTS idx_conv_ticket
  ON agent_conversations(ticket_id) WHERE ticket_id IS NOT NULL;

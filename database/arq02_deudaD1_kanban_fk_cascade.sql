-- F-ARQ02-18 D.1 — FK CASCADE kanban_tareas.id_incidencia → incidencias_run(ticket_id)
-- Idempotente vía pg_constraint lookup. Post-C.2 hay 0 huérfanos,
-- validación de ALTER pasa instantánea (índice idx_kanban_incidencia presente).

BEGIN;

\echo '── PRE: huerfanos kanban_tareas ──'
SELECT COUNT(*) AS huerfanos
FROM kanban_tareas kt
WHERE kt.id_incidencia IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM incidencias_run ir WHERE ir.ticket_id = kt.id_incidencia);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'kanban_tareas_id_incidencia_fkey'
      AND conrelid = 'kanban_tareas'::regclass
  ) THEN
    ALTER TABLE kanban_tareas
      ADD CONSTRAINT kanban_tareas_id_incidencia_fkey
      FOREIGN KEY (id_incidencia)
      REFERENCES incidencias_run(ticket_id)
      ON DELETE CASCADE
      ON UPDATE CASCADE;
    RAISE NOTICE 'FK kanban_tareas_id_incidencia_fkey creada';
  ELSE
    RAISE NOTICE 'FK kanban_tareas_id_incidencia_fkey ya existe (idempotente)';
  END IF;
END $$;

\echo '── POST: constraints kanban_tareas (FK) ──'
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'kanban_tareas'::regclass AND contype = 'f'
ORDER BY conname;

COMMIT;

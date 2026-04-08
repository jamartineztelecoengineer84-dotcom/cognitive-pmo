#!/bin/bash
# ARQ-02 F5.1 — runner: ALTER + INDEX + backfill via \copy + verificaciones
# Idempotente: re-ejecutable sin daño porque ALTER tiene IF NOT EXISTS,
# CREATE INDEX usa IF NOT EXISTS, y el UPDATE solo afecta a filas con
# ticket_id IS NULL.
set -euo pipefail
export PGPASSWORD=Seacaboelabuso_0406

PSQL="psql -h 192.168.1.49 -U jose_admin -d cognitive_pmo -v ON_ERROR_STOP=1"
DIR=/root/cognitive-pmo

echo "== F5.1 pre-check baseline =="
$PSQL -c "
SELECT
  (SELECT COUNT(*) FROM agent_conversations) AS conv_total,
  (SELECT COUNT(*) FROM agent_conversations WHERE content ~ 'INC-[0-9]{8}-[A-F0-9]+') AS con_menciones_legacy;
"

echo "== F5.1.a/d: ALTER + INDEX =="
$PSQL -f $DIR/database/arq02_fase5_agent_conversations_ticket_id.sql

echo "== F5.1.b/c: TEMP MAP + BACKFILL (single transaction) =="
$PSQL << SQL
BEGIN;

CREATE TEMP TABLE _ticket_id_map (
  old_id text PRIMARY KEY,
  new_id text NOT NULL,
  ts text
) ON COMMIT DROP;

\copy _ticket_id_map (old_id, new_id, ts) FROM '$DIR/_dumps/arq02/ticket_id_map_F1.csv' WITH (FORMAT CSV, HEADER true)
\copy _ticket_id_map (old_id, new_id, ts) FROM '$DIR/_dumps/arq02/ticket_id_map_F1_2_1_extra.csv' WITH (FORMAT CSV, HEADER true)

\echo '── map_total (esperado 37) ──'
SELECT COUNT(*) AS map_total FROM _ticket_id_map;

\echo '── map_apuntando_a_fantasma (esperado 0) ──'
SELECT COUNT(*) AS map_apuntando_a_fantasma
FROM _ticket_id_map m
WHERE NOT EXISTS (SELECT 1 FROM incidencias_run r WHERE r.ticket_id = m.new_id);

\echo '── Backfill UPDATE ──'
UPDATE agent_conversations ac
SET ticket_id = m.new_id
FROM _ticket_id_map m
WHERE ac.ticket_id IS NULL
  AND ac.content ~ 'INC-[0-9]{8}-[A-F0-9]+'
  AND (regexp_match(ac.content, 'INC-[0-9]{8}-[A-F0-9]+'))[1] = m.old_id;

\echo '── Verificación post-backfill ──'
SELECT
  COUNT(*) AS total_conv,
  COUNT(*) FILTER (WHERE ticket_id IS NOT NULL) AS con_ticket_id,
  COUNT(*) FILTER (WHERE ticket_id IS NULL AND content ~ 'INC-[0-9]{8}-[A-F0-9]+') AS legacy_no_mapeados
FROM agent_conversations;

\echo '── fantasmas (esperado 0) ──'
SELECT COUNT(*) AS fantasmas
FROM agent_conversations ac
WHERE ac.ticket_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM incidencias_run r WHERE r.ticket_id = ac.ticket_id);

COMMIT;
SQL

echo "== F5.1 post-check =="
$PSQL -c "
SELECT
  (SELECT COUNT(*) FROM agent_conversations WHERE ticket_id IS NOT NULL) AS con_ticket,
  (SELECT COUNT(*) FROM agent_conversations WHERE ticket_id IS NULL AND content ~ 'INC-[0-9]{8}-[A-F0-9]+') AS legacy_huerfanos,
  (SELECT COUNT(*) FROM pg_indexes WHERE tablename='agent_conversations' AND indexname='idx_conv_ticket') AS index_creado;
"

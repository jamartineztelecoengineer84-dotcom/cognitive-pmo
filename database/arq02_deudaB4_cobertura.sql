-- ARQ-02 Deuda B.4 / F-ARQ02-13: vista de cobertura sobre agent_conversations
-- que excluye las 56 filas con menciones legacy huérfanas pre-F1.
--
-- Estas 56 filas mencionan tickets en formato legacy INC-YYYYMMDD-HEX que
-- fueron borrados antes de la migración F1 (probablemente seeds/scenarios
-- purgados en cleanups intermedios). Sus IDs no están en el _ticket_id_map
-- de F1 (verificado en B.2 y B.4 recon), por lo que NO son recuperables vía
-- backfill — son huérfanos terminales.
--
-- Esta vista permite calcular métricas honestas de "cobertura ticket_id"
-- excluyendo el ruido histórico irrecuperable. Las filas siguen vivas en la
-- tabla cruda agent_conversations (auditoría legítima del comportamiento de
-- los agentes en esos días).
--
-- Idempotente: CREATE OR REPLACE VIEW.

CREATE OR REPLACE VIEW agent_conversations_cobertura AS
SELECT *
FROM agent_conversations
WHERE NOT (
  ticket_id IS NULL
  AND content ~ 'INC-[0-9]{8}-[A-F0-9]+'
  AND created_at < '2026-04-07'
);

COMMENT ON VIEW agent_conversations_cobertura IS
  'F-ARQ02-13: excluye 56 filas con menciones legacy huérfanas pre-F1 (tickets purgados, no recuperables). Usar este view en métricas de cobertura ticket_id, no la tabla cruda.';

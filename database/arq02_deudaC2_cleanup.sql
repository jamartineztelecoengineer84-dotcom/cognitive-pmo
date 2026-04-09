-- ARQ-02 Deuda C.2 / F-ARQ02-06: cleanup one-shot de residuales de smokes
-- pre-Bloque A/B identificados por dry-run C.2 (ver _dumps/deuda_arq02/C_recon.md
-- sección 2).
--
-- NO es una migración estructural — es un wipe de datos basura identificados
-- explícitamente por su pattern (id, ticket_id) en el dry-run.
--
-- Idempotente: re-ejecutar no produce efectos si ya fue aplicado, porque los
-- DELETEs son por id/ticket explícito y los huérfanos por filtro NOT EXISTS.
--
-- Filas que se borran (orden topológico):
--   1) 12 kanban_tareas hijas de las 4 incidencias residuales (formato KT-*)
--   2) 35 kanban_tareas huérfanas (id_incidencia apunta a fantasma)
--   3) N agent_conversations vinculadas a las 4 incidencias residuales
--   4) 4 incidencias_run residuales (CASCADE limpia incidencias_live)
--   5) 1 build_live PRJ-MNQDXKA5 (smoke BUILD residual sin dependencias)

BEGIN;

\echo '── BASELINE pre-cleanup ──'
SELECT
  (SELECT count(*) FROM kanban_tareas    WHERE id NOT LIKE 'KAN-SC%')        AS kanban_legacy,
  (SELECT count(*) FROM incidencias_run  WHERE ticket_id NOT LIKE 'INC-SC%') AS inc_legacy,
  (SELECT count(*) FROM build_live       WHERE id_proyecto !~ '^PRJ-SC[A-D]') AS build_live_legacy,
  (SELECT count(*) FROM kanban_tareas k
    WHERE k.id_incidencia IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM incidencias_run r WHERE r.ticket_id = k.id_incidencia)) AS kanban_huerfanas;

-- ════════════════════════════════════════════════════════════════════
-- PASO 1 — Borrar las 12 kanban hijas de las 4 incidencias residuales
-- ════════════════════════════════════════════════════════════════════
\echo '── PASO 1: kanban hijas de las 4 incidencias residuales ──'
DELETE FROM kanban_tareas
WHERE id_incidencia IN (
  'INC-000037-20260401',
  'INC-000034-20260401',
  'INC-000035-20260408',
  'INC-000038-20260408'
);

-- ════════════════════════════════════════════════════════════════════
-- PASO 2 — Borrar las 35 kanban huérfanas (id_incidencia apunta a fantasma)
-- ════════════════════════════════════════════════════════════════════
\echo '── PASO 2: kanban huérfanas (NOT EXISTS parent en incidencias_run) ──'
DELETE FROM kanban_tareas k
WHERE k.id_incidencia IS NOT NULL
  AND k.id LIKE 'KT-%'
  AND k.id NOT LIKE 'KAN-SC%'
  AND NOT EXISTS (
    SELECT 1 FROM incidencias_run r WHERE r.ticket_id = k.id_incidencia
  );

-- ════════════════════════════════════════════════════════════════════
-- PASO 3 — Borrar agent_conversations vinculadas a las 4 incidencias residuales
-- ════════════════════════════════════════════════════════════════════
\echo '── PASO 3: agent_conversations vinculadas a las 4 incidencias residuales ──'
DELETE FROM agent_conversations
WHERE ticket_id IN (
  'INC-000037-20260401',
  'INC-000034-20260401',
  'INC-000035-20260408',
  'INC-000038-20260408'
);

-- ════════════════════════════════════════════════════════════════════
-- PASO 4 — Borrar las 4 incidencias_run residuales (CASCADE limpia incidencias_live)
-- ════════════════════════════════════════════════════════════════════
\echo '── PASO 4: incidencias_run residuales (CASCADE → incidencias_live) ──'
DELETE FROM incidencias_run
WHERE ticket_id IN (
  'INC-000037-20260401',
  'INC-000034-20260401',
  'INC-000035-20260408',
  'INC-000038-20260408'
);

-- ════════════════════════════════════════════════════════════════════
-- PASO 5 — Borrar PRJ-MNQDXKA5 (smoke BUILD residual)
-- ════════════════════════════════════════════════════════════════════
\echo '── PASO 5: build_live PRJ-MNQDXKA5 (smoke residual sin dependencias) ──'
DELETE FROM build_live WHERE id_proyecto = 'PRJ-MNQDXKA5';

-- ════════════════════════════════════════════════════════════════════
-- PASO 6 — Purgar PRJ-SC* residuales de runs scenario previos
-- ════════════════════════════════════════════════════════════════════
-- Necesario para que test_p96_router::test_build_portfolio vea baseline 60
-- exacto. La vista v_p96_build_portfolio devuelve TODO build_live sin filtrar
-- SC, por lo que filas SC de runs scenario anteriores quedan persistentes
-- entre sesiones de pytest y rompen el test.
\echo '── PASO 6: build_live PRJ-SC* (residuales scenario inter-sesión) ──'
DELETE FROM build_live WHERE id_proyecto LIKE 'PRJ-SC%';
\echo 'build_live tras purga SC:'
SELECT COUNT(*) FROM build_live;

\echo '── POST-CLEANUP counts ──'
SELECT
  (SELECT count(*) FROM kanban_tareas    WHERE id NOT LIKE 'KAN-SC%')        AS kanban_legacy,
  (SELECT count(*) FROM incidencias_run  WHERE ticket_id NOT LIKE 'INC-SC%') AS inc_legacy,
  (SELECT count(*) FROM build_live       WHERE id_proyecto !~ '^PRJ-SC[A-D]') AS build_live_legacy,
  (SELECT count(*) FROM kanban_tareas k
    WHERE k.id_incidencia IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM incidencias_run r WHERE r.ticket_id = k.id_incidencia)) AS kanban_huerfanas_post;

COMMIT;

-- =====================================================================
-- P97 FASE 2.1 — Cleanup de los 3 proyectos legacy sin silo en build_live
-- Decisión del estratega: build_live debe quedar en 60 exactos.
-- Idempotente: si los 3 ya fueron borrados, no afecta.
-- =====================================================================

BEGIN;

DELETE FROM build_live WHERE silo IS NULL;

COMMIT;

-- Verificación esperada:
--   build_live total              = 60
--   build_live silos NOT NULL     = 60
--   build_live silos NULL         = 0
--   build_live silos distintos    = 8
--   v_p96_build_portfolio total   = 60
SELECT 'build_live total'             AS lbl, COUNT(*) FROM build_live
UNION ALL SELECT 'silos distintos',     COUNT(DISTINCT silo) FROM build_live;

-- ARQ-02 F3 — DROP TABLE incidencias (zombie fósil)
-- Fase: ARQ-02 F3
-- Fecha: 2026-04-08
-- Commit: <pendiente, rellenar en F6>
--
-- Elimina la tabla incidencias (sin sufijo) que era residuo del primer
-- seed del sistema. Schema obsoleto incompatible con incidencias_run/_live,
-- 1 sola fila fósil ("Test incidencia" del 2026-03-19, id INC-02990DA7),
-- cero FKs apuntando a ella, cero código que la consuma. Los endpoints
-- /incidencias* van todos a incidencias_run desde F1.3b.
--
-- Snapshot defensivo de la fila en _dumps/arq02/incidencias_zombie_F3.csv
-- por si fuera necesario rehidratar (no se espera).
--
-- Idempotente: usa DROP TABLE IF EXISTS + guards.

BEGIN;

-- Guard 1: si existe, debe tener exactamente 0 o 1 fila (la del fósil)
DO $$
DECLARE n INT;
BEGIN
  IF to_regclass('public.incidencias') IS NOT NULL THEN
    SELECT COUNT(*) INTO n FROM incidencias;
    IF n > 1 THEN
      RAISE EXCEPTION 'incidencias tiene % filas (esperaba 0 o 1) — abortar DROP', n;
    END IF;
  END IF;
END $$;

-- Guard 2: ninguna FK debe apuntar a incidencias
DO $$
DECLARE fk_count INT;
BEGIN
  SELECT COUNT(*) INTO fk_count
  FROM information_schema.referential_constraints rc
  JOIN information_schema.constraint_column_usage ccu
    ON rc.constraint_name = ccu.constraint_name
  WHERE ccu.table_name = 'incidencias';
  IF fk_count > 0 THEN
    RAISE EXCEPTION '% FKs apuntan a incidencias (esperaba 0) — abortar DROP', fk_count;
  END IF;
END $$;

DROP TABLE IF EXISTS incidencias;

COMMIT;

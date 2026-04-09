-- =====================================================================
-- ARQ-03 F2.1 — Función PL/pgSQL compartido.crear_esquema_escenario(text)
-- Clona la estructura de primitiva en un esquema sc_* vacío, reescribiendo
-- las referencias internas (primitiva.X → sc_X.X) y preservando las
-- referencias cross-schema a compartido.
-- =====================================================================

BEGIN;

CREATE OR REPLACE FUNCTION compartido.crear_esquema_escenario(p_scenario text)
RETURNS void
LANGUAGE plpgsql
AS $func$
DECLARE
  v_rec       record;
  v_new_def   text;
  n_tablas    int := 0;
  n_seqs      int := 0;
  n_defaults  int := 0;
  n_fks       int := 0;
  n_triggers  int := 0;
  n_vistas    int := 0;
BEGIN
  -- 1) Validar nombre
  IF p_scenario !~ '^sc_[a-z][a-z0-9_]*$' THEN
    RAISE EXCEPTION 'Nombre debe cumplir ^sc_[a-z][a-z0-9_]*$, recibido: %', p_scenario;
  END IF;
  IF p_scenario IN ('sc_primitiva','sc_compartido','sc_public') THEN
    RAISE EXCEPTION 'Nombre reservado: %', p_scenario;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = p_scenario) THEN
    RAISE EXCEPTION 'El esquema % ya existe. Usa DROP SCHEMA %I CASCADE antes.', p_scenario, p_scenario;
  END IF;

  -- 2) Crear esquema
  EXECUTE format('CREATE SCHEMA %I', p_scenario);
  EXECUTE format('COMMENT ON SCHEMA %I IS %L',
    p_scenario,
    'ARQ-03: esquema escenario clonado de primitiva (' || now()::text || ')');

  -- 2bis) F2.1 fix v2: forzar search_path local para que todas las
  -- resoluciones implícitas de pg_get_constraintdef / pg_get_viewdef
  -- (y los ALTER/CREATE subsecuentes) ancien OIDs a p_scenario en
  -- lugar de a primitiva (que viene primero vía ALTER ROLE F1).
  EXECUTE format(
    'SET LOCAL search_path = %I, compartido, public, pg_catalog',
    p_scenario
  );

  -- 3) Clonar tablas con LIKE INCLUDING ALL (sin FKs, se añaden en paso 7)
  FOR v_rec IN
    SELECT c.relname
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = 'primitiva' AND c.relkind = 'r'
      ORDER BY c.relname
  LOOP
    EXECUTE format(
      'CREATE TABLE %I.%I (LIKE primitiva.%I '
      || 'INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES '
      || 'INCLUDING COMMENTS INCLUDING STATISTICS INCLUDING STORAGE '
      || 'INCLUDING GENERATED INCLUDING IDENTITY)',
      p_scenario, v_rec.relname, v_rec.relname
    );
    n_tablas := n_tablas + 1;
  END LOOP;

  -- 4) Crear secuencias independientes (mismos parámetros que primitiva, valores frescos)
  FOR v_rec IN
    SELECT c.relname,
           s.seqstart, s.seqincrement, s.seqmax, s.seqmin, s.seqcache, s.seqcycle
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
      JOIN pg_sequence s  ON s.seqrelid = c.oid
      WHERE n.nspname = 'primitiva' AND c.relkind = 'S'
  LOOP
    EXECUTE format(
      'CREATE SEQUENCE %I.%I INCREMENT BY %s MINVALUE %s MAXVALUE %s START WITH %s CACHE %s %s',
      p_scenario, v_rec.relname,
      v_rec.seqincrement, v_rec.seqmin, v_rec.seqmax, v_rec.seqstart, v_rec.seqcache,
      CASE WHEN v_rec.seqcycle THEN 'CYCLE' ELSE 'NO CYCLE' END
    );
    n_seqs := n_seqs + 1;
  END LOOP;

  -- 5) Reescribir DEFAULTs que apuntan a primitiva.seq → p_scenario.seq
  FOR v_rec IN
    SELECT c.relname AS tabla, a.attname AS col,
           pg_get_expr(d.adbin, d.adrelid) AS default_expr
      FROM pg_attrdef d
      JOIN pg_class c ON c.oid = d.adrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
      JOIN pg_attribute a ON a.attrelid = d.adrelid AND a.attnum = d.adnum
      WHERE n.nspname = p_scenario
        AND pg_get_expr(d.adbin, d.adrelid) LIKE '%primitiva.%'
  LOOP
    v_new_def := replace(v_rec.default_expr, 'primitiva.', p_scenario || '.');
    EXECUTE format('ALTER TABLE %I.%I ALTER COLUMN %I SET DEFAULT %s',
      p_scenario, v_rec.tabla, v_rec.col, v_new_def);
    n_defaults := n_defaults + 1;
  END LOOP;

  -- 6) OWNED BY: asociar secuencias con columnas del nuevo esquema
  FOR v_rec IN
    SELECT seq.relname AS seq, t.relname AS tab, a.attname AS col
      FROM pg_class seq
      JOIN pg_namespace nseq ON nseq.oid = seq.relnamespace
      JOIN pg_depend dep ON dep.objid = seq.oid AND dep.deptype = 'a'
      JOIN pg_class t ON t.oid = dep.refobjid
      JOIN pg_namespace nt ON nt.oid = t.relnamespace
      JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = dep.refobjsubid
      WHERE nseq.nspname = 'primitiva'
        AND nt.nspname   = 'primitiva'
        AND seq.relkind  = 'S'   -- F2.1 fix: filtrar solo secuencias (los índices también tienen deptype='a')
  LOOP
    EXECUTE format('ALTER SEQUENCE %I.%I OWNED BY %I.%I.%I',
      p_scenario, v_rec.seq, p_scenario, v_rec.tab, v_rec.col);
  END LOOP;

  -- 7) Añadir FKs (preservando cross-schema a compartido intactas)
  FOR v_rec IN
    SELECT con.conname, src.relname AS tabla_src,
           pg_get_constraintdef(con.oid) AS def
      FROM pg_constraint con
      JOIN pg_class src ON src.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = src.relnamespace
      WHERE ns.nspname = 'primitiva' AND con.contype = 'f'
      ORDER BY src.relname, con.conname
  LOOP
    -- replace() solo afecta el literal 'primitiva.'; 'compartido.' intacto
    v_new_def := replace(v_rec.def, 'primitiva.', p_scenario || '.');
    EXECUTE format('ALTER TABLE %I.%I ADD CONSTRAINT %I %s',
      p_scenario, v_rec.tabla_src, v_rec.conname, v_new_def);
    n_fks := n_fks + 1;
  END LOOP;

  -- 8) Clonar triggers (funciones quedan en compartido, solo cambia ON <tabla>)
  FOR v_rec IN
    SELECT t.tgname, pg_get_triggerdef(t.oid) AS def
      FROM pg_trigger t
      JOIN pg_class c ON c.oid = t.tgrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = 'primitiva' AND NOT t.tgisinternal
  LOOP
    v_new_def := replace(v_rec.def, 'primitiva.', p_scenario || '.');
    EXECUTE v_new_def;
    n_triggers := n_triggers + 1;
  END LOOP;

  -- 9) Clonar vistas
  FOR v_rec IN
    SELECT c.relname, pg_get_viewdef(c.oid, true) AS def
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = 'primitiva' AND c.relkind = 'v'
      ORDER BY c.relname
  LOOP
    v_new_def := replace(v_rec.def, 'primitiva.', p_scenario || '.');
    EXECUTE format('CREATE VIEW %I.%I AS %s', p_scenario, v_rec.relname, v_new_def);
    n_vistas := n_vistas + 1;
  END LOOP;

  RAISE NOTICE 'Esquema % creado: % tablas, % seqs, % defaults reescritos, % FKs, % triggers, % vistas',
    p_scenario, n_tablas, n_seqs, n_defaults, n_fks, n_triggers, n_vistas;
END;
$func$;

COMMENT ON FUNCTION compartido.crear_esquema_escenario(text) IS
  'ARQ-03 F2.1: clona primitiva en un esquema sc_* vacío. Idempotente vía DROP SCHEMA CASCADE previo.';

COMMIT;

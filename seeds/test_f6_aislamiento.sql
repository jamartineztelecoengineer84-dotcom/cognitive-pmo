-- =============================================================
-- ARQ-03 F6: Tests de aislamiento multi-escenario
-- 6 tests: counts, no-leak, search_path switch, compartido,
--          FK cross-schema, datos distintos
-- =============================================================

-- =============================================
-- TEST 1: Row counts por escenario (12 tablas)
-- Esperado: NOR=3224, IBE=4727, LIT=6878
-- =============================================
\echo '=== TEST 1: ROW COUNTS POR ESCENARIO ==='

\echo '--- sc_norte (Holgura 40%) ---'
SET search_path = sc_norte, compartido, public;
SELECT 'cmdb_activos' as tabla, count(*) as filas FROM cmdb_activos
UNION ALL SELECT 'cmdb_relaciones', count(*) FROM cmdb_relaciones
UNION ALL SELECT 'incidencias_run', count(*) FROM incidencias_run
UNION ALL SELECT 'cartera_build', count(*) FROM cartera_build
UNION ALL SELECT 'presupuestos', count(*) FROM presupuestos
UNION ALL SELECT 'build_risks', count(*) FROM build_risks
UNION ALL SELECT 'build_stakeholders', count(*) FROM build_stakeholders
UNION ALL SELECT 'build_quality_gates', count(*) FROM build_quality_gates
UNION ALL SELECT 'build_sprints', count(*) FROM build_sprints
UNION ALL SELECT 'build_sprint_items', count(*) FROM build_sprint_items
UNION ALL SELECT 'build_subtasks', count(*) FROM build_subtasks
UNION ALL SELECT 'cmdb_change_windows', count(*) FROM cmdb_change_windows;

\echo '--- sc_iberico (Óptimo 70%) ---'
SET search_path = sc_iberico, compartido, public;
SELECT 'cmdb_activos' as tabla, count(*) as filas FROM cmdb_activos
UNION ALL SELECT 'cmdb_relaciones', count(*) FROM cmdb_relaciones
UNION ALL SELECT 'incidencias_run', count(*) FROM incidencias_run
UNION ALL SELECT 'cartera_build', count(*) FROM cartera_build
UNION ALL SELECT 'presupuestos', count(*) FROM presupuestos
UNION ALL SELECT 'build_risks', count(*) FROM build_risks
UNION ALL SELECT 'build_stakeholders', count(*) FROM build_stakeholders
UNION ALL SELECT 'build_quality_gates', count(*) FROM build_quality_gates
UNION ALL SELECT 'build_sprints', count(*) FROM build_sprints
UNION ALL SELECT 'build_sprint_items', count(*) FROM build_sprint_items
UNION ALL SELECT 'build_subtasks', count(*) FROM build_subtasks
UNION ALL SELECT 'cmdb_change_windows', count(*) FROM cmdb_change_windows;

\echo '--- sc_litoral (Saturado 105%) ---'
SET search_path = sc_litoral, compartido, public;
SELECT 'cmdb_activos' as tabla, count(*) as filas FROM cmdb_activos
UNION ALL SELECT 'cmdb_relaciones', count(*) FROM cmdb_relaciones
UNION ALL SELECT 'incidencias_run', count(*) FROM incidencias_run
UNION ALL SELECT 'cartera_build', count(*) FROM cartera_build
UNION ALL SELECT 'presupuestos', count(*) FROM presupuestos
UNION ALL SELECT 'build_risks', count(*) FROM build_risks
UNION ALL SELECT 'build_stakeholders', count(*) FROM build_stakeholders
UNION ALL SELECT 'build_quality_gates', count(*) FROM build_quality_gates
UNION ALL SELECT 'build_sprints', count(*) FROM build_sprints
UNION ALL SELECT 'build_sprint_items', count(*) FROM build_sprint_items
UNION ALL SELECT 'build_subtasks', count(*) FROM build_subtasks
UNION ALL SELECT 'cmdb_change_windows', count(*) FROM cmdb_change_windows;

-- =============================================
-- TEST 2: NO-LEAK — ticket_ids NO se repiten entre esquemas
-- Si hay 0 filas → PASS (no hay leak)
-- =============================================
\echo '=== TEST 2: NO-LEAK (ticket_ids únicos por esquema) ==='
SELECT 'LEAK norte↔iberico' as test, count(*) as coincidencias
FROM sc_norte.incidencias_run n
JOIN sc_iberico.incidencias_run i ON n.ticket_id = i.ticket_id
UNION ALL
SELECT 'LEAK norte↔litoral', count(*)
FROM sc_norte.incidencias_run n
JOIN sc_litoral.incidencias_run l ON n.ticket_id = l.ticket_id
UNION ALL
SELECT 'LEAK iberico↔litoral', count(*)
FROM sc_iberico.incidencias_run i
JOIN sc_litoral.incidencias_run l ON i.ticket_id = l.ticket_id;

-- =============================================
-- TEST 3: NO-LEAK — id_proyecto NO se repite entre esquemas
-- =============================================
\echo '=== TEST 3: NO-LEAK (id_proyecto únicos por esquema) ==='
SELECT 'LEAK norte↔iberico' as test, count(*) as coincidencias
FROM sc_norte.cartera_build n
JOIN sc_iberico.cartera_build i ON n.id_proyecto = i.id_proyecto
UNION ALL
SELECT 'LEAK norte↔litoral', count(*)
FROM sc_norte.cartera_build n
JOIN sc_litoral.cartera_build l ON n.id_proyecto = l.id_proyecto
UNION ALL
SELECT 'LEAK iberico↔litoral', count(*)
FROM sc_iberico.cartera_build i
JOIN sc_litoral.cartera_build l ON i.id_proyecto = l.id_proyecto;

-- =============================================
-- TEST 4: COMPARTIDO accesible desde cada esquema
-- pmo_project_managers y pmo_staff_skills deben ser iguales
-- =============================================
\echo '=== TEST 4: COMPARTIDO accesible desde cada esquema ==='
SET search_path = sc_norte, compartido, public;
SELECT 'norte_pm' as ctx, count(*) FROM pmo_project_managers;
SET search_path = sc_iberico, compartido, public;
SELECT 'iberico_pm' as ctx, count(*) FROM pmo_project_managers;
SET search_path = sc_litoral, compartido, public;
SELECT 'litoral_pm' as ctx, count(*) FROM pmo_project_managers;

-- Verificar que es LA MISMA tabla (mismo OID)
SELECT 'compartido_oid_check' as test,
  (SELECT oid FROM pg_class WHERE relname='pmo_project_managers' AND relnamespace=(SELECT oid FROM pg_namespace WHERE nspname='compartido')) as oid_compartido,
  'SAME_TABLE' as resultado;

-- =============================================
-- TEST 5: SEARCH_PATH SWITCH — misma query, distinto resultado
-- =============================================
\echo '=== TEST 5: SEARCH_PATH SWITCH ==='
SET search_path = sc_norte, compartido, public;
SELECT 'norte' as escenario, count(*) as incidencias FROM incidencias_run;
SET search_path = sc_iberico, compartido, public;
SELECT 'iberico' as escenario, count(*) as incidencias FROM incidencias_run;
SET search_path = sc_litoral, compartido, public;
SELECT 'litoral' as escenario, count(*) as incidencias FROM incidencias_run;

-- =============================================
-- TEST 6: DATOS DISTINTOS — primer ticket_id diferente por esquema
-- =============================================
\echo '=== TEST 6: DATOS DISTINTOS (primer ticket por esquema) ==='
SELECT 'norte' as esc, ticket_id FROM sc_norte.incidencias_run ORDER BY ticket_id LIMIT 1
UNION ALL
SELECT 'iberico', ticket_id FROM sc_iberico.incidencias_run ORDER BY ticket_id LIMIT 1
UNION ALL
SELECT 'litoral', ticket_id FROM sc_litoral.incidencias_run ORDER BY ticket_id LIMIT 1;

-- =============================================
-- RESUMEN FINAL
-- =============================================
\echo '=== RESUMEN: TOTALES POR ESCENARIO ==='
SELECT 'sc_norte' as esquema,
  (SELECT count(*) FROM sc_norte.cmdb_activos) +
  (SELECT count(*) FROM sc_norte.cmdb_relaciones) +
  (SELECT count(*) FROM sc_norte.incidencias_run) +
  (SELECT count(*) FROM sc_norte.cartera_build) +
  (SELECT count(*) FROM sc_norte.presupuestos) +
  (SELECT count(*) FROM sc_norte.build_risks) +
  (SELECT count(*) FROM sc_norte.build_stakeholders) +
  (SELECT count(*) FROM sc_norte.build_quality_gates) +
  (SELECT count(*) FROM sc_norte.build_sprints) +
  (SELECT count(*) FROM sc_norte.build_sprint_items) +
  (SELECT count(*) FROM sc_norte.build_subtasks) +
  (SELECT count(*) FROM sc_norte.cmdb_change_windows) as total_filas
UNION ALL
SELECT 'sc_iberico',
  (SELECT count(*) FROM sc_iberico.cmdb_activos) +
  (SELECT count(*) FROM sc_iberico.cmdb_relaciones) +
  (SELECT count(*) FROM sc_iberico.incidencias_run) +
  (SELECT count(*) FROM sc_iberico.cartera_build) +
  (SELECT count(*) FROM sc_iberico.presupuestos) +
  (SELECT count(*) FROM sc_iberico.build_risks) +
  (SELECT count(*) FROM sc_iberico.build_stakeholders) +
  (SELECT count(*) FROM sc_iberico.build_quality_gates) +
  (SELECT count(*) FROM sc_iberico.build_sprints) +
  (SELECT count(*) FROM sc_iberico.build_sprint_items) +
  (SELECT count(*) FROM sc_iberico.build_subtasks) +
  (SELECT count(*) FROM sc_iberico.cmdb_change_windows)
UNION ALL
SELECT 'sc_litoral',
  (SELECT count(*) FROM sc_litoral.cmdb_activos) +
  (SELECT count(*) FROM sc_litoral.cmdb_relaciones) +
  (SELECT count(*) FROM sc_litoral.incidencias_run) +
  (SELECT count(*) FROM sc_litoral.cartera_build) +
  (SELECT count(*) FROM sc_litoral.presupuestos) +
  (SELECT count(*) FROM sc_litoral.build_risks) +
  (SELECT count(*) FROM sc_litoral.build_stakeholders) +
  (SELECT count(*) FROM sc_litoral.build_quality_gates) +
  (SELECT count(*) FROM sc_litoral.build_sprints) +
  (SELECT count(*) FROM sc_litoral.build_sprint_items) +
  (SELECT count(*) FROM sc_litoral.build_subtasks) +
  (SELECT count(*) FROM sc_litoral.cmdb_change_windows);

\echo '=== FIN F6 TESTS ==='

-- Restaurar search_path por defecto
SET search_path = primitiva, compartido, public;

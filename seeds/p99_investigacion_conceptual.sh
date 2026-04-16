#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
# P99 INVESTIGACIÓN CONCEPTUAL COMPLETA
# ══════════════════════════════════════════════════════════════════════
# NO es solo "qué hay" — es "para qué se creó, tiene sentido, y qué
# hay que cambiar desde la concepción"
#
# SECCIONES:
#   A. Modelo de datos completo (tablas, relaciones, constraints)
#   B. Lógica del backend (cómo calcula estados dinámicos)
#   C. Coherencia de datos (¿los seeds cuentan una historia realista?)
#   D. Flujo completo técnico→incidencia→kanban→dashboard
#   E. Qué ve el frontend (endpoints reales + respuestas)
#   F. Diagnóstico conceptual (¿qué falla en el diseño?)
#
# Uso: bash p99_investigacion_conceptual.sh 2>&1 | tee /tmp/p99_invest_conceptual.log
# ══════════════════════════════════════════════════════════════════════

export PGPASSWORD='REDACTED-old-password'
PG="psql -h localhost -U jose_admin -d cognitive_pmo -t -A"
PGF="psql -h localhost -U jose_admin -d cognitive_pmo"  # formatted output

echo "══════════════════════════════════════════════════════════════"
echo "  P99 INVESTIGACIÓN CONCEPTUAL COMPLETA"
echo "  $(date)"
echo "══════════════════════════════════════════════════════════════"

# ══════════════════════════════════════════════════════════════
# A. MODELO DE DATOS — Estructura completa
# ══════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  A. MODELO DE DATOS"
echo "══════════════════════════════════════════════════════════════"

echo ""
echo "--- A1. Schemas existentes ---"
$PG -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog','information_schema','pg_toast') ORDER BY schema_name;"

echo ""
echo "--- A2. Tablas en 'compartido' (pool compartido — PIEDRA FUNDAMENTAL) ---"
$PG -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'compartido' ORDER BY table_name;"

echo ""
echo "--- A3. Tablas en 'sc_norte' (representativo de cada schema) ---"
$PG -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'sc_norte' ORDER BY table_name;"

echo ""
echo "--- A4. compartido.pmo_staff_skills — EL POOL DE TÉCNICOS ---"
echo "  Estructura:"
$PGF -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='compartido' AND table_name='pmo_staff_skills' ORDER BY ordinal_position;"
echo ""
echo "  Total técnicos:"
$PG -c "SELECT COUNT(*) FROM compartido.pmo_staff_skills;"
echo "  Estados estáticos:"
$PG -c "SELECT estado, COUNT(*) FROM compartido.pmo_staff_skills GROUP BY estado ORDER BY COUNT(*) DESC;"
echo "  Campo carga_actual:"
$PG -c "SELECT MIN(carga_actual), MAX(carga_actual), AVG(carga_actual)::numeric(5,2) FROM compartido.pmo_staff_skills;"
echo "  Campos de skills:"
$PGF -c "SELECT id_recurso, nombre, especialidad, skills_requeridas, carga_actual, estado FROM compartido.pmo_staff_skills LIMIT 5;"

echo ""
echo "--- A5. compartido.pmo_project_managers — POOL DE PMs ---"
echo "  Estructura:"
$PGF -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='compartido' AND table_name='pmo_project_managers' ORDER BY ordinal_position;"
echo ""
echo "  Total PMs:"
$PG -c "SELECT COUNT(*) FROM compartido.pmo_project_managers;"
echo "  Sample:"
$PGF -c "SELECT * FROM compartido.pmo_project_managers LIMIT 3;"

echo ""
echo "--- A6. incidencias_run — INCIDENCIAS RUN (per-schema) ---"
echo "  Estructura completa:"
$PGF -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='sc_norte' AND table_name='incidencias_run' ORDER BY ordinal_position;"
echo ""
echo "  CHECK constraints:"
$PG -c "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'sc_norte.incidencias_run'::regclass AND contype = 'c';"

echo ""
echo "--- A7. incidencias_live — ¿QUÉ ES? ¿PARA QUÉ EXISTE? ---"
echo "  Estructura:"
$PGF -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='sc_norte' AND table_name='incidencias_live' ORDER BY ordinal_position;"
echo ""
echo "  CHECK constraints:"
$PG -c "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'sc_norte.incidencias_live'::regclass AND contype = 'c';" 2>/dev/null || echo "  (sin constraints o tabla no existe)"
echo ""
echo "  Relación con incidencias_run (¿tienen los mismos ticket_id?):"
for SC in sc_norte sc_iberico sc_litoral; do
  LIVE=$($PG -c "SELECT COUNT(*) FROM $SC.incidencias_live;" 2>/dev/null || echo "0")
  RUN=$($PG -c "SELECT COUNT(*) FROM $SC.incidencias_run;")
  OVERLAP=$($PG -c "SELECT COUNT(*) FROM $SC.incidencias_live l JOIN $SC.incidencias_run r ON l.ticket_id = r.ticket_id;" 2>/dev/null || echo "0")
  echo "  $SC: live=$LIVE, run=$RUN, overlap=$OVERLAP"
done

echo ""
echo "--- A8. kanban_tareas — TAREAS KANBAN ---"
echo "  Estructura completa:"
$PGF -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='sc_norte' AND table_name='kanban_tareas' ORDER BY ordinal_position;"
echo ""
echo "  CHECK constraints:"
$PG -c "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'sc_norte.kanban_tareas'::regclass AND contype = 'c';"

echo ""
echo "--- A9. cartera_build — PROYECTOS BUILD ---"
echo "  Estructura:"
$PGF -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='sc_norte' AND table_name='cartera_build' ORDER BY ordinal_position;"
echo ""
echo "  Sample:"
$PGF -c "SET search_path = sc_norte, compartido, public; SELECT id_proyecto, nombre_proyecto, estado, responsable_asignado, presupuesto FROM cartera_build LIMIT 5;"

echo ""
echo "--- A10. pmo_governance_scoring — GOVERNANCE (per-schema) ---"
echo "  Estructura:"
$PGF -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='sc_norte' AND table_name='pmo_governance_scoring' ORDER BY ordinal_position;"
echo ""
echo "  Sample:"
$PGF -c "SET search_path = sc_norte, compartido, public; SELECT id_proyecto, nombre_proyecto, id_pm, gate_status, score_global FROM pmo_governance_scoring LIMIT 5;"

# ══════════════════════════════════════════════════════════════
# B. LÓGICA DEL BACKEND — Cómo calcula estados
# ══════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  B. LÓGICA DEL BACKEND (main.py)"
echo "══════════════════════════════════════════════════════════════"

echo ""
echo "--- B1. GET /team/tecnicos — ¿cómo calcula estado dinámico? ---"
echo "  Buscando la lógica en main.py..."
grep -n "estado_run_dinamico\|estado_run\|OCUPADO\|ASIGNADO\|DISPONIBLE" /root/cognitive-pmo/backend/main.py | head -40

echo ""
echo "--- B2. Bloque completo de cálculo de estado dinámico ---"
# Extraer desde GET /team/tecnicos hasta el return
sed -n '/def.*team.*tecnico\|@app.get.*\/team\/tecnico/,/^@app\.\|^async def\|^def /p' /root/cognitive-pmo/backend/main.py | head -120

echo ""
echo "--- B3. GET /incidencias/live — ¿qué devuelve? ---"
sed -n '/def.*incidencias_live\|@app.get.*\/incidencias\/live/,/^@app\.\|^async def\|^def /p' /root/cognitive-pmo/backend/main.py | head -60

echo ""
echo "--- B4. GET /pmo/managers — ¿cómo calcula estado PM? ---"
sed -n '/def.*pmo.*manager\|@app.get.*\/pmo\/managers/,/^@app\.\|^async def\|^def /p' /root/cognitive-pmo/backend/main.py | head -60

echo ""
echo "--- B5. GET /pmo/governance/dashboard — ¿métricas? ---"
sed -n '/def.*governance.*dashboard\|@app.get.*\/pmo\/governance\/dashboard/,/^@app\.\|^async def\|^def /p' /root/cognitive-pmo/backend/main.py | head -80

# ══════════════════════════════════════════════════════════════
# C. COHERENCIA DE DATOS — ¿Los seeds cuentan una historia?
# ══════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  C. COHERENCIA DE DATOS POR SCHEMA"
echo "══════════════════════════════════════════════════════════════"

for SC in sc_norte sc_iberico sc_litoral; do
  echo ""
  echo "────────────────────────────────────────"
  echo "  $SC"
  echo "────────────────────────────────────────"

  echo ""
  echo "  C1. Incidencias RUN:"
  echo "    Total:"
  $PG -c "SELECT COUNT(*) FROM $SC.incidencias_run;"
  echo "    Por estado:"
  $PG -c "SELECT estado, COUNT(*) FROM $SC.incidencias_run GROUP BY estado ORDER BY COUNT(*) DESC;"
  echo "    DISTINCT tecnico_asignado (TODOS):"
  $PG -c "SELECT COUNT(DISTINCT tecnico_asignado) FROM $SC.incidencias_run WHERE tecnico_asignado IS NOT NULL AND tecnico_asignado != '';"
  echo "    DISTINCT tecnico_asignado (SOLO ABIERTAS = no CERRADO/RESUELTO):"
  $PG -c "SELECT COUNT(DISTINCT tecnico_asignado) FROM $SC.incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO') AND tecnico_asignado IS NOT NULL AND tecnico_asignado != '';"
  echo "    Técnicos con MÁS de 1 incidencia abierta:"
  $PG -c "SELECT tecnico_asignado, COUNT(*) AS n FROM $SC.incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO') AND tecnico_asignado IS NOT NULL GROUP BY tecnico_asignado HAVING COUNT(*) > 1 ORDER BY n DESC LIMIT 10;"
  echo "    ¿Hay tecnico_asignado NULL en abiertas?:"
  $PG -c "SELECT COUNT(*) FROM $SC.incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO') AND (tecnico_asignado IS NULL OR tecnico_asignado = '');"

  echo ""
  echo "  C2. Kanban tareas:"
  echo "    Total:"
  $PG -c "SELECT COUNT(*) FROM $SC.kanban_tareas;"
  echo "    Por columna:"
  $PG -c "SELECT columna, COUNT(*) FROM $SC.kanban_tareas GROUP BY columna ORDER BY COUNT(*) DESC;"
  echo "    DISTINCT id_tecnico (ACTIVAS = no Completado/Done/Backlog):"
  $PG -c "SELECT COUNT(DISTINCT id_tecnico) FROM $SC.kanban_tareas WHERE columna NOT IN ('Completado','Done','Backlog') AND id_tecnico IS NOT NULL AND id_tecnico != '';"
  echo "    Técnicos con MÁS de 1 tarea activa:"
  $PG -c "SELECT id_tecnico, COUNT(*) AS n FROM $SC.kanban_tareas WHERE columna NOT IN ('Completado','Done','Backlog') AND id_tecnico IS NOT NULL GROUP BY id_tecnico HAVING COUNT(*) > 1 ORDER BY n DESC LIMIT 10;"
  echo "    ¿Hay id_tecnico NULL en activas?:"
  $PG -c "SELECT COUNT(*) FROM $SC.kanban_tareas WHERE columna NOT IN ('Completado','Done','Backlog') AND (id_tecnico IS NULL OR id_tecnico = '');"
  echo "    Por tipo (RUN/BUILD):"
  $PG -c "SELECT tipo, COUNT(*) FROM $SC.kanban_tareas GROUP BY tipo;"

  echo ""
  echo "  C3. Incidencias LIVE:"
  echo "    Total:"
  $PG -c "SELECT COUNT(*) FROM $SC.incidencias_live;" 2>/dev/null || echo "    (tabla no existe)"
  echo "    ¿Tiene tecnico_asignado?"
  $PG -c "SELECT COUNT(*) FROM $SC.incidencias_live WHERE tecnico_asignado IS NOT NULL AND tecnico_asignado != '';" 2>/dev/null || echo "    (N/A)"
  echo "    Prioridades:"
  $PG -c "SELECT prioridad, COUNT(*) FROM $SC.incidencias_live GROUP BY prioridad ORDER BY prioridad;" 2>/dev/null || echo "    (N/A)"

  echo ""
  echo "  C4. Cartera BUILD:"
  echo "    Total proyectos:"
  $PG -c "SELECT COUNT(*) FROM $SC.cartera_build;"
  echo "    Por estado:"
  $PG -c "SELECT estado, COUNT(*) FROM $SC.cartera_build GROUP BY estado ORDER BY COUNT(*) DESC;"
  echo "    DISTINCT responsable_asignado:"
  $PG -c "SELECT COUNT(DISTINCT responsable_asignado) FROM $SC.cartera_build WHERE responsable_asignado IS NOT NULL;"
  echo "    ¿Son FTE-xxx o PM-xxx?"
  $PG -c "SELECT responsable_asignado FROM $SC.cartera_build WHERE responsable_asignado IS NOT NULL LIMIT 5;"

  echo ""
  echo "  C5. Governance scoring:"
  echo "    Total:"
  $PG -c "SELECT COUNT(*) FROM $SC.pmo_governance_scoring;"
  echo "    Por gate_status:"
  $PG -c "SELECT gate_status, COUNT(*) FROM $SC.pmo_governance_scoring GROUP BY gate_status ORDER BY COUNT(*) DESC;"
  echo "    DISTINCT id_pm:"
  $PG -c "SELECT COUNT(DISTINCT id_pm) FROM $SC.pmo_governance_scoring WHERE id_pm IS NOT NULL;"
  echo "    Sample id_pm:"
  $PG -c "SELECT DISTINCT id_pm FROM $SC.pmo_governance_scoring WHERE id_pm IS NOT NULL LIMIT 5;"

  echo ""
  echo "  C6. UNIÓN FINAL — Técnicos únicos ocupados:"
  $PG -c "
    SELECT COUNT(DISTINCT tecnico) FROM (
      SELECT tecnico_asignado AS tecnico FROM $SC.incidencias_run
        WHERE estado NOT IN ('CERRADO','RESUELTO')
        AND tecnico_asignado IS NOT NULL AND tecnico_asignado != ''
      UNION
      SELECT id_tecnico AS tecnico FROM $SC.kanban_tareas
        WHERE columna NOT IN ('Completado','Done','Backlog')
        AND id_tecnico IS NOT NULL AND id_tecnico != ''
    ) sub;
  "
done

# ══════════════════════════════════════════════════════════════
# D. FLUJO COMPLETO — ¿Cómo se vinculan las piezas?
# ══════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  D. FLUJO CONCEPTUAL"
echo "══════════════════════════════════════════════════════════════"

echo ""
echo "--- D1. ¿kanban_tareas tiene id_incidencia? ¿Se vinculan RUN↔BUILD? ---"
echo "  kanban con id_incidencia no nulo:"
for SC in sc_norte sc_iberico sc_litoral; do
  $PG -c "SELECT COUNT(*) FROM $SC.kanban_tareas WHERE id_incidencia IS NOT NULL AND id_incidencia != '';"
  echo "  → $SC"
done

echo ""
echo "--- D2. ¿cartera_build.responsable_asignado es un FTE del pool? ---"
echo "  ¿Cuántos responsables de cartera_build existen en pmo_staff_skills?"
for SC in sc_norte sc_iberico sc_litoral; do
  $PG -c "
    SELECT COUNT(DISTINCT cb.responsable_asignado)
    FROM $SC.cartera_build cb
    JOIN compartido.pmo_staff_skills ps ON cb.responsable_asignado = ps.id_recurso;
  "
  echo "  → $SC (match FTE en pool)"
done

echo ""
echo "--- D3. ¿incidencias_run.tecnico_asignado es un FTE del pool? ---"
for SC in sc_norte sc_iberico sc_litoral; do
  TOTAL=$($PG -c "SELECT COUNT(DISTINCT tecnico_asignado) FROM $SC.incidencias_run WHERE tecnico_asignado IS NOT NULL AND tecnico_asignado != '';")
  MATCH=$($PG -c "SELECT COUNT(DISTINCT ir.tecnico_asignado) FROM $SC.incidencias_run ir JOIN compartido.pmo_staff_skills ps ON ir.tecnico_asignado = ps.id_recurso WHERE ir.tecnico_asignado IS NOT NULL;")
  echo "  $SC: $MATCH/$TOTAL match con pool"
done

echo ""
echo "--- D4. ¿kanban_tareas.id_tecnico es un FTE del pool? ---"
for SC in sc_norte sc_iberico sc_litoral; do
  TOTAL=$($PG -c "SELECT COUNT(DISTINCT id_tecnico) FROM $SC.kanban_tareas WHERE id_tecnico IS NOT NULL AND id_tecnico != '';")
  MATCH=$($PG -c "SELECT COUNT(DISTINCT kt.id_tecnico) FROM $SC.kanban_tareas kt JOIN compartido.pmo_staff_skills ps ON kt.id_tecnico = ps.id_recurso WHERE kt.id_tecnico IS NOT NULL;")
  echo "  $SC: $MATCH/$TOTAL match con pool"
done

echo ""
echo "--- D5. ¿Hay técnicos que están en INCIDENCIAS + KANBAN a la vez? ---"
for SC in sc_norte sc_iberico sc_litoral; do
  $PG -c "
    SELECT COUNT(*) FROM (
      SELECT tecnico_asignado AS t FROM $SC.incidencias_run
        WHERE estado NOT IN ('CERRADO','RESUELTO') AND tecnico_asignado IS NOT NULL
      INTERSECT
      SELECT id_tecnico FROM $SC.kanban_tareas
        WHERE columna NOT IN ('Completado','Done','Backlog') AND id_tecnico IS NOT NULL
    ) sub;
  "
  echo "  → $SC técnicos en ambas tablas"
done

# ══════════════════════════════════════════════════════════════
# E. QUÉ VE EL FRONTEND — Endpoints reales
# ══════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  E. RESPUESTAS API REALES"
echo "══════════════════════════════════════════════════════════════"

for SC in sc_norte sc_iberico sc_litoral; do
  echo ""
  echo "────── $SC ──────"

  echo ""
  echo "  E1. /team/tecnicos — estados:"
  curl -s -H "X-Scenario: $SC" http://localhost:8088/team/tecnicos | python3 -c "
import sys,json
d=json.load(sys.stdin)
items=d if isinstance(d,list) else []
estados={}
vinc_count=0
for t in items:
    e=t.get('estado','?')
    estados[e]=estados.get(e,0)+1
    if t.get('vinculacion'): vinc_count+=1
print(f'  Total: {len(items)}, Ocupados: {sum(v for k,v in estados.items() if k not in (\"DISPONIBLE\",\"?\"))}, Con vinculación: {vinc_count}')
print(f'  Estados: {dict(sorted(estados.items()))}')
# Muestra 3 ocupados con vinculación
occ=[t for t in items if t.get('estado')!='DISPONIBLE' and t.get('vinculacion')]
for t in occ[:3]:
    print(f'    {t[\"id_recurso\"]}: {t[\"estado\"]} → {t.get(\"vinculacion\",\"\")[:80]}')
# Muestra 2 disponibles
disp=[t for t in items if t.get('estado')=='DISPONIBLE']
for t in disp[:2]:
    print(f'    {t[\"id_recurso\"]}: DISPONIBLE → vinc: \"{t.get(\"vinculacion\",\"\")}\"')
"

  echo ""
  echo "  E2. /incidencias/live — sample:"
  curl -s -H "X-Scenario: $SC" http://localhost:8088/incidencias/live | python3 -c "
import sys,json
d=json.load(sys.stdin)
items=d if isinstance(d,list) else []
print(f'  Total: {len(items)}')
for inc in items[:3]:
    print(f'    {inc.get(\"ticket_id\")}: {inc.get(\"prioridad\",inc.get(\"prioridad_ia\",\"?\"))} | {inc.get(\"estado\",\"?\")} | tec={inc.get(\"tecnico_asignado\",\"?\")} | sla_h={inc.get(\"sla_horas\",\"?\")}')
"

  echo ""
  echo "  E3. /pmo/managers — estados PM:"
  curl -s -H "X-Scenario: $SC" http://localhost:8088/pmo/managers | python3 -c "
import sys,json
d=json.load(sys.stdin)
items=d if isinstance(d,list) else []
estados={}
for pm in items:
    e=pm.get('estado','?')
    estados[e]=estados.get(e,0)+1
print(f'  Total PMs: {len(items)}, Estados: {dict(sorted(estados.items()))}')
for pm in items[:3]:
    print(f'    {pm.get(\"id_pm\")}: {pm.get(\"estado\")} | proy_activos={pm.get(\"proyectos_activos\",\"?\")} | carga={pm.get(\"carga\",\"?\")}')
"

  echo ""
  echo "  E4. /pmo/governance/dashboard — KPIs:"
  curl -s -H "X-Scenario: $SC" http://localhost:8088/pmo/governance/dashboard | python3 -c "
import sys,json
d=json.load(sys.stdin)
for k in ['total_proyectos','proyectos_activos','score_medio','total_pms','pms_asignados','pms_sobrecargados','proyectos_activos_schema','carga_media_pm']:
    if k in d:
        print(f'    {k}: {d[k]}')
"

  echo ""
  echo "  E5. /presupuestos — sample:"
  curl -s -H "X-Scenario: $SC" http://localhost:8088/presupuestos 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    items=d if isinstance(d,list) else []
    print(f'  Total: {len(items)}')
    for b in items[:3]:
        print(f'    {b.get(\"id_proyecto\",\"?\")} | {b.get(\"nombre_proyecto\",\"?\")[:40]} | estado={b.get(\"estado\",\"?\")}')
except: print('  (endpoint no disponible o error)')
"
done

# ══════════════════════════════════════════════════════════════
# F. DIAGNÓSTICO CONCEPTUAL
# ══════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  F. PREGUNTAS CONCEPTUALES PARA ANÁLISIS"
echo "══════════════════════════════════════════════════════════════"
echo ""
echo "  F1. ¿El estado estático de pmo_staff_skills se usa para algo?"
echo "      (campo 'estado' en compartido — ¿sobrescribe el dinámico?)"
echo ""
echo "  F2. ¿carga_actual de pmo_staff_skills refleja la realidad?"
echo "      (¿se actualiza dinámicamente o es un valor fijo del seed?)"
for SC in sc_norte sc_iberico sc_litoral; do
  echo "    $SC — carga_actual stats:"
  $PG -c "SELECT MIN(carga_actual), MAX(carga_actual), AVG(carga_actual)::numeric(5,2), COUNT(*) FILTER (WHERE carga_actual > 0) AS con_carga FROM compartido.pmo_staff_skills;"
done
echo ""
echo "  F3. ¿Debería un técnico poder estar en MÚLTIPLES incidencias?"
echo "      (realista: sí, un técnico P3/P4 puede tener 2-3 tickets)"
echo ""
echo "  F4. ¿El campo estado de incidencias_run solo permite:"
echo "      QUEUED, EN_CURSO, ESCALADO, RESUELTO, CERRADO?"
echo "      ¿Falta un estado ASIGNADO?"
echo ""
echo "  F5. ¿Cuántas incidencias por schema deberían estar abiertas"
echo "      para simular operación real de un banco?"
echo "      sc_norte (pequeño): ¿~15-20 abiertas?"
echo "      sc_iberico (mediano): ¿~30-40 abiertas?"
echo "      sc_litoral (grande): ¿~60-80 abiertas?"
echo ""
echo "  F6. ¿El ratio incidencias/kanban es correcto?"
echo "      Actualmente per-schema:"
for SC in sc_norte sc_iberico sc_litoral; do
  INC=$($PG -c "SELECT COUNT(*) FROM $SC.incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO');")
  KAN=$($PG -c "SELECT COUNT(*) FROM $SC.kanban_tareas WHERE columna NOT IN ('Completado','Done','Backlog');")
  echo "      $SC: $INC inc abiertas / $KAN tareas activas"
done
echo ""
echo "  F7. ¿Cuántos técnicos de cartera_build.responsable_asignado"
echo "      también aparecen como ocupados en incidencias/kanban?"
for SC in sc_norte sc_iberico sc_litoral; do
  $PG -c "
    SELECT COUNT(DISTINCT cb.responsable_asignado) FROM $SC.cartera_build cb
    WHERE cb.responsable_asignado IN (
      SELECT tecnico_asignado FROM $SC.incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO')
      UNION
      SELECT id_tecnico FROM $SC.kanban_tareas WHERE columna NOT IN ('Completado','Done','Backlog')
    );
  "
  echo "  → $SC responsables BUILD que también están ocupados en RUN/kanban"
done

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  FIN INVESTIGACIÓN CONCEPTUAL"
echo "  MANDA ESTE LOG COMPLETO"
echo "══════════════════════════════════════════════════════════════"

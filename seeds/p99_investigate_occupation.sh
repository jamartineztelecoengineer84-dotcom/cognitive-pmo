#!/bin/bash
# ══════════════════════════════════════════════════════════════
# P99 INVESTIGACIÓN CONCEPTUAL — ¿Por qué solo 1% ocupación?
# ══════════════════════════════════════════════════════════════
# Examina TODAS las tablas que determinan si un técnico está
# OCUPADO o DISPONIBLE, por cada schema.
#
# El estado dinámico se calcula en GET /team/tecnicos:
#   1) incidencias_run.tecnico_asignado (estado NOT IN CERRADO/RESUELTO)
#   2) kanban_tareas.id_tecnico (columna NOT IN Completado/Done/Backlog)
#   → Si hay match → ASIGNADO/OCUPADO
#   → Si no → DISPONIBLE
#
# Uso: bash p99_investigate_occupation.sh 2>&1 | tee /tmp/p99_invest_occ.log

echo "════════════════════════════════════════════════════════"
echo "P99 INVESTIGACIÓN OCUPACIÓN TÉCNICOS"
echo "════════════════════════════════════════════════════════"

# Auto-detectar contenedor de BD
DB_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i 'db\|postgres' | head -1)
if [ -z "$DB_CONTAINER" ]; then
  echo "No se encontró contenedor de BD. Intentando psql directo..."
  PG="psql -U cognitive -d cognitive_pmo -t -A"
else
  echo "Contenedor BD: $DB_CONTAINER"
  PG="docker exec $DB_CONTAINER psql -U cognitive -d cognitive_pmo -t -A"
fi

echo ""
echo "═══ 0. POOL DE TÉCNICOS (compartido.pmo_staff_skills) ═══"
$PG -c "SELECT COUNT(*) AS total_tecnicos FROM compartido.pmo_staff_skills;"
$PG -c "SELECT estado, COUNT(*) FROM compartido.pmo_staff_skills GROUP BY estado ORDER BY COUNT(*) DESC;"
echo "--- Primeros 5 IDs de técnicos:"
$PG -c "SELECT id_recurso FROM compartido.pmo_staff_skills ORDER BY id_recurso LIMIT 5;"

for SC in sc_norte sc_iberico sc_litoral; do
  echo ""
  echo "════════════════════════════════════════════════════════"
  echo "  SCHEMA: $SC"
  echo "════════════════════════════════════════════════════════"

  echo ""
  echo "--- 1. incidencias_run: total filas ---"
  $PG -c "SELECT COUNT(*) FROM $SC.incidencias_run;"

  echo "--- 1b. incidencias_run: estados ---"
  $PG -c "SELECT estado, COUNT(*) FROM $SC.incidencias_run GROUP BY estado ORDER BY COUNT(*) DESC;"

  echo "--- 1c. incidencias_run: ABIERTAS (no CERRADO/RESUELTO) ---"
  $PG -c "SELECT COUNT(*) FROM $SC.incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto');"

  echo "--- 1d. incidencias_run: DISTINCT tecnico_asignado en ABIERTAS ---"
  $PG -c "SELECT COUNT(DISTINCT tecnico_asignado) FROM $SC.incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto') AND tecnico_asignado IS NOT NULL AND tecnico_asignado != '';"

  echo "--- 1e. incidencias_run: sample tecnico_asignado ABIERTAS ---"
  $PG -c "SELECT tecnico_asignado, estado, ticket_id FROM $SC.incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto') AND tecnico_asignado IS NOT NULL AND tecnico_asignado != '' LIMIT 10;"

  echo "--- 1f. incidencias_run: ¿tecnico_asignado es FTE-xxx? ---"
  $PG -c "SELECT tecnico_asignado, COUNT(*) FROM $SC.incidencias_run WHERE tecnico_asignado IS NOT NULL AND tecnico_asignado != '' GROUP BY tecnico_asignado ORDER BY COUNT(*) DESC LIMIT 10;"

  echo ""
  echo "--- 2. kanban_tareas: total filas ---"
  $PG -c "SELECT COUNT(*) FROM $SC.kanban_tareas;"

  echo "--- 2b. kanban_tareas: columnas (estados) ---"
  $PG -c "SELECT columna, COUNT(*) FROM $SC.kanban_tareas GROUP BY columna ORDER BY COUNT(*) DESC;"

  echo "--- 2c. kanban_tareas: ACTIVAS (no Completado/Done/Backlog) ---"
  $PG -c "SELECT COUNT(*) FROM $SC.kanban_tareas WHERE columna NOT IN ('Completado','Done','Backlog');"

  echo "--- 2d. kanban_tareas: DISTINCT id_tecnico en ACTIVAS ---"
  $PG -c "SELECT COUNT(DISTINCT id_tecnico) FROM $SC.kanban_tareas WHERE columna NOT IN ('Completado','Done','Backlog') AND id_tecnico IS NOT NULL AND id_tecnico != '';"

  echo "--- 2e. kanban_tareas: sample id_tecnico ACTIVAS ---"
  $PG -c "SELECT id_tecnico, columna, titulo, id_proyecto FROM $SC.kanban_tareas WHERE columna NOT IN ('Completado','Done','Backlog') AND id_tecnico IS NOT NULL AND id_tecnico != '' LIMIT 10;"

  echo "--- 2f. kanban_tareas: ¿id_tecnico es FTE-xxx? ---"
  $PG -c "SELECT id_tecnico, COUNT(*) FROM $SC.kanban_tareas WHERE id_tecnico IS NOT NULL AND id_tecnico != '' GROUP BY id_tecnico ORDER BY COUNT(*) DESC LIMIT 10;"

  echo ""
  echo "--- 3. UNIÓN: técnicos ÚNICOS ocupados (incidencias + kanban) ---"
  $PG -c "
    SELECT COUNT(DISTINCT tecnico) AS tecnicos_ocupados FROM (
      SELECT tecnico_asignado AS tecnico FROM $SC.incidencias_run
        WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto')
        AND tecnico_asignado IS NOT NULL AND tecnico_asignado != ''
      UNION
      SELECT id_tecnico AS tecnico FROM $SC.kanban_tareas
        WHERE columna NOT IN ('Completado','Done','Backlog')
        AND id_tecnico IS NOT NULL AND id_tecnico != ''
    ) sub;
  "

  echo "--- 4. cartera_build: proyectos activos ---"
  $PG -c "SELECT COUNT(*) FROM $SC.cartera_build WHERE estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado');"

  echo "--- 4b. cartera_build: responsable_asignado (¿FTE o PM?) ---"
  $PG -c "SELECT responsable_asignado, COUNT(*) FROM $SC.cartera_build WHERE responsable_asignado IS NOT NULL GROUP BY responsable_asignado ORDER BY COUNT(*) DESC LIMIT 10;"

  echo ""
  echo "--- 5. RESUMEN $SC ---"
  $PG -c "
    SELECT
      (SELECT COUNT(*) FROM compartido.pmo_staff_skills) AS total_tecnicos,
      (SELECT COUNT(DISTINCT tecnico) FROM (
        SELECT tecnico_asignado AS tecnico FROM $SC.incidencias_run
          WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto')
          AND tecnico_asignado IS NOT NULL AND tecnico_asignado != ''
        UNION
        SELECT id_tecnico AS tecnico FROM $SC.kanban_tareas
          WHERE columna NOT IN ('Completado','Done','Backlog')
          AND id_tecnico IS NOT NULL AND id_tecnico != ''
      ) sub) AS tecnicos_ocupados,
      (SELECT COUNT(*) FROM $SC.incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO','Cerrado','Resuelto')) AS incidencias_abiertas,
      (SELECT COUNT(*) FROM $SC.kanban_tareas WHERE columna NOT IN ('Completado','Done','Backlog')) AS tareas_activas,
      (SELECT COUNT(*) FROM $SC.cartera_build WHERE estado NOT IN ('COMPLETADO','CERRADO','Completado','Cerrado')) AS proyectos_activos;
  "
done

echo ""
echo "════════════════════════════════════════════════════════"
echo "═══ 6. DIAGNÓSTICO ESTADO DINÁMICO (main.py) ═══"
echo "════════════════════════════════════════════════════════"
echo "El endpoint /team/tecnicos calcula estado_run_dinamico:"
echo "  1) Busca en incidencias_run WHERE tecnico_asignado=FTE-xxx AND estado NOT IN CERRADO/RESUELTO"
echo "  2) Si match → OCUPADO"
echo "  3) Busca en kanban_tareas WHERE id_tecnico=FTE-xxx AND columna NOT IN Completado/Done/Backlog"
echo "  4) Si match → ASIGNADO"
echo "  5) Si nada → DISPONIBLE"
echo ""
echo "PROBLEMA PROBABLE:"
echo "  - Pocos técnicos asignados en incidencias_run.tecnico_asignado"
echo "  - Pocos/ningún id_tecnico en kanban_tareas"
echo "  - Los seeds originales solo pusieron ~10-20 FTE-xxx diferentes"
echo ""

# Test real del endpoint
echo "═══ 7. TEST REAL /team/tecnicos ═══"
for SC in sc_norte sc_iberico sc_litoral; do
  echo ""
  echo "--- $SC ---"
  curl -s -H "X-Scenario: $SC" http://localhost:8088/team/tecnicos 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data if isinstance(data, list) else data.get('tecnicos', [])
    estados = {}
    for t in items:
        e = t.get('estado', 'SIN')
        estados[e] = estados.get(e, 0) + 1
    total = len(items)
    ocu = sum(v for k,v in estados.items() if k not in ('DISPONIBLE','SIN'))
    print(f'  Total: {total}, Ocupados: {ocu} ({100*ocu//max(total,1)}%), Estados: {dict(sorted(estados.items()))}')
except Exception as e:
    print(f'  ERROR: {e}')
"
done

echo ""
echo "════════════════════════════════════════════════════════"
echo "FIN INVESTIGACIÓN — MANDA ESTE LOG COMPLETO"
echo "════════════════════════════════════════════════════════"

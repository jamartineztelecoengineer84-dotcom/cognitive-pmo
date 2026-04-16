#!/bin/bash
# ═══════════════════════════════════════════════════════════
# P99 INVESTIGACION v3 — 5 issues pendientes
# ═══════════════════════════════════════════════════════════
# Primo: ejecuta y manda el output COMPLETO a Cowork
# Uso: bash p99_investigate_v3.sh 2>&1 | tee /tmp/p99_invest_v3.log

export PGPASSWORD='REDACTED-old-password'
PSQL="psql -h localhost -U jose_admin -d cognitive_pmo -t -A"
MAIN="/root/cognitive-pmo/backend/main.py"
IDX="/root/cognitive-pmo/frontend/index.html"

echo "═══════════════════════════════════════════════════════════"
echo "P99 INVESTIGACION v3 — $(date)"
echo "═══════════════════════════════════════════════════════════"

# ─────────────────────────────────────────────────────────
# 1. INCIDENCIAS: ¿datos distintos por schema?
# ─────────────────────────────────────────────────────────
echo ""
echo "═══ 1. INCIDENCIAS POR SCHEMA ═══"
for SC in primitiva sc_norte sc_iberico sc_litoral; do
  echo "--- $SC ---"
  $PSQL -c "SET search_path=$SC,compartido,public; SELECT COUNT(*) as total, COUNT(CASE WHEN estado NOT IN ('CERRADO','RESUELTO') THEN 1 END) as abiertas, MIN(timestamp_creacion)::date as min_fecha, MAX(timestamp_creacion)::date as max_fecha, COUNT(CASE WHEN sla_limite IS NOT NULL THEN 1 END) as con_sla FROM incidencias_run;"
  echo "  Muestra 3 primeras abiertas:"
  $PSQL -c "SET search_path=$SC,compartido,public; SELECT ticket_id, prioridad, estado, sla_limite, timestamp_creacion FROM incidencias_run WHERE estado NOT IN ('CERRADO','RESUELTO') ORDER BY timestamp_creacion DESC LIMIT 3;"
done

# ─────────────────────────────────────────────────────────
# 2. BACKEND: endpoint /incidencias — qué devuelve sla_horas?
# ─────────────────────────────────────────────────────────
echo ""
echo "═══ 2. BACKEND /incidencias ═══"
grep -n "sla_horas\|sla_limite\|/incidencias" "$MAIN" | head -20
echo "--- Bloque GET /incidencias ---"
grep -n -A 30 '@app.get.*/incidencias' "$MAIN" | head -40

# ─────────────────────────────────────────────────────────
# 3. BACKEND: endpoint /team/tecnicos — tarea_actual?
# ─────────────────────────────────────────────────────────
echo ""
echo "═══ 3. BACKEND /team/tecnicos ═══"
grep -n "tarea_actual\|proyecto_actual\|estado_run_dinamico" "$MAIN" | head -20
echo "--- Bloque completo GET /team/tecnicos ---"
grep -n -A 50 '@app.get.*/team/tecnicos' "$MAIN" | head -60

# ─────────────────────────────────────────────────────────
# 4. BACKEND: endpoint /presupuestos — nombre_proyecto?
# ─────────────────────────────────────────────────────────
echo ""
echo "═══ 4. BACKEND /presupuestos ═══"
grep -n -A 20 '@app.get.*/presupuestos' "$MAIN" | head -30
echo "--- curl test presupuestos sc_norte ---"
curl -s -H "X-Scenario: sc_norte" -H "Authorization: Bearer test" http://localhost:8000/presupuestos 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(type(d).__name__, len(d) if isinstance(d,list) else 'dict'); [print(k) for k in (d[0].keys() if isinstance(d,list) and d else d.keys() if isinstance(d,dict) else [])]" 2>/dev/null || echo "  (curl failed — API may need auth)"

# ─────────────────────────────────────────────────────────
# 5. BACKEND: endpoint /pmo/governance/dashboard — per schema?
# ─────────────────────────────────────────────────────────
echo ""
echo "═══ 5. BACKEND /pmo/governance ═══"
grep -n -A 30 '@app.get.*/pmo/governance/dashboard' "$MAIN" | head -40
echo "--- pmo_project_managers location ---"
grep -n "pmo_project_managers" "$MAIN" | head -10

# ─────────────────────────────────────────────────────────
# 6. FRONTEND index.html: secciones clave
# ─────────────────────────────────────────────────────────
echo ""
echo "═══ 6. FRONTEND index.html ═══"
echo "--- Total lines ---"
wc -l "$IDX"
echo "--- Incidencias fetch ---"
grep -n "incidencias\|sla_horas\|sla_limite\|loadInc\|loadIncidencias" "$IDX" | head -20
echo "--- Presupuestos fetch ---"
grep -n "presupuestos\|loadPres\|loadBudget\|nombre_proyecto\|id_proyecto.*nombre" "$IDX" | head -20
echo "--- Skills ---"
grep -n "skills_requeridas\|skills_req\|competencias\|loadProy\|cartera/proyectos" "$IDX" | head -20
echo "--- PMO GOV capacity ---"
grep -n "capacidad\|Capacidad\|governance/dashboard\|pmo/governance\|carga_pm\|pm_stats" "$IDX" | head -20
echo "--- Team tarea_actual ---"
grep -n "tarea_actual\|proyecto_actual\|vinculacion\|asignado_a" "$IDX" | head -20

# ─────────────────────────────────────────────────────────
# 7. DATA: skills_requeridas en cartera_build
# ─────────────────────────────────────────────────────────
echo ""
echo "═══ 7. SKILLS_REQUERIDAS ═══"
for SC in sc_norte sc_iberico sc_litoral; do
  echo "--- $SC ---"
  $PSQL -c "SET search_path=$SC,compartido,public; SELECT id_proyecto, nombre_proyecto, skills_requeridas FROM cartera_build LIMIT 5;"
done

# ─────────────────────────────────────────────────────────
# 8. DATA: pmo_governance_scoring status
# ─────────────────────────────────────────────────────────
echo ""
echo "═══ 8. GOVERNANCE SCORING ═══"
for SC in sc_norte sc_iberico sc_litoral; do
  echo "--- $SC ---"
  $PSQL -c "SET search_path=$SC,compartido,public; SELECT COUNT(*), AVG(total_score)::numeric(4,1), string_agg(DISTINCT gate_status, ',') FROM pmo_governance_scoring;"
done

# ─────────────────────────────────────────────────────────
# 9. Columns in incidencias_run
# ─────────────────────────────────────────────────────────
echo ""
echo "═══ 9. COLUMNS incidencias_run ═══"
$PSQL -c "SET search_path=sc_norte,compartido,public; SELECT column_name, data_type FROM information_schema.columns WHERE table_name='incidencias_run' AND table_schema='sc_norte' ORDER BY ordinal_position;"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "FIN INVESTIGACION — Manda este log a Cowork"
echo "═══════════════════════════════════════════════════════════"

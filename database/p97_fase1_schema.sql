-- =====================================================================
-- P97 FASE 1 — Schema P96 v6 (12 tablas + 3 vistas sobre datos existentes)
-- Generado: 2026-04-07
-- Sin tocar tablas existentes. Sin seed (eso es FASE 2).
-- =====================================================================

-- ─────────────────────────────────────────────────────────────────────
-- PARTE B — 12 tablas físicas
-- ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS p96_governors (
  id_gov VARCHAR PRIMARY KEY,
  nombre VARCHAR, role_code VARCHAR, silo VARCHAR, av_cls VARCHAR(4),
  projs INT, bac NUMERIC, cpi NUMERIC, spi NUMERIC,
  cap INT, risk INT, ia INT, status CHAR(2),
  team INT, ai_lead BOOL, descripcion TEXT, spark JSONB
);

CREATE TABLE IF NOT EXISTS p96_run_layers (
  k VARCHAR PRIMARY KEY, label VARCHAR, sub VARCHAR, cls VARCHAR, silo VARCHAR
);

CREATE TABLE IF NOT EXISTS p96_run_crits (
  k CHAR(2) PRIMARY KEY, label VARCHAR, sub VARCHAR
);

CREATE TABLE IF NOT EXISTS p96_run_matrix (
  layer VARCHAR REFERENCES p96_run_layers(k),
  crit  CHAR(2) REFERENCES p96_run_crits(k),
  cis INT, opex NUMERIC, inc INT, heat INT,
  PRIMARY KEY (layer, crit)
);

CREATE TABLE IF NOT EXISTS p96_build_project_detail (
  id_proyecto VARCHAR PRIMARY KEY,
  gates JSONB,    -- {G0:'done',G1:'done',G2:'now',G3:'todo',G4:'todo',G5:'todo'}
  team  JSONB,    -- [{n,r,cap}, ...]
  risks JSONB     -- [{lv:'hi'|'lo', t:'...'}]
);

CREATE TABLE IF NOT EXISTS p96_pulse_kpis (
  k VARCHAR PRIMARY KEY,
  lb VARCHAR, vl VARCHAR, un VARCHAR, rag CHAR(2), sub VARCHAR, tt TEXT
);

CREATE TABLE IF NOT EXISTS p96_pulse_alerts (
  id VARCHAR PRIMARY KEY,
  sev CHAR(2), title VARCHAR, descripcion TEXT, meta JSONB, ow VARCHAR
);

CREATE TABLE IF NOT EXISTS p96_pulse_blocks (
  id VARCHAR PRIMARY KEY,
  sev CHAR(2), title VARCHAR, descripcion TEXT, pj VARCHAR, own VARCHAR, days INT
);

CREATE TABLE IF NOT EXISTS p96_pulse_decisions (
  id VARCHAR PRIMARY KEY,
  title VARCHAR, descripcion TEXT, own VARCHAR, amt VARCHAR, due DATE, urg VARCHAR
);

CREATE TABLE IF NOT EXISTS p96_pulse_responsables (
  id SERIAL PRIMARY KEY,
  nm VARCHAR, rl VARCHAR, ct VARCHAR, ini CHAR(2),
  kpi_vl VARCHAR, kpi_lb VARCHAR, lg CHAR(2)
);

CREATE TABLE IF NOT EXISTS p96_pulse_hitos (
  id SERIAL PRIMARY KEY,
  dt VARCHAR, wk VARCHAR, title VARCHAR, descripcion TEXT, tg VARCHAR, tgt VARCHAR
);

CREATE TABLE IF NOT EXISTS p96_strategy_frameworks (
  k VARCHAR PRIMARY KEY,   -- 'dafo'|'pestle'|'porter'|'okr'
  payload JSONB
);

-- ─────────────────────────────────────────────────────────────────────
-- PARTE C — 3 vistas sobre tablas existentes (NO duplicar datos)
-- ─────────────────────────────────────────────────────────────────────

-- v_p96_build_portfolio  ←  build_live (6 filas reales actualmente)
-- silo y ai_lead → NULL (NO existen en build_live)
-- CPI defaultea a 1.00 si presupuesto_consumido = 0
-- SPI defaultea a 1.00 si las fechas o el BAC no permiten cálculo
CREATE OR REPLACE VIEW v_p96_build_portfolio AS
SELECT
  bl.id_proyecto,
  bl.nombre,
  NULL::varchar                              AS silo,
  bl.pm_asignado                             AS pm,
  ROUND(bl.presupuesto_bac/1000)             AS bac_k,
  bl.gate_actual                             AS gate,
  CASE WHEN bl.presupuesto_consumido > 0
       THEN ROUND( (bl.presupuesto_bac * bl.progreso_pct/100.0) / bl.presupuesto_consumido, 2)
       ELSE 1.00
  END                                        AS cpi,
  CASE WHEN bl.presupuesto_bac > 0
        AND bl.fecha_inicio IS NOT NULL
        AND bl.fecha_fin_prevista IS NOT NULL
        AND bl.fecha_fin_prevista > bl.fecha_inicio
       THEN ROUND(
              (bl.progreso_pct/100.0) /
              NULLIF(
                EXTRACT(EPOCH FROM (now() - bl.fecha_inicio)) /
                NULLIF(EXTRACT(EPOCH FROM (bl.fecha_fin_prevista - bl.fecha_inicio)), 0),
              0),
              2)
       ELSE 1.00
  END                                        AS spi,
  bl.prioridad                               AS prio,
  bl.risk_score                              AS risk,
  bl.progreso_pct                            AS prog,
  NULL::boolean                              AS ai_lead
FROM build_live bl;

-- v_p96_run_cis  ←  cmdb_activos (226 CIs reales)
-- inc: COUNT de incidencias_run abiertas para ese CI
-- silo, sla, slo, runbook → NULL (NO existen en cmdb_activos)
CREATE OR REPLACE VIEW v_p96_run_cis AS
SELECT
  ca.id_activo                               AS id,
  ca.nombre                                  AS name,
  ca.capa                                    AS layer,
  ca.criticidad                              AS crit,
  NULL::varchar                              AS silo,
  ca.tipo                                    AS type,
  COALESCE(ca.fabricante, ca.proveedor)      AS vendor,
  ca.coste_mensual                           AS opex,
  COALESCE(
    (SELECT COUNT(*) FROM incidencias_run ir
       WHERE ir.ci_afectado = ca.codigo
         AND ir.estado NOT IN ('RESUELTO','CERRADO','CLOSED')),
    0)                                       AS inc,
  NULL::numeric                              AS sla,
  NULL::numeric                              AS slo,
  COALESCE(ca.responsable_tecnico, ca.propietario) AS owner,
  ca.ubicacion                               AS room,
  NULL::varchar                              AS runbook
FROM cmdb_activos ca;

-- v_p96_run_incidents  ←  incidencias_run (34 filas reales)
-- team, steps → NULL (NO existen en incidencias_run)
CREATE OR REPLACE VIEW v_p96_run_incidents AS
SELECT
  ir.ticket_id                               AS id,
  ir.incidencia_detectada                    AS title,
  ir.prioridad_ia                            AS prio,
  ir.estado                                  AS status,
  ir.ci_afectado                             AS ci,
  ir.timestamp_creacion                      AS opened,
  ir.sla_limite                              AS sla,
  ir.impacto_negocio                         AS impact,
  ir.tecnico_asignado                        AS owner,
  NULL::jsonb                                AS team,
  NULL::jsonb                                AS steps
FROM incidencias_run ir;

-- =====================================================================
-- Verificación esperada:
--   \dt p96_*       → 12 tablas
--   \dv v_p96_*     → 3 vistas
--   SELECT count(*) FROM v_p96_build_portfolio;   → 6
--   SELECT count(*) FROM v_p96_run_cis;            → 226
--   SELECT count(*) FROM v_p96_run_incidents;      → 34
-- =====================================================================

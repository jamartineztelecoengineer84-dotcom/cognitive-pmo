-- ============================================================
-- P99 — Seed CEO Dashboard por escenario
-- Crea p96_run_crits, p96_run_layers, p96_governors, p96_run_matrix
-- en cada sc_* con datos DISTINTOS por banco.
--
-- search_path = (sc_X, compartido, public) → las tablas sc_*
-- tienen prioridad sobre compartido automáticamente.
-- ============================================================

BEGIN;

-- ════════════════════════════════════════════════════════════
-- TABLAS REFERENCIA (misma estructura, copiada a cada schema)
-- ════════════════════════════════════════════════════════════

-- ── p96_run_crits ──
DO $$ BEGIN
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_norte.p96_run_crits   (LIKE compartido.p96_run_crits INCLUDING ALL)';
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_iberico.p96_run_crits (LIKE compartido.p96_run_crits INCLUDING ALL)';
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_litoral.p96_run_crits (LIKE compartido.p96_run_crits INCLUDING ALL)';
END $$;

INSERT INTO sc_norte.p96_run_crits   SELECT * FROM compartido.p96_run_crits ON CONFLICT DO NOTHING;
INSERT INTO sc_iberico.p96_run_crits SELECT * FROM compartido.p96_run_crits ON CONFLICT DO NOTHING;
INSERT INTO sc_litoral.p96_run_crits SELECT * FROM compartido.p96_run_crits ON CONFLICT DO NOTHING;

-- ── p96_run_layers ──
DO $$ BEGIN
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_norte.p96_run_layers   (LIKE compartido.p96_run_layers INCLUDING ALL)';
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_iberico.p96_run_layers (LIKE compartido.p96_run_layers INCLUDING ALL)';
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_litoral.p96_run_layers (LIKE compartido.p96_run_layers INCLUDING ALL)';
END $$;

INSERT INTO sc_norte.p96_run_layers   SELECT * FROM compartido.p96_run_layers ON CONFLICT DO NOTHING;
INSERT INTO sc_iberico.p96_run_layers SELECT * FROM compartido.p96_run_layers ON CONFLICT DO NOTHING;
INSERT INTO sc_litoral.p96_run_layers SELECT * FROM compartido.p96_run_layers ON CONFLICT DO NOTHING;

-- ════════════════════════════════════════════════════════════
-- p96_governors POR ESCENARIO
-- Norte: banco pequeño (BAC reducido, menos riesgo)
-- Ibérico: banco mediano (≈ valores actuales)
-- Litoral: banco grande (BAC alto, más riesgo, más equipo)
-- ════════════════════════════════════════════════════════════

DO $$ BEGIN
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_norte.p96_governors   (LIKE compartido.p96_governors INCLUDING ALL)';
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_iberico.p96_governors (LIKE compartido.p96_governors INCLUDING ALL)';
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_litoral.p96_governors (LIKE compartido.p96_governors INCLUDING ALL)';
END $$;

-- ── SC_NORTE (banco pequeño: ~60% BAC, menos riesgo) ──
INSERT INTO sc_norte.p96_governors VALUES
('GOV-01','Pablo Rivas','PMO_SENIOR','CROSS','bl',5,2.53,1.02,1.01,70,28,82,'gn',4,true,'PMO Senior cross-silo. Banco Norte: cartera reducida, alta eficiencia.','[8,10,12,14,16,18]'),
('GOV-02','Javier Iglesias','DIRECTOR_INFRA','IT-INFRA','gn',4,1.72,1.05,1.02,65,18,75,'gn',6,true,'Director Infraestructura Norte. Infraestructura estable, pocos cambios.','[12,14,16,18,20,22]'),
('GOV-03','Elena Marín','DIRECTOR_SEC','IT-SEGURIDAD','yl',3,1.15,1.08,1.03,60,20,72,'gn',5,true,'Directora Seguridad Norte. Perímetro pequeño, cumplimiento alto.','[10,12,14,16,18,20]'),
('GOV-04','Marta Núñez','TEAM_LEAD','IT-INFRA','gn',3,0.92,0.98,0.97,75,25,85,'or',5,false,'Team Lead Infra Norte. Equipo compacto y eficiente.','[8,10,12,14,16,18]'),
('GOV-05','Raúl Santos','VP_OPERATIONS','CROSS','bl',4,2.09,1.01,0.99,60,22,68,'or',8,true,'VP Operaciones Norte. Baja complejidad operativa.','[14,16,18,20,22,24]'),
('GOV-06','Andrés Vela','PM_BUILD','IT-DATA','or',3,1.28,0.95,0.96,80,32,78,'or',3,false,'PM BUILD Data Norte. Pocos proyectos pero alta carga unitaria.','[6,8,10,12,14,16]'),
('GOV-07','Lorena Castillo','PMO_JUNIOR','IT-RED','gn',2,0.68,1.06,1.04,50,12,90,'gn',3,true,'PMO Junior Red Norte. Red sencilla, buen control.','[4,6,8,10,12,14]'),
('GOV-08','Sergio Mateos','PM_BUILD','IT-CLOUD','rd',3,1.44,0.72,0.78,85,52,65,'rd',4,false,'PM BUILD Cloud Norte. Migración cloud con retrasos.','[10,12,14,16,18,20]'),
('GOV-09','Nuria Beltrán','PM_BUILD','IT-VIRTUAL','gn',2,0.55,1.04,1.02,55,15,72,'gn',3,true,'PM BUILD Virtual Norte. Virtualización básica OK.','[6,8,10,12,14,16]'),
('GOV-10','Diego Herrera','TEAM_LEAD','IT-STORAGE','yl',2,0.75,0.94,0.92,70,30,60,'or',4,false,'Team Lead Storage Norte. Cabinas antiguas, riesgo medio.','[8,10,12,14,16,18]'),
('GOV-11','Carmen Ruiz','DIRECTOR_APPS','IT-APPS','gn',3,1.35,1.03,1.01,65,20,76,'gn',5,true,'Directora Apps Norte. Portfolio reducido, buena salud.','[10,12,14,16,18,20]'),
('GOV-12','Tomás Gil','PM_BUILD','IT-SEGURIDAD','yl',2,0.82,0.97,0.95,75,28,70,'or',3,false,'PM BUILD Seguridad Norte. SIEM en proceso.','[6,8,10,12,14,16]'),
('GOV-13','Isabel Mora','PMO_SENIOR','IT-DATA','gn',4,1.88,1.01,1.00,60,22,80,'gn',6,true,'PMO Senior Data Norte. Data warehouse pequeño pero limpio.','[12,14,16,18,20,22]'),
('GOV-14','Felipe Ortiz','TEAM_LEAD','IT-CLOUD','or',2,0.95,0.90,0.88,80,38,55,'or',4,false,'Team Lead Cloud Norte. Kubernetes en maduración.','[8,10,12,14,16,18]'),
('GOV-15','Laura Vega','PM_BUILD','IT-APPS','gn',3,1.10,1.02,1.01,55,16,82,'gn',4,true,'PM BUILD Apps Norte. Migración legacy progresa bien.','[8,10,12,14,16,18]')
ON CONFLICT DO NOTHING;

-- ── SC_IBÉRICO (banco mediano: ≈ valores actuales, ligeramente ajustados) ──
INSERT INTO sc_iberico.p96_governors VALUES
('GOV-01','Pablo Rivas','PMO_SENIOR','CROSS','bl',8,4.21,0.96,0.98,95,42,78,'or',6,true,'PMO Senior cross-silo. Banco Ibérico: cartera media-alta.','[12,18,15,22,28,35]'),
('GOV-02','Javier Iglesias','DIRECTOR_INFRA','IT-INFRA','gn',6,2.87,1.02,0.99,80,24,71,'gn',9,true,'Director Infraestructura Ibérico. Renovación backbone activa.','[18,22,28,30,32,38]'),
('GOV-03','Elena Marín','DIRECTOR_SEC','IT-SEGURIDAD','yl',5,1.92,1.05,1.00,85,28,69,'or',7,true,'Directora Seguridad Ibérico. SOC+SIEM en expansión.','[15,18,22,25,28,32]'),
('GOV-04','Marta Núñez','TEAM_LEAD','IT-INFRA','gn',4,1.54,0.91,0.94,90,38,82,'or',8,false,'Team Lead Infra Ibérico. Servidores al límite.','[14,18,20,22,26,30]'),
('GOV-05','Raúl Santos','VP_OPERATIONS','CROSS','bl',7,3.48,0.97,0.96,75,35,65,'or',12,true,'VP Operaciones Ibérico. 7 proyectos cross-silo.','[22,26,30,34,38,42]'),
('GOV-06','Andrés Vela','PM_BUILD','IT-DATA','or',5,2.14,0.88,0.92,100,48,75,'rd',4,false,'PM BUILD Data Ibérico. Fabric+DW sobredimensionado.','[10,14,18,22,26,30]'),
('GOV-07','Lorena Castillo','PMO_JUNIOR','IT-RED','gn',3,1.02,1.03,1.01,65,18,88,'gn',5,true,'PMO Junior Red Ibérico. Backbone estable.','[8,10,12,14,16,18]'),
('GOV-08','Sergio Mateos','PM_BUILD','IT-CLOUD','rd',5,2.35,0.65,0.86,110,74,62,'rd',6,false,'PM BUILD Cloud Ibérico. Migración con bloqueos serios.','[18,22,28,32,38,44]'),
('GOV-09','Nuria Beltrán','PM_BUILD','IT-VIRTUAL','gn',3,0.88,0.99,1.00,70,22,72,'gn',4,true,'PM BUILD Virtual Ibérico. Hipervisores renovados.','[10,12,14,16,18,20]'),
('GOV-10','Diego Herrera','TEAM_LEAD','IT-STORAGE','yl',4,1.45,0.93,0.90,85,35,58,'or',6,false,'Team Lead Storage Ibérico. Cabinas en EOL.','[12,16,20,24,28,32]'),
('GOV-11','Carmen Ruiz','DIRECTOR_APPS','IT-APPS','gn',5,2.20,1.01,0.99,75,25,74,'or',7,true,'Directora Apps Ibérico. Portfolio diversificado.','[16,20,24,28,32,36]'),
('GOV-12','Tomás Gil','PM_BUILD','IT-SEGURIDAD','yl',3,1.38,0.96,0.94,80,32,68,'or',5,false,'PM BUILD Seguridad Ibérico. Compliance en curso.','[10,14,18,22,26,30]'),
('GOV-13','Isabel Mora','PMO_SENIOR','IT-DATA','gn',6,3.15,1.00,0.98,65,26,78,'or',8,true,'PMO Senior Data Ibérico. Data lake + BI activo.','[18,22,26,30,34,38]'),
('GOV-14','Felipe Ortiz','TEAM_LEAD','IT-CLOUD','or',4,1.65,0.88,0.85,90,42,52,'or',5,false,'Team Lead Cloud Ibérico. K8s con problemas de escala.','[14,18,22,26,30,34]'),
('GOV-15','Laura Vega','PM_BUILD','IT-APPS','gn',5,1.85,1.00,0.99,60,20,80,'gn',6,true,'PM BUILD Apps Ibérico. Legacy casi migrado.','[14,18,22,26,30,34]')
ON CONFLICT DO NOTHING;

-- ── SC_LITORAL (banco grande: ~150% BAC, más riesgo, más equipo) ──
INSERT INTO sc_litoral.p96_governors VALUES
('GOV-01','Pablo Rivas','PMO_SENIOR','CROSS','bl',12,6.32,0.91,0.94,100,58,72,'rd',9,true,'PMO Senior cross-silo. Banco Litoral: megacartera diversificada.','[20,28,35,42,48,55]'),
('GOV-02','Javier Iglesias','DIRECTOR_INFRA','IT-INFRA','gn',9,4.31,0.98,0.96,90,35,68,'or',14,true,'Director Infraestructura Litoral. Backbone nacional + 3 CPDs.','[28,32,38,42,48,55]'),
('GOV-03','Elena Marín','DIRECTOR_SEC','IT-SEGURIDAD','yl',8,2.88,1.01,0.98,95,38,65,'or',10,true,'Directora Seguridad Litoral. SOC 24/7 + SIEM + threat hunting.','[22,28,32,38,42,48]'),
('GOV-04','Marta Núñez','TEAM_LEAD','IT-INFRA','gn',6,2.31,0.88,0.90,100,48,78,'rd',12,false,'Team Lead Infra Litoral. Saturación de capacidad.','[20,26,32,38,44,50]'),
('GOV-05','Raúl Santos','VP_OPERATIONS','CROSS','bl',10,5.22,0.93,0.92,85,45,60,'rd',18,true,'VP Operaciones Litoral. Complejidad cross-silo extrema.','[32,38,44,50,56,62]'),
('GOV-06','Andrés Vela','PM_BUILD','IT-DATA','or',8,3.21,0.82,0.88,100,62,70,'rd',6,false,'PM BUILD Data Litoral. Fabric nacional sobredimensionado.','[16,22,28,34,40,46]'),
('GOV-07','Lorena Castillo','PMO_JUNIOR','IT-RED','gn',5,1.53,1.00,0.98,75,24,85,'or',7,true,'PMO Junior Red Litoral. Red WAN + SD-WAN compleja.','[12,16,20,24,28,32]'),
('GOV-08','Sergio Mateos','PM_BUILD','IT-CLOUD','rd',8,3.53,0.58,0.75,120,88,58,'rd',9,false,'PM BUILD Cloud Litoral. Multi-cloud con crisis de costes.','[28,34,42,48,56,64]'),
('GOV-09','Nuria Beltrán','PM_BUILD','IT-VIRTUAL','gn',5,1.32,0.96,0.97,80,28,68,'or',6,true,'PM BUILD Virtual Litoral. 2000+ VMs, consolidación activa.','[14,18,22,26,30,34]'),
('GOV-10','Diego Herrera','TEAM_LEAD','IT-STORAGE','yl',6,2.18,0.89,0.87,95,45,54,'rd',8,false,'Team Lead Storage Litoral. 5 PB, cabinas EOL urgente.','[18,24,30,36,42,48]'),
('GOV-11','Carmen Ruiz','DIRECTOR_APPS','IT-APPS','gn',8,3.30,0.97,0.96,80,32,70,'or',10,true,'Directora Apps Litoral. 200+ apps, modernización masiva.','[24,30,36,42,48,54]'),
('GOV-12','Tomás Gil','PM_BUILD','IT-SEGURIDAD','yl',5,2.07,0.93,0.91,90,42,64,'or',7,false,'PM BUILD Seguridad Litoral. Zero trust en despliegue.','[14,20,26,32,38,44]'),
('GOV-13','Isabel Mora','PMO_SENIOR','IT-DATA','gn',9,4.73,0.97,0.95,70,34,75,'or',12,true,'PMO Senior Data Litoral. Data mesh + BI federado.','[26,32,38,44,50,56]'),
('GOV-14','Felipe Ortiz','TEAM_LEAD','IT-CLOUD','or',6,2.48,0.84,0.82,100,52,48,'rd',7,false,'Team Lead Cloud Litoral. K8s nacional con 3 clústers.','[20,26,32,38,44,50]'),
('GOV-15','Laura Vega','PM_BUILD','IT-APPS','gn',7,2.78,0.98,0.97,65,24,76,'gn',8,true,'PM BUILD Apps Litoral. Core banking en migración.','[20,26,32,38,44,50]')
ON CONFLICT DO NOTHING;


-- ════════════════════════════════════════════════════════════
-- p96_run_matrix POR ESCENARIO
-- 8 layers × 4 criticidades = 32 celdas
-- Norte: ~60% (banco pequeño, menos CIs, menos OPEX)
-- Ibérico: ≈100% (valores base)
-- Litoral: ~150% (banco grande, más CIs, más OPEX, más incidencias)
-- ════════════════════════════════════════════════════════════

DO $$ BEGIN
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_norte.p96_run_matrix   (LIKE compartido.p96_run_matrix INCLUDING ALL)';
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_iberico.p96_run_matrix (LIKE compartido.p96_run_matrix INCLUDING ALL)';
  EXECUTE 'CREATE TABLE IF NOT EXISTS sc_litoral.p96_run_matrix (LIKE compartido.p96_run_matrix INCLUDING ALL)';
END $$;

-- ── SC_NORTE (pequeño: ~135 CIs, ~370k OPEX, ~25 inc) ──
INSERT INTO sc_norte.p96_run_matrix (layer, crit, cis, opex, inc, heat) VALUES
('INFRA','C1',5,47000,1,38),('INFRA','C2',7,32000,1,28),('INFRA','C3',8,17000,0,14),('INFRA','C4',4,5000,0,5),
('RED','C1',4,31000,1,33),('RED','C2',5,20000,1,29),('RED','C3',7,11000,0,12),('RED','C4',2,3000,0,4),
('CLOUD','C1',3,55000,2,52),('CLOUD','C2',5,37000,1,35),('CLOUD','C3',6,21000,1,18),('CLOUD','C4',3,7000,0,8),
('VIRTUAL','C1',2,25000,0,24),('VIRTUAL','C2',4,17000,1,23),('VIRTUAL','C3',5,9000,1,10),('VIRTUAL','C4',2,4000,0,3),
('STORAGE','C1',2,35000,1,31),('STORAGE','C2',4,23000,0,19),('STORAGE','C3',5,11000,0,11),('STORAGE','C4',2,5000,0,4),
('SEGURIDAD','C1',4,38000,2,43),('SEGURIDAD','C2',3,19000,1,25),('SEGURIDAD','C3',4,10000,1,12),('SEGURIDAD','C4',1,3000,0,3),
('DATA','C1',2,48000,2,47),('DATA','C2',4,29000,1,27),('DATA','C3',4,13000,1,13),('DATA','C4',2,5000,0,5),
('APPS','C1',3,43000,2,51),('APPS','C2',5,25000,2,30),('APPS','C3',5,13000,1,16),('APPS','C4',2,5000,0,7)
ON CONFLICT DO NOTHING;

-- ── SC_IBÉRICO (mediano: ~226 CIs, ~619k OPEX, ~47 inc — valores base) ──
INSERT INTO sc_iberico.p96_run_matrix (layer, crit, cis, opex, inc, heat) VALUES
('INFRA','C1',8,78000,3,62),('INFRA','C2',12,54000,2,45),('INFRA','C3',14,28000,1,22),('INFRA','C4',6,9000,0,8),
('RED','C1',6,52000,2,55),('RED','C2',9,34000,3,48),('RED','C3',11,18000,1,20),('RED','C4',4,5500,0,6),
('CLOUD','C1',5,92000,4,85),('CLOUD','C2',8,61000,3,58),('CLOUD','C3',10,35000,2,30),('CLOUD','C4',5,12000,0,14),
('VIRTUAL','C1',3,41000,1,40),('VIRTUAL','C2',7,29000,2,38),('VIRTUAL','C3',9,15000,2,16),('VIRTUAL','C4',4,6000,0,5),
('STORAGE','C1',4,58000,2,52),('STORAGE','C2',6,38000,1,32),('STORAGE','C3',8,19000,1,18),('STORAGE','C4',3,7500,0,7),
('SEGURIDAD','C1',7,64000,3,72),('SEGURIDAD','C2',5,32000,2,42),('SEGURIDAD','C3',6,17000,1,19),('SEGURIDAD','C4',2,4500,0,5),
('DATA','C1',4,80000,3,78),('DATA','C2',6,48000,2,44),('DATA','C3',7,21000,1,22),('DATA','C4',3,8500,0,8),
('APPS','C1',5,72000,4,80),('APPS','C2',8,42000,3,50),('APPS','C3',9,22000,2,26),('APPS','C4',4,8500,0,12)
ON CONFLICT DO NOTHING;

-- ── SC_LITORAL (grande: ~340 CIs, ~930k OPEX, ~75 inc) ──
INSERT INTO sc_litoral.p96_run_matrix (layer, crit, cis, opex, inc, heat) VALUES
('INFRA','C1',12,117000,5,82),('INFRA','C2',18,81000,3,62),('INFRA','C3',21,42000,2,30),('INFRA','C4',9,13500,0,11),
('RED','C1',9,78000,3,72),('RED','C2',14,51000,4,65),('RED','C3',16,27000,2,28),('RED','C4',6,8250,0,8),
('CLOUD','C1',8,138000,6,95),('CLOUD','C2',12,91500,5,78),('CLOUD','C3',15,52500,3,42),('CLOUD','C4',8,18000,1,18),
('VIRTUAL','C1',5,61500,2,55),('VIRTUAL','C2',11,43500,3,52),('VIRTUAL','C3',14,22500,3,22),('VIRTUAL','C4',6,9000,0,7),
('STORAGE','C1',6,87000,3,70),('STORAGE','C2',9,57000,2,45),('STORAGE','C3',12,28500,2,25),('STORAGE','C4',5,11250,0,10),
('SEGURIDAD','C1',11,96000,5,92),('SEGURIDAD','C2',8,48000,3,58),('SEGURIDAD','C3',9,25500,2,26),('SEGURIDAD','C4',3,6750,0,7),
('DATA','C1',6,120000,5,95),('DATA','C2',9,72000,3,60),('DATA','C3',11,31500,2,30),('DATA','C4',5,12750,0,11),
('APPS','C1',8,108000,6,95),('APPS','C2',12,63000,5,68),('APPS','C3',14,33000,3,35),('APPS','C4',6,12750,1,16)
ON CONFLICT DO NOTHING;


-- ════════════════════════════════════════════════════════════
-- VERIFICACIÓN
-- ════════════════════════════════════════════════════════════

SELECT '=== GOVERNORS ===' AS seccion;
SELECT schema, count, round(sum_bac,2) AS total_bac, round(avg_cpi,2) AS avg_cpi
FROM (
  SELECT 'sc_norte' AS schema, COUNT(*) AS count, SUM(bac) AS sum_bac, AVG(cpi) AS avg_cpi FROM sc_norte.p96_governors
  UNION ALL
  SELECT 'sc_iberico', COUNT(*), SUM(bac), AVG(cpi) FROM sc_iberico.p96_governors
  UNION ALL
  SELECT 'sc_litoral', COUNT(*), SUM(bac), AVG(cpi) FROM sc_litoral.p96_governors
) t;

SELECT '=== RUN MATRIX ===' AS seccion;
SELECT schema, count, total_cis, round(total_opex) AS total_opex, total_inc
FROM (
  SELECT 'sc_norte' AS schema, COUNT(*) AS count, SUM(cis) AS total_cis, SUM(opex) AS total_opex, SUM(inc) AS total_inc FROM sc_norte.p96_run_matrix
  UNION ALL
  SELECT 'sc_iberico', COUNT(*), SUM(cis), SUM(opex), SUM(inc) FROM sc_iberico.p96_run_matrix
  UNION ALL
  SELECT 'sc_litoral', COUNT(*), SUM(cis), SUM(opex), SUM(inc) FROM sc_litoral.p96_run_matrix
) t;

COMMIT;

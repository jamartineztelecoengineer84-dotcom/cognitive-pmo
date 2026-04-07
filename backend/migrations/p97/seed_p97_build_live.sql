-- =====================================================================
-- P97 FASE 2 — UPSERT 60 proyectos en build_live (cartera P96 v6 completa)
-- Source: bgPortfolio (l.2634-2704 del mockup)
-- Mapping:
--   p[0]=id, p[1]=nombre, p[2]=silo, p[3]=pm, p[4]=bacK (en miles → ×1000)
--   p[5]=gate, p[6]=cpi, p[7]=spi, p[8]=prio (1-4 → texto), p[9]=risk
--   p[10]=prog%, p[11]=ai_lead
-- presupuesto_consumido = ROUND( (BAC × prog/100) / cpi )    -- AC = EV/CPI
-- ON CONFLICT pisa todas las columnas EXCEPTO fechas (COALESCE para preservar)
-- =====================================================================

BEGIN;

-- Mapeo prioridad: 4=Crítica, 3=Alta, 2=Media, 1=Baja
WITH portfolio(id_proyecto, nombre, silo, pm, bac_k, gate, cpi, spi, prio_n, risk_n, prog_n, ai) AS (VALUES
  ('PRJ-MSF','Microsoft Fabric — nuevo entorno analítico',  'IT-DATA',     'Pablo Rivas',     1178,'G2',0.94,0.87,4,3,35,true),
  ('PRJ-BBN','Renovación Backbone Core de red',             'IT-RED',      'Javier Iglesias',  765,'G3',1.07,1.03,4,2,70,true),
  ('PRJ-OSP','OpenShift on-premise · plataforma',           'IT-CLOUD',    'Sergio Mateos',    650,'G2',0.65,0.86,4,4,30,false),
  ('PRJ-NAC','Clearpass NAC · oficinas',                    'IT-RED',      'Javier Iglesias',  640,'G3',1.05,1.00,3,2,75,false),
  ('PRJ-SOC','SOC unificado SIEM/SOAR',                     'IT-SEGURIDAD','Elena Marín',      512,'G3',1.05,1.00,4,2,70,true),
  -- IT-INFRA (10)
  ('PRJ-HPE','Renovación servidores HPE ProLiant Gen11',    'IT-INFRA',    'Beatriz Lago',     485,'G3',1.02,0.99,3,2,60,true),
  ('PRJ-ADF','Upgrade Active Directory forest 2025',        'IT-INFRA',    'Javier Iglesias',  210,'G4',0.98,1.01,3,2,85,false),
  ('PRJ-DCI','Implantación DCIM Nlyte',                     'IT-INFRA',    'Beatriz Lago',     320,'G2',0.95,0.92,2,2,40,true),
  ('PRJ-CAP','Capacity planning automated',                 'IT-INFRA',    'Beatriz Lago',     155,'G1',1.00,1.00,2,1,15,true),
  ('PRJ-ROC','RHEL 9 → Rocky Linux migration',              'IT-INFRA',    'Javier Iglesias',  180,'G2',0.97,0.95,3,3,45,false),
  ('PRJ-PRO','Prometheus + Grafana stack corporate',        'IT-INFRA',    'Marta Núñez',      145,'G3',1.04,1.02,2,1,70,true),
  ('PRJ-TAN','Tanium endpoint management',                  'IT-INFRA',    'Marta Núñez',      220,'G4',1.00,0.98,3,2,80,false),
  ('PRJ-INT','SCCM → Intune migration',                     'IT-INFRA',    'Marta Núñez',      195,'G2',0.92,0.90,2,3,35,false),
  ('PRJ-PXY','Proxy corporate upgrade',                     'IT-INFRA',    'Marta Núñez',      120,'G3',1.01,1.00,1,1,65,false),
  ('PRJ-NTP','Stratum NTP redundant',                       'IT-INFRA',    'Marta Núñez',       45,'G5',1.06,1.05,1,1,100,false),
  -- IT-RED (6)
  ('PRJ-SDW','SD-WAN rollout 38 oficinas',                  'IT-RED',      'Javier Iglesias',  420,'G2',0.93,0.91,3,3,40,true),
  ('PRJ-VPN','VPN GlobalProtect Palo Alto',                 'IT-RED',      'Rubén Ortiz',      185,'G3',1.02,1.00,3,2,65,false),
  ('PRJ-DNS','Infoblox DDI modernization',                  'IT-RED',      'Rubén Ortiz',      220,'G2',0.98,0.96,2,2,35,false),
  ('PRJ-WIF','WiFi 6E corporate refresh',                   'IT-RED',      'Rubén Ortiz',      240,'G3',1.03,1.01,2,2,60,false),
  ('PRJ-ISE','Cisco ISE RADIUS',                            'IT-RED',      'Carlos Vega',      165,'G3',0.99,0.98,2,2,55,false),
  ('PRJ-F5L','F5 Big-IP load balancer refresh',             'IT-RED',      'Carlos Vega',      195,'G2',0.95,0.94,3,2,40,false),
  -- IT-CLOUD (8)
  ('PRJ-AZR','Azure landing zone enterprise',               'IT-CLOUD',    'Sergio Mateos',    580,'G3',0.91,0.93,4,3,55,true),
  ('PRJ-AWS','AWS pilot digital bank',                      'IT-CLOUD',    'Hugo Ramos',       340,'G1',1.00,1.00,3,3,20,true),
  ('PRJ-OCI','Oracle Cloud para DW',                        'IT-CLOUD',    'Hugo Ramos',       285,'G2',0.88,0.90,3,3,35,false),
  ('PRJ-GCP','GCP data lake POC',                           'IT-CLOUD',    'Sergio Mateos',    120,'G1',1.00,1.00,2,3,10,true),
  ('PRJ-TER','Terraform + IaC governance',                  'IT-CLOUD',    'Hugo Ramos',       165,'G3',1.04,1.02,2,2,65,true),
  ('PRJ-CST','FinOps · Cloud cost optimization',            'IT-CLOUD',    'Sergio Mateos',     85,'G4',1.08,1.05,2,1,85,true),
  ('PRJ-CFN','CloudFront CDN enterprise',                   'IT-CLOUD',    'Hugo Ramos',        95,'G3',1.00,0.99,2,1,60,false),
  ('PRJ-SAA','SaaS catalog rationalization',                'IT-CLOUD',    'Sergio Mateos',     75,'G2',0.96,0.95,1,2,40,false),
  -- IT-VIRTUAL (5)
  ('PRJ-VMW','Broadcom vSphere migration strategy',         'IT-VIRTUAL',  'Nuria Beltrán',    385,'G2',0.92,0.93,4,4,30,true),
  ('PRJ-OSV','OpenShift Virtualization POC',                'IT-VIRTUAL',  'Nuria Beltrán',    145,'G1',1.00,1.00,3,3,15,true),
  ('PRJ-PMX','Proxmox VE pilot',                            'IT-VIRTUAL',  'Nuria Beltrán',     85,'G2',1.00,0.98,2,3,35,false),
  ('PRJ-VDI','Citrix VDI refresh 500 usuarios',             'IT-VIRTUAL',  'Nuria Beltrán',    245,'G3',0.97,0.96,3,2,60,false),
  ('PRJ-HCI','Nutanix HCI evaluación',                      'IT-VIRTUAL',  'Nuria Beltrán',    110,'G1',1.00,1.00,2,2,12,false),
  -- IT-STORAGE (6)
  ('PRJ-NTA','NetApp AFF A900 upgrade',                     'IT-STORAGE',  'Inés Carmona',     320,'G3',1.03,1.01,3,2,65,false),
  ('PRJ-DEL','Dell PowerStore consolidation',               'IT-STORAGE',  'Inés Carmona',     285,'G2',0.98,0.97,3,3,45,false),
  ('PRJ-BKP','Rubrik backup modernization',                 'IT-STORAGE',  'Inés Carmona',     220,'G3',1.02,1.00,3,2,60,true),
  ('PRJ-RAN','Ransomware immutable storage',                'IT-STORAGE',  'Inés Carmona',     195,'G4',1.04,1.02,4,2,80,true),
  ('PRJ-OBJ','Object storage S3-compat',                    'IT-STORAGE',  'Inés Carmona',     140,'G2',0.97,0.96,2,2,40,false),
  ('PRJ-ARC','Archive cold storage tier',                   'IT-STORAGE',  'Inés Carmona',      95,'G1',1.00,1.00,1,1,15,false),
  -- IT-SEGURIDAD (7)
  ('PRJ-PAM','CyberArk PAM rollout',                        'IT-SEGURIDAD','Elena Marín',      340,'G2',0.94,0.95,4,3,40,true),
  ('PRJ-EDR','CrowdStrike Falcon EDR',                      'IT-SEGURIDAD','Diego Soler',      285,'G4',1.05,1.03,4,2,85,true),
  ('PRJ-DLP','Symantec DLP refresh',                        'IT-SEGURIDAD','Diego Soler',      180,'G3',0.99,0.98,3,2,60,false),
  ('PRJ-ZTN','Zero Trust Network Access',                   'IT-SEGURIDAD','Elena Marín',      265,'G2',0.92,0.93,4,3,35,true),
  ('PRJ-WAF','Imperva WAF upgrade',                         'IT-SEGURIDAD','Nuria Gil',        140,'G3',1.01,1.00,3,2,65,false),
  ('PRJ-CMP','DORA compliance program',                     'IT-SEGURIDAD','Elena Marín',      220,'G3',0.96,0.97,4,3,55,true),
  ('PRJ-MFA','MFA Okta enterprise',                         'IT-SEGURIDAD','Nuria Gil',        165,'G4',1.03,1.02,3,2,80,false),
  -- IT-DATA (7)
  ('PRJ-DBT','dbt transformation framework',                'IT-DATA',     'Pablo Rivas',      185,'G3',1.02,1.00,3,2,65,true),
  ('PRJ-CAT','Collibra data catalog',                       'IT-DATA',     'Tomás Aranda',     240,'G2',0.95,0.94,3,3,40,true),
  ('PRJ-GOV','Data governance program',                     'IT-DATA',     'Tomás Aranda',     195,'G2',0.93,0.92,4,3,35,true),
  ('PRJ-ETL','Informatica → Fabric migration',              'IT-DATA',     'Sandra Ortega',    265,'G2',0.90,0.88,3,3,30,true),
  ('PRJ-ODS','ODS real-time refactor',                      'IT-DATA',     'Daniel Pérez',     185,'G3',0.98,0.97,3,3,55,false),
  ('PRJ-MDM','Master Data Management',                      'IT-DATA',     'Tomás Aranda',     220,'G1',1.00,1.00,3,3,15,true),
  ('PRJ-DLK','Data lake modernization',                     'IT-DATA',     'Sandra Ortega',    310,'G2',0.95,0.94,3,3,40,true),
  -- IT-APPS (6)
  ('PRJ-T24','T24 Temenos R24 upgrade',                     'IT-APPS',     'Raúl Santos',      820,'G2',0.89,0.90,4,4,35,true),
  ('PRJ-CRM','Salesforce FS Cloud rollout',                 'IT-APPS',     'Raúl Santos',      485,'G2',0.92,0.93,4,3,40,true),
  ('PRJ-EBN','eBanking UX refresh',                         'IT-APPS',     'Raúl Santos',      385,'G3',1.00,0.99,4,2,65,true),
  ('PRJ-MOB','Mobile app V5 rollout',                       'IT-APPS',     'Raúl Santos',      320,'G3',1.03,1.02,4,2,75,true),
  ('PRJ-API','API gateway Kong',                            'IT-APPS',     'Raúl Santos',      195,'G3',1.01,1.00,3,2,60,false),
  ('PRJ-PAY','Payment gateway upgrade',                     'IT-APPS',     'Raúl Santos',      240,'G2',0.94,0.95,4,3,40,false)
)
INSERT INTO build_live (
  id_proyecto, nombre, silo, pm_asignado,
  presupuesto_bac, presupuesto_consumido,
  gate_actual, prioridad, risk_score, progreso_pct, ai_lead,
  estado, fecha_inicio, fecha_fin_prevista
)
SELECT
  p.id_proyecto,
  p.nombre,
  p.silo,
  p.pm,
  p.bac_k * 1000                                         AS presupuesto_bac,
  ROUND( (p.bac_k * 1000.0 * p.prog_n / 100.0) / p.cpi ) AS presupuesto_consumido,
  p.gate,
  CASE p.prio_n WHEN 4 THEN 'Crítica' WHEN 3 THEN 'Alta' WHEN 2 THEN 'Media' ELSE 'Baja' END,
  p.risk_n,
  p.prog_n,
  p.ai,
  'EN_EJECUCION',
  '2025-10-01'::timestamp,
  '2026-12-31'::timestamp
FROM portfolio p
ON CONFLICT (id_proyecto) DO UPDATE SET
  nombre                = EXCLUDED.nombre,
  silo                  = EXCLUDED.silo,
  pm_asignado           = EXCLUDED.pm_asignado,
  presupuesto_bac       = EXCLUDED.presupuesto_bac,
  presupuesto_consumido = EXCLUDED.presupuesto_consumido,
  gate_actual           = EXCLUDED.gate_actual,
  prioridad             = EXCLUDED.prioridad,
  risk_score            = EXCLUDED.risk_score,
  progreso_pct          = EXCLUDED.progreso_pct,
  ai_lead               = EXCLUDED.ai_lead,
  -- preservar fechas si ya existían
  fecha_inicio          = COALESCE(build_live.fecha_inicio,       EXCLUDED.fecha_inicio),
  fecha_fin_prevista    = COALESCE(build_live.fecha_fin_prevista, EXCLUDED.fecha_fin_prevista);

COMMIT;

-- VERIFICACIÓN
SELECT 'build_live total'                       AS lbl, COUNT(*) FROM build_live
UNION ALL SELECT 'build_live con silo NOT NULL', COUNT(*) FROM build_live WHERE silo IS NOT NULL
UNION ALL SELECT 'v_p96_build_portfolio total',  COUNT(*) FROM v_p96_build_portfolio
UNION ALL SELECT 'v_p96_build_portfolio con silo', COUNT(*) FROM v_p96_build_portfolio WHERE silo IS NOT NULL;

SELECT silo, COUNT(*) FROM build_live WHERE silo IS NOT NULL GROUP BY silo ORDER BY 2 DESC;

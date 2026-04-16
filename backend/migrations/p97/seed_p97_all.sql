-- =====================================================================
-- P97 FASE 2 — Seed P96 v6 (12 tablas físicas + 5 detalles BUILD)
-- Source: /volume1/docker/cognitive-pmo/work/p96_v6_source.html
-- Idempotente: ON CONFLICT DO NOTHING en todas las tablas con PK natural
-- NO toca tablas existentes (build_live + cmdb_activos van en seed_p97_build_live.sql)
-- =====================================================================

BEGIN;

-- ─────────────────────────────────────────────────────────────────────
-- 1) p96_governors  ← bgGovernorsData (l.2153, 15 filas)
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_governors (id_gov, nombre, role_code, silo, av_cls, projs, bac, cpi, spi, cap, risk, ia, status, team, ai_lead, descripcion, spark) VALUES
('GOV-01','Pablo Rivas',         'PMO_SENIOR',     'CROSS',        'bl', 8, 4.21, 0.96, 0.98,  95, 42, 78, 'or',  6, true,  'PMO Senior con responsabilidad cross-silo. Lleva 8 proyectos BUILD activos en IT-DATA, IT-CLOUD y oficinas.', '[12,18,15,22,28,35]'::jsonb),
('GOV-02','Javier Iglesias',     'DIRECTOR_INFRA', 'IT-INFRA',     'gn', 6, 2.87, 1.02, 0.99,  80, 24, 71, 'gn',  9, true,  'Director de Infraestructura. Lleva la renovación del backbone, NAC y capacidad de servidores.',              '[18,22,28,30,32,38]'::jsonb),
('GOV-03','Elena Marín',         'DIRECTOR_SEC',   'IT-SEGURIDAD', 'rd', 5, 1.92, 1.05, 1.00,  85, 28, 69, 'gn',  7, true,  'Directora de Seguridad. Lleva el SOC unificado SIEM/SOAR y el cumplimiento DORA.',                          '[14,17,21,24,28,30]'::jsonb),
('GOV-04','Marta Núñez',         'TEAM_LEAD',      'IT-INFRA',     'or', 4, 1.54, 0.91, 0.94,  90, 38, 82, 'or',  8, false, 'Team Lead Infra Core. Coordina el equipo que ejecuta los proyectos de Javier Iglesias.',                     '[16,20,22,26,28,32]'::jsonb),
('GOV-05','Raúl Santos',         'VP_OPERATIONS',  'CROSS',        'pu', 7, 3.48, 0.97, 0.96,  75, 35, 65, 'or', 32, false, 'VP Operations. Cubre IT-INFRA + IT-RED + IT-CLOUD + IT-VIRTUAL + IT-STORAGE.',                              '[20,18,22,25,27,28]'::jsonb),
('GOV-06','Andrés Vela',         'PM_BUILD',       'IT-DATA',      'bl', 5, 2.14, 0.88, 0.92, 100, 48, 75, 'or',  4, false, 'PM Build de la rama IT-DATA. Microsoft Fabric, lakehouse y nuevo modelo semántico.',                          '[10,14,18,20,22,24]'::jsonb),
('GOV-07','Lorena Castillo',     'PMO_JUNIOR',     'IT-RED',       'gn', 3, 0.92, 1.03, 1.01,  65, 18, 88, 'gn',  3, false, 'PMO Junior IT-RED. Apoya a Javier en proyectos menores y campañas de auditoría.',                            '[8,12,16,20,24,28]'::jsonb),
('GOV-08','Sergio Mateos',       'PM_BUILD',       'IT-CLOUD',     'rd', 4, 1.74, 0.65, 0.86, 110, 74, 62, 'rd',  5, false, 'PM Build IT-CLOUD. OpenShift on-premise. Sobrecoste 53%, retraso 3 semanas.',                                 '[22,18,15,12,10,8]'::jsonb),
('GOV-09','Nuria Beltrán',       'PM_BUILD',       'IT-VIRTUAL',   'bl', 3, 1.21, 0.99, 1.00,  70, 22, 60, 'gn',  4, false, 'PM Build IT-VIRTUAL. Migración Broadcom vSphere y proyecto Proxmox piloto.',                                 '[16,18,20,22,24,26]'::jsonb),
('GOV-10','Diego Soler',         'TEAM_LEAD',      'IT-SEGURIDAD', 'or', 3, 1.12, 0.93, 0.95,  90, 36, 70, 'or',  5, false, 'Team Lead SecOps. Operación del SOC y respuesta ante incidentes.',                                          '[14,16,18,20,22,24]'::jsonb),
('GOV-11','Inés Carmona',        'PM_BUILD',       'IT-STORAGE',   'gn', 3, 1.05, 1.04, 1.02,  75, 20, 64, 'gn',  3, false, 'PM Build IT-STORAGE. Renovación cabinas NetApp y backup Rubrik.',                                            '[12,14,18,21,25,28]'::jsonb),
('GOV-12','Tomás Aranda',        'PMO_JUNIOR',     'IT-DATA',      'or', 2, 0.65, 0.94, 0.97,  60, 30, 80, 'or',  2, false, 'PMO Junior IT-DATA. Apoyo en proyectos de gobierno del dato y catálogo.',                                    '[8,10,13,16,18,20]'::jsonb),
('GOV-13','Beatriz Lago',        'PM_BUILD',       'IT-INFRA',     'gn', 4, 1.51, 1.06, 1.03,  85, 22, 73, 'gn',  6, false, 'PM Build IT-INFRA. Capacity & DCIM, refresco de servidores HPE.',                                            '[14,18,22,24,26,30]'::jsonb),
('GOV-14','Rubén Ortiz',         'TEAM_LEAD',      'IT-RED',       'pu', 3, 1.02, 0.99, 0.98,  80, 26, 67, 'gn',  6, false, 'Team Lead Red Backbone. Operación L2/L3 y monitorización SDN.',                                              '[16,17,19,22,24,25]'::jsonb),
('GOV-15','Carmen Delgado',      'CTO',            'CROSS',        'pu',12, 8.40, 0.93, 0.95, 100, 55, 74, 'rd', 75, true,  'CTO. Acceso económico completo. Lleva los 12 proyectos estratégicos del banco. Capacidad saturada.',          '[24,22,20,22,21,19]'::jsonb)
ON CONFLICT (id_gov) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────
-- 2) p96_run_layers  ← bgRunLayers (l.2324, 8 filas)
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_run_layers (k, label, sub, cls, silo) VALUES
('INFRA','IT-INFRA',     'servidores físicos', 'c-infra','IT-INFRA'),
('RED',  'IT-RED',       'networking L2/L3',   'c-red',  'IT-RED'),
('CLOUD','IT-CLOUD',     'SaaS/IaaS/PaaS',     'c-cloud','IT-CLOUD'),
('VIRT', 'IT-VIRTUAL',   'hypervisors VMs',    'c-virt', 'IT-VIRTUAL'),
('STO',  'IT-STORAGE',   'cabinas backup',     'c-sto',  'IT-STORAGE'),
('SEC',  'IT-SEGURIDAD', 'FW · SOC · IAM',     'c-sec',  'IT-SEGURIDAD'),
('DATA', 'IT-DATA',      'BBDD · DW · lake',   'c-data', 'IT-DATA'),
('APPS', 'IT-APPS',      'aplicaciones banca', 'c-apps', 'IT-APPS')
ON CONFLICT (k) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────
-- 3) p96_run_crits  ← bgRunCrits (l.2334, 4 filas)
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_run_crits (k, label, sub) VALUES
('C1','C1','crítico máx.'),
('C2','C2','alto'),
('C3','C3','medio'),
('C4','C4','bajo')
ON CONFLICT (k) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────
-- 4) p96_run_matrix  ← bgRunMatrix (l.2341, 32 celdas: 8 layers × 4 crits)
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_run_matrix (layer, crit, cis, opex, inc, heat) VALUES
('INFRA','C1', 8,78000,3,62),('INFRA','C2',12,54000,2,45),('INFRA','C3',14,28000,1,22),('INFRA','C4', 6, 9000,0, 8),
('RED',  'C1', 6,52000,2,55),('RED',  'C2', 9,34000,3,48),('RED',  'C3',11,18000,1,20),('RED',  'C4', 4, 5500,0, 6),
('CLOUD','C1', 5,92000,4,85),('CLOUD','C2', 8,61000,3,58),('CLOUD','C3',10,35000,2,30),('CLOUD','C4', 5,12000,1,14),
('VIRT', 'C1', 3,41000,1,40),('VIRT', 'C2', 7,29000,2,38),('VIRT', 'C3', 9,15000,0,16),('VIRT', 'C4', 4, 6000,0, 5),
('STO',  'C1', 4,58000,2,52),('STO',  'C2', 6,38000,1,32),('STO',  'C3', 8,19000,1,18),('STO',  'C4', 3, 7500,0, 7),
('SEC',  'C1', 7,64000,3,72),('SEC',  'C2', 5,32000,2,42),('SEC',  'C3', 6,17000,1,19),('SEC',  'C4', 2, 4500,0, 5),
('DATA', 'C1', 4,88000,3,78),('DATA', 'C2', 6,48000,2,44),('DATA', 'C3', 7,21000,1,22),('DATA', 'C4', 3, 6800,0, 8),
('APPS', 'C1', 5,72000,4,80),('APPS', 'C2', 8,42000,3,50),('APPS', 'C3', 9,22000,2,26),('APPS', 'C4', 4, 8500,1,12)
ON CONFLICT (layer, crit) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────
-- 5) p96_pulse_kpis  ← bgPulseKPIs (l.2920, 6 filas)
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_pulse_kpis (k, lb, vl, un, rag, sub, tt) VALUES
('cart','Cartera BUILD',   '0.93',  'CPI',     'am','60 proys · 15.77 M€ BAC',         'CPI medio ponderado por BAC. Umbral verde ≥0.95, ámbar 0.85–0.95, rojo <0.85. Refleja la eficiencia global de la cartera de inversión.'),
('run', 'Estabilidad RUN', '99.82', '%',       'gn','MTTR 4h12m · 47 inc abiertas',    'Uptime ponderado del CMDB (226 CIs). Por encima del SLA 99.8% comprometido al comité. Vigilar zona caliente CLOUD×C1.'),
('gov', 'Gobernanza',      '11/15', 'verdes',  'am','3 ámbar · 1 rojo',                'Gobernadores con CPI≥0.95 y riesgo<3. Sergio Mateos (IT-CLOUD) en rojo por sobrecarga y CPI 0.65.'),
('cmp', 'Compliance',      '94',    '/100',    'gn','RGPD · DORA · PCI',                'Score compuesto legal/regulatorio. Auditoría DORA programada 2026-05-04. Hallazgos menores resueltos.'),
('ia',  'Adopción IA',     '68',    '%',       'gn','meta 2026 = 60%',                  'Porcentaje de proyectos BUILD con componente IA productivo o en gate G3+. Supera meta anual.'),
('eq',  'Equipo',          '88',    '/100',    'am','4 saturados · eNPS 42',            'Score compuesto capacidad+rotación+eNPS. 4 gobernadores por encima del 100% de capacidad: riesgo de burnout.')
ON CONFLICT (k) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────
-- 6) p96_pulse_alerts  ← bgPulseAlerts (l.2929, 5 filas, meta JSONB)
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_pulse_alerts (id, sev, title, descripcion, meta, ow) VALUES
('ALT-001','rd','Sergio Mateos (IT-CLOUD) saturado al 110%',
 'Gestiona 6 proyectos con CPI 0.65 y SPI 0.70. Riesgo alto de burnout y de deslizamiento de PRJ-AZR y PRJ-AWS. Requiere redistribución inmediata o refuerzo externo.',
 '["GOV-08","PRJ-AZR","PRJ-AWS","CPI 0.65"]'::jsonb,
 'Ana Torres (COO)'),
('ALT-002','rd','Zona caliente CLOUD×C1 en mapa RUN',
 '14 incidencias abiertas en CIs críticos de capa CLOUD en los últimos 30 días. 2 con impacto en core banking T24. MTTR ha subido a 5h48m vs objetivo 4h.',
 '["CLOUD×C1","14 inc","MTTR 5h48"]'::jsonb,
 'Sergio Mateos (IT-CLOUD)'),
('ALT-003','am','5 proyectos en gate G4 sin fecha de cierre',
 'PRJ-NAC, PRJ-WAF, PRJ-DLP, PRJ-MDM y PRJ-CRM llevan +90 días en G4. Riesgo de quedar atrapados antes del cierre fiscal 2026.',
 '["G4","5 proys","+90 días"]'::jsonb,
 'Carmen Delgado (CTO)'),
('ALT-004','am','Presupuesto IT-SEGURIDAD agotado al 87% (Q1)',
 'Con 3 trimestres por delante ya se ha consumido el 87% del BAC. PRJ-ZTN y PRJ-PAM requerirán ampliación presupuestaria en el próximo comité.',
 '["IT-SEG","87% BAC","Q1"]'::jsonb,
 'Luis Navarro (CFO)'),
('ALT-005','gn','PRJ-SOC listo para cerrar en gate G5',
 'Primer proyecto del año en cerrar G5 con CPI 1.04 y SPI 1.02. Comité puede aprobar cierre y liberar el capital para reasignación en próxima cartera.',
 '["PRJ-SOC","G5","CPI 1.04"]'::jsonb,
 'Elena Ruiz (PMO)')
ON CONFLICT (id) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────
-- 7) p96_pulse_blocks  ← bgPulseBlocks (l.2937, 5 filas)
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_pulse_blocks (id, sev, title, descripcion, pj, own, days) VALUES
('BLK-001','rd','Licencias Azure bloqueadas por legal',     'Cláusula DPA no aprobada por asesoría jurídica. PRJ-AZR parado en gate G2.',                          'PRJ-AZR','Legal',   18),
('BLK-002','rd','Certificado raíz CA interno caducado',     'Bloquea despliegue de PRJ-ZTN y afecta 12 CIs en capa SEC.',                                          'PRJ-ZTN','IT-SEG',  12),
('BLK-003','am','Vendor Dell no confirma entrega storage',  'PRJ-DEL esperando 3 bandejas. Slack en proveedor, impacto en G3.',                                    'PRJ-DEL','Compras',  9),
('BLK-004','am','PRJ-T24 esperando firma de Consejo',       'Aprobación del Consejo de Administración para upgrade core pendiente desde 03-Abr.',                  'PRJ-T24','Consejo',  7),
('BLK-005','am','Entrevistas PMO IT-CLOUD sin candidatos',  'Refuerzo para Sergio Mateos: 0/3 finalistas pasaron última ronda.',                                   'GOV-08', 'RRHH',     6)
ON CONFLICT (id) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────
-- 8) p96_pulse_decisions  ← bgPulseDecs (l.2945, 5 filas)
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_pulse_decisions (id, title, descripcion, own, amt, due, urg) VALUES
('DEC-001','Aprobar ampliación presupuestaria IT-SEGURIDAD +380 k€',
 'Para cubrir PRJ-ZTN y PRJ-PAM hasta cierre fiscal 2026. Sin ampliación ambos proyectos paran en G3.',
 'CFO · CEO', '+380 k€', '2026-04-14', 'near'),
('DEC-002','Validar cierre PRJ-SOC en gate G5',
 'CPI 1.04, SPI 1.02, todos los KPIs en verde. Comité debe firmar cierre formal y liberar 420 k€ de contingencia.',
 'CEO · PMO', 'cierre', '2026-04-14', 'near'),
('DEC-003','Decisión go/no-go PRJ-ZTN (Zero Trust)',
 'Reevaluar viabilidad tras bloqueo de cert CA. 2 alternativas sobre la mesa: Cisco Duo vs Zscaler. Riesgo compliance DORA si no se decide.',
 'CIO · CISO', '1.2 M€', '2026-04-21', 'over'),
('DEC-004','Reprioritizar PRJ-ISE vs PRJ-WAF',
 'Ambos compiten por equipo y presupuesto Q2. PMO propone priorizar WAF por exposición a fraude online reciente.',
 'CIO · CTO', '640 k€', '2026-04-28', ''),
('DEC-005','Fichaje PMO refuerzo IT-CLOUD',
 'Aprobar incorporación externa (perfil senior PMO Cloud) mientras RRHH no encuentra candidato interno.',
 'COO · CFO', '85 k€/año', '2026-05-05', '')
ON CONFLICT (id) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────
-- 9) p96_pulse_responsables  ← bgPulseResps (l.2953, 6 filas)
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_pulse_responsables (nm, rl, ct, ini, kpi_vl, kpi_lb, lg) VALUES
('Ana Torres',     'COO',  'Operaciones · RUN + Gobernanza',     'AT', '99.82%', 'uptime',     'gn'),
('Carmen Delgado', 'CTO',  'Tecnología · Arquitectura BUILD',    'CD', '0.93',   'CPI',        'am'),
('Luis Navarro',   'CFO',  'Finanzas · Presupuesto + RBAC',      'LN', '87%',    'BAC cons',   'am'),
('Elena Ruiz',     'PMO',  'Oficina proyectos · 60 BUILD',       'ER', '11/15',  'gov verdes', 'am'),
('Javier Soto',    'CISO', 'Seguridad · Compliance',             'JS', '94',     'cmp',        'gn'),
('Marta Lorca',    'CDO',  'Datos · Gobierno del dato + IA',     'ML', '68%',    'IA',         'gn');

-- ─────────────────────────────────────────────────────────────────────
-- 10) p96_pulse_hitos  ← bgPulseHitos (l.2962, 8 filas)
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_pulse_hitos (dt, wk, title, descripcion, tg, tgt) VALUES
('14-Abr','SEM 16','Comité Dirección semanal',         'Aprobar DEC-001, DEC-002 y revisar alertas ALT-001/002', 'cmt','COMITÉ'),
('15-Abr','SEM 16','Gate G5 PRJ-SOC',                  'Cierre formal del SOC managed · 420 k€ liberados',       'g5', 'GATE G5'),
('21-Abr','SEM 17','Legacy Kanban borrado definitivo', 'Scope #kg-root sustituye al legacy en producción',        'aud','RELEASE'),
('28-Abr','SEM 18','Revisión cartera Q2 · Comité',     'Reprioritizar PRJ-ISE vs PRJ-WAF y aprobar DEC-004',     'cmt','COMITÉ'),
('04-May','SEM 19','Auditoría DORA kick-off',          'Arranque auditoría externa compliance DORA 2026',         'aud','AUDITORÍA'),
('05-May','SEM 19','DEC-005 fichaje PMO IT-CLOUD',     'Deadline decisión refuerzo Sergio Mateos',                'cmt','DECISIÓN'),
('12-May','SEM 20','Presentación presupuesto 2027',    'CFO presenta al Consejo el budget IT 2027',               'bgt','PRESUPUESTO'),
('19-May','SEM 21','Gate G2 PRJ-AZR (condicional)',    'Sujeto a desbloqueo legal de licencias Azure',            'g5', 'GATE G2');

-- ─────────────────────────────────────────────────────────────────────
-- 11) p96_strategy_frameworks  ← bgStratData (l.3226, 4 marcos)
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_strategy_frameworks (k, payload) VALUES
('dafo', '{
  "eyebrow":"HERRAMIENTA · DAFO",
  "title":"Análisis DAFO de Cognitive PMO",
  "sub":"Diagnóstico interno (D/F) + externo (A/O) aplicado al banco",
  "tag":"2×2",
  "tagCol":"var(--acc-bl)",
  "intro":"El DAFO sintetiza en cuatro cuadrantes la posición competitiva de Cognitive PMO. Las dos columnas internas (Fortalezas y Debilidades) describen capacidades propias del programa; las dos externas (Oportunidades y Amenazas) describen el entorno bancario y regulatorio.",
  "f":["Plataforma multi-agente IA (15 agentes) ya en producción","Gobernanza unificada RUN+BUILD en una sola UI","Trazabilidad RBAC económica con 23 roles y 175 usuarios","TFM MUDEP como aval académico del modelo"],
  "d":["Equipo gobernanza saturado (Sergio Mateos al 110%)","Dependencia de un único hosting NAS para producción","Documentación de operación incompleta para 5 agentes","CPI medio cartera 0.93 — eficiencia mejorable"],
  "o":["Regulación DORA exige observabilidad: encaja con el RUN","60% bancos europeos sin cuadro mando IT integrado","Adopción IA generativa para automatizar gates PMI","Consolidar como producto interno reusable en grupo"],
  "a":["Vendors hyperscaler con suites equivalentes (ServiceNow)","Endurecimiento RGPD/AI Act sobre datos económicos","Burnout del equipo gobernanza si no se refuerza","Recortes presupuestarios IT 2027 si baja BNP de la entidad"]
}'::jsonb),
('pestle','{
  "eyebrow":"HERRAMIENTA · PESTLE",
  "title":"Análisis PESTLE del entorno",
  "sub":"Macro-factores que condicionan al sector financiero IT en 2026",
  "tag":"MACRO",
  "tagCol":"var(--acc-cy)",
  "intro":"PESTLE descompone el entorno macro en seis dimensiones independientes para detectar riesgos y oportunidades estratégicas que escapan al control interno del programa.",
  "items":[
    {"k":"P","nm":"Político",   "ds":"Inestabilidad geopolítica europea, presión por soberanía digital y banca pública. Posibles sanciones contra hyperscalers no-UE.","lv":"med","ic":"pu"},
    {"k":"E","nm":"Económico",  "ds":"Tipos de interés en lateral, márgenes bancarios bajo presión, recortes de OPEX IT del 5% en grupo Q3 2026.","lv":"alta","ic":"cy"},
    {"k":"S","nm":"Social",     "ds":"Cliente bancario exige IA conversacional, transparencia algorítmica y contacto humano híbrido. Talento IT escaso (eNPS 42).","lv":"med","ic":"pk"},
    {"k":"T","nm":"Tecnológico","ds":"Aceleración IA generativa, FinOps y observabilidad como capacidades core. Cierre del gap multi-cloud cada 6 meses.","lv":"alta","ic":"cy"},
    {"k":"L","nm":"Legal",      "ds":"DORA, AI Act, RGPD reforzado y NIS2 obligan a trazabilidad económica de cada decisión IT. Auditoría DORA 2026-05-04.","lv":"alta","ic":"pu"},
    {"k":"E","nm":"Entorno",    "ds":"Compromiso net-zero del banco arrastra a IT: medir kgCO₂ por servicio CMDB y reportar al regulador anualmente.","lv":"med","ic":"pk"}
  ]
}'::jsonb),
('porter','{
  "eyebrow":"HERRAMIENTA · 5 FUERZAS DE PORTER",
  "title":"5 Fuerzas de Porter — banca digital",
  "sub":"Intensidad competitiva del sector donde opera el banco",
  "tag":"5F",
  "tagCol":"var(--acc-pu)",
  "intro":"Las 5 fuerzas miden la atractividad estructural del sector. Cuanto mayor la intensidad de cada fuerza, menor el margen sostenible. Cognitive PMO actúa como respuesta interna a varias de estas presiones.",
  "items":[
    {"k":"F1","nm":"Amenaza de nuevos entrantes",     "ds":"Neobancos UE (N26, Revolut, Bunq) y fintechs con licencia EMI/PI. Barreras de entrada bajas en pagos pero altas en crédito regulado.","lv":"alta","ic":"pu"},
    {"k":"F2","nm":"Amenaza de productos sustitutos", "ds":"Wallets Big Tech (Apple Pay, Google Pay), DeFi y stablecoins reguladas tras MiCA. Sustituyen ingresos de comisiones core.","lv":"alta","ic":"pu"},
    {"k":"F3","nm":"Poder de los clientes",           "ds":"Comparadores online y portabilidad inmediata bajan switching costs. Clientes corporativos exigen APIs abiertas y SLA estrictos.","lv":"med","ic":"pu"},
    {"k":"F4","nm":"Poder de los proveedores",        "ds":"Concentración en 3 hyperscalers (AWS/Azure/GCP), Temenos T24 como core único, vendor lock-in en seguridad. Riesgo bloqueo PRJ-AZR demuestra esta fuerza.","lv":"alta","ic":"pu"},
    {"k":"F5","nm":"Rivalidad competitiva",           "ds":"Bancos tradicionales españoles (Santander, BBVA, CaixaBank) compitiendo en IA, sostenibilidad y experiencia digital. Margen NIM bajo presión.","lv":"alta","ic":"pu"}
  ]
}'::jsonb),
('okr','{
  "eyebrow":"HERRAMIENTA · OKR",
  "title":"OKRs Cognitive PMO — Q2 2026",
  "sub":"3 objetivos trimestrales · 9 key results medibles",
  "tag":"Q2",
  "tagCol":"var(--acc-pk)",
  "intro":"Los OKRs traducen la estrategia anual en compromisos trimestrales medibles. Los Objetivos describen el qué inspirador y los Key Results el cómo medirlo. Cadencia: anual estratégica + trimestral táctica.",
  "objs":[
    {"n":"O1","t":"Convertir Cognitive PMO en la fuente única de verdad económica IT del banco","krs":[
      {"t":"KR1.1 — Migrar el 100% de los 60 proyectos BUILD al módulo P96 antes del 30-jun","p":78},
      {"t":"KR1.2 — Reducir el gap entre cifras CFO y PMO de 12% a <3% (mensual)","p":55},
      {"t":"KR1.3 — Conseguir adopción del CEO Dashboard por los 6 C-level (uso semanal)","p":66}
    ]},
    {"n":"O2","t":"Estabilizar la operación RUN bajo objetivos DORA","krs":[
      {"t":"KR2.1 — Mantener uptime ≥99.85% en CIs C1 (core banking)","p":88},
      {"t":"KR2.2 — Reducir MTTR de 4h12 a <3h en zonas calientes (CLOUD×C1)","p":42},
      {"t":"KR2.3 — Pasar la auditoría DORA 2026-05-04 sin hallazgos críticos","p":70}
    ]},
    {"n":"O3","t":"Hacer de la IA gobernanza una ventaja sostenible","krs":[
      {"t":"KR3.1 — Llevar adopción IA en cartera de 68% a 80% antes del cierre Q2","p":60},
      {"t":"KR3.2 — Lanzar 3 agentes IA nuevos (FinOps, Compliance, Wellbeing) en producción","p":33},
      {"t":"KR3.3 — Publicar 2 papers MUDEP/Anthropic sobre el modelo multi-agente","p":50}
    ]}
  ]
}'::jsonb)
ON CONFLICT (k) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────
-- 12) p96_build_project_detail  ← bgProjectsData (l.1945, 5 filas ricas)
--     gates + team + risks como JSONB
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO p96_build_project_detail (id_proyecto, gates, team, risks) VALUES
('PRJ-MSF',
 '{"G0":"done","G1":"done","G2":"now","G3":"todo","G4":"todo","G5":"todo"}'::jsonb,
 '[{"n":"Sandra Ortega","r":"TECH_SENIOR","cap":"80%"},{"n":"Daniel Pérez","r":"TECH_SENIOR","cap":"60%"},{"n":"Lucía Ferrer","r":"TECH_JUNIOR","cap":"100%"},{"n":"Adriana Suárez","r":"TECH_JUNIOR","cap":"40%"}]'::jsonb,
 '[{"lv":"hi","t":"Dependencia con licencia Power BI Premium F64 (vencimiento Q3)"},{"lv":"hi","t":"Migración Synapse → Fabric requiere ventana fin de semana"},{"lv":"lo","t":"Formación equipo aún en progreso (4 de 6 certificados)"}]'::jsonb),
('PRJ-BBN',
 '{"G0":"done","G1":"done","G2":"done","G3":"now","G4":"todo","G5":"todo"}'::jsonb,
 '[{"n":"Marta Núñez","r":"TEAM_LEAD","cap":"50%"},{"n":"Carlos Vega","r":"TECH_SENIOR","cap":"90%"},{"n":"Iván Rojo","r":"TECH_SENIOR","cap":"70%"}]'::jsonb,
 '[{"lv":"lo","t":"Cisco confirma stock de chassis 9500 — sin retraso logístico"}]'::jsonb),
('PRJ-OSP',
 '{"G0":"done","G1":"done","G2":"now","G3":"todo","G4":"todo","G5":"todo"}'::jsonb,
 '[{"n":"Sandra Ortega","r":"TECH_SENIOR","cap":"40%"},{"n":"Hugo Ramos","r":"TECH_SENIOR","cap":"80%"}]'::jsonb,
 '[{"lv":"hi","t":"CPI=0.65 — sobrecoste del 53% sobre lo planificado"},{"lv":"hi","t":"SPI=0.86 — retraso de 3 semanas en arranque cluster"}]'::jsonb),
('PRJ-NAC',
 '{"G0":"done","G1":"done","G2":"done","G3":"now","G4":"todo","G5":"todo"}'::jsonb,
 '[{"n":"Marta Núñez","r":"TEAM_LEAD","cap":"30%"},{"n":"Iván Rojo","r":"TECH_SENIOR","cap":"60%"}]'::jsonb,
 '[{"lv":"lo","t":"Despliegue por oleadas oficinas — sin incidencias"}]'::jsonb),
('PRJ-SOC',
 '{"G0":"done","G1":"done","G2":"done","G3":"now","G4":"todo","G5":"todo"}'::jsonb,
 '[{"n":"Diego Soler","r":"TECH_SENIOR","cap":"90%"},{"n":"Nuria Gil","r":"TECH_SENIOR","cap":"80%"}]'::jsonb,
 '[{"lv":"lo","t":"CPI=1.05 SPI=1.00 — proyecto sano, sin desviaciones"}]'::jsonb)
ON CONFLICT (id_proyecto) DO NOTHING;

COMMIT;

-- =====================================================================
-- VERIFICACIÓN
-- =====================================================================
SELECT 'p96_governors'           AS tabla, COUNT(*) FROM p96_governors
UNION ALL SELECT 'p96_run_layers',           COUNT(*) FROM p96_run_layers
UNION ALL SELECT 'p96_run_crits',            COUNT(*) FROM p96_run_crits
UNION ALL SELECT 'p96_run_matrix',           COUNT(*) FROM p96_run_matrix
UNION ALL SELECT 'p96_pulse_kpis',           COUNT(*) FROM p96_pulse_kpis
UNION ALL SELECT 'p96_pulse_alerts',         COUNT(*) FROM p96_pulse_alerts
UNION ALL SELECT 'p96_pulse_blocks',         COUNT(*) FROM p96_pulse_blocks
UNION ALL SELECT 'p96_pulse_decisions',      COUNT(*) FROM p96_pulse_decisions
UNION ALL SELECT 'p96_pulse_responsables',   COUNT(*) FROM p96_pulse_responsables
UNION ALL SELECT 'p96_pulse_hitos',          COUNT(*) FROM p96_pulse_hitos
UNION ALL SELECT 'p96_strategy_frameworks',  COUNT(*) FROM p96_strategy_frameworks
UNION ALL SELECT 'p96_build_project_detail', COUNT(*) FROM p96_build_project_detail;

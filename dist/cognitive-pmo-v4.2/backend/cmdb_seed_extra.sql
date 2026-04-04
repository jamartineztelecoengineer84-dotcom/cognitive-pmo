-- ============================================================
-- CMDB SEED EXTRA: Activos masivos para entidad bancaria
-- ============================================================

-- SERVIDORES VIRTUALES (VMware / ESXi)
INSERT INTO cmdb_activos (codigo,nombre,capa,tipo,subtipo,estado_ciclo,criticidad,entorno,ubicacion,propietario,responsable_tecnico,proveedor,coste_mensual,especificaciones) VALUES
('VM-PRO-001','VM App Contabilidad','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PRODUCCION','CPD Madrid - ESXi Cluster','Finanzas','Laura Sanz Bermejo','VMware',600,'{"vcpu":8,"ram_gb":32,"disco_gb":500,"os":"RHEL 9"}'),
('VM-PRO-002','VM App RRHH','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','MEDIA','PRODUCCION','CPD Madrid - ESXi Cluster','RRHH','Ricardo Soto Mendoza','VMware',400,'{"vcpu":4,"ram_gb":16,"disco_gb":200,"os":"Windows Server 2022"}'),
('VM-PRO-003','VM Print Server','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','BAJA','PRODUCCION','CPD Madrid','Soporte IT','Ricardo Soto Mendoza','VMware',200,'{"vcpu":2,"ram_gb":8,"disco_gb":100,"os":"Windows Server 2022"}'),
('VM-PRO-004','VM Proxy Squid','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Seguridad IT','Diana Sánchez Alonso','VMware',350,'{"vcpu":4,"ram_gb":16,"disco_gb":200,"os":"Ubuntu 22.04"}'),
('VM-PRO-005','VM GitLab Server','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','DevOps','Ana Belén Gutiérrez Palacios','VMware',800,'{"vcpu":16,"ram_gb":64,"disco_gb":2000,"os":"Ubuntu 22.04"}'),
('VM-PRO-006','VM Jenkins CI/CD','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','DevOps','Olga Méndez Ramos','VMware',600,'{"vcpu":8,"ram_gb":32,"disco_gb":500,"os":"Ubuntu 22.04"}'),
('VM-PRO-007','VM SonarQube','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','MEDIA','PRODUCCION','CPD Madrid','QA','Natalia Campos Rivero','VMware',400,'{"vcpu":4,"ram_gb":16,"disco_gb":200,"os":"Ubuntu 22.04"}'),
('VM-PRO-008','VM Nexus Repository','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','DevOps','Ana Belén Gutiérrez Palacios','VMware',500,'{"vcpu":4,"ram_gb":32,"disco_gb":1000,"os":"Ubuntu 22.04"}'),
('VM-PRO-009','VM WSUS Server','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','MEDIA','PRODUCCION','CPD Madrid','Windows','Beatriz Castaño Villar','VMware',300,'{"vcpu":4,"ram_gb":16,"disco_gb":500,"os":"Windows Server 2022"}'),
('VM-PRO-010','VM SCCM Server','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Windows','Beatriz Castaño Villar','VMware',600,'{"vcpu":8,"ram_gb":32,"disco_gb":800,"os":"Windows Server 2022"}'),
('VM-PRO-011','VM Ansible Tower','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','DevOps','Olga Méndez Ramos','VMware',500,'{"vcpu":4,"ram_gb":16,"disco_gb":200,"os":"RHEL 9"}'),
('VM-PRO-012','VM HashiCorp Vault','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Seguridad IT','Diana Sánchez Alonso','VMware',500,'{"vcpu":4,"ram_gb":16,"disco_gb":100,"os":"Ubuntu 22.04"}'),
('VM-PRO-013','VM NTP Server','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Infraestructura','Javier Iglesias Roca','VMware',150,'{"vcpu":2,"ram_gb":4,"disco_gb":50,"os":"Ubuntu 22.04"}'),
('VM-PRO-014','VM Radius Server','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Seguridad IT','Marta Fuentes Escobar','VMware',250,'{"vcpu":2,"ram_gb":8,"disco_gb":100,"os":"Ubuntu 22.04"}'),
('VM-PRO-015','VM Terraform State','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','DevOps','Ana Belén Gutiérrez Palacios','VMware',300,'{"vcpu":2,"ram_gb":8,"disco_gb":200,"os":"Ubuntu 22.04"}'),
('VM-PRE-001','VM App Core PRE','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PREPRODUCCION','CPD Madrid','Backend','Laura Sanz Bermejo','VMware',400,'{"vcpu":8,"ram_gb":32,"disco_gb":500,"os":"RHEL 9"}'),
('VM-PRE-002','VM App Pagos PRE','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PREPRODUCCION','CPD Madrid','Backend','Raquel Sánchez Blanco','VMware',350,'{"vcpu":4,"ram_gb":16,"disco_gb":300,"os":"RHEL 9"}'),
('VM-DEV-001','VM Dev Sandbox 1','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','BAJA','DESARROLLO','CPD Madrid','Backend','Marina Nieto Calvo','VMware',200,'{"vcpu":4,"ram_gb":16,"disco_gb":200,"os":"Ubuntu 22.04"}'),
('VM-DEV-002','VM Dev Sandbox 2','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','BAJA','DESARROLLO','CPD Madrid','Frontend','Sergio Morales Pinto','VMware',200,'{"vcpu":4,"ram_gb":16,"disco_gb":200,"os":"Ubuntu 22.04"}'),
('VM-DEV-003','VM QA Automation','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','MEDIA','DESARROLLO','CPD Madrid','QA','Natalia Campos Rivero','VMware',300,'{"vcpu":8,"ram_gb":32,"disco_gb":500,"os":"Ubuntu 22.04"}')
ON CONFLICT (codigo) DO NOTHING;

-- BASES DE DATOS ADICIONALES
INSERT INTO cmdb_activos (codigo,nombre,capa,tipo,subtipo,estado_ciclo,criticidad,entorno,ubicacion,propietario,responsable_tecnico,proveedor,coste_mensual,especificaciones) VALUES
('DB-PRO-006','MySQL App RRHH','INFRAESTRUCTURA','Base de Datos','MySQL','OPERATIVO','MEDIA','PRODUCCION','CPD Madrid','RRHH','Pedro Flores Suárez','Oracle',200,'{"version":"8.0","replicas":1,"storage_gb":50}'),
('DB-PRO-007','PostgreSQL PMO','INFRAESTRUCTURA','Base de Datos','PostgreSQL','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','PMO','Pedro Flores Suárez','EDB',300,'{"version":"15.6","replicas":1,"storage_gb":20}'),
('DB-PRO-008','SQL Server Contabilidad','INFRAESTRUCTURA','Base de Datos','SQL Server','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Finanzas','Óscar Blanco Heredia','Microsoft',1500,'{"version":"2022","edition":"Enterprise","storage_gb":500}'),
('DB-PRO-009','InfluxDB Métricas','INFRAESTRUCTURA','Base de Datos','InfluxDB','OPERATIVO','MEDIA','PRODUCCION','K8S-PRO-001','DevOps','Ana Belén Gutiérrez Palacios','InfluxData',0,'{"version":"2.7","retention":"90d","series":250000}'),
('DB-PRO-010','MariaDB CMS Intranet','INFRAESTRUCTURA','Base de Datos','MariaDB','OPERATIVO','BAJA','PRODUCCION','CPD Madrid','Comunicación','Ricardo Soto Mendoza','MariaDB',100,'{"version":"11.2","storage_gb":30}'),
('DB-PRE-001','PostgreSQL PRE','INFRAESTRUCTURA','Base de Datos','PostgreSQL','OPERATIVO','MEDIA','PREPRODUCCION','CPD Madrid','Backend','Pedro Flores Suárez','EDB',200,'{"version":"15.6"}'),
('DB-PRE-002','Oracle PRE','INFRAESTRUCTURA','Base de Datos','Oracle','OPERATIVO','ALTA','PREPRODUCCION','CPD Madrid','Data Engineering','Óscar Blanco Heredia','Oracle',3000,'{"version":"19c","edition":"Standard"}')
ON CONFLICT (codigo) DO NOTHING;

-- SWITCHES ADICIONALES
INSERT INTO cmdb_activos (codigo,nombre,capa,tipo,subtipo,estado_ciclo,criticidad,entorno,ubicacion,propietario,responsable_tecnico,proveedor,fabricante,modelo,coste_mensual,especificaciones) VALUES
('NET-SW-004','Switch Acceso Planta 2','RED','Switch','Acceso L2','OPERATIVO','MEDIA','PRODUCCION','Sede Central - P2','Infraestructura','Hugo Morales Delgado','Cisco','Cisco','Catalyst 9300-48P',400,'{"ports":"48x 1GbE PoE+"}'),
('NET-SW-005','Switch Acceso Planta 3','RED','Switch','Acceso L2','OPERATIVO','MEDIA','PRODUCCION','Sede Central - P3','Infraestructura','Hugo Morales Delgado','Cisco','Cisco','Catalyst 9300-48P',400,'{"ports":"48x 1GbE PoE+"}'),
('NET-SW-006','Switch CPD Storage','RED','Switch','Storage FC','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Infraestructura','Isabel Álvarez Calvo','Brocade','Brocade','G720',1200,'{"ports":"64x 32Gb FC"}'),
('NET-SW-007','Switch CPD Storage Redundante','RED','Switch','Storage FC','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Infraestructura','Isabel Álvarez Calvo','Brocade','Brocade','G720',1200,'{"ports":"64x 32Gb FC"}'),
('NET-SW-008','Switch Sucursal Madrid Centro','RED','Switch','Acceso L2','OPERATIVO','MEDIA','PRODUCCION','Sucursal Madrid Centro','Infraestructura','Hugo Morales Delgado','Cisco','Cisco','Catalyst 9200-24P',150,'{"ports":"24x 1GbE PoE"}'),
('NET-SW-009','Switch Sucursal Barcelona','RED','Switch','Acceso L2','OPERATIVO','MEDIA','PRODUCCION','Sucursal Barcelona','Infraestructura','Hugo Morales Delgado','Cisco','Cisco','Catalyst 9200-24P',150,'{"ports":"24x 1GbE PoE"}'),
('NET-SW-010','Switch DR Barcelona Core','RED','Switch','Core L3','OPERATIVO','ALTA','DR','CPD Barcelona','Infraestructura','Isabel Álvarez Calvo','Cisco','Cisco','Nexus 9336C-FX2',2200,'{"ports":"36x 100GbE"}'),
('NET-RT-001','Router WAN Principal','RED','Router','WAN','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Infraestructura','Isabel Álvarez Calvo','Cisco','Cisco','ASR 1001-X',1800,'{"interfaces":"4x 10GbE","bgp_peers":8}'),
('NET-RT-002','Router WAN Backup','RED','Router','WAN','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Infraestructura','Isabel Álvarez Calvo','Cisco','Cisco','ASR 1001-X',1800,'{"interfaces":"4x 10GbE"}'),
('NET-RT-003','Router MPLS Sucursales','RED','Router','MPLS','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Infraestructura','Hugo Morales Delgado','Cisco','Cisco','ISR 4451-X',1200,'{"sucursales":45}'),
('NET-AP-001','WiFi AP Planta 1','RED','Access Point WiFi','WiFi 6E','OPERATIVO','BAJA','PRODUCCION','Sede Central - P1','Infraestructura','Hugo Morales Delgado','Cisco','Cisco','Catalyst 9136',80,'{}'),
('NET-AP-002','WiFi AP Planta 2','RED','Access Point WiFi','WiFi 6E','OPERATIVO','BAJA','PRODUCCION','Sede Central - P2','Infraestructura','Hugo Morales Delgado','Cisco','Cisco','Catalyst 9136',80,'{}'),
('NET-AP-003','WiFi AP Planta 3','RED','Access Point WiFi','WiFi 6E','OPERATIVO','BAJA','PRODUCCION','Sede Central - P3','Infraestructura','Hugo Morales Delgado','Cisco','Cisco','Catalyst 9136',80,'{}'),
('NET-AP-004','WiFi Controller','RED','Access Point WiFi','WLC','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Infraestructura','Hugo Morales Delgado','Cisco','Cisco','Catalyst 9800-40',800,'{"aps_managed":85}'),
('NET-DNS-001','DNS Primario','RED','DNS','Bind','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Infraestructura','Isabel Álvarez Calvo','ISC','ISC','BIND 9',0,'{"zones":120}'),
('NET-DNS-002','DNS Secundario','RED','DNS','Bind','OPERATIVO','ALTA','PRODUCCION','CPD Barcelona','Infraestructura','Isabel Álvarez Calvo','ISC','ISC','BIND 9',0,'{}'),
('NET-PRX-001','Proxy Inverso HAProxy','RED','Proxy Inverso','HAProxy','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Infraestructura','Isabel Álvarez Calvo','HAProxy','HAProxy','HAProxy Enterprise',600,'{"backends":35,"connections":50000}')
ON CONFLICT (codigo) DO NOTHING;

-- APLICACIONES / MICROSERVICIOS ADICIONALES
INSERT INTO cmdb_activos (codigo,nombre,capa,tipo,subtipo,estado_ciclo,criticidad,entorno,ubicacion,propietario,responsable_tecnico,coste_mensual,especificaciones) VALUES
('APP-PRO-011','Servicio de Notificaciones','APLICACION','API / Microservicio','Push/SMS/Email','OPERATIVO','ALTA','PRODUCCION','K8S-PRO-001','Backend','Marina Nieto Calvo',0,'{"pods":3,"canales":["push","sms","email"],"mensajes_dia":150000}'),
('APP-PRO-012','Servicio de Autenticación OAuth2','APLICACION','API / Microservicio','Auth','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Seguridad IT','Diana Sánchez Alonso',0,'{"pods":4,"tokens_dia":500000,"mfa":true}'),
('APP-PRO-013','Servicio de Documentos (DMS)','APLICACION','API / Microservicio','Documentos','OPERATIVO','ALTA','PRODUCCION','K8S-PRO-001','Backend','Raquel Sánchez Blanco',0,'{"pods":2,"docs_almacenados":2500000}'),
('APP-PRO-014','Motor de Reglas AML','APLICACION','API / Microservicio','Anti-Money Laundering','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Compliance','Daniel Prieto Gallardo',0,'{"pods":4,"reglas":850,"alertas_dia":1200}'),
('APP-PRO-015','Servicio de Reporting BI','APLICACION','API / Microservicio','Business Intelligence','OPERATIVO','ALTA','PRODUCCION','K8S-PRO-001','Data Engineering','Óscar Blanco Heredia',0,'{"pods":3,"reports":200,"usuarios":120}'),
('APP-PRO-016','CRM Bancario','APLICACION','Aplicación Web','CRM','OPERATIVO','ALTA','PRODUCCION','K8S-PRO-001','Comercial','Cristina Vega Salinas',2500,'{"pods":4,"clientes":450000}'),
('APP-PRO-017','Portal del Empleado','APLICACION','Aplicación Web','Intranet','OPERATIVO','MEDIA','PRODUCCION','K8S-PRO-001','RRHH','Ricardo Soto Mendoza',0,'{"pods":2,"usuarios":850}'),
('APP-PRO-018','App Firma Digital','APLICACION','API / Microservicio','Firma Electrónica','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Legal','Daniel Prieto Gallardo',1200,'{"pods":2,"firmas_dia":8000}'),
('APP-PRO-019','Pasarela Bizum','APLICACION','API / Microservicio','Pagos Instantáneos','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Backend','Raquel Sánchez Blanco',0,'{"pods":3,"tps":3000}'),
('APP-PRO-020','Motor de Scoring Crédito','APLICACION','API / Microservicio','Credit Scoring','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Data Engineering','Óscar Blanco Heredia',0,'{"pods":4,"modelos":8,"evaluaciones_dia":25000}'),
('APP-PRO-021','Servicio Open Banking PSD2','APLICACION','API / Microservicio','Open Banking','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Backend','Marina Nieto Calvo',0,'{"pods":3,"tpps_conectados":45,"apis":["AIS","PIS","PIIS"]}'),
('APP-PRO-022','Gestor de Colas JMS','APLICACION','Cola de Mensajería','ActiveMQ','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Backend','Laura Sanz Bermejo',0,'{"queues":80,"topics":25}'),
('APP-PRO-023','ETL Pipeline Airflow','APLICACION','Middleware / ESB','Apache Airflow','OPERATIVO','ALTA','PRODUCCION','K8S-PRO-001','Data Engineering','Jorge Díaz Vázquez',0,'{"dags":120,"tasks_day":15000}'),
('APP-PRO-024','Servicio de Geolocalización','APLICACION','API / Microservicio','Geolocation','OPERATIVO','MEDIA','PRODUCCION','K8S-PRO-001','Frontend','Sergio Morales Pinto',0,'{"pods":2,"queries_dia":80000}'),
('APP-PRO-025','Chatbot Atención Cliente','APLICACION','API / Microservicio','AI Chatbot','OPERATIVO','MEDIA','PRODUCCION','K8S-PRO-001','Soporte IT','Ricardo Soto Mendoza',1500,'{"pods":3,"conversaciones_dia":5000,"nlp":"GPT-4"}'),
('APP-SaaS-001','Salesforce Financial Services','APLICACION','Servicio Cloud (SaaS)','CRM Cloud','OPERATIVO','ALTA','PRODUCCION','Cloud','Comercial','Cristina Vega Salinas',8000,'{"usuarios":200,"modulo":"Financial Services Cloud"}'),
('APP-SaaS-002','Workday HCM','APLICACION','Servicio Cloud (SaaS)','RRHH Cloud','OPERATIVO','MEDIA','PRODUCCION','Cloud','RRHH','Ricardo Soto Mendoza',6000,'{"empleados":850}'),
('APP-SaaS-003','DocuSign','APLICACION','Servicio Cloud (SaaS)','Firma Digital','OPERATIVO','ALTA','PRODUCCION','Cloud','Legal','Daniel Prieto Gallardo',2000,'{"sobres_mes":5000}'),
('APP-SaaS-004','Slack Enterprise','APLICACION','Servicio Cloud (SaaS)','Comunicación','OPERATIVO','MEDIA','PRODUCCION','Cloud','IT','Ricardo Soto Mendoza',3200,'{"usuarios":850,"canales":400}'),
('APP-SaaS-005','Zoom Enterprise','APLICACION','Servicio Cloud (SaaS)','Videoconferencia','OPERATIVO','MEDIA','PRODUCCION','Cloud','IT','Ricardo Soto Mendoza',2400,'{"licencias":200}')
ON CONFLICT (codigo) DO NOTHING;

-- SEGURIDAD ADICIONAL
INSERT INTO cmdb_activos (codigo,nombre,capa,tipo,subtipo,estado_ciclo,criticidad,entorno,ubicacion,propietario,responsable_tecnico,proveedor,coste_mensual,especificaciones) VALUES
('SEC-IDS-001','IDS/IPS Suricata','SEGURIDAD','IDS/IPS','Network IDS','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','SOC','Inés García-Cano Duarte','OISF',0,'{"rules":45000,"interfaces_monitored":8}'),
('SEC-DLP-001','DLP Symantec','SEGURIDAD','IDS/IPS','Data Loss Prevention','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Seguridad IT','Marta Fuentes Escobar','Broadcom',3500,'{"endpoints":850,"policies":120}'),
('SEC-SCAN-001','Qualys Vulnerability Scanner','SEGURIDAD','IDS/IPS','Vulnerability Scanner','OPERATIVO','ALTA','PRODUCCION','Cloud','SOC','Inés García-Cano Duarte','Qualys',2800,'{"ips_scanned":2000,"frequency":"weekly"}'),
('SEC-NAC-001','Cisco ISE NAC','SEGURIDAD','IDS/IPS','Network Access Control','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Seguridad IT','Marta Fuentes Escobar','Cisco',2200,'{"endpoints":1500,"policies":80}'),
('SEC-SOAR-001','Splunk SOAR','SEGURIDAD','IDS/IPS','SOAR','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','SOC','Inés García-Cano Duarte','Splunk',4000,'{"playbooks":45,"automations_month":2000}'),
('SEC-PKI-001','PKI Interna (ADCS)','SEGURIDAD','Certificado SSL/TLS','PKI','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Seguridad IT','Diana Sánchez Alonso','Microsoft',0,'{"ca_root":1,"ca_intermediate":2,"certs_issued":3500}'),
('SEC-HSM-001','HSM Thales Luna','SEGURIDAD','Certificado SSL/TLS','HSM','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Seguridad IT','Diana Sánchez Alonso','Thales',3000,'{"keys_stored":250,"fips":"140-2 Level 3"}'),
('SEC-WAF-002','Cloudflare WAF','SEGURIDAD','WAF','Cloud WAF','OPERATIVO','ALTA','PRODUCCION','Cloud','Seguridad IT','Diana Sánchez Alonso','Cloudflare',1500,'{"domains":15,"rules":200}')
ON CONFLICT (codigo) DO NOTHING;

-- PUESTOS DE TRABAJO / ENDPOINTS
INSERT INTO cmdb_activos (codigo,nombre,capa,tipo,subtipo,estado_ciclo,criticidad,entorno,ubicacion,propietario,responsable_tecnico,coste_mensual,especificaciones) VALUES
('PT-SEDE-001','Puestos Trabajo Sede Central','SOPORTE','Puesto de Trabajo','Desktop Pool','OPERATIVO','MEDIA','PRODUCCION','Sede Central','Soporte IT','Marcos Morales Guerrero',0,'{"cantidad":350,"modelo":"Dell OptiPlex 7090","os":"Windows 11 Enterprise","ram_gb":16}'),
('PT-SUC-001','Puestos Trabajo Sucursales','SOPORTE','Puesto de Trabajo','Thin Client Pool','OPERATIVO','MEDIA','PRODUCCION','Sucursales','Soporte IT','Marcos Morales Guerrero',0,'{"cantidad":400,"modelo":"Dell Wyse 5070","os":"ThinOS","vdi":"Citrix"}'),
('PT-PORT-001','Portátiles Corporativos','SOPORTE','Puesto de Trabajo','Laptop Pool','OPERATIVO','MEDIA','PRODUCCION','Todas sedes','Soporte IT','Felipe Ortiz Cruz',0,'{"cantidad":250,"modelo":"Dell Latitude 5540","os":"Windows 11","bitlocker":true}'),
('PT-VDI-001','VDI Citrix Farm','INFRAESTRUCTURA','Servidor Virtual (VM)','Citrix VDI','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Soporte IT','Beatriz Castaño Villar',4500,'{"sesiones_concurrent":300,"hosts":8,"gpu":"NVIDIA T4"}'),
('IMP-001','Impresoras Red Sede Central','SOPORTE','Impresora/MFP','MFP Pool','OPERATIVO','BAJA','PRODUCCION','Sede Central','Soporte IT','Marcos Morales Guerrero',800,'{"cantidad":25,"modelo":"HP LaserJet Enterprise M635","color":true}'),
('IMP-002','Impresoras Sucursales','SOPORTE','Impresora/MFP','MFP Pool','OPERATIVO','BAJA','PRODUCCION','Sucursales','Soporte IT','Marcos Morales Guerrero',600,'{"cantidad":90,"modelo":"HP LaserJet Pro M428"}'),
('TEL-001','Telefonía IP Sede','SOPORTE','Teléfono IP','IP Phone Pool','OPERATIVO','MEDIA','PRODUCCION','Sede Central','Soporte IT','Tomás Soler Ortega',1200,'{"cantidad":350,"modelo":"Cisco 8845","cucm":"14.0"}'),
('TEL-002','Telefonía IP Sucursales','SOPORTE','Teléfono IP','IP Phone Pool','OPERATIVO','MEDIA','PRODUCCION','Sucursales','Soporte IT','Tomás Soler Ortega',1800,'{"cantidad":450,"modelo":"Cisco 7841"}'),
('TEL-003','Contact Center Cisco','SOPORTE','Teléfono IP','Contact Center','OPERATIVO','ALTA','PRODUCCION','Sede Central','Soporte IT','Ricardo Soto Mendoza',5500,'{"agentes":80,"colas":25,"ivr":true}')
ON CONFLICT (codigo) DO NOTHING;

-- CLOUD RESOURCES
INSERT INTO cmdb_activos (codigo,nombre,capa,tipo,subtipo,estado_ciclo,criticidad,entorno,ubicacion,propietario,responsable_tecnico,proveedor,coste_mensual,especificaciones) VALUES
('AWS-001','AWS Account Principal','INFRAESTRUCTURA','Servicio Cloud (SaaS)','AWS Account','OPERATIVO','CRITICA','PRODUCCION','eu-west-1','DevOps','Ana Belén Gutiérrez Palacios','AWS',15000,'{"services":["EC2","S3","RDS","Lambda","CloudFront","Route53"],"monthly_avg":"€15K"}'),
('AWS-S3-001','S3 Bucket Documentos','INFRAESTRUCTURA','Storage / SAN','S3','OPERATIVO','ALTA','PRODUCCION','eu-west-1','Data Engineering','Óscar Blanco Heredia','AWS',800,'{"size_tb":12,"versioning":true,"encryption":"AES-256"}'),
('AWS-S3-002','S3 Bucket Backups','INFRAESTRUCTURA','Storage / SAN','S3 Glacier','OPERATIVO','ALTA','PRODUCCION','eu-west-1','Infraestructura','Javier Iglesias Roca','AWS',200,'{"size_tb":50,"storage_class":"Glacier Deep Archive"}'),
('AWS-CF-001','CloudFront CDN','RED','CDN','AWS CloudFront','OPERATIVO','ALTA','PRODUCCION','Global','Frontend','Sergio Morales Pinto','AWS',1200,'{"distributions":5,"origins":8,"requests_month":"50M"}'),
('AWS-R53-001','Route53 DNS Público','RED','DNS','AWS Route53','OPERATIVO','CRITICA','PRODUCCION','Global','Infraestructura','Isabel Álvarez Calvo','AWS',50,'{"hosted_zones":8,"records":250}'),
('AWS-LAM-001','Lambda Functions Pack','APLICACION','API / Microservicio','Serverless','OPERATIVO','ALTA','PRODUCCION','eu-west-1','Backend','Marina Nieto Calvo','AWS',600,'{"functions":35,"invocations_month":"2M"}'),
('AZURE-001','Azure AD Premium P2','SEGURIDAD','Servicio Cloud (SaaS)','Identity','OPERATIVO','CRITICA','PRODUCCION','Cloud','Seguridad IT','Beatriz Castaño Villar','Microsoft',4200,'{"usuarios":850,"conditional_access":true,"pim":true}')
ON CONFLICT (codigo) DO NOTHING;

-- MONITORIZACIÓN Y BACKUP ADICIONAL
INSERT INTO cmdb_activos (codigo,nombre,capa,tipo,subtipo,estado_ciclo,criticidad,entorno,ubicacion,propietario,responsable_tecnico,coste_mensual,especificaciones) VALUES
('MON-PRO-003','PagerDuty Alerting','SOPORTE','Sistema Monitorización','Alerting','OPERATIVO','ALTA','PRODUCCION','Cloud','NOC','Alberto Lozano Mejía',800,'{"services":45,"escalation_policies":12,"on_call_schedules":8}'),
('MON-PRO-004','Datadog APM','SOPORTE','Sistema Monitorización','APM','OPERATIVO','ALTA','PRODUCCION','Cloud','DevOps','Olga Méndez Ramos',3500,'{"hosts":80,"custom_metrics":5000,"traces_month":"500M"}'),
('MON-PRO-005','ELK Stack Logs','SOPORTE','Sistema Monitorización','Log Management','OPERATIVO','ALTA','PRODUCCION','K8S-PRO-001','DevOps','Ana Belén Gutiérrez Palacios',0,'{"nodes":3,"ingestion_gb_day":50}'),
('BAK-001','Commvault Backup Orchestrator','INFRAESTRUCTURA','Cabina Backup','Commvault','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Infraestructura','Javier Iglesias Roca',2500,'{"clients":120,"data_protected_tb":180,"jobs_daily":200}'),
('BAK-002','DR Replication Zerto','INFRAESTRUCTURA','Cabina Backup','Zerto','OPERATIVO','CRITICA','DR','CPD Barcelona','Infraestructura','Javier Iglesias Roca',3000,'{"vms_protected":60,"rpo_seconds":15,"journal_tb":10}')
ON CONFLICT (codigo) DO NOTHING;

-- ATMs y NEGOCIO ADICIONAL
INSERT INTO cmdb_activos (codigo,nombre,capa,tipo,subtipo,estado_ciclo,criticidad,entorno,ubicacion,propietario,coste_mensual,especificaciones) VALUES
('ATM-NET-003','Red Cajeros Zona Este','NEGOCIO','ATM / Cajero','Red ATM','OPERATIVO','ALTA','PRODUCCION','Zona Este','Operaciones',1000,'{"cajeros":32,"protocolo":"NDC+"}'),
('ATM-NET-004','Red Cajeros Zona Oeste','NEGOCIO','ATM / Cajero','Red ATM','OPERATIVO','ALTA','PRODUCCION','Zona Oeste','Operaciones',900,'{"cajeros":28}'),
('ATM-NET-005','Cajeros Centros Comerciales','NEGOCIO','ATM / Cajero','Red ATM','OPERATIVO','ALTA','PRODUCCION','Nacional','Operaciones',1100,'{"cajeros":40,"tipo":"lobby"}'),
('TPV-001','Red TPVs Comercios','NEGOCIO','ATM / Cajero','TPV Network','OPERATIVO','ALTA','PRODUCCION','Nacional','Operaciones',2500,'{"terminales":12000,"protocolo":"ISO 8583"}'),
('BANCA-001','Plataforma Banca Empresas','NEGOCIO','Proyecto PMO','Banca Corporativa','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Dirección IT',0,'{"clientes_empresa":8500}'),
('BANCA-002','Plataforma Banca Privada','NEGOCIO','Proyecto PMO','Wealth Management','OPERATIVO','ALTA','PRODUCCION','K8S-PRO-001','Dirección IT',0,'{"clientes_premium":2500,"aum_millones":4500}')
ON CONFLICT (codigo) DO NOTHING;

-- RELACIONES EXTRA
INSERT INTO cmdb_relaciones (id_activo_origen, id_activo_destino, tipo_relacion, descripcion, criticidad)
SELECT o.id_activo, d.id_activo, r.tipo, r.desc_rel, r.crit FROM (VALUES
('APP-PRO-012','K8S-PRO-001','EJECUTA_EN','Auth service en K8s','CRITICA'),
('APP-PRO-011','K8S-PRO-001','EJECUTA_EN','Notificaciones en K8s','ALTA'),
('APP-PRO-014','DB-PRO-001','DEPENDE_DE','AML usa Oracle','CRITICA'),
('APP-PRO-016','K8S-PRO-001','EJECUTA_EN','CRM en K8s','ALTA'),
('APP-PRO-019','APP-PRO-005','DEPENDE_DE','Bizum usa Pasarela Pagos','CRITICA'),
('APP-PRO-020','DB-PRO-003','DEPENDE_DE','Scoring usa MongoDB','ALTA'),
('APP-PRO-021','APP-PRO-004','DEPENDE_DE','Open Banking usa API Gateway','CRITICA'),
('APP-PRO-002','APP-PRO-012','DEPENDE_DE','Banca Online usa Auth','CRITICA'),
('APP-PRO-003','APP-PRO-012','DEPENDE_DE','App Móvil usa Auth','CRITICA'),
('VM-PRO-005','STO-PRO-001','DEPENDE_DE','GitLab usa SAN','ALTA'),
('VM-PRO-012','SRV-PRO-005','DEPENDE_DE','Vault depende de AD','CRITICA'),
('NET-RT-001','NET-SW-001','CONECTA_A','Router WAN a switch core','CRITICA'),
('NET-RT-003','NET-RT-001','DEPENDE_DE','MPLS sobre WAN','CRITICA'),
('NET-AP-004','NET-SW-003','CONECTA_A','WLC a switch acceso','MEDIA'),
('SEC-NAC-001','SRV-PRO-005','DEPENDE_DE','NAC depende de AD','CRITICA'),
('SEC-SOAR-001','SEC-SIEM-001','DEPENDE_DE','SOAR depende de SIEM','ALTA'),
('APP-PRO-015','DB-PRO-003','DEPENDE_DE','BI usa MongoDB','ALTA'),
('APP-PRO-023','DB-PRO-001','DEPENDE_DE','ETL lee Oracle','ALTA'),
('APP-PRO-023','DB-PRO-003','DEPENDE_DE','ETL escribe MongoDB','ALTA'),
('PT-VDI-001','SRV-PRO-005','DEPENDE_DE','VDI usa AD','ALTA'),
('PT-VDI-001','STO-PRO-001','DEPENDE_DE','VDI usa SAN','ALTA'),
('AWS-CF-001','APP-PRO-002','SIRVE_A','CDN sirve a Banca Online','ALTA'),
('BAK-002','DR-SRV-001','RESPALDA_A','Zerto replica a DR','CRITICA'),
('BAK-001','STO-PRO-001','RESPALDA_A','Commvault respalda SAN','ALTA'),
('MON-PRO-004','K8S-PRO-001','MONITORIZA','Datadog monitoriza K8s','ALTA')
) AS r(cod_o, cod_d, tipo, desc_rel, crit)
JOIN cmdb_activos o ON o.codigo = r.cod_o
JOIN cmdb_activos d ON d.codigo = r.cod_d
ON CONFLICT DO NOTHING;

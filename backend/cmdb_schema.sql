-- ============================================================
-- COGNITIVE PMO - CMDB: Configuration Management Database
-- Inventario inteligente de activos IT para entidad bancaria
-- ============================================================

-- ============================================================
-- 1. CATEGORÍAS DE CIs
-- ============================================================
CREATE TABLE IF NOT EXISTS cmdb_categorias (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    capa VARCHAR(30) NOT NULL CHECK (capa IN ('INFRAESTRUCTURA','APLICACION','RED','SEGURIDAD','NEGOCIO','SOPORTE')),
    icono VARCHAR(50) DEFAULT 'server',
    color VARCHAR(7) DEFAULT '#6B7280'
);

-- ============================================================
-- 2. ACTIVOS / CONFIGURATION ITEMS (CIs)
-- ============================================================
CREATE TABLE IF NOT EXISTS cmdb_activos (
    id_activo SERIAL PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(200) NOT NULL,
    id_categoria INTEGER REFERENCES cmdb_categorias(id_categoria),
    capa VARCHAR(30) NOT NULL CHECK (capa IN ('INFRAESTRUCTURA','APLICACION','RED','SEGURIDAD','NEGOCIO','SOPORTE')),
    tipo VARCHAR(80) NOT NULL,
    subtipo VARCHAR(80),
    estado_ciclo VARCHAR(20) DEFAULT 'OPERATIVO' CHECK (estado_ciclo IN ('DISCOVERY','PLANIFICADO','DESPLEGANDO','OPERATIVO','DEGRADADO','MANTENIMIENTO','RETIRADO')),
    criticidad VARCHAR(10) DEFAULT 'MEDIA' CHECK (criticidad IN ('CRITICA','ALTA','MEDIA','BAJA')),
    entorno VARCHAR(20) DEFAULT 'PRODUCCION' CHECK (entorno IN ('PRODUCCION','PREPRODUCCION','DESARROLLO','STAGING','DR','LAB')),
    ubicacion VARCHAR(100),
    propietario VARCHAR(100),
    responsable_tecnico VARCHAR(100),
    proveedor VARCHAR(100),
    fabricante VARCHAR(100),
    modelo VARCHAR(100),
    version VARCHAR(50),
    serial_number VARCHAR(100),
    fecha_adquisicion DATE,
    fecha_fin_soporte DATE,
    fecha_fin_vida DATE,
    coste_adquisicion NUMERIC(12,2) DEFAULT 0,
    coste_mensual NUMERIC(10,2) DEFAULT 0,
    id_proyecto VARCHAR(50),
    notas TEXT,
    tags TEXT[] DEFAULT '{}',
    especificaciones JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 3. RELACIONES / DEPENDENCIAS ENTRE CIs
-- ============================================================
CREATE TABLE IF NOT EXISTS cmdb_relaciones (
    id_relacion SERIAL PRIMARY KEY,
    id_activo_origen INTEGER REFERENCES cmdb_activos(id_activo) ON DELETE CASCADE,
    id_activo_destino INTEGER REFERENCES cmdb_activos(id_activo) ON DELETE CASCADE,
    tipo_relacion VARCHAR(30) NOT NULL CHECK (tipo_relacion IN ('DEPENDE_DE','EJECUTA_EN','CONECTA_A','PROTEGE_A','RESPALDA_A','MONITORIZA','PARTE_DE','SIRVE_A')),
    descripcion VARCHAR(200),
    criticidad VARCHAR(10) DEFAULT 'MEDIA'
);

-- ============================================================
-- 4. VLANs
-- ============================================================
CREATE TABLE IF NOT EXISTS cmdb_vlans (
    id_vlan SERIAL PRIMARY KEY,
    vlan_id INTEGER NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    subred VARCHAR(18) NOT NULL,
    mascara VARCHAR(15) DEFAULT '255.255.255.0',
    gateway VARCHAR(15),
    entorno VARCHAR(20) DEFAULT 'PRODUCCION',
    ubicacion VARCHAR(100),
    estado VARCHAR(15) DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA','RESERVADA','DESACTIVADA')),
    proposito VARCHAR(50),
    total_ips INTEGER DEFAULT 0,
    ips_usadas INTEGER DEFAULT 0
);

-- ============================================================
-- 5. REGISTRO DE IPs
-- ============================================================
CREATE TABLE IF NOT EXISTS cmdb_ips (
    id_ip SERIAL PRIMARY KEY,
    direccion_ip VARCHAR(15) NOT NULL UNIQUE,
    id_vlan INTEGER REFERENCES cmdb_vlans(id_vlan),
    id_activo INTEGER REFERENCES cmdb_activos(id_activo),
    hostname VARCHAR(100),
    tipo VARCHAR(20) DEFAULT 'ESTATICA' CHECK (tipo IN ('ESTATICA','DHCP','RESERVADA','VIRTUAL','VIP')),
    estado VARCHAR(15) DEFAULT 'ASIGNADA' CHECK (estado IN ('LIBRE','ASIGNADA','RESERVADA','CONFLICTO')),
    mac_address VARCHAR(17),
    puerto_switch VARCHAR(30),
    notas VARCHAR(200),
    ultima_vista TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 6. SOFTWARE INVENTORY
-- ============================================================
CREATE TABLE IF NOT EXISTS cmdb_software (
    id_software SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    version VARCHAR(50),
    editor VARCHAR(100),
    tipo_licencia VARCHAR(30) CHECK (tipo_licencia IN ('OPEN_SOURCE','COMERCIAL','SUSCRIPCION','FREEMIUM','CUSTOM','INTERNA')),
    num_licencias INTEGER DEFAULT 0,
    licencias_usadas INTEGER DEFAULT 0,
    coste_anual NUMERIC(10,2) DEFAULT 0,
    fecha_renovacion DATE,
    estado VARCHAR(15) DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO','OBSOLETO','SIN_SOPORTE','EVALUACION','RETIRADO')),
    critico_negocio BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- 7. SOFTWARE instalado en ACTIVOS (N:M)
-- ============================================================
CREATE TABLE IF NOT EXISTS cmdb_activo_software (
    id_activo INTEGER REFERENCES cmdb_activos(id_activo) ON DELETE CASCADE,
    id_software INTEGER REFERENCES cmdb_software(id_software) ON DELETE CASCADE,
    version_instalada VARCHAR(50),
    fecha_instalacion DATE DEFAULT CURRENT_DATE,
    PRIMARY KEY (id_activo, id_software)
);

-- ============================================================
-- 8. HISTORIAL DE CAMBIOS EN CMDB
-- ============================================================
CREATE TABLE IF NOT EXISTS cmdb_cambios (
    id_cambio SERIAL PRIMARY KEY,
    id_activo INTEGER REFERENCES cmdb_activos(id_activo),
    tipo_cambio VARCHAR(30) NOT NULL,
    descripcion TEXT,
    realizado_por VARCHAR(100),
    fecha TIMESTAMP DEFAULT NOW(),
    datos_antes JSONB,
    datos_despues JSONB
);

-- ÍNDICES
CREATE INDEX IF NOT EXISTS idx_cmdb_activos_capa ON cmdb_activos(capa);
CREATE INDEX IF NOT EXISTS idx_cmdb_activos_estado ON cmdb_activos(estado_ciclo);
CREATE INDEX IF NOT EXISTS idx_cmdb_activos_tipo ON cmdb_activos(tipo);
CREATE INDEX IF NOT EXISTS idx_cmdb_activos_proyecto ON cmdb_activos(id_proyecto);
CREATE INDEX IF NOT EXISTS idx_cmdb_activos_criticidad ON cmdb_activos(criticidad);
CREATE INDEX IF NOT EXISTS idx_cmdb_relaciones_origen ON cmdb_relaciones(id_activo_origen);
CREATE INDEX IF NOT EXISTS idx_cmdb_relaciones_destino ON cmdb_relaciones(id_activo_destino);
CREATE INDEX IF NOT EXISTS idx_cmdb_ips_vlan ON cmdb_ips(id_vlan);
CREATE INDEX IF NOT EXISTS idx_cmdb_ips_activo ON cmdb_ips(id_activo);

-- ============================================================
-- DATOS SEED: CATEGORÍAS
-- ============================================================
INSERT INTO cmdb_categorias (nombre, capa, icono, color) VALUES
('Servidor Físico','INFRAESTRUCTURA','server','#3B82F6'),
('Servidor Virtual (VM)','INFRAESTRUCTURA','monitor','#60A5FA'),
('Contenedor/Pod K8s','INFRAESTRUCTURA','box','#06B6D4'),
('Cluster Kubernetes','INFRAESTRUCTURA','layers','#0891B2'),
('Storage / SAN','INFRAESTRUCTURA','hard-drive','#8B5CF6'),
('Balanceador de Carga','INFRAESTRUCTURA','git-merge','#A855F7'),
('Base de Datos','INFRAESTRUCTURA','database','#F59E0B'),
('Switch','RED','git-branch','#10B981'),
('Router','RED','wifi','#059669'),
('Firewall','SEGURIDAD','shield','#EF4444'),
('WAF','SEGURIDAD','shield-alert','#DC2626'),
('IDS/IPS','SEGURIDAD','alert-triangle','#F97316'),
('VPN Gateway','RED','lock','#7C3AED'),
('Access Point WiFi','RED','wifi','#34D399'),
('Aplicación Web','APLICACION','globe','#2563EB'),
('API / Microservicio','APLICACION','code','#3B82F6'),
('Middleware / ESB','APLICACION','layers','#6366F1'),
('Cola de Mensajería','APLICACION','mail','#8B5CF6'),
('Servicio Cloud (SaaS)','APLICACION','cloud','#0EA5E9'),
('CDN','RED','zap','#F472B6'),
('Certificado SSL/TLS','SEGURIDAD','key','#F59E0B'),
('DNS','RED','globe','#10B981'),
('Proxy Inverso','RED','shuffle','#6366F1'),
('Cabina Backup','INFRAESTRUCTURA','archive','#D97706'),
('UPS / SAI','SOPORTE','battery','#EAB308'),
('Sistema Monitorización','SOPORTE','activity','#EC4899'),
('Licencia Software','NEGOCIO','file-text','#9CA3AF'),
('Proyecto PMO','NEGOCIO','briefcase','#2563EB'),
('Puesto de Trabajo','SOPORTE','laptop','#64748B'),
('Impresora/MFP','SOPORTE','printer','#94A3B8'),
('Teléfono IP','SOPORTE','phone','#64748B'),
('ATM / Cajero','NEGOCIO','credit-card','#EF4444')
ON CONFLICT (nombre) DO NOTHING;

-- ============================================================
-- DATOS SEED: VLANs (entidad bancaria típica)
-- ============================================================
INSERT INTO cmdb_vlans (vlan_id, nombre, subred, gateway, entorno, ubicacion, proposito, total_ips) VALUES
(10,  'MGMT-CORE',          '10.0.10.0/24',   '10.0.10.1',   'PRODUCCION',    'CPD Madrid',     'Gestión equipos core',        254),
(20,  'SERVIDORES-PRO',     '10.0.20.0/24',   '10.0.20.1',   'PRODUCCION',    'CPD Madrid',     'Servidores producción',       254),
(21,  'SERVIDORES-PRE',     '10.0.21.0/24',   '10.0.21.1',   'PREPRODUCCION', 'CPD Madrid',     'Servidores preproducción',    254),
(22,  'SERVIDORES-DEV',     '10.0.22.0/24',   '10.0.22.1',   'DESARROLLO',    'CPD Madrid',     'Servidores desarrollo',       254),
(30,  'BBDD-PRO',           '10.0.30.0/24',   '10.0.30.1',   'PRODUCCION',    'CPD Madrid',     'Bases de datos producción',   254),
(31,  'BBDD-PRE',           '10.0.31.0/24',   '10.0.31.1',   'PREPRODUCCION', 'CPD Madrid',     'Bases de datos pre',          254),
(40,  'DMZ-PUBLICA',        '172.16.40.0/24', '172.16.40.1',  'PRODUCCION',    'CPD Madrid',     'DMZ servicios públicos',      254),
(41,  'DMZ-PARTNERS',       '172.16.41.0/24', '172.16.41.1',  'PRODUCCION',    'CPD Madrid',     'DMZ conexiones partners',     254),
(50,  'USUARIOS-SEDE',      '10.0.50.0/23',   '10.0.50.1',   'PRODUCCION',    'Sede Central',   'Puestos de trabajo sede',     510),
(51,  'USUARIOS-SUC',       '10.0.52.0/22',   '10.0.52.1',   'PRODUCCION',    'Sucursales',     'Puestos trabajo sucursales',  1022),
(60,  'WIFI-CORP',          '10.0.60.0/24',   '10.0.60.1',   'PRODUCCION',    'Todas sedes',    'WiFi corporativa',            254),
(61,  'WIFI-GUEST',         '10.0.61.0/24',   '10.0.61.1',   'PRODUCCION',    'Todas sedes',    'WiFi invitados',              254),
(70,  'VOIP',               '10.0.70.0/24',   '10.0.70.1',   'PRODUCCION',    'Todas sedes',    'Telefonía IP',                254),
(80,  'ATM-RED',            '10.0.80.0/24',   '10.0.80.1',   'PRODUCCION',    'Nacional',       'Red de cajeros automáticos',  254),
(90,  'SWIFT-CORE',         '10.0.90.0/28',   '10.0.90.1',   'PRODUCCION',    'CPD Madrid',     'SWIFT Alliance segmento',     14),
(100, 'KUBERNETES-PRO',     '10.1.0.0/16',    '10.1.0.1',    'PRODUCCION',    'CPD Madrid',     'Pod network Kubernetes PRO',  65534),
(101, 'KUBERNETES-PRE',     '10.2.0.0/16',    '10.2.0.1',    'PREPRODUCCION', 'CPD Madrid',     'Pod network Kubernetes PRE',  65534),
(110, 'BACKUP-NET',         '10.0.110.0/24',  '10.0.110.1',  'PRODUCCION',    'CPD Madrid',     'Red de backup dedicada',      254),
(120, 'MONITORING',         '10.0.120.0/24',  '10.0.120.1',  'PRODUCCION',    'CPD Madrid',     'Red de monitorización',       254),
(200, 'DR-SERVIDORES',      '10.10.20.0/24',  '10.10.20.1',  'DR',            'CPD Barcelona',  'DR servidores',               254),
(201, 'DR-BBDD',            '10.10.30.0/24',  '10.10.30.1',  'DR',            'CPD Barcelona',  'DR bases de datos',           254),
(250, 'LAB-SEGURIDAD',      '192.168.250.0/24','192.168.250.1','LAB',          'SOC Madrid',     'Laboratorio ciberseguridad',  254),
(251, 'LAB-DESARROLLO',     '192.168.251.0/24','192.168.251.1','LAB',          'Sede Central',   'Laboratorio desarrollo',      254)
ON CONFLICT (vlan_id) DO NOTHING;

-- ============================================================
-- DATOS SEED: ACTIVOS (infraestructura bancaria completa)
-- ============================================================
INSERT INTO cmdb_activos (codigo, nombre, capa, tipo, subtipo, estado_ciclo, criticidad, entorno, ubicacion, propietario, responsable_tecnico, proveedor, fabricante, modelo, version, coste_mensual, especificaciones) VALUES
-- SERVIDORES FÍSICOS
('SRV-PRO-001','Servidor Core Banking Principal','INFRAESTRUCTURA','Servidor Físico','Rack 2U','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack A01','Dirección IT','Javier Iglesias Roca','Dell Technologies','Dell','PowerEdge R750','iDRAC 9',4500,'{"cpu":"2x Intel Xeon Gold 6348","ram_gb":512,"discos":"8x 1.92TB NVMe SSD","raid":"RAID 10","os":"RHEL 9.2"}'),
('SRV-PRO-002','Servidor Core Banking Secundario','INFRAESTRUCTURA','Servidor Físico','Rack 2U','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack A02','Dirección IT','Javier Iglesias Roca','Dell Technologies','Dell','PowerEdge R750','iDRAC 9',4500,'{"cpu":"2x Intel Xeon Gold 6348","ram_gb":512,"discos":"8x 1.92TB NVMe SSD","raid":"RAID 10","os":"RHEL 9.2"}'),
('SRV-PRO-003','Servidor SWIFT Alliance','INFRAESTRUCTURA','Servidor Físico','Rack 1U','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack S01','Operaciones','Hugo Morales Delgado','SWIFT','HP','ProLiant DL360 Gen10+','iLO 5',3200,'{"cpu":"2x Intel Xeon Silver 4314","ram_gb":256,"discos":"4x 960GB SSD","os":"Windows Server 2022","swift_version":"7.4"}'),
('SRV-PRO-004','Servidor Pasarela de Pagos','INFRAESTRUCTURA','Servidor Físico','Rack 2U','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack A03','Dirección IT','Laura Sanz Bermejo','HP Enterprise','HP','ProLiant DL380 Gen10+','iLO 5',3800,'{"cpu":"2x Intel Xeon Gold 5318Y","ram_gb":384,"discos":"6x 1.92TB SSD","os":"RHEL 9.1"}'),
('SRV-PRO-005','Servidor Active Directory DC1','INFRAESTRUCTURA','Servidor Físico','Rack 1U','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack D01','Seguridad IT','Beatriz Castaño Villar','Dell Technologies','Dell','PowerEdge R650','iDRAC 9',1800,'{"cpu":"Intel Xeon Silver 4314","ram_gb":128,"discos":"2x 480GB SSD","os":"Windows Server 2022","roles":"AD DS, DNS, DHCP"}'),
('SRV-PRO-006','Servidor Active Directory DC2','INFRAESTRUCTURA','Servidor Físico','Rack 1U','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack D02','Seguridad IT','Beatriz Castaño Villar','Dell Technologies','Dell','PowerEdge R650','iDRAC 9',1800,'{"cpu":"Intel Xeon Silver 4314","ram_gb":128,"discos":"2x 480GB SSD","os":"Windows Server 2022","roles":"AD DS, DNS"}'),
('SRV-PRO-007','Servidor Exchange Online Hybrid','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','ALTA','PRODUCCION','CPD Madrid - ESXi Cluster','Soporte IT','Ricardo Soto Mendoza','Microsoft','VMware','ESXi 8.0','Exchange 2019 CU14',2200,'{"vcpu":8,"ram_gb":64,"disco_gb":500,"os":"Windows Server 2022"}'),
('SRV-PRO-008','Servidor File Server','INFRAESTRUCTURA','Servidor Virtual (VM)','VMware','OPERATIVO','MEDIA','PRODUCCION','CPD Madrid - ESXi Cluster','Soporte IT','Ricardo Soto Mendoza','Dell Technologies','VMware','ESXi 8.0','',800,'{"vcpu":4,"ram_gb":32,"disco_gb":8000,"os":"Windows Server 2022","shares":45}'),
-- KUBERNETES
('K8S-PRO-001','Cluster Kubernetes Producción','INFRAESTRUCTURA','Cluster Kubernetes','EKS-like','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','DevOps','Ana Belén Gutiérrez Palacios','Red Hat','Red Hat','OpenShift 4.14','4.14.8',8500,'{"masters":3,"workers":12,"vcpu_total":192,"ram_total_gb":768,"pods_running":340}'),
('K8S-PRE-001','Cluster Kubernetes Preproducción','INFRAESTRUCTURA','Cluster Kubernetes','EKS-like','OPERATIVO','ALTA','PREPRODUCCION','CPD Madrid','DevOps','Olga Méndez Ramos','Red Hat','Red Hat','OpenShift 4.14','4.14.8',3200,'{"masters":3,"workers":6,"vcpu_total":96,"ram_total_gb":384,"pods_running":180}'),
-- BASES DE DATOS
('DB-PRO-001','Oracle Core Banking','INFRAESTRUCTURA','Base de Datos','Oracle RAC','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack DB01','Data Engineering','Óscar Blanco Heredia','Oracle','Oracle','Exadata X9M','19c',12000,'{"nodes":2,"cpu_cores":48,"ram_gb":1536,"storage_tb":50,"edition":"Enterprise","rac":true}'),
('DB-PRO-002','PostgreSQL Operaciones','INFRAESTRUCTURA','Base de Datos','PostgreSQL','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Data Engineering','Pedro Flores Suárez','EDB','PostgreSQL','15.6','15.6',1200,'{"replicas":2,"cpu_cores":16,"ram_gb":128,"storage_tb":5,"streaming_replication":true}'),
('DB-PRO-003','MongoDB Analytics','INFRAESTRUCTURA','Base de Datos','MongoDB','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Data Engineering','Jorge Díaz Vázquez','MongoDB Inc','MongoDB','7.0','Enterprise',2400,'{"shards":3,"replicas_per_shard":3,"ram_gb":192,"storage_tb":20}'),
('DB-PRO-004','Redis Cache Cluster','INFRAESTRUCTURA','Base de Datos','Redis','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','DevOps','Olga Méndez Ramos','Redis Ltd','Redis','7.2','Enterprise',800,'{"nodes":6,"ram_gb":96,"mode":"cluster","persistence":"AOF"}'),
('DB-PRO-005','Elasticsearch Logs','INFRAESTRUCTURA','Base de Datos','Elasticsearch','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','DevOps','Ana Belén Gutiérrez Palacios','Elastic','Elastic','8.12','Platinum',1800,'{"nodes":5,"ram_gb":160,"storage_tb":30,"indices":450}'),
-- STORAGE
('STO-PRO-001','SAN Principal NetApp','INFRAESTRUCTURA','Storage / SAN','NetApp FAS','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack ST01','Infraestructura','Javier Iglesias Roca','NetApp','NetApp','FAS9500','ONTAP 9.13',6500,'{"shelves":8,"raw_tb":500,"usable_tb":350,"protocols":["NFS","CIFS","iSCSI","FC"],"snapshots":true}'),
('STO-PRO-002','Backup Appliance Veeam','INFRAESTRUCTURA','Cabina Backup','Veeam','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Infraestructura','Javier Iglesias Roca','Veeam','HP','StoreOnce 5260','Veeam 12',3200,'{"capacity_tb":200,"dedup_ratio":"15:1","jobs_daily":85,"retention_days":90}'),
-- RED
('NET-FW-001','Firewall Perimetral Norte','SEGURIDAD','Firewall','Next-Gen','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack FW01','Seguridad IT','Marta Fuentes Escobar','Palo Alto','Palo Alto','PA-5260','PAN-OS 11.1',4200,'{"throughput_gbps":30,"sessions":8000000,"rules":1250,"ha":"Active/Passive"}'),
('NET-FW-002','Firewall Perimetral Sur','SEGURIDAD','Firewall','Next-Gen','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack FW02','Seguridad IT','Marta Fuentes Escobar','Palo Alto','Palo Alto','PA-5260','PAN-OS 11.1',4200,'{"throughput_gbps":30,"ha":"Active/Passive","pair":"NET-FW-001"}'),
('NET-FW-003','Firewall Interno','SEGURIDAD','Firewall','Next-Gen','OPERATIVO','ALTA','PRODUCCION','CPD Madrid - Rack FW03','Seguridad IT','Diana Sánchez Alonso','Fortinet','Fortinet','FortiGate 3700F','FortiOS 7.4',2800,'{"throughput_gbps":20,"zones":12}'),
('NET-WAF-001','WAF Aplicaciones Web','SEGURIDAD','WAF','Cloud WAF','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Seguridad IT','Diana Sánchez Alonso','F5','F5','BIG-IP ASM','17.1',3500,'{"virtual_servers":25,"policies":40,"ssl_offload":true}'),
('NET-SW-001','Switch Core Nexus','RED','Switch','Core L3','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack N01','Infraestructura','Isabel Álvarez Calvo','Cisco','Cisco','Nexus 9336C-FX2','NX-OS 10.3',2200,'{"ports":"36x 100GbE","vlans_active":45,"spanning_tree":"RPVST+"}'),
('NET-SW-002','Switch Core Nexus Redundante','RED','Switch','Core L3','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid - Rack N02','Infraestructura','Isabel Álvarez Calvo','Cisco','Cisco','Nexus 9336C-FX2','NX-OS 10.3',2200,'{"ports":"36x 100GbE","vpc_pair":"NET-SW-001"}'),
('NET-SW-003','Switch Acceso Planta 1','RED','Switch','Acceso L2','OPERATIVO','MEDIA','PRODUCCION','Sede Central - P1','Infraestructura','Hugo Morales Delgado','Cisco','Cisco','Catalyst 9300-48P','IOS-XE 17.9',400,'{"ports":"48x 1GbE PoE+","uplink":"2x 10GbE"}'),
('NET-LB-001','Balanceador F5 BIG-IP','INFRAESTRUCTURA','Balanceador de Carga','Hardware','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Infraestructura','Isabel Álvarez Calvo','F5','F5','BIG-IP i5800','TMOS 17.1',3600,'{"throughput_gbps":40,"virtual_servers":60,"ssl_tps":100000,"ha":"Active/Standby"}'),
('NET-VPN-001','VPN Concentrator','RED','VPN Gateway','SSL VPN','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','Seguridad IT','Marta Fuentes Escobar','Cisco','Cisco','ASA 5555-X','ASA 9.18',1200,'{"concurrent_vpn":2000,"protocols":["SSL","IPSec","AnyConnect"]}'),
-- APLICACIONES
('APP-PRO-001','Core Banking System (T24)','APLICACION','Aplicación Web','Core Banking','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Dirección IT','Laura Sanz Bermejo','Temenos','Temenos','T24 Transact','R22',0,'{"pods":12,"users_concurrent":500,"transactions_day":2500000}'),
('APP-PRO-002','Banca Online (Web)','APLICACION','Aplicación Web','Banca Digital','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Frontend Engineering','Sergio Morales Pinto','Interno','Interno','CognitivBank Web','3.8.1',0,'{"pods":8,"users_concurrent":15000,"framework":"React 18","cdn":true}'),
('APP-PRO-003','App Móvil Banking','APLICACION','Aplicación Web','Mobile Banking','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Frontend Engineering','Sergio Morales Pinto','Interno','Interno','CognitivBank Mobile','5.2.0',0,'{"pods":6,"platforms":["iOS","Android"],"downloads":1200000}'),
('APP-PRO-004','API Gateway','APLICACION','API / Microservicio','API Gateway','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Backend Engineering','Marina Nieto Calvo','Kong Inc','Kong','Kong Enterprise','3.5',1500,'{"routes":340,"rate_limiting":true,"oauth2":true,"requests_sec":25000}'),
('APP-PRO-005','Pasarela de Pagos PSD2','APLICACION','API / Microservicio','Pagos','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Backend Engineering','Raquel Sánchez Blanco','Interno','Interno','PayGateway','2.1.0',0,'{"pods":4,"tps":5000,"psd2_compliant":true,"3ds2":true}'),
('APP-PRO-006','Motor de Riesgo','APLICACION','API / Microservicio','Risk Engine','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','Data Engineering','Óscar Blanco Heredia','Interno','Interno','RiskEngine ML','1.8.0',0,'{"pods":6,"models":12,"predictions_day":500000,"ml_framework":"TensorFlow"}'),
('APP-PRO-007','SWIFT Alliance Gateway','APLICACION','Middleware / ESB','Mensajería SWIFT','OPERATIVO','CRITICA','PRODUCCION','SRV-PRO-003','Operaciones','Hugo Morales Delgado','SWIFT','SWIFT','Alliance Gateway','7.4',5500,'{"messages_day":45000,"formats":["MT","MX","ISO20022"]}'),
('APP-PRO-008','Kafka Event Streaming','APLICACION','Cola de Mensajería','Event Streaming','OPERATIVO','CRITICA','PRODUCCION','K8S-PRO-001','DevOps','Ana Belén Gutiérrez Palacios','Confluent','Apache','Kafka','3.6',2400,'{"brokers":5,"topics":120,"partitions":800,"messages_sec":150000,"retention_days":7}'),
('APP-PRO-009','Cognitive PMO Platform','APLICACION','Aplicación Web','PMO','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','PMO','Jose Antonio Martinez Victoria','Interno','Interno','Cognitive PMO','2.0',0,'{"stack":"FastAPI+PostgreSQL+Vanilla JS","agents":7,"flowise":true}'),
('APP-PRO-010','ServiceNow ITSM','APLICACION','Servicio Cloud (SaaS)','ITSM','OPERATIVO','ALTA','PRODUCCION','Cloud','Soporte IT','Ricardo Soto Mendoza','ServiceNow','ServiceNow','Tokyo','Tokyo Q4',8500,'{"tickets_month":4500,"users":200,"modules":["Incident","Change","Problem","CMDB"]}'),
-- SEGURIDAD
('SEC-SIEM-001','SIEM Splunk Enterprise','SEGURIDAD','IDS/IPS','SIEM','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','SOC','Inés García-Cano Duarte','Splunk','Splunk','Enterprise','9.2',7500,'{"ingestion_gb_day":200,"indexes":85,"alerts":320,"retention_days":365}'),
('SEC-AV-001','Antivirus CrowdStrike','SEGURIDAD','IDS/IPS','EDR','OPERATIVO','ALTA','PRODUCCION','Todos','Seguridad IT','Marta Fuentes Escobar','CrowdStrike','CrowdStrike','Falcon','6.x',4200,'{"endpoints":850,"modules":["Prevent","Insight","Discover"]}'),
('SEC-PAM-001','CyberArk PAM','SEGURIDAD','Servicio Cloud (SaaS)','PAM','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Seguridad IT','Diana Sánchez Alonso','CyberArk','CyberArk','Privilege Cloud','13.2',3800,'{"cuentas_privilegiadas":450,"sesiones_grabadas":true,"rotacion_auto":true}'),
-- MONITORIZACIÓN
('MON-PRO-001','Grafana + Prometheus','SOPORTE','Sistema Monitorización','Observabilidad','OPERATIVO','ALTA','PRODUCCION','K8S-PRO-001','DevOps','Ana Belén Gutiérrez Palacios','Grafana Labs','Grafana','Grafana Enterprise','10.3',1200,'{"dashboards":85,"datasources":12,"alerts":250,"metrics_series":500000}'),
('MON-PRO-002','Zabbix Infraestructura','SOPORTE','Sistema Monitorización','Infra Monitoring','OPERATIVO','ALTA','PRODUCCION','CPD Madrid','NOC','Alberto Lozano Mejía','Zabbix','Zabbix','Zabbix','6.4 LTS',0,'{"hosts":620,"items":45000,"triggers":8500,"templates":120}'),
-- DR
('DR-SRV-001','Servidor DR Core Banking','INFRAESTRUCTURA','Servidor Físico','Rack 2U','OPERATIVO','CRITICA','DR','CPD Barcelona - Rack A01','Dirección IT','Javier Iglesias Roca','Dell Technologies','Dell','PowerEdge R750','iDRAC 9',2800,'{"cpu":"2x Xeon Gold 6348","ram_gb":512,"replica_de":"SRV-PRO-001"}'),
('DR-DB-001','Oracle DR Core Banking','INFRAESTRUCTURA','Base de Datos','Oracle Data Guard','OPERATIVO','CRITICA','DR','CPD Barcelona','Data Engineering','Óscar Blanco Heredia','Oracle','Oracle','Exadata X9M','19c',6000,'{"data_guard":"Physical Standby","lag_seconds":5,"replica_de":"DB-PRO-001"}'),
-- ATMs
('ATM-NET-001','Red Cajeros Zona Norte','NEGOCIO','ATM / Cajero','Red ATM','OPERATIVO','ALTA','PRODUCCION','Zona Norte','Operaciones','Patricia López de la Fuente','NCR','NCR','SelfServ 80','','1500','{"cajeros":45,"uptime_sla":"99.5%","protocolo":"NDC+"}'),
('ATM-NET-002','Red Cajeros Zona Sur','NEGOCIO','ATM / Cajero','Red ATM','OPERATIVO','ALTA','PRODUCCION','Zona Sur','Operaciones','Patricia López de la Fuente','Diebold','Diebold Nixdorf','DN Series 200','',1200,'{"cajeros":38,"uptime_sla":"99.5%"}'),
-- CERTIFICADOS
('CERT-001','Certificado SSL *.bank.com','SEGURIDAD','Certificado SSL/TLS','Wildcard','OPERATIVO','CRITICA','PRODUCCION','Todos','Seguridad IT','Diana Sánchez Alonso','DigiCert','DigiCert','OV Wildcard','SHA-256',600,'{"dominio":"*.bank.com","expira":"2027-03-15","san":["bank.com","api.bank.com","app.bank.com"]}'),
('CERT-002','Certificado SSL Banca Online','SEGURIDAD','Certificado SSL/TLS','EV','OPERATIVO','CRITICA','PRODUCCION','DMZ','Seguridad IT','Diana Sánchez Alonso','DigiCert','DigiCert','EV SSL','SHA-256',1200,'{"dominio":"online.bank.com","expira":"2026-11-20","ev":true}'),
-- UPS
('UPS-001','SAI Principal CPD Madrid','SOPORTE','UPS / SAI','Online','OPERATIVO','CRITICA','PRODUCCION','CPD Madrid','Infraestructura','Javier Iglesias Roca','Eaton','Eaton','9PX 200kVA','',350,'{"potencia_kva":200,"autonomia_min":30,"baterias":40}'),
('UPS-002','SAI CPD Barcelona','SOPORTE','UPS / SAI','Online','OPERATIVO','CRITICA','DR','CPD Barcelona','Infraestructura','Javier Iglesias Roca','APC','APC','Symmetra PX 100kVA','',250,'{"potencia_kva":100,"autonomia_min":25}')
ON CONFLICT (codigo) DO NOTHING;

-- ============================================================
-- DATOS SEED: SOFTWARE
-- ============================================================
INSERT INTO cmdb_software (nombre, version, editor, tipo_licencia, num_licencias, licencias_usadas, coste_anual, estado, critico_negocio) VALUES
('Red Hat Enterprise Linux','9.2','Red Hat','SUSCRIPCION',80,62,96000,'ACTIVO',true),
('Windows Server','2022','Microsoft','COMERCIAL',45,38,54000,'ACTIVO',true),
('Oracle Database Enterprise','19c','Oracle','COMERCIAL',4,2,280000,'ACTIVO',true),
('PostgreSQL','15.6','PostgreSQL Global','OPEN_SOURCE',0,0,0,'ACTIVO',true),
('MongoDB Enterprise','7.0','MongoDB Inc','SUSCRIPCION',3,3,36000,'ACTIVO',false),
('Redis Enterprise','7.2','Redis Ltd','SUSCRIPCION',1,1,18000,'ACTIVO',true),
('Elasticsearch Platinum','8.12','Elastic','SUSCRIPCION',1,1,42000,'ACTIVO',false),
('VMware vSphere Enterprise Plus','8.0','Broadcom','COMERCIAL',24,20,72000,'ACTIVO',true),
('Red Hat OpenShift','4.14','Red Hat','SUSCRIPCION',2,2,120000,'ACTIVO',true),
('Microsoft 365 E5','Latest','Microsoft','SUSCRIPCION',850,820,408000,'ACTIVO',false),
('CrowdStrike Falcon','6.x','CrowdStrike','SUSCRIPCION',850,850,180000,'ACTIVO',true),
('Splunk Enterprise','9.2','Splunk','SUSCRIPCION',1,1,90000,'ACTIVO',true),
('CyberArk Privilege Cloud','13.2','CyberArk','SUSCRIPCION',1,1,65000,'ACTIVO',true),
('Veeam Backup & Replication','12','Veeam','SUSCRIPCION',1,1,24000,'ACTIVO',true),
('ServiceNow ITSM','Tokyo','ServiceNow','SUSCRIPCION',200,185,102000,'ACTIVO',false),
('PAN-OS','11.1','Palo Alto Networks','SUSCRIPCION',2,2,48000,'ACTIVO',true),
('FortiOS','7.4','Fortinet','SUSCRIPCION',1,1,18000,'ACTIVO',true),
('Cisco NX-OS','10.3','Cisco','COMERCIAL',4,4,12000,'ACTIVO',true),
('Kong Enterprise','3.5','Kong Inc','SUSCRIPCION',1,1,36000,'ACTIVO',true),
('Apache Kafka (Confluent)','3.6','Confluent','SUSCRIPCION',1,1,28800,'ACTIVO',true),
('Grafana Enterprise','10.3','Grafana Labs','SUSCRIPCION',1,1,14400,'ACTIVO',false),
('Zabbix','6.4','Zabbix','OPEN_SOURCE',0,0,0,'ACTIVO',false),
('Temenos T24 Transact','R22','Temenos','COMERCIAL',1,1,500000,'ACTIVO',true),
('F5 BIG-IP ASM','17.1','F5 Networks','COMERCIAL',2,2,42000,'ACTIVO',true),
('Cisco AnyConnect','5.1','Cisco','SUSCRIPCION',2000,1200,24000,'ACTIVO',false),
('Git / GitLab Enterprise','16.8','GitLab','SUSCRIPCION',150,142,27000,'ACTIVO',false),
('Jira Software','9.x','Atlassian','SUSCRIPCION',150,140,21600,'ACTIVO',false),
('Confluence','8.x','Atlassian','SUSCRIPCION',150,130,12600,'ACTIVO',false),
('Flowise AI','1.8','FlowiseAI','OPEN_SOURCE',0,0,0,'ACTIVO',false),
('SonarQube Enterprise','10.4','SonarSource','SUSCRIPCION',1,1,15000,'ACTIVO',false)
ON CONFLICT DO NOTHING;

-- ============================================================
-- DATOS SEED: RELACIONES / DEPENDENCIAS
-- ============================================================
INSERT INTO cmdb_relaciones (id_activo_origen, id_activo_destino, tipo_relacion, descripcion, criticidad)
SELECT o.id_activo, d.id_activo, r.tipo, r.desc_rel, r.crit FROM (VALUES
('APP-PRO-001','DB-PRO-001','DEPENDE_DE','Core Banking depende de Oracle RAC','CRITICA'),
('APP-PRO-001','K8S-PRO-001','EJECUTA_EN','Core Banking corre en Kubernetes','CRITICA'),
('APP-PRO-002','K8S-PRO-001','EJECUTA_EN','Banca Online en Kubernetes','CRITICA'),
('APP-PRO-002','APP-PRO-004','DEPENDE_DE','Banca Online usa API Gateway','CRITICA'),
('APP-PRO-003','APP-PRO-004','DEPENDE_DE','App Móvil usa API Gateway','CRITICA'),
('APP-PRO-004','K8S-PRO-001','EJECUTA_EN','API Gateway en Kubernetes','CRITICA'),
('APP-PRO-004','NET-LB-001','DEPENDE_DE','API Gateway tras balanceador','ALTA'),
('APP-PRO-005','DB-PRO-002','DEPENDE_DE','Pasarela pagos usa PostgreSQL','CRITICA'),
('APP-PRO-005','APP-PRO-008','DEPENDE_DE','Pasarela pagos publica en Kafka','ALTA'),
('APP-PRO-006','DB-PRO-003','DEPENDE_DE','Motor riesgo usa MongoDB','ALTA'),
('APP-PRO-006','DB-PRO-004','DEPENDE_DE','Motor riesgo usa Redis cache','ALTA'),
('APP-PRO-007','SRV-PRO-003','EJECUTA_EN','SWIFT Gateway en servidor dedicado','CRITICA'),
('APP-PRO-008','K8S-PRO-001','EJECUTA_EN','Kafka en Kubernetes','CRITICA'),
('K8S-PRO-001','STO-PRO-001','DEPENDE_DE','Kubernetes usa SAN para PVs','CRITICA'),
('K8S-PRO-001','NET-SW-001','CONECTA_A','Kubernetes conecta a switch core','ALTA'),
('DB-PRO-001','STO-PRO-001','DEPENDE_DE','Oracle usa SAN NetApp','CRITICA'),
('DB-PRO-001','SRV-PRO-001','EJECUTA_EN','Oracle en servidor Core Banking','CRITICA'),
('NET-FW-001','NET-SW-001','CONECTA_A','Firewall conecta a switch core','CRITICA'),
('NET-WAF-001','NET-FW-001','DEPENDE_DE','WAF tras firewall perimetral','CRITICA'),
('NET-LB-001','NET-FW-003','DEPENDE_DE','Balanceador tras firewall interno','ALTA'),
('SEC-SIEM-001','DB-PRO-005','DEPENDE_DE','SIEM usa Elasticsearch','ALTA'),
('MON-PRO-001','K8S-PRO-001','EJECUTA_EN','Grafana en Kubernetes','MEDIA'),
('MON-PRO-001','K8S-PRO-001','MONITORIZA','Grafana monitoriza Kubernetes','ALTA'),
('MON-PRO-002','SRV-PRO-001','MONITORIZA','Zabbix monitoriza servidores','ALTA'),
('STO-PRO-002','STO-PRO-001','RESPALDA_A','Veeam respalda SAN NetApp','ALTA'),
('DR-SRV-001','SRV-PRO-001','RESPALDA_A','DR replica servidor principal','CRITICA'),
('DR-DB-001','DB-PRO-001','RESPALDA_A','Data Guard replica Oracle','CRITICA'),
('SRV-PRO-005','SRV-PRO-006','RESPALDA_A','DC2 replica DC1','CRITICA'),
('SEC-AV-001','SRV-PRO-001','PROTEGE_A','CrowdStrike protege servidores','ALTA'),
('SEC-PAM-001','SRV-PRO-005','PROTEGE_A','CyberArk gestiona accesos AD','CRITICA')
) AS r(cod_o, cod_d, tipo, desc_rel, crit)
JOIN cmdb_activos o ON o.codigo = r.cod_o
JOIN cmdb_activos d ON d.codigo = r.cod_d
ON CONFLICT DO NOTHING;

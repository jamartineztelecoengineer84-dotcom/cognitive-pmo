-- ============================================================
-- COGNITIVE PMO — Database Initialization
-- ============================================================

CREATE TABLE IF NOT EXISTS pmo_staff_skills (
    id_tecnico VARCHAR PRIMARY KEY,
    nombre VARCHAR NOT NULL,
    silo VARCHAR,
    nivel VARCHAR(2),
    skills_score INT,
    tags TEXT[],
    disponible BOOLEAN DEFAULT true,
    estado VARCHAR DEFAULT 'DISPONIBLE',
    carga_actual INT DEFAULT 0,
    ubicacion VARCHAR DEFAULT 'Madrid'
);

CREATE TABLE IF NOT EXISTS cartera_build (
    id_proyecto VARCHAR PRIMARY KEY,
    nombre TEXT NOT NULL,
    prioridad VARCHAR,
    prioridad_num INT,
    estado VARCHAR,
    horas_estimadas INT,
    skill_requerida VARCHAR,
    fecha_inicio DATE,
    fecha_fin DATE,
    fte_asignado VARCHAR
);

CREATE TABLE IF NOT EXISTS incidencias (
    id_incidencia VARCHAR PRIMARY KEY,
    descripcion TEXT,
    prioridad VARCHAR,
    categoria VARCHAR,
    estado VARCHAR DEFAULT 'QUEUED',
    sla_limite VARCHAR,
    tecnico_asignado VARCHAR,
    fecha_creacion TIMESTAMP DEFAULT NOW(),
    flag_build_vs_run BOOLEAN DEFAULT FALSE,
    impacto_negocio VARCHAR
);

CREATE TABLE IF NOT EXISTS kanban_tareas (
    id VARCHAR PRIMARY KEY,
    tipo VARCHAR,
    prioridad VARCHAR,
    titulo TEXT,
    columna VARCHAR DEFAULT 'Backlog',
    usuario_asignado VARCHAR,
    id_tecnico VARCHAR,
    tiempo_horas INT DEFAULT 0,
    bloqueador TEXT,
    fecha TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- STAFF — Frontend (FTE-001 to FTE-041, 41 total)
-- N2=28, N3=10, N4=3
-- ============================================================
INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-001','Alejandro García Martínez','Frontend','N2',42,ARRAY['HTML/CSS','JS','React'],true,'DISPONIBLE',0,'Madrid'),
('FTE-002','Laura Sánchez López','Frontend','N2',38,ARRAY['HTML/CSS','JS','Vue'],true,'DISPONIBLE',0,'Madrid'),
('FTE-003','Miguel Fernández García','Frontend','N2',45,ARRAY['HTML/CSS','JS','Angular'],true,'DISPONIBLE',0,'Madrid'),
('FTE-004','María González Rodríguez','Frontend','N2',40,ARRAY['HTML/CSS','JS','React'],true,'DISPONIBLE',0,'Madrid'),
('FTE-005','Carlos Rodríguez Martínez','Frontend','N2',35,ARRAY['HTML/CSS','JS'],true,'DISPONIBLE',0,'Madrid'),
('FTE-006','Ana Martínez López','Frontend','N2',48,ARRAY['HTML/CSS','JS','Vue','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-007','José López Fernández','Frontend','N2',41,ARRAY['HTML/CSS','JS','React'],true,'DISPONIBLE',0,'Madrid'),
('FTE-008','Isabel Pérez García','Frontend','N2',37,ARRAY['HTML/CSS','JS','Angular'],true,'DISPONIBLE',0,'Madrid'),
('FTE-009','David González López','Frontend','N2',43,ARRAY['HTML/CSS','JS','Git'],true,'DISPONIBLE',0,'Barcelona'),
('FTE-010','Carmen Martínez Rodríguez','Frontend','N2',39,ARRAY['HTML/CSS','JS','React'],true,'DISPONIBLE',0,'Madrid'),
('FTE-011','Francisco García Fernández','Frontend','N2',36,ARRAY['HTML/CSS','JS'],true,'DISPONIBLE',0,'Madrid'),
('FTE-012','Lucía Rodríguez García','Frontend','N2',44,ARRAY['HTML/CSS','JS','Vue','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-013','Antonio López Martínez','Frontend','N2',46,ARRAY['HTML/CSS','JS','React','TypeScript'],true,'DISPONIBLE',0,'Madrid'),
('FTE-014','Marta Fernández López','Frontend','N2',33,ARRAY['HTML/CSS','JS'],true,'DISPONIBLE',0,'Valencia'),
('FTE-015','Javier González García','Frontend','N2',47,ARRAY['HTML/CSS','JS','Angular','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-016','Rosa Pérez Rodríguez','Frontend','N2',34,ARRAY['HTML/CSS','JS','Vue'],true,'DISPONIBLE',0,'Madrid'),
('FTE-017','Manuel García López','Frontend','N2',42,ARRAY['HTML/CSS','JS','React'],true,'DISPONIBLE',0,'Madrid'),
('FTE-018','Pilar López García','Frontend','N2',38,ARRAY['HTML/CSS','JS'],true,'DISPONIBLE',0,'Madrid'),
('FTE-019','Sergio Martínez Fernández','Frontend','N2',41,ARRAY['HTML/CSS','JS','Vue'],true,'DISPONIBLE',0,'Sevilla'),
('FTE-020','Elena Rodríguez López','Frontend','N2',45,ARRAY['HTML/CSS','JS','React','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-021','Pablo González Martínez','Frontend','N2',36,ARRAY['HTML/CSS','JS'],true,'DISPONIBLE',0,'Madrid'),
('FTE-022','Cristina García Rodríguez','Frontend','N2',43,ARRAY['HTML/CSS','JS','Angular'],true,'DISPONIBLE',0,'Madrid'),
('FTE-023','Raúl Fernández García','Frontend','N2',39,ARRAY['HTML/CSS','JS','Vue'],true,'DISPONIBLE',0,'Madrid'),
('FTE-024','Natalia López Martínez','Frontend','N2',44,ARRAY['HTML/CSS','JS','React','TypeScript'],true,'DISPONIBLE',0,'Madrid'),
('FTE-025','Diego Martínez López','Frontend','N2',37,ARRAY['HTML/CSS','JS'],true,'DISPONIBLE',0,'Bilbao'),
('FTE-026','Silvia Rodríguez Fernández','Frontend','N2',40,ARRAY['HTML/CSS','JS','Vue'],true,'DISPONIBLE',0,'Madrid'),
('FTE-027','Adrián García Martínez','Frontend','N2',46,ARRAY['HTML/CSS','JS','React','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-028','Patricia González López','Frontend','N2',35,ARRAY['HTML/CSS','JS'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-029','Roberto Pérez García','Frontend','N3',62,ARRAY['HTML/CSS','JS','React','TypeScript','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-030','Beatriz Martínez Rodríguez','Frontend','N3',65,ARRAY['HTML/CSS','JS','Vue','Webpack','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-031','Óscar López Fernández','Frontend','N3',68,ARRAY['HTML/CSS','JS','Angular','RxJS','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-032','Verónica García García','Frontend','N3',63,ARRAY['HTML/CSS','JS','React','Redux','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-033','Gonzalo Fernández Martínez','Frontend','N3',70,ARRAY['HTML/CSS','JS','Vue','TypeScript','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-034','Inés Rodríguez López','Frontend','N3',61,ARRAY['HTML/CSS','JS','Angular','Git'],true,'DISPONIBLE',0,'Barcelona'),
('FTE-035','Eduardo Martínez García','Frontend','N3',67,ARRAY['HTML/CSS','JS','React','Next.js','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-036','Lorena González Fernández','Frontend','N3',64,ARRAY['HTML/CSS','JS','Vue','Nuxt.js','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-037','Álvaro López Rodríguez','Frontend','N3',69,ARRAY['HTML/CSS','JS','Angular','TypeScript','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-038','Nuria García Martínez','Frontend','N3',66,ARRAY['HTML/CSS','JS','React','TypeScript','Jest'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-039','Fernando Pérez López','Frontend','N4',85,ARRAY['HTML/CSS','JS','React','TypeScript','Architecture','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-040','Carolina Rodríguez García','Frontend','N4',88,ARRAY['HTML/CSS','JS','Vue','Architecture','Performance','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-041','Héctor Martínez Fernández','Frontend','N4',91,ARRAY['HTML/CSS','JS','Angular','Architecture','TypeScript','Git'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

-- ============================================================
-- STAFF — Redes (FTE-042 to FTE-074, 33 total)
-- N2=20, N3=10, N4=3
-- ============================================================
INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-042','Luis Sánchez Martínez','Redes','N2',40,ARRAY['IP/Gateway','Netstat','VLAN'],true,'DISPONIBLE',0,'Madrid'),
('FTE-043','Teresa García López','Redes','N2',38,ARRAY['IP/Gateway','Port Security','DNS'],true,'DISPONIBLE',0,'Madrid'),
('FTE-044','Andrés Fernández Rodríguez','Redes','N2',42,ARRAY['IP/Gateway','Netstat','WiFi'],true,'DISPONIBLE',0,'Madrid'),
('FTE-045','Rocío López García','Redes','N2',37,ARRAY['IP/Gateway','VLAN Config Switch'],true,'DISPONIBLE',0,'Madrid'),
('FTE-046','Víctor Martínez Fernández','Redes','N2',44,ARRAY['IP/Gateway','DNS','Port Security'],true,'DISPONIBLE',0,'Barcelona'),
('FTE-047','Amparo González Rodríguez','Redes','N2',39,ARRAY['IP/Gateway','Netstat'],true,'DISPONIBLE',0,'Madrid'),
('FTE-048','Rubén García Martínez','Redes','N2',41,ARRAY['IP/Gateway','VLAN Config Switch','DNS'],true,'DISPONIBLE',0,'Madrid'),
('FTE-049','Mónica López López','Redes','N2',36,ARRAY['IP/Gateway','WiFi'],true,'DISPONIBLE',0,'Madrid'),
('FTE-050','Ignacio Rodríguez García','Redes','N2',43,ARRAY['IP/Gateway','Netstat','Port Security'],true,'DISPONIBLE',0,'Madrid'),
('FTE-051','Encarnación Fernández López','Redes','N2',38,ARRAY['IP/Gateway','VLAN Config Switch'],true,'DISPONIBLE',0,'Sevilla'),
('FTE-052','Tomás Martínez Rodríguez','Redes','N2',45,ARRAY['IP/Gateway','DNS','WiFi'],true,'DISPONIBLE',0,'Madrid'),
('FTE-053','Concepción García Fernández','Redes','N2',37,ARRAY['IP/Gateway','Netstat'],true,'DISPONIBLE',0,'Madrid'),
('FTE-054','Ramón López Martínez','Redes','N2',40,ARRAY['IP/Gateway','Port Security','DNS'],true,'DISPONIBLE',0,'Madrid'),
('FTE-055','Esperanza Rodríguez López','Redes','N2',42,ARRAY['IP/Gateway','VLAN Config Switch','Netstat'],true,'DISPONIBLE',0,'Madrid'),
('FTE-056','Emilio González García','Redes','N2',39,ARRAY['IP/Gateway','WiFi'],true,'DISPONIBLE',0,'Valencia'),
('FTE-057','Dolores Martínez Fernández','Redes','N2',41,ARRAY['IP/Gateway','DNS','Port Security'],true,'DISPONIBLE',0,'Madrid'),
('FTE-058','Julio García López','Redes','N2',36,ARRAY['IP/Gateway','Netstat'],true,'DISPONIBLE',0,'Madrid'),
('FTE-059','Mercedes Fernández Rodríguez','Redes','N2',44,ARRAY['IP/Gateway','VLAN Config Switch','DNS'],true,'DISPONIBLE',0,'Madrid'),
('FTE-060','Enrique López García','Redes','N2',38,ARRAY['IP/Gateway','WiFi','Netstat'],true,'DISPONIBLE',0,'Madrid'),
('FTE-061','Francisca Rodríguez Martínez','Redes','N2',43,ARRAY['IP/Gateway','Port Security','VLAN'],true,'DISPONIBLE',0,'Zaragoza')
ON CONFLICT (id_tecnico) DO NOTHING;

INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-062','Jaime García Rodríguez','Redes','N3',63,ARRAY['IP/Gateway','VLAN Config Switch','BGP','DNS','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-063','Susana López Fernández','Redes','N3',65,ARRAY['IP/Gateway','Netstat','OSPF','Firewall','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-064','Nicolás Martínez García','Redes','N3',68,ARRAY['IP/Gateway','VLAN Config Switch','Load Balancer','DNS'],true,'DISPONIBLE',0,'Madrid'),
('FTE-065','Yolanda Fernández López','Redes','N3',62,ARRAY['IP/Gateway','WiFi','Port Security','Netstat'],true,'DISPONIBLE',0,'Madrid'),
('FTE-066','Marcos Rodríguez Martínez','Redes','N3',70,ARRAY['IP/Gateway','BGP','OSPF','VLAN Config Switch'],true,'DISPONIBLE',0,'Barcelona'),
('FTE-067','Inmaculada García García','Redes','N3',64,ARRAY['IP/Gateway','DNS','Firewall','WiFi'],true,'DISPONIBLE',0,'Madrid'),
('FTE-068','Timoteo López Rodríguez','Redes','N3',67,ARRAY['IP/Gateway','VLAN Config Switch','Load Balancer'],true,'DISPONIBLE',0,'Madrid'),
('FTE-069','Remedios Martínez Fernández','Redes','N3',61,ARRAY['IP/Gateway','Netstat','Port Security','DNS'],true,'DISPONIBLE',0,'Madrid'),
('FTE-070','César González López','Redes','N3',69,ARRAY['IP/Gateway','BGP','OSPF','Firewall','WiFi'],true,'DISPONIBLE',0,'Madrid'),
('FTE-071','Reyes García Martínez','Redes','N3',66,ARRAY['IP/Gateway','VLAN Config Switch','DNS','Load Balancer'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-072','Guillermo López García','Redes','N4',86,ARRAY['IP/Gateway','BGP','OSPF','VLAN Config Switch','Architecture','Cisco'],true,'DISPONIBLE',0,'Madrid'),
('FTE-073','Virtudes Fernández García','Redes','N4',89,ARRAY['IP/Gateway','Load Balancer','Firewall','BGP','Architecture'],true,'DISPONIBLE',0,'Madrid'),
('FTE-074','Leandro Rodríguez López','Redes','N4',92,ARRAY['IP/Gateway','VLAN Config Switch','BGP','OSPF','SD-WAN','Architecture'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

-- ============================================================
-- STAFF — Windows (FTE-075 to FTE-111, 37 total)
-- N2=27, N3=8, N4=2
-- ============================================================
INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-075','Valentín García Martínez','Windows','N2',40,ARRAY['Gestión Servicios','AD','PowerShell'],true,'DISPONIBLE',0,'Madrid'),
('FTE-076','Felisa López López','Windows','N2',37,ARRAY['Gestión Servicios','Active Directory'],true,'DISPONIBLE',0,'Madrid'),
('FTE-077','Horacio Fernández García','Windows','N2',42,ARRAY['Gestión Servicios','GPO','AD'],true,'DISPONIBLE',0,'Madrid'),
('FTE-078','Angustias Rodríguez Fernández','Windows','N2',39,ARRAY['Gestión Servicios','Exchange'],true,'DISPONIBLE',0,'Madrid'),
('FTE-079','Isidoro Martínez López','Windows','N2',41,ARRAY['Gestión Servicios','PowerShell','AD'],true,'DISPONIBLE',0,'Barcelona'),
('FTE-080','Manuela González Rodríguez','Windows','N2',38,ARRAY['Gestión Servicios','Active Directory'],true,'DISPONIBLE',0,'Madrid'),
('FTE-081','Saturnino García García','Windows','N2',44,ARRAY['Gestión Servicios','GPO','PowerShell'],true,'DISPONIBLE',0,'Madrid'),
('FTE-082','Paquita López Martínez','Windows','N2',36,ARRAY['Gestión Servicios','AD'],true,'DISPONIBLE',0,'Madrid'),
('FTE-083','Evaristo Fernández López','Windows','N2',43,ARRAY['Gestión Servicios','Exchange','Teams'],true,'DISPONIBLE',0,'Madrid'),
('FTE-084','Milagros Rodríguez García','Windows','N2',40,ARRAY['Gestión Servicios','GPO','AD'],true,'DISPONIBLE',0,'Sevilla'),
('FTE-085','Primitivo Martínez Fernández','Windows','N2',37,ARRAY['Gestión Servicios','PowerShell'],true,'DISPONIBLE',0,'Madrid'),
('FTE-086','Celestina González López','Windows','N2',45,ARRAY['Gestión Servicios','Active Directory','Exchange'],true,'DISPONIBLE',0,'Madrid'),
('FTE-087','Prudencio García Rodríguez','Windows','N2',41,ARRAY['Gestión Servicios','GPO','VDI'],true,'DISPONIBLE',0,'Madrid'),
('FTE-088','Asunción López García','Windows','N2',38,ARRAY['Gestión Servicios','AD'],true,'DISPONIBLE',0,'Madrid'),
('FTE-089','Aurelio Fernández Martínez','Windows','N2',42,ARRAY['Gestión Servicios','PowerShell','Teams'],true,'DISPONIBLE',0,'Valencia'),
('FTE-090','Purificación Rodríguez López','Windows','N2',39,ARRAY['Gestión Servicios','Exchange','AD'],true,'DISPONIBLE',0,'Madrid'),
('FTE-091','Germán García Fernández','Windows','N2',40,ARRAY['Gestión Servicios','GPO','PowerShell'],true,'DISPONIBLE',0,'Madrid'),
('FTE-092','Visitación López Rodríguez','Windows','N2',36,ARRAY['Gestión Servicios','Active Directory'],true,'DISPONIBLE',0,'Madrid'),
('FTE-093','Epifanio Martínez García','Windows','N2',44,ARRAY['Gestión Servicios','Exchange','VDI'],true,'DISPONIBLE',0,'Madrid'),
('FTE-094','Sagrario González Fernández','Windows','N2',41,ARRAY['Gestión Servicios','AD','GPO'],true,'DISPONIBLE',0,'Zaragoza'),
('FTE-095','Casimiro García López','Windows','N2',37,ARRAY['Gestión Servicios','PowerShell'],true,'DISPONIBLE',0,'Madrid'),
('FTE-096','Elvira Fernández García','Windows','N2',43,ARRAY['Gestión Servicios','Active Directory','Teams'],true,'DISPONIBLE',0,'Madrid'),
('FTE-097','Lamberto Rodríguez Martínez','Windows','N2',39,ARRAY['Gestión Servicios','GPO','Exchange'],true,'DISPONIBLE',0,'Madrid'),
('FTE-098','Matilde López Fernández','Windows','N2',46,ARRAY['Gestión Servicios','AD','PowerShell','VDI'],true,'DISPONIBLE',0,'Madrid'),
('FTE-099','Cándido Martínez Rodríguez','Windows','N2',38,ARRAY['Gestión Servicios','Active Directory'],true,'DISPONIBLE',0,'Madrid'),
('FTE-100','Obdulia García García','Windows','N2',41,ARRAY['Gestión Servicios','Exchange','Teams'],true,'DISPONIBLE',0,'Madrid'),
('FTE-101','Teófilo González López','Windows','N2',35,ARRAY['Gestión Servicios','GPO'],true,'DISPONIBLE',0,'Barcelona')
ON CONFLICT (id_tecnico) DO NOTHING;

INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-102','Esperanza López Martínez','Windows','N3',62,ARRAY['Gestión Servicios','AD','PowerShell','GPO','Licencias'],true,'DISPONIBLE',0,'Madrid'),
('FTE-103','Salustiano García Fernández','Windows','N3',65,ARRAY['Gestión Servicios','Exchange','Teams','VDI','AD'],true,'DISPONIBLE',0,'Madrid'),
('FTE-104','Rosario Rodríguez García','Windows','N3',68,ARRAY['Gestión Servicios','PowerShell','GPO','AD','Licencias'],true,'DISPONIBLE',0,'Madrid'),
('FTE-105','Clemente Martínez López','Windows','N3',63,ARRAY['Gestión Servicios','VDI','Exchange','AD'],true,'DISPONIBLE',0,'Madrid'),
('FTE-106','Dionisio Fernández Rodríguez','Windows','N3',70,ARRAY['Gestión Servicios','PowerShell','AD','SCCM','GPO'],true,'DISPONIBLE',0,'Sevilla'),
('FTE-107','Herminia González García','Windows','N3',61,ARRAY['Gestión Servicios','Exchange','Teams','AD'],true,'DISPONIBLE',0,'Madrid'),
('FTE-108','Policarpo García Martínez','Windows','N3',67,ARRAY['Gestión Servicios','GPO','PowerShell','VDI'],true,'DISPONIBLE',0,'Madrid'),
('FTE-109','Calixta López García','Windows','N3',64,ARRAY['Gestión Servicios','AD','Exchange','Licencias'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-110','Filomena Rodríguez López','Windows','N4',86,ARRAY['Gestión Servicios','AD','PowerShell','Architecture','SCCM','VDI'],true,'DISPONIBLE',0,'Madrid'),
('FTE-111','Baldomero Martínez García','Windows','N4',90,ARRAY['Gestión Servicios','Exchange','Teams','VDI','Architecture','PowerShell'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

-- ============================================================
-- STAFF — Soporte (FTE-112 to FTE-128, 17 total)
-- N1=1, N2=14, N3=2
-- ============================================================
INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-112','Nazario López Fernández','Soporte','N1',20,ARRAY['Helpdesk','Tickets'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-113','Adela García Rodríguez','Soporte','N2',32,ARRAY['Helpdesk','Tickets','Hardware'],true,'DISPONIBLE',0,'Madrid'),
('FTE-114','Benigno Fernández López','Soporte','N2',35,ARRAY['Helpdesk','Tickets','Software'],true,'DISPONIBLE',0,'Madrid'),
('FTE-115','Crescencia Rodríguez García','Soporte','N2',30,ARRAY['Helpdesk','Tickets'],true,'DISPONIBLE',0,'Madrid'),
('FTE-116','Dámaso Martínez Fernández','Soporte','N2',34,ARRAY['Helpdesk','Tickets','Hardware'],true,'DISPONIBLE',0,'Barcelona'),
('FTE-117','Eustaquio González López','Soporte','N2',31,ARRAY['Helpdesk','Tickets','Software'],true,'DISPONIBLE',0,'Madrid'),
('FTE-118','Fabiola García García','Soporte','N2',36,ARRAY['Helpdesk','Tickets','AD Básico'],true,'DISPONIBLE',0,'Madrid'),
('FTE-119','Gumersindo López Martínez','Soporte','N2',33,ARRAY['Helpdesk','Tickets','Hardware'],true,'DISPONIBLE',0,'Madrid'),
('FTE-120','Higinia Fernández Rodríguez','Soporte','N2',30,ARRAY['Helpdesk','Tickets'],true,'DISPONIBLE',0,'Madrid'),
('FTE-121','Iluminada Rodríguez López','Soporte','N2',35,ARRAY['Helpdesk','Tickets','Software'],true,'DISPONIBLE',0,'Sevilla'),
('FTE-122','Jacinto Martínez García','Soporte','N2',32,ARRAY['Helpdesk','Tickets','Hardware'],true,'DISPONIBLE',0,'Madrid'),
('FTE-123','Komelia González Fernández','Soporte','N2',34,ARRAY['Helpdesk','Tickets','AD Básico'],true,'DISPONIBLE',0,'Madrid'),
('FTE-124','Leocadio García López','Soporte','N2',31,ARRAY['Helpdesk','Tickets'],true,'DISPONIBLE',0,'Madrid'),
('FTE-125','Macarena López García','Soporte','N2',36,ARRAY['Helpdesk','Tickets','Software'],true,'DISPONIBLE',0,'Madrid'),
('FTE-126','Nemesio Fernández Martínez','Soporte','N2',33,ARRAY['Helpdesk','Tickets','Hardware'],true,'DISPONIBLE',0,'Valencia')
ON CONFLICT (id_tecnico) DO NOTHING;

INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-127','Obispo Rodríguez García','Soporte','N3',55,ARRAY['Helpdesk','Tickets','ITSM','Escalaciones','Hardware'],true,'DISPONIBLE',0,'Madrid'),
('FTE-128','Perpetua Martínez López','Soporte','N3',58,ARRAY['Helpdesk','Tickets','ITSM','Software','AD Básico'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

-- ============================================================
-- STAFF — BBDD (FTE-129 to FTE-134, 6 total)
-- N3=4, N4=2
-- ============================================================
INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-129','Quintín González García','BBDD','N3',65,ARRAY['SQL','Oracle DBA','Backup DB','Create Table'],true,'DISPONIBLE',0,'Madrid'),
('FTE-130','Rosalinda García Fernández','BBDD','N3',68,ARRAY['SQL','Oracle DBA','Create Table','BI'],true,'DISPONIBLE',0,'Madrid'),
('FTE-131','Servando López Rodríguez','BBDD','N3',62,ARRAY['SQL','Backup DB','Create Table','MySQL'],true,'DISPONIBLE',0,'Madrid'),
('FTE-132','Tadea Fernández Martínez','BBDD','N3',70,ARRAY['SQL','Oracle DBA','Backup DB','PostgreSQL'],true,'DISPONIBLE',0,'Barcelona')
ON CONFLICT (id_tecnico) DO NOTHING;

INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-133','Ursicino Rodríguez López','BBDD','N4',88,ARRAY['SQL','Oracle DBA','Backup DB','Architecture','Tuning','PostgreSQL'],true,'DISPONIBLE',0,'Madrid'),
('FTE-134','Valentina Martínez García','BBDD','N4',92,ARRAY['SQL','Oracle DBA','BI','Architecture','Tuning','MySQL'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

-- ============================================================
-- STAFF — Seguridad (FTE-135 to FTE-139, 5 total)
-- N3=3, N4=2
-- ============================================================
INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-135','Wenceslao García López','Seguridad','N3',67,ARRAY['Firewall','SIEM','EDR','Permisos Carpeta'],true,'DISPONIBLE',0,'Madrid'),
('FTE-136','Ximena López García','Seguridad','N3',64,ARRAY['Firewall','PAM','PKI','EDR'],true,'DISPONIBLE',0,'Madrid'),
('FTE-137','Yolanda Fernández Rodríguez','Seguridad','N3',70,ARRAY['Firewall','SIEM','ZTNA','PKI'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-138','Zacarías Rodríguez Fernández','Seguridad','N4',89,ARRAY['Firewall','SIEM','PAM','PKI','ZTNA','Architecture'],true,'DISPONIBLE',0,'Madrid'),
('FTE-139','Amalia Martínez González','Seguridad','N4',94,ARRAY['Firewall','SIEM','EDR','PAM','ZTNA','Architecture','CyberArk'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

-- ============================================================
-- STAFF — DevOps (FTE-140 to FTE-143, 4 total)
-- N3=3, N4=1
-- ============================================================
INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-140','Bautista García Martínez','DevOps','N3',68,ARRAY['CI/CD','Git','Kubernetes','Monitoring','Docker'],true,'DISPONIBLE',0,'Madrid'),
('FTE-141','Celestino López Fernández','DevOps','N3',65,ARRAY['CI/CD','Git','Docker','Grafana','Ansible'],true,'DISPONIBLE',0,'Madrid'),
('FTE-142','Dominga Fernández García','DevOps','N3',71,ARRAY['CI/CD','Kubernetes','Grafana','Monitoring','Terraform'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-143','Eladio Rodríguez López','DevOps','N4',90,ARRAY['CI/CD','Kubernetes','Terraform','Architecture','Grafana','Git'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

-- ============================================================
-- STAFF — QA (FTE-144 to FTE-145, 2 total)
-- N3=2
-- ============================================================
INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-144','Felicísima García González','QA','N3',63,ARRAY['Testing','Selenium','JUnit','JIRA'],true,'DISPONIBLE',0,'Madrid'),
('FTE-145','Genaro López Martínez','QA','N3',66,ARRAY['Testing','Selenium','Postman','JIRA','API Testing'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

-- ============================================================
-- STAFF — Backend (FTE-146 to FTE-150, 5 total)
-- N3=5
-- ============================================================
INSERT INTO pmo_staff_skills (id_tecnico,nombre,silo,nivel,skills_score,tags,disponible,estado,carga_actual,ubicacion) VALUES
('FTE-146','Hermenegildo Fernández López','Backend','N3',64,ARRAY['Microservicios','Java','Spring Boot','Docker'],true,'DISPONIBLE',0,'Madrid'),
('FTE-147','Ildefonso Rodríguez García','Backend','N3',67,ARRAY['Microservicios','Python','FastAPI','Docker','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-148','Josefa Martínez Fernández','Backend','N3',70,ARRAY['Microservicios','Java','Spring Boot','Kubernetes','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-149','Kildara González López','Backend','N3',65,ARRAY['Microservicios','Node.js','Express','Docker','Git'],true,'DISPONIBLE',0,'Madrid'),
('FTE-150','Longinos García Rodríguez','Backend','N3',68,ARRAY['Microservicios','Python','Django','REST API','Git'],true,'DISPONIBLE',0,'Madrid')
ON CONFLICT (id_tecnico) DO NOTHING;

-- ============================================================
-- PROJECTS (46 total)
-- ============================================================
INSERT INTO cartera_build (id_proyecto,nombre,prioridad,prioridad_num,estado,horas_estimadas,skill_requerida,fecha_inicio,fecha_fin) VALUES
('PRJ0001','Centralizar la gestión de identidades','Critica',1,'En Progreso',60,'AD:Crear Usuario','2025-01-15','2025-03-15'),
('PRJ0002','Implementación arquitectura SIEM integrada','Alta',2,'Planificado',45,'Cloud:VM Start/Stop','2025-02-01','2025-03-20'),
('PRJ0003','Modelo de gestión de secretos','Alta',2,'En Progreso',50,'Seguridad:Permisos Carpeta','2025-01-20','2025-03-25'),
('PRJ0004','Renovación de hardware de CyberArk','Critica',1,'Completado',25,'Hardware:Instalar RAM','2025-01-01','2025-01-25'),
('PRJ0005','Aplicar control de acceso NAC en oficinas','Alta',2,'Planificado',80,'Redes:Port Security','2025-03-01','2025-05-30'),
('PRJ0006','Implantar Exadata servidor Mission Critical','Critica',1,'En Progreso',120,'Linux:Navegación','2025-01-10','2025-04-30'),
('PRJ0007','Migración Simep entorno linux','Media',3,'Planificado',45,'Linux:Gestión Archivos','2025-04-01','2025-05-15'),
('PRJ0008','Montar entorno preproducción servicios calidad','Media',3,'Backlog',35,'Linux:Navegación','2025-05-01','2025-06-15'),
('PRJ0009','Rearquitectura de la red de los Data Centers','Critica',1,'En Progreso',150,'Redes:Netstat','2025-01-05','2025-06-30'),
('PRJ0010','Migración Infraestructura y Swift Alliance 7','Alta',2,'Planificado',90,'Redes:IP/Gateway','2025-02-15','2025-05-15'),
('PRJ0011','Migrar sistemas Linux Red Hat 7 a versión actual','Alta',2,'En Progreso',50,'Linux:Procesos','2025-01-25','2025-03-30'),
('PRJ0012','Renovar infraestructura servidores de ETL','Alta',2,'Planificado',55,'Linux:Tareas Crontab','2025-03-01','2025-04-30'),
('PRJ0013','Reestructuración de las redes de chasis Synergy','Media',3,'Backlog',90,'Redes:VLAN Config Switch','2025-04-15','2025-07-30'),
('PRJ0014','Actualización VerisecUP','Alta',2,'En Progreso',30,'Windows:Gestión Servicios','2025-01-30','2025-02-28'),
('PRJ0015','Actualizar Erwin Mart Server','Baja',4,'Backlog',40,'SQL:Create Table','2025-06-01','2025-07-15'),
('PRJ0016','Actualizar plataforma copias de seguridad corporativa','Critica',1,'En Progreso',60,'SQL:Backup DB','2025-01-12','2025-03-12'),
('PRJ0017','Adopción e implantación plataforma datos analíticos','Media',3,'Planificado',85,'Cloud:Crear Bucket','2025-03-15','2025-06-15'),
('PRJ0018','Aislar weblogic de Pagos de ARES','Critica',1,'En Progreso',55,'Linux:Procesos','2025-01-18','2025-03-18'),
('PRJ0019','Migración Active Directory a Azure AD','Critica',1,'Planificado',110,'AD:Sincronización','2025-02-01','2025-06-30'),
('PRJ0020','Implementar WAF corporativo','Alta',2,'Backlog',70,'Seguridad:Firewall','2025-04-01','2025-07-15'),
('PRJ0021','Renovación switches core CPD Madrid','Alta',2,'En Progreso',95,'Redes:VLAN Config Switch','2025-01-20','2025-04-30'),
('PRJ0022','Actualización SAP ERP módulo FICO','Critica',1,'En Progreso',200,'SAP:ABAP','2025-01-10','2025-09-30'),
('PRJ0023','Implantación SIEM Splunk','Alta',2,'Planificado',130,'Seguridad:SIEM','2025-03-01','2025-08-31'),
('PRJ0024','Migración Oracle 12c a 19c','Critica',1,'En Progreso',180,'SQL:Oracle DBA','2025-01-05','2025-07-31'),
('PRJ0025','Renovación infraestructura VDI','Alta',2,'Backlog',160,'Windows:VDI','2025-05-01','2025-10-31'),
('PRJ0026','Implementar plataforma DevSecOps','Media',3,'Planificado',120,'DevOps:CI/CD','2025-04-01','2025-09-30'),
('PRJ0027','Actualización firmware servidores HPE','Media',3,'Backlog',40,'Hardware:Firmware','2025-06-01','2025-07-31'),
('PRJ0028','Migración correo Exchange a M365','Alta',2,'En Progreso',75,'Windows:Exchange','2025-02-01','2025-05-31'),
('PRJ0029','Implantación EDR CrowdStrike','Alta',2,'Planificado',65,'Seguridad:EDR','2025-03-15','2025-06-30'),
('PRJ0030','Renovación SAN almacenamiento CPD','Critica',1,'Planificado',140,'Storage:SAN','2025-04-01','2025-08-31'),
('PRJ0031','Automatización backups con Veeam','Media',3,'En Progreso',50,'Storage:Backup','2025-02-15','2025-04-30'),
('PRJ0032','Implantación Kubernetes producción','Alta',2,'En Progreso',110,'DevOps:Kubernetes','2025-01-20','2025-05-31'),
('PRJ0033','Migración aplicaciones legacy a microservicios','Critica',1,'Planificado',300,'Backend:Microservicios','2025-06-01','2025-12-31'),
('PRJ0034','Actualización PKI corporativa','Alta',2,'Backlog',55,'Seguridad:PKI','2025-05-01','2025-07-31'),
('PRJ0035','Renovación red WiFi oficinas','Media',3,'Planificado',80,'Redes:WiFi','2025-04-15','2025-07-15'),
('PRJ0036','Implementar PAM CyberArk','Critica',1,'En Progreso',95,'Seguridad:PAM','2025-02-01','2025-06-30'),
('PRJ0037','Actualización plataforma BI Cognos','Media',3,'Backlog',70,'SQL:BI','2025-06-01','2025-09-30'),
('PRJ0038','Migración DNS a BIND9 redundante','Media',3,'Planificado',35,'Redes:DNS','2025-05-01','2025-06-30'),
('PRJ0039','Implantación monitorización Zabbix','Media',3,'En Progreso',45,'DevOps:Monitoring','2025-03-01','2025-05-31'),
('PRJ0040','Renovación licencias Windows Server 2022','Alta',2,'Planificado',60,'Windows:Licencias','2025-04-01','2025-06-30'),
('PRJ0041','Actualización plataforma videoconferencia','Baja',4,'Backlog',25,'Windows:Teams','2025-07-01','2025-08-31'),
('PRJ0042','Migración repositorios SVN a GitLab','Media',3,'En Progreso',40,'DevOps:Git','2025-02-15','2025-04-30'),
('PRJ0043','Implementar Zero Trust Network Access','Critica',1,'Planificado',170,'Seguridad:ZTNA','2025-05-01','2025-11-30'),
('PRJ0044','Actualización plataforma ITSM ','Alta',2,'En Progreso',80,'ITSM:','2025-02-01','2025-05-31'),
('PRJ0045','Renovación balanceadores F5','Alta',2,'Backlog',65,'Redes:Load Balancer','2025-06-01','2025-08-31'),
('PRJ0046','Implantación observabilidad con Grafana','Media',3,'Planificado',55,'DevOps:Grafana','2025-04-15','2025-07-31')
ON CONFLICT (id_proyecto) DO NOTHING;

-- ============================================================
-- KANBAN TASKS (21 tasks)
-- ============================================================
INSERT INTO kanban_tareas (id,tipo,prioridad,titulo,columna,usuario_asignado,id_tecnico,tiempo_horas,bloqueador) VALUES
('TSK-001','RUN','Critica','P1: Caída servicio SWIFT Alliance','En Progreso','Carlos Rodríguez',NULL,8,NULL),
('TSK-002','RUN','Alta','Resolver latencia red CPD Madrid','Análisis','Laura Sánchez',NULL,4,NULL),
('TSK-003','BUILD','Critica','Migración Oracle 12c - Fase 1','En Progreso','Roberto Pérez',NULL,16,NULL),
('TSK-004','RUN','Media','Actualizar certificados SSL caducados','Backlog','Miguel Fernández',NULL,0,NULL),
('TSK-005','BUILD','Alta','Implantar Kubernetes - Namespace Prod','Code Review','Fernando Pérez',NULL,6,NULL),
('TSK-006','RUN','Alta','Incidencia AD - Bloqueo masivo cuentas','En Progreso','Ana Martínez',NULL,5,NULL),
('TSK-007','BUILD','Media','Configurar pipeline CI/CD GitLab','Testing','Bautista García',NULL,3,NULL),
('TSK-008','RUN','Critica','P1: Fallo backup corporativo nocturno','Bloqueado','Quintín González',NULL,0,'Esperando acceso a SAN'),
('TSK-009','BUILD','Alta','Renovar switches core - Capa distribución','En Progreso','Guillermo López',NULL,12,NULL),
('TSK-010','RUN','Media','Revisar logs Firewall perímetro','Backlog','Wenceslao García',NULL,0,NULL),
('TSK-011','BUILD','Alta','Implementar PAM CyberArk - Fase 2','Análisis','Zacarías Rodríguez',NULL,8,NULL),
('TSK-012','RUN','Baja','Actualizar documentación procedimientos','Backlog','Obispo Rodríguez',NULL,0,NULL),
('TSK-013','BUILD','Critica','Migración AD a Azure AD - Pruebas piloto','Code Review','Valentín García',NULL,10,NULL),
('TSK-014','RUN','Alta','Resolver error VPN usuarios remotos','En Progreso','Jaime García',NULL,4,NULL),
('TSK-015','BUILD','Media','Despliegue Grafana dashboards producción','Despliegue','Eladio Rodríguez',NULL,2,NULL),
('TSK-016','RUN','Media','Análisis capacidad servidores ETL','Análisis','Servando López',NULL,5,NULL),
('TSK-017','BUILD','Alta','Configurar WAF reglas aplicación web','Testing','Ximena López',NULL,7,NULL),
('TSK-018','RUN','Baja','Limpieza logs servidores producción','Backlog','Fabiola García',NULL,0,NULL),
('TSK-019','BUILD','Alta','Migración correo Exchange - Lote 3','Despliegue','Esperanza López',NULL,6,NULL),
('TSK-020','RUN','Media','Revisar alertas Zabbix sin resolver','En Progreso','Celestino López',NULL,3,NULL),
('TSK-021','BUILD','Media','Actualización ITSM  v2.1','Completado','Ildefonso Rodríguez',NULL,8,NULL)
ON CONFLICT (id) DO NOTHING;

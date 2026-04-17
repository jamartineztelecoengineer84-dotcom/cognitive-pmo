-- ============================================================
-- COGNITIVE PMO - RBAC: Role-Based Access Control
-- Sistema completo de autenticación, roles y permisos
-- Incluye: Estructura directiva corporativa de IT
-- ============================================================

-- ============================================================
-- 1. TABLA DE ROLES
-- ============================================================
CREATE TABLE IF NOT EXISTS rbac_roles (
    id_role SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    nivel_jerarquico INTEGER NOT NULL DEFAULT 0,  -- 0=más alto (CEO), 10=más bajo
    color VARCHAR(7) DEFAULT '#6B7280',
    icono VARCHAR(50) DEFAULT 'shield',
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 2. TABLA DE PERMISOS (granulares por módulo)
-- ============================================================
CREATE TABLE IF NOT EXISTS rbac_permisos (
    id_permiso SERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    modulo VARCHAR(50) NOT NULL,
    accion VARCHAR(30) NOT NULL CHECK (accion IN ('ver','crear','editar','eliminar','aprobar','exportar','ejecutar','admin')),
    descripcion TEXT,
    criticidad VARCHAR(10) DEFAULT 'MEDIA' CHECK (criticidad IN ('BAJA','MEDIA','ALTA','CRITICA'))
);

-- ============================================================
-- 3. RELACIÓN ROLE <-> PERMISOS (N:M)
-- ============================================================
CREATE TABLE IF NOT EXISTS rbac_role_permisos (
    id_role INTEGER REFERENCES rbac_roles(id_role) ON DELETE CASCADE,
    id_permiso INTEGER REFERENCES rbac_permisos(id_permiso) ON DELETE CASCADE,
    PRIMARY KEY (id_role, id_permiso)
);

-- ============================================================
-- 4. TABLA DE USUARIOS DEL SISTEMA
-- ============================================================
CREATE TABLE IF NOT EXISTS rbac_usuarios (
    id_usuario SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(200) NOT NULL,
    avatar_url VARCHAR(500),
    id_role INTEGER REFERENCES rbac_roles(id_role),
    id_recurso VARCHAR(20),  -- FK a pmo_staff_skills (técnicos)
    id_pm VARCHAR(20),       -- FK a pmo_project_managers (PMs)
    id_directivo VARCHAR(20), -- FK a directorio_corporativo
    departamento VARCHAR(100),
    cargo VARCHAR(150),
    telefono VARCHAR(30),
    ultimo_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    requiere_cambio_password BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 5. SESIONES ACTIVAS (JWT tracking)
-- ============================================================
CREATE TABLE IF NOT EXISTS rbac_sesiones (
    id_sesion SERIAL PRIMARY KEY,
    id_usuario INTEGER REFERENCES rbac_usuarios(id_usuario) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    activa BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- 6. LOG DE AUDITORÍA DE ACCESO
-- ============================================================
CREATE TABLE IF NOT EXISTS rbac_audit_log (
    id_log SERIAL PRIMARY KEY,
    id_usuario INTEGER,
    email VARCHAR(255),
    accion VARCHAR(50) NOT NULL,
    modulo VARCHAR(50),
    recurso VARCHAR(200),
    detalle JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    resultado VARCHAR(20) DEFAULT 'OK' CHECK (resultado IN ('OK','DENEGADO','ERROR')),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 7. DIRECTORIO CORPORATIVO - ESTRUCTURA DE DIRECCIÓN IT
-- Empresa grande de IT tipo consultora/banco
-- ============================================================
CREATE TABLE IF NOT EXISTS directorio_corporativo (
    id_directivo VARCHAR(20) PRIMARY KEY,
    nombre_completo VARCHAR(200) NOT NULL,
    cargo VARCHAR(150) NOT NULL,
    nivel_organizativo VARCHAR(30) NOT NULL CHECK (nivel_organizativo IN (
        'C-LEVEL','VP','DIRECTOR','SUBDIRECTOR','GERENTE','COORDINADOR','JEFE_EQUIPO'
    )),
    area VARCHAR(100) NOT NULL,
    reporta_a VARCHAR(20) REFERENCES directorio_corporativo(id_directivo),
    email VARCHAR(255) NOT NULL UNIQUE,
    telefono VARCHAR(30),
    ubicacion VARCHAR(100) DEFAULT 'Madrid HQ',
    fecha_incorporacion DATE DEFAULT CURRENT_DATE,
    activo BOOLEAN DEFAULT TRUE,
    bio TEXT,
    linkedin VARCHAR(255),
    foto_url VARCHAR(500)
);

-- ============================================================
-- ÍNDICES PARA RBAC
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_rbac_usuarios_email ON rbac_usuarios(email);
CREATE INDEX IF NOT EXISTS idx_rbac_usuarios_role ON rbac_usuarios(id_role);
CREATE INDEX IF NOT EXISTS idx_rbac_usuarios_recurso ON rbac_usuarios(id_recurso);
CREATE INDEX IF NOT EXISTS idx_rbac_sesiones_usuario ON rbac_sesiones(id_usuario);
CREATE INDEX IF NOT EXISTS idx_rbac_sesiones_token ON rbac_sesiones(token_hash);
CREATE INDEX IF NOT EXISTS idx_rbac_audit_usuario ON rbac_audit_log(id_usuario);
CREATE INDEX IF NOT EXISTS idx_rbac_audit_timestamp ON rbac_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_directorio_area ON directorio_corporativo(area);
CREATE INDEX IF NOT EXISTS idx_directorio_reporta ON directorio_corporativo(reporta_a);

-- ============================================================
-- DATOS: ROLES DEL SISTEMA
-- ============================================================
INSERT INTO rbac_roles (code, nombre, descripcion, nivel_jerarquico, color, icono) VALUES
  ('SUPERADMIN',      'Super Administrador',           'Acceso total al sistema. Dios mode.',                                    0, '#EF4444', 'crown'),
  ('CEO',             'Chief Executive Officer',        'Dirección general. Dashboard ejecutivo y reportes estratégicos.',         1, '#DC2626', 'building'),
  ('CTO',             'Chief Technology Officer',       'Dirección tecnológica. Visión completa técnica y arquitectura.',          1, '#B91C1C', 'cpu'),
  ('CIO',             'Chief Information Officer',      'Dirección de información. Gobernanza TI y compliance.',                  1, '#991B1B', 'database'),
  ('CISO',            'Chief Information Security Officer', 'Dirección de seguridad. Auditorías, compliance y war room.',          1, '#7F1D1D', 'shield-alert'),
  ('CFO',             'Chief Financial Officer',        'Dirección financiera. Presupuestos y control de costes.',                1, '#F59E0B', 'banknote'),
  ('VP_ENGINEERING',  'VP of Engineering',              'Vice Presidencia de Ingeniería. Gestión técnica global.',                2, '#8B5CF6', 'code'),
  ('VP_OPERATIONS',   'VP of Operations',               'Vice Presidencia de Operaciones. RUN y disponibilidad.',                2, '#6366F1', 'activity'),
  ('VP_PMO',          'VP of PMO',                      'Vice Presidencia PMO. Gobernanza de proyectos y portfolio.',             2, '#4F46E5', 'briefcase'),
  ('DIRECTOR_IT',     'Director de IT',                 'Dirección departamental IT. Gestión de equipos y recursos.',             3, '#2563EB', 'monitor'),
  ('DIRECTOR_SEC',    'Director de Seguridad',          'Dirección de ciberseguridad. Gestión de incidentes de seguridad.',       3, '#0891B2', 'shield'),
  ('DIRECTOR_INFRA',  'Director de Infraestructura',    'Dirección de infraestructura y redes.',                                  3, '#0D9488', 'server'),
  ('DIRECTOR_DATA',   'Director de Datos',              'Dirección de datos y BBDD.',                                             3, '#059669', 'hard-drive'),
  ('PMO_SENIOR',      'PMO Senior / Program Manager',   'Gestión de programas. Gobernanza, presupuestos, riesgos.',              4, '#10B981', 'folder-kanban'),
  ('PMO_JUNIOR',      'PMO Junior / Project Manager',   'Gestión de proyectos individuales. Kanban y seguimiento.',              5, '#34D399', 'clipboard-list'),
  ('TEAM_LEAD',       'Team Lead / Jefe de Equipo',     'Líder técnico de silo. Gestión de equipo y asignaciones.',              5, '#06B6D4', 'users'),
  ('TECH_SENIOR',     'Técnico Senior (N3-N4)',         'Técnico experto. Resolución avanzada e incidencias críticas.',           6, '#3B82F6', 'wrench'),
  ('TECH_JUNIOR',     'Técnico Junior (N1-N2)',         'Técnico base. Operaciones y soporte estándar.',                          7, '#60A5FA', 'tool'),
  ('QA_LEAD',         'QA Lead',                        'Líder de calidad. Testing, compliance y auditoría técnica.',             5, '#A855F7', 'check-circle'),
  ('DEVOPS_LEAD',     'DevOps Lead',                    'Líder DevOps. CI/CD, infraestructura como código.',                      5, '#EC4899', 'git-branch'),
  ('AUDITOR',         'Auditor / Compliance',           'Auditoría y cumplimiento. Solo lectura + reportes de compliance.',       4, '#F97316', 'file-search'),
  ('OBSERVADOR',      'Observador / Stakeholder',       'Solo lectura. Dashboards y reportes ejecutivos.',                        8, '#9CA3AF', 'eye'),
  ('READONLY',        'Solo Lectura',                   'Acceso mínimo de solo lectura a dashboards públicos.',                   9, '#D1D5DB', 'lock')
ON CONFLICT (code) DO NOTHING;

-- ============================================================
-- DATOS: PERMISOS GRANULARES POR MÓDULO
-- ============================================================
INSERT INTO rbac_permisos (code, modulo, accion, descripcion, criticidad) VALUES
  -- DASHBOARD
  ('dashboard.ver',            'dashboard',     'ver',       'Ver dashboard principal',                     'BAJA'),
  ('dashboard.ejecutivo',      'dashboard',     'ver',       'Ver dashboard ejecutivo con KPIs estratégicos','MEDIA'),
  ('dashboard.exportar',       'dashboard',     'exportar',  'Exportar datos del dashboard',                'MEDIA'),

  -- EQUIPO / RECURSOS HUMANOS
  ('team.ver',                 'team',          'ver',       'Ver listado de técnicos',                     'BAJA'),
  ('team.crear',               'team',          'crear',     'Crear nuevo técnico',                         'ALTA'),
  ('team.editar',              'team',          'editar',    'Editar datos de técnicos',                    'ALTA'),
  ('team.eliminar',            'team',          'eliminar',  'Eliminar técnico',                            'CRITICA'),
  ('team.asignar',             'team',          'ejecutar',  'Asignar técnico a incidencia/proyecto',       'ALTA'),
  ('team.ver_salarios',        'team',          'ver',       'Ver información salarial (confidencial)',     'CRITICA'),

  -- CARTERA DE PROYECTOS (BUILD)
  ('proyectos.ver',            'proyectos',     'ver',       'Ver cartera de proyectos',                    'BAJA'),
  ('proyectos.crear',          'proyectos',     'crear',     'Crear nuevo proyecto',                        'ALTA'),
  ('proyectos.editar',         'proyectos',     'editar',    'Editar proyecto existente',                   'ALTA'),
  ('proyectos.eliminar',       'proyectos',     'eliminar',  'Eliminar proyecto',                           'CRITICA'),
  ('proyectos.aprobar',        'proyectos',     'aprobar',   'Aprobar cambio de estado de proyecto',        'CRITICA'),
  ('proyectos.pausar',         'proyectos',     'ejecutar',  'Pausar proyecto por riesgo P1',               'CRITICA'),

  -- INCIDENCIAS (RUN)
  ('incidencias.ver',          'incidencias',   'ver',       'Ver incidencias',                             'BAJA'),
  ('incidencias.crear',        'incidencias',   'crear',     'Crear nueva incidencia',                      'MEDIA'),
  ('incidencias.editar',       'incidencias',   'editar',    'Editar incidencia',                           'MEDIA'),
  ('incidencias.eliminar',     'incidencias',   'eliminar',  'Eliminar incidencia',                         'CRITICA'),
  ('incidencias.escalar',      'incidencias',   'ejecutar',  'Escalar incidencia a nivel superior',         'ALTA'),

  -- KANBAN
  ('kanban.ver',               'kanban',        'ver',       'Ver tablero Kanban',                          'BAJA'),
  ('kanban.crear',             'kanban',        'crear',     'Crear tarea en Kanban',                       'MEDIA'),
  ('kanban.editar',            'kanban',        'editar',    'Editar/mover tarea en Kanban',                'MEDIA'),
  ('kanban.eliminar',          'kanban',        'eliminar',  'Eliminar tarea de Kanban',                    'ALTA'),

  -- PRESUPUESTOS
  ('presupuestos.ver',         'presupuestos',  'ver',       'Ver presupuestos',                            'MEDIA'),
  ('presupuestos.crear',       'presupuestos',  'crear',     'Crear presupuesto',                           'ALTA'),
  ('presupuestos.editar',      'presupuestos',  'editar',    'Editar presupuesto',                          'ALTA'),
  ('presupuestos.eliminar',    'presupuestos',  'eliminar',  'Eliminar presupuesto',                        'CRITICA'),
  ('presupuestos.aprobar',     'presupuestos',  'aprobar',   'Aprobar presupuesto',                         'CRITICA'),
  ('presupuestos.ver_total',   'presupuestos',  'ver',       'Ver totales y desglose completo',             'ALTA'),

  -- GOBERNANZA / PMO
  ('gobernanza.ver',           'gobernanza',    'ver',       'Ver scoring de gobernanza',                   'MEDIA'),
  ('gobernanza.editar',        'gobernanza',    'editar',    'Editar parámetros de gobernanza',             'ALTA'),
  ('gobernanza.dashboard',     'gobernanza',    'ver',       'Ver dashboard de gobernanza',                 'MEDIA'),
  ('pmo.managers.ver',         'pmo',           'ver',       'Ver Project Managers',                        'BAJA'),
  ('pmo.managers.crear',       'pmo',           'crear',     'Crear Project Manager',                       'ALTA'),
  ('pmo.managers.editar',      'pmo',           'editar',    'Editar Project Manager',                      'ALTA'),

  -- WAR ROOM / CRISIS
  ('warroom.ver',              'warroom',       'ver',       'Ver war room y sesiones',                     'MEDIA'),
  ('warroom.crear',            'warroom',       'crear',     'Iniciar sesión de war room',                  'ALTA'),
  ('warroom.participar',       'warroom',       'ejecutar',  'Participar en war room (enviar mensajes)',    'MEDIA'),
  ('warroom.cerrar',           'warroom',       'ejecutar',  'Cerrar sesión de war room',                   'ALTA'),

  -- ALERTAS
  ('alertas.ver',              'alertas',       'ver',       'Ver alertas inteligentes',                    'BAJA'),
  ('alertas.crear',            'alertas',       'crear',     'Crear alerta',                                'MEDIA'),
  ('alertas.gestionar',        'alertas',       'editar',    'Acknowledge/resolver alertas',                'ALTA'),

  -- COMPLIANCE / AUDITORÍA
  ('compliance.ver',           'compliance',    'ver',       'Ver auditorías y compliance',                 'MEDIA'),
  ('compliance.crear',         'compliance',    'crear',     'Crear auditoría',                             'ALTA'),
  ('compliance.editar',        'compliance',    'editar',    'Editar auditoría',                            'ALTA'),
  ('compliance.dashboard',     'compliance',    'ver',       'Ver dashboard de compliance',                 'MEDIA'),

  -- POSTMORTEM
  ('postmortem.ver',           'postmortem',    'ver',       'Ver postmortems',                             'MEDIA'),
  ('postmortem.crear',         'postmortem',    'crear',     'Crear postmortem',                            'MEDIA'),
  ('postmortem.aprobar',       'postmortem',    'aprobar',   'Aprobar postmortem',                          'ALTA'),

  -- SIMULACIONES
  ('simulacion.ver',           'simulacion',    'ver',       'Ver simulaciones what-if',                    'MEDIA'),
  ('simulacion.ejecutar',      'simulacion',    'ejecutar',  'Ejecutar simulación',                         'ALTA'),

  -- DOCUMENTACIÓN
  ('documentacion.ver',        'documentacion', 'ver',       'Ver repositorio documental',                  'BAJA'),
  ('documentacion.crear',      'documentacion', 'crear',     'Crear documento',                             'MEDIA'),
  ('documentacion.editar',     'documentacion', 'editar',    'Editar documento',                            'MEDIA'),
  ('documentacion.eliminar',   'documentacion', 'eliminar',  'Eliminar documento',                          'ALTA'),

  -- PLANES RUN/BUILD
  ('planes.ver',               'planes',        'ver',       'Ver planes RUN y BUILD',                      'BAJA'),
  ('planes.crear',             'planes',        'crear',     'Crear plan',                                  'MEDIA'),
  ('planes.eliminar',          'planes',        'eliminar',  'Eliminar plan',                               'ALTA'),

  -- AGENTES IA / FLOWISE
  ('agentes.ver',              'agentes',       'ver',       'Ver configuración de agentes IA',             'MEDIA'),
  ('agentes.configurar',       'agentes',       'admin',     'Configurar chatflows de Flowise',             'CRITICA'),
  ('agentes.chat',             'agentes',       'ejecutar',  'Interactuar con agentes IA',                  'MEDIA'),
  ('agentes.metricas',         'agentes',       'ver',       'Ver métricas de rendimiento de agentes',      'MEDIA'),

  -- DEV TOOLS
  ('devtools.ver',             'devtools',      'ver',       'Ver herramientas de desarrollo',              'ALTA'),
  ('devtools.sql',             'devtools',      'ejecutar',  'Ejecutar SQL directo',                        'CRITICA'),
  ('devtools.files',           'devtools',      'ver',       'Ver archivos del servidor',                   'CRITICA'),

  -- ADMINISTRACIÓN RBAC
  ('rbac.ver',                 'rbac',          'ver',       'Ver configuración RBAC',                      'ALTA'),
  ('rbac.usuarios',            'rbac',          'admin',     'Gestionar usuarios del sistema',              'CRITICA'),
  ('rbac.roles',               'rbac',          'admin',     'Gestionar roles y permisos',                  'CRITICA'),
  ('rbac.audit',               'rbac',          'ver',       'Ver log de auditoría',                        'ALTA'),

  -- DIRECTORIO CORPORATIVO
  ('directorio.ver',           'directorio',    'ver',       'Ver organigrama corporativo',                 'BAJA'),
  ('directorio.editar',        'directorio',    'editar',    'Editar directorio corporativo',               'CRITICA'),

  -- PREDICCIONES
  ('prediccion.ver',           'prediccion',    'ver',       'Ver predicciones de demanda',                 'MEDIA'),

  -- CATÁLOGOS
  ('catalogo.ver',             'catalogo',      'ver',       'Ver catálogos (skills, incidencias)',         'BAJA'),
  ('catalogo.editar',          'catalogo',      'editar',    'Editar catálogos maestros',                   'ALTA')
ON CONFLICT (code) DO NOTHING;

-- ============================================================
-- ASIGNACIÓN DE PERMISOS POR ROL
-- ============================================================

-- SUPERADMIN: TODO
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'SUPERADMIN'
ON CONFLICT DO NOTHING;

-- CEO: Dashboards ejecutivos, presupuestos (ver), gobernanza, directorio
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'CEO' AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo','dashboard.exportar',
  'team.ver','proyectos.ver','incidencias.ver','kanban.ver',
  'presupuestos.ver','presupuestos.ver_total','presupuestos.aprobar',
  'gobernanza.ver','gobernanza.dashboard','pmo.managers.ver',
  'warroom.ver','alertas.ver','compliance.ver','compliance.dashboard',
  'postmortem.ver','simulacion.ver','documentacion.ver',
  'planes.ver','agentes.metricas','directorio.ver','directorio.editar',
  'prediccion.ver','catalogo.ver','rbac.ver','rbac.audit'
) ON CONFLICT DO NOTHING;

-- CTO: Todo técnico + arquitectura
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'CTO' AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo','dashboard.exportar',
  'team.ver','team.crear','team.editar','team.asignar',
  'proyectos.ver','proyectos.crear','proyectos.editar','proyectos.aprobar','proyectos.pausar',
  'incidencias.ver','incidencias.crear','incidencias.editar','incidencias.escalar',
  'kanban.ver','kanban.crear','kanban.editar',
  'presupuestos.ver','presupuestos.ver_total',
  'gobernanza.ver','gobernanza.editar','gobernanza.dashboard',
  'pmo.managers.ver','pmo.managers.crear','pmo.managers.editar',
  'warroom.ver','warroom.crear','warroom.participar','warroom.cerrar',
  'alertas.ver','alertas.crear','alertas.gestionar',
  'compliance.ver','compliance.dashboard',
  'postmortem.ver','postmortem.crear','postmortem.aprobar',
  'simulacion.ver','simulacion.ejecutar',
  'documentacion.ver','documentacion.crear','documentacion.editar',
  'planes.ver','planes.crear','planes.eliminar',
  'agentes.ver','agentes.configurar','agentes.chat','agentes.metricas',
  'devtools.ver','devtools.sql','devtools.files',
  'rbac.ver','rbac.audit','directorio.ver','directorio.editar',
  'prediccion.ver','catalogo.ver','catalogo.editar'
) ON CONFLICT DO NOTHING;

-- CIO: Gobernanza y compliance enfocado
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'CIO' AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo','dashboard.exportar',
  'team.ver','proyectos.ver','proyectos.aprobar',
  'incidencias.ver','kanban.ver',
  'presupuestos.ver','presupuestos.ver_total','presupuestos.aprobar',
  'gobernanza.ver','gobernanza.editar','gobernanza.dashboard',
  'pmo.managers.ver','pmo.managers.crear','pmo.managers.editar',
  'warroom.ver','warroom.participar',
  'alertas.ver','alertas.gestionar',
  'compliance.ver','compliance.crear','compliance.editar','compliance.dashboard',
  'postmortem.ver','postmortem.aprobar',
  'simulacion.ver','simulacion.ejecutar',
  'documentacion.ver','documentacion.crear','documentacion.editar',
  'planes.ver','agentes.ver','agentes.metricas',
  'rbac.ver','rbac.audit','directorio.ver','directorio.editar',
  'prediccion.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- CISO: Seguridad, war room, compliance
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'CISO' AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo','dashboard.exportar',
  'team.ver','proyectos.ver','incidencias.ver','incidencias.escalar',
  'kanban.ver','presupuestos.ver',
  'gobernanza.ver','gobernanza.dashboard',
  'warroom.ver','warroom.crear','warroom.participar','warroom.cerrar',
  'alertas.ver','alertas.crear','alertas.gestionar',
  'compliance.ver','compliance.crear','compliance.editar','compliance.dashboard',
  'postmortem.ver','postmortem.crear','postmortem.aprobar',
  'simulacion.ver','simulacion.ejecutar',
  'documentacion.ver','documentacion.crear',
  'planes.ver','agentes.metricas',
  'rbac.ver','rbac.audit','directorio.ver',
  'prediccion.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- CFO: Presupuestos y financiero
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'CFO' AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo','dashboard.exportar',
  'team.ver','team.ver_salarios','proyectos.ver',
  'incidencias.ver','kanban.ver',
  'presupuestos.ver','presupuestos.crear','presupuestos.editar','presupuestos.eliminar','presupuestos.aprobar','presupuestos.ver_total',
  'gobernanza.ver','gobernanza.dashboard','pmo.managers.ver',
  'compliance.ver','compliance.dashboard',
  'documentacion.ver','planes.ver',
  'directorio.ver','prediccion.ver','catalogo.ver',
  'rbac.audit'
) ON CONFLICT DO NOTHING;

-- VP_ENGINEERING
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'VP_ENGINEERING' AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo','dashboard.exportar',
  'team.ver','team.crear','team.editar','team.asignar',
  'proyectos.ver','proyectos.crear','proyectos.editar','proyectos.aprobar',
  'incidencias.ver','incidencias.crear','incidencias.editar','incidencias.escalar',
  'kanban.ver','kanban.crear','kanban.editar','kanban.eliminar',
  'presupuestos.ver','presupuestos.ver_total',
  'gobernanza.ver','gobernanza.dashboard','pmo.managers.ver',
  'warroom.ver','warroom.crear','warroom.participar',
  'alertas.ver','alertas.crear','alertas.gestionar',
  'postmortem.ver','postmortem.crear',
  'simulacion.ver','simulacion.ejecutar',
  'documentacion.ver','documentacion.crear','documentacion.editar',
  'planes.ver','planes.crear',
  'agentes.ver','agentes.chat','agentes.metricas',
  'devtools.ver','directorio.ver','prediccion.ver','catalogo.ver','catalogo.editar'
) ON CONFLICT DO NOTHING;

-- VP_OPERATIONS
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'VP_OPERATIONS' AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo','dashboard.exportar',
  'team.ver','team.editar','team.asignar',
  'proyectos.ver','incidencias.ver','incidencias.crear','incidencias.editar','incidencias.escalar',
  'kanban.ver','kanban.crear','kanban.editar',
  'presupuestos.ver',
  'gobernanza.ver','gobernanza.dashboard','pmo.managers.ver',
  'warroom.ver','warroom.crear','warroom.participar','warroom.cerrar',
  'alertas.ver','alertas.crear','alertas.gestionar',
  'compliance.ver',
  'postmortem.ver','postmortem.crear','postmortem.aprobar',
  'simulacion.ver','simulacion.ejecutar',
  'documentacion.ver','documentacion.crear',
  'planes.ver','planes.crear','planes.eliminar',
  'agentes.ver','agentes.chat','agentes.metricas',
  'directorio.ver','prediccion.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- VP_PMO
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'VP_PMO' AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo','dashboard.exportar',
  'team.ver','team.asignar',
  'proyectos.ver','proyectos.crear','proyectos.editar','proyectos.aprobar','proyectos.pausar',
  'incidencias.ver','kanban.ver','kanban.crear','kanban.editar',
  'presupuestos.ver','presupuestos.crear','presupuestos.editar','presupuestos.ver_total','presupuestos.aprobar',
  'gobernanza.ver','gobernanza.editar','gobernanza.dashboard',
  'pmo.managers.ver','pmo.managers.crear','pmo.managers.editar',
  'warroom.ver','warroom.participar',
  'alertas.ver',
  'compliance.ver','compliance.dashboard',
  'postmortem.ver',
  'simulacion.ver','simulacion.ejecutar',
  'documentacion.ver','documentacion.crear','documentacion.editar','documentacion.eliminar',
  'planes.ver','planes.crear','planes.eliminar',
  'agentes.ver','agentes.chat','agentes.metricas',
  'directorio.ver','prediccion.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- DIRECTOR_IT
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'DIRECTOR_IT' AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo',
  'team.ver','team.crear','team.editar','team.asignar',
  'proyectos.ver','proyectos.crear','proyectos.editar',
  'incidencias.ver','incidencias.crear','incidencias.editar','incidencias.escalar',
  'kanban.ver','kanban.crear','kanban.editar',
  'presupuestos.ver',
  'gobernanza.ver','gobernanza.dashboard','pmo.managers.ver',
  'warroom.ver','warroom.participar',
  'alertas.ver','alertas.gestionar',
  'postmortem.ver','postmortem.crear',
  'documentacion.ver','documentacion.crear','documentacion.editar',
  'planes.ver','planes.crear',
  'agentes.ver','agentes.chat',
  'directorio.ver','prediccion.ver','catalogo.ver','catalogo.editar'
) ON CONFLICT DO NOTHING;

-- DIRECTOR_SEC, DIRECTOR_INFRA, DIRECTOR_DATA: similar a DIRECTOR_IT con variaciones
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code IN ('DIRECTOR_SEC','DIRECTOR_INFRA','DIRECTOR_DATA') AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo',
  'team.ver','team.editar','team.asignar',
  'proyectos.ver','incidencias.ver','incidencias.crear','incidencias.editar',
  'kanban.ver','kanban.crear','kanban.editar',
  'presupuestos.ver',
  'gobernanza.ver','gobernanza.dashboard','pmo.managers.ver',
  'warroom.ver','warroom.participar',
  'alertas.ver','alertas.gestionar',
  'compliance.ver',
  'postmortem.ver','postmortem.crear',
  'documentacion.ver','documentacion.crear',
  'planes.ver','planes.crear',
  'agentes.ver','agentes.chat',
  'directorio.ver','prediccion.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- PMO_SENIOR
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'PMO_SENIOR' AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo','dashboard.exportar',
  'team.ver','team.asignar',
  'proyectos.ver','proyectos.crear','proyectos.editar','proyectos.aprobar',
  'incidencias.ver','kanban.ver','kanban.crear','kanban.editar',
  'presupuestos.ver','presupuestos.crear','presupuestos.editar','presupuestos.ver_total',
  'gobernanza.ver','gobernanza.editar','gobernanza.dashboard',
  'pmo.managers.ver',
  'warroom.ver','warroom.participar',
  'alertas.ver',
  'compliance.ver',
  'postmortem.ver',
  'simulacion.ver',
  'documentacion.ver','documentacion.crear','documentacion.editar',
  'planes.ver','planes.crear',
  'agentes.ver','agentes.chat',
  'directorio.ver','prediccion.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- PMO_JUNIOR
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'PMO_JUNIOR' AND p.code IN (
  'dashboard.ver',
  'team.ver','team.asignar',
  'proyectos.ver','proyectos.editar',
  'incidencias.ver','kanban.ver','kanban.crear','kanban.editar',
  'presupuestos.ver',
  'gobernanza.ver','gobernanza.dashboard','pmo.managers.ver',
  'warroom.ver',
  'alertas.ver',
  'postmortem.ver',
  'documentacion.ver','documentacion.crear',
  'planes.ver','planes.crear',
  'agentes.chat',
  'directorio.ver','prediccion.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- TEAM_LEAD
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'TEAM_LEAD' AND p.code IN (
  'dashboard.ver',
  'team.ver','team.editar','team.asignar',
  'proyectos.ver',
  'incidencias.ver','incidencias.crear','incidencias.editar','incidencias.escalar',
  'kanban.ver','kanban.crear','kanban.editar',
  'presupuestos.ver',
  'gobernanza.ver',
  'warroom.ver','warroom.participar',
  'alertas.ver','alertas.gestionar',
  'postmortem.ver','postmortem.crear',
  'documentacion.ver','documentacion.crear',
  'planes.ver','planes.crear',
  'agentes.chat',
  'directorio.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- TECH_SENIOR
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'TECH_SENIOR' AND p.code IN (
  'dashboard.ver',
  'team.ver',
  'proyectos.ver',
  'incidencias.ver','incidencias.crear','incidencias.editar',
  'kanban.ver','kanban.crear','kanban.editar',
  'warroom.ver','warroom.participar',
  'alertas.ver',
  'postmortem.ver','postmortem.crear',
  'documentacion.ver','documentacion.crear',
  'planes.ver',
  'agentes.chat',
  'directorio.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- TECH_JUNIOR
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'TECH_JUNIOR' AND p.code IN (
  'dashboard.ver',
  'team.ver',
  'proyectos.ver',
  'incidencias.ver','incidencias.crear',
  'kanban.ver','kanban.crear','kanban.editar',
  'alertas.ver',
  'postmortem.ver',
  'documentacion.ver',
  'planes.ver',
  'agentes.chat',
  'directorio.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- QA_LEAD
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'QA_LEAD' AND p.code IN (
  'dashboard.ver',
  'team.ver',
  'proyectos.ver',
  'incidencias.ver','incidencias.crear','incidencias.editar',
  'kanban.ver','kanban.crear','kanban.editar',
  'compliance.ver','compliance.crear','compliance.editar','compliance.dashboard',
  'postmortem.ver','postmortem.crear','postmortem.aprobar',
  'documentacion.ver','documentacion.crear','documentacion.editar',
  'planes.ver',
  'agentes.chat',
  'directorio.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- DEVOPS_LEAD
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'DEVOPS_LEAD' AND p.code IN (
  'dashboard.ver',
  'team.ver','team.editar',
  'proyectos.ver',
  'incidencias.ver','incidencias.crear','incidencias.editar','incidencias.escalar',
  'kanban.ver','kanban.crear','kanban.editar',
  'warroom.ver','warroom.participar',
  'alertas.ver','alertas.crear','alertas.gestionar',
  'postmortem.ver','postmortem.crear',
  'documentacion.ver','documentacion.crear',
  'planes.ver','planes.crear',
  'agentes.ver','agentes.configurar','agentes.chat','agentes.metricas',
  'devtools.ver',
  'directorio.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- AUDITOR
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'AUDITOR' AND p.code IN (
  'dashboard.ver','dashboard.ejecutivo','dashboard.exportar',
  'team.ver','proyectos.ver','incidencias.ver','kanban.ver',
  'presupuestos.ver','presupuestos.ver_total',
  'gobernanza.ver','gobernanza.dashboard','pmo.managers.ver',
  'warroom.ver','alertas.ver',
  'compliance.ver','compliance.crear','compliance.editar','compliance.dashboard',
  'postmortem.ver',
  'simulacion.ver',
  'documentacion.ver',
  'planes.ver','agentes.metricas',
  'rbac.ver','rbac.audit',
  'directorio.ver','prediccion.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- OBSERVADOR
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'OBSERVADOR' AND p.code IN (
  'dashboard.ver',
  'team.ver','proyectos.ver','incidencias.ver','kanban.ver',
  'presupuestos.ver',
  'gobernanza.ver','gobernanza.dashboard',
  'alertas.ver','compliance.ver',
  'postmortem.ver','documentacion.ver','planes.ver',
  'directorio.ver','catalogo.ver'
) ON CONFLICT DO NOTHING;

-- READONLY
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'READONLY' AND p.code IN (
  'dashboard.ver','catalogo.ver','directorio.ver'
) ON CONFLICT DO NOTHING;


-- ============================================================
-- DIRECTORIO CORPORATIVO: ESTRUCTURA DE DIRECCIÓN
-- Gran empresa de IT / Consultora tecnológica financiera
-- ============================================================

-- C-LEVEL
INSERT INTO directorio_corporativo (id_directivo, nombre_completo, cargo, nivel_organizativo, area, reporta_a, email, telefono, ubicacion, bio) VALUES
('DIR-001', 'Alejandro Vidal Montero',     'CEO - Chief Executive Officer',              'C-LEVEL', 'Dirección General',       NULL,      'alejandro.vidal@cognitive-pmo.es',    '+34 691 001 001', 'Madrid HQ',       'MBA por IE Business School. 25 años liderando transformación digital en banca.'),
('DIR-002', 'Carmen Delgado Ríos',          'CTO - Chief Technology Officer',             'C-LEVEL', 'Tecnología',              'DIR-001', 'carmen.delgado@cognitive-pmo.es',      '+34 691 001 002', 'Madrid HQ',       'PhD en Computer Science. Ex-CTO de Indra. Arquitecta de la plataforma Cognitive PMO.'),
('DIR-003', 'Roberto Navarro Sáenz',        'CIO - Chief Information Officer',            'C-LEVEL', 'Sistemas de Información', 'DIR-001', 'roberto.navarro@cognitive-pmo.es',     '+34 691 001 003', 'Madrid HQ',       'CISM, CGEIT. Especialista en gobernanza TI y transformación digital bancaria.'),
('DIR-004', 'Elena Marquez Aguirre',        'CISO - Chief Information Security Officer',  'C-LEVEL', 'Ciberseguridad',          'DIR-001', 'elena.marquez@cognitive-pmo.es',       '+34 691 001 004', 'Madrid HQ',       'CISSP, CEH. Ex-directora de seguridad en BBVA. Experta en Zero Trust.'),
('DIR-005', 'Francisco Herrera Luna',       'CFO - Chief Financial Officer',              'C-LEVEL', 'Finanzas',                'DIR-001', 'francisco.herrera@cognitive-pmo.es',   '+34 691 001 005', 'Madrid HQ',       'CPA, CFA. 20 años en control financiero de empresas tecnológicas.')
ON CONFLICT (id_directivo) DO NOTHING;

-- VP (Vice Presidents)
INSERT INTO directorio_corporativo (id_directivo, nombre_completo, cargo, nivel_organizativo, area, reporta_a, email, telefono, ubicacion, bio) VALUES
('DIR-010', 'Miguel Ángel Ruiz Portillo',   'VP of Engineering',                          'VP', 'Ingeniería de Software',      'DIR-002', 'miguelangel.ruiz@cognitive-pmo.es',   '+34 691 002 001', 'Madrid HQ',       'MSc en Software Engineering. Lidera 80+ ingenieros en 4 equipos de desarrollo.'),
('DIR-011', 'Patricia López de la Fuente',  'VP of Operations (IT Ops)',                  'VP', 'Operaciones IT',              'DIR-002', 'patricia.lopez@cognitive-pmo.es',      '+34 691 002 002', 'Barcelona Hub',   'ITIL Master, SRE. Responsable de SLA 99.95% en producción bancaria.'),
('DIR-012', 'Gonzalo Fernández-Vega',       'VP of PMO',                                  'VP', 'PMO Corporativa',             'DIR-003', 'gonzalo.fernandez@cognitive-pmo.es',   '+34 691 002 003', 'Madrid HQ',       'PMP, PgMP, SAFe SPC. Gestión del portfolio de 46+ proyectos estratégicos.')
ON CONFLICT (id_directivo) DO NOTHING;

-- DIRECTORES
INSERT INTO directorio_corporativo (id_directivo, nombre_completo, cargo, nivel_organizativo, area, reporta_a, email, telefono, ubicacion, bio) VALUES
('DIR-020', 'Laura Sanz Bermejo',           'Directora de Desarrollo Backend',            'DIRECTOR', 'Backend Engineering',     'DIR-010', 'laura.sanz@cognitive-pmo.es',          '+34 691 003 001', 'Madrid HQ',       'Arquitecta principal. Java, Python, microservicios. 15 años en banca digital.'),
('DIR-021', 'Sergio Morales Pinto',         'Director de Desarrollo Frontend',            'DIRECTOR', 'Frontend Engineering',    'DIR-010', 'sergio.morales@cognitive-pmo.es',      '+34 691 003 002', 'Madrid HQ',       'Líder de UX Engineering. React, Angular, design systems.'),
('DIR-022', 'Natalia Campos Rivero',        'Directora de QA & Testing',                  'DIRECTOR', 'Quality Assurance',       'DIR-010', 'natalia.campos@cognitive-pmo.es',      '+34 691 003 003', 'Barcelona Hub',   'ISTQB Advanced. Automatización de pruebas y CI/CD quality gates.'),
('DIR-023', 'Javier Iglesias Roca',         'Director de Infraestructura & Redes',        'DIRECTOR', 'Infraestructura',         'DIR-011', 'javier.iglesias@cognitive-pmo.es',     '+34 691 003 004', 'Madrid CPD',      'CCIE, CCDA. Arquitecto de red de los Data Centers Madrid y Barcelona.'),
('DIR-024', 'Marta Fuentes Escobar',        'Directora de Seguridad Operativa',           'DIRECTOR', 'Seguridad IT',            'DIR-004', 'marta.fuentes@cognitive-pmo.es',       '+34 691 003 005', 'Madrid HQ',       'OSCP, GIAC. Gestión de SOC 24/7 y respuesta a incidentes.'),
('DIR-025', 'Óscar Blanco Heredia',         'Director de Datos & BBDD',                   'DIRECTOR', 'Data Engineering',        'DIR-011', 'oscar.blanco@cognitive-pmo.es',        '+34 691 003 006', 'Madrid CPD',      'Oracle ACE. DBA senior con expertise en PostgreSQL, Oracle, MongoDB.'),
('DIR-026', 'Ana Belén Gutiérrez Palacios', 'Directora de DevOps & SRE',                  'DIRECTOR', 'DevOps',                  'DIR-010', 'anabelen.gutierrez@cognitive-pmo.es',  '+34 691 003 007', 'Barcelona Hub',   'CKA, AWS SA Pro. Kubernetes, Terraform, GitOps.'),
('DIR-027', 'Ricardo Soto Mendoza',         'Director de Soporte & Service Desk',         'DIRECTOR', 'Soporte IT',              'DIR-011', 'ricardo.soto@cognitive-pmo.es',        '+34 691 003 008', 'Madrid HQ',       'HDI Support Center Director. Gestión de 40+ técnicos N1-N2.'),
('DIR-028', 'Beatriz Castaño Villar',       'Directora de Windows & Sistemas',            'DIRECTOR', 'Sistemas Windows',        'DIR-011', 'beatriz.castano@cognitive-pmo.es',     '+34 691 003 009', 'Madrid HQ',       'MCSE, Azure Expert. Active Directory y ecosistema Microsoft corporativo.')
ON CONFLICT (id_directivo) DO NOTHING;

-- SUBDIRECTORES / GERENTES
INSERT INTO directorio_corporativo (id_directivo, nombre_completo, cargo, nivel_organizativo, area, reporta_a, email, telefono, ubicacion, bio) VALUES
('DIR-030', 'Pablo Rivas Camacho',          'Gerente de Proyecto - Infraestructura',      'GERENTE', 'PMO - Infraestructura',   'DIR-012', 'pablo.rivas@cognitive-pmo.es',         '+34 691 004 001', 'Madrid HQ',       'PMP. Gestión de proyectos de red y Data Center.'),
('DIR-031', 'Cristina Vega Salinas',        'Gerente de Proyecto - Aplicaciones',         'GERENTE', 'PMO - Aplicaciones',      'DIR-012', 'cristina.vega@cognitive-pmo.es',       '+34 691 004 002', 'Madrid HQ',       'PMP, CSM. Proyectos de desarrollo de aplicaciones core banking.'),
('DIR-032', 'Daniel Prieto Gallardo',       'Gerente de Proyecto - Seguridad',            'GERENTE', 'PMO - Seguridad',         'DIR-012', 'daniel.prieto@cognitive-pmo.es',       '+34 691 004 003', 'Madrid HQ',       'PMP, CISSP. Proyectos de compliance y ciberseguridad.'),
('DIR-033', 'Lucía Romero Ibarra',          'Gerente de Proyecto - Digital',              'GERENTE', 'PMO - Digital',           'DIR-012', 'lucia.romero@cognitive-pmo.es',        '+34 691 004 004', 'Barcelona Hub',   'PMP, SAFe. Transformación digital y proyectos de IA.'),
('DIR-034', 'Alberto Lozano Mejía',         'Subdirector de NOC',                         'SUBDIRECTOR', 'NOC',                 'DIR-023', 'alberto.lozano@cognitive-pmo.es',      '+34 691 004 005', 'Madrid CPD',      'NOC Manager. Monitorización 24/7 y gestión de alertas.'),
('DIR-035', 'Inés García-Cano Duarte',      'Subdirectora de SOC',                        'SUBDIRECTOR', 'SOC',                 'DIR-024', 'ines.garciacano@cognitive-pmo.es',     '+34 691 004 006', 'Madrid HQ',       'SOC Manager. Threat hunting y análisis de incidentes de seguridad.')
ON CONFLICT (id_directivo) DO NOTHING;

-- COORDINADORES / JEFES DE EQUIPO (conectan con los FTEs)
INSERT INTO directorio_corporativo (id_directivo, nombre_completo, cargo, nivel_organizativo, area, reporta_a, email, telefono, ubicacion, bio) VALUES
('DIR-040', 'Marcos Morales Guerrero',      'Jefe de Equipo - Soporte N1/N2',             'JEFE_EQUIPO', 'Soporte IT',          'DIR-027', 'marcos.morales@cognitive-pmo.es',      '+34 691 005 001', 'Madrid HQ',       'Coordina equipo de soporte de primer y segundo nivel.'),
('DIR-041', 'Isabel Álvarez Calvo',         'Jefa de Equipo - Redes',                     'JEFE_EQUIPO', 'Redes',               'DIR-023', 'isabel.alvarez@cognitive-pmo.es',      '+34 691 005 002', 'Madrid CPD',      'Coordinadora del equipo de ingeniería de redes.'),
('DIR-042', 'Olga Méndez Ramos',            'Jefa de Equipo - DevOps',                    'JEFE_EQUIPO', 'DevOps',              'DIR-026', 'olga.mendez@cognitive-pmo.es',         '+34 691 005 003', 'Barcelona Hub',   'Tech Lead DevOps. Kubernetes, CI/CD, IaC.'),
('DIR-043', 'Marina Nieto Calvo',           'Jefa de Equipo - Backend',                   'JEFE_EQUIPO', 'Backend Engineering', 'DIR-020', 'marina.nieto@cognitive-pmo.es',        '+34 691 005 004', 'Madrid HQ',       'Tech Lead Backend. APIs, microservicios, Python/Java.'),
('DIR-044', 'Raquel Sánchez Blanco',        'Jefa de Equipo - Backend Senior',            'JEFE_EQUIPO', 'Backend Engineering', 'DIR-020', 'raquel.sanchez@cognitive-pmo.es',      '+34 691 005 005', 'Madrid HQ',       'Arquitecta de software senior. Patrones de diseño y DDD.'),
('DIR-045', 'Felipe Ortiz Cruz',            'Jefe de Equipo - Soporte N3/N4',             'JEFE_EQUIPO', 'Soporte IT',          'DIR-027', 'felipe.ortiz@cognitive-pmo.es',        '+34 691 005 006', 'Madrid HQ',       'Coordinador de soporte avanzado y escalaciones.'),
('DIR-046', 'Tomás Soler Ortega',           'Jefe de Equipo - Soporte Especializado',     'JEFE_EQUIPO', 'Soporte IT',          'DIR-027', 'tomas.soler@cognitive-pmo.es',         '+34 691 005 007', 'Madrid HQ',       'Especialista en soporte de aplicaciones críticas bancarias.'),
('DIR-047', 'Diana Sánchez Alonso',         'Jefa de Equipo - Seguridad',                 'JEFE_EQUIPO', 'Seguridad IT',        'DIR-024', 'diana.sanchez@cognitive-pmo.es',       '+34 691 005 008', 'Madrid HQ',       'Pentesting y gestión de vulnerabilidades.')
ON CONFLICT (id_directivo) DO NOTHING;


-- ============================================================
-- USUARIOS DEL SISTEMA
-- Generados a partir de: directivos + FTEs (150 técnicos)
-- Contraseña temporal: 12345 (hash SHA-256 simple para demo)
-- ============================================================

-- Hash de '12345' = '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5'
-- Hash de 'admin' = '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'

-- SUPERADMIN
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, departamento, cargo, activo, requiere_cambio_password)
SELECT 'admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
       'Administrador del Sistema',
       r.id_role, 'IT - Plataforma', 'System Administrator', TRUE, FALSE
FROM rbac_roles r WHERE r.code = 'SUPERADMIN'
ON CONFLICT (email) DO NOTHING;

-- DIRECTIVOS: C-Level
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-001' AND r.code = 'CEO'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-002' AND r.code = 'CTO'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-003' AND r.code = 'CIO'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-004' AND r.code = 'CISO'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-005' AND r.code = 'CFO'
ON CONFLICT (email) DO NOTHING;

-- VPs
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-010' AND r.code = 'VP_ENGINEERING'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-011' AND r.code = 'VP_OPERATIONS'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-012' AND r.code = 'VP_PMO'
ON CONFLICT (email) DO NOTHING;

-- DIRECTORES
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo IN ('DIR-020','DIR-021') AND r.code = 'DIRECTOR_IT'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-022' AND r.code = 'QA_LEAD'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-023' AND r.code = 'DIRECTOR_INFRA'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-024' AND r.code = 'DIRECTOR_SEC'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-025' AND r.code = 'DIRECTOR_DATA'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo = 'DIR-026' AND r.code = 'DEVOPS_LEAD'
ON CONFLICT (email) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo IN ('DIR-027','DIR-028') AND r.code = 'DIRECTOR_IT'
ON CONFLICT (email) DO NOTHING;

-- GERENTES PMO
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo IN ('DIR-030','DIR-031','DIR-032','DIR-033') AND r.code = 'PMO_SENIOR'
ON CONFLICT (email) DO NOTHING;

-- SUBDIRECTORES NOC/SOC
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo IN ('DIR-034','DIR-035') AND r.code = 'DIRECTOR_IT'
ON CONFLICT (email) DO NOTHING;

-- JEFES DE EQUIPO (son FTEs N4 promovidos)
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_directivo, departamento, cargo, activo)
SELECT d.email, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       d.nombre_completo, r.id_role, d.id_directivo, d.area, d.cargo, TRUE
FROM directorio_corporativo d, rbac_roles r
WHERE d.id_directivo IN ('DIR-040','DIR-041','DIR-042','DIR-043','DIR-044','DIR-045','DIR-046','DIR-047')
  AND r.code = 'TEAM_LEAD'
ON CONFLICT (email) DO NOTHING;


-- ============================================================
-- USUARIOS FTE: Técnicos (150 personas)
-- Email generado como: nombre.apellido@cognitive-pmo.es
-- Rol basado en nivel: N3-N4 = TECH_SENIOR, N1-N2 = TECH_JUNIOR
-- Los que son jefes de equipo ya se insertaron arriba
-- ============================================================

-- Formato email: nombre.apellido1@cognitive-pmo.es (acentos normalizados con TRANSLATE)

-- N3-N4 = TECH_SENIOR (que no son ya TEAM_LEAD)
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_recurso, departamento, cargo, activo)
SELECT
  LOWER(TRANSLATE(
    SPLIT_PART(s.nombre, ' ', 1) || '.' || SPLIT_PART(s.nombre, ' ', 2),
    'áéíóúÁÉÍÓÚñÑüÜ', 'aeiouAEIOUnNuU'
  )) || '@cognitive-pmo.es',
  '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
  s.nombre,
  r.id_role,
  s.id_recurso,
  s.silo_especialidad,
  'Técnico ' || s.nivel || ' - ' || s.silo_especialidad,
  TRUE
FROM pmo_staff_skills s, rbac_roles r
WHERE s.nivel IN ('N3','N4') AND r.code = 'TECH_SENIOR'
  AND s.nombre NOT IN (
    SELECT dc.nombre_completo FROM directorio_corporativo dc
  )
ON CONFLICT (email) DO NOTHING;

-- N1-N2 = TECH_JUNIOR
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, id_recurso, departamento, cargo, activo)
SELECT
  LOWER(TRANSLATE(
    SPLIT_PART(s.nombre, ' ', 1) || '.' || SPLIT_PART(s.nombre, ' ', 2),
    'áéíóúÁÉÍÓÚñÑüÜ', 'aeiouAEIOUnNuU'
  )) || '@cognitive-pmo.es',
  '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
  s.nombre,
  r.id_role,
  s.id_recurso,
  s.silo_especialidad,
  'Técnico ' || s.nivel || ' - ' || s.silo_especialidad,
  TRUE
FROM pmo_staff_skills s, rbac_roles r
WHERE s.nivel IN ('N1','N2') AND r.code = 'TECH_JUNIOR'
  AND s.nombre NOT IN (
    SELECT dc.nombre_completo FROM directorio_corporativo dc
  )
ON CONFLICT (email) DO NOTHING;

-- Auditor externo
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, departamento, cargo, activo)
SELECT 'auditor.externo@cognitive-pmo.es', '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       'Auditor Externo - Deloitte',
       r.id_role, 'Auditoría Externa', 'Auditor de Sistemas', TRUE
FROM rbac_roles r WHERE r.code = 'AUDITOR'
ON CONFLICT (email) DO NOTHING;

-- Observador / Stakeholder
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, departamento, cargo, activo)
SELECT 'stakeholder@cognitive-pmo.es', '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
       'Comité de Dirección',
       r.id_role, 'Dirección General', 'Stakeholder Ejecutivo', TRUE
FROM rbac_roles r WHERE r.code = 'OBSERVADOR'
ON CONFLICT (email) DO NOTHING;

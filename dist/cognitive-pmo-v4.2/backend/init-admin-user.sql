-- ============================================================
-- Cognitive PMO - Init Admin User (Idempotent)
-- Creates SUPERADMIN role and admin user with all permissions
-- ============================================================

-- 1. Create SUPERADMIN role
INSERT INTO rbac_roles (code, nombre, descripcion, nivel_jerarquico, color, icono, activo)
VALUES ('SUPERADMIN', 'Super Administrador', 'Acceso total al sistema', 0, '#EF4444', 'crown', TRUE)
ON CONFLICT (code) DO NOTHING;

-- 2. Create admin user (password: admin -> sha256 hash)
INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, departamento, cargo, activo, requiere_cambio_password)
SELECT 'admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
       'Administrador del Sistema', r.id_role, 'IT - Plataforma', 'System Administrator', TRUE, FALSE
FROM rbac_roles r WHERE r.code = 'SUPERADMIN'
ON CONFLICT (email) DO UPDATE SET
    password_hash = '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
    activo = TRUE,
    requiere_cambio_password = FALSE;

-- 3. Ensure SUPERADMIN has ALL permissions
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'SUPERADMIN'
ON CONFLICT DO NOTHING;

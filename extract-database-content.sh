#!/bin/bash
# ============================================================
# Cognitive PMO - Extract Database Content
# Exports ALL data (INSERT statements) from cognitive_pmo database
# Output: BD_cajamar_v4.sql
# ============================================================

set -e

# Database connection params
DB_HOST="${DB_HOST:-192.168.1.49}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-cognitive_pmo}"
DB_USER="${DB_USER:-jose_admin}"

OUTPUT_FILE="BD_cajamar_v4.sql"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "╔══════════════════════════════════════════════════════╗"
echo "║   Cognitive PMO - Database Content Extractor         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  Host: $DB_HOST:$DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Output: $OUTPUT_FILE"
echo ""

# Add header comment
cat > "$OUTPUT_FILE" << HEADER
-- ============================================================
-- Cognitive PMO - Database Content Export
-- Version: v4 (Cajamar)
-- Date: $TIMESTAMP
-- Source: $DB_HOST:$DB_PORT/$DB_NAME
-- Format: INSERT statements (data only)
-- ============================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

HEADER

echo "[1/3] Exporting data from all tables..."

# Export data only with column inserts
PGPASSWORD="${DB_PASSWORD:-Seacaboelabuso_0406}" pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --data-only \
    --inserts \
    --column-inserts \
    --no-owner \
    --no-privileges \
    --no-comments \
    >> "$OUTPUT_FILE"

echo "[2/3] Adding admin user safety net..."

cat >> "$OUTPUT_FILE" << 'ADMIN_SQL'

-- ============================================================
-- Ensure admin user exists after data load
-- ============================================================

INSERT INTO rbac_roles (code, nombre, descripcion, nivel_jerarquico, color, icono, activo)
VALUES ('SUPERADMIN', 'Super Administrador', 'Acceso total al sistema', 0, '#EF4444', 'crown', TRUE)
ON CONFLICT (code) DO NOTHING;

INSERT INTO rbac_usuarios (email, password_hash, nombre_completo, id_role, departamento, cargo, activo, requiere_cambio_password)
SELECT 'admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
       'Administrador del Sistema', r.id_role, 'IT - Plataforma', 'System Administrator', TRUE, FALSE
FROM rbac_roles r WHERE r.code = 'SUPERADMIN'
ON CONFLICT (email) DO UPDATE SET
    password_hash = '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
    activo = TRUE,
    requiere_cambio_password = FALSE;

-- Ensure SUPERADMIN has ALL permissions
INSERT INTO rbac_role_permisos (id_role, id_permiso)
SELECT r.id_role, p.id_permiso
FROM rbac_roles r, rbac_permisos p
WHERE r.code = 'SUPERADMIN'
ON CONFLICT DO NOTHING;
ADMIN_SQL

echo "[3/3] Done!"
echo ""

SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
LINES=$(wc -l < "$OUTPUT_FILE")
INSERTS=$(grep -ci "^INSERT" "$OUTPUT_FILE" || true)

echo "  Output: $OUTPUT_FILE"
echo "  Size: $SIZE"
echo "  Lines: $LINES"
echo "  INSERT statements: $INSERTS"
echo ""
echo "To load this file into a clean database:"
echo "  psql -h <host> -U <user> -d cognitive_pmo -f $OUTPUT_FILE"

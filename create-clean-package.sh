#!/bin/bash
# ============================================================
# Cognitive PMO - Create Clean Deployment Package
# Creates a self-contained tar.gz with PostgreSQL included
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

VERSION="v32"
PACKAGE_NAME="cognitive-pmo-${VERSION}-clean"
TEMP_DIR="/tmp/${PACKAGE_NAME}"
OUTPUT_FILE="${PACKAGE_NAME}.tar.gz"

# Database connection for schema export
DB_HOST="${DB_HOST:-192.168.1.49}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-cognitive_pmo}"
DB_USER="${DB_USER:-jose_admin}"

echo "╔══════════════════════════════════════════════════════╗"
echo "║   Cognitive PMO - Clean Package Creator              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  Version: $VERSION"
echo "  Output: $OUTPUT_FILE"
echo ""

# Clean up any previous attempt
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

echo "[1/7] Exporting schema from database..."

PGPASSWORD="${DB_PASSWORD:-Seacaboelabuso_0406}" pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --schema-only \
    --no-owner \
    --no-privileges \
    --no-comments \
    > "$TEMP_DIR/schema-only.sql" 2>/dev/null || {
        echo "  WARNING: Could not export schema from live database."
        echo "  Will use existing SQL files instead."
        touch "$TEMP_DIR/schema-only.sql"
    }

echo "[2/7] Copying backend..."
mkdir -p "$TEMP_DIR/backend"
cp -r "${SCRIPT_DIR}/backend/"*.py "$TEMP_DIR/backend/" 2>/dev/null || true
cp "${SCRIPT_DIR}/backend/requirements.txt" "$TEMP_DIR/backend/"
cp "${SCRIPT_DIR}/backend/Dockerfile" "$TEMP_DIR/backend/"

# Copy schema SQL files (not data seeds)
cp "${SCRIPT_DIR}/backend/init.sql" "$TEMP_DIR/backend/" 2>/dev/null || true
cp "${SCRIPT_DIR}/backend/rbac_schema.sql" "$TEMP_DIR/backend/" 2>/dev/null || true
cp "${SCRIPT_DIR}/backend/cmdb_schema.sql" "$TEMP_DIR/backend/" 2>/dev/null || true
cp "${SCRIPT_DIR}/backend/cmdb_costes_schema.sql" "$TEMP_DIR/backend/" 2>/dev/null || true
cp "${SCRIPT_DIR}/backend/init-admin-user.sql" "$TEMP_DIR/backend/" 2>/dev/null || true

# Explicitly exclude data seed files
rm -f "$TEMP_DIR/backend/cmdb_seed_extra.sql"
rm -f "$TEMP_DIR/backend/cmdb_ips_seed.sql"

echo "[3/7] Copying frontend..."
mkdir -p "$TEMP_DIR/frontend"
cp -r "${SCRIPT_DIR}/frontend/"* "$TEMP_DIR/frontend/" 2>/dev/null || true

echo "[4/7] Copying docker-compose (clean version with PostgreSQL)..."
cp "${SCRIPT_DIR}/docker-compose.clean.yml" "$TEMP_DIR/docker-compose.yml"

echo "[5/7] Creating .env file..."
cat > "$TEMP_DIR/.env" << 'ENV'
DB_HOST=db
DB_PORT=5432
DB_NAME=cognitive_pmo
DB_USER=pmo_admin
DB_PASSWORD=CognitivePMO_2025!
JWT_SECRET=cognitive-pmo-rbac-secret-key-2026-change-in-prod
ENV

echo "[6/7] Creating deploy script..."
cat > "$TEMP_DIR/deploy.sh" << 'DEPLOY'
#!/bin/bash
# Cognitive PMO - Quick Deploy Script
set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║   Cognitive PMO - Deployment                         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check docker
if ! command -v docker &>/dev/null; then
    echo "ERROR: Docker is not installed."
    exit 1
fi

echo "[1/4] Building and starting services..."
docker compose up -d --build

echo "[2/4] Waiting for database..."
for i in $(seq 1 30); do
    if docker compose exec -T db pg_isready -U pmo_admin -d cognitive_pmo &>/dev/null; then
        echo "  Database is ready!"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

echo "[3/4] Waiting for API..."
for i in $(seq 1 20); do
    if curl -s http://localhost:8088/health &>/dev/null; then
        echo "  API is ready!"
        break
    fi
    echo "  Waiting... ($i/20)"
    sleep 2
done

echo "[4/4] Status:"
docker compose ps

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Cognitive PMO is running!                          ║"
echo "║                                                      ║"
echo "║   Frontend: http://localhost:3030                    ║"
echo "║   API:      http://localhost:8088                    ║"
echo "║                                                      ║"
echo "║   Login: admin / admin                               ║"
echo "║                                                      ║"
echo "║   To load data, use DEV > Database Loader in the UI ║"
echo "╚══════════════════════════════════════════════════════╝"
DEPLOY
chmod +x "$TEMP_DIR/deploy.sh"

echo "[7/7] Creating tar.gz package..."
cd /tmp
tar czf "${SCRIPT_DIR}/${OUTPUT_FILE}" "$PACKAGE_NAME"
cd - > /dev/null

# Clean up temp
rm -rf "$TEMP_DIR"

SIZE=$(du -h "${SCRIPT_DIR}/${OUTPUT_FILE}" | cut -f1)
echo ""
echo "  Package created: $OUTPUT_FILE ($SIZE)"
echo ""
echo "  To deploy on a new machine:"
echo "    tar xzf $OUTPUT_FILE"
echo "    cd $PACKAGE_NAME"
echo "    ./deploy.sh"

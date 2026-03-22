#!/bin/bash
# ============================================================
# Cognitive PMO - Deploy from Clean Package
# Extracts tar.gz and runs docker compose
# ============================================================

set -e

PACKAGE_FILE="${1:-cognitive-pmo-v32-clean.tar.gz}"

echo "╔══════════════════════════════════════════════════════╗"
echo "║   Cognitive PMO - Clean Deployment                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check package exists
if [ ! -f "$PACKAGE_FILE" ]; then
    echo "ERROR: Package file not found: $PACKAGE_FILE"
    echo "Usage: $0 [package-file.tar.gz]"
    exit 1
fi

# Check docker
if ! command -v docker &>/dev/null; then
    echo "ERROR: Docker is not installed."
    exit 1
fi

echo "[1/5] Extracting package..."
tar xzf "$PACKAGE_FILE"

# Find the extracted directory
DEPLOY_DIR=$(tar tzf "$PACKAGE_FILE" | head -1 | cut -d/ -f1)
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "ERROR: Could not find extracted directory: $DEPLOY_DIR"
    exit 1
fi

cd "$DEPLOY_DIR"
echo "  Extracted to: $(pwd)"

echo "[2/5] Starting services with Docker Compose..."
docker compose up -d --build

echo "[3/5] Waiting for database to be ready..."
for i in $(seq 1 30); do
    if docker compose exec -T db pg_isready -U pmo_admin -d cognitive_pmo &>/dev/null; then
        echo "  Database is ready!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  WARNING: Database may not be ready yet."
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

echo "[4/5] Waiting for API to be ready..."
for i in $(seq 1 20); do
    if curl -s http://localhost:8088/health &>/dev/null; then
        echo "  API is ready!"
        break
    fi
    if [ "$i" -eq 20 ]; then
        echo "  WARNING: API may not be ready yet."
    fi
    echo "  Waiting... ($i/20)"
    sleep 2
done

echo "[5/5] Service status:"
docker compose ps

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Deployment Complete!                               ║"
echo "║                                                      ║"
echo "║   Frontend: http://localhost:3030                    ║"
echo "║   API:      http://localhost:8088                    ║"
echo "║                                                      ║"
echo "║   Login: admin / admin                               ║"
echo "║                                                      ║"
echo "║   To load production data:                           ║"
echo "║   1. Go to DEV tab > Database Loader                 ║"
echo "║   2. Upload your BD_cajamar_v4.sql file              ║"
echo "║   3. Click 'Cargar en Base de Datos'                 ║"
echo "╚══════════════════════════════════════════════════════╝"

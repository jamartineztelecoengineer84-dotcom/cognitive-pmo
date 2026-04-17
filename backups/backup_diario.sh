#!/bin/bash
# Backup diario de PostgreSQL — Cognitive PMO
# Retención: 7 días · Cron: 03:00 UTC

BACKUP_DIR="/root/cognitive-pmo/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/cognitive_pmo_$TIMESTAMP.sql.gz"
RETENTION_DAYS=7

PG_CONTAINER=$(docker ps --filter "name=postgres" --format "{{.Names}}" | head -1)
if [ -z "$PG_CONTAINER" ]; then echo "ERROR: No PostgreSQL container"; exit 1; fi

echo "[$(date '+%d/%m/%Y %H:%M')] Backup → $BACKUP_FILE"

docker exec "$PG_CONTAINER" pg_dump \
    -U jose_admin -d cognitive_pmo \
    --no-owner --no-privileges --format=plain \
    | gzip > "$BACKUP_FILE"

SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || echo 0)
if [ "$SIZE" -gt 1000 ]; then
    TAMANO=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "  OK: $TAMANO"
    BORRADOS=$(find "$BACKUP_DIR" -name "cognitive_pmo_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
    echo "  Limpieza: $BORRADOS antiguos eliminados"
    echo "BACKUP_OK"
else
    echo "ERROR: Backup vacío"
    docker exec cognitive-pmo-api-1 python -c "
from monitor import notificar_error
notificar_error('database', 'backup_fail', 'Backup diario falló o fichero vacío. Revisar manualmente.', endpoint='cron/backup')
" 2>/dev/null || true
    exit 1
fi

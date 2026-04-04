#!/bin/bash
# ═══ Cognitive PMO v4.2 — Carga de datos ═══
# Ejecutar DESPUES de "docker compose up -d" cuando la BD este corriendo
#
# Uso:
#   ./cargar_datos.sh          → Carga TODOS los datos
#   ./cargar_datos.sh tabla    → Carga solo una tabla especifica
#

set -e

CONTAINER=$(docker compose ps -q db)
if [ -z "$CONTAINER" ]; then
  echo "El contenedor de PostgreSQL no esta corriendo."
  echo "   Ejecuta primero: docker compose up -d"
  exit 1
fi

# Esperar a que PostgreSQL este listo
echo "Esperando a PostgreSQL..."
until docker exec $CONTAINER pg_isready -U ${POSTGRES_USER:-jose_admin} > /dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL listo"

if [ -n "$1" ]; then
  # Carga selectiva de una tabla
  FILE="db_tables/$1.sql"
  if [ -f "$FILE" ]; then
    echo "Cargando tabla: $1"
    docker exec -i $CONTAINER psql -U ${POSTGRES_USER:-jose_admin} -d ${POSTGRES_DB:-cognitive_pmo} < "$FILE"
    echo "Tabla $1 cargada"
  else
    echo "No existe: $FILE"
    echo "   Tablas disponibles:"
    ls db_tables/*.sql | sed 's/db_tables\//  /;s/\.sql//'
    exit 1
  fi
else
  # Carga completa
  echo "Cargando TODOS los datos..."
  docker exec -i $CONTAINER psql -U ${POSTGRES_USER:-jose_admin} -d ${POSTGRES_DB:-cognitive_pmo} < db_data.sql
  echo "Todos los datos cargados"
fi

# Verificar
echo ""
echo "=== Verificacion ==="
docker exec $CONTAINER psql -U ${POSTGRES_USER:-jose_admin} -d ${POSTGRES_DB:-cognitive_pmo} -c "
SELECT 'Tablas' as tipo, COUNT(*)::text as total FROM information_schema.tables WHERE table_schema='public'
UNION ALL
SELECT 'Tecnicos', COUNT(*)::text FROM pmo_staff_skills
UNION ALL
SELECT 'Proyectos', COUNT(*)::text FROM cartera_build
UNION ALL
SELECT 'Incidencias catalogo', COUNT(*)::text FROM catalogo_incidencias
UNION ALL
SELECT 'CMDB activos', COUNT(*)::text FROM cmdb_activos
ORDER BY tipo;
"

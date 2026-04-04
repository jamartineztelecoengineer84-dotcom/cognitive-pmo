-- ============================================================
-- COGNITIVE PMO - AGENTS MIGRATIONS (Fase 1)
-- Extensiones, índices y campos para el módulo de agentes IA
-- ============================================================

-- Extensión para búsqueda por similaridad en catálogo
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Índice para búsqueda en catálogo de incidencias
CREATE INDEX IF NOT EXISTS idx_catalogo_trgm
ON catalogo_incidencias USING gin (incidencia gin_trgm_ops);

-- Campos nuevos en gobernanza_transacciones
ALTER TABLE gobernanza_transacciones
  ADD COLUMN IF NOT EXISTS pending_sync jsonb DEFAULT '[]'::jsonb;
ALTER TABLE gobernanza_transacciones
  ADD COLUMN IF NOT EXISTS depth integer DEFAULT 1;
ALTER TABLE gobernanza_transacciones
  ADD COLUMN IF NOT EXISTS correlation_id character varying;
ALTER TABLE gobernanza_transacciones
  ADD COLUMN IF NOT EXISTS retry_count integer DEFAULT 0;
ALTER TABLE gobernanza_transacciones
  ADD COLUMN IF NOT EXISTS sync_status character varying DEFAULT 'PENDIENTE';

-- Índice para sync worker
CREATE INDEX IF NOT EXISTS idx_gov_tx_sync
ON gobernanza_transacciones (sync_status)
WHERE sync_status IN ('PENDIENTE', 'EN_PROCESO');

-- Índice para task advisor worker
CREATE INDEX IF NOT EXISTS idx_kanban_recent
ON kanban_tareas (fecha_creacion DESC);

-- Pipeline sessions (estado persistente de pipelines BUILD)
CREATE TABLE IF NOT EXISTS pipeline_sessions (
  id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
  nombre_proyecto VARCHAR NOT NULL DEFAULT '',
  estado VARCHAR DEFAULT 'EN_PROGRESO',
  pausa_actual INTEGER DEFAULT 0,
  pipeline_data JSONB NOT NULL DEFAULT '{}',
  business_case JSONB DEFAULT '{}',
  session_id VARCHAR DEFAULT '',
  tiempo_acumulado_ms INTEGER DEFAULT 0,
  coste_acumulado NUMERIC DEFAULT 0,
  agentes_completados JSONB DEFAULT '[]',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_sessions_estado
ON pipeline_sessions (estado, updated_at DESC);

-- ============================================
-- Tech Dashboard Tables — Cognitive PMO
-- Fase 0: Schema para dashboard de técnicos
-- ============================================

-- 1. Salas de chat vinculadas a incidencias o tareas de proyecto
CREATE TABLE IF NOT EXISTS tech_chat_salas (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('run','build')),
    id_referencia VARCHAR(30) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    activa BOOLEAN DEFAULT TRUE,
    UNIQUE(tipo, id_referencia)
);

-- 2. Mensajes de chat
CREATE TABLE IF NOT EXISTS tech_chat_mensajes (
    id SERIAL PRIMARY KEY,
    id_sala INTEGER NOT NULL REFERENCES tech_chat_salas(id) ON DELETE CASCADE,
    id_autor VARCHAR(20) NOT NULL,
    rol_autor VARCHAR(20) NOT NULL CHECK (rol_autor IN ('tecnico','gobernador','pm','agente')),
    mensaje TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chat_msg_sala_ts ON tech_chat_mensajes(id_sala, created_at DESC);

-- 3. Log de comandos de terminal
CREATE TABLE IF NOT EXISTS tech_terminal_log (
    id SERIAL PRIMARY KEY,
    id_recurso VARCHAR(20) NOT NULL,
    sesion_id UUID NOT NULL DEFAULT gen_random_uuid(),
    servidor VARCHAR(100) NOT NULL,
    comando TEXT NOT NULL,
    salida TEXT,
    vinculado_tipo VARCHAR(10) CHECK (vinculado_tipo IN ('run','build')),
    vinculado_id VARCHAR(30),
    ip_origen INET,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_terminal_recurso_ts ON tech_terminal_log(id_recurso, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_terminal_sesion ON tech_terminal_log(sesion_id);

-- 4. Valoración mensual de rendimiento
CREATE TABLE IF NOT EXISTS tech_valoracion_mensual (
    id SERIAL PRIMARY KEY,
    id_recurso VARCHAR(20) NOT NULL,
    mes DATE NOT NULL,
    total_incidencias INTEGER DEFAULT 0,
    incidencias_en_sla INTEGER DEFAULT 0,
    pct_sla NUMERIC(5,2) DEFAULT 0,
    total_tareas INTEGER DEFAULT 0,
    story_points_completados INTEGER DEFAULT 0,
    velocidad_media_sp NUMERIC(5,2) DEFAULT 0,
    tasa_reopen NUMERIC(5,2) DEFAULT 0,
    puntuacion NUMERIC(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(id_recurso, mes)
);

-- Añadir columna rol a pmo_staff_skills si no existe
ALTER TABLE pmo_staff_skills ADD COLUMN IF NOT EXISTS rol VARCHAR(50);

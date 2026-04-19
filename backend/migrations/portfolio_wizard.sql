-- Portfolio Wizard Migration — ARQ-04 Portfolio Prioritization
-- Ejecutar en todos los schemas: primitiva, sc_iberico, sc_litoral, sc_norte, sc_piloto0

CREATE TABLE IF NOT EXISTS portfolio_evaluations (
    id SERIAL PRIMARY KEY,
    eval_name VARCHAR(200) NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    modified_at TIMESTAMPTZ DEFAULT NOW(),
    created_by INTEGER,
    objectives JSONB NOT NULL DEFAULT '[]',
    committee JSONB NOT NULL DEFAULT '[]',
    ahp_votes JSONB NOT NULL DEFAULT '{}',
    obj_weights JSONB NOT NULL DEFAULT '[]',
    crit_weights JSONB NOT NULL DEFAULT '{}',
    kt_scores JSONB NOT NULL DEFAULT '{}',
    solver_config JSONB NOT NULL DEFAULT '{}',
    solver_result JSONB NOT NULL DEFAULT '[]',
    project_count INTEGER,
    total_score NUMERIC(8,2),
    total_cost NUMERIC(12,2),
    changelog TEXT[] DEFAULT ARRAY['Evaluación inicial'],
    history JSONB DEFAULT '[]'
);

ALTER TABLE cartera_build ADD COLUMN IF NOT EXISTS alignment_score NUMERIC(6,3) DEFAULT NULL;

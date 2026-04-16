-- ============================================================
-- ARQ-04 F4 — Tabla de configuración de LLM providers
-- Schema: primitiva (datos de configuración, no transaccionales)
-- ============================================================

CREATE SCHEMA IF NOT EXISTS primitiva;

CREATE TABLE IF NOT EXISTS primitiva.llm_provider_config (id SERIAL PRIMARY KEY, provider_name VARCHAR(50) NOT NULL UNIQUE, display_name VARCHAR(100) NOT NULL, auth_type VARCHAR(30) NOT NULL DEFAULT 'api_key', is_active BOOLEAN NOT NULL DEFAULT TRUE, is_default BOOLEAN NOT NULL DEFAULT FALSE, config_json JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW());

INSERT INTO primitiva.llm_provider_config (provider_name, display_name, auth_type, is_active, is_default, config_json) VALUES ('anthropic', 'Anthropic Claude', 'api_key', TRUE, TRUE, '{"models":["claude-sonnet-4-20250514","claude-haiku-4-5-20251001"]}'::jsonb) ON CONFLICT (provider_name) DO NOTHING;

INSERT INTO primitiva.llm_provider_config (provider_name, display_name, auth_type, is_active, is_default, config_json) VALUES ('openai', 'OpenAI', 'api_key', FALSE, FALSE, '{"models":["gpt-4.1","gpt-4o-mini"]}'::jsonb) ON CONFLICT (provider_name) DO NOTHING;

INSERT INTO primitiva.llm_provider_config (provider_name, display_name, auth_type, is_active, is_default, config_json) VALUES ('ollama', 'Ollama (Local)', 'none', FALSE, FALSE, '{"models":["llama3:8b","gemma3:1b"],"base_url":"http://localhost:11434"}'::jsonb) ON CONFLICT (provider_name) DO NOTHING;

INSERT INTO primitiva.llm_provider_config (provider_name, display_name, auth_type, is_active, is_default, config_json) VALUES ('chatgpt', 'ChatGPT Plus (Codex)', 'oauth', FALSE, FALSE, '{"models":["gpt-5.4"],"endpoint":"chatgpt.com/backend-api/codex/responses","note":"Requires OpenClaw OAuth token"}'::jsonb) ON CONFLICT (provider_name) DO NOTHING;

-- P98 F1 — Add id_pm_usuario FK to build_live
-- Jose Antonio Martinez Victoria · 2026-04-08
ALTER TABLE build_live
  ADD COLUMN id_pm_usuario INT NULL REFERENCES rbac_usuarios(id_usuario);
CREATE INDEX idx_build_live_id_pm_usuario ON build_live(id_pm_usuario);

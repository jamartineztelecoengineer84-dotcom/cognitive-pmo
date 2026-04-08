-- P98 F3.1 — Poblar rbac_usuarios.id_pm para que /api/pm/my-resources devuelva equipo
-- Jose Antonio Martinez Victoria · 2026-04-08
--
-- Asigna cada uno de los 151 trabajadores activos (TECH_SENIOR, TECH_JUNIOR,
-- DEVOPS_LEAD, QA_LEAD, TEAM_LEAD) a uno de los 10 PMs reales por round-robin
-- determinista ordenado por id_usuario ASC.
--
-- Resultado:
--   PMO_SENIOR (4): Pablo Rivas (16, recibe el sobrante), Cristina, Daniel, Lucía → 15 c/u
--   PMO_JUNIOR (6): Inés, Marta, Sergio, Nuria, Hugo, Rubén → 15 c/u
--   Total: 151
--
-- id_pm es VARCHAR en el schema actual, por eso casteamos a texto.

WITH workers AS (
  SELECT u.id_usuario,
         ROW_NUMBER() OVER (ORDER BY u.id_usuario ASC) - 1 AS rn
  FROM rbac_usuarios u
  JOIN rbac_roles r ON u.id_role = r.id_role
  WHERE r.code IN ('TECH_SENIOR','TECH_JUNIOR','DEVOPS_LEAD','QA_LEAD','TEAM_LEAD')
    AND u.activo = TRUE
),
mapping AS (
  SELECT
    w.id_usuario,
    (ARRAY[19, 20, 21, 22, 1425, 1426, 1427, 1428, 1429, 1430])[(w.rn % 10) + 1] AS pm_id
  FROM workers w
)
UPDATE rbac_usuarios u
SET id_pm = m.pm_id::text
FROM mapping m
WHERE u.id_usuario = m.id_usuario;

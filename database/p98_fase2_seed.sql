-- P98 F2 — Seed PMO_JUNIOR + reasignación de los 60 proyectos
-- Jose Antonio Martinez Victoria · 2026-04-08
--
-- Este script:
--   1) Inserta 6 nuevos usuarios PMO_JUNIOR (id_role=15)
--   2) Reasigna los 60 proyectos de build_live a 10 PMs reales
--      (4 PMO_SENIOR existentes round-robin sobre los 32 proyectos de mayor BAC,
--       6 PMO_JUNIOR nuevos round-robin sobre los 28 restantes).
--      Pobla build_live.id_pm_usuario (FK añadida en P98 F1) y reescribe
--      build_live.pm_asignado con el nombre corto consistente.
--
-- password_hash = sha256('12345') = 5994471a...cacfc5 (mismo formato que el seed inicial)
--
-- Idempotencia: los INSERT usan ON CONFLICT (email) DO NOTHING para poder
-- re-aplicar el seed. Los UPDATE son idempotentes por construcción
-- (orden determinista por presupuesto_bac DESC, id_proyecto ASC).

-- ─────────────────────────────────────────────────────────────────────
-- 1) INSERT 6 PMO_JUNIOR
-- ─────────────────────────────────────────────────────────────────────
INSERT INTO rbac_usuarios
  (email, password_hash, nombre_completo, id_role, departamento, cargo, activo, requiere_cambio_password)
VALUES
  ('ines.carmona@cognitivepmo.com',  '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', 'Inés Carmona Ruiz',    15, 'PMO', 'Project Manager Junior', TRUE, FALSE),
  ('marta.nunez@cognitivepmo.com',   '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', 'Marta Núñez Herrera',  15, 'PMO', 'Project Manager Junior', TRUE, FALSE),
  ('sergio.mateos@cognitivepmo.com', '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', 'Sergio Mateos Lara',   15, 'PMO', 'Project Manager Junior', TRUE, FALSE),
  ('nuria.beltran@cognitivepmo.com', '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', 'Nuria Beltrán Ortega', 15, 'PMO', 'Project Manager Junior', TRUE, FALSE),
  ('hugo.ramos@cognitivepmo.com',    '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', 'Hugo Ramos Castillo',  15, 'PMO', 'Project Manager Junior', TRUE, FALSE),
  ('ruben.ortiz@cognitivepmo.com',   '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', 'Rubén Ortiz Delgado',  15, 'PMO', 'Project Manager Junior', TRUE, FALSE)
ON CONFLICT (email) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────
-- 2) Reasignación determinista de proyectos
--    Reparto round-robin sobre el orden ORDER BY presupuesto_bac DESC, id_proyecto ASC.
--    SENIOR: Pablo Rivas (19), Cristina Vega (20), Daniel Prieto (21), Lucía Romero (22)
--      → 8 proyectos cada uno (top 32 por BAC)
--    JUNIOR: Inés Carmona, Marta Núñez, Sergio Mateos, Nuria Beltrán, Hugo Ramos, Rubén Ortiz
--      → 5+5+5+5+4+4 (28 restantes)
-- ─────────────────────────────────────────────────────────────────────
WITH ordered AS (
  SELECT id_proyecto, ROW_NUMBER() OVER (ORDER BY presupuesto_bac DESC, id_proyecto ASC) - 1 AS rn
  FROM build_live
),
mapping AS (
  SELECT
    o.id_proyecto,
    CASE
      WHEN o.rn <  32 THEN
        CASE (o.rn % 4)
          WHEN 0 THEN 19  WHEN 1 THEN 20
          WHEN 2 THEN 21  WHEN 3 THEN 22
        END
      ELSE
        (SELECT id_usuario FROM rbac_usuarios WHERE email = (
          ARRAY[
            'ines.carmona@cognitivepmo.com',
            'marta.nunez@cognitivepmo.com',
            'sergio.mateos@cognitivepmo.com',
            'nuria.beltran@cognitivepmo.com',
            'hugo.ramos@cognitivepmo.com',
            'ruben.ortiz@cognitivepmo.com'
          ])[((o.rn - 32) % 6) + 1]
        ))
    END AS uid_pm
  FROM ordered o
)
UPDATE build_live b
SET id_pm_usuario = m.uid_pm,
    pm_asignado = (
      SELECT split_part(u.nombre_completo, ' ', 1) || ' ' || split_part(u.nombre_completo, ' ', 2)
      FROM rbac_usuarios u WHERE u.id_usuario = m.uid_pm
    )
FROM mapping m
WHERE b.id_proyecto = m.id_proyecto;

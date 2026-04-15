# ROADMAP Depuración RBAC + Datos PM

**Fecha inicio:** 2026-04-15
**Origen:** RBAC_AUDIT_2026-04-15.md (auditoría primo NAS)
**Ventana:** 15-Abr → Junio 2026 (pre-defensa TFM)
**Estado freeze:** levantado para esta línea de trabajo; el TFM se actualiza en paralelo (v3+ de cada capítulo).

---

## FASE 0 — Congelación del estado actual (30 min)

Antes de tocar nada, foto fija de lo que hay para poder volver si algo se tuerce.

- [ ] Tag git `pre-rbac-cleanup` sobre commit actual en NAS
- [ ] `pg_dump` completo de BBDD cognitive_pmo → backup en `/root/backups/`
- [ ] Export CSV de las tablas clave: rbac_usuarios, rbac_roles, pmo_project_managers, cartera_build, build_live, incidencias_live
- [ ] Screenshot del login + shell SUPERADMIN funcionando (post BUG-LOGIN-01)

**Criterio de éxito:** existe un punto de retorno limpio.

---

## FASE 1 — Unificación del dominio `id_pm_usuario` (CRÍTICO, bloquea todo)

**Problema:** `cartera_build.id_pm_usuario` es VARCHAR con 'PM-XXX', `build_live.id_pm_usuario` es INTEGER con id_usuario de rbac. Dos universos que no se cruzan.

**Decisión tomada:** unificar hacia `rbac_usuarios.id_usuario` (entero). `pmo_project_managers` queda como tabla de atributos profesionales (skills, scoring, carga) siempre joined vía `id_usuario_rbac`.

- [ ] 1.1 — Crear función SQL `compartido.fn_map_pm_code_to_rbac(pm_code)` que dado 'PM-XXX' devuelva el id_usuario correspondiente
- [ ] 1.2 — Crear columna intermedia `cartera_build.id_pm_usuario_new INTEGER`
- [ ] 1.3 — Poblar `id_pm_usuario_new` con la función (los NULLs quedan NULL, los 'PM-016' → 19 de Pablo Rivas, etc.)
- [ ] 1.4 — Verificar cruce: query de control debe devolver 0 inconsistencias
- [ ] 1.5 — Renombrar: `id_pm_usuario` → `id_pm_usuario_old`, `id_pm_usuario_new` → `id_pm_usuario`. FK → `rbac_usuarios.id_usuario`
- [ ] 1.6 — Actualizar todos los endpoints `/api/pm/*`, `/api/cartera/*`, `/api/build/*` que leían el VARCHAR
- [ ] 1.7 — Tests: 15/15 smoke de cartera deben pasar con IDs enteros
- [ ] 1.8 — Dejar columna `_old` visible 1 semana por si hay rollback; después DROP

**Criterio de éxito:** un único dominio numérico para PMs, tests verdes, dashboard RUN/BUILD no se rompe.
**Material TFM:** esta refactorización es caso de estudio perfecto para Cap 5 "Evolución del modelo" — documenta el error de diseño y cómo se corrige sin downtime.

---

## FASE 2 — Rescate de los 15 PMs huérfanos (PM-001 a PM-015)

**Problema:** pmo_project_managers tiene 15 PMs sin `id_usuario_rbac`. Aparecen llevando proyectos pero no existen como usuarios.

- [ ] 2.1 — Decisión humano-seed: ¿los 15 PMs son personas reales que tendrían login, o son "ghost PMs" de datos sintéticos que se reasignan a los 10 buenos?
- [ ] 2.2 — Ejecutar opción elegida (script SQL + INSERT/UPDATE)
- [ ] 2.3 — Linkear `pmo_project_managers.id_usuario_rbac` para los PMs supervivientes
- [ ] 2.4 — Verificar: `SELECT COUNT(*) FROM pmo_project_managers WHERE id_usuario_rbac IS NULL` = 0
- [ ] 2.5 — Smoke test: login con email de cada PM nuevo debe funcionar

**Criterio de éxito:** todos los PMs en pmo_project_managers tienen identidad RBAC o están marcados inactivos.

---

## FASE 3 — Reasignación de los 34 proyectos sin PM

**Problema:** 34 de 46 proyectos en cartera_build tienen id_pm_usuario NULL (74%).

- [ ] 3.1 — Matriz distribución: cruzar `perfil_requerido` × `especialidad` de pmo_project_managers
- [ ] 3.2 — Respetar max_proyectos y carga_actual
- [ ] 3.3 — Generar propuesta automática (CSV)
- [ ] 3.4 — JA revisa y ajusta manualmente
- [ ] 3.5 — UPDATE masivo validado
- [ ] 3.6 — Verificar: 0 proyectos con id_pm_usuario NULL

**Criterio de éxito:** toda la cartera tiene PM responsable.
**Material TFM:** Cap 4 — IA propone, humano decide, sistema ejecuta.

---

## FASE 4 — Unificar login demo vs login normal

**Problema:** VP_Ops y VP_Eng tienen dos rutas distintas según canal de entrada.

- [ ] 4.1 — Decidir landing canónico para VP_OPERATIONS y VP_ENGINEERING
- [ ] 4.2 — Unificar en p97RouteAfterLogin()
- [ ] 4.3 — Alinear demoLogin() con ruta canónica
- [ ] 4.4 — Verificar los 7 demo buttons

**Criterio de éxito:** cada rol tiene UNA landing determinista.

---

## FASE 5 — Matriz RBAC canónica server-side (opcional)

- [ ] 5.1 — Decidir si se crean rbac_scopes + rbac_silo_map
- [ ] 5.2 — Si sí: schema + seed + endpoint /api/rbac/my-scope
- [ ] 5.3 — Migrar frontend a leer del endpoint
- [ ] 5.4 — docs/RBAC_MATRIX.md como referencia

---

## FASE 6 — Pulido cosmético login

- [x] 6.1 — Footer © 2026 (hecho en BUG-LOGIN-01)
- [ ] 6.2 — "Planificador Gantt" duplicado en racks
- [ ] 6.3 — "Allreed 6" → "Thread 6"
- [ ] 6.4 — "Allocactor PMO" → "Allocator"
- [ ] 6.5 — UUIDs más variados
- [ ] 6.6 — Adriana Suárez huérfana en fila última

---

## FASE 7 — Reflejo en TFM (paralelo)

- [ ] 7.1 — Cap 3 v3: sección "Auditoría consistencia RBAC"
- [ ] 7.2 — Cap 4 v4: dualidad IDs como anti-patrón corregido
- [ ] 7.3 — Cap 5 v4: rescate PMs huérfanos como caso práctico
- [ ] 7.4 — Cap 5 v4: workflow IA-humano con reasignación proyectos
- [ ] 7.5 — Cap 6 v4: líneas futuras actualizadas
- [ ] 7.6 — Anexo C actualizado con modelo final IDs

---

## Orden de ejecución

FASE 0 → 1 → 2 → 3 → 4 → 6 → 5 (opcional) → 7 (paralelo desde F1)

---

## Métricas de cierre

- 0 proyectos con id_pm_usuario NULL (salvo Standby)
- 0 PMs con id_usuario_rbac NULL (salvo inactivos)
- 1 dominio numérico id_pm_usuario
- 1 landing determinista por rol
- 0 typos en login
- TFM Caps 3-6 v4+
- Backup + tag pre/post rollback

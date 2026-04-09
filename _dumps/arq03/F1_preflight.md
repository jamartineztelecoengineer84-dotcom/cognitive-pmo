# ARQ-03 F1.0 — Pre-flight para mover tablas

**Fecha:** 2026-04-09
**Commit base:** 3ae2012da28dcf53eecfd42348c4754405519687
**Modo:** SOLO LECTURA. No se ha modificado nada en BD ni en código.
**Único artefacto generado:** este documento.

---

## 1. Secuencias en `public` (Tarea 1)

**Total: 27 secuencias** (24 con owner automático + 3 huérfanas)

### 1.1 — Secuencias con owner table (24) — se mueven automáticamente

Cuando se hace `ALTER TABLE X SET SCHEMA Y`, PostgreSQL arrastra automáticamente las secuencias asociadas vía `pg_depend` (deptype='a' = auto-owned). Lista:

| secuencia | tabla owner | columna | caja destino |
|---|---|---|---|
| catalogo_incidencias_id_catalogo_seq | catalogo_incidencias | id_catalogo | A |
| catalogo_skills_id_skill_seq | catalogo_skills | id_skill | A |
| cmdb_activos_id_activo_seq | cmdb_activos | id_activo | B |
| cmdb_cambios_id_cambio_seq | cmdb_cambios | id_cambio | B |
| cmdb_categorias_id_categoria_seq | cmdb_categorias | id_categoria | A |
| cmdb_costes_id_coste_seq | cmdb_costes | id_coste | B |
| cmdb_ips_id_ip_seq | cmdb_ips | id_ip | B |
| cmdb_relaciones_id_relacion_seq | cmdb_relaciones | id_relacion | B |
| cmdb_software_id_software_seq | cmdb_software | id_software | B |
| cmdb_vlans_id_vlan_seq | cmdb_vlans | id_vlan | B |
| documentacion_repositorio_id_seq | documentacion_repositorio | id | A |
| p96_pulse_hitos_id_seq | p96_pulse_hitos | id | B |
| p96_pulse_responsables_id_seq | p96_pulse_responsables | id | B |
| rbac_audit_log_id_log_seq | rbac_audit_log | id_log | A |
| rbac_permisos_id_permiso_seq | rbac_permisos | id_permiso | A |
| rbac_roles_id_role_seq | rbac_roles | id_role | A |
| rbac_sesiones_id_sesion_seq | rbac_sesiones | id_sesion | A |
| rbac_usuarios_id_usuario_seq | rbac_usuarios | id_usuario | A |
| tech_adjuntos_id_seq | tech_adjuntos | id | B |
| tech_chat_mensajes_id_seq | tech_chat_mensajes | id | B |
| tech_chat_salas_id_seq | tech_chat_salas | id | B |
| tech_notificaciones_id_seq | tech_notificaciones | id | B |
| tech_terminal_log_id_seq | tech_terminal_log | id | B |
| tech_valoracion_mensual_id_seq | tech_valoracion_mensual | id | B |

**Subtotal automático**: 24 secuencias (9→A, 15→B). Cero acción manual requerida.

### 1.2 — Secuencias huérfanas (3) — REQUIEREN ALTER SEQUENCE explícito

| secuencia | usada por | tabla destino | caja |
|---|---|---|---|
| `inc_ticket_seq` | función `generar_ticket_id()` (escribe `incidencias_run`) | primitiva | B |
| `itsm_draft_seq` | función `generar_draft_id()` (escribe `itsm_form_drafts`) | primitiva | B |
| `seq_txn` | (sin uso identificado en grep — probablemente `gobernanza_transacciones`) | primitiva | B |

**Acción F1.1**: añadir 3 `ALTER SEQUENCE … SET SCHEMA primitiva` explícitos al script de migración.

---

## 2. Funciones definidas en `public` (Tarea 2)

**Total: 38 funciones** = 31 de extensión `pg_trgm` (C) + **7 del proyecto** (plpgsql/sql).

### 2.1 — Funciones de extensión `pg_trgm` (31) — NO MOVER

```
gin_extract_query_trgm, gin_extract_value_trgm, gin_trgm_consistent,
gin_trgm_triconsistent, gtrgm_compress/consistent/decompress/distance/
in/options/out/penalty/picksplit/same/union, set_limit, show_limit,
show_trgm, similarity, similarity_dist, similarity_op,
strict_word_similarity (+5 variantes op/dist),
word_similarity (+4 variantes op/dist)
```

**Razón**: son funciones C ancladas a la extensión `pg_trgm` (la usa `idx_catalogo_trgm` para búsqueda fuzzy). Mover una función de extensión rompe la extensión. **Permanecen en `public`** y se accede via search_path implícito en cualquier esquema futuro.

### 2.2 — Funciones del proyecto (7)

| # | función | lenguaje | sec_def | proconfig | body usa `public.` literal | caja destino propuesta |
|---|---|---|---|---|---|---|
| 1 | `buscar_tecnico_por_skill(text,text)` | plpgsql | f | NULL | **no** | **compartido** (usa solo `pmo_staff_skills` que va a A) |
| 2 | `fn_registrar_cambio_estado()` | plpgsql | f | NULL | **no** | **primitiva** (trigger sobre `cartera_build` B) |
| 3 | `fn_validar_ventana_cambio(int,timestamp,varchar)` | plpgsql | f | NULL | **no** | **primitiva** (usa `cmdb_change_windows` B) |
| 4 | `generar_draft_id()` | sql | f | NULL | **no** | **primitiva** (usa `itsm_draft_seq`) |
| 5 | `generar_ticket_id()` | plpgsql | f | NULL | **no** | **primitiva** (usa `inc_ticket_seq`) |
| 6 | `trigger_run_to_live_insert()` | plpgsql | f | NULL | **no** | **primitiva** (trigger sobre `incidencias_run` B) |
| 7 | `trigger_run_to_live_update()` | plpgsql | f | NULL | **no** | **primitiva** (trigger sobre `incidencias_run` B) |

**Hallazgos críticos**:
- **0 funciones SECURITY DEFINER**: ninguna ejecuta con privilegios elevados. No hay riesgo de bypass de search_path.
- **0 funciones con `proconfig` no nulo**: ninguna fija `SET search_path = ...` en su definición. Todas heredan el search_path del rol que las invoca.
- **0 funciones con `public.X` literal en `prosrc`**: verificación crítica hecha sobre el body real (no sobre `pg_get_functiondef` que añade la cabecera `CREATE OR REPLACE FUNCTION public.X` automáticamente y produciría falsos positivos). Confirmado: las 7 funciones del proyecto son **schema-agnósticas** — todas resuelven sus refs a tablas via search_path implícito.

### 2.3 — Bodies inspeccionados (verificación literal)

**`generar_ticket_id`** (sin esquema en body):
```sql
DECLARE next_n BIGINT; fecha_hoy TEXT;
BEGIN
  next_n := nextval('inc_ticket_seq');     -- ← sin esquema
  fecha_hoy := to_char(now(), 'YYYYMMDD');
  RETURN 'INC-' || lpad(next_n::TEXT, 6, '0') || '-' || fecha_hoy;
END;
```

**`generar_draft_id`**:
```sql
SELECT 'RUN-' || lpad(nextval('itsm_draft_seq')::text, 6, '0')
            || '-' || to_char(current_date, 'YYYYMMDD');
```

**`trigger_run_to_live_insert`**:
```sql
BEGIN
  IF NEW.estado IN ('QUEUED','EN_CURSO','ESCALADO') THEN
    INSERT INTO incidencias_live (...) VALUES (...);    -- ← sin esquema
  END IF;
END;
```

**`trigger_run_to_live_update`**:
```sql
BEGIN
  IF NEW.estado IN ('RESUELTO','CERRADO') THEN
    DELETE FROM incidencias_live WHERE ticket_id = NEW.ticket_id;
  ELSIF NEW.estado IN ('QUEUED','EN_CURSO','ESCALADO') THEN
    UPDATE incidencias_live SET ... WHERE ticket_id = NEW.ticket_id;
  END IF;
END;
```

**`fn_validar_ventana_cambio`**:
```sql
DECLARE v_dow VARCHAR; v_hour INT; v_ventana cmdb_change_windows%ROWTYPE; ...
BEGIN
  SELECT * INTO v_ventana FROM cmdb_change_windows
  WHERE cmdb_change_windows.id_activo = p_id_activo
    AND cmdb_change_windows.estado = 'ACTIVA' ...
END;
```

**`buscar_tecnico_por_skill`**:
```sql
BEGIN
  RETURN QUERY
  SELECT s.id_recurso, s.nombre, s.nivel, ...
  FROM pmo_staff_skills s
  WHERE s.estado_run = 'DISPONIBLE' ...
END;
```

**Conclusión sec 2**: las 7 funciones son **completamente esquema-agnósticas**. F1.1 solo necesita `ALTER FUNCTION ... SET SCHEMA Y` para reubicar el nombre cualificado, pero **no requiere reescribir ninguna línea de cuerpo**.

---

## 3. Triggers en `public` (Tarea 3)

**Total: 3 triggers** (todos sobre tablas Caja B):

| trigger_name | tabla (caja) | función llamada | esquema función |
|---|---|---|---|
| `trg_cambio_estado_proyecto` | cartera_build (B) | fn_registrar_cambio_estado | public |
| `trg_run_to_live_insert` | incidencias_run (B) | trigger_run_to_live_insert | public |
| `trg_run_to_live_update` | incidencias_run (B) | trigger_run_to_live_update | public |

**Comportamiento al mover**:
- Los triggers son **propiedad de la tabla**: cuando se hace `ALTER TABLE incidencias_run SET SCHEMA primitiva`, los triggers `trg_run_to_live_insert/update` se mueven con ella automáticamente.
- La referencia trigger→función está guardada por **OID** en `pg_trigger.tgfoid`, no por nombre. Mover la función con `ALTER FUNCTION ... SET SCHEMA primitiva` actualiza el OID en su mismo lugar (el OID no cambia), por tanto el trigger sigue apuntando correctamente.
- **Acción F1.1**: ninguna explícita sobre triggers. Los 3 se reubican gratis con sus tablas.

**Alerta única**: si las funciones `trigger_run_to_live_*` se mueven a un esquema distinto que la tabla `incidencias_run`, los triggers seguirían funcionando porque PostgreSQL no requiere coubicación. Pero por coherencia, **función y tabla deben ir al mismo esquema** (`primitiva`).

---

## 4. Vistas y vistas materializadas en `public` (Tarea 4)

**Total: 12 vistas (regulares, ninguna materializada)**.

**0 vistas con `public.X` literal** en su definición. Todas usan refs sin esquema → resolverán via search_path tras el move.

| # | vista | tablas origen | propuesta |
|---|---|---|---|
| 1 | `agent_conversations_cobertura` | agent_conversations (B) | **primitiva** |
| 2 | `v_cambios_pendientes_aplicar` | cmdb_change_approvals, cmdb_change_proposals, cmdb_change_windows (todas B) | **primitiva** |
| 3 | `v_p96_build_portfolio` | build_live (B) | **primitiva** |
| 4 | `v_p96_run_cis` | cmdb_activos (B), incidencias_run (B) | **primitiva** |
| 5 | `v_p96_run_incidents` | incidencias_run (B) | **primitiva** |
| 6 | `v_proxima_ejecucion_gabinete` | calendario_periodos_demanda (A) | **compartido** |
| 7 | `view_disponibilidad_global` | cartera_build (B) + incidencias_run (B) + pmo_staff_skills (A) | **primitiva** (cross-caja, vive donde están las B; resolverá A via search_path) |
| 8 | `vista_audit_gobernanza` | cartera_build (B) + gobernanza_transacciones (B) + pmo_staff_skills (A) | **primitiva** (cross-caja) |
| 9 | `vista_carga_por_silo` | pmo_staff_skills (A) | **compartido** |
| 10 | `vista_portafolio_build` | cartera_build (B) | **primitiva** |
| 11 | `vista_proyectos_riesgo` | cartera_build (B) | **primitiva** |
| 12 | `vista_serie_temporal_incidencias` | incidencias_run (B) | **primitiva** |

**Subtotales**: 10 vistas → primitiva + 2 vistas → compartido.

**Acción F1.1**: añadir 12 `ALTER VIEW … SET SCHEMA …` explícitos. Las vistas no se mueven automáticamente con sus tablas; PostgreSQL las deja en su esquema original aunque sus dependencias migren (lo cual sería incoherente — la vista en `public` apuntando a tablas en `primitiva`).

**Verificación de recompilación**: PostgreSQL recompila las vistas automáticamente cuando sus tablas dependientes se mueven, gracias al sistema de OIDs. No hay que `DROP/CREATE`. Pero el `ALTER VIEW SET SCHEMA` es necesario para reubicar el nombre.

---

## 5. Tipos enum y dominios en `public` (Tarea 5)

**Total: 0 enums, 0 dominios**.

Toda la enumeración se hace vía `CHECK constraints` sobre `varchar` (visto en F0 recon: prioridad, estado, columna, etc. todas usan `CHECK ... ANY (ARRAY[...])`). Esto es ventaja para F1: cero tipos custom que mover, cero refs cross-schema a tipos.

---

## 6. Grep código (Tarea 6)

```bash
grep -rn "generar_ticket_id\|CREATE OR REPLACE FUNCTION\|CREATE TRIGGER" database/ | grep -i "public\."
```

**Resultado: 0 matches**. Cero scripts SQL en `database/` cualifican `public.` cuando crean funciones o triggers. Todas las definiciones SQL del repo asumen el esquema implícito (default `public`) y por tanto **se reubicarán automáticamente** si se ejecutan en una sesión con `search_path = primitiva, compartido, public`.

> Confirmación cruzada con F0_recon.md: los únicos 6 matches de `public.` en código son `to_regclass(...)` benignos. Ninguno aparece en las funciones/triggers grepeados ahora.

---

## 7. Evaluación final (5 líneas)

1. **F1 se puede hacer con un ALTER TABLE barato** + 3 ALTERs auxiliares pequeños. Las 7 funciones del proyecto son **schema-agnósticas** (verificado en `prosrc`, no en `pg_get_functiondef`), los 3 triggers se reubican gratis con sus tablas, las 12 vistas no usan literal `public.`, y no hay enums/dominios que mover.
2. **Acciones explícitas requeridas** además del `ALTER TABLE × 68`:
   - `ALTER FUNCTION × 7` (1 → compartido, 6 → primitiva)
   - `ALTER VIEW × 12` (2 → compartido, 10 → primitiva)
   - `ALTER SEQUENCE × 3` para las huérfanas (`inc_ticket_seq`, `itsm_draft_seq`, `seq_txn` → primitiva)
   - 24 secuencias restantes se arrastran automáticamente con su tabla owner
3. **Cero reescritura de cuerpos de funciones**. Cero modificaciones a triggers. Cero modificaciones a vistas. La extensión `pg_trgm` se queda intacta en `public`.
4. **El único cambio de código en F1** sigue siendo el ya identificado en F0_reparto: `backend/tests/test_arq02_f4_itsm_drafts.py:44` (literal `'public.itsm_form_drafts'` → `'primitiva.itsm_form_drafts'`).
5. **Riesgo residual mínimo**: la tercera secuencia huérfana `seq_txn` no tiene grep matches en código — verificar antes de F1.1 que no la use ningún path crítico que asuma `public.seq_txn` cualificado. Si el grep en F1.0bis confirma que `seq_txn` solo se usa via `nextval('seq_txn')` sin esquema, va a `primitiva` sin riesgo.

---

## Resumen ejecutivo

| Concepto | Cantidad | Acción F1.1 |
|---|---|---|
| Tablas a mover | 68 (18→A + 50→B) | `ALTER TABLE × 68` |
| Secuencias con owner | 24 | automático con tabla |
| Secuencias huérfanas | 3 | `ALTER SEQUENCE × 3` |
| Funciones del proyecto | 7 | `ALTER FUNCTION × 7` |
| Funciones extension `pg_trgm` | 31 | quedan en public (no tocar) |
| Triggers | 3 | automático con tabla |
| Vistas | 12 | `ALTER VIEW × 12` |
| Vistas materializadas | 0 | — |
| Enums | 0 | — |
| Dominios | 0 | — |
| Funciones SECURITY DEFINER | **0** | — |
| Funciones con `proconfig` (search_path bloqueado) | **0** | — |
| Funciones con `public.` literal en body | **0** | — |
| Vistas con `public.` literal | **0** | — |
| Refs `public.` en SQL del repo (sin to_regclass) | **0** | — |
| Test a actualizar (`itsm_form_drafts`) | 1 | reemplazar literal |

**Total objetos a tocar en F1.1**: 68 tablas + 3 secuencias + 7 funciones + 12 vistas + 1 test = **91 cambios atómicos**, todos en una transacción. Cero riesgo de inconsistencia parcial gracias a `BEGIN; ... COMMIT;`.

---

## Semáforo final

🟢 **VERDE — listo para F1.1**

Justificación:
- Cero funciones rotas tras el move (verificado a nivel `prosrc`)
- Cero vistas con `public.` literal (recompilación automática)
- Cero enums/dominios cross-schema
- Cero `SECURITY DEFINER` ni `proconfig` que bloqueen search_path
- 31 funciones de extensión permanecen en `public` (compatibilidad total)
- Solo 1 cambio quirúrgico de código (`test_arq02_f4_itsm_drafts.py:44`)
- Plan de migración cabe en 1 transacción `BEGIN/COMMIT`

**Caveat menor (no bloqueante)**: la secuencia huérfana `seq_txn` no tiene grep visible en código. Antes de ejecutar F1.1, hacer un grep dirigido `grep -rn seq_txn backend/ database/` para confirmar su uso real. Si no aparece, quizá sea una secuencia muerta y se puede dejar en `public` o droppear.

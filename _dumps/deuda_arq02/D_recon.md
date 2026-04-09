# Bloque D — Recon + cierre

## D.2 — F-02 (Grupo A `INC-YYYY-XXXX` en `kanban_tareas.id_incidencia`)

**CERRADA POR INEXISTENCIA — 2026-04-09.**

Recon D.1 PASO 3 mostró distribución completa de formatos en `kanban_tareas.id_incidencia`:

| formato | n |
|---|---|
| NULL | 265 |
| `INC-NNNNNN-YYYYMMDD` (canónico) | 187 |
| `INC-YYYY-XXXX` (Grupo A legacy F-02) | **0** |
| otros | 0 |

**0 filas en formato Grupo A** → la deuda F-02 no tiene target real. Las filas legacy fueron purgadas en algún cleanup previo (probablemente migración ARQ-01 F1 que renumeró todos los `INC-YYYYMMDD-HEX` al formato canónico, o el C.2 PASO 2 que purgó las 35 huérfanas). Sin código, sin migración, sin tests. F-02 cerrada por inexistencia.

---

## D.1 — F-ARQ02-18 FK CASCADE `kanban_tareas.id_incidencia → incidencias_run`

**CERRADA — 2026-04-09.**

### Pre-recon (D.1 PASO 1-5)
- `kanban_tareas.id_incidencia`: `varchar(30)`, NULLABLE, sin FK previa, índice `idx_kanban_incidencia` ya presente
- 0 huérfanos post-C.2
- Distribución limpia: 265 NULL + 187 canónico
- `incidencias_run.ticket_id` PRIMARY KEY ✓
- Pre-requisitos para FK CASCADE: 6/6 ✓

### Migration aplicada

`database/arq02_deudaD1_kanban_fk_cascade.sql` (idempotente vía `pg_constraint` lookup):

```sql
ALTER TABLE kanban_tareas
  ADD CONSTRAINT kanban_tareas_id_incidencia_fkey
  FOREIGN KEY (id_incidencia)
  REFERENCES incidencias_run(ticket_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE;
```

**Primera aplicación**: `NOTICE: FK kanban_tareas_id_incidencia_fkey creada` + listado post mostrando ambas FK (`id_tecnico_fkey` + nuevo `id_incidencia_fkey`).
**Segunda aplicación**: `NOTICE: FK kanban_tareas_id_incidencia_fkey ya existe (idempotente)` ✓.

### Tests regresión nuevos

`backend/tests/test_deudaD1_fk_cascade.py` (2 tests sync `_run`):
1. `test_fk_cascade_rechaza_id_incidencia_fantasma`: INSERT con `id_incidencia='INC-999999-20260409'` → `asyncpg.ForeignKeyViolationError` ✓
2. `test_fk_cascade_borra_hijas_al_borrar_padre`: seed incidencia + kanban hija, DELETE incidencia → CASCADE limpia kanban (count post = 0) ✓

### Cleanup defensivo simplificado

`test_deudaA_integrador.py:_cleanup`: removido `DELETE FROM kanban_tareas WHERE id_incidencia=$1` (ahora redundante por CASCADE). Conservado `DELETE FROM agent_conversations` (columna soft, sin FK). Conservado `DELETE FROM incidencias_run` (que ahora cascadea). Comment inline F-ARQ02-18 explicando el cambio.

---

## F-ARQ02-19 — `conftest.py` autouse session-scope purga PRJ-SC* residuales

**CERRADA — 2026-04-09.**

### Causa raíz

`v_p96_build_portfolio` (vista usada por endpoint `GET /api/p96/build/portfolio`) **NO filtra filas con `id_proyecto LIKE 'PRJ-SC%'`**. Por tanto:

- `test_p96_router::test_build_portfolio` espera `len(data) == 60` (60 baseline legacy)
- Pero los tests scenario (`test_scenario_engine::test_legacy_intacto_post_overload`, `test_scenario_e2e::test_e2e_seed_scenario`, etc.) llaman a `seed_scenario_overload/optimal/half` que insertan **40 filas `PRJ-SCA/B/C/D`** en `build_live`
- Como pytest ordena alfabéticamente (`test_p96_router < test_scenario_*`), `test_p96` corre PRIMERO en cada sesión
- Pero las 40 filas SC **persisten entre sesiones**: la sesión N-1 termina dejando SC=40, y la sesión N arranca con esos 40 ya en BD → `test_p96` ve 100 (60 + 40) → fail

C.2 lo "resolvió" temporalmente con `PASO 6 SQL purga SC` (un wipe inmediato), pero la siguiente sesión pytest volvía a romper porque los tests scenario re-poblaban SC. **Solución estructural pendiente**.

### Fix aplicado

`backend/tests/conftest.py` con fixture `_purge_scenario_residuals_at_session_start` (`scope="session", autouse=True`):

```python
@pytest.fixture(scope="session", autouse=True)
def _purge_scenario_residuals_at_session_start():
    async def _purge():
        c = await asyncpg.connect(host=..., user=..., password=..., ...)
        try:
            await c.execute("DELETE FROM build_live WHERE id_proyecto LIKE 'PRJ-SC%'")
        finally:
            await c.close()
    asyncio.get_event_loop().run_until_complete(_purge())
    yield
```

- **Scope `session`**: corre UNA vez al arrancar pytest, antes de cualquier test
- **`autouse=True`**: aplica a todos los tests sin necesidad de declararlo
- **No teardown**: no purga al final, los tests scenario pueden dejar SC=40 al cerrar (se limpiará en la siguiente sesión)
- **No toca ningún test existente**: cero modificaciones a `test_p96_router`, `test_scenario_*`, ni promesas anteriores rotas
- **Cubre cualquier futuro test scenario** que se añada — el fixture se ejecuta independientemente del set de tests

### Verificación

- **Primera corrida pytest** (post fixture): **88 passed / 0 failed en 41.19s** ✅
- **Segunda corrida inmediata** (verificación idempotencia): **88 passed / 0 failed en 40.75s** ✅

El fixture limpia SC al inicio de cada sesión → `test_p96_router::test_build_portfolio` siempre ve `build_live=60` exacto independientemente del estado dejado por la sesión previa.

### Resumen Bloque D

| Deuda | Estado | Mecanismo |
|---|---|---|
| F-02 (Grupo A `INC-YYYY-XXXX`) | CERRADA por inexistencia | Recon mostró 0 filas, no hay target |
| F-ARQ02-18 (FK CASCADE) | CERRADA | Migration `arq02_deudaD1_kanban_fk_cascade.sql` + 2 tests regresión + cleanup defensivo simplificado |
| F-ARQ02-19 (PRJ-SC* persistente inter-sesión) | CERRADA | `conftest.py` autouse session-scope purga al inicio |

**Suite**: 88 passed / 0 failed (verificado en 2 pasadas consecutivas).

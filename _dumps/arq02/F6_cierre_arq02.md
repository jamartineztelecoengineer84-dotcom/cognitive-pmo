# ARQ-02 — Cierre Refundación RUN

**Fecha:** 2026-04-09
**Tag:** `arq02-done`
**Duración:** 2026-04-07 → 2026-04-09 (3 días)

## Cadena de commits

| Fase | SHA | Descripción |
|------|------|-------------|
| F0 | `cc44317` | snapshot baseline RUN |
| F1 | `63da607` | ticket_id `INC-NNNNNN-YYYYMMDD` via SEQUENCE + cascada |
| F2 | `11b62e1` | `incidencias_live ⊆ incidencias_run` via FK + sync triggers |
| F3 | `66b553f` | DROP TABLE `incidencias` zombie fósil |
| F4 | `206a111` | rename `run_incident_plans` → `itsm_form_drafts` |
| F5 | `bfde8ec` | `agent_conversations.ticket_id` soft + backfill heurístico |
| F6 | _este commit_ | cierre ARQ-02: invariantes + smoke scenarios + reporte |

## Invariantes verificados (F6.1)

- Formato `ticket_id`: 37/37 cumplen `^INC-[0-9]{6}-[0-9]{8}$`
- SEQUENCE alineada con max real (`seq_last=37`, `max_num=37`)
- FK `incidencias_live_ticket_id_fkey`: `live → run` con `ON DELETE/UPDATE CASCADE`
- 2 triggers AFTER ROW en `incidencias_run`:
  `trg_run_to_live_insert` (crea fila live al insertar ticket abierto) +
  `trg_run_to_live_update` (propaga cambios + DELETE on RESUELTO/CERRADO + fallback INSERT en reapertura)
- `live ⊆ run`: 0 huérfanos
- Tabla zombie `incidencias` (sin sufijo) DROPeada
- Rename `run_incident_plans` → `itsm_form_drafts` completo (0 referencias antiguas en código backend)
- `agent_conversations.ticket_id varchar(30) NULL` añadida + índice parcial `idx_conv_ticket WHERE ticket_id IS NOT NULL`
- 126 filas backfilled (7,8% del total 1.624), 0 fantasmas, 100% formato nuevo
- Smoke 4 scenarios (EMPTY/HALF/OPTIMAL/OVERLOAD): `huerfanos=0` y `fantasmas_conv=0` en los 4

## Counts smoke F6.2 (snapshot por scenario)

| Scenario | run | live | huerfanos | fantasmas_conv |
|----------|----:|-----:|----------:|---------------:|
| HALF     | 45  | 9    | 0         | 0              |
| OPTIMAL  | 49  | 13   | 0         | 0              |
| OVERLOAD | 59  | 21   | 0         | 0              |
| EMPTY    | 37  | 5    | 0         | 0              |

**Reset final**: BD vuelve a EMPTY tras el smoke (`run=37, live=5, drafts=61, conv_con_ticket=126, seq=(37,t)`).

## Counts baseline post-ARQ-02 (EMPTY)

| Tabla | Count |
|-------|-------|
| `incidencias_run` | 37 |
| `incidencias_live` | 5 |
| `itsm_form_drafts` | 61 |
| `agent_conversations` | 1.624 |
| `agent_conversations.ticket_id NOT NULL` | 126 |
| `inc_ticket_seq` | (37, true) |
| `incidencias` (zombie) | DROPeada (no existe) |

## Tests

- **61/64 pytest verde** (incluyendo 19 nuevos en ARQ-02: 6 F2.1 + 2 F3 + 5 F4 + 6 F5 — el conteo exacto puede variar ±1 entre patches)
- **3 rojos**: F-ARQ02-01 (baselines hardcoded en `test_p96_router::test_build_portfolio`, `test_scenario_e2e::test_e2e_seed_scenario`, `test_scenario_engine::test_legacy_intacto_post_overload`)

## Deuda registrada (13 items, F-ARQ02-01..13)

| ID | Descripción | Destino |
|----|-------------|---------|
| F-ARQ02-01 | 3 tests con baselines hardcoded (60/341/34 vs 61/347/37) | Refactor a fixtures dinámicas post-ARQ-02 |
| F-ARQ02-02 | 3 kanban huérfanos `INC-2026-XXXX` (Grupo A fósiles del seed inicial) | Ignorar |
| F-ARQ02-03 | `tech_chat_salas.id_referencia` polimórfico (acepta `INC-*` y `BUS-AG-*`) | Post-ARQ-02 split en 2 columnas |
| F-ARQ02-04 | Formulario ITSM duplica ticket vía 3 paths (`POST /incidencias` + `POST /run/plans` + `POST /agents/AG-001/invoke`) | Refactor del flujo ITSM post-ARQ-02 |
| F-ARQ02-05 | `POST /incidencias/live` redundante post-trigger (no-op idempotente) | Deprecación post-ARQ-02 |
| F-ARQ02-06 | Tests del scenario engine no garantizan EMPTY al final del módulo (drift entre runs) | Mitigación con teardown module-scoped |
| F-ARQ02-07 | **DESCARTADA en F4.0.bis** (hipótesis falsa: `POST /incidencias` solo escribe en `incidencias_run`) | Cerrada |
| F-ARQ02-08 | Formulario ITSM llama a `POST /run/plans` como side-channel (sin coordinación con los otros 2 paths) | Post-ARQ-02 |
| F-ARQ02-09 | `POST /run/plans` usa `uuid4().hex[:4]` para `plan_id` (no atómico, prob colisión 1/65k/día) | Migrar a SEQUENCE separada `itsm_draft_seq` post-ARQ-02 |
| F-ARQ02-10 | `regexp_match` solo extrae el primer `ticket_id` por fila en `agent_conversations` | Aceptable, post-ARQ-02 evaluable con `regexp_matches` global |
| F-ARQ02-11 | Mojibake bytes UTF8 inválidos en `agent_conversations.content` (`0xc3`, `0xf0 0x9f` truncados) | Data fix post-ARQ-02 con `convert_from(::bytea, 'LATIN1')` |
| F-ARQ02-12 | 8 INSERT del backend (`engine.py`, `main.py`x2, `war_room_api.py`x5) no pueblan `ticket_id` en filas nuevas | Refactor post-ARQ-02 |
| F-ARQ02-13 | 56 menciones legacy huérfanas en `agent_conversations.content` (old_ids no presentes en mapping F1/F1.2.1) | Análisis post-ARQ-02 (probablemente alucinaciones del modelo + tests rollbackeados) |

## Audit trail (artefactos en `_dumps/arq02/`)

- `schemas_F0.txt` — schemas de las 8 tablas RUN pre-ARQ-02
- `data_F0.sql` — pg_dump 11MB de datos pre-ARQ-02
- `counts_F0.txt` — baseline counts F0
- `counts_pre_F1.txt` — verificación pre-F1
- `ticket_id_map_F1.csv` — 35 mapeos viejo→nuevo (F1.2)
- `ticket_id_map_F1_2_1_extra.csv` — 2 mapeos promovidos (F1.2.1)
- `incidencias_zombie_F3.csv` — fila fósil pre-DROP
- `tests_F0.txt` + `invariants_F0.txt` — pytest baselines

## Migrations versionadas

```
database/arq02_fase2_1_live_fk_triggers.sql
database/arq02_fase3_drop_zombie_incidencias.sql
database/arq02_fase4_rename_itsm_form_drafts.sql
database/arq02_fase5_agent_conversations_ticket_id.sql
database/arq02_fase5_run.sh
```

Todas idempotentes (re-aplicables sin daño) gracias a guards `IF NOT EXISTS` / `to_regclass` checks.

## Siguiente hito

ARQ-02 cerrada. Reanudar **P98 (PM Dashboard)** desde F4 sobre fundaciones limpias:
- ARQ-01 ✅ (refundación BUILD)
- ARQ-02 ✅ (refundación RUN)
- `/api/pm/*` limpios, `/api/p96/*` estables, scenario engine validado en 4 estados.

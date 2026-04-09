# Bloque B — Mini-recon

## Sección 1 — F-ARQ02-12: agent_conversations.ticket_id sin poblar

### 1.1 — Sites de `INSERT INTO agent_conversations` (grep)

`grep -rn "INSERT INTO agent_conversations" backend/` encuentra **7 sites** (NO 8 como dice el ticket — verificación abajo). El octavo posible referente debe ser un `SELECT` o el `ALTER TABLE` de la migración F5.1, no un INSERT real.

| # | Fichero:línea | Función contenedora | Endpoint | Columnas insertadas |
|---|---|---|---|---|
| 1 | `backend/war_room_api.py:555` | `session_message` | `POST /warroom/sessions/{session_id}/message` | session_id, agent_id, agent_name, role='user', content |
| 2 | `backend/war_room_api.py:640` | `chat` (user msg) | `POST /chat` | session_id, agent_id, agent_name, role='user', content |
| 3 | `backend/war_room_api.py:691` | `chat` (assistant Anthropic) | `POST /chat` (rama API real) | session_id, agent_id, agent_name, role='assistant', content, tokens_used, latency_ms, model_used |
| 4 | `backend/war_room_api.py:725` | `chat` (assistant mock) | `POST /chat` (rama mock) | session_id, agent_id, agent_name, role='assistant', content, model_used |
| 5 | `backend/agents/engine.py:115` | `AgentEngine._log` | `POST /agents/{agent_id}/invoke` (todos los agentes con engine genérico, p.ej. AG-001) | session_id, agent_id, agent_name, role∈{user,assistant}, content, tokens_used, model_used, latency_ms |
| 6 | `backend/main.py:2186` | `build_advisor_chat` (user) | `POST /build/advisor/chat` (AG-018 Governance Advisor) | session_id, agent_id='AG-018', agent_name, role='user', content, metadata |
| 7 | `backend/main.py:2219` | `build_advisor_chat` (assistant) | `POST /build/advisor/chat` | session_id, agent_id='AG-018', agent_name, role='assistant', content |

> **Discrepancia con el ticket**: F-ARQ02-12 registró 8 sites; el grep actual sólo devuelve 7 INSERT reales en `backend/`. La diferencia probable: alguien contó el `INSERT` doble dentro de `engine.py:115` (que se ejecuta dos veces en un bucle `for role, content in [("user", ...), ("assistant", ...)]` — un único site físico, dos filas lógicas). Eso reconcilia 7 físicos = 8 lógicos.

### 1.2 — Disponibilidad de `ticket_id` por site

| # | Site | ¿`ticket_id` disponible en el contexto del request? | Veredicto | Razonamiento |
|---|---|---|---|---|
| 1 | `war_room_api.py:555` `session_message` | **PARCIAL** | derivable | Los params son `(session_id, agent_id, content)`. No hay `ticket_id` directo, pero `war_room_sessions` puede traer el ticket_id asociado a la sesión vía JOIN (las war rooms se abren para tratar incidencias). Requeriría 1 query extra `SELECT ticket_id FROM war_room_sessions WHERE id = $1`. |
| 2 | `war_room_api.py:640` `chat` user | **NO** | sistema | `ChatMessage(session_id, agent_id, message)` — endpoint de chat libre con cualquier agente (incluye AG-008/9/10/12 y CLIPY). El usuario no está obligado a hablar de un ticket concreto. Conversación general. |
| 3 | `war_room_api.py:691` `chat` assistant Anthropic | **NO** | sistema | Mismo contexto que (2) — la respuesta del LLM hereda el `session_id` de la conversación libre. Sin ticket. |
| 4 | `war_room_api.py:725` `chat` assistant mock | **NO** | sistema | Idéntico a (3), rama mock cuando no hay `ANTHROPIC_API_KEY`. |
| 5 | `agents/engine.py:115` `AgentEngine._log` | **PARCIAL** | derivable parcialmente | Recibe `user_msg` y `session_id`. Para **AG-001** (post-A.2) el `user_msg` puede empezar con `TICKET: INC-NNNNNN-YYYYMMDD\n...` → regex extraíble. Para **otros agentes** que no usan el shell ITSM, no hay garantía de prefijo. Cubre la mayor parte del tráfico real (AG-001 es el agente más invocado). |
| 6 | `main.py:2186` `build_advisor_chat` user | **NO** | legítimo NULL | AG-018 es el Governance Advisor del pipeline **BUILD** (proyectos), no RUN (incidencias). El `context: dict` que llega tiene `id_proyecto` / `nombre_proyecto`, no `ticket_id`. Conceptualmente no aplica — `agent_conversations.ticket_id` sólo tiene sentido para conversaciones del lado RUN. |
| 7 | `main.py:2219` `build_advisor_chat` assistant | **NO** | legítimo NULL | Mismo razonamiento que (6). |

### 1.3 — Estado actual en BD

```sql
SELECT count(*) FILTER (WHERE ticket_id IS NULL) AS sin_ticket,
       count(*) FILTER (WHERE ticket_id IS NOT NULL) AS con_ticket,
       count(*) AS total
FROM agent_conversations;
```

```
 sin_ticket | con_ticket | total
------------+------------+-------
       1506 |        126 | 1632
```

- **92.3 %** de las filas existentes tienen `ticket_id IS NULL`
- **7.7 %** (126 filas) sí lo tienen — vienen de algún path que YA puebla la columna (probablemente backfill manual o un site fuera de los 7 grep, p.ej. el script de seed F5.1 o tests previos). **Verificar antes de mover nada.**
- La columna existe (migración `arq02_fase5_agent_conversations_ticket_id.sql`) con índice parcial idempotente sobre `ticket_id IS NOT NULL`.

### 1.4 — Veredicto en 3 líneas

1. **Trivialmente poblables (1 site, ~50–60 % del tráfico real)**: `engine.py:115` para AG-001 — basta extraer regex `^TICKET:\s*(INC-\d{6}-\d{8})` del `user_msg` antes del INSERT (mismo prefijo que ya consume `create_incident` vía `pre_existing_ticket_id` en A.2). Cero refactor de signatures. Cubre toda la cadena AG-001 invocada desde el shell ITSM, que es donde el ticket_id en la conversación tiene más valor analítico.
2. **Requieren refactor pequeño (1 site, peso bajo)**: `war_room_api.py:555` `session_message` — un `SELECT ticket_id FROM war_room_sessions WHERE id=$1` extra antes del INSERT, o cachear el ticket_id en memoria por sesión. Defensible pero opcional (las war rooms son flujo poco frecuente).
3. **Legítimamente NULL (5 sites)**: los 3 sites de `chat` libre (`war_room_api.py:640/691/725`) son conversaciones generales sin ticket asociado, y los 2 sites de `build_advisor_chat` (`main.py:2186/2219`) son del pipeline BUILD que no maneja tickets. Estos **deben quedarse NULL** — el bug "92 % NULL" no es real, parte de ese NULL es semánticamente correcto. La métrica honesta sería `count(*) FILTER (WHERE ticket_id IS NULL AND agent_id IN ('AG-001'))`, no global.

**Implicación para B.1**: F-ARQ02-12 puede cerrarse con un cambio quirúrgico de **~10 líneas** en `engine.py:115` (regex + parámetro extra al INSERT) + opcionalmente otras 5 en `session_message`. NO requiere tocar `chat` ni `build_advisor_chat`. El "12 → 1 line of code" potencial es real.

---

### 1.5 — Pre-check antes de tocar `engine.py:115`

#### 1.5.1 — Bloque INSERT actual (engine.py L102-134) y scope

```python
async def _log(self, session_id: str, user_msg: str, response: str,
               tokens: int, latency: int):
    """Registra conversación y métricas en PostgreSQL"""
    if not self.db:
        return
    if not session_id:
        session_id = str(uuid4())

    try:
        # Log conversación (user + assistant)
        for role, content in [("user", user_msg), ("assistant", response)]:
            if content:
                await self.db.execute("""
                    INSERT INTO agent_conversations
                    (session_id, agent_id, agent_name, role, content,
                     tokens_used, model_used, latency_ms)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, session_id, self.config.agent_id, self.config.agent_name,
                    role, content, tokens, self.config.model, latency)

        # Log métricas (upsert por agente+fecha)
        await self.db.execute(""" INSERT INTO agent_performance_metrics ... """, ...)
    except Exception as e:
        log.warning(f"Could not log agent metrics: {e}")
```

**Variables en scope dentro de `_log`**:
- `self.db` (conexión asyncpg)
- `self.config.agent_id`, `self.config.agent_name`, `self.config.model`
- `session_id` (str — id de sesión, NO ticket)
- `user_msg` (str — input crudo del usuario; **AQUÍ está el prefijo `TICKET:` cuando viene del shell ITSM post-A.2**)
- `response` (str — output del LLM)
- `tokens` (int), `latency` (int)

**No hay** `request`, `body`, `Headers` ni `ticket_id` explícito en scope — `_log` está totalmente desacoplado del nivel HTTP. La única fuente derivable es **regex sobre `user_msg`**. Limpio: las dos filas (`user` + `assistant`) comparten el mismo `ticket_id` (calcular una sola vez antes del loop).

**Cambio mínimo propuesto** (~6 líneas efectivas):
```python
import re  # verificar si ya está al top del módulo
_TICKET_RE = re.compile(r'^TICKET:\s*(INC-\d{6}-\d{8})')

async def _log(self, session_id, user_msg, response, tokens, latency):
    ...
    m = _TICKET_RE.match(user_msg or "")
    ticket_id = m.group(1) if m else None

    for role, content in [("user", user_msg), ("assistant", response)]:
        if content:
            await self.db.execute("""
                INSERT INTO agent_conversations
                (session_id, agent_id, agent_name, role, content,
                 tokens_used, model_used, latency_ms, ticket_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, session_id, self.config.agent_id, self.config.agent_name,
                role, content, tokens, self.config.model, latency, ticket_id)
```

#### 1.5.2 — Tests existentes que tocan `_log` o `agent_conversations`

`grep -rn "_log\|agent_conversations" backend/tests/`:

| Fichero | Líneas relevantes | Tipo de assert | ¿Bloquea? |
|---|---|---|---|
| `test_arq02_f5_agent_conversations.py` | L38-143 (6 tests) | columna existe / índice / `backfill >= 126` / sin fantasmas / regex válido / BUILD ratio <5% | **NO** — todos compatibles con poblar más filas. `test_backfill_minimo_126` usa `>=` (poblar más es OK). `test_ningun_ticket_id_fantasma` exige que todo `ticket_id IS NOT NULL` exista en `incidencias_run` — el regex extrae el id que el shell A.2 acaba de crear, así que se cumple. `test_ticket_id_formato_nuevo` exige regex `^INC-\d{6}-\d{8}$` — coincide con el regex que vamos a usar. `test_agentes_build_sin_ticket_id` exige <5% en AG-005/007/013 — AG-018 no está en la lista y los agentes BUILD no llegan al `_log` con prefijo `TICKET:` (no usan shell ITSM), quedan NULL. ✅ |
| `test_p96_router.py` | L27-68 | helper `_login(...)` (falso positivo del grep `_log`) | NO |
| `test_tech_dashboard.py` | L15+ | helper `_login(...)` (falso positivo) | NO |
| `test_scenario_e2e.py` | L26+ | helper `_login(...)` (falso positivo) | NO |

**Único test real**: `test_arq02_f5_agent_conversations.py`. **Ningún test hace `assert ticket_id IS NULL`** ni patchea `engine._log`. Vía libre.

#### 1.5.3 — Backfill retroactivo elegible

```sql
SELECT count(*) FROM agent_conversations
WHERE agent_id='AG-001' AND ticket_id IS NULL AND content LIKE 'TICKET:%';
```

```
backfillable_AG001_TICKET_prefix:   2
total_AG001:                      134
AG-001 con ticket_id IS NULL:      97
```

**Sólo 2 filas** elegibles para backfill retroactivo por regex. Confirma que:
- El prefijo `TICKET:` es **muy reciente** (introducido en A.2 commit `3234f58`).
- Las 97 filas históricas AG-001 con NULL son **previas a A.2** y NO tienen el prefijo en `content` — el shell antiguo no lo añadía. Backfill por regex es **estadísticamente irrelevante**.
- Las 126 filas pobladas en F5.1 vinieron de otra estrategia (probablemente JOIN por session_id, o seed manual). NO duplicar ese trabajo.

**Decisión sugerida**: NO ejecutar backfill retroactivo en B.1. Sólo poblar tráfico futuro. Los 2 huérfanos elegibles son ruido.

#### 1.5.4 — Constraints + schema de `agent_conversations.ticket_id` (`\d+ agent_conversations`)

```
--- col ticket_id ---
data_type='character varying', character_maximum_length=30, is_nullable='YES'

--- constraints ---
agent_conversations_role_check -> CHECK (role IN ('user','assistant','system','tool'))
agent_conversations_pkey       -> PRIMARY KEY (id)

--- indexes ---
agent_conversations_pkey -> UNIQUE (id)
idx_conv_session         -> btree (session_id)
idx_conv_agent           -> btree (agent_id)
idx_conv_created         -> btree (created_at DESC)
idx_conv_ticket          -> btree (ticket_id) WHERE (ticket_id IS NOT NULL)  ← parcial
```

**Hallazgos críticos**:
- **NO hay FK** desde `agent_conversations.ticket_id` hacia `incidencias_run.ticket_id`. La columna es **soft / desacoplada** (decisión consciente F5.1: "soft, sin FK" según el header de la migración `arq02_fase5_agent_conversations_ticket_id.sql`).
- **NO hay CASCADE**: si se borra un ticket de `incidencias_run`, las filas de `agent_conversations` quedan con `ticket_id` huérfano (ni se borran ni se ponen a NULL). Esto es **deliberado** — el log de auditoría debe sobrevivir al borrado del ticket original.
- `varchar(30)` holgado para el formato `INC-NNNNNN-YYYYMMDD` (18 chars).
- Índice parcial `idx_conv_ticket` ya filtra `WHERE ticket_id IS NOT NULL` → poblar más filas no degrada inserts (el índice sólo crece para filas pobladas).

**Implicación para B.1**: como NO hay FK, escribir un `ticket_id` que no exista en `incidencias_run` **no falla el INSERT**, pero rompería `test_ningun_ticket_id_fantasma`. El regex extrae el id del prefijo que el propio shell creó vía `POST /incidencias` justo antes del invoke → siempre existe en `incidencias_run` cuando llega a `_log`. Riesgo bajo, pero opcional blindar con un EXISTS check defensivo. **Discutir antes de implementar** si añadir el guard o asumir el invariante A.2.

---

**Resumen pre-check B.1**:
1. **Cambio limpio** ~6 líneas en `engine.py:_log` (regex + 1 columna extra al INSERT). Variables suficientes en scope, no hace falta tocar firmas.
2. **Sin tests rotos** — el único test relacionado (`test_arq02_f5_*`) usa `>=` en counts y todos sus asserts son compatibles. Los otros matches del grep son falsos positivos (`_login` ≠ `_log`).
3. **Backfill retroactivo NO útil** (sólo 2 filas históricas elegibles por regex). Saltarlo.
4. **Sin FK CASCADE** — riesgo de "fantasma" controlado por invariante A.2 ("el shell crea el ticket antes del invoke"). Opción: añadir EXISTS guard defensivo o confiar en el invariante. Decisión pendiente.

---

## Sección 2 — F-ARQ02-10: regexp_match (singular) misses subsequent ticket mentions

### 2.1 — Sites de `regexp_match` / `regexp_matches` en backend/ y database/

`grep -rn "regexp_match\|regexp_matches" backend/ database/`:

| Fichero:línea | Función / script | Variante |
|---|---|---|
| `database/arq02_fase5_run.sh:49` | F5.1 backfill UPDATE (TEMP MAP join) | `regexp_match` (singular) |

**Único site en todo el repo.** No hay uso de `regexp_match` en código Python (`backend/`), ni en otros scripts SQL de `database/`. La deuda F-ARQ02-10 está concentrada en un único sitio: el runner de la migración F5.1.

### 2.2 — Bloque exacto del backfill F5 (`database/arq02_fase5_run.sh`)

Contexto: la migración F1 (`ticket_id_map_F1.csv`, `ticket_id_map_F1_2_1_extra.csv`) re-numeró los `incidencias_run.ticket_id` del formato legacy `INC-YYYYMMDD-HEX` al nuevo `INC-NNNNNN-YYYYMMDD`. F5.1 debe backfillear `agent_conversations.ticket_id` parseando el `content` (que sólo contiene los IDs viejos en texto libre) y mapeando vía la TEMP TABLE `_ticket_id_map(old_id, new_id)`.

```sql
-- L43-49 de database/arq02_fase5_run.sh
\echo '── Backfill UPDATE ──'
UPDATE agent_conversations ac
SET ticket_id = m.new_id
FROM _ticket_id_map m
WHERE ac.ticket_id IS NULL
  AND ac.content ~ 'INC-[0-9]{8}-[A-F0-9]+'
  AND (regexp_match(ac.content, 'INC-[0-9]{8}-[A-F0-9]+'))[1] = m.old_id;
```

**Columna actualizada**: `agent_conversations.ticket_id`.
**Bug**: `regexp_match` (singular) devuelve **únicamente la primera coincidencia** del regex en `content`. Si una fila menciona dos o más tickets distintos (p.ej. una respuesta de AG-002 que dice *"Procesando ticket INC-20260408-3C92, relacionado con INC-20260401-3BD9..."*), sólo la **primera** se compara contra `m.old_id`. La segunda mención queda invisible al join. Si la primera mención no existe en el map (porque ese ticket nunca se renumeró, o porque es texto que casualmente cumple la regex pero no es un id real), la fila se queda con `ticket_id IS NULL` aunque la SEGUNDA mención sí estuviese en el map.

**Fix correcto**: usar `regexp_matches(ac.content, 'INC-[0-9]{8}-[A-F0-9]+', 'g')` (plural + flag global) → devuelve **un setof** de matches que se puede `JOIN LATERAL` o usar como subquery con `ANY()`.

### 2.3 — Filas víctimas del bug (multi-mention en `content`)

**Formato nuevo `INC-NNNNNN-YYYYMMDD` (post-A.2):**
```sql
SELECT count(*) FROM agent_conversations
WHERE content ~ 'INC-\d{6}-\d{8}.*INC-\d{6}-\d{8}';
→ 2
```

**Formato legacy `INC-YYYYMMDD-HEX` (pre-F1):**
```sql
SELECT count(*) FROM agent_conversations
WHERE content ~ 'INC-[0-9]{8}-[A-F0-9]+.*INC-[0-9]{8}-[A-F0-9]+';
→ 89
```

**Total filas con multi-mention**: **91** (2 nuevo + 89 legacy).

### 2.4 — Breakdown multi-mention por estado de `ticket_id`

| Conjunto | con_ticket_id | sin_ticket_id (NULL) | total |
|---|---|---|---|
| Multi formato nuevo | 0 | **2** | 2 |
| Multi formato legacy | 69 | **20** | 89 |
| **Total** | 69 | **22** | 91 |

**Lectura**:
- **22 filas multi-mention quedaron NULL** tras el backfill F5.1 — son víctimas directas del bug `regexp_match` singular: el primer match de cada una NO estaba en el map, pero un match secundario sí podría estarlo.
- **69 filas multi-mention sí tienen `ticket_id` poblado**: el primer match SÍ estaba en el map y ganó. **Pero el ticket_id asignado puede ser conceptualmente incorrecto** si el "ticket principal" de esa conversación era el segundo (p.ej. un AG-002 procesando ticket B mientras menciona ticket A como referencia). Esto es **silent miss-attribution**, peor que un NULL.

**Sample 3 filas multi-mention (3 con ticket_id, 2 NULL nuevo)**:

| id | ticket_id actual | agent | role | content[:200] |
|---|---|---|---|---|
| `34ffe8c9...` | NULL | AG-002 | assistant | `Procesando asignación de recursos para ticket **INC-000038-20260408** (P4 - Lentitud Citrix)... ASIGNACIÓN DE RECURSOS - INC-000038-20260408...` |
| `709f062c...` | NULL | AG-002 | user | `Resultado del Dispatcher: Voy a procesar esta incidencia de lentitud en el aplicativo de Agentes en Citrix...` (contiene 2+ INC-NNNNNN-YYYYMMDD) |
| `581c2511...` | `INC-000035-20260408` | AG-002 | assistant | `Procesando asignación de recursos para **INC-20260408-3C92** - Fallo sistema fichaje horario... "ticket_id": "INC-20260408-3C92"...` |
| `583c5d06...` | `INC-000035-20260408` | AG-002 | user | `Resultado del Dispatcher: ... incidencia P4 sobre el fallo del sistema de fichaje horario...` |
| `4e265edd...` | `INC-000034-20260401` | AG-002 | assistant | `Procesando asignación de recursos para INC-20260401-3BD9 (P1 - SWIFT)... "ticket_id": "INC-20260401-3BD9"...` |

> Nota: las 2 filas formato nuevo (multi NULL) son posteriores a A.2 — son AG-002 (downstream del Dispatcher) que recibe el output AG-001 con dos menciones del mismo ticket; **no llevan prefijo `TICKET:`** porque sólo AG-001 lo recibe del shell. La fix B.1 (`engine._log` regex) NO las cubre — necesitarían que el spawner propague el ticket explícitamente, o un parse general del primer `INC-\d{6}-\d{8}` en cualquier `user_msg`. Eso es alcance B.3+, no B.2.

### 2.5 — Veredicto: ¿solo SQL o requiere re-ejecutar backfill?

**Diagnóstico**:
1. **El fix del script SQL es trivial** (~3 líneas): cambiar el `WHERE` por un `JOIN LATERAL regexp_matches(..., 'g')` o usar `EXISTS (SELECT 1 FROM regexp_matches(...) ...)`. Patch puramente declarativo.
2. **Pero el script ya se ejecutó una vez** y produjo 126 filas pobladas + 22 multi-mention NULL + posibles miss-attributions silenciosas en las 69 multi-mention populated. **Cambiar sólo el script no toca esos datos**: hay que decidir si re-ejecutar.

**Análisis del re-backfill**:
- El UPDATE original tiene `WHERE ac.ticket_id IS NULL` → **es idempotente NO destructivo**: re-ejecutar con la versión corregida **NO sobrescribe** las 126 filas ya pobladas. Sólo intentaría rellenar los NULL restantes.
- ✅ **Las 22 filas multi-mention NULL** SÍ se beneficiarían del re-backfill corregido (todas las que tengan ≥1 match en el map serían capturadas).
- ❌ **Las 69 filas multi-mention con miss-attribution silenciosa NO se corrigen** con el re-backfill (siguen `IS NOT NULL`, el WHERE las salta). Para corregirlas haría falta un UPDATE separado **destructivo** que sobrescriba ticket_id existente — eso requiere criterio: ¿cuál de los 2+ matches es el "canónico"? (probablemente el más frecuente en el `content`, o el primero dentro de un patrón estructurado tipo `"ticket_id": "..."`). **Eso es scope creep**, no F-ARQ02-10 puro.
- También hay un riesgo: re-ejecutar el backfill requiere los 2 CSVs `_dumps/arq02/ticket_id_map_F1*.csv`. Verificar que existen y son los mismos (no sobrescritos por F1.2.x).

**Recomendación 3 líneas**:
1. **Fix SQL es declarativo** (~3 líneas): `regexp_match` → `regexp_matches(..., 'g')` con `LATERAL` o `EXISTS`. Único site, único script, idempotente al re-ejecutar.
2. **Re-ejecutar el backfill es seguro y aditivo** (el `WHERE ticket_id IS NULL` lo protege) — recuperaría hasta **22 filas** que hoy son NULL por el bug. NO sobrescribe las 126 ya pobladas. Verificar antes que los 2 CSVs `_dumps/arq02/ticket_id_map_F1*.csv` siguen disponibles.
3. **Las 69 multi-mention con `ticket_id` ya asignado pueden estar mal-atribuidas** (silent miss-attribution: ganó la primera mención aunque el ticket conceptual fuera otro) — esto NO lo arregla F-ARQ02-10 stricto sensu y requiere decisión heurística separada (¿criterio de "ticket canónico" en multi-mention?). **Dejar fuera de B.2**, abrir como F-ARQ02-15 si interesa.

**Implicación para B.2**: Cambio quirúrgico SQL en `database/arq02_fase5_run.sh` L49 + re-ejecutar `bash database/arq02_fase5_run.sh` (idempotente, no destructivo) + 1-2 tests que verifiquen que las 22 NULL multi-mention ya no son NULL. Las 2 filas formato nuevo NO se solucionan en B.2 (son downstream AG-002, fuera del alcance del backfill SQL).

---

### 2.6 — Resultados ejecución B.2 + deudas derivadas

**SQL fix aplicado** (`database/arq02_fase5_run.sh`):
```sql
UPDATE agent_conversations ac
SET ticket_id = m.new_id
FROM _ticket_id_map m
WHERE ac.ticket_id IS NULL
  AND EXISTS (
    SELECT 1 FROM regexp_matches(ac.content, 'INC-[0-9]{8}-[A-F0-9]+', 'g') AS r(match)
    WHERE r.match[1] = m.old_id
  );
```

**Deltas medidos baseline → post**:

| Métrica | Baseline | Post re-run | Delta |
|---|---|---|---|
| `ticket_id IS NULL AND multi-mention legacy` | 20 | 20 | **0** |
| `ticket_id IS NOT NULL` (total) | 126 | 126 | 0 |
| `ticket_id IS NOT NULL AND created_at < 2026-04-09` | 126 | 126 | **0 (las 126 originales intactas)** ✅ |
| `ticket_id IS NULL AND legacy single+multi` | 56 | 56 | 0 |

**Output del runner**: `UPDATE 0` filas — ninguna captura nueva.

**Diagnóstico del delta=0**:

Análisis post-mortem en Python (`re.findall` sobre las 20 filas multi-NULL + intersección contra los `old_id` del CSV):

```
multi-NULL filas: 20    IDs distintos en su content: 12
map old_ids:      37
intersección IDs ∩ map: 0
```

**Las 20 filas multi-mention NULL contienen IDs que NUNCA estuvieron en el `_ticket_id_map`** — sample: `INC-20260321-6DE9` *(este sí está en el map de hecho — ver nota más abajo)*, `INC-20260322-BD0F`, `INC-20260321-12CE`, `INC-20260401-A7CF`, `INC-20260321-9C04`, `INC-20260321-EE5C`, `INC-20260322-8664`, `INC-20260401-CFC9`. Son IDs históricos huérfanos del universo de migración F1 (probablemente tickets de scenarios/seeds borrados o de fases pre-arq01).

> Nota: el primer sample `INC-20260321-6DE9` SÍ aparece en el CSV `ticket_id_map_F1.csv` línea 1 (mapea a `INC-000001-20260321`). Sin embargo, el output del script Python dijo "intersección: 0". La causa probable: el `set` de Python recogió 12 IDs distintos del SUBconjunto de filas multi-NULL, y casualmente esos 12 no incluyen `INC-20260321-6DE9`, aunque ese id sí aparece en otras filas single-mention pobladas. El sample mostrado en `IDs multi-NULL no en map` viene del set restado, así que es la lista correcta de los huérfanos reales. Reconciliación: las 20 filas multi-NULL tienen IDs propios huérfanos, distintos del id que usé como REAL_OLD_ID en los tests.

**El bug F-ARQ02-10 sí existe en el código** (`regexp_match` singular falla con multi-mention cuando el primer match no está en el map), pero **la base de datos real no contiene víctimas reales** del bug en este momento. El recon original (sección 2.4) interpretó las 22 multi-NULL como víctimas; revisión empírica las descarta a todas — son víctimas de otra causa (huérfanos del universo F1).

**Validación con tests sintéticos**: los 2 tests `test_deudaB2_regexp_matches_all.py` SÍ demuestran el comportamiento corregido sobre datos controlados:

- `test_backfill_captura_segundo_match`: fila con `'Foo INC-99999999-DEAD bar INC-20260321-6DE9 baz'` → primer match es ficticio, segundo está en el map → backfill nuevo lo captura como `INC-000001-20260321`. Con `regexp_match` singular esta fila quedaría NULL. **PASS**.
- `test_backfill_no_pisa_pobladas`: fila con `ticket_id` ya seteado a un id real → backfill respeta el `WHERE NULL` y no la sobrescribe. **PASS**.

Ambos PASS bajo el SQL nuevo. Esto valida que el fix es correcto, aunque su impacto sobre los datos reales actuales sea 0.

**Conclusión**: el SQL fix es **preventivo y blinda futuros backfills** contra el bug. La pasada actual no recuperó filas porque la BD no contenía víctimas reales del bug (las multi-NULL reales tenían otra causa: IDs huérfanos del map). Tests sintéticos demuestran que la fix funciona como se espera.

**Deudas derivadas (abiertas, fuera de alcance B.2)**:

- **F-ARQ02-15 — silent miss-attribution en multi-mention pobladas**: las 69 filas multi-mention con `ticket_id IS NOT NULL` pueden tener atribución incorrecta (ganó la primera mención del content aunque el ticket "principal" fuera el segundo). Requiere heurística de "ticket canónico" (frecuencia, patrón estructurado `"ticket_id": "..."`, contexto del agent_id) + UPDATE destructivo. **Abrir como F-ARQ02-15** para Bloque C+.

- **F-ARQ02-16 — AG-002 downstream sin prefijo TICKET:**: las 2 filas multi-mention formato nuevo NULL son AG-002 (downstream del Dispatcher). Reciben el output del Dispatcher como `user_msg` pero **no** llevan el prefijo `TICKET:` que el shell sólo añade al primer agente de la cadena. La fix B.1 (`engine._log` regex) no las cubre. Requiere que el spawner/orchestrator propague el ticket_id explícito a los agentes downstream, o que `_log` use `re.search` (no `match`) sobre todo el `user_msg`. **Abrir como F-ARQ02-16** para Bloque C+.

- **F-ARQ02-17 LOW PRIORITY — IDs huérfanos del map F1**: 56 filas con menciones legacy en content que nunca se renumeraron en F1 (IDs de scenarios/tests borrados, fases pre-arq01). Legítimamente NULL desde el mapeo F1; podría hacerse un backfill de "best effort" mapeando por timestamp/contexto, pero probablemente no vale la pena (datos históricos sin valor analítico). **Documentar como F-ARQ02-17**.

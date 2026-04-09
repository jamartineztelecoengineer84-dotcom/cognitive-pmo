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

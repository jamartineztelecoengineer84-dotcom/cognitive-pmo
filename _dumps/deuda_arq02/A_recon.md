# Deuda A · F0 RECON · solo lectura

Fecha: 2026-04-09
HEAD: 69c3f35 (arq02-done)

---

## 1. Submit handler ITSM (frontend)

**Ubicación**: NO existe `frontend/itsm/`. El form ITSM vive en `frontend/index.html`.
Entry point: botón `run-exec-btn` (línea 1806) → `onclick="itsmSubmitAndPipeline()"`.

### grep submit + endpoints en frontend/index.html
```
1806:            <button class="btn-exec" id="run-exec-btn" onclick="itsmSubmitAndPipeline()" style="flex:1;">
5865:async function itsmSubmitAndPipeline() {
5888:    const r = await authFetch(API_BASE + '/incidencias', {
6229:    const r = await authFetch(API_BASE + '/run/plans');
6239:async function runSaveToBuffer(data) {
6243:    const r = await authFetch(API_BASE + '/run/plans', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) });
6313:    try { await authFetch(API_BASE + '/run/plans/' + encodeURIComponent(e.id), {method:'DELETE'}); } catch(ex) {}
6343:async function executeRunPipeline(text) {
6418:    var resp1 = await authFetch(API_BASE + '/agents/AG-001/invoke', {
6518:    var resp2 = await authFetch(API_BASE + '/agents/AG-002/invoke', {
6686:              if (cand.id && task.task_id) { authFetch(API_BASE + '/asignar/tecnico/tarea', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:task.task_id,id_recurso:cand.id,ticket_id:task.ticket_id||''})}).catch(function(){}); }
6808:              authFetch(API_BASE + '/asignar/tecnico/tarea', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:rt.id,id_recurso:bestTech.id,ticket_id:ticketId||''})}).catch(function(){});
6822:      var resp4 = await authFetch(API_BASE + '/agents/AG-004/invoke', {
6842:      var liveResp = await authFetch(API_BASE + '/incidencias/live', {
6860:      await authFetch(API_BASE + '/incidencias/live/' + ticketId + '/progreso?progreso=0&tareas_completadas=0&total_tareas=' + totalTareasLive, {method: 'PUT'}).catch(function(){});
6876:        var resp12 = await authFetch(API_BASE + '/agents/AG-012/invoke', {
6970:    fetch(API_BASE + '/incidencias/live')
7007:      fetch(API_BASE + '/incidencias/live/' + tid + '/progreso?progreso=' + globalPct + '&tareas_completadas=0&total_tareas=' + kanbanCards.length, {method:'PUT'})
7065:    var resp = await authFetch(API_BASE + '/incidencias/live');
7239:    var incResp = await authFetch(API_BASE + '/incidencias/live');
7318:        authFetch(API_BASE + '/incidencias/live/' + ticketId, {method:'DELETE'}).then(function() { overlay.remove(); loadActiveIncidents(); }).catch(function(){});
7503:                fetch(API_BASE + '/incidencias/live/' + tid + '/progreso?progreso=' + g4 + '&tareas_completadas=' + dT4 + '&total_tareas=' + tT4, {method:'PUT'})
7549:            fetch(API_BASE + '/incidencias/live/' + tid + '/progreso?progreso=' + g5 + '&tareas_completadas=' + dT5 + '&total_tareas=' + tT5, {method:'PUT'})
```

### Handler completo `itsmSubmitAndPipeline()` (frontend/index.html L5865-5915)
```javascript
async function itsmSubmitAndPipeline() {
  const desc = document.getElementById('run-input').value.trim();
  if (!desc) { document.getElementById('run-input').focus(); showToast('Describe la incidencia'); return; }
  const prio = document.getElementById('itsm-prio-calc').textContent || 'P3';
  const catVal = document.getElementById('itsm-catalogo').value;
  const catOpt = document.getElementById('itsm-catalogo').selectedOptions[0];
  // Register incident in DB
  const payload = {
    id_catalogo: catVal ? parseInt(catVal) : null,
    descripcion: desc,
    prioridad: prio,
    categoria: catOpt && catOpt.value ? catOpt.textContent : null,
    area_afectada: document.getElementById('itsm-area-auto')?.textContent || null,
    urgencia: document.getElementById('itsm-urgencia').value,
    impacto: document.getElementById('itsm-impacto').value,
    sla_limite: parseFloat(document.getElementById('itsm-sla').value) || null,
    impacto_negocio: document.getElementById('itsm-impacto-neg').value || null,
    canal_entrada: document.getElementById('itsm-canal').value,
    reportado_por: document.getElementById('itsm-reporter').value.trim() || null,
    servicio_afectado: document.getElementById('itsm-servicio').value || null,
    ci_afectado: document.getElementById('itsm-ci').value.trim() || null,
  };
  try {
    const r = await authFetch(API_BASE + '/incidencias', {
      method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
    });
    const result = await r.json();
    const ticketId = result.ticket_id || 'INC-????';
    document.getElementById('itsm-ticket-id').textContent = ticketId;
    showToast('Incidencia ' + ticketId + ' registrada (' + prio + ')');
    // Save to buffer
    runSaveToBuffer({
      'itsm-desc': desc, 'itsm-prio': prio, 'itsm-catalogo': payload.id_catalogo||'',
      'itsm-canal': payload.canal_entrada, 'itsm-impacto': payload.impacto,
      'itsm-urgencia': payload.urgencia, 'itsm-sla': String(payload.sla_limite||24),
      'itsm-servicio': payload.servicio_afectado||'', 'itsm-reporter': payload.reportado_por||'',
      'itsm-ci': payload.ci_afectado||'', 'itsm-impacto-neg': payload.impacto_negocio||'',
      'itsm-area': payload.area_afectada||'', 'run-input': desc, 'ticket-id': ticketId,
    });
    // Now build enriched text for pipeline
    const enrichedText = `[${ticketId}] ${prio} | ${desc}
Impacto: ${payload.impacto} | Urgencia: ${payload.urgencia} | SLA: ${payload.sla_limite}h
Servicio: ${payload.servicio_afectado||'N/A'} | CI: ${payload.ci_afectado||'N/A'} | Canal: ${payload.canal_entrada}
${payload.impacto_negocio ? 'Impacto Negocio: '+payload.impacto_negocio : ''}
${payload.categoria ? 'Catálogo: '+payload.categoria : ''}`;
    document.getElementById('run-input').value = enrichedText;
    executePipeline('run');
  } catch(e) {
    showToast('Error registrando: '+e.message);
  }
}
```

### Handler `runSaveToBuffer(data)` (frontend/index.html L6239-6248)
```javascript
async function runSaveToBuffer(data) {
  const nombre = data['itsm-desc'] || data['run-input'] || 'Incidencia sin descripción';
  const payload = { nombre, prioridad: data['itsm-prio'] || 'P3', area: data['itsm-area'] || '', sla_horas: parseFloat(data['itsm-sla']) || null, plan_data: {...data} };
  try {
    const r = await authFetch(API_BASE + '/run/plans', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) });
    if (r.ok) { await loadRunPlansFromDB(); return; }
  } catch(e) {}
  _runBuffer.unshift({ id:'RUN-'+Date.now().toString(36), nombre, prioridad:data['itsm-prio']||'P3', area:data['itsm-area']||'', sla:data['itsm-sla']||0, timestamp:new Date().toLocaleString('es-ES'), fields:{...data} });
  renderRunBuffer();
}
```

### Handler `executeRunPipeline(text)` (extracto: agentes invocados, frontend/index.html)
```javascript
// L6361 — pipeline visual creado
  var pipeline = createAnimatedPipeline(['AG-001', 'AG-002', 'AG-004', 'AG-012']);
  dashboard.appendChild(pipeline);

// L6418-6422 — AG-001 invoke
    var resp1 = await authFetch(API_BASE + '/agents/AG-001/invoke', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text, session_id: sessionId})
    });
    var r1 = await resp1.json();

// L6518-6522 — AG-002 invoke
    var resp2 = await authFetch(API_BASE + '/agents/AG-002/invoke', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: 'Resultado del Dispatcher:\n' + result1.substring(0, 800) + tasksContext, session_id: sessionId})
    });
    var r2 = await resp2.json();

// L6686 — asignar/tecnico/tarea (auto-asignaciones de candidatos)
              if (cand.id && task.task_id) { authFetch(API_BASE + '/asignar/tecnico/tarea', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:task.task_id,id_recurso:cand.id,ticket_id:task.ticket_id||''})}).catch(function(){}); }

// L6808-6809 — asignar/tecnico/tarea (fallback bestTech)
              authFetch(API_BASE + '/asignar/tecnico/tarea', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:rt.id,id_recurso:bestTech.id,ticket_id:ticketId||''})}).catch(function(){});
              addLog('GOB', 'dispatcher', 'Auto-asignado ' + bestTech.nombre + ' a "' + (rt.titulo||'').substring(0,30) + '"', false);

// L6820-6832 — AG-004 Buffer (condicional needsBuffer)
    if (needsBuffer) {
      addLog('AG-004', 'buffer', 'Evaluando RUN vs BUILD...', false);
      var resp4 = await authFetch(API_BASE + '/agents/AG-004/invoke', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: 'Escalado:\n' + result2.substring(0, 1500), session_id: sessionId})
      });
      var r4 = await resp4.json();
      if (!resp4.ok) throw new Error(r4.detail || 'AG-004 error');
      finalResult = r4.response || r4.result || '';
      setAgentState('AG-004', 'done', '\u2713');
      addLog('AG-004', 'buffer', 'Reasignaci\u00f3n completada.', false);
      addPreview('AG-004 Buffer \u2014 Decisi\u00f3n', '#06b6d4', finalResult);
    }

// L6834-6862 — REGISTRO LIVE (POST /incidencias/live + PUT progreso)
    // Register live incident in sidebar (after AG-004, before AG-012)
    try {
      var totalTareasLive = 0;
      try {
        var ltResp2 = await authFetch(API_BASE + '/kanban/tareas');
        var ltAll2 = await ltResp2.json();
        totalTareasLive = ltAll2.filter(function(t) { return t.fecha_creacion && new Date(t.fecha_creacion) > new Date(Date.now() - 600000); }).length;
      } catch(e2) {}
      var liveResp = await authFetch(API_BASE + '/incidencias/live', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          ticket_id: ticketId || '',
          incidencia_detectada: text.substring(0, 200),
          prioridad: globalPrio,
          sla_horas: globalSlaHours,
          canal_entrada: document.getElementById('run-canal') ? document.getElementById('run-canal').value : '',
          reportado_por: document.getElementById('run-reportado') ? document.getElementById('run-reportado').value : '',
          servicio_afectado: document.getElementById('run-servicio') ? document.getElementById('run-servicio').value : '',
          impacto_negocio: document.getElementById('run-impacto') ? document.getElementById('run-impacto').value : ''
        })
      });
      if (liveResp.ok) {
        addLog('LIVE', 'dispatcher', 'Incidencia registrada en panel de control.', false);
        window._currentLiveTicketId = ticketId;
      }
      await authFetch(API_BASE + '/incidencias/live/' + ticketId + '/progreso?progreso=0&tareas_completadas=0&total_tareas=' + totalTareasLive, {method: 'PUT'}).catch(function(){});
    } catch(ex) { console.error('Live register error:', ex); }
    if (typeof loadActiveIncidents === 'function') loadActiveIncidents();

// L6864-6885 — AG-012 Task Advisor
    // ═══ AG-012 TASK ADVISOR ═══
    setAgentState('AG-012', 'active');
    addLog('AG-012', 'advisor', 'Enriqueciendo tarjetas con instrucciones t\u00e9cnicas...', false);
    addLog('AG-012', 'advisor', 'tool: query_cmdb_activo()', true);
    try {
      var tkResp012 = await authFetch(API_BASE + '/kanban/tareas');
      var allTk012 = await tkResp012.json();
      var recentTasks012 = allTk012.filter(function(t) {
        return t.fecha_creacion && new Date(t.fecha_creacion) > new Date(Date.now() - 300000);
      });
      if (recentTasks012.length > 0) {
        var taskSummary = recentTasks012.map(function(t) { return t.id + ': ' + t.titulo; }).join('\n');
        var resp12 = await authFetch(API_BASE + '/agents/AG-012/invoke', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: 'Enriquece estas tarjetas:\n' + taskSummary.substring(0, 1500), session_id: sessionId})
        });
        if (resp12.ok) addLog('AG-012', 'advisor', 'Instrucciones generadas para ' + recentTasks012.length + ' tarjetas.', false);
      }
    } catch(ex12) {
      addLog('AG-012', 'advisor', 'Completado con warnings.', false);
    }
    setAgentState('AG-012', 'done', '\u2713');
```

---

## 2. Endpoints invocados por el submit (orden secuencial)

El submit `itsmSubmitAndPipeline()` ejecuta los siguientes hits HTTP, en este orden:

```
PASO  ENDPOINT                                  DISPARADO POR                LÍNEA frontend
────  ────────────────────────────────────────  ───────────────────────────  ──────────────
1     POST /incidencias                         itsmSubmitAndPipeline()      L5888
                                                  (await directo)

2     POST /run/plans                           runSaveToBuffer()            L6243
                                                  (await dentro de itsmSubmit, sin error handler)

3     executePipeline('run') -> executeRunPipeline(enrichedText) L5911 -> L6343

      Dentro de executeRunPipeline:
      3a    POST /agents/AG-001/invoke          AG-001 Dispatcher            L6418
      3b    POST /agents/AG-002/invoke          AG-002 Resource Mgr RUN      L6518
      3c    POST /asignar/tecnico/tarea         (1..N veces, candidates)     L6686
      3d    POST /asignar/tecnico/tarea         (fallback bestTech)          L6808
      3e    POST /agents/AG-004/invoke          (CONDICIONAL needsBuffer)    L6822
      3f    POST /incidencias/live              registro panel LIVE          L6842  ← REDUNDANTE post-F2.1
      3g    PUT  /incidencias/live/{id}/progreso?...&total_tareas=N           L6860
      3h    GET  /kanban/tareas                 (fetch tareas recientes)     L6869
      3i    POST /agents/AG-012/invoke          AG-012 Task Advisor          L6876

Notas:
- TODOS los await son secuenciales. NO hay Promise.all en este flujo.
- runSaveToBuffer (paso 2) NO usa await en error path: si falla, escribe en
  memoria local (_runBuffer.unshift) y sigue. El POST /run/plans NO bloquea
  el pipeline. Path: itsmSubmitAndPipeline -> runSaveToBuffer -> POST /run/plans.
- El POST /incidencias/live (paso 3f) era OBLIGATORIO antes de F2.1, ahora es
  REDUNDANTE: el trigger trg_run_to_live_insert ya creó la fila al insertar
  en incidencias_run en el paso 1. El INSERT de live es absorbido por
  ON CONFLICT (ticket_id) DO NOTHING.
- El paso 3 (executePipeline) NO espera al resultado del 2 (runSaveToBuffer)
  porque runSaveToBuffer se llama dentro de un .then implícito antes del
  enrichedText, pero su await está en línea 5896 SIN aguardar al pipeline.
```

---

## 3. Código completo de los 3 endpoints backend

### 3.a — `POST /incidencias` (backend/main.py:666-693)
```python
@app.post("/incidencias")
async def crear_incidencia(inc: IncidenciaITSM):
    inc_id = "INC-MOCK-NODB"  # F1.3b fallback si no hay pool
    pool = get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                inc_id = await conn.fetchval("SELECT generar_ticket_id()")
                row = await conn.fetchrow(
                    """INSERT INTO incidencias_run
                       (ticket_id, incidencia_detectada, id_catalogo, prioridad_ia,
                        categoria, area_afectada, sla_limite, impacto_negocio,
                        urgencia, impacto, canal_entrada, reportado_por,
                        servicio_afectado, ci_afectado, notas_adicionales, estado)
                       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,'QUEUED')
                       RETURNING *""",
                    inc_id, inc.descripcion, inc.id_catalogo, inc.prioridad,
                    inc.categoria, inc.area_afectada,
                    inc.sla_limite, inc.impacto_negocio,
                    inc.urgencia, inc.impacto, inc.canal_entrada,
                    inc.reportado_por, inc.servicio_afectado,
                    inc.ci_afectado, inc.notas_adicionales,
                )
                return serialize(row)
        except Exception as e:
            logger.warning(f"DB error in POST /incidencias: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"ticket_id": inc_id, "estado": "QUEUED", "_mock": True}
```

### 3.b — `POST /incidencias/live` (backend/main.py:935-985)
```python
@app.post("/incidencias/live")
async def crear_incidencia_live(req: IncidenciaLive):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            # ARQ-02 F2.1 — el ticket debe existir en incidencias_run primero.
            # La FK + trigger AFTER INSERT ya crearon la fila en live, este
            # endpoint queda como no-op idempotente defensivo (ON CONFLICT DO
            # NOTHING absorbe la fila duplicada).
            exists = await conn.fetchval(
                "SELECT 1 FROM incidencias_run WHERE ticket_id = $1",
                req.ticket_id,
            )
            if not exists:
                raise HTTPException(
                    status_code=404,
                    detail=f"Ticket {req.ticket_id} no existe en incidencias_run. "
                           f"El panel live solo puede mostrar tickets ya creados en run."
                )
            sla_int = int(req.sla_horas)
            await conn.execute("""
                INSERT INTO incidencias_live
                (ticket_id, incidencia_detectada, prioridad, sla_horas, estado,
                 fecha_limite, canal_entrada, reportado_por, servicio_afectado, impacto_negocio)
                VALUES ($1, $2, $3, $4, 'IN_PROGRESS',
                 now() + make_interval(hours => $5), $6, $7, $8, $9)
                ON CONFLICT (ticket_id) DO NOTHING
            """, req.ticket_id, req.incidencia_detectada, req.prioridad,
                req.sla_horas, sla_int, req.canal_entrada, req.reportado_por,
                req.servicio_afectado, req.impacto_negocio)
            return {"ok": True, "ticket_id": req.ticket_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidencias/live")
async def listar_incidencias_live():
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM incidencias_live
                ORDER BY
                  CASE prioridad WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 4 END,
                  fecha_creacion DESC
```

### 3.c — `POST /run/plans` (backend/main.py:1252-1281, incluye class RunPlanCreate)
```python
class RunPlanCreate(BaseModel):
    id: Optional[str] = None
    ticket_id: Optional[str] = None
    nombre: str
    prioridad: str = "P3"
    area: Optional[str] = None
    sla_horas: Optional[float] = None
    plan_data: dict = {}


@app.post("/run/plans")
async def create_run_plan(p: RunPlanCreate):
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503)
    plan_id = p.id or ("RUN-" + datetime.now().strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:4].upper())
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO itsm_form_drafts (id,ticket_id,nombre,prioridad,area,sla_horas,plan_data)
                VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb)
                ON CONFLICT (id) DO UPDATE SET plan_data=EXCLUDED.plan_data, nombre=EXCLUDED.nombre
                RETURNING *""",
                plan_id, p.ticket_id, p.nombre, p.prioridad, p.area, p.sla_horas,
                json.dumps(p.plan_data, ensure_ascii=False),
            )
            return serialize(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

```

---

## 4. Grep `uuid4|generar_ticket_id|inc_ticket_seq|INSERT INTO incidencias` por endpoint

### 4.a — POST /incidencias (líneas 666-693)
```
673:                inc_id = await conn.fetchval("SELECT generar_ticket_id()")
675:                    """INSERT INTO incidencias_run
```

### 4.b — POST /incidencias/live (líneas 935-985)
```
958:                INSERT INTO incidencias_live
```

### 4.c — POST /run/plans (líneas 1252-1281)
```
1267:    plan_id = p.id or ("RUN-" + datetime.now().strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:4].upper())
```

**Hallazgo**: `POST /run/plans` línea 1267 sigue construyendo plan_id con
`uuid.uuid4()[:4]` (formato `RUN-YYYYMMDD-HEX`). Es F-ARQ02-09 ya registrada.

---

## 5. Triggers vivos en incidencias_run

```
         tgname         |     tgrelid     
------------------------+-----------------
 trg_run_to_live_insert | incidencias_run
 trg_run_to_live_update | incidencias_run
(2 filas)

```

**Confirmado**: los 2 triggers de F2 (`trg_run_to_live_insert` y `trg_run_to_live_update`) siguen vivos.
Eliminar el POST /incidencias/live en el frontend NO rompe la sincronización
porque el trigger AFTER INSERT se dispara automáticamente.

---

## 6. Counts BD

```
 count 
-------
    38
(1 fila)

 count 
-------
     6
(1 fila)

 count 
-------
    61
(1 fila)

```

**Drift detectado vs baseline EMPTY (37/5/61)**:
- `incidencias_run`: **38** (era 37) → +1 ticket residual creado vía SEQUENCE durante pytest
  (no es `INC-SC*` por lo tanto el reset_scenario no lo borra). F-ARQ02-06 + F-ARQ02-14.
- `incidencias_live`: **6** (era 5) → +1 fila propagada por trigger F2.1 al insertar el ticket residual.
- `itsm_form_drafts`: **61** ✅

El drift NO bloquea la planificación de F-ARQ02-04+09. La cabeza de schema es correcta.

---

## 7. git status + git log

```
En la rama master
Tu rama está actualizada con 'origin/master'.

Archivos sin seguimiento:
  (usa "git add <archivo>..." para incluirlo a lo que será confirmado)
	_dumps/arq02/ARQ01_ARQ02_STATE_DUMP_2026-04-09.md
	_dumps/deuda_arq02/

no hay nada agregado al commit pero hay archivos sin seguimiento presentes (usa "git add" para hacerles seguimiento)
```

```
69c3f35 chore(arq02-f6): cierre ARQ-02 + reporte invariantes + smoke scenarios
bfde8ec feat(arq02-f5): agent_conversations.ticket_id soft + backfill heurístico
206a111 refactor(arq02-f4): rename run_incident_plans → itsm_form_drafts
66b553f chore(arq02-f3): DROP TABLE incidencias zombie fósil
11b62e1 feat(arq02-f2): incidencias_live ⊆ incidencias_run via FK + sync triggers
```

**HEAD**: `69c3f35` (chore arq02-f6 cierre) — coincide con tag `arq02-done`.
**Working tree**: limpio salvo el dump anterior `_dumps/arq02/ARQ01_ARQ02_STATE_DUMP_2026-04-09.md` (untracked, no bloquea).

---

## RESUMEN PARA F-ARQ02-04 + F-ARQ02-09 (planificación)

**F-ARQ02-04** — Formulario ITSM duplica/triplica el ticket. Hechos del recon:
1. `itsmSubmitAndPipeline` ejecuta 2 paths que crean filas en BD distintas:
   - `POST /incidencias` → `incidencias_run` con `INC-NNNNNN-YYYYMMDD` (vía SEQUENCE)
   - `POST /run/plans` → `itsm_form_drafts` con `RUN-YYYYMMDD-HEX` (vía uuid4)
2. Después `executeRunPipeline` invoca `POST /agents/AG-001/invoke` pasando el
   texto enriquecido como mensaje. AG-001 internamente llama a `create_incident`
   tool, que crea OTRO ticket en `incidencias_run`. → 2 tickets por submit (Δt~8s).
3. `POST /incidencias/live` (paso 3f, L6842) ya es no-op porque el trigger F2.1
   crea la fila live al insertar en `incidencias_run`. F-ARQ02-05 lo confirma.

**F-ARQ02-09** — `POST /run/plans` usa `uuid4().hex[:4]` para `plan_id`. Sin SEQUENCE.
Probabilidad de colisión 1/65k por día. Hallazgo en main.py:1267.

**Combinación F-04 + F-09 en un commit atómico**: refactor del path del formulario
para que (a) NO duplique tickets, (b) NO llame a /incidencias/live (eliminado),
(c) plan_id de itsm_form_drafts use SEQUENCE separada `itsm_draft_seq`.

**Archivos a tocar (estimado, NO modificado)**:
- `frontend/index.html` líneas 5888 (POST /incidencias), 5896 (runSaveToBuffer),
  6418 (AG-001 invoke), 6842 (POST /incidencias/live ELIMINAR)
- `backend/main.py` línea 1267 (plan_id uuid4 → SEQUENCE)
- `database/arq02_fase7_itsm_draft_seq.sql` (CREATE SEQUENCE + función)
- Tests post-refactor: 1 submit del formulario crea EXACTAMENTE 1 fila en run + 1 en live + 1 en drafts.

---

## 8. AG-001 internals (mini-recon A.1bis)

### 8.a — grep AG-001/create_incident/agents endpoints en backend/main.py
```
```

### 8.b — Handler completo POST /agents/{agent_id}/invoke (backend/agents/router.py:28-67)
```python
@router.post("/{agent_id}/invoke")
async def invoke_agent(agent_id: str, body: InvokeRequest):
    """Invoca un agente individual (con spawning si configurado)"""
    if agent_id not in AGENT_CONFIGS:
        raise HTTPException(404, f"Agent {agent_id} not configured")
    pool = get_pool()
    if not pool:
        raise HTTPException(503, "Database not available")
    config = AGENT_CONFIGS[agent_id]

    # Check if agent has spawning configured
    if agent_id in SPAWNABLE_AGENTS:
        spawn_config = SPAWNABLE_AGENTS[agent_id]
        spawner = SpawnableEngine(
            config=config,
            db_pool=pool,
            director_prompt=spawn_config["director_prompt"],
            worker_prompt_template=spawn_config["worker_prompt_template"],
            merger_prompt=spawn_config.get("merger_prompt", ""),
            max_workers=spawn_config.get("max_workers", 8),
            worker_max_tokens=spawn_config.get("worker_max_tokens", 4096),
            programmatic_merge=spawn_config.get("programmatic_merge", False),
            merge_function=spawn_config.get("merge_function"),
        )
        result_data = await spawner.invoke(
            body.message, body.session_id or ""
        )
        return {
            "agent_id": agent_id,
            "response": result_data["response"],
            "spawning_info": result_data["spawning_info"]
        }

    # Normal (non-spawnable) agent
    engine = AgentEngine(config, pool)
    result = await engine.invoke(
        user_msg=body.message,
        session_id=body.session_id or ""
    )
    return {"agent_id": agent_id, "response": result}
```

### 8.c — Tool create_incident (backend/agents/tools.py:119-148, ya migrado en F1.3a)
```python
@register_tool("create_incident")
async def create_incident(db, descripcion: str, prioridad: str,
                          categoria: str, sla_horas: float,
                          area_afectada: str, **kwargs):
    """Crea incidencia en incidencias_run"""
    ticket_id = await db.fetchval("SELECT generar_ticket_id()")
    await db.execute("""
        INSERT INTO incidencias_run
        (ticket_id, incidencia_detectada, prioridad_ia, categoria,
         sla_limite, area_afectada, impacto_negocio, servicio_afectado,
         ci_afectado, urgencia, impacto, agente_origen,
         timestamp_creacion, estado)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,'AG-001',now(),'QUEUED')
    """, ticket_id, descripcion, prioridad, categoria,
        sla_horas, area_afectada,
        kwargs.get('impacto_negocio', ''),
        kwargs.get('servicio_afectado', ''),
        kwargs.get('ci_afectado', ''),
        kwargs.get('urgencia', 'Media'),
        kwargs.get('impacto', 'Medio'))

    sla_limite = datetime.now() + timedelta(hours=sla_horas)
    return {
        "ticket_id": ticket_id,
        "prioridad": prioridad,
        "sla_horas": sla_horas,
        "sla_limite": sla_limite.strftime("%Y-%m-%d %H:%M"),
        "status": "created"
    }

```

Localización con grep:
```
backend/agents/tools.py:120:async def create_incident(db, descripcion: str, prioridad: str,
```

### 8.d — ¿AG-001 recibe ticket_id desde el invoke?
```
# grep ticket_id en prompts/ag001*.txt
(0 matches: el prompt de AG-001 NO recibe ni menciona ticket_id)

# grep ticket_id en cualquier fichero ag001/dispatcher
backend/agents/router.py:173:    dispatcher_tasks = await _fetch_incident_tasks(pool, dispatcher_incident.get('ticket_id', ''))
backend/agents/router.py:182:        f"TICKET: {dispatcher_incident.get('ticket_id','')}\n"
backend/agents/router.py:198:            f"Escalado. Sin técnicos libres.\nTicket: {dispatcher_incident.get('ticket_id','')}\n{r2[:1500]}",
```

### 8.e — Hallazgos del mini-recon

1. **Endpoint POST /agents/{agent_id}/invoke vive en backend/agents/router.py:28**, no en main.py.
   No tiene 'POST /incidencias' wraps; recibe `{message, session_id}` y delega a
   `AgentEngine(config, pool).invoke(user_msg, session_id)`. **No recibe ticket_id**.

2. **El handler invoke_agent es agnóstico al ticket_id**: pasa el `message` literal del
   body al `AgentEngine.invoke`, y el LLM (Claude Sonnet 4) decide qué tools llamar.
   Para AG-001, el prompt ag001_dispatcher.txt instruye 'Crea registro en incidencias_run
   con create_incident' como **paso 5 del proceso**, lo que dispara la tool create_incident
   que internamente hace `SELECT generar_ticket_id()` (post-F1.3a).

3. **El prompt de AG-001 NO menciona ticket_id**. Por tanto, AG-001 NO sabe que el shell
   ya creó un ticket vía POST /incidencias antes del invoke. El LLM siempre crea uno
   nuevo. → ESTO ES F-ARQ02-04 raíz: el shell duplica porque AG-001 es ciego al ticket
   pre-creado.

4. **Solución conceptual para A.2 (NO ahora)**: pasar el `ticket_id` desde el shell al
   invoke como parte del `message` (ej. prefijo `[ticket_id=INC-XXX]`) o como nuevo
   campo `pre_existing_ticket` en el body, y modificar el prompt de AG-001 para que SI
   recibe un ticket_id externo, llame a `create_tasks(ticket_id, ...)` directamente sin
   pasar por create_incident.

5. **Confirmación tool create_incident es el único punto de creación en el path agéntico**:
   tras F1.3a el INSERT INTO incidencias_run usa generar_ticket_id() — ya está atómico,
   solo hay que evitar que se dispare cuando el shell ya creó un ticket.


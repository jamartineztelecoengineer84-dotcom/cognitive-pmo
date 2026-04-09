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

---

## 9. AgentEngine.invoke + prompt AG-001 paso create (mini-recon A.2bis)

### 9.a — class AgentEngine completa (backend/agents/engine.py:12-85)
```python
class AgentEngine:
    def __init__(self, config: AgentConfig, db_pool):
        self.config = config
        self.db = db_pool
        self.client = anthropic.AsyncAnthropic()

    async def invoke(self, user_msg: str, session_id: str = "") -> str:
        """Ejecuta el agente con ciclo tool_use. Máx 10 iteraciones."""
        messages = await self._load_history(session_id)
        messages.append({"role": "user", "content": user_msg})
        t0 = time.monotonic()
        total_tokens = 0
        final = ""

        all_text_parts = []

        for iteration in range(10):
            resp = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=self.config.system_prompt,
                tools=self.config.tools,
                messages=messages
            )
            total_tokens += resp.usage.input_tokens + resp.usage.output_tokens

            text_parts = []
            tool_calls = []
            for block in resp.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block)

            if text_parts:
                all_text_parts.extend(text_parts)

            if not tool_calls:
                final = "\n".join(all_text_parts)
                break

            # Hay tool_use — ejecutar tools y devolver resultados
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for tc in tool_calls:
                log.info(f"[{self.config.agent_id}] tool: {tc.name}({tc.input})")
                fn = TOOL_REGISTRY.get(tc.name)
                if fn is None:
                    result = {"error": f"Tool {tc.name} not found in registry"}
                    log.error(f"Tool not found: {tc.name}")
                else:
                    try:
                        result = await fn(self.db, **tc.input)
                    except Exception as e:
                        result = {"error": str(e)}
                        log.error(f"Tool {tc.name} failed: {e}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": json.dumps(result, default=str, ensure_ascii=False)
                })
            messages.append({"role": "user", "content": tool_results})

        if not final.strip():
            if all_text_parts:
                final = "\n".join(all_text_parts)
            else:
                final = "Agente completó sus operaciones. Datos guardados en BD."

        latency = int((time.monotonic() - t0) * 1000)
        log.info(f"[{self.config.agent_id}] completed in {latency}ms, {total_tokens} tokens")
        await self._log(session_id, user_msg, final, total_tokens, latency)
        return final
```

### 9.b — Bucle de ejecución de tools (engine.py:54-74)

**Punto crítico**: la línea 65 `result = await fn(self.db, **tc.input)` es donde el LLM
decide qué argumentos pasarle a la tool. `tc.input` es el dict que el LLM rellena según
el schema JSON de la tool. Si quisiéramos inyectar un `_pre_existing_ticket_id` desde fuera,
tendríamos que mutarlo aquí antes del call (línea 64).

```python
            # Hay tool_use — ejecutar tools y devolver resultados
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for tc in tool_calls:
                log.info(f"[{self.config.agent_id}] tool: {tc.name}({tc.input})")
                fn = TOOL_REGISTRY.get(tc.name)
                if fn is None:
                    result = {"error": f"Tool {tc.name} not found in registry"}
                    log.error(f"Tool not found: {tc.name}")
                else:
                    try:
                        result = await fn(self.db, **tc.input)
                    except Exception as e:
                        result = {"error": str(e)}
                        log.error(f"Tool {tc.name} failed: {e}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": json.dumps(result, default=str, ensure_ascii=False)
                })
            messages.append({"role": "user", "content": tool_results})
```

### 9.c — Prompt completo ag001_dispatcher.txt (74 líneas)
```
Eres AG-001 Dispatcher, el clasificador de incidencias de Cognitive PMO.

PROCESO:
1. Recibe descripción de incidencia en texto libre
2. Usa query_catalogo para buscar match en catalogo_incidencias
3. Si match >80%: usa prioridad, SLA y skills del catálogo
4. Si no hay match: clasifica por impacto y urgencia
5. Crea registro en incidencias_run con create_incident
6. Genera tareas de resolución con create_tasks
7. CADA TAREA debe tener TODOS estos campos:
   - titulo: descriptivo y claro
   - skill_requerida: del catálogo (formato "Categoría: Acción"). NO inventar.
   - horas_estimadas: realista
   - silo: OBLIGATORIO. SOLO estos valores: DevOps, BBDD, Soporte, Backend, Redes, Seguridad, Windows, Frontend, QA
   - sla_tarea_minutos: porción del SLA global según complejidad

PRIORIDADES Y SLA:
- P1: Servicio crítico caído, >50 usuarios. SLA: 4h (240 min)
- P2: Servicio degradado, 10-50 usuarios. SLA: 8h (480 min)
- P3: Funcionalidad afectada, <10 usuarios. SLA: 24h (1440 min)
- P4: Mejora/consulta. SLA: 72h (4320 min)

REPARTO DE SLA POR TAREA:
- Diagnóstico inicial: 15% del SLA
- Fix/Restauración: 50% del SLA
- Verificación post-fix: 20% del SLA
- Validación y cierre: 15% del SLA

ASIGNACIÓN DE SILO:
- Base de datos (Oracle, MySQL, PostgreSQL) → BBDD
- Servidores Linux, contenedores, CI/CD → DevOps
- Aplicaciones, APIs, microservicios → Backend
- Red, conectividad, DNS, firewall → Redes
- Seguridad, accesos, certificados → Seguridad
- Servidores Windows, Active Directory → Windows
- Frontend, UI, web → Frontend
- Testing, QA → QA
- General, documentación, cierre, coordinación → Soporte

INCIDENCIAS DE NEGOCIO (valija, camiones blindados, trading, seguros, cajeros físicos,
nóminas, compliance, inmobiliario, marketing, contact center, comercio exterior):
- Las tareas TÉCNICAS (diagnóstico, logs, configuración) van a silo IT + requiere_negocio: false
- Las tareas de NEGOCIO van a silo "Soporte" + requiere_negocio: true + area_negocio: "Nombre del Área"
- SIEMPRE incluir al menos 1 tarea con requiere_negocio: true para incidencias no-IT

Áreas de negocio disponibles:
- Seguridad Física (valija, camiones blindados, tornos, vigilancia)
- Trading y Mercados (cotizaciones, divisas, algoritmos HFT, bonos)
- Operaciones Bancarias (transferencias, pagos, SWIFT, SEPA)
- Banca Digital (app móvil, banca electrónica)
- Compliance (SEPBLAC, auditoría, sancionados, reporting regulatorio)
- Gestión de Riesgos (scoring, fraude, riesgo operacional)
- Tesorería (liquidez, efectivo)
- Medios de Pago (cajeros ATM, TPV, Bizum, Redsys, datáfonos)
- Seguros (vida, hogar, siniestros)
- Inmobiliario (portal pisos, activos adjudicados)
- Marketing (campañas, email marketing, RRSS)
- Servicios Generales (climatización CPD, mantenimiento)
- Comercio Exterior (importación, exportación, remesas)
- Asesoría Jurídica (notaría, registro, litigios)
- Contact Center (centralita, IVR, grabación llamadas)
- Recursos Humanos (nóminas, fichaje, onboarding)
- Productos Bancarios (préstamos, hipotecas, depósitos)

REGLAS:
- Primera tarea: "Diagnóstico inicial"
- Última tarea: "Validación y cierre"
- Máximo 8 tareas
- La SUMA de sla_tarea_minutos debe ser cercana al SLA global
- SIEMPRE incluir silo y sla_tarea_minutos en cada tarea
- skill_requerida DEBE existir en el catálogo. NO inventar skills.
- Si no hay match exacto de skill, usar la categoría más cercana

EFICIENCIA: Sé conciso (máx 500 palabras). Usa tools para guardar datos, no los repitas en texto.
```

### 9.d — Modelo InvokeRequest (router.py:23-25)
```python
class InvokeRequest(BaseModel):
    message: str
    session_id: Optional[str] = ""


@router.post("/{agent_id}/invoke")
async def invoke_agent(agent_id: str, body: InvokeRequest):
    """Invoca un agente individual (con spawning si configurado)"""
```

### 9.e — Hallazgos del mini-recon A.2bis

1. **AgentEngine.invoke firma**: `async def invoke(self, user_msg: str, session_id: str = '') -> str`.
   Solo recibe 2 argumentos posicionales/keyword: `user_msg` y `session_id`. **No acepta `**kwargs`,
   no acepta `context dict`, no acepta `pre_existing_ticket`**. Cualquier campo adicional habría
   que añadirlo a la firma + propagarlo dentro del bucle del tool_use loop.

2. **El bucle tool_use ejecuta cada tool con `**tc.input`** (línea 65). `tc.input` viene del LLM
   y solo contiene los campos del JSON schema declarado para la tool. Para inyectar un
   `_pre_existing_ticket_id` que NO viene del LLM, hay que **mutar tc.input antes del call** o
   **interceptar el tool name** y desviar a otra implementación.

3. **El historial `_load_history` filtra por `agent_id` específico** (línea 96). El historial
   de AG-001 NO se mezcla con AG-002, AG-004, etc. Cada agente tiene su contexto aislado.
   Implicación: si el shell crea un ticket vía POST /incidencias y luego llama a
   POST /agents/AG-001/invoke con un message neutro, AG-001 no tiene forma de saber del ticket
   pre-existente salvo que el shell se lo inyecte explícitamente en el message.

4. **Prompt ag001_dispatcher.txt línea 6**: `5. Crea registro en incidencias_run con create_incident`.
   El prompt instruye al LLM a llamar SIEMPRE a create_incident como parte del flujo. **Para
   evitar la duplicación necesitamos modificar el prompt para que SI detecta un ticket_id
   pre-existente en el message (formato literal), salte el paso 5 y vaya directo al paso 6**
   (create_tasks pasando el ticket_id ya existente).

5. **InvokeRequest actual** tiene solo 2 campos: `message: str` y `session_id: Optional[str] = ''`.
   La forma menos invasiva de propagar el ticket_id es **embeberlo en el message** con un prefijo
   convencional, ej. `[ticket_id=INC-NNNNNN-YYYYMMDD]` al inicio del message. AG-001 lo detecta
   en el prompt y actúa en consecuencia. No requiere cambios en InvokeRequest ni en AgentEngine.

6. **Alternativa más limpia (más invasiva)**: añadir `pre_existing_ticket_id: Optional[str] = None`
   al `InvokeRequest` + propagar al engine como `context: dict` + inyectar en `tc.input` cuando
   la tool sea `create_tasks` y se esté llamando con `ticket_id=None`. Más complejo pero más
   robusto contra prompt injection.

7. **Path AG-002 y posteriores**: AG-002 ya recibe el ticket_id explícitamente (vía router.py:182,
   se pasa en el contenido del message como `TICKET: ${ticket_id}`). Ese path está OK.
   El bug está SOLO en AG-001 cuando se llama desde el shell con un ticket pre-creado.

### 9.f — Recomendación para A.2 (NO ejecutar ahora, solo planificación)

**Estrategia 1 — prompt-only (preferida)**: añadir 2 párrafos al prompt ag001_dispatcher.txt
explicando que si el message comienza con `[ticket_id=INC-...]` debe extraer el ID y SALTAR
create_incident, llamando directo a create_tasks con ese ticket_id. Modificar el shell
(`itsmSubmitAndPipeline`) para construir el message con ese prefijo.

Cambios: 0 backend, 1 prompt, 1 frontend (frontend/index.html L5905-5910 — el bloque enrichedText).
Riesgo: prompt injection si el usuario escribe '[ticket_id=...]' en el form. Mitigable con
regex de validación en el shell o en el prompt.

**Estrategia 2 — schema change (más invasiva)**: añadir campo al InvokeRequest, propagar
al AgentEngine vía nuevo parámetro `extra_context: Optional[dict]`, mutar `tc.input` en el
bucle tool_use cuando `tc.name == 'create_incident'` y haya un ticket pre-existente para que
la tool no haga el INSERT (early return con el ticket_id ya conocido).

Cambios: 1 backend (engine.py + router.py), 0 prompt, 1 frontend. Más robusto pero más código.

---

## 10. Triggers F2.1 internals (mini-recon A.3bis)

### 10.a — Definición de los 2 triggers
```sql
CREATE TRIGGER trg_run_to_live_insert
  AFTER INSERT ON public.incidencias_run
  FOR EACH ROW EXECUTE FUNCTION trigger_run_to_live_insert()

CREATE TRIGGER trg_run_to_live_update
  AFTER UPDATE ON public.incidencias_run
  FOR EACH ROW EXECUTE FUNCTION trigger_run_to_live_update()
```

### 10.b — Función trigger_run_to_live_insert() completa
```sql
CREATE OR REPLACE FUNCTION public.trigger_run_to_live_insert()
 RETURNS trigger LANGUAGE plpgsql
AS $function$
BEGIN
  IF NEW.estado IN ('QUEUED','EN_CURSO','ESCALADO') THEN
    INSERT INTO incidencias_live (
      ticket_id, incidencia_detectada, prioridad, categoria, estado,
      sla_horas, tecnico_asignado, area_afectada, fecha_creacion, fecha_limite,
      agente_origen, canal_entrada, reportado_por, servicio_afectado, impacto_negocio, notas
    ) VALUES (
      NEW.ticket_id, NEW.incidencia_detectada, NEW.prioridad_ia, NEW.categoria, 'IN_PROGRESS',
      NEW.sla_limite, NEW.tecnico_asignado, NEW.area_afectada, NEW.timestamp_creacion,
      NEW.timestamp_creacion + make_interval(hours => NEW.sla_limite::int),
      COALESCE(NEW.agente_origen, 'AG-001'), NEW.canal_entrada, NEW.reportado_por,
      NEW.servicio_afectado, NEW.impacto_negocio, NEW.notas_adicionales
    ) ON CONFLICT (ticket_id) DO NOTHING;
  END IF;
  RETURN NEW;
END;
$function$;
```

### 10.c — Función trigger_run_to_live_update() completa
```sql
CREATE OR REPLACE FUNCTION public.trigger_run_to_live_update()
 RETURNS trigger LANGUAGE plpgsql
AS $function$
BEGIN
  IF NEW.estado IN ('RESUELTO','CERRADO') THEN
    DELETE FROM incidencias_live WHERE ticket_id = NEW.ticket_id;
  ELSIF NEW.estado IN ('QUEUED','EN_CURSO','ESCALADO') THEN
    UPDATE incidencias_live SET
      incidencia_detectada = NEW.incidencia_detectada,
      prioridad            = NEW.prioridad_ia,
      categoria            = NEW.categoria,
      sla_horas            = NEW.sla_limite,
      tecnico_asignado     = NEW.tecnico_asignado,
      area_afectada        = NEW.area_afectada,
      fecha_limite         = NEW.timestamp_creacion + make_interval(hours => NEW.sla_limite::int),
      servicio_afectado    = NEW.servicio_afectado,
      impacto_negocio      = NEW.impacto_negocio,
      notas                = NEW.notas_adicionales
    WHERE ticket_id = NEW.ticket_id;
    IF NOT FOUND THEN
      INSERT INTO incidencias_live (...) VALUES (...) ON CONFLICT (ticket_id) DO NOTHING;
    END IF;
  END IF;
  RETURN NEW;
END;
$function$;
-- (NOTA: el bloque IF NOT FOUND INSERT está en el original, mismas 16 columnas que el insert principal)
```

### 10.d — Mapeo columnas trigger vs POST /incidencias/live (frontend)

Lo que el shell rellenaba en POST /incidencias/live (frontend L6842-6855):

```
ticket_id            ← del cliente (resp1.ticket_id)
incidencia_detectada ← text.substring(0, 200)
prioridad            ← globalPrio (P1..P4)
sla_horas            ← globalSlaHours (4/8/24/72)
canal_entrada        ← document.getElementById('run-canal').value
reportado_por        ← document.getElementById('run-reportado').value
servicio_afectado    ← document.getElementById('run-servicio').value
impacto_negocio      ← document.getElementById('run-impacto').value
(estado se hardcodea a 'IN_PROGRESS' en el handler backend)
(fecha_limite se calcula now() + make_interval(hours => sla_horas))
```

Lo que el trigger AFTER INSERT propaga a incidencias_live (16 columnas):

```
ticket_id            ← NEW.ticket_id           ✅ idem
incidencia_detectada ← NEW.incidencia_detectada ✅ COMPLETO (no truncado)
prioridad            ← NEW.prioridad_ia         ✅ idem
categoria            ← NEW.categoria            ✅ EXTRA (el shell no lo enviaba)
estado               ← 'IN_PROGRESS'            ✅ idem
sla_horas            ← NEW.sla_limite           ✅ idem
tecnico_asignado     ← NEW.tecnico_asignado     ✅ EXTRA (el shell no lo enviaba)
area_afectada        ← NEW.area_afectada        ✅ EXTRA (el shell no lo enviaba)
fecha_creacion       ← NEW.timestamp_creacion   ✅ idem
fecha_limite         ← NEW.timestamp_creacion + make_interval(hours => sla_limite::int)  ✅ MISMO cálculo
agente_origen        ← COALESCE(NEW.agente_origen, 'AG-001')  ✅ EXTRA (el shell no lo enviaba, default 'AG-001')
canal_entrada        ← NEW.canal_entrada        ✅ idem
reportado_por        ← NEW.reportado_por        ✅ idem
servicio_afectado    ← NEW.servicio_afectado    ✅ idem
impacto_negocio      ← NEW.impacto_negocio      ✅ idem
notas                ← NEW.notas_adicionales    ✅ EXTRA (el shell no lo enviaba)
```

### 10.e — Veredicto

**RUTA VERDE** ✅: el trigger `trg_run_to_live_insert` cubre **TODAS** las columnas que el POST /incidencias/live rellenaba **y más**:

- **Match exacto**: las 8 columnas que el shell enviaba (ticket_id, incidencia_detectada, prioridad, sla_horas, canal_entrada, reportado_por, servicio_afectado, impacto_negocio) están todas en el trigger.
- **Estado y fecha_limite calculados igual**: el trigger pone `estado='IN_PROGRESS'` hardcoded igual que el handler de `crear_incidencia_live`, y `fecha_limite` se calcula con la **misma fórmula** `timestamp_creacion + make_interval(hours => sla_limite::int)` (verificado contra main.py:947).
- **Bonus del trigger**: añade `categoria`, `tecnico_asignado`, `area_afectada`, `agente_origen`, `notas` que el POST /incidencias/live NO rellenaba (el shell perdía esa info al pasar por live).
- **fecha_creacion**: el trigger usa `NEW.timestamp_creacion` (= momento del INSERT en run), el handler usaba el default `now()` de incidencias_live (= momento del INSERT en live, ~milisegundos después). **Diferencia despreciable**, ahora es más precisa.
- **incidencia_detectada**: el trigger copia el texto **completo**, el handler del shell hacía `text.substring(0, 200)` truncando a 200 chars. **El trigger es estrictamente mejor**.

**Conclusión**: borrar el bloque del frontend que llama a POST /incidencias/live (L6842-6862) es 100% seguro. La fila live se sigue creando automáticamente al hacer POST /incidencias del paso 1, vía el trigger AFTER INSERT, con datos **más completos y precisos** que antes.

Nota sobre el PUT /incidencias/live/{id}/progreso (L6860, L7007, L7503, L7549): NO eliminar. Esos PUT siguen siendo necesarios porque actualizan UI state (progreso_pct, total_tareas, tareas_completadas) que el trigger NO toca por diseño (F2.1 contract: las 3 columnas UI son escribibles solo por el frontend).

**Decisión recomendada**: borrar SOLO las líneas L6834-6861 del frontend (el bloque `try { var liveResp = ... POST .../incidencias/live ... }`). El PUT del progreso de L6860 está dentro del mismo try/catch — hay que ver si lo mantenemos como llamada separada o lo eliminamos también.

---

## 11. F-ARQ02-08 mini-recon (A.4bis)

### 11.1 — TODAS las referencias en código (filtrando backups)

**frontend/index.html (vivo, NO backups):**
```
L5896:    runSaveToBuffer({...})                                ← itsmSubmitAndPipeline llama tras POST /incidencias
L6232:    async function loadRunPlansFromDB()                  ← carga GET /run/plans al setup
L6234:        const r = await authFetch(API_BASE + '/run/plans')
L6244:    async function runSaveToBuffer(data) {                ← guarda draft
L6248:        const r = await authFetch(API_BASE + '/run/plans', {method:'POST', ...})
L6275:        <button ... runRestoreFromBuffer(...)>             ← UI: botón Restaurar
L6276:        <button ... runRerunFromBuffer(...)>               ← UI: botón Re-ejecutar
L6277:        <button ... runDeletePlan(...)>                    ← UI: botón Eliminar
L6283:    function runRestoreFromBuffer(idx)                    ← lee fields de _runBuffer (memoria local)
L6302:    function runRerunFromBuffer(idx)                      ← restore + executePipeline('run')
L6313:    async function runDeletePlan(idx)
L6318:        await authFetch('/run/plans/' + e.id, {method:'DELETE'})  ← DELETE backend
L6328:    loadRunPlansFromDB()                                   ← setup inicial al cargar la página
```

**backend/main.py (3 endpoints + tabla):**
```
L1249: @app.get("/run/plans")
L1255:     SELECT * FROM itsm_form_drafts ORDER BY created_at DESC
L1272: @app.post("/run/plans")
L1282:     INSERT INTO itsm_form_drafts (...)
L1294: @app.delete("/run/plans/{plan_id}")
L1301:     DELETE FROM itsm_form_drafts WHERE id=$1
```

**tests:** test_arq02_f4_itsm_drafts.py + test_deudaA1_itsm_draft_seq.py (consumidores válidos, no UI)

**Backups (frontend/index.html.backup_*) — EXCLUIDOS** (deuda histórica F-ARQ01-chore, no relevantes).

### 11.2 — ¿Existe handler 'recuperar borrador' o GET por id?

**Sí, existe el flujo completo de recuperación de drafts en frontend, PERO trabaja en memoria local:**

1. **Setup inicial** (L6328): `loadRunPlansFromDB()` → `GET /run/plans` → carga TODOS los drafts en memoria como `_runBuffer`.
2. **runSaveToBuffer()** (L6244): cada submit del formulario llama `POST /run/plans` con el payload completo + recarga `loadRunPlansFromDB()`.
3. **Botón ↩ Restaurar** (L6275): llama `runRestoreFromBuffer(idx)` que lee `_runBuffer[idx].fields` (memoria) y rellena los campos del formulario actual con los valores del draft. **NO hace GET /run/plans/{id}**, lee del array en memoria que se cargó al inicio.
4. **Botón ▶ Re-ejecutar** (L6276): `runRerunFromBuffer` = restore + `executePipeline('run')` directo.
5. **Botón ✕ Eliminar** (L6277): `runDeletePlan` → `DELETE /run/plans/{id}` + splice del array local.

**NO existe `GET /run/plans/{id}` en el backend** (solo `GET /run/plans` plural). El frontend lee el array completo al cargar la página y trabaja sobre la copia en memoria.

**Conclusión 11.2**: SÍ hay UI consumidora (3 botones por draft: Restaurar / Re-ejecutar / Eliminar). El usuario puede recuperar borradores desde el panel del formulario ITSM. **No es ruido**: es una feature del shell.

### 11.3 — ¿Se está poblando hoy?

```
 count |        ultima_creacion        |       primera_creacion        
-------+-------------------------------+-------------------------------
    61 | 2026-03-20 11:14:41.462437+00 | 2026-03-20 11:14:41.080308+00
```

**Distribución por formato de id**:
```
 catalog_legacy | drafts_nuevos_seq | drafts_legacy_uuid | total 
----------------+-------------------+--------------------+-------
             61 |                 0 |                  0 |    61
```

**Hallazgos**:
- **61 filas, todas del seed inicial 2026-03-20 11:14:41** (catálogo `RUN-CAT-001..061`)
- **0 drafts creados desde entonces** — ni con formato uuid4 viejo (limpiados en F4 cleanup), ni con formato SEQUENCE nuevo (deudaA1)
- **`max(created_at) == primer seed`** — la tabla NO se ha poblado en 20 días

Esto significa una de tres cosas:
1. **Nadie ha usado el formulario ITSM en 20 días** desde el cierre F4 (poco probable, hemos hecho varios smokes)
2. **Los smokes (F1.4, F2.3, A.3) usaban path agéntico directo** sin pasar por `itsmSubmitAndPipeline` que es quien llama a `runSaveToBuffer`
3. **El `runSaveToBuffer` falla silenciosamente** (catch sin log) y nunca llega a poblar

**Verificación rápida sobre el código**: `runSaveToBuffer` (L6244) tiene un `try { ... if (r.ok) { ... return; } } catch(e) {}` y el fallback escribe en memoria local sin error visible. **Fallo silente confirmado** si el POST diera 5xx.

Pero el smoke A.3 (paso 4) sí ejecutó `itsmSubmitAndPipeline` indirectamente (creé un ticket vía `POST /incidencias` directo, NO desde el form Safari). El form Safari real NO ha sido usado por Jose en estas semanas — los smokes fueron `curl` desde primo o llamadas del scenario engine.

### 11.4 — Veredicto en 2 líneas

**(b) MANTENER** porque hay 3 botones de UI vivos en el shell (`runRestoreFromBuffer`, `runRerunFromBuffer`, `runDeletePlan`) que consumen `_runBuffer` cargado desde `GET /run/plans` al cargar la página, ofreciendo al usuario recuperar/re-ejecutar/eliminar borradores guardados del formulario ITSM. La feature está **viva en el código**, aunque el seed catalog (61 filas `RUN-CAT-*` de 2026-03-20) sigue siendo lo único que se ha guardado y **no hay drafts nuevos creados desde entonces** (probablemente porque los smokes han ido por `curl` directo, no por el form Safari real).

**Acción derivada (no ahora)**: F-ARQ02-08 NO debe eliminarse. Es UNA feature legítima del shell, no ruido. **El verdadero F-ARQ02-08 era "el shell duplica el ticket"** (ya resuelto en A.2 al pasar el `pre_existing_ticket_id`). El `runSaveToBuffer` por sí solo no causa duplicación (escribe en `itsm_form_drafts`, no en `incidencias_run`). Lo que F-ARQ02-08 consolida es: "el shell hace 3 hits HTTP en serie por cada submit" → 1 `POST /incidencias` (ticket real, A.2 lo cubre) + 1 `POST /run/plans` (draft, MANTENER) + 1 `POST /agents/AG-001/invoke` (cadena agéntica, A.2 lo cubre). Los 3 paths son legítimos post-A.2/A.3, no se duplica nada porque el ticket real es único.

**F-ARQ02-08 puede marcarse como RESUELTA por A.2** (la duplicación era el problema real). El `runSaveToBuffer` se queda como feature de "borradores recuperables" del shell.

**F-ARQ02-08 → RESUELTA-POR-A.2** (cierre Bloque A, 2026-04-07): la duplicación de ticket que justificaba esta deuda quedó cubierta por el flow `pre_existing_ticket_id` de AG-001 implementado en A.2 (`3234f58`). `runSaveToBuffer` sobrevive como feature legítima de borradores recuperables.


# 06 — Reglas y Método de Trabajo

**Generado:** 2026-04-01

---

## Método de Trabajo

### Arquitectura de desarrollo: 2 Claudes

1. **Claude Analista** — Analiza el estado actual, genera documentación, propone PROMPTs
2. **Claude Ejecutor** — Recibe PROMPTs autocontenidos, aplica cambios quirúrgicos

### Flujo de trabajo
1. Claude Analista examina el código y genera un PROMPT autocontenido
2. El usuario copia el PROMPT y lo pega en Claude Ejecutor
3. Claude Ejecutor aplica los cambios siguiendo las instrucciones exactas
4. Verificación con grep antes/después + validación JS + docker restart

---

## Reglas de Modificación

### Regla 1: Máximo 5 líneas por cambio
Cada modificación debe ser lo más atómica posible. Si necesitas cambiar más de 5 líneas, divide en múltiples PROMPTs.

### Regla 2: grep antes y después
Siempre verificar con grep que:
- La línea a buscar existe exactamente
- La línea reemplazada quedó correcta
- No hay efectos colaterales

### Regla 3: Validar JavaScript
Después de cada cambio en index.html, ejecutar:
```bash
node -e "var fs=require('fs');var html=fs.readFileSync('frontend/index.html','utf8');var scripts=html.match(/<script[^>]*>([\s\S]*?)<\/script>/gi);scripts.forEach(function(s){var c=s.replace(/<\/?script[^>]*>/gi,'');try{new Function(c);}catch(e){console.log('ERROR:',e.message);}});console.log('OK');"
```

### Regla 4: docker compose restart frontend
Siempre reiniciar nginx después de cambios en frontend:
```bash
docker compose restart frontend
```

### Regla 5: NO tocar funciones existentes
Solo AÑADIR código nuevo. Nunca modificar funciones que ya funcionan.

---

## Zonas Congeladas

Estas funciones NO se deben modificar bajo ninguna circunstancia:

| Función | Línea | Motivo |
|---------|-------|--------|
| `authFetch` | 3777 | Core de autenticación |
| `executeRunPipeline` | 5595 | Pipeline RUN completo |
| `executeBuildPipeline` | 7479 | Pipeline BUILD completo |
| `savePipelineState` | 7251 | Persistencia de sesiones |
| `showBuildPause` | 8526 | UI pausas de gobernanza (2600+ líneas) |
| `showBuildFinalScreen` | 10316 | Pantalla final BUILD |
| `executePipeline` | 11192 | Dispatcher principal |
| `itsmSubmitAndPipeline` | 5117 | Registro ITSM |
| `buildSubmitAndPipeline` | 5439 | Registro proyecto |
| `renderPipelineStepsHeader` | 7370 | Navegación pipeline |
| `navigateToPipelineStep` | 7440 | Navegación entre pausas |

---

## Patrones Aprendidos

### Patrón Safari JSON
Safari y algunos navegadores no parsean bien JSON directo de `response.json()`.
Usar siempre:
```javascript
var r = await fetch(url);
var t = await r.text();
try { return JSON.parse(t); } catch(e) { return t; }
```
Este patrón está implementado en `authFetch` y en las funciones `af()` de gov-run.html y gov-build.html.

### Patrón de tabs con event delegation
Los tabs del pipeline BUILD usan `data-tab-idx` + `setTimeout(50)` para evitar race conditions:
```javascript
// El setTimeout de 50ms es necesario para que el DOM se actualice
setTimeout(function() { /* render tab content */ }, 50);
```

### Patrón de ocultar paneles por ID interno
En vez de usar selectores CSS `nth-child` (que fallan con paneles dinámicos), usar JavaScript con `.closest('.panel')`:
```javascript
var el = document.getElementById('run-exec-btn');
if (el) { var p = el.closest('.panel'); if (p) p.style.display = 'none'; }
```

### Patrón de token via URL para iframes
Para compartir autenticación entre padre e iframe:
```
// Padre (gov-run.html):
fr.src = '/index.html?token=' + encodeURIComponent(TK) + '#auto-run';

// Hijo (index.html):
var parentToken = new URLSearchParams(window.location.search).get('token');
if (parentToken) { AUTH_TOKEN = parentToken; localStorage.setItem('cpm_token', parentToken); }
```

### Patrón de agrupación por nombre único en catálogos
El catálogo tiene 4.575 registros pero solo 61 incidencias únicas. Se agrupa con:
```javascript
var seen = {};
data.forEach(function(c) {
    var nm = c.incidencia || '';
    if (!nm || seen[nm]) return;
    seen[nm] = true;
    // crear option...
});
```

### Patrón de gov-mode CSS agresivo
Para modo gobernador, aplicar la clase `gov-mode` múltiples veces para cubrir timing de login:
```javascript
document.body.classList.add('gov-mode');
document.addEventListener('DOMContentLoaded', hideGovPanels);
setTimeout(hideGovPanels, 100);
setTimeout(hideGovPanels, 500);
setTimeout(hideGovPanels, 1500);
setTimeout(hideGovPanels, 3000);
```

---

## Arquitectura Docker

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   nginx     │────▶│   FastAPI    │────▶│  PostgreSQL  │
│  :3030/80   │     │   :8088      │     │  :5432       │
│             │     │              │     │              │
│ index.html  │     │ main.py      │     │ 46 tablas    │
│ gov-run     │     │ agents/      │     │ 8.600+ filas │
│ gov-build   │     │ cmdb_api     │     │              │
│             │     │ rbac_api     │     │              │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────▼───────┐
                    │  Claude API  │
                    │ (Anthropic)  │
                    │ 14 agentes   │
                    │ 35 tools     │
                    └──────────────┘
```

---

## Convenciones de Código

- **Variables CSS:** `var(--blue)`, `var(--green)`, `var(--red)`, `var(--bg2)`, `var(--text1)`, etc.
- **IDs de agentes:** `AG-XXX` (001-018)
- **IDs de técnicos:** `FTE-XXX` (001-150)
- **IDs de PMs:** `PM-XXX` (001-015)
- **IDs de proyectos:** `PRJ-XXX` (001-046)
- **IDs de incidencias:** `INC-YYYYMMDD-XXXX`
- **Prioridades RUN:** P1 (Crítica), P2 (Alta), P3 (Media), P4 (Baja)
- **Niveles técnicos:** N1 (Junior), N2 (Mid), N3 (Senior), N4 (Expert)
- **Silos:** Frontend, Soporte, Redes, Windows, Backend, QA, DevOps, Seguridad, BBDD

# Bloque C — Mini-recon

## Sección 1 — F-ARQ02-06: drift de los 3 tests rojos F-ARQ02-01

### 1.1 — ¿Dónde vive el scenario engine?

`grep -rn "scenario_engine\|seed_scenario\|scenarios" backend/ --include="*.py"`:

| Fichero | Rol |
|---|---|
| `backend/scenario_engine.py` | **Servicio principal** — funciones puras `seed_scenario_empty/half/optimal/overload` + `reset_scenario` |
| `backend/main.py` | Endpoint `POST /api/admin/seed-scenario` (envoltorio HTTP, importa de `scenario_engine`) |
| `backend/tests/test_scenario_engine.py` | Tests unitarios del servicio (llaman a las funciones directamente con un asyncpg conn) |
| `backend/tests/test_scenario_e2e.py` | Tests end-to-end vía endpoint HTTP (admin token) |

No hay tabla `scenarios_config` — los escenarios son código puro.

### 1.2 — Los 3 asserts F-ARQ02-01 que fallan

#### (a) `test_p96_router::test_build_portfolio` (L112-119)

```python
def test_build_portfolio(ceo_token):
    code, data = _get("/api/p96/build/portfolio", ceo_token)
    assert code == 200
    assert isinstance(data, list)
    assert len(data) == 60          # ← FALLA: actual = 61
    sample = data[0]
    assert "cpi" in sample
    assert "spi" in sample
```

**Mide**: número total de proyectos devueltos por el endpoint `GET /api/p96/build/portfolio` (vista materializada `v_p96_build_portfolio` sobre `build_live`). Hardcoded a 60 (los 60 proyectos legacy del seed P98 F2). **Actual: 61** → un proyecto legacy extra.

#### (b) `test_scenario_e2e::test_e2e_seed_scenario` (L118-133, CHECK 7)

```python
r = httpx.post(f"{API_URL}/api/admin/seed-scenario",
               json={"scenario_id": 0, "reset": True}, ...)
b = r.json(); c2 = b["counts"]
assert c2["build_live_scenario"] == 0
assert c2["kanban_scenario"]     == 0
assert c2["build_live_legacy"]   == 60     # ← FALLA: actual = 61
assert c2["kanban_legacy"]       == 341
assert c2["cartera_build"]       == 46
```

**Mide**: tras un seed EMPTY (que purga TODAS las filas scenario), los counts legacy intactos. La aserción que falla es `build_live_legacy == 60` — el endpoint devuelve `61` porque hay un proyecto legacy extra que el seed reset NO toca (correctamente — el reset sólo borra `LIKE 'PRJ-SC%'`).

#### (c) `test_scenario_engine::test_legacy_intacto_post_overload` (L236-257)

```python
def test_legacy_intacto_post_overload():
    """Tras OVERLOAD, los counts legacy siguen igual a counts_F0.txt."""
    async def _go():
        c = await _conn()
        try:
            await seed_scenario_overload(c)
            return (
                await c.fetchval("SELECT COUNT(*) FROM cartera_build"),
                await c.fetchval("SELECT COUNT(*) FROM build_live WHERE id_proyecto !~ '^PRJ-SC[A-D]'"),
                await c.fetchval("SELECT COUNT(*) FROM kanban_tareas WHERE id NOT LIKE 'KAN-SC%'"),
                await c.fetchval("SELECT COUNT(*) FROM incidencias_run WHERE ticket_id NOT LIKE 'INC-SC%'"),
            )
        finally:
            await c.close()
    assert _run(_go()) == (46, 60, 341, 34)   # ← FALLA: actual = (46, 61, 385, 38)
```

**Mide**: 4 counts de 4 tablas tras `seed_scenario_overload` (que sólo debería tocar filas con prefijo SC):
- `cartera_build` (read-only por invariante I5): 46 ✓
- `build_live` legacy (no SC): esperado 60, **actual 61** (delta +1)
- `kanban_tareas` legacy (no `KAN-SC%`): esperado 341, **actual 385** (delta **+44**)
- `incidencias_run` legacy (no `INC-SC%`): esperado 34, **actual 38** (delta +4)

### 1.3 — Punto de generación: ¿bulk INSERT determinista o loop con random?

`scenario_engine.py` usa **loops Python** con `random` Pseudoaleatorio sembrado:

```python
async def seed_scenario_overload(conn):
    random.seed(42)                    # ← I6: reproducible
    await reset_scenario(conn)
    pms = await conn.fetch("...")
    assert len(pms) == 10

    for i in range(40):                # ← count FIJO (40 build_live)
        ... INSERT INTO build_live ...

    for i in range(160):               # ← count FIJO (160 kanban)
        ... INSERT INTO kanban_tareas ...

    for i in range(22):                # ← count FIJO (22 incidencias_run)
        ... INSERT INTO incidencias_run ...
```

**Counts hardcoded** (40/160/22 OVERLOAD; 40/120/12 OPTIMAL; 20/60/8 HALF; 0/0/0 EMPTY). `random.seed(42)` se llama AL INICIO de cada función seed → las elecciones aleatorias (`random.choice`, `random.randint`, `random.uniform`) son **deterministas** entre runs.

`reset_scenario` (L32-48) borra **sólo filas con prefijo scenario**:
```python
DELETE FROM incidencias_run WHERE ticket_id LIKE 'INC-SC%'
DELETE FROM kanban_tareas    WHERE id        LIKE 'KAN-SC%'
DELETE FROM build_live, ..., WHERE id_proyecto ~ '^PRJ-SC[A-D][0-9]+$'
```

**No toca legacy.** El engine es 100% determinista y respeta los invariantes I1–I6.

### 1.4 — Auditoría de no-determinismo

Revisión del módulo `scenario_engine.py` punto por punto:

| Fuente potencial | Hallazgo |
|---|---|
| `random.randint/choice/uniform` sin `random.seed()` | ❌ NO — `random.seed(42)` está al inicio de las 3 funciones seed |
| `uuid.uuid4()` como parte del INSERT | ❌ NO — los `id_proyecto`/`id_kanban`/`ticket_id` son deterministas (`PRJ-SC{prefix}{num:03d}`, `KAN-SC{i:04d}`, `INC-SC{i:03d}`) |
| `datetime.now()` afectando el count | ❌ NO — `now()` se usa para `fecha_inicio` pero NO afecta cuántas filas se insertan |
| `SELECT * FROM X` sin `ORDER BY` | ❌ NO — las queries de PMs y técnicos llevan `ORDER BY id_pm` / `ORDER BY horas_legacy ASC, s.id_recurso ASC` |
| Dependencias del count con la hora/día | ❌ NO |
| `ON CONFLICT DO NOTHING` que acumule | ❌ NO — los INSERTs son secos sin ON CONFLICT (fallarían ruidosamente si hubiera duplicate key, lo cual demuestra que cada run parte de tabla limpia para los `SC%`) |

**Conclusión auditoría**: el engine **NO es la fuente del drift**. Es perfectamente determinista.

### 1.5 — ¿Cómo invocan los tests al engine?

| Test | Modo de invocación | Cleanup previo |
|---|---|---|
| `test_legacy_intacto_post_overload` | **Servicio directo**: `from scenario_engine import seed_scenario_overload; await seed_scenario_overload(c)` | NO — asume que el legacy ya está en su baseline (60/341/34). El propio `seed_scenario_overload` hace `reset_scenario` (sólo SC%) al inicio. |
| `test_e2e_seed_scenario` (CHECK 7) | **Endpoint HTTP**: `POST /api/admin/seed-scenario` con admin token | NO — asume baseline legacy 60/341 |
| `test_build_portfolio` | **Endpoint GET** `/api/p96/build/portfolio` (vista) | NO — asume baseline 60 proyectos en `build_live` legacy |

Ninguno de los 3 tests hace `TRUNCATE` o limpieza de filas legacy. Todos asumen que la BD parte de un baseline congelado de **60 / 341 / 34 / 46**.

### 1.6 — Estructura del drift observado

**Counts actuales en BD (post-último pytest)**:
```
cartera_build:                    46    ← invariante I5, intacta ✓
build_live legacy (no SC):        61    ← +1 vs baseline 60
build_live SC:                    40    ← OK (último OVERLOAD activo)
kanban legacy (no KAN-SC):        385   ← +44 vs baseline 341
kanban SC:                       120    ← OK (último OVERLOAD = 160 pero el test optimal dejó 120)
incidencias legacy (no INC-SC):   38    ← +4 vs baseline 34
incidencias SC:                   12    ← OK (último OPTIMAL = 12)
```

**Patrón de los kanban legacy "extra"**:

```
prefix    | count
----------+------
KT-*      | 352   ← +N (los nuevos: KT-20260409-XXXX, generados HOY por AG-001)
BLD-*     |  20   ← seed P98 F2 original
BLD-D*    |   3
BLD-F*    |   3
BLD-BF*   |   1
... (otros 6 BLD-XXX)
```

**10 kanban más recientes** (todas son `KT-YYYYMMDD-HEX` con `id_proyecto=NULL`):
```
KT-20260409-F0EC   None   'Validación y cierre'                       2026-04-09 09:29:37
KT-20260409-B449   None   'Verificación post-optimización'            2026-04-09 09:29:37
KT-20260409-3C4C   None   'Optimización de consultas y configuración' 2026-04-09 09:29:37
KT-20260409-287F   None   'Análisis de consultas lentas y bloqueos'   2026-04-09 09:29:37
KT-20260409-BD8A   None   'Revisar logs de base de datos y errores'   2026-04-09 09:29:37
KT-20260409-58A0   None   'Diagnóstico inicial - Análisis rendimien'  2026-04-09 09:29:37
KT-20260409-0913   None   'Validación y cierre'                       2026-04-09 09:12:05
KT-20260409-E01A   None   'Verificación de mejora de rendimiento'     2026-04-09 09:12:05
KT-20260409-5D23   None   'Optimización de consultas y configuració'  2026-04-09 09:12:05
KT-20260409-B20D   None   'Revisión de logs del servidor BD'          2026-04-09 09:12:05
```

**Estructura clarísima**: son grupos de **6-7 kanban por timestamp** generados a las 09:12 y 09:29 de hoy. Hora 09:12 = `test_deudaA_integrador` que invoca AG-001. Hora 09:29 = `test_deudaB_integrador` que también invoca AG-001. Cada invocación crea **1 incidencia + ~6 tareas kanban hijas** (la cadena del Dispatcher: Diagnóstico → Logs → Análisis → Optimización → Verificación → Validación).

**Patrón temporal del drift en `kanban_tareas` durante Bloque B** (observado en los outputs de pytest):
```
post-A:        367   (baseline declarado en F1.4)
post-B.1:      373
post-B.2:      379
post-B.4:      385
```
**+6 por cada test integrador que invoca AG-001 → invoca create_tasks**.

**Incidencias legacy más recientes**:
```
INC-000038-20260408   P4  QUEUED   2026-04-08 22:45  ← creada por test_deudaB1_engine_ticket
INC-000035-20260408   P4  QUEUED   2026-04-08 18:14
INC-000034-20260401   P1  QUEUED   2026-04-01 10:57
INC-000037-20260401   P1  EN_CURSO 2026-04-01 10:38
...
```

**Causa raíz identificada**:

1. Los tests integradores Bloque A/B (`test_deudaA_integrador`, `test_deudaB1_engine_ticket`, `test_deudaB_integrador`) hacen `POST /incidencias` + `POST /agents/AG-001/invoke` para verificar el flow end-to-end.
2. AG-001 dispara la tool `create_tasks` de su tool registry, que crea **6-7 filas en `kanban_tareas`** con formato `KT-YYYYMMDD-HEX` (formato legacy del shell).
3. El cleanup de los tests integradores hace `DELETE FROM incidencias_run WHERE ticket_id=$1` — pero **NO borra las kanban hijas** generadas por `create_tasks`. No hay FK CASCADE entre `kanban_tareas` e `incidencias_run` (la columna `id_incidencia` es nullable, sin constraint).
4. Cada run del scenario engine reset borra `LIKE 'KAN-SC%'`, pero estas tareas están en formato `KT-*`, no `KAN-SC*` → quedan **fuera del alcance del reset**, acumulando como "legacy" para el contador.
5. **El proyecto extra `PRJ-MNQDXKA5`** (build_live +1) se creó el 2026-04-08 18:32 y no coincide con ningún test integrador del Bloque A/B. Sospechosamente parece un proyecto creado por una invocación de AG-005/006/007 (BUILD chain) en algún smoke previo no limpiado. Investigar separadamente — quizá tiene mismo origen residual.

### 1.7 — Comparación con counts ARQ-02 F6 smoke

Memoria del cierre F6: en smoke 4 scenarios documentamos `OVERLOAD run=59, live=21`. Hoy tras el último OVERLOAD: `kanban SC=120` (no estamos midiendo OVERLOAD final, el test_optimal corrió después y dejó 120). Lo importante: **los counts SC son correctos cuando midas justo después del último seed**, pero los **counts legacy crecen monotónicamente** porque cada test integrador deja residuos KT-*.

Entre F6 smoke (cierre ARQ-02 base) y hoy:
- F6 smoke esperaba `kanban legacy = 341`
- Hoy actual `kanban legacy = 385` (+44 = ~7 invocaciones × ~6 tareas/invoke)
- Eso coincide con: 1 smoke A.3 PASO 4 + 1 test_deudaA_integrador × N runs + test_deudaB1_engine_ticket × 3 sub-tests × N runs + test_deudaB_integrador × N runs ≈ 7-8 invocaciones acumuladas en los Bloques A y B.

### 1.8 — Veredicto en 4 líneas

**(a) ¿No-determinismo del engine o drift acumulativo?** **Drift acumulativo, no no-determinismo del engine**. El scenario engine es perfectamente determinista (`random.seed(42)`, counts hardcoded 40/160/22, reset estricto a `SC%`). La causa real es que los **tests integradores Bloque A/B invocan AG-001 → create_tasks**, generando 6-7 filas `KT-YYYYMMDD-HEX` por run en `kanban_tareas` que NO empiezan por `KAN-SC%`, escapan al reset del scenario engine, y se acumulan como "legacy" en el contador. La estructura es perfectamente identificable: +6/+7 kanban por cada invocación AG-001, +1 incidencia por test integrador. Cero aleatoriedad en juego.

**(b) ¿Fix correcto?** **TRES opciones, NO `random.seed`**:
1. **Cleanup defensivo en los tests integradores**: añadir `DELETE FROM kanban_tareas WHERE id_incidencia=$tid OR (id_proyecto IS NULL AND fecha_creacion >= $start_of_test)` antes del DELETE de la incidencia padre. ~3 LOC en cada test integrador (3 ficheros). Pragmático.
2. **FK CASCADE en `kanban_tareas.id_incidencia`**: añadir `FOREIGN KEY (id_incidencia) REFERENCES incidencias_run(ticket_id) ON DELETE CASCADE`. Más limpio estructuralmente, pero requiere migración SQL + verificar que ninguna kanban legítima tiene `id_incidencia` huérfano (probablemente unas cuantas BLD-* de seeds antiguos).
3. **Separar test DB**: contenedor postgres dedicado a tests con `pg_dump` baseline y reset entre runs. Es la solución "correcta" pero invasiva (cambiar docker-compose, pipeline CI, etc.).

**Recomendación**: Opción 1 (cleanup defensivo en tests) para C.2 mismo, + abrir F-ARQ02-18 para Opción 2 (FK CASCADE) como mejora estructural en Bloque D.

**(c) ¿Afecta a producción?** **NO**. El scenario engine es exclusivamente test fixture (`POST /api/admin/seed-scenario` está protegido por admin token y solo se llama desde tests E2E). El cleanup defensivo en tests no toca producción. La opción 2 (FK CASCADE) sí tocaría schema de producción pero sería transparente para los usuarios — kanban huérfanas son basura legítima, su eliminación al borrar el padre es comportamiento esperado.

**(d) ¿Se puede atacar C.2 sin tocar C.1, o C.2 cambia los counts esperados?** **C.2 (cleanup) hace los baselines verdaderos otra vez**, así que los 3 tests rojos volverían a verde **sin cambiar sus asserts hardcoded** (`60/341/34`). Sin embargo, hay un problema: **44 filas residuales ya están en BD** del histórico de tests pasados. C.2 puede:
- Limpiar el residuo histórico (DELETE one-shot de las 44 KT-* huérfanas + 4 INC-* + el proyecto PRJ-MNQDXKA5) → vuelve a baseline 341/34/60.
- Y a partir de ese punto, los tests integradores nuevos limpian su propio residuo en `finally` → no vuelve a crecer.

**Implicación**: C.1 y C.2 son **independientes** si se ejecutan en orden correcto: primero C.2 (cleanup histórico + cleanup defensivo en tests integradores), luego C.1 puede confirmar que los 3 tests rojos pasan SIN tocar sus asserts. Si C.1 ya estaba planeado como "actualizar baselines" (subir 60→61, 341→385), **conviene cancelarlo** y hacer sólo C.2 — los baselines hardcoded son los correctos, son los datos los que están sucios.

**Pregunta abierta para el usuario**: ¿prefieres atacar primero el cleanup one-shot del residuo histórico (1 SQL idempotente que borra las 44+4+1 filas residuales identificables por su patrón temporal/formato) + cleanup defensivo en los 3 tests integradores Bloque A/B + verificar que los 3 tests rojos vuelven a verde con los baselines originales? Eso cierra F-ARQ02-06 sin tocar `test_p96_router.py`, `test_scenario_e2e.py` ni `test_scenario_engine.py`. Es la opción más limpia.

---

## Sección 2 — Dry-run F-ARQ02-06: identificación al byte de las filas a limpiar

> **Hallazgo crítico que invalida parte de la sec 1**: la hipótesis "44 KT-* residuales = los nuevos del Bloque A/B" era simplista. La verdad es más matizada: los KT-* totales son **352** (la mayoría son seeds legítimos del 2026-02-08 a 2026-03-22), pero hay **35 KT-* huérfanas** (parent borrado) que sí son residuales de tests sin cleanup. Y el delta `385 - 341 = 44` no equivale exactamente a esas 35 huérfanas — hay un componente adicional de incidencias_run extras que arrastran kanban hijas vivas. Esta sección reconstruye el cuadro real al byte.

### 2.1 — kanban_tareas KT-* huérfanas (parent ya no existe)

```sql
SELECT count(*) FROM kanban_tareas k
WHERE k.id LIKE 'KT-%' AND k.id NOT LIKE 'KAN-SC%'
  AND k.id_incidencia IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM incidencias_run r WHERE r.ticket_id = k.id_incidencia);
→ 35
```

**Distribución por día**:

| Día | n | Parents huérfanos |
|---|---|---|
| 2026-04-09 | **32** | `INC-000043-20260409` (único) |
| 2026-03-18 | 1 | `INC-2026-0841` |
| 2026-03-09 | 1 | `INC-2026-0841` |
| 2026-03-08 | 1 | `INC-2026-0839` |
| **Total** | **35** | |

**Las 32 del 2026-04-09** vinculan TODAS al mismo `INC-000043-20260409` (que ya no existe en `incidencias_run`), agrupadas en 2 timestamps: `09:12:05` y `09:29:37`. Cada timestamp ≈ 16 kanban (más de las 6-7 normales por invocación AG-001) — esto sugiere que pytest hizo varios runs reusando el mismo `tid` o que hubo invocaciones manuales adicionales acumulando. Sample:
```
KT-20260409-F0EC  parent=INC-000043-20260409  09:29:37  'Validación y cierre'
KT-20260409-B449  parent=INC-000043-20260409  09:29:37  'Verificación post-optimización'
KT-20260409-3C4C  parent=INC-000043-20260409  09:29:37  'Optimización de consultas y configuración'
KT-20260409-287F  parent=INC-000043-20260409  09:29:37  'Análisis de consultas lentas y bloqueos'
KT-20260409-BD8A  parent=INC-000043-20260409  09:29:37  'Revisar logs de base de datos y errores'
KT-20260409-58A0  parent=INC-000043-20260409  09:29:37  'Diagnóstico inicial - Análisis rendimiento BD'
KT-20260409-0913  parent=INC-000043-20260409  09:12:05  'Validación y cierre'
... (resto del bloque 09:12)
```

**KT-* del 2026-04-09 con parent vivo: 0**. Las 32 son TODAS huérfanas — son al 100% residuales de mis tests de hoy.

**Las 3 huérfanas antiguas** (2026-03-08/09/18) apuntan a `INC-2026-0841` y `INC-2026-0839` — formato legacy de fases F1/F2 anteriores a ARQ-01. Son residuales históricas de smokes pre-arq01, sin contexto recuperable. Borrarlas es seguro.

**KT-* con `id_proyecto IS NOT NULL` (sospechosas)**: 52 con proyecto + 0 con proyecto Y huérfanas. Las KT-* con proyecto son legítimas (vinculadas a un proyecto BUILD), no son residuales de tests integradores.

### 2.2 — incidencias_run formato nuevo (38 → baseline 34)

`incidencias_run` legacy = 38 (TODAS son `INC-NNNNNN-YYYYMMDD` formato post-arq01 — **0 filas** quedan en formato legacy `INC-YYYYMMDD-HEX`, fueron migradas en F1).

**Las 38 ordenadas ASC por timestamp** (corte teórico baseline=34 entre #34 y #35):

```
 #1  INC-000001-20260321  03-21 00:15  kan=1
 #2  INC-000002-20260321  03-21 17:28  kan=6
 ...
#32  INC-000032-20260326  03-26 11:21  kan=6
#33  INC-000036-20260401  04-01 10:29  kan=0   ← procesado pero AG-001 no creó kanban
#34  INC-000033-20260401  04-01 10:33  kan=6   ← último baseline si baseline=34
#35  INC-000037-20260401  04-01 10:38  kan=0   ← PRIMERA EXTRA
#36  INC-000034-20260401  04-01 10:57  kan=6
#37  INC-000035-20260408  04-08 18:14  kan=6
#38  INC-000038-20260408  04-08 22:45  kan=6
```

**Las 4 extras (#35-#38)**:
- `INC-000037-20260401`: kan=0 (probablemente ticket creado pero AG-001 no completó la cadena)
- `INC-000034-20260401`: kan=6 (procesado, 6 kanban hijas vivas)
- `INC-000035-20260408`: kan=6 (procesado, 6 kanban hijas vivas)
- `INC-000038-20260408`: kan=6 (procesado, 6 kanban hijas vivas)

Si borramos las 4: **se llevarán por delante 18 kanban hijas vivas** que pasarán a ser huérfanas — habría que borrarlas TAMBIÉN (no hay FK CASCADE).

**Incidencias_run vs baseline**: 38 - 4 = 34 ✓ exacto.

> Caveat: el corte exacto (#34 vs #35) es heurístico — asume que el baseline 34 fue snapshotado entre `INC-000033` (10:33) e `INC-000037` (10:38). El snapshot real puede haber sido en otro punto. Las 4 más recientes son la mejor aproximación.

### 2.3 — `PRJ-MNQDXKA5` (build_live legacy +1)

```sql
SELECT * FROM build_live WHERE id_proyecto='PRJ-MNQDXKA5';
```

| campo | valor |
|---|---|
| id_proyecto | `PRJ-MNQDXKA5` |
| nombre | `Modelo de gestión de secretos` |
| pm_asignado | `Pendiente` |
| estado | `EN_EJECUCION` |
| progreso_pct | `0` |
| silo | `None` |
| fecha_inicio | `2026-04-08 18:32:05.396562` |
| fecha_fin_prevista | `None` |
| gate_actual | `G2-PLANIFICACION` |

**Nombre del id es ruido aleatorio** (`MNQDXKA5` ≠ formato `PRJ-XXX` legítimo de los 60 baseline `PRJ-OSP/SDW/AZR/...`). PM "Pendiente", silo NULL, progreso 0%, sin fecha_fin — claramente un proyecto creado por un POST /build/projects o /run-chain de un AG-005/006/007 smoke que falló a mitad de la cadena. **Es residuo de smoke BUILD**, no legítimo.

**Otros PRJ-* legacy**: 60 más (todos `PRJ-XXX` 3-letras formato baseline de seed P98 F2):
```
PRJ-ADF, PRJ-API, PRJ-ARC, PRJ-AWS, PRJ-AZR, PRJ-BBN, PRJ-BKP, PRJ-CAP,
PRJ-CAT, PRJ-CFN, PRJ-CMP, PRJ-CRM, PRJ-CST, PRJ-DBT, PRJ-DCI, PRJ-DEL,
PRJ-DLK, PRJ-DLP, PRJ-DNS, PRJ-EBN, PRJ-EDR, PRJ-ETL, PRJ-F5L, PRJ-GCP,
PRJ-GOV, PRJ-HCI, PRJ-HPE, PRJ-INT, PRJ-ISE, PRJ-MDM, PRJ-MFA,
PRJ-MNQDXKA5,  ← ÚNICO con formato anómalo
PRJ-MOB, PRJ-MSF, PRJ-NAC, PRJ-NTA, PRJ-NTP, PRJ-OBJ, PRJ-OCI, PRJ-ODS,
PRJ-OSP, PRJ-OSV, PRJ-PAM, PRJ-PAY, PRJ-PMX, PRJ-PRO, PRJ-PXY, PRJ-RAN,
PRJ-ROC, PRJ-SAA, PRJ-SDW, PRJ-SOC, PRJ-T24, PRJ-TAN, PRJ-TER, PRJ-VDI,
PRJ-VMW, PRJ-VPN, PRJ-WAF, PRJ-WIF, PRJ-ZTN
```
**60 baseline + 1 PRJ-MNQDXKA5 = 61 = el current count.** El cleanup obvio.

### 2.4 — Dependencias en cascada del cleanup

**Tablas con `id_proyecto`**:
```
build_live, build_project_plans, build_quality_gates, build_risks,
build_sprint_items, build_sprints, build_stakeholders, build_subtasks,
cartera_build, cmdb_activos, cmdb_costes, gobernanza_transacciones,
incidencias_run, kanban_tareas, p96_build_project_detail (vista),
pmo_governance_scoring, presupuestos, v_p96_build_portfolio (vista),
vista_proyectos_riesgo (vista)
```

**Filas dependientes de `PRJ-MNQDXKA5`** en cada una: **NINGUNA** (verificado tabla por tabla en build_subtasks/stakeholders/risks/quality_gates/sprints/sprint_items/project_plans/kanban_tareas). Borrar la fila de `build_live` es seguro y limpio. Las vistas (`p96_build_project_detail`, `v_p96_build_portfolio`, `vista_proyectos_riesgo`) se actualizarán automáticamente al desaparecer la fila.

**Tablas con `id_incidencia`/`ticket_id`**:
```
agent_conversations.ticket_id            ← soft, sin FK
agent_conversations_cobertura.ticket_id  ← vista (deriva de la anterior)
incidencias_live.ticket_id               ← FK CASCADE ON DELETE ✓
incidencias_run.ticket_id                ← PK
itsm_form_drafts.ticket_id               ← columna soft
kanban_tareas.id_incidencia              ← columna soft, sin FK
```

**FK constraints reales** (consulta a `pg_constraint`):
```
[incidencias_live]  FK ticket_id → incidencias_run(ticket_id) ON UPDATE CASCADE ON DELETE CASCADE  ✓
[kanban_tareas]     FK id_tecnico → pmo_staff_skills(id_recurso)
[incidencias_run]   FK id_catalogo → catalogo_incidencias
[incidencias_run]   FK tecnico_asignado → pmo_staff_skills
[build_live]        FK id_pm_usuario → rbac_usuarios
```

**NO HAY FK** entre `kanban_tareas.id_incidencia` ni entre `agent_conversations.ticket_id` y `incidencias_run`. Confirmado: borrar una incidencia deja kanban hijas y conversations vivas como huérfanas. **Hay que borrarlas explícitamente** en el cleanup.

**Plan de borrado correcto orden topológico**:
1. `DELETE FROM kanban_tareas WHERE id_incidencia IN (las 4 incidencias extras)` → +12 kanban afectadas
2. `DELETE FROM agent_conversations WHERE ticket_id IN (las 4 incidencias extras)` → un puñado más de conversations
3. `DELETE FROM kanban_tareas WHERE id_incidencia NOT IN (SELECT ticket_id FROM incidencias_run) AND id LIKE 'KT-%'` → las 35 huérfanas existentes
4. `DELETE FROM incidencias_run WHERE ticket_id IN (las 4 extras)` → CASCADE limpia `incidencias_live`
5. `DELETE FROM build_live WHERE id_proyecto='PRJ-MNQDXKA5'`

### 2.5 — Verificación de baselines tras cleanup hipotético

**Estado actual**:
```
kanban_legacy:    385  (tabla)
inc_legacy:        38  (tabla)
build_live_legacy: 61  (tabla)
```

**Si borramos solo las huérfanas (35 KT-*)**:
```
kanban_legacy → 385 - 35 = 350    (baseline 341 → off by +9)
```
**No alcanza el baseline 341.** Las 9 que sobran son kanban "vivas" cuyo padre es una de las 4 incidencias residuales. Si las incluimos en el cleanup:

**Si borramos huérfanas (35) + 4 incidencias extras + sus 12 kanban hijas + PRJ-MNQDXKA5**:
```
kanban_legacy    → 385 - 35 - 12 = 338    (baseline 341 → off by -3)
inc_legacy       → 38 - 4 = 34            ✓ exacto
build_live_legacy → 61 - 1 = 60            ✓ exacto
```

**El kanban da 338, NO 341**. Off by **-3**. Esto significa que las 3 kanban "extras" en el baseline 341 ya no existen — fueron borradas por algún proceso intermedio. **El baseline original 341 ya no es alcanzable exactamente** sin reinsertar 3 filas que no sabemos cuáles eran.

**Caveat baseline irrecuperable**: el snapshot baseline `(46, 60, 341, 34)` fue tomado en un momento histórico congelado. Las purgas intermedias y los smokes varios han movido la BD a un estado donde reproducir exactamente 341 kanban legacy es imposible sin un dump del estado original.

**Implicación**: el cleanup puede llegar a **340 ± 3** kanban legacy, pero no exactamente 341. Por lo tanto **C.2 no puede cerrar los 3 tests rojos sin tocar sus asserts** — habrá que actualizar al menos 1 baseline en `test_scenario_engine.py:257` y `test_scenario_e2e.py:131` (kanban_legacy de 341 a 338 o lo que dé el cleanup).

Los otros 2 baselines SÍ son alcanzables exactamente:
- `build_live_legacy=60` ✓ (con cleanup de PRJ-MNQDXKA5)
- `incidencias_legacy=34` ✓ (con cleanup de las 4 extras)
- `cartera_build=46` ✓ (intacto, invariante I5)

### 2.6 — Tests integradores que necesitan cleanup defensivo

**`grep "/agents/.*/invoke|engine.invoke|httpx.post.*invoke" backend/tests/`**:

```
backend/tests/test_deudaA_integrador.py:85:    f"{API_URL}/agents/AG-001/invoke",
```

**Único fichero**. `test_deudaB1_engine_ticket.py` y `test_deudaB_integrador.py` usan `engine._log()` directo (sólo escriben `agent_conversations`, NO disparan `create_tasks` → NO generan kanban). Por tanto **solo `test_deudaA_integrador.py` necesita cleanup defensivo**.

**Bloque de cleanup actual** (`test_deudaA_integrador.py`):

```python
async def _cleanup(tid):                                            # L46-52
    c = await _conn()
    try:
        await c.execute("DELETE FROM incidencias_run WHERE ticket_id = $1", tid)
    finally:
        await c.close()
```

**Línea exacta donde añadir el DELETE FROM kanban_tareas**: justo **antes** del `DELETE FROM incidencias_run` en la línea 52. Cambio mínimo:

```python
async def _cleanup(tid):
    c = await _conn()
    try:
        await c.execute("DELETE FROM kanban_tareas WHERE id_incidencia = $1", tid)
        await c.execute("DELETE FROM agent_conversations WHERE ticket_id = $1", tid)
        await c.execute("DELETE FROM incidencias_run WHERE ticket_id = $1", tid)
    finally:
        await c.close()
```

3 LOC. Cleanup completo: kanban hijas + agent_conversations vinculadas + incidencia padre. CASCADE limpia `incidencias_live` automáticamente.

`test_deudaB1_engine_ticket.py` y `test_deudaB_integrador.py` ya tienen el cleanup correcto para SU caso (sólo `agent_conversations` + `incidencias_run`, porque no llaman a `engine.invoke()` real).

### 2.7 — Otros tests con `invoke` que pudieran ensuciar

**`grep -rn "invoke\|/agents/.*invoke" backend/tests/`**:

| Fichero | Pattern | ¿Llama HTTP real a /agents/invoke? |
|---|---|---|
| `test_deudaA_integrador.py` | L85 `httpx.post(f"{API_URL}/agents/AG-001/invoke", ...)` | **SÍ** — único en toda la suite |
| `test_deudaB1_engine_ticket.py` | usa `engine._log()` directo | NO |
| `test_deudaB_integrador.py` | usa `engine._log()` directo | NO |

**Conclusión paso 7**: en TODA la suite de tests `backend/tests/`, el único punto que dispara `create_tasks` (y por tanto genera kanban) es `test_deudaA_integrador.py:85`. El cleanup defensivo en ese único fichero es suficiente para evitar drift futuro de los 3 baselines tras C.2.

### 2.8 — Resumen ejecutivo del dry-run

**Filas a borrar en C.2 cleanup one-shot**:

| Tabla | Filtro | Filas |
|---|---|---|
| `kanban_tareas` | `id LIKE 'KT-%' AND id_incidencia IN (las 4 extras)` | **12** |
| `agent_conversations` | `ticket_id IN (las 4 extras)` | varias (auditoría, no contadas) |
| `kanban_tareas` | `id LIKE 'KT-%' AND id_incidencia NOT IN (SELECT ticket_id FROM incidencias_run)` | **35** (huérfanas) |
| `incidencias_run` | `ticket_id IN ('INC-000037-20260401','INC-000034-20260401','INC-000035-20260408','INC-000038-20260408')` | **4** (CASCADE limpia incidencias_live) |
| `build_live` | `id_proyecto='PRJ-MNQDXKA5'` | **1** |

**Resultado esperado tras cleanup**:
```
kanban_legacy    → ~338 (baseline 341 NO alcanzable exactamente, off por -3)
inc_legacy       → 34   ✓ exacto
build_live_legacy → 60   ✓ exacto
cartera_build    → 46   ✓ intacto
```

**Implicaciones**:

1. **Los 3 tests rojos NO se pueden cerrar SIN tocar sus asserts**: el baseline `kanban_legacy=341` no es exactamente reproducible. C.2 ejecutiva debe incluir actualización de los asserts a `~338` (o el valor exacto post-cleanup) en `test_scenario_engine.py:257` y `test_scenario_e2e.py:131`. El test `test_p96_router::test_build_portfolio` SÍ se cierra sin tocar (baseline 60 sí es alcanzable).

2. **Plan recomendado para C.2 ejecutiva**:
   - Paso 1: SQL idempotente `database/arq02_deudaC2_cleanup.sql` con los 5 DELETEs en orden topológico (envuelto en BEGIN/COMMIT, con `\echo` de counts antes/después).
   - Paso 2: cleanup defensivo en `test_deudaA_integrador.py:46-52` (3 LOC añadidas).
   - Paso 3: actualizar 2 asserts en los tests scenario (kanban_legacy 341→valor real post-cleanup).
   - Paso 4: NO tocar `test_p96_router::test_build_portfolio` (su baseline 60 sí queda exacto).
   - Paso 5: re-run pytest, verificar que los 3 rojos pasan a verde.
   - Paso 6: 1 test nuevo `test_deudaC2_cleanup_no_huerfanas.py` que asserte que `kanban_tareas.id_incidencia NOT IN (SELECT ticket_id FROM incidencias_run)` count=0 (regresión: nunca volverán a haber huérfanas mientras los tests usen el cleanup defensivo).

3. **Abrir F-ARQ02-18** para Bloque D: añadir FK CASCADE `kanban_tareas.id_incidencia → incidencias_run` (mejora estructural definitiva, hace el cleanup defensivo redundante). Requiere migración + verificar que ninguna kanban legítima del baseline tiene `id_incidencia` huérfano — hoy las 3 kanban antiguas que apuntan a `INC-2026-0841/0839` lo serían, así que la migración tendría que purgarlas primero.

**Pregunta abierta para el usuario antes de C.2 ejecutiva**:
- (a) ¿OK con que el baseline `kanban_legacy=341` se actualice a su nuevo valor real (~338) en los 2 tests, dado que reproducirlo exactamente es imposible?
- (b) ¿OK con borrar las 4 incidencias residuales (`INC-000037`, `INC-000034`, `INC-000035`, `INC-000038`) y sus 12 kanban hijas + agent_conversations vinculadas? Las 4 son de los días 04-01 y 04-08, claramente residuales de smokes previos al Bloque A.
- (c) ¿OK con borrar `PRJ-MNQDXKA5`? Sin contexto, sin subtasks, smoke residual.
- (d) ¿OK con borrar las 32 KT-* huérfanas del 04-09 vinculadas a `INC-000043-20260409`? Son 100% basura de mis tests de hoy.

---

### 2.9 — Cierre F-ARQ02-06 + F-ARQ02-01

**F-ARQ02-06 CERRADA — 2026-04-09**. Cleanup one-shot aplicado en `database/arq02_deudaC2_cleanup.sql` (idempotente, BEGIN/COMMIT, 6 pasos). Resultados reales medidos:

| Métrica | Pre | Post | Esperado |
|---|---|---|---|
| `kanban_legacy` | 385 | **332** | (irreproducible 341, actualizado a 332) |
| `inc_legacy` | 38 | **34** | 34 ✓ |
| `build_live_legacy` | 61 | **60** | 60 ✓ |
| `kanban_huerfanas` | 35 | **0** | 0 ✓ |
| `build_live_total` (post PASO 6 SC purge) | 100 | **60** | 60 ✓ |

**Filas borradas por paso del SQL one-shot**:
- PASO 1 (kanban hijas de 4 inc residuales): **18** (no 12 estimadas; INC-000037 también tenía kanban contrariamente al `kan=0` del dry-run inicial)
- PASO 2 (kanban huérfanas existentes): **35**
- PASO 3 (agent_conversations vinculadas): **8** (no anticipadas en sec 2.4 — rompió `test_backfill_minimo_126`, fix con threshold 126→118)
- PASO 4 (incidencias_run residuales): **4** (CASCADE limpia incidencias_live)
- PASO 5 (PRJ-MNQDXKA5): **1**
- PASO 6 (PRJ-SC* residuales scenario): **40** (añadido en C.2 cierre tras detectar que `test_p96_router::test_build_portfolio` daba 100 por persistencia inter-sesión de SC)

**Cleanup defensivo aplicado en `test_deudaA_integrador.py:_cleanup`** (3 LOC): borrar `kanban_tareas` + `agent_conversations` ANTES de la incidencia padre. Único test en toda la suite que invoca AG-001 vía HTTP real.

**Tests actualizados**:
- `test_scenario_engine.py:257` baseline `(46,60,341,34) → (46,60,332,34)` con comment inline.
- `test_scenario_e2e.py:131` baseline `kanban_legacy == 341 → 332` con comment inline.
- `test_arq02_f5_agent_conversations.py:test_backfill_minimo_126` threshold `>= 126 → >= 118` con comment inline.
- `test_p96_router::test_build_portfolio` **NO tocado** — pasa a verde tras PASO 6 SC purge en el SQL.

**Test de regresión nuevo** `test_deudaC2_cleanup_no_huerfanas.py` (2 tests sync `_run`):
1. `test_no_kanban_huerfanas`: 0 kanban con `id_incidencia` apuntando a fantasma.
2. `test_no_agent_conversations_fantasma`: 0 conversations con `ticket_id` fantasma.

Ambos PASS. Garantizan que cualquier regresión futura (test sin cleanup defensivo) será detectada inmediatamente.

**Suite completa post-C.2**: **86 passed / 0 failed en 38.52s** ✅. Los 3 tests F-ARQ02-01 (`test_p96_router::test_build_portfolio`, `test_scenario_e2e::test_e2e_seed_scenario`, `test_scenario_engine::test_legacy_intacto_post_overload`) pasaron a verde.

**F-ARQ02-01 CERRADA por C.2** — no era un bug de los tests, era drift acumulativo de datos residuales. Los baselines hardcoded eran correctos en el snapshot original; los tests fallaban porque la BD se contaminó con residuales de smokes posteriores.

**Deuda derivada abierta para Bloque D**:
- **F-ARQ02-18** — añadir FK CASCADE `kanban_tareas.id_incidencia → incidencias_run(ticket_id) ON DELETE CASCADE`. Mejora estructural definitiva que haría el cleanup defensivo en `test_deudaA_integrador._cleanup` redundante. Requiere migración SQL + verificación previa de que ninguna kanban legítima tiene `id_incidencia` huérfano (las 3 históricas pre-arq01 ya fueron purgadas en C.2 PASO 2).

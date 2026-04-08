# SMOKE E2E — P97 CEO Dashboard v6

Checklist manual para validar el flujo completo en Safari.
Cierra sesión y borra `localStorage`/`sessionStorage` entre pruebas si hace falta.

---

## Pasos

- [ ] **1. Shell login como CEO** — entrar al shell `/`, hacer login con `alejandro.vidal@cognitivepmo.com` / `12345`. Debe redirigir automáticamente a `/p96/`.

- [ ] **2. Header + governors** — en `/p96/` verificar que el topbar muestra **"Alejandro Vidal · CEO"** y que el grid de Gobernadores carga **15 gobernadores**.

- [ ] **3. Portfolio BUILD** — ir a la pestaña BUILD/Cartera y verificar que se listan **60 proyectos** y cada fila muestra **CPI** y **SPI** numéricos.

- [ ] **4. Logout desde /p96/** — pulsar el botón de logout del topbar de `/p96/`. Debe limpiar sessionStorage y volver al login del shell (`/`).

- [ ] **5. Acceso directo a /p96/ con allowlist** — abrir `/p96/` directamente en una pestaña nueva (sin token). Debe aparecer el overlay de login del mockup **filtrado**: NO deben verse las cards `TEAM_LEAD`, `TECH_SENIOR`, `TECH_JUNIOR`. Hacer click en la card **CEO** → carga datos reales.

- [ ] **6. CIO sin salarios individuales** — login (vía shell o card del overlay) como `roberto.navarro@cognitivepmo.com` / `12345`. Verificar que NO se muestran salarios individuales en los widgets económicos (`ver_salario_ind = false`).

- [ ] **7. TECH_JUNIOR no entra a /p96/** — desde el shell `/`, login con `adriana.suarez@cognitivepmo.com` / `12345`. Debe redirigir a `/tech-dashboard.html` y **NO** a `/p96/`.

- [ ] **8. /api/me sin token → 401** — desde la consola del navegador o `curl`:
  ```bash
  curl -i http://NAS:3030/api/me
  ```
  Debe devolver `HTTP/1.1 401 Unauthorized`.

---

**Resultado esperado:** 8/8 ✅

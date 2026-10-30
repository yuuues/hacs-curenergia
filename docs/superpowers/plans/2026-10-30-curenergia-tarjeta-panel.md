# CurEnergía Facturas (tarjeta y panel) — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Plan 3 de 3.** Los planes 1 (librería) y 2 (integración, v0.1.1 publicada y probada con datos reales) están hechos. Este plan construye la **interfaz**:

- la tarjeta Lovelace `custom:curenergia-invoices-card`, con editor visual;
- el panel lateral "Facturas";
- el registro de ambos desde la integración;
- el logo (`brand/`);
- la comprobación en CI de que el JS compilado está al día;
- la versión 0.2.0.

**Goal:** que el usuario vea la tabla factura frente a Datadis en una tarjeta y en un panel lateral, sin instalar nada aparte de la integración.

**Architecture:** el código fuente vive en `frontend/` (TypeScript + Lit, empaquetado con Rollup) y genera **un único** módulo ES, `custom_components/curenergia/frontend/curenergia.js`. Ese fichero define la tabla compartida, la tarjeta, su editor, el gráfico y el panel. La integración sirve la carpeta como ruta estática, carga el módulo en todas las vistas con `add_extra_js_url` y registra el panel con `panel_custom` cuando alguna entrada tiene activada la opción del panel. Los datos llegan solo por la API websocket del plan 2 (`curenergia/invoices`, `curenergia/summary`).

**Tech Stack:** Node 22, TypeScript 5.9.3, Lit 3.3.3, Rollup 4.66.0, Vitest 5.0.5 + happy-dom 21.0.4, Python (HA 2026.10.4 en tests), Pillow solo en el script del logo.

**Spec:** `docs/superpowers/specs/2026-10-29-curenergia-facturas-design.md` (§11, §12, §13). Boceto orientativo: `docs/superpowers/specs/2026-10-29-curenergia-boceto.html`, opciones B y C.

## Decisiones del usuario en este plan

- **U1 — Columnas de luz:** Periodo · kWh factura · kWh Datadis · Δ kWh · Importe · Δ €.
  - "Importe" es el total de la factura.
  - "Δ €" es `comparison.delta_eur`, la diferencia en potencia + energía (D2).
  - La fila desplegable muestra "Potencia + energía: factura X € / e-data Y €" (`invoice_eur` / `edata_eur`) y el Δ %.
  - No hay columna "€ e-data", porque no se puede restar del total.
- **U2 — Editor visual de la tarjeta:** sí.
- **U3 — Logo:** icono genérico generado por nosotros (una factura con un rayo), sin la marca de CurEnergía.

## Global Constraints

- **Dependencias exactas en `frontend/package.json`** (con `npm ci` y `package-lock.json` versionado):

  | Tipo | Paquete | Versión |
  |---|---|---|
  | runtime | `lit` | `3.3.3` |
  | dev | `typescript` | `5.9.3` |
  | dev | `rollup` | `4.66.0` |
  | dev | `@rollup/plugin-typescript` | `12.3.1` |
  | dev | `@rollup/plugin-node-resolve` | `16.0.3` |
  | dev | `@rollup/plugin-terser` | `1.0.2` |
  | dev | `tslib` | `2.8.1` |
  | dev | `vitest` | `5.0.5` |
  | dev | `happy-dom` | `21.0.4` |

  - Sin `custom-card-helpers` ni otras librerías: los tipos de HA que hacen falta se definen en `types.ts`.
  - `"engines": {"node": ">=22.12"}`.
- **Salida:** `custom_components/curenergia/frontend/curenergia.js`, un único fichero ES module minificado. Se versiona en git y lo genera solo `npm run build`.
- **Nombres de elementos** (custom elements):
  - `curenergia-invoices-card` (tarjeta, `type: custom:curenergia-invoices-card`)
  - `curenergia-invoices-card-editor`
  - `curenergia-invoice-table`
  - `curenergia-bar-chart`
  - `curenergia-panel`
  - Cada `customElements.define` va protegido con `if (!customElements.get(name))`.
- **Rutas y panel:**
  - Ruta estática `/curenergia_static` → `custom_components/curenergia/frontend/`.
  - Módulo: `/curenergia_static/curenergia.js?v=<versión del manifest>`.
  - Panel: `frontend_url_path="curenergia"`, `webcomponent_name="curenergia-panel"`, `sidebar_title="Facturas"` (HA no traduce el título de un panel personalizado; dentro del panel el título sí va traducido), `sidebar_icon="mdi:receipt-text"`, `require_admin=True`.
- **Tema:** solo variables CSS de HA (`--primary-text-color`, `--secondary-text-color`, `--divider-color`, `--card-background-color`, `--success-color`, `--warning-color`, `--error-color`, `--primary-color`). Ningún color fijo.
- **Colores de Δ por estado:**

  | Estado | Color |
  |---|---|
  | `ok` | `--success-color` |
  | `no_cuadra` | `--warning-color` |
  | `estimada`, `sin_datos`, `gas` | `--secondary-text-color` |
  | `no_leida` | `--error-color` |

  - Pastillas de texto: "estimada" / "estimated" y "no se pudo leer" / "could not be read".
- **Idioma:**
  - Español si `hass.locale.language` empieza por `es`; si no, inglés. Todos los textos van en `i18n.ts`.
  - Números con `Intl.NumberFormat(hass.locale.language)`: kWh con 0–2 decimales, € con 2, €/kWh con 4, % con 1.
  - Fechas `dd/mm/aaaa` construidas a partir del texto ISO, **sin** `new Date(iso)` (evita desfases por zona horaria).
  - Un valor `null` se muestra como "—".
- **Gas, columnas:** Periodo · kWh · m³ · Importe · €/kWh.
- **Tarjeta:**
  - Configuración: `title?: string`, `supply?: "electricity" | "gas"` (pestaña inicial, por defecto `electricity`), `max_invoices?: number` (por defecto 6, entre 1 y 60), `entry_id?: string`.
  - `getStubConfig()` → `{ max_invoices: 6 }`.
  - Recarga los datos al conectarse y después cada 15 min mientras está conectada.
- **Python:** se mantienen las reglas del plan 2: privacidad, cláusulas `except (A, B):`, `scripts/ha-test.sh`, 100 % en `config_flow.py` y commits firmados sin push.

## Review Focus

1. **Sin entradas cargadas o sin facturas** (`contracts: []`): la tarjeta y el panel muestran "Todavía no hay facturas" / "No invoices yet" y no fallan. → tests en las Tareas 2 y 4.
2. **Valores nulos**: `comparison`, `edata_eur`, `delta_pct`, `periods`, `m3` o `energy_price_kwh` a `null` se muestran como "—" y no como "NaN" ni "null". → test en la Tarea 2.
3. **Fechas y zona horaria**: `"2026-08-29"` se muestra "29/08/2026" con cualquier zona horaria del navegador. → test en la Tarea 1.
4. **Dos contratos del mismo suministro**: la tabla muestra un subtítulo con el nombre de cada contrato (`name`) y sus filas debajo. → test en la Tarea 2.
5. **JS compilado desactualizado**: CI falla si `npm run build` cambia `curenergia.js` respecto a lo versionado. → paso en la Tarea 1.

---

### Task 1: Esqueleto del frontend, tipos, API, formato, idiomas y build

**Files:**
- Create: `frontend/package.json`, `frontend/package-lock.json`, `frontend/tsconfig.json`, `frontend/rollup.config.mjs`, `frontend/vitest.config.ts`
- Create: `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/format.ts`, `frontend/src/i18n.ts`, `frontend/src/index.ts`
- Create: `frontend/test/format.test.ts`, `frontend/test/api.test.ts`, `frontend/test/i18n.test.ts`
- Create: `custom_components/curenergia/frontend/curenergia.js` (generado)
- Modify: `.github/workflows/integration.yml` (job `frontend`), `.github/dependabot.yml` (npm en `/frontend`), `.gitignore` (`frontend/node_modules/`)

**Interfaces:**
- Produces (`types.ts`): reflejan exactamente el contrato websocket del plan 2 (`custom_components/curenergia/websocket.py`).
  - `InvoiceRow`, `Comparison`, `ContractInvoices`, `InvoicesResponse` y `Summary`. Mismos nombres de clave que el JSON, `number | null` donde puede venir `null`, `supply: "electricity" | "gas"`.
  - `Status = "ok" | "no_cuadra" | "estimada" | "sin_datos" | "no_leida" | "gas"`.
  - `HomeAssistant`, el subconjunto mínimo: `locale: { language: string }`, `connection: { sendMessagePromise<T>(msg: object): Promise<T> }`, `language: string`.
- Produces (`api.ts`):
  - `fetchInvoices(hass, opts?: { entry_id?: string; supply?: Supply }): Promise<InvoicesResponse>`
  - `fetchSummary(hass, entry_id?: string): Promise<Summary>`
  - Envían `{type: "curenergia/invoices", ...}` y `{type: "curenergia/summary", ...}` sin claves `undefined`.
- Produces (`format.ts`):
  - `formatDate(iso: string): string`
  - `formatPeriod(start: string, end: string): string` (devuelve "29/08 – 28/09/2026"; con años distintos, "29/12/2025 – 28/01/2026")
  - `formatKwh(lang, v: number | null): string`
  - `formatEur(lang, v): string`
  - `formatPricePerKwh(lang, v): string`
  - `formatPct(lang, v): string`
  - `formatDelta(lang, v, kind: "kwh" | "eur"): string` (con signo "+"/"−"; "0" sin signo)
  - `deltaColorVar(status: Status): string` (devuelve el nombre de la variable CSS según la tabla de Global Constraints)
- Produces (`i18n.ts`): `t(hass: HomeAssistant, key: StringKey, vars?: Record<string, string | number>): string`.
  - `StringKey` es la unión de claves de un objeto `STRINGS = { es: {...}, en: {...} }` con las mismas claves en los dos idiomas.
  - Incluye los textos de estado del plan 2 (Cuadra / No cuadra / Lectura estimada / Sin datos suficientes / No se pudo leer / Gas (sin casar)), las cabeceras de columna, las pestañas Luz / Gas, el vacío, el error y los textos del panel y del editor.

- [ ] **Step 1: crear `package.json`, `tsconfig.json`, `rollup.config.mjs` y `vitest.config.ts`**
  - `package.json`: dependencias según Global Constraints. Scripts:
    - `"build": "rollup -c"`
    - `"test": "vitest run"`
    - `"typecheck": "tsc --noEmit"`
  - `tsconfig.json`: `target ES2021`, `module ESNext`, `moduleResolution bundler`, `strict`, `experimentalDecorators true`, `useDefineForClassFields false`.
  - `rollup.config.mjs`: entrada `src/index.ts`, salida `../custom_components/curenergia/frontend/curenergia.js` (formato `es`), plugins node-resolve + typescript + terser.
  - `vitest.config.ts`: `environment: "happy-dom"`, `include: ["test/**/*.test.ts"]`.
  - Generar el lock con `npm install --prefix frontend`.

- [ ] **Step 2: escribir los tests que fallan**

```ts
// format.test.ts
it("formats ISO dates without timezone shift", () => {
  process.env.TZ = "America/Los_Angeles";
  expect(formatDate("2026-08-29")).toBe("29/08/2026");
});
it("formats periods", () => {
  expect(formatPeriod("2026-08-29", "2026-09-28")).toBe("29/08 – 28/09/2026");
  expect(formatPeriod("2025-12-28", "2026-01-31")).toBe("28/12/2025 – 31/01/2026");
});
it("formats numbers per locale and nulls as dash", () => {
  expect(formatEur("es", 102.55)).toBe("102,55 €");
  expect(formatKwh("en", 380.06)).toBe("380.06 kWh");
  expect(formatPricePerKwh("es", 0.2698)).toBe("0,2698 €/kWh");
  expect(formatEur("es", null)).toBe("—");
});
it("signs deltas", () => {
  expect(formatDelta("es", -1.82, "eur")).toBe("−1,82 €");
  expect(formatDelta("es", 5, "kwh")).toBe("+5 kWh");
  expect(formatDelta("es", 0, "kwh")).toBe("0 kWh");
});
it("maps status to theme colour variables", () => {
  expect(deltaColorVar("ok")).toBe("--success-color");
  expect(deltaColorVar("no_cuadra")).toBe("--warning-color");
  expect(deltaColorVar("estimada")).toBe("--secondary-text-color");
  expect(deltaColorVar("no_leida")).toBe("--error-color");
});
// api.test.ts — un hass falso con sendMessagePromise = vi.fn()
it("sends the invoices command without undefined keys", async () => { /* expect toHaveBeenCalledWith({type: "curenergia/invoices", supply: "gas"}) */ });
it("sends the summary command with entry_id", async () => { /* {type: "curenergia/summary", entry_id: "abc"} */ });
// i18n.test.ts
it("has the same keys in es and en", () => { expect(Object.keys(STRINGS.es).sort()).toEqual(Object.keys(STRINGS.en).sort()); });
it("picks Spanish for es-ES and English otherwise", () => { /* t({locale:{language:"es-ES"}}, "tab_electricity") === "Luz"; "de" → "Electricity" */ });
```

  Nota: si el formateo de `Intl` mete espacios especiales (` `), el test normaliza los espacios antes de comparar, y la implementación también los normaliza.

- [ ] **Step 3: ejecutar los tests y comprobar que fallan**

Run: `npm --prefix frontend test`
Expected: FAIL (no existen los módulos).

- [ ] **Step 4: implementar `types.ts`, `api.ts`, `format.ts`, `i18n.ts` e `index.ts`**. `index.ts` solo importa los módulos de elementos; las Tareas 2–4 los añaden.

- [ ] **Step 5: ejecutar los tests y la comprobación de tipos**

Run: `npm --prefix frontend test && npm --prefix frontend run typecheck`
Expected: PASS.

- [ ] **Step 6: build y job de CI**
  - Ejecutar `npm --prefix frontend run build`. Debe crear `custom_components/curenergia/frontend/curenergia.js`.
  - Añadir el job `frontend` a `integration.yml`:
    - checkout fijado al mismo SHA y con `persist-credentials: false`;
    - `actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0` con `node-version: 22`;
    - `npm ci`, `npm run typecheck`, `npm test` y `npm run build` con `working-directory: frontend`;
    - por último `git diff --exit-code -- custom_components/curenergia/frontend/` para que falle si el bundle no está al día.
  - Añadir `frontend/**` a las rutas del workflow.
  - Añadir el ecosistema `npm` en `/frontend` a Dependabot.

- [ ] **Step 7: commit**: `feat(frontend): scaffold Lit/Rollup build with types, API, formatting and i18n`.

---

### Task 2: Tabla compartida `curenergia-invoice-table`

**Files:**
- Create: `frontend/src/invoice-table.ts`
- Test: `frontend/test/invoice-table.test.ts`
- Modify: `frontend/src/index.ts`, `custom_components/curenergia/frontend/curenergia.js` (rebuild)

**Interfaces:**
- Consumes: Tarea 1 (`types`, `format`, `i18n`).
- Produces: `class CurenergiaInvoiceTable extends LitElement`, registrado como `curenergia-invoice-table`, con estas propiedades:
  - `hass: HomeAssistant`
  - `contracts: ContractInvoices[]` (respuesta completa con los dos suministros)
  - `supply: Supply` (pestaña activa; la cambia el propio componente al pulsar una pestaña y lanza el evento `supply-changed` con `detail.supply`)
  - `maxInvoices?: number` (sin límite si no se indica)
- Comportamiento:
  - Pestañas Luz / Gas. Se muestra la pestaña aunque no tenga contratos; entonces aparece el texto de vacío.
  - Por cada contrato del suministro activo: subtítulo con `name` si hay más de un contrato de ese suministro, y una tabla con las facturas de más reciente a más antigua, limitada a `maxInvoices`.
  - Columnas según U1 y Global Constraints. El Δ kWh y el Δ € se colorean según `deltaColorVar(status)`. En las filas `estimada` se ven en gris (se muestran igualmente).
  - La celda del periodo lleva las pastillas "estimada" (si `estimated`) y "no se pudo leer" (si `status === "no_leida"`). La fila de una real que cierra un grupo (`comparison.group.length > 1`) lleva el texto "abarca N facturas" / "covers N invoices".
  - La fila es desplegable (clic o Enter, `aria-expanded`). El detalle muestra:
    - los conceptos (`label` e importe) y el IVA (`rate`, `base`, `amount`);
    - en luz, P1/P2/P3 factura / Datadis;
    - en luz, "Potencia + energía: factura X € / e-data Y € (Δ Z %)" y el €/kWh de la energía (`energy_price_kwh`);
    - si `in_group_of`, "regularizada en la factura N" / "settled by invoice N";
    - si `comparison.group.length > 1`, la lista de números de factura del grupo.

- [ ] **Step 1: escribir los tests que fallan.** Montar el elemento en happy-dom con datos inventados y esperar a `updateComplete`.

```ts
it("renders electricity columns in order", ...);     // cabeceras: Periodo, kWh factura, kWh Datadis, Δ kWh, Importe, Δ €
it("renders gas columns in order", ...);             // Periodo, kWh, m³, Importe, €/kWh
it("shows dashes for null comparison values", ...);  // fila sin comparison → "—" en kWh Datadis, Δ kWh, Δ €; nunca "NaN"/"null"
it("colours deltas by status", ...);                 // ok → style con var(--success-color); no_cuadra → --warning-color
it("labels estimated and unreadable rows", ...);
it("expands a row on click and Enter", ...);         // aria-expanded true; detalle con conceptos, P1..P3 y "factura … / e-data …"
it("limits rows to maxInvoices, newest first", ...);
it("shows a header per contract when there are two of the same supply", ...);
it("shows the empty text when there are no contracts", ...);
it("switches tab and emits supply-changed", ...);
```

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `npm --prefix frontend test -- invoice-table`
Expected: FAIL.

- [ ] **Step 3: implementar `invoice-table.ts`**. Estilos con las variables CSS de HA. En ancho estrecho (`< 450px`), la tabla hace scroll horizontal dentro de su contenedor.

- [ ] **Step 4: ejecutar los tests, la comprobación de tipos y el build**

Run: `npm --prefix frontend test && npm --prefix frontend run typecheck && npm --prefix frontend run build`
Expected: PASS y bundle regenerado.

- [ ] **Step 5: commit**: `feat(frontend): add shared invoice table with tabs and expandable rows`.

---

### Task 3: Tarjeta y editor visual

**Files:**
- Create: `frontend/src/card.ts`, `frontend/src/card-editor.ts`
- Test: `frontend/test/card.test.ts`, `frontend/test/card-editor.test.ts`
- Modify: `frontend/src/index.ts`, `custom_components/curenergia/frontend/curenergia.js`

**Interfaces:**
- Consumes: Tareas 1–2.
- Produces:
  - `curenergia-invoices-card`:
    - `setConfig(config)` valida `max_invoices` (entero de 1 a 60) y `supply` (`electricity` / `gas`) y lanza `Error` con mensaje claro si no son válidos.
    - `static getStubConfig()` → `{ max_invoices: 6 }`.
    - `static getConfigElement()` → `document.createElement("curenergia-invoices-card-editor")`.
    - `getCardSize()` → `3 + min(max_invoices, filas)`.
    - Al recibir `hass` por primera vez llama a `fetchInvoices(hass, {entry_id})`, y vuelve a hacerlo cada 15 min mientras está conectada (el intervalo se limpia en `disconnectedCallback`).
    - Muestra `ha-card` con `header = title ?? t("card_title")`, dentro la tabla con `supply` inicial y `maxInvoices`. Si hay error, muestra `t("load_error")`, sin el detalle del error.
  - Registro en `window.customCards`: `{ type: "curenergia-invoices-card", name: "CurEnergía", description: <t en>, preview: false, documentationURL: "https://github.com/yuuues/hacs-curenergia#readme" }`.
  - `curenergia-invoices-card-editor`:
    - usa `ha-form` con este esquema: `title` (text), `supply` (select electricity/gas), `max_invoices` (number box 1–60) y `entry_id` (selector `config_entry` con `integration: "curenergia"`);
    - etiquetas vía `computeLabel` con `t()`;
    - al cambiar, lanza `config-changed` con `detail.config` (sin claves vacías).

- [ ] **Step 1: escribir los tests que fallan**

```ts
it("rejects invalid max_invoices and supply", ...);         // setConfig({max_invoices: 0}) lanza; {supply: "water"} lanza
it("returns a stub config", ...);                            // getStubConfig() deep-equals {max_invoices: 6}
it("fetches once on first hass and every 15 minutes", ...);  // vi.useFakeTimers; 2 llamadas tras 15 min; 0 nuevas tras desconectar
it("passes entry_id to the API", ...);
it("shows a load error without details", ...);              // sendMessagePromise rechaza con Error("secret") → texto load_error, sin "secret"
it("registers in window.customCards once", ...);
it("editor emits config-changed without empty keys", ...);   // value-changed de ha-form con {title: "", max_invoices: 4} → {max_invoices: 4, type...}
```

  Nota: `ha-card` y `ha-form` no existen en los tests. Se definen elementos falsos mínimos en un helper de test.

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `npm --prefix frontend test -- card`
Expected: FAIL.

- [ ] **Step 3: implementar `card.ts` y `card-editor.ts`**.

- [ ] **Step 4: ejecutar los tests, la comprobación de tipos y el build**

Run: `npm --prefix frontend test && npm --prefix frontend run typecheck && npm --prefix frontend run build`
Expected: PASS.

- [ ] **Step 5: commit**: `feat(frontend): add invoices card with visual editor`.

---

### Task 4: Gráfico y panel lateral

**Files:**
- Create: `frontend/src/chart.ts`, `frontend/src/panel.ts`
- Test: `frontend/test/chart.test.ts`, `frontend/test/panel.test.ts`
- Modify: `frontend/src/index.ts`, `custom_components/curenergia/frontend/curenergia.js`

**Interfaces:**
- Consumes: Tareas 1–2.
- Produces:
  - `curenergia-bar-chart`:
    - Propiedades: `hass` e `invoices: InvoiceRow[]`. Usa las de luz, como mucho las 12 más recientes, ordenadas de más antigua a más reciente.
    - Dibuja un SVG propio, sin librerías:
      - por factura, una barra "factura" (`--primary-color`) y otra "Datadis" (`--secondary-text-color`), escaladas al máximo;
      - leyenda;
      - etiqueta del eje X con `mm/aa` de `period_end`;
      - `<title>` en cada barra con el valor formateado.
    - Una factura sin comparación solo dibuja la barra de factura.
  - `curenergia-panel`:
    - Propiedades HA de panel: `hass`, `narrow`, `panel`.
    - Al recibir `hass` por primera vez, llama a `fetchSummary` y `fetchInvoices` (sin `entry_id`, es decir, todas las entradas).
    - Muestra:
      - una barra superior con `ha-menu-button` (`.hass`, `.narrow`) y el título `t("panel_title")`;
      - tres KPI del resumen: "Facturado en 12 meses" (`billed_12m` €), "kWh factura vs Datadis" (`kwh_delta_pct` %, con signo) y "Lecturas estimadas" (`estimated_count`);
      - un aviso si `mail_error` ("No se pudo leer el correo; se muestran las facturas guardadas");
      - un aviso si `unreadable_emails > 0` ("N correos con factura que no se pudo leer");
      - el gráfico y la tabla compartida sin límite de filas.
    - Recarga cada 15 min, como la tarjeta.

- [ ] **Step 1: escribir los tests que fallan**

```ts
it("draws one pair of bars per electricity invoice, max 12, oldest first", ...);
it("draws only the invoice bar when comparison is null", ...);
it("renders KPIs from the summary", ...);           // 1234.5 € → "1234,50 €"; kwh_delta_pct 1.2 → "+1,2 %"; null → "—"
it("shows mail error and unreadable warnings", ...);
it("shows the empty text with no contracts", ...);
it("fetches summary and invoices once on first hass", ...);
```

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `npm --prefix frontend test -- chart panel`
Expected: FAIL.

- [ ] **Step 3: implementar `chart.ts` y `panel.ts`**.

- [ ] **Step 4: ejecutar los tests, la comprobación de tipos y el build**

Run: `npm --prefix frontend test && npm --prefix frontend run typecheck && npm --prefix frontend run build`
Expected: PASS.

- [ ] **Step 5: commit**: `feat(frontend): add sidebar panel with KPIs and invoice chart`.

---

### Task 5: Registro desde la integración

**Files:**
- Create: `custom_components/curenergia/frontend.py`
- Modify: `custom_components/curenergia/__init__.py`, `custom_components/curenergia/manifest.json`
- Test: `tests/test_frontend.py`

**Interfaces:**
- Consumes: el bundle de las Tareas 1–4 y la opción `CONF_SHOW_PANEL` (`const.py`).
- Produces (`frontend.py`):
  - `async def async_register_frontend(hass) -> None`: se llama una vez desde `async_setup`.
    - Registra la ruta estática con `hass.http.async_register_static_paths([StaticPathConfig("/curenergia_static", <dir frontend>, cache_headers=False)])`.
    - Añade `add_extra_js_url(hass, f"/curenergia_static/curenergia.js?v={version}")`, con la versión leída de `async_get_integration(hass, DOMAIN)`.
    - Guarda la URL del módulo en `hass.data[DOMAIN]`.
  - `async def async_update_panel(hass) -> None`:
    - Si alguna entrada **cargada** de `curenergia` tiene `show_panel` activado (`True` por defecto), registra el panel con `panel_custom.async_register_panel` (valores de Global Constraints, `module_url` = la URL del módulo) si aún no está registrado.
    - Si no, lo quita con `frontend.async_remove_panel(hass, "curenergia", warn_if_unknown=False)`.
    - Se llama al final de `async_setup_entry` y en `async_unload_entry` (después de descargar). El cambio de opciones pasa por la recarga.
  - `manifest.json`: `dependencies` pasa a `["frontend", "http", "panel_custom", "recorder", "websocket_api"]`, y `version` a `"0.2.0"`.

- [ ] **Step 1: escribir los tests que fallan** (con R14: `pytestmark` con `recorder_mock` y `enable_custom_integrations`)

```python
async def test_module_served_and_added(hass, hass_client): ...   # GET /curenergia_static/curenergia.js → 200; la URL con ?v=0.2.0 está en hass.data[frontend DATA_EXTRA_MODULE_URL]
async def test_panel_registered_for_admins(hass): ...            # tras setup con show_panel True: "curenergia" en hass.data[frontend DATA_PANELS], require_admin True, sidebar_icon "mdi:receipt-text"
async def test_panel_removed_when_option_off(hass): ...          # options show_panel False + recarga → panel ausente
async def test_panel_kept_while_another_entry_wants_it(hass): ...# dos entradas, se descarga una → el panel sigue
async def test_panel_removed_on_last_unload(hass): ...
```

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `scripts/ha-test.sh tests/test_frontend.py -v`
Expected: FAIL.

- [ ] **Step 3: implementar `frontend.py` y los cambios en `__init__.py` y `manifest.json`**.

- [ ] **Step 4: ejecutar todos los tests y ruff**

Run: `scripts/ha-test.sh && scripts/ha-test.sh --ruff`
Expected: PASS. `config_flow.py` sigue al 100 %.

- [ ] **Step 5: commit**: `feat(ha): serve the frontend bundle and register the sidebar panel`.

---

### Task 6: Logo, documentación y versión 0.2.0

**Files:**
- Create: `scripts/make_brand.py`
- Create: `custom_components/curenergia/brand/icon.png` (256×256), `icon@2x.png` (512×512), `logo.png` (256×256), `logo@2x.png` (512×512), `dark_icon.png`, `dark_logo.png`
- Modify: `custom_components/curenergia/quality_scale.yaml` (`brands: done`), `.github/workflows/integration.yml` (quitar `ignore: brands` si HACS ya acepta `brand/` local; si no, se mantiene y se explica en el commit)
- Modify: `README.md` (tarjeta: cómo añadirla y sus opciones; panel: qué muestra, opción para ocultarlo y que es solo para administradores), y el spec §11 (la decisión U1 y que la tarjeta tiene editor visual)

**Interfaces:** ninguna nueva.

- [ ] **Step 1: escribir `scripts/make_brand.py`**:
  - Genera los PNG con Pillow (ejecutar con `uv run --with pillow python scripts/make_brand.py`).
  - Diseño: cuadrado redondeado transparente, hoja de factura blanca con tres líneas grises y un rayo ámbar (`#FFB300`) en la esquina inferior derecha. La variante `dark_` lleva una hoja gris claro.
  - Nada de logos ni colores de CurEnergía.
  - El script es determinista: misma salida en cada ejecución.

- [ ] **Step 2: generar las imágenes y comprobarlas**

Run: `uv run --with pillow python scripts/make_brand.py && uv run --with pillow python -c "from PIL import Image; import sys; [print(p, Image.open(p).size) for p in sys.argv[1:]]" custom_components/curenergia/brand/*.png`
Expected: tamaños 256×256 y 512×512 según el nombre.

- [ ] **Step 3: actualizar `quality_scale.yaml`, el README y el spec §11; verificar**

Run: `scripts/ha-test.sh && scripts/ha-test.sh --ruff && npm --prefix frontend test && npm --prefix frontend run build && git diff --exit-code -- custom_components/curenergia/frontend/`
Expected: todo en verde y sin diferencias en el bundle.

- [ ] **Step 4: comprobar que no hay datos personales**

Run: el mismo comando de recuento del plan 2 sobre los ficheros cambiados desde el commit de este plan (excluyendo `uv.lock` y `frontend/package-lock.json`).
Expected: `0`.

- [ ] **Step 5: commit**: `feat: add brand images and document the card and panel (0.2.0)`.
  - La etiqueta `v0.2.0` y la release las hace el controlador **después** de que el usuario lo apruebe; no forman parte de esta tarea.

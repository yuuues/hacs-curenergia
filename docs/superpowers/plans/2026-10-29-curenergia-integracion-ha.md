# CurEnergía Facturas (integración de Home Assistant) — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Plan 2 de 3.** El plan 1 (librería `pycurenergia` 0.1.0) está hecho. Este plan construye la **parte Python de la integración**: config flow, IMAP, almacenamiento, casación con e-data, sensores, botón, API websocket, diagnósticos, calidad Bronze y CI. El **plan 3** construye la tarjeta y el panel (TypeScript + Lit), registra sus rutas estáticas y el panel lateral, añade el logo (`brand/`) y prepara la release para HACS. Por eso aquí la opción "panel lateral" solo se guarda: el plan 3 la usa.

**Goal:** integración `curenergia` que lee automáticamente las facturas de CurEnergía del correo (IMAP, solo lectura), las guarda, las casa con las estadísticas largas de e-data, y las expone como sensores y por websocket.

**Architecture:** la lógica que no depende de Home Assistant vive en módulos puros que se prueban sin HA: `imap_utf7.py`, `mail.py` (cliente IMAP síncrono sobre `imaplib`, con la fábrica de conexión inyectable) y `matching.py` (agrupación de estimadas y comparación). Los módulos de HA (`storage.py`, `edata.py`, `coordinator.py`, plataformas, `websocket.py`, `diagnostics.py`) los orquestan. Un `DataUpdateCoordinator` por entrada sondea el correo cada 6 h, parsea los PDF nuevos en el executor, guarda las facturas en un `Store` y recalcula la casación leyendo el recorder. Los sensores y la API websocket leen solo los datos del coordinador.

**Tech Stack:** Python ≥ 3.14.2, Home Assistant 2026.10.4 (para tests), `pytest-homeassistant-custom-component==0.13.375`, `pycurenergia==0.1.0`, `imaplib` y `email` de la biblioteca estándar, `uv`, `ruff`, Docker para ejecutar los tests en Linux, GitHub Actions (hassfest, HACS, tests).

**Spec:** `docs/superpowers/specs/2026-10-29-curenergia-facturas-design.md` (§7, §8.2, §8.3, §9, §10, §11.1, §12, §13, §14).

## Hechos verificados (para que el implementador no los repita)

- **e-data** (`uvejota/homeassistant-edata` 2026.10.4, dominio `edata`):
  - La entrada guarda `data["cups"]` (CUPS completo) y `data["scups"]` (sufijo corto). Su `unique_id` es el CUPS en mayúsculas.
  - El `<id>` de las estadísticas es `data["scups"].lower()`. Ids: `edata:<id>_consumption`, `edata:<id>_p1_consumption` (`_p2_`, `_p3_`), `edata:<id>_power_cost`, `edata:<id>_energy_cost`.
  - Son estadísticas externas horarias con `has_sum=True`. Cada fila lleva `start` = **inicio** de la hora (Datadis entrega la hora 1..24 como final del intervalo, y e-data resta 1 h), `state` = valor de esa hora y `sum` acumulado. Las de `p1..p3` solo tienen filas en las horas de ese tramo.
  - Las de coste solo existen si el usuario activó la facturación en e-data.
  - `power_term`/`energy_term` de e-data **incluyen el impuesto eléctrico y el IVA** con sus fórmulas por defecto: `electricity_tax * iva_tax * …`, con `electricity_tax=1.0511300560` e `iva_tax=1.21`.
- **Correo**: el remitente envía también avisos sin PDF, que se ignoran. El cuerpo HTML trae una línea `Importe: N,NN €`. El adjunto se llama `{contrato}_{marca de tiempo}.pdf`, así que no sirve para saber el número de factura.
- **Tests**: Home Assistant no corre en Windows. Los tests de la integración se ejecutan en un contenedor Docker con `scripts/ha-test.sh` (Tarea 1). Los de la librería siguen como en el plan 1.

## Global Constraints

- Dominio `curenergia`. Código en `custom_components/curenergia/`. `manifest.json`:
  - `"requirements": ["pycurenergia==0.1.0"]`, `"version": "0.1.0"`, `"codeowners": ["@yuuues"]`
  - `"config_flow": true`, `"integration_type": "service"`, `"iot_class": "cloud_polling"`
  - `"dependencies": ["recorder", "websocket_api"]`
  - `"documentation"` y `"issue_tracker"` apuntan a `https://github.com/yuuues/hacs-curenergia`
- `hacs.json` (raíz): `{"name": "CurEnergía Facturas", "homeassistant": "2026.3.0", "render_readme": true}`.
- Remitente fijo: `noresponder@clientescurenergia.es`. Valores por defecto:

  | Opción | Valor |
  |---|---|
  | servidor | `imap.gmail.com` |
  | puerto | `993` (SSL) |
  | sondeo | 6 h |
  | umbral kWh | `1` |
  | umbral € | `2` % |
  | panel lateral | sí |
  | guardar PDF | no |
  | vínculo e-data | automático |

- Estados de factura, exactamente: `ok`, `no_cuadra`, `estimada`, `sin_datos`, `no_leida`, `gas`.
- Los umbrales son estrictos: se marca si `|Δ| > umbral`, y una diferencia igual al umbral no se marca.
- Ventana de una factura: `[period_start 00:00, period_end + 1 día 00:00)` en la zona horaria de HA (`dt_util.get_default_time_zone()`), la misma que usa e-data al escribir.
- Importes y kWh internos en `Decimal`. En el `Store` se guardan como `str`. En websocket y en los sensores salen como números (`float`), redondeados a 2 decimales (€ y kWh) y a 4 (€/kWh).
- **Privacidad (§14):**
  - Los logs nunca incluyen CUPS, contrato, número de factura, nombre, dirección, correo, asunto ni texto del correo o del PDF. Para identificar algo se usa el UID IMAP o el índice.
  - Los diagnósticos ocultan `username`, `password`, `cups`, `contract` y `number` con `async_redact_data`.
  - Nunca se suben al repo datos reales: los tests usan las fixtures anonimizadas de `lib/tests/fixtures/` y valores inventados.
- Textos de UI: `strings.json` (inglés) = `translations/en.json` (copia exacta, un test lo comprueba), y `translations/es.json` (español).
- Sin acciones de servicio. La búsqueda manual es una entidad `button`.
- Ejecutar los tests de la integración con `scripts/ha-test.sh [args de pytest]` desde Git Bash. `ruff` se ejecuta con `scripts/ha-test.sh --ruff`.
- Commits firmados (no usar `--no-gpg-sign`). Mensajes en inglés, con el estilo `feat(ha): …` / `test(ha): …` / `ci: …`.

## Review Focus

1. **Correo reenviado o duplicado con la misma factura**: se guarda una sola vez, por número de factura, y se conserva la primera. → test en la Tarea 7.
2. **Correos del remitente sin PDF** (avisos, la mayoría de los ~67 del buzón): se ignoran sin error y su UID queda como procesado. → test en la Tarea 7.
3. **Cambio de hora dentro de la ventana** (octubre: 745 h, marzo: 743 h): la cobertura de Datadis se calcula con horas reales transcurridas y no da `sin_datos` falso. → test en la Tarea 5.
4. **Carpeta con acentos o espacios** (`Facturas/Energía`): se muestra decodificada y el `SELECT` usa el nombre en UTF-7 modificado y entre comillas. → tests en la Tarea 2.
5. **Fallo temporal de IMAP después del primer arranque**: los sensores siguen disponibles con los datos guardados y solo se registra un aviso. Un fallo de login lanza reautenticación. → tests en la Tarea 7.

## Decisiones tomadas al planificar (revisables)

- **D1 — Lectura de correo:** `imaplib` en el executor, sin dependencias nuevas. Se descarga el mensaje entero con `BODY.PEEK[]` (no marca como leído) y solo los UID nuevos. La primera vez son unos 35 MB.
- **D2 — € comparables:** la factura se lleva a la misma base que e-data. `factura_€ = (potencia + energía) × (1 + impuesto_eléctrico / (potencia + energía + bono_social)) × (1 + IVA/100)`. Δ € = factura_€ − e-data_€. Δ % = Δ € / e-data_€ × 100. Si el usuario cambió las fórmulas de e-data, la comparación pierde sentido (se documenta en el README).
- **D3 — Cobertura de Datadis:** la ventana está cubierta si `edata:<id>_consumption` tiene al menos `horas − 2` filas horarias, la primera empieza antes de `inicio + 2 h` y la última empieza en `fin − 3 h` o después. Si no, `sin_datos`.
- **D4 — PDF que no se puede leer** (`InvoiceParseError`/`InvoiceReadError`): no hay número de factura, así que no hay fila. Se guarda el UID con la versión de `pycurenergia`. Se reintenta cuando cambia la versión de la librería, y se cuenta en el resumen (`unreadable_emails`). `UnsupportedInvoiceError` (rectificativa, abono) se guarda aparte y no se reintenta (`unsupported_emails`).
- **D5 — Fallo de IMAP con datos ya guardados:** aviso en el log y se siguen sirviendo los datos guardados. Así los sensores no pasan a "no disponible" por un corte de red.
- **D6 — Dispositivos:** uno por contrato, llamado `CurEnergía luz` / `CurEnergía gas`. Si hay más de un contrato del mismo tipo, se añade un espacio y los 4 últimos dígitos del contrato. El botón va en un dispositivo de servicio por entrada, llamado `CurEnergía`. `unique_id` de entidad: `f"{entry_id}_{contract}_{key}"`.
- **D7 — Websocket:** cualquier usuario autenticado puede leerlo, como los sensores. El panel (plan 3) es solo para administradores.
- **D8 — Grupo de estimadas que no se puede cerrar:** el grupo (estimadas seguidas + la real) debe ser contiguo: cada `period_start` es el día siguiente al `period_end` anterior. La real queda `sin_datos` si el grupo tiene un hueco, si contiene una `no_leida`, o si su primera factura es la más antigua guardada de ese contrato y además es estimada (no se sabe si había estimadas antes).

---

### Task 1: Esqueleto, entorno de tests y manifiesto

**Files:**
- Create: `pyproject.toml` (raíz), `uv.lock` (raíz), `scripts/ha-test.sh`, `hacs.json`
- Create: `custom_components/curenergia/__init__.py`, `const.py`, `manifest.json`
- Create: `tests/__init__.py`, `tests/conftest.py`, `tests/test_init.py`

**Interfaces:**
- Produces (`const.py`):
  - `DOMAIN = "curenergia"` y `SENDER = "noresponder@clientescurenergia.es"`.
  - Claves de opciones: `CONF_FOLDER = "folder"`, `CONF_SCAN_HOURS = "scan_hours"`, `CONF_KWH_THRESHOLD = "kwh_threshold"`, `CONF_EUR_THRESHOLD_PCT = "eur_threshold_pct"`, `CONF_SHOW_PANEL = "show_panel"`, `CONF_SAVE_PDFS = "save_pdfs"`, `CONF_EDATA_ENTRY = "edata_entry"`. Para `CONF_EDATA_ENTRY`, el valor `EDATA_AUTO = "auto"` significa vínculo automático.
  - Valores por defecto: `DEFAULT_HOST = "imap.gmail.com"`, `DEFAULT_PORT = 993`, `DEFAULT_SCAN_HOURS = 6`, `DEFAULT_KWH_THRESHOLD = 1.0`, `DEFAULT_EUR_THRESHOLD_PCT = 2.0`.
  - En los datos de la entrada se usan `CONF_HOST`, `CONF_PORT`, `CONF_USERNAME` y `CONF_PASSWORD` de `homeassistant.const`.
- Produces (tests):
  - `tests/conftest.py` activa `auto_enable_custom_integrations` (autouse).
  - Fixture `madrid_tz`: `await hass.config.async_set_time_zone("Europe/Madrid")`.
  - Fixture `fixture_invoice(name: str) -> Invoice`: hace `parse_invoice_text` de `lib/tests/fixtures/<name>.txt`. Nombres: `electricity_2026-10`, `gas_2026-09`.
  - Helper `make_invoice(**changes) -> Invoice`: `dataclasses.replace` sobre la fixture de luz.

- [ ] **Step 1: `pyproject.toml` de la raíz**:
  - Proyecto no empaquetable: `[project] name = "hacs-curenergia-dev"`, `version = "0"`, `requires-python = ">=3.14.2"`, `dependencies = []`, y `[tool.uv] package = false`.
  - `[dependency-groups] ha = ["pytest-homeassistant-custom-component==0.13.375", "pycurenergia", "ruff>=0.6"]`, con `[tool.uv.sources] pycurenergia = { path = "lib", editable = true }`.
  - pytest: `testpaths = ["tests"]`, `asyncio_mode = "auto"`.
  - ruff: `target-version = "py314"`, mismo `select` que la librería, `extend-exclude = ["lib"]`.

- [ ] **Step 2: `scripts/ha-test.sh`**. Ejecuta, con `MSYS_NO_PATHCONV=1`:

  ```
  docker run --rm -v "<raíz>:/work" -v curenergia-venv:/work/.venv -v curenergia-uvcache:/root/.cache/uv -w /work ghcr.io/astral-sh/uv:python3.14-trixie-slim uv run --locked --group ha pytest "$@"
  ```

  - Con `--ruff` como primer argumento, en lugar de pytest ejecuta `ruff check custom_components tests` y `ruff format --check custom_components tests`.
  - Con `--lock`, ejecuta `uv lock`.
  - `<raíz>` es el directorio del repo obtenido con `git rev-parse --show-toplevel`.

- [ ] **Step 3: generar `uv.lock`**

Run: `scripts/ha-test.sh --lock`
Expected: crea `uv.lock` sin errores.

- [ ] **Step 4: escribir el test que falla**

```python
async def test_manifest_loads(hass):
    integration = await async_get_integration(hass, DOMAIN)
    assert integration.requirements == ["pycurenergia==0.1.0"]
    assert integration.config_flow is True

def test_fixture_invoice_parses(fixture_invoice):
    assert fixture_invoice("electricity_2026-10").supply is SupplyType.ELECTRICITY
    assert fixture_invoice("gas_2026-09").supply is SupplyType.GAS
```

- [ ] **Step 5: ejecutar el test y comprobar que falla**

Run: `scripts/ha-test.sh tests/test_init.py -v`
Expected: FAIL (`IntegrationNotFound`).

- [ ] **Step 6: crear el código**
  - `manifest.json` según Global Constraints.
  - `const.py`.
  - `__init__.py` con `CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)` y un `async_setup` que devuelve `True`. La Tarea 7 lo completa.
  - `hacs.json`.

- [ ] **Step 7: ejecutar el test y comprobar que pasa**

Run: `scripts/ha-test.sh tests/test_init.py -v`
Expected: PASS.

- [ ] **Step 8: commit**: `feat(ha): scaffold curenergia integration and dockerised test env`.

---

### Task 2: Cliente IMAP de solo lectura

**Files:**
- Create: `custom_components/curenergia/imap_utf7.py`, `custom_components/curenergia/mail.py`
- Test: `tests/test_imap_utf7.py`, `tests/test_mail.py`, `tests/fake_imap.py`

**Interfaces:**
- Produces (`imap_utf7.py`):
  - `encode(name: str) -> str` y `decode(name: str) -> str`.
  - Implementan el UTF-7 modificado del RFC 3501 §5.1.3: `&` se escribe `&-`, los caracteres no ASCII imprimibles van en base64 de UTF-16BE con `,` en lugar de `/` y sin relleno, entre `&` y `-`.
- Produces (`mail.py`):
  - `class MailAuthError(Exception)` y `class MailConnectionError(Exception)`. Los mensajes de ambas nunca incluyen el usuario ni la contraseña.
  - `@dataclass(frozen=True) class MailMessage`: `uid: int`, `email_total: Decimal | None`, `pdfs: tuple[bytes, ...]`.
  - `@dataclass(frozen=True) class FetchResult`: `uidvalidity: int`, `all_uids: frozenset[int]`, `messages: tuple[MailMessage, ...]`.
  - `class MailClient(host: str, port: int, username: str, password: str, *, imap_factory: Callable[[str, int], imaplib.IMAP4] | None = None)`. Por defecto la fábrica es `imaplib.IMAP4_SSL(host, port, ssl_context=homeassistant.util.ssl.get_default_context(), timeout=30)`. Métodos, todos síncronos:
    - `check_login() -> None`: conecta, hace login y logout.
    - `list_folders() -> list[str]`: nombres decodificados, sin los que tienen `\Noselect`, en orden alfabético.
    - `fetch(folder: str, skip_uids: Collection[int], uidvalidity: int | None) -> FetchResult`: si `uidvalidity` no coincide con el del servidor, `skip_uids` se ignora.
  - `parse_email_total(body: str) -> Decimal | None`: busca `Importe:\s*([\d.]+,\d{2})\s*€` tras quitar etiquetas HTML y `&nbsp;`, y convierte con `pycurenergia.numbers.parse_decimal`.
  - `default_folder(folders: list[str]) -> str`: devuelve la primera que contenga `curenergia` (sin distinguir mayúsculas ni acentos); si no hay, `[Gmail]/All Mail` si existe; si no, `INBOX`.
- Comportamiento de `fetch`:
  - `select(<"nombre UTF-7">, readonly=True)` y `UIDVALIDITY` de `response("UIDVALIDITY")`.
  - `uid("SEARCH", None, "FROM", f'"{SENDER}"')`.
  - Por cada UID no saltado, `uid("FETCH", uid, "(BODY.PEEK[])")`.
  - Se descarta el mensaje si la dirección del `From` (con `email.utils.parseaddr`, en minúsculas) no es `SENDER`.
  - PDFs: partes con `application/pdf` o nombre de fichero que acabe en `.pdf`.
  - Texto para el importe: el `text/plain` si existe; si no, el `text/html`.
  - Login rechazado → `MailAuthError`. `OSError`, `ssl.SSLError` o `imaplib.IMAP4.error` después del login → `MailConnectionError`. Siempre se intenta `logout()`.

- [ ] **Step 1: escribir los tests que fallan**

```python
@pytest.mark.parametrize("plain,wire", [
    ("INBOX", "INBOX"), ("Facturas/Energía", "Facturas/Energ&AO0-a"),
    ("A&B", "A&-B"), ("[Gmail]/Todos", "[Gmail]/Todos"), ("日本", "&ZeVnLA-"),
])
def test_utf7_round_trip(plain, wire):
    assert encode(plain) == wire and decode(wire) == plain

def test_list_folders_decodes_and_skips_noselect(): ...   # FakeIMAP con "[Gmail]" \Noselect → no aparece; "Facturas/Energ&AO0-a" → "Facturas/Energía"
def test_fetch_selects_readonly_with_quoted_utf7_name(): ...  # fake.selected == ('"Facturas/Energ&AO0-a"', True)
def test_fetch_uses_body_peek_and_skips_known_uids(): ...     # skip {1} → solo FETCH de 2; comando contiene "BODY.PEEK[]"
def test_fetch_ignores_skip_when_uidvalidity_changed(): ...
def test_fetch_drops_message_from_other_sender(): ...          # From "otro@ejemplo.es" → no está en messages, sí en all_uids
def test_fetch_message_without_pdf_has_empty_pdfs(): ...
def test_parse_email_total_from_html():
    assert parse_email_total("<td>Importe: 1.058,40&nbsp;€</td>") == Decimal("1058.40")
    assert parse_email_total("sin importe") is None
def test_login_rejected_raises_auth_error(): ...               # FakeIMAP.login lanza imaplib.IMAP4.error
def test_socket_error_raises_connection_error(): ...           # fábrica lanza OSError
def test_default_folder_prefers_curenergia_label():
    assert default_folder(["INBOX", "[Gmail]/All Mail", "CurEnergía"]) == "CurEnergía"
    assert default_folder(["INBOX", "[Gmail]/All Mail"]) == "[Gmail]/All Mail"
    assert default_folder(["INBOX"]) == "INBOX"
```

`tests/fake_imap.py`:
- `FakeIMAP(folders: dict[str, FakeFolder], password: str = "ok")`, con `FakeFolder(uidvalidity: int, messages: dict[int, bytes])`.
- Implementa `login`, `list`, `select`, `response`, `uid`, `logout` con las mismas formas de respuesta que `imaplib` (`("OK", [b"..."])`).
- Guarda `selected` y `fetched_commands` para las aserciones.
- Los mensajes se construyen con `email.message.EmailMessage` y un PDF falso (`b"%PDF-1.4 fake"`).

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `scripts/ha-test.sh tests/test_imap_utf7.py tests/test_mail.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: implementar `imap_utf7.py` y `mail.py`** según las interfaces. El parseo de las líneas de `LIST` acepta nombres entre comillas y sin comillas.

- [ ] **Step 4: ejecutar los tests y comprobar que pasan**

Run: `scripts/ha-test.sh tests/test_imap_utf7.py tests/test_mail.py -v`
Expected: PASS.

- [ ] **Step 5: commit**: `feat(ha): add read-only IMAP client for CurEnergía emails`.

---

### Task 3: Almacenamiento de facturas y estado del buzón

**Files:**
- Create: `custom_components/curenergia/storage.py`
- Test: `tests/test_storage.py`

**Interfaces:**
- Consumes: `pycurenergia.Invoice`, `Concept`, `ConceptKey`, `SupplyType`, `Problem`.
- Produces:
  - `invoice_to_dict(invoice: Invoice) -> dict[str, Any]` / `invoice_from_dict(data: dict[str, Any]) -> Invoice`. `Decimal` → `str`, `date` → ISO, enums → valor, tuplas → listas.
  - `@dataclass class StoredInvoice`: `invoice: Invoice`, `problems: list[str]`, `email_total: Decimal | None`.
    - Propiedad `unreadable: bool`, que vale `bool(problems)`.
    - `problems` contiene los valores de `pycurenergia.Problem` más `"email_total_mismatch"` cuando `email_total` existe y difiere del total en más de 0,01.
  - `@dataclass class MailState`: `uidvalidity: int | None`, `seen: set[int]`, `failed: dict[int, str]` (UID → versión de pycurenergia), `unsupported: set[int]`.
  - `class InvoiceStore(hass, entry_id: str)`: `Store` versión 1, clave `f"curenergia.{entry_id}"`. Métodos:
    - `async_load() -> None`
    - `invoices: dict[str, StoredInvoice]` (clave: número de factura)
    - `mail: MailState`
    - `add(stored: StoredInvoice) -> bool`: `False` si el número ya existe; no reemplaza.
    - `reset_mail() -> None`
    - `async_save() -> None`
    - `async_remove() -> None`
  - `build_stored(invoice: Invoice, email_total: Decimal | None) -> StoredInvoice`: ejecuta `check_consistency` y añade la comprobación del importe del correo.

- [ ] **Step 1: escribir los tests que fallan**

```python
@pytest.mark.parametrize("name", ["electricity_2026-10", "gas_2026-09"])
def test_invoice_round_trip(fixture_invoice, name):
    inv = fixture_invoice(name)
    assert invoice_from_dict(json.loads(json.dumps(invoice_to_dict(inv)))) == inv

def test_build_stored_flags_email_total_mismatch(fixture_invoice):
    inv = fixture_invoice("electricity_2026-10")
    assert build_stored(inv, inv.total).problems == []
    assert build_stored(inv, inv.total + Decimal("0.02")).problems == ["email_total_mismatch"]
    assert build_stored(inv, None).unreadable is False

async def test_store_persists_and_deduplicates(hass, hass_storage, fixture_invoice): ...
    # add() dos veces el mismo número → True, False; tras async_save y un InvoiceStore nuevo + async_load,
    # invoices y mail (uidvalidity, seen, failed, unsupported) son iguales
```

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `scripts/ha-test.sh tests/test_storage.py -v`
Expected: FAIL.

- [ ] **Step 3: implementar `storage.py`**.

- [ ] **Step 4: ejecutar los tests y comprobar que pasan**

Run: `scripts/ha-test.sh tests/test_storage.py -v`
Expected: PASS.

- [ ] **Step 5: commit**: `feat(ha): persist invoices and mailbox state in a Store`.

---

### Task 4: Casación (lógica pura)

**Files:**
- Create: `custom_components/curenergia/matching.py`
- Test: `tests/test_matching.py`

**Interfaces:**
- Consumes: `StoredInvoice` (Tarea 3), `Invoice`, `ConceptKey`.
- Produces:
  - `class Status(StrEnum)`: `OK = "ok"`, `MISMATCH = "no_cuadra"`, `ESTIMATED = "estimada"`, `NO_DATA = "sin_datos"`, `UNREADABLE = "no_leida"`, `GAS = "gas"`.
  - `@dataclass(frozen=True) class Totals`: `kwh: Decimal`, `p1: Decimal | None`, `p2: Decimal | None`, `p3: Decimal | None`, `eur: Decimal | None`. Son las sumas de e-data en una ventana; `eur` es `power_cost + energy_cost`, o `None` si no hay costes.
  - `type TotalsProvider = Callable[[datetime, datetime], Awaitable[Totals | None]]`. Devuelve `None` si no hay e-data o la ventana no está cubierta.
  - `@dataclass(frozen=True) class Thresholds`: `kwh: Decimal`, `eur_pct: Decimal`.
  - `@dataclass(frozen=True) class Comparison`:
    - `group: tuple[str, ...]`: números de factura, del más antiguo al más reciente.
    - `window_start: datetime`, `window_end: datetime`.
    - `invoice_kwh`, `invoice_periods: tuple[Decimal | None, Decimal | None, Decimal | None]`, `invoice_eur: Decimal`.
    - `edata: Totals`.
    - `delta_kwh: Decimal`, `delta_periods: tuple[Decimal | None, …]`, `delta_eur: Decimal | None`, `delta_pct: Decimal | None`.
  - `@dataclass(frozen=True) class InvoiceRow`: `stored: StoredInvoice`, `status: Status`, `comparison: Comparison | None`, `in_group_of: str | None`. Este último es el número de la factura real que cierra el grupo, para las estimadas ya regularizadas.
  - `invoice_window(start: date, end: date, tz: tzinfo) -> tuple[datetime, datetime]`
  - `comparable_eur(invoice: Invoice) -> Decimal`: fórmula D2. Si `potencia + energía + bono_social == 0`, el factor del impuesto es 1.
  - `async def match_contract(rows: list[StoredInvoice], provider: TotalsProvider, thresholds: Thresholds, tz: tzinfo) -> list[InvoiceRow]`:
    - Recibe las facturas de **un** contrato y devuelve filas ordenadas por `period_start`.
    - Gas: todas `GAS` y sin comparación.
    - Luz: recorrido en orden.
      - Una `no_leida` da `UNREADABLE` y lleva su comparación propia si el proveedor la da.
      - Una estimada da `ESTIMATED`, con la comparación de su propia ventana (para mostrarla en gris), y se acumula en el grupo pendiente.
      - Una real cierra el grupo: ventana combinada desde el inicio de la primera estimada hasta el final de la real, con las sumas de todo el grupo. Su estado es `NO_DATA` si se cumple D8 o si el proveedor devuelve `None`. Si no, `MISMATCH` cuando el total o algún tramo P1–P3 tiene `|Δ kWh| > umbral`, o cuando `|Δ %| > umbral €`. En cualquier otro caso, `OK`.
      - Las estimadas del grupo cerrado reciben `in_group_of` y mantienen `ESTIMATED`.
      - Un tramo se compara solo si la factura y e-data lo tienen.
      - Sin `eur` de e-data, o con `eur == 0`: `delta_eur` y `delta_pct` son `None` y no cuentan para el marcado.

- [ ] **Step 1: escribir los tests que fallan.**
  - Proveedor falso: devuelve `Totals` a partir de un dict `{(inicio, fin): Totals}`, y `None` si la ventana no está.
  - Facturas creadas con `make_invoice(number=…, period_start=…, period_end=…, estimated=…, kwh=…, kwh_p1=…)`.

```python
def test_invoice_window_madrid():
    s, e = invoice_window(date(2026, 9, 5), date(2026, 10, 4), MADRID)
    assert (s.isoformat(), e.isoformat()) == ("2026-09-05T00:00:00+02:00", "2026-10-05T00:00:00+02:00")

def test_comparable_eur_grosses_up_taxes():
    inv = make_invoice(concepts=(Concept(ConceptKey.POWER, "p", Decimal("10")), Concept(ConceptKey.ENERGY, "e", Decimal("40")),
        Concept(ConceptKey.SOCIAL_BONUS, "b", Decimal("0")), Concept(ConceptKey.ELECTRICITY_TAX, "t", Decimal("2.5"))), vat_rate=Decimal("21"))
    assert comparable_eur(inv) == Decimal("50") * Decimal("1.05") * Decimal("1.21")

async def test_real_invoice_within_threshold_is_ok(): ...          # Δ total 1 kWh exacto → OK (umbral estricto)
async def test_real_invoice_over_kwh_threshold_is_mismatch(): ...   # Δ 1.01 → MISMATCH
async def test_single_period_over_threshold_is_mismatch(): ...      # total igual, P2 +1.5 → MISMATCH
async def test_eur_over_pct_threshold_is_mismatch(): ...            # Δ% 2.01 → MISMATCH; 2.00 → OK
async def test_missing_edata_costs_ignored(): ...                   # eur None → delta_eur None, estado por kWh
async def test_estimated_never_mismatch(): ...                      # estimada con Δ 50 kWh → ESTIMATED, comparison propia presente
async def test_real_after_estimates_uses_combined_window(): ...     # E1, E2, R contiguas → R.comparison.group == (E1, E2, R),
                                                                    # window = [E1.start, R.end+1d), invoice_kwh = suma; E1/E2.in_group_of == R
async def test_group_with_gap_is_no_data(): ...                     # E1 y R no contiguas → R NO_DATA
async def test_group_starting_at_oldest_estimated_is_no_data(): ... # primera factura guardada estimada → R NO_DATA
async def test_unreadable_in_group_is_no_data(): ...
async def test_trailing_estimated_waits(): ...                      # R, E → E ESTIMATED sin in_group_of
async def test_provider_none_is_no_data(): ...
async def test_gas_rows_are_gas(): ...
```

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `scripts/ha-test.sh tests/test_matching.py -v`
Expected: FAIL.

- [ ] **Step 3: implementar `matching.py`**. El módulo no importa nada de `homeassistant`.

- [ ] **Step 4: ejecutar los tests y comprobar que pasan**

Run: `scripts/ha-test.sh tests/test_matching.py -v`
Expected: PASS.

- [ ] **Step 5: commit**: `feat(ha): match invoices against e-data totals with combined windows`.

---

### Task 5: Lectura de e-data desde el recorder

**Files:**
- Create: `custom_components/curenergia/edata.py`
- Test: `tests/test_edata.py`

**Interfaces:**
- Consumes: `Totals`, `TotalsProvider` (Tarea 4).
- Produces:
  - `EDATA_DOMAIN = "edata"`
  - `find_edata_id(hass, cups: str, override_entry_id: str | None) -> str | None`:
    - Con override: la entrada de e-data con ese `entry_id`, o `None` si no existe.
    - Sin override: la entrada cuyo `data["cups"].upper()` es igual a `cups.upper()`.
    - Devuelve `data["scups"].lower()`.
  - `edata_entries(hass) -> list[tuple[str, str]]`: pares `(entry_id, title)` para el desplegable de opciones.
  - `make_provider(hass, edata_id: str) -> TotalsProvider`:
    - Ejecuta en `get_instance(hass).async_add_executor_job`.
    - Cobertura (D3): `statistics_during_period(hass, start, end, {f"edata:{edata_id}_consumption"}, "hour", None, {"state"})`.
    - Sumas: `statistic_during_period(hass, start, end, statistic_id, {"change"}, None)` para `consumption`, `p1..p3_consumption`, `power_cost` y `energy_cost`.
    - Un tramo sin filas da `None`. Para `eur`, si falta cualquiera de los dos costes, `None`.
    - Convierte a `Decimal` con `Decimal(str(round(x, 6)))`.

- [ ] **Step 1: escribir los tests que fallan.**
  - Usan las fixtures `recorder_mock` y `madrid_tz`.
  - Escriben estadísticas externas `edata:abcd_*` con `async_add_external_statistics`: filas horarias con `start`, `state` y `sum` acumulado. Después, `await async_wait_recording_done(hass)`.

```python
async def test_find_edata_id_by_cups(hass): ...          # MockConfigEntry(domain="edata", data={"cups": "ES0000000000000000AA", "scups": "00AA"}) → "00aa"
async def test_find_edata_id_override_and_missing(hass): ...
async def test_provider_sums_window(hass, recorder_mock, madrid_tz): ...
    # 1 kWh/h todo septiembre (P1 en horas 10-14, P2 resto, sin P3), costes 0.1 €/h → kwh == 720, p3 is None, eur == Decimal("144")
async def test_provider_dst_october_window_covered(hass, recorder_mock, madrid_tz): ...
    # 2026-10-01..2026-10-31: 745 h reales con fila cada hora → Totals, no None; kwh == 745
async def test_provider_incomplete_end_is_none(hass, recorder_mock, madrid_tz): ...  # faltan las 10 últimas horas → None
async def test_provider_without_costs_has_eur_none(hass, recorder_mock, madrid_tz): ...
```

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `scripts/ha-test.sh tests/test_edata.py -v`
Expected: FAIL.

- [ ] **Step 3: implementar `edata.py`**.

- [ ] **Step 4: ejecutar los tests y comprobar que pasan**

Run: `scripts/ha-test.sh tests/test_edata.py -v`
Expected: PASS.

- [ ] **Step 5: commit**: `feat(ha): read e-data long-term statistics for invoice windows`.

---

### Task 6: Config flow, reautenticación y opciones

**Files:**
- Create: `custom_components/curenergia/config_flow.py`, `strings.json`, `translations/en.json`, `translations/es.json`
- Test: `tests/test_config_flow.py`

**Interfaces:**
- Consumes: `MailClient`, `MailAuthError`, `MailConnectionError`, `default_folder` (Tarea 2) y `edata_entries` (Tarea 5).
- Produces:
  - `CurenergiaConfigFlow(ConfigFlow, domain=DOMAIN)`, `VERSION = 1`:
    - Paso `user`: `host`, `port`, `username`, `password` (selector de contraseña).
      - Prueba `check_login` en el executor. Errores: `invalid_auth` y `cannot_connect`. Cualquier otra excepción da `unknown` y se registra con `_LOGGER.exception` sin datos.
      - `unique_id = f"{username}@{host}".lower()` y `_abort_if_unique_id_configured()`.
    - Paso `folder`: `SelectSelector` con `list_folders()`, por defecto `default_folder(...)`.
      - Crea la entrada: título `CurEnergía`, la carpeta en `options[CONF_FOLDER]` y el resto de opciones por defecto.
    - Pasos `reauth` y `reauth_confirm`: solo pide la contraseña. Mismos errores. Termina con `async_update_reload_and_abort(entry, data_updates={CONF_PASSWORD: …})`.
  - `CurenergiaOptionsFlow(OptionsFlowWithReload)`, paso `init`, con los campos:

    | Campo | Selector |
    |---|---|
    | carpeta | desplegable con las carpetas leídas |
    | `scan_hours` | `NumberSelector` 1–24 |
    | `kwh_threshold` | `NumberSelector` 0–100, paso 0.1 |
    | `eur_threshold_pct` | `NumberSelector` 0–100, paso 0.1 |
    | `show_panel` | booleano |
    | `save_pdfs` | booleano |
    | `edata_entry` | desplegable: `auto` + `edata_entries` |

    - Si falla leer las carpetas, el campo carpeta pasa a texto libre con la carpeta actual y se muestra el error `cannot_connect`.
    - Si cambia la carpeta, la Tarea 7 vacía el estado del buzón al recargar.
  - Textos en los tres JSON:
    - Títulos, campos y descripciones de pasos.
    - Errores `invalid_auth`, `cannot_connect`, `unknown`.
    - Abortos `already_configured`, `reauth_successful`.
    - La descripción del paso `user` avisa de que la contraseña de aplicación da acceso a todo el buzón y enlaza al README.

- [ ] **Step 1: escribir los tests que fallan.** `MailClient` se sustituye con `patch("custom_components.curenergia.config_flow.MailClient")`.

```python
async def test_user_flow_creates_entry(hass): ...            # → folder → CREATE_ENTRY, unique_id "user@example.es@imap.gmail.com", options[folder] == "CurEnergia"
async def test_user_flow_errors(hass, exc, error): ...       # parametrizado: MailAuthError→invalid_auth, MailConnectionError→cannot_connect, RuntimeError→unknown; y luego se recupera
async def test_user_flow_already_configured(hass): ...
async def test_reauth_flow(hass): ...                        # contraseña nueva guardada, reason reauth_successful; también rama de error
async def test_options_flow(hass): ...                       # cambia umbrales y edata_entry → entry.options actualizadas
async def test_options_flow_folders_unavailable(hass): ...   # list_folders lanza MailConnectionError → errors cannot_connect, campo texto
def test_strings_match_english_translation(): ...            # json strings.json == translations/en.json; es.json tiene las mismas claves
```

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `scripts/ha-test.sh tests/test_config_flow.py -v`
Expected: FAIL.

- [ ] **Step 3: implementar `config_flow.py` y los textos**.

- [ ] **Step 4: ejecutar los tests con cobertura al 100 %**

Run: `scripts/ha-test.sh tests/test_config_flow.py --cov=custom_components.curenergia.config_flow --cov-report=term-missing --cov-fail-under=100`
Expected: PASS, y `config_flow.py` al 100 %.

- [ ] **Step 5: commit**: `feat(ha): add config, reauth and options flows`.

---

### Task 7: Coordinador, ingesta y ciclo de vida de la entrada

**Files:**
- Create: `custom_components/curenergia/coordinator.py`
- Modify: `custom_components/curenergia/__init__.py`
- Test: `tests/test_coordinator.py`, `tests/test_init.py`

**Interfaces:**
- Consumes: Tareas 2–6. Usa `pycurenergia.parse_invoice_pdf`, `InvoiceParseError`, `InvoiceReadError`, `UnsupportedInvoiceError` y `__version__`.
- Produces:
  - `type CurenergiaConfigEntry = ConfigEntry[CurenergiaCoordinator]`.
  - `@dataclass(frozen=True) class ContractData`: `contract: str`, `supply: SupplyType`, `rows: list[InvoiceRow]`, `device_name: str` (D6).
    - Propiedad `latest: InvoiceRow | None`: la de mayor `period_end`.
  - `@dataclass(frozen=True) class CoordinatorData`: `contracts: dict[str, ContractData]`, `unreadable_emails: int`, `unsupported_emails: int`, `last_mail_check: datetime | None`, `mail_error: bool`.
  - `class CurenergiaCoordinator(DataUpdateCoordinator[CoordinatorData])`:
    - Constructor `(hass, entry)`, con `update_interval=timedelta(hours=options[CONF_SCAN_HOURS])`.
    - Atributo `store: InvoiceStore`.
    - Método `async def async_totals_provider(cups: str) -> TotalsProvider | None`, que también usan los diagnósticos.
  - `_async_update_data`:
    1. Si la carpeta de las opciones no es la guardada en el `Store`, `store.reset_mail()`.
    2. Hace `MailClient.fetch` en el executor. Salta los UID de `seen` ∪ `unsupported` ∪ los de `failed` cuya versión es la actual.
    3. Por cada mensaje y PDF: `parse_invoice_pdf` en el executor, luego `build_stored` y `store.add`.
       - Un PDF fallido va a `failed`, con un aviso en el log que solo lleva el UID.
       - Un PDF no soportado va a `unsupported`.
       - Si `save_pdfs` está activo, el PDF de una factura nueva se guarda en `hass.config.path("curenergia", f"{number}.pdf")` en el executor.
    4. Marca como `seen` los UID que han terminado bien, también los de mensajes sin PDF. Guarda el `Store`.
    5. Agrupa por contrato y ejecuta `match_contract`.
       - Proveedor: el de `find_edata_id(cups, override)`, con `override = None` si la opción vale `EDATA_AUTO`. Si no hay e-data, un proveedor que siempre devuelve `None`.
       - Umbrales: los de las opciones, convertidos con `Decimal(str(valor))`.
       - Cada factura nueva con `unreadable` deja un aviso en el log, solo con el UID y los códigos de problema.
  - Errores:
    - `MailAuthError` → `ConfigEntryAuthFailed`.
    - `MailConnectionError` sin datos previos (primer refresco) → `UpdateFailed`. El setup lo convierte en `ConfigEntryNotReady`.
    - `MailConnectionError` con datos previos → D5: se recalcula la casación con lo guardado, `mail_error=True` y un aviso en el log.
  - `__init__.py`:
    - `async_setup_entry`: crea el coordinador, `await coordinator.store.async_load()`, `await coordinator.async_config_entry_first_refresh()`, asigna `entry.runtime_data` y carga las plataformas `[Platform.SENSOR, Platform.BUTTON]`.
    - `async_unload_entry`: descarga las plataformas.
    - `async_remove_entry`: borra el `Store`.
    - `async_setup` registra los comandos websocket (Tarea 9). Hasta entonces, nada.

- [ ] **Step 1: escribir los tests que fallan.**
  - `MailClient` se sustituye por un falso que devuelve `FetchResult` preparados.
  - `parse_invoice_pdf` se sustituye para que cada PDF falso devuelva una factura (`fixture_invoice` o `make_invoice`) o lance la excepción indicada.

```python
async def test_first_refresh_stores_invoices(hass): ...                 # 2 mensajes luz+gas → 2 contratos, store tiene 2 facturas, seen == {1, 2}
async def test_duplicate_invoice_kept_once(hass): ...                   # dos mensajes con el mismo número → 1 factura, la del primer UID
async def test_message_without_pdf_marked_seen(hass): ...
async def test_parse_error_recorded_and_retried_on_new_version(hass): ...  # failed[uid] == __version__; con otra versión → se reintenta
async def test_unsupported_not_retried(hass): ...
async def test_uidvalidity_change_reprocesses_without_duplicates(hass): ...
async def test_folder_change_resets_mail_state(hass): ...
async def test_auth_error_starts_reauth(hass): ...                      # entry.state SETUP_ERROR y flujo reauth en curso
async def test_connection_error_on_setup_not_ready(hass): ...           # ConfigEntryState.SETUP_RETRY
async def test_connection_error_later_keeps_data(hass): ...             # segundo refresco con MailConnectionError → last_update_success True, mail_error True, datos intactos
async def test_save_pdfs_option_writes_file(hass, tmp_path): ...
async def test_unload_and_remove_entry(hass, hass_storage): ...
```

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `scripts/ha-test.sh tests/test_coordinator.py tests/test_init.py -v`
Expected: FAIL.

- [ ] **Step 3: implementar `coordinator.py` y completar `__init__.py`**.

- [ ] **Step 4: ejecutar los tests y comprobar que pasan**

Run: `scripts/ha-test.sh tests/test_coordinator.py tests/test_init.py -v`
Expected: PASS.

- [ ] **Step 5: commit**: `feat(ha): poll mailbox, ingest invoices and match them in a coordinator`.

---

### Task 8: Sensores y botón

**Files:**
- Create: `custom_components/curenergia/entity.py`, `sensor.py`, `button.py`
- Modify: `strings.json`, `translations/en.json`, `translations/es.json` (sección `entity`)
- Test: `tests/test_sensor.py`, `tests/test_button.py`

**Interfaces:**
- Consumes: `CurenergiaCoordinator`, `ContractData`, `InvoiceRow`, `Status` (Tareas 4 y 7).
- Produces:
  - `CurenergiaContractEntity(CoordinatorEntity[CurenergiaCoordinator])`, en `entity.py`:
    - `_attr_has_entity_name = True`.
    - Recibe `contract: str` y `key: str`, y construye `unique_id` según D6.
    - `DeviceInfo(identifiers={(DOMAIN, f"{entry_id}_{contract}")}, name=device_name, manufacturer="CurEnergía", model=<tariff de la última factura>)`.
  - Sensores, uno por contrato, de la última factura (`ContractData.latest`). `translation_key` = clave:

    | Clave | Tipo |
    |---|---|
    | `total` | `MONETARY`, `EUR` |
    | `kwh` | `ENERGY`, `kWh` |
    | `price_kwh` | sin device_class, unidad `€/kWh`; valor `total / kwh` (`None` si `kwh == 0`) |
    | `issue_date`, `period_start`, `period_end` | `DATE` |
    | `status` | `ENUM`, con `options` = valores de `Status` |
    | `delta_kwh` (solo luz) | `ENERGY`, `kWh`, de `comparison.delta_kwh` |
    | `delta_eur` (solo luz) | `MONETARY`, `EUR`, de `comparison.delta_eur` |

    - **Ningún sensor tiene `state_class`.**
    - Los sensores de luz sin comparación tienen valor `None`.
  - Los contratos nuevos crean sus entidades sin recargar: un listener del coordinador compara con un conjunto de contratos conocidos.
  - `button.py`: `translation_key="check_now"` ("Buscar facturas ahora" / "Check for invoices now"). Va en el dispositivo de servicio de la entrada (D6, `entry_type=DeviceEntryType.SERVICE`), con `unique_id` `f"{entry_id}_check_now"`. `async_press` llama a `coordinator.async_request_refresh()`.
  - Textos del enum `status`:

    | Estado | en | es |
    |---|---|---|
    | `ok` | OK | Cuadra |
    | `no_cuadra` | Mismatch | No cuadra |
    | `estimada` | Estimated reading | Lectura estimada |
    | `sin_datos` | Not enough data | Sin datos suficientes |
    | `no_leida` | Could not be read | No se pudo leer |
    | `gas` | Gas (not matched) | Gas (sin casar) |

- [ ] **Step 1: escribir los tests que fallan.** Se monta la entrada con el coordinador de la Tarea 7 (con los falsos de mail y parser). El proveedor de e-data se sustituye por uno que devuelve `Totals` fijos.

```python
async def test_contract_sensors_created(hass, entity_registry): ...   # luz: 9 entidades; gas: 7; unique_id con entry_id y contrato
async def test_sensor_values_latest_invoice(hass): ...                # total, kwh, price_kwh == round(total/kwh, 4), period_end ISO, status "ok"
async def test_no_state_class(hass): ...                              # ningún estado tiene atributo state_class
async def test_new_contract_adds_entities(hass): ...                  # segundo refresco con un contrato nuevo → aparecen sus entidades
async def test_two_electricity_contracts_named_by_suffix(hass, device_registry): ...
async def test_button_requests_refresh(hass): ...
```

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `scripts/ha-test.sh tests/test_sensor.py tests/test_button.py -v`
Expected: FAIL.

- [ ] **Step 3: implementar las plataformas y los textos**.

- [ ] **Step 4: ejecutar los tests y comprobar que pasan**

Run: `scripts/ha-test.sh tests/test_sensor.py tests/test_button.py tests/test_config_flow.py::test_strings_match_english_translation -v`
Expected: PASS.

- [ ] **Step 5: commit**: `feat(ha): add latest-invoice sensors and check-now button`.

---

### Task 9: API websocket y diagnósticos

**Files:**
- Create: `custom_components/curenergia/websocket.py`, `custom_components/curenergia/diagnostics.py`
- Modify: `custom_components/curenergia/__init__.py` (`async_setup` llama a `async_register_websocket(hass)`)
- Test: `tests/test_websocket.py`, `tests/test_diagnostics.py`

**Interfaces:**
- Consumes: `CoordinatorData`, `InvoiceRow`, `Comparison` (Tareas 4 y 7), y `async_totals_provider` y `invoice_window` para los diagnósticos.
- Produces: contrato que consume el plan 3. Las claves son exactamente estas:
  - **`curenergia/invoices`**:
    - Petición: `{"entry_id"?: str, "supply"?: "electricity" | "gas"}`. Sin `entry_id`, se usan todas las entradas cargadas.
    - Respuesta: `{"contracts": [{"entry_id", "contract", "supply", "name", "invoices": [Row…]}]}`. Las facturas van ordenadas de la más reciente a la más antigua.
    - Cada `Row`:

      ```
      number, supply, issue_date, period_start, period_end (ISO),
      estimated: bool, status: str, problems: [str],
      total, kwh, price_kwh, m3 | null, energy_price_kwh | null,
      periods: {"p1","p2","p3"} | null,
      concepts: [{"key","label","amount"}],
      vat: {"rate","base","amount"},
      in_group_of: str | null,
      comparison: null | {
        "group": [str], "window_start", "window_end" (ISO con zona),
        "invoice_kwh", "invoice_periods": {"p1","p2","p3"}, "invoice_eur",
        "edata_kwh", "edata_periods": {"p1","p2","p3"}, "edata_eur" | null,
        "delta_kwh", "delta_periods": {"p1","p2","p3"}, "delta_eur" | null, "delta_pct" | null
      }
      ```

    - Cualquier valor de tramo puede ser `null`.
  - **`curenergia/summary`**:
    - Petición: `{"entry_id"?: str}`.
    - Respuesta: `{"billed_12m", "kwh_delta_pct" | null, "estimated_count", "unreadable_emails", "unsupported_emails", "last_mail_check" | null, "mail_error"}`.
    - `billed_12m` es la suma de `total` de las facturas (luz y gas) con `issue_date` en los últimos 365 días.
    - `kwh_delta_pct` = (Σ `invoice_kwh` − Σ `edata_kwh`) / Σ `edata_kwh` × 100, sobre las comparaciones de facturas reales con estado `ok` o `no_cuadra` en ese plazo.
    - `estimated_count` cuenta las estimadas en ese plazo.
  - Un `entry_id` desconocido o no cargado devuelve el error `not_found`.
  - `async_get_config_entry_diagnostics(hass, entry) -> dict`:
    - Contiene las opciones, `data` redactado, `pycurenergia` versión, `mail` (uidvalidity, número de seen/failed/unsupported) y por factura (identificada por índice) `supply`, `period_start`, `period_end`, `estimated`, `status`, `problems`.
    - Para cada factura de luz real, añade `boundary_deltas`: `{"base", "start-1d", "start+1d", "end-1d", "end+1d"}`, con el Δ kWh de cada ventana desplazada (`None` si el proveedor no la cubre). Es lo que pide §9.3.
    - Todo pasa por `async_redact_data` con `TO_REDACT = {"username", "password", "cups", "contract", "number"}`.

- [ ] **Step 1: escribir los tests que fallan**

```python
async def test_ws_invoices_shape(hass, hass_ws_client): ...      # claves exactas de Row y comparison; orden por period_start desc; supply filtra
async def test_ws_invoices_unknown_entry(hass, hass_ws_client): ...  # error code "not_found"
async def test_ws_summary(hass, hass_ws_client, freezer): ...     # valores calculados a mano con facturas inventadas
async def test_diagnostics_redacted(hass, hass_client): ...       # usa get_diagnostics_for_config_entry; ni la contraseña, ni el usuario,
    # ni el CUPS, ni el contrato, ni el número de la fixture aparecen en json.dumps(result); boundary_deltas tiene las 5 claves
```

- [ ] **Step 2: ejecutar los tests y comprobar que fallan**

Run: `scripts/ha-test.sh tests/test_websocket.py tests/test_diagnostics.py -v`
Expected: FAIL.

- [ ] **Step 3: implementar `websocket.py` y `diagnostics.py`**. En `websocket.py`, con `@websocket_api.websocket_command`, `@websocket_api.async_response` y `websocket_api.async_register_command`.

- [ ] **Step 4: ejecutar los tests y comprobar que pasan**

Run: `scripts/ha-test.sh tests/test_websocket.py tests/test_diagnostics.py -v`
Expected: PASS.

- [ ] **Step 5: commit**: `feat(ha): expose invoices over websocket and add redacted diagnostics`.

---

### Task 10: Calidad Bronze, README, CI y spec

**Files:**
- Create: `custom_components/curenergia/quality_scale.yaml`, `README.md` (raíz), `.github/workflows/integration.yml`
- Modify: `.github/dependabot.yml`, `docs/superpowers/specs/2026-10-29-curenergia-facturas-design.md`

**Interfaces:**
- Consumes: todo lo anterior.
- Produces:
  - `quality_scale.yaml`. Todas las reglas Bronze se marcan `done`, salvo estas:
    - `action-setup: exempt` y `docs-actions: exempt`, con el motivo "no service actions; a button entity is used".
    - `brands: todo`, con el comentario "local brand/ folder added in plan 3".
    - Las reglas Bronze son: `action-setup`, `appropriate-polling`, `brands`, `common-modules`, `config-flow-test-coverage`, `config-flow`, `dependency-transparency`, `docs-actions`, `docs-high-level-description`, `docs-installation-instructions`, `docs-removal-instructions`, `entity-event-setup`, `entity-unique-id`, `has-entity-name`, `runtime-data`, `test-before-configure`, `test-before-setup`, `unique-config-entry`.
    - `reauthentication-flow: done` y `diagnostics: done`.
  - `README.md` en español con resumen en inglés, que cubre:
    - Qué hace, y que no es un proyecto oficial.
    - Instalación por HACS como repositorio personalizado. Requiere que el repo sea público.
    - Preparación del correo según §7.4: filtro + etiqueta, alternativa del buzón dedicado, aviso de que la contraseña de aplicación da acceso a todo el buzón, y nota sobre Google Workspace.
    - Configuración y opciones.
    - Qué significa cada estado.
    - Cómo se comparan los € (D2) y el requisito de tener la facturación activada en e-data.
    - Privacidad, y desinstalación (eliminar la entrada y luego quitarla en HACS).
  - `integration.yml`:
    - Se dispara con `push` y `pull_request` en las rutas `custom_components/**`, `tests/**`, `pyproject.toml`, `uv.lock`, `hacs.json` y el propio workflow.
    - `permissions: contents: read` y `persist-credentials: false`.
    - Las acciones van fijadas a SHA con un comentario de versión: los mismos SHA de `lib.yml` para checkout y setup-uv; para hassfest y HACS, el SHA se resuelve con `gh api repos/<owner>/<repo>/commits/<ref> --jq .sha`.
    - Tres jobs:
      - `hassfest`: `home-assistant/actions/hassfest`.
      - `hacs`: `hacs/action` con `category: integration` y `ignore: brands`.
      - `tests`: Python 3.14, `uv run --locked --group ha ruff check custom_components tests`, y luego `uv run --locked --group ha pytest --cov=custom_components.curenergia --cov-report=term-missing`, más la comprobación del 100 % de `config_flow` de la Tarea 6.
  - `dependabot.yml`: añade el ecosistema `uv` en `/`.
  - Spec:
    - Añade en §8.2 `energy_price_kwh` y `InvoiceReadError`.
    - En §9.2 y §9.4, sustituye los "(builder)" por lo verificado en "Hechos verificados" y D2.
    - En §9.3, añade D3.

- [ ] **Step 1: escribir `quality_scale.yaml`, `README.md`, `integration.yml` y los cambios de dependabot y del spec**.

- [ ] **Step 2: pasar ruff y toda la batería de tests**

Run: `scripts/ha-test.sh --ruff && scripts/ha-test.sh --cov=custom_components.curenergia --cov-report=term-missing`
Expected: ruff limpio. Todos los tests en verde. Cobertura total ≥ 95 % y `config_flow.py` al 100 %.

- [ ] **Step 3: validar el YAML del workflow**

Run: `uv run --with pyyaml python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/integration.yml'))"`
Expected: sin errores.

- [ ] **Step 4: comprobar que no hay datos personales**

Run, después de `git add`, sobre todo lo que añade el plan (desde el primer commit de la Tarea 1):

```
git diff --cached <base> -U0 | uv run --directory lib python -c "import sys,tomllib; s=sys.stdin.read(); keys=tomllib.load(open('../private/secrets.toml','rb')).get('replace',{}); print(sum(k in s for k in keys))"
```

Expected: `0`. El comando solo imprime cuántos valores reales aparecen, nunca cuáles.

- [ ] **Step 5: commit**: `ci: add hassfest, HACS and integration test workflow; docs: README and quality scale`.

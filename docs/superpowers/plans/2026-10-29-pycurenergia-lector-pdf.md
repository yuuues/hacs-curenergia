# pycurenergia (lector de facturas PDF) — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Plan 1 de 3.** El diseño cubre tres subsistemas independientes. Este plan construye la **librería** del lector de PDF. El **plan 2**, de la integración (IMAP, almacenamiento, casación con e-data, entidades y config flow), y el **plan 3**, de la tarjeta y el panel, se escriben cuando este esté terminado. Así parten de la interfaz real de la librería.

**Goal:** librería Python `pycurenergia`, publicable en PyPI, que convierte un PDF de factura de CurEnergía (luz o gas) en un `Invoice` tipado y comprueba su coherencia interna.

**Architecture:** dos capas separadas. Primero, PDF → texto (`pypdf`). Después, texto → `Invoice`, con un parser por tipo de suministro. Las pruebas de la segunda capa usan fixtures de texto **anonimizadas**, generadas por un script a partir de los PDF reales del usuario, que viven en `private/` y nunca se suben. Las comprobaciones de coherencia devuelven códigos de problema y no lanzan excepciones: así la integración puede guardar la factura con estado `no_leida`.

**Tech Stack:** Python ≥ 3.13, `pypdf`, `uv` (entorno y build), `pytest`, `ruff`, `reportlab` (solo en tests, para generar un PDF sintético), GitHub Actions y PyPI trusted publishing.

**Spec:** `docs/superpowers/specs/2026-10-29-curenergia-facturas-design.md` (§8, §14 y §15 son las secciones relevantes).

## Global Constraints

- Paquete `pycurenergia` en `lib/`, layout `lib/src/pycurenergia/`. Versión inicial `0.1.0`, licencia MIT, `requires-python = ">=3.13"`. Única dependencia de runtime: `pypdf>=5.0`.
- Todos los importes, kWh, m³ y porcentajes son `decimal.Decimal`, nunca `float`.
- Formato de números español: `1.234,56`, con signo negativo opcional `-12,34`. Fechas: `dd/mm/aaaa` y en texto (`5 de agosto de 2026`).
- Tolerancia de las comprobaciones de coherencia: **0,01 €** y **0,01 kWh**.
- **Nunca** se suben al repo PDF reales, texto real ni datos personales: nombre, NIF, dirección, CUPS reales, números de contrato reales, nº de contador, referencia del contrato de acceso o números de factura reales. Esto aplica también a nombres de fichero y a mensajes de commit. Los PDF de `private/` se guardan con nombres neutros.
- Los textos de anclaje que buscan los parsers son los de la tabla §8.1 del spec, tal como salen de `pypdf` en las fixtures.
- Ejecutar todo con `uv run --directory lib …` desde la raíz del repo.

## Review Focus

1. **Periodo partido en dos líneas** (`… 28 de septiembre de\n2026`): ocurre en la factura real de luz y debe parsearse bien. → test en la Tarea 4.
2. **Concepto nuevo en el resumen** que el parser no conoce: se parsea como `ConceptKey.OTHER` con su etiqueta y la suma sigue cuadrando, sin fallar. → test en la Tarea 4.
3. **Factura de luz con lectura estimada** (`Lectura actual (estimada)`): `estimated=True`. → test en la Tarea 4.
4. **Falta un campo obligatorio** (por ejemplo, la línea del nº de factura): `InvoiceParseError` que nombra el campo, no un `AttributeError` ni un valor vacío. → tests en las Tareas 4 y 5.
5. **Adjunto que no es una factura reconocible**, o abono con importes negativos: `UnsupportedInvoiceError` para texto desconocido, y `parse_decimal("-12,34") == Decimal("-12.34")`. → tests en las Tareas 1 y 6.

---

### Task 1: Esqueleto de la librería, números/fechas y CI

**Files:**
- Create: `LICENSE` (MIT, titular: "yuuues"), `lib/pyproject.toml`, `lib/README.md`, `lib/src/pycurenergia/__init__.py`, `lib/src/pycurenergia/py.typed`, `lib/src/pycurenergia/numbers.py`
- Create: `.github/workflows/lib.yml`
- Test: `lib/tests/test_numbers.py`

**Interfaces:**
- Produces:
  - `parse_decimal(text: str) -> Decimal`
  - `parse_spanish_date(text: str) -> date`, que acepta `"6 de octubre de 2026"` con cualquier espacio en blanco, saltos de línea incluidos, entre palabras.
  - `parse_dmy(text: str) -> date`
  - Las dos funciones de fecha lanzan `ValueError` si la entrada no es válida.

- [ ] **Step 1: Crear `lib/pyproject.toml`**: build backend `hatchling`, `name = "pycurenergia"`, `version = "0.1.0"`, `dependencies = ["pypdf>=5.0"]`, `[dependency-groups] dev = ["pytest>=8", "ruff>=0.6", "reportlab>=4"]`, `[tool.ruff]` con `target-version = "py313"` y `select = ["E","F","I","UP","B"]`. Añadir también `LICENSE`, el `README.md` mínimo (qué es, aviso de proyecto no oficial) y `py.typed` vacío.

- [ ] **Step 2: Escribir el test que falla**

```python
from datetime import date
from decimal import Decimal
import pytest
from pycurenergia.numbers import parse_decimal, parse_spanish_date, parse_dmy

@pytest.mark.parametrize("text,expected", [
    ("102,55", Decimal("102.55")), ("4.156,35", Decimal("4156.35")),
    ("0,000077", Decimal("0.000077")), ("-12,34", Decimal("-12.34")),
    ("4,6", Decimal("4.6")), ("2.444", Decimal("2444")),
])
def test_parse_decimal(text, expected):
    assert parse_decimal(text) == expected

def test_parse_spanish_date_handles_line_break():
    assert parse_spanish_date("28 de septiembre de\n2026") == date(2026, 9, 28)
    assert parse_spanish_date("1 de mayo de 2027") == date(2027, 5, 1)

def test_parse_dmy():
    assert parse_dmy("07/09/2026") == date(2026, 9, 7)

def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        parse_spanish_date("30 de febrerillo de 2026")
    with pytest.raises(ValueError):
        parse_decimal("abc")
```

Nota: `"2.444"` sin coma decimal son miles (son los m³ del gas, §8.1).

- [ ] **Step 3: Ejecutar y comprobar que falla**: `uv run --directory lib pytest tests/test_numbers.py -v`. Esperado: FAIL (`ModuleNotFoundError: pycurenergia.numbers`).

- [ ] **Step 4: Implementar `numbers.py`.** Meses en español: enero … diciembre, incluido "setiembre" como alias de septiembre.

- [ ] **Step 5: Ejecutar y comprobar que pasa**: el mismo comando. Esperado: PASS. Después, `uv run --directory lib ruff check .` sin errores.

- [ ] **Step 6: Crear `.github/workflows/lib.yml`**: se dispara en `push`/`pull_request` con `paths: ["lib/**", ".github/workflows/lib.yml"]`. Matriz Python `3.13` y `3.14`. Usa `astral-sh/setup-uv`, y ejecuta `uv run --directory lib ruff check .` y `uv run --directory lib pytest -v`.

- [ ] **Step 7: Commit**: `git add LICENSE lib .github/workflows/lib.yml` y `git commit -m "feat(lib): scaffold pycurenergia with Spanish number/date parsing"`.

---

### Task 2: Modelo `Invoice` y comprobaciones de coherencia

**Files:**
- Create: `lib/src/pycurenergia/models.py`, `lib/src/pycurenergia/validation.py`, `lib/src/pycurenergia/errors.py`
- Test: `lib/tests/test_validation.py`

**Interfaces:**
- Produces (`models.py`):
  - `class SupplyType(StrEnum)`: `ELECTRICITY = "electricity"`, `GAS = "gas"`
  - `class ConceptKey(StrEnum)`: `POWER`, `ENERGY`, `SOCIAL_BONUS`, `ELECTRICITY_TAX`, `METER_RENTAL`, `GAS_FIXED_TERM`, `GAS_ENERGY`, `GAS_TAX`, `OTHER`. Valores en minúsculas: `"power"`, `"energy"`, …
  - `@dataclass(frozen=True, slots=True) class Concept`: `key: ConceptKey`, `label: str`, `amount: Decimal`
  - `@dataclass(frozen=True, slots=True) class Invoice`. Campos: `supply: SupplyType`, `number: str`, `contract: str`, `cups: str` (sin espacios), `issue_date: date`, `period_start: date`, `period_end: date`, `estimated: bool`, `total: Decimal`, `concepts: tuple[Concept, ...]` (sin el IVA), `vat_rate: Decimal` (21 para "21 %"), `vat_base: Decimal`, `vat_amount: Decimal`, `kwh: Decimal`, `tariff: str`, `access_tariff: str`. Campos opcionales: `kwh_p1: Decimal | None = None`, `kwh_p2 = None`, `kwh_p3 = None`, `m3: Decimal | None = None`, `contracted_power_kw: tuple[Decimal, ...] = ()`, `late_interest: Decimal = Decimal(0)`. Método: `def concept_total(self, *keys: ConceptKey) -> Decimal`, que suma los conceptos con esas claves.
- Produces (`validation.py`):
  - `class Problem(StrEnum)`: `TOTAL_MISMATCH = "total_mismatch"`, `VAT_MISMATCH = "vat_mismatch"`, `KWH_PERIODS_MISMATCH = "kwh_periods_mismatch"`, `PERIOD_INVERTED = "period_inverted"`
  - `check_consistency(invoice: Invoice) -> list[Problem]`. Lista vacía = coherente.
- Produces (`errors.py`):
  - `class InvoiceParseError(Exception)`, con atributo `field: str`
  - `class UnsupportedInvoiceError(Exception)`

Reglas de `check_consistency`: (a) `sum(concepts) + vat_amount == total`; (b) `vat_rate/100 × vat_base == vat_amount`; (c) si `kwh_p1/p2/p3` no son `None`, `p1 + p2 + p3 == kwh`; (d) `period_start <= period_end`. (a), (b) y (c) con las tolerancias de Global Constraints.

- [ ] **Step 1: Escribir los tests que fallan.** Usar un helper `make_invoice(**overrides)` con los valores de la factura de luz anonimizada (los mismos que se esperan en la Tarea 4):
  - `total=Decimal("102.55")`
  - conceptos: `POWER 11.94`, `ENERGY 67.07`, `SOCIAL_BONUS 0.74`, `ELECTRICITY_TAX 4.08`, `OTHER "Otros" 0.15`, `METER_RENTAL 0.80`
  - `vat_rate=21`, `vat_base=84.63`, `vat_amount=17.77`
  - `kwh=380.06`, `kwh_p1=107.11`, `kwh_p2=104.16`, `kwh_p3=168.79`
  - `period_start=2026-08-29`, `period_end=2026-09-28`

  Tests:
  - `test_consistent_invoice_has_no_problems`: `== []`
  - `test_total_mismatch`: con `total=102.60`, devuelve `[Problem.TOTAL_MISMATCH]`
  - `test_rounding_within_tolerance`: con `total=102.56`, devuelve `[]`
  - `test_vat_mismatch`: con `vat_amount=18.00` y `total=102.78`, devuelve `[Problem.VAT_MISMATCH]`
  - `test_kwh_periods_mismatch`: con `kwh_p3=160`, devuelve `[Problem.KWH_PERIODS_MISMATCH]`
  - `test_gas_without_periods_skips_kwh_rule`: con `kwh_p1=kwh_p2=kwh_p3=None`, devuelve `[]`
  - `test_period_inverted`
  - `test_concept_total`: `inv.concept_total(ConceptKey.POWER, ConceptKey.ENERGY) == Decimal("79.01")`

- [ ] **Step 2: Ejecutar y comprobar que fallan**: `uv run --directory lib pytest tests/test_validation.py -v`. Esperado: FAIL (import error).

- [ ] **Step 3: Implementar `models.py`, `errors.py` y `validation.py`** con las firmas de arriba.

- [ ] **Step 4: Ejecutar y comprobar que pasan**: el mismo comando. Esperado: PASS.

- [ ] **Step 5: Commit**: `git commit -m "feat(lib): add Invoice model and consistency checks"`.

---

### Task 3: Extracción de texto, anonimizador y fixtures

**Files:**
- Create: `lib/src/pycurenergia/text.py`, `lib/scripts/anonymize.py`, `lib/tests/conftest.py`
- Create (generadas, sí se suben): `lib/tests/fixtures/electricity_2026-10.txt`, `lib/tests/fixtures/gas_2026-09.txt`
- Create (locales, **no** se suben, `private/` está en `.gitignore`): `private/invoices/electricity_2026-10.pdf`, `private/invoices/gas_2026-09.pdf`, `private/secrets.toml`
- Test: `lib/tests/test_text.py`, `lib/tests/test_anonymize.py`

**Interfaces:**
- Produces (`text.py`): `extract_text(pdf: bytes) -> str`. Concatena `page.extract_text() or ""` de cada página separadas por `"\f"`.
- Produces (`anonymize.py`, no se empaqueta):
  - `drop_noise_lines(text: str) -> str`
  - `apply_replacements(text: str, mapping: dict[str, str]) -> str`
  - `find_leaks(text: str, mapping: dict[str, str]) -> list[tuple[int, str]]`, que devuelve (nº de línea, valor real filtrado).
  - CLI: `anonymize.py PDF --out TXT` y `anonymize.py --check TXT...`.
- Produces (`conftest.py`): añade `lib/scripts` a `sys.path`; fixture de pytest `fixture_text` que devuelve una función `(name: str) -> str`, que lee `lib/tests/fixtures/<name>.txt` en UTF-8.

Comportamiento del anonimizador, en este orden:
1. `drop_noise_lines` elimina tres tipos de línea. Los códigos de barras llevan el contrato dentro, a veces codificado con una fuente de código de barras:
   - (a) líneas con una secuencia de ≥ 20 dígitos seguidos;
   - (b) líneas en las que más de la mitad de los caracteres no blancos quedan fuera de este conjunto: letras ASCII, dígitos, `áéíóúüñÁÉÍÓÚÜÑçÇªº` y la puntuación `.,:;()/%€-'"*+&!?¿¡`. Es el caso de `ÕÆ»£¢«…Ö` (fuente Code128) y de `Ļüá×ìļ`;
   - (c) líneas sin ninguna secuencia de ≥ 4 letras que contienen un tabulador o alguno de `[]{}<>@_=^~|\`, como `kh\t1e) MXH\tH>,m`.
   Además, `secrets.toml` puede llevar `[drop] patterns = ["regex", …]` con patrones extra que elimina líneas completas.
2. `apply_replacements` aplica `private/secrets.toml` (`[replace]` con `"valor real" = "valor falso"`), de la clave más larga a la más corta. Si no se pasa `--secrets`, la ruta se calcula desde la ubicación del script: `Path(__file__).parents[2] / "private" / "secrets.toml"`.
3. Sustituye cualquier `\b\d{8}[A-Z]\b` (NIF) por `00000000T`.
4. `find_leaks` busca cada valor real, también con los espacios quitados, y cualquier NIF distinto de `00000000T`. Si encuentra algo, el CLI sale con código 1, lista las líneas y **no escribe** el fichero.

- [ ] **Step 1: Copiar los PDF.** Los dos PDF que el usuario dejó en su carpeta `Downloads` (formato `<contrato>_<fecha>.pdf`) se copian a `private/invoices/electricity_2026-10.pdf` y `private/invoices/gas_2026-09.pdf`. Comprobar con `git status --short` que no aparece nada de `private/`.

- [ ] **Step 2: Escribir los tests que fallan.**
  - `test_text.py::test_extract_text_joins_pages_with_formfeed`: genera con `reportlab`, en memoria, un PDF de 2 páginas ("Página uno" / "Página dos"). Comprueba que `extract_text(data).split("\f")` tiene longitud 2 y que cada parte contiene su texto.
  - `test_anonymize.py`:
    - `test_drops_barcode_and_glyph_lines`: la entrada `"A\n9050712345678901234567890123456789012345678901\nƼžƚƚƚžƼĽƁƂƃƄƅ\nÕÆ»£¢«ÀÊ¿©¨³Ö\nĻüá×ìļ\nkh\t1e) MXH\tH>,m\nk[4Q98@_SP.]=]Ll\nB"` da `"A\nB"`.
    - `test_keeps_normal_lines`: `"Página   1 / 4"`, `"83100021"`, `"IVA 21 % s/84,63 € 17,77 €"` y `"inscripción 1ª - CIF A-95554630"` se conservan sin cambios.
    - `test_replacements_longest_first`: `{"ES 0031 1": "X", "ES 0031": "Y"}` sobre `"ES 0031 1 y ES 0031"` da `"X y Y"`.
    - `test_nif_masked`: `"NIF:  12345678Z"` da `"NIF:  00000000T"`.
    - `test_find_leaks_detects_value_without_spaces`: con el mapping `{"ES 0031 9999": "F"}`, el texto `"línea\nES00319999"` da `[(2, "ES 0031 9999")]`.

- [ ] **Step 3: Ejecutar y comprobar que fallan**: `uv run --directory lib pytest tests/test_text.py tests/test_anonymize.py -v`. Esperado: FAIL.

- [ ] **Step 4: Implementar `text.py`, `anonymize.py` y `conftest.py`.**

- [ ] **Step 5: Ejecutar y comprobar que pasan**: el mismo comando. Esperado: PASS.

- [ ] **Step 6: Crear `private/secrets.toml`** leyendo el texto extraído de los dos PDF. Los valores reales solo se escriben en este fichero local. Los falsos están fijados aquí porque los tests los comprueban:

| Dato real | Valor falso |
|---|---|
| Nº de contrato de luz | `100000001` |
| Nº de contrato de gas | `1000000002` |
| CUPS de luz (con espacios, tal como sale) | `ES 0031 0000 0000 0001 AA` |
| CUPS de gas | `ES 0217 0000 0000 0002 BB` |
| Nº de factura de luz | `09261006010000001` |
| Nº de factura de gas | `09260911010000002` |
| Nº de factura de la 1ª fila de la tabla de intereses | `09260806010000003` |
| Nº de factura de la 2ª fila | `09260903010000004` |
| Nombre del titular | `NOMBRE APELLIDO1 APELLIDO2` |
| Calle de la dirección de suministro | `C/ FALSA, 1, 1 1` |
| Código postal y población | `08000 CIUDAD (PROVINCIA)` |
| Nº de contador de luz / de gas | `300000001` / `700000002` |
| Referencia del contrato de acceso | `500000000001` |
| Direcciones de los "Puntos de atención cercanos" | `CL OFICINA 1 08000 CIUDAD` / `PZ OFICINA 2 08000 CIUDAD` |

La dirección de gas sale partida en dos líneas, así que la calle y la población se reemplazan por separado.

- [ ] **Step 7: Generar las fixtures**:
  - `uv run --directory lib python scripts/anonymize.py ../private/invoices/electricity_2026-10.pdf --out tests/fixtures/electricity_2026-10.txt`
  - lo mismo con el gas, a `gas_2026-09.txt`.

  Esperado: código 0 en los dos. **Revisar a mano** las dos fixtures en busca de cualquier dato personal que quede y, si aparece, añadirlo a `secrets.toml` y regenerar. Después ejecutar `--check` sobre las dos. Esperado: código 0.

- [ ] **Step 8: Commit** (solo código y fixtures anonimizadas): `git add lib/src/pycurenergia/text.py lib/scripts lib/tests` y `git commit -m "feat(lib): add PDF text extraction, anonymizer and anonymized fixtures"`. Antes de hacer commit, `git status --short` no debe mostrar nada de `private/`.

---

### Task 4: Parser de luz

**Files:**
- Create: `lib/src/pycurenergia/electricity.py`
- Test: `lib/tests/test_electricity.py`

**Interfaces:**
- Consumes: `numbers.*` (Tarea 1); `Invoice`, `Concept`, `ConceptKey`, `SupplyType`, `InvoiceParseError` (Tarea 2); `fixture_text` (Tarea 3).
- Produces: `parse_electricity(text: str) -> Invoice`.

Anclajes (§8.1 del spec):
- **Nº de factura y emisión:** `Nº Factura: <n> emitida el <fecha en texto>`. Es el único anclaje; no se usa como alternativa el pie de página `Número de factura`.
- **Contrato:** `Referencia del contrato de suministro (…): <n>`.
- **Periodo:** `Periodo de consumo: <fecha> a <fecha>`, que puede cruzar un salto de línea.
- **kWh:** `Su consumo en el periodo facturado ha sido: <n> kWh` y `Consumo en P1|P2|P3: <n> kWh`.
- **Resumen:** las líneas `<etiqueta> <importe> €` que van desde `Por potencia contratada` hasta `TOTAL IMPORTE FACTURA:`, sin la línea de IVA. Se mapean así: `Por potencia contratada`→`POWER`, `Por energía consumida`→`ENERGY`, `Por financiación del bono social`→`SOCIAL_BONUS`, `Impuesto electricidad`→`ELECTRICITY_TAX`, `Alquiler del contador`→`METER_RENTAL`. Cualquier otra etiqueta → `OTHER`, conservando la etiqueta.
- **IVA:** la primera línea `IVA <tipo> % s/<base> € <importe> €`. **Total:** `TOTAL IMPORTE FACTURA:`.
- **Intereses de demora:** `late_interest` sale de `Intereses de demora (*) <importe> €`; vale 0 si no aparece.
- **Estimada:** `estimated` sale de `Lectura actual (real|estimada)`.
- **Potencia contratada:** `contracted_power_kw` = (punta, valle), de `Potencia contratada periodo punta|valle:`.
- **Tarifas:** `tariff` es la primera palabra tras `TIPO DE CONTRATO:` (`"PVPC"`). `access_tariff` es el valor de `Peajes de transporte y distribución : `.
- **CUPS:** se guarda con los espacios quitados.

Si falta un campo obligatorio se lanza `InvoiceParseError(field=...)`. Son obligatorios: `number`, `issue_date`, `period`, `total`, `kwh`, `contract`, `cups` e IVA.

- [ ] **Step 1: Escribir los tests que fallan.**
  - `test_parses_anonymized_invoice`, con `inv = parse_electricity(fixture_text("electricity_2026-10"))`:
    - `inv.supply is SupplyType.ELECTRICITY`, `inv.number == "09261006010000001"`, `inv.contract == "100000001"`, `inv.cups == "ES0031000000000001AA"`
    - `inv.issue_date == date(2026, 10, 6)`; `(inv.period_start, inv.period_end) == (date(2026, 8, 29), date(2026, 9, 28))`. El fin del periodo está partido en dos líneas en la fixture (Review Focus 1).
    - `inv.estimated is False`; `inv.total == Decimal("102.55")`
    - `inv.kwh == Decimal("380.06")`; `(inv.kwh_p1, inv.kwh_p2, inv.kwh_p3) == (Decimal("107.11"), Decimal("104.16"), Decimal("168.79"))`
    - `(inv.vat_rate, inv.vat_base, inv.vat_amount) == (Decimal("21"), Decimal("84.63"), Decimal("17.77"))`
    - `inv.tariff == "PVPC"`; `inv.access_tariff == "2.0TD"`; `inv.contracted_power_kw == (Decimal("4.6"), Decimal("4.6"))`; `inv.late_interest == Decimal("0.15")`
    - `[(c.key, c.amount) for c in inv.concepts] == [(POWER, 11.94), (ENERGY, 67.07), (SOCIAL_BONUS, 0.74), (ELECTRICITY_TAX, 4.08), (OTHER, 0.15), (METER_RENTAL, 0.80)]` (los importes como `Decimal`); y la etiqueta de `OTHER` es `"Otros"`.
    - `check_consistency(inv) == []`
  - `test_unknown_concept_becomes_other` (Review Focus 2): modificar la fixture con `text.replace("Alquiler del contador 0,80 €", "Concepto nuevo 1,00 €\nAlquiler del contador 0,80 €", 1).replace("102,55", "103,55")`. Esperado: hay un `Concept(OTHER, "Concepto nuevo", Decimal("1.00"))` y `check_consistency` devuelve `[]`.
  - `test_estimated_reading` (Review Focus 3): `text.replace("Lectura actual (real)", "Lectura actual (estimada)")` da `estimated is True`.
  - `test_missing_number_raises` (Review Focus 4): quitar la línea `Nº Factura:` da `InvoiceParseError` con `.field == "number"`.

- [ ] **Step 2: Ejecutar y comprobar que fallan**: `uv run --directory lib pytest tests/test_electricity.py -v`. Esperado: FAIL.

- [ ] **Step 3: Implementar `parse_electricity`** con expresiones regulares sobre el texto completo. Las que cruzan saltos de línea usan `\s+`.

- [ ] **Step 4: Ejecutar y comprobar que pasan**: el mismo comando. Esperado: PASS.

- [ ] **Step 5: Commit**: `git commit -m "feat(lib): parse CurEnergía electricity invoices"`.

---

### Task 5: Parser de gas

**Files:**
- Create: `lib/src/pycurenergia/gas.py`
- Test: `lib/tests/test_gas.py`

**Interfaces:**
- Consumes: los mismos módulos que la Tarea 4.
- Produces: `parse_gas(text: str) -> Invoice`.

Anclajes:
- **Conceptos:** las líneas con importe `… <importe> €` que van desde la línea `ENERGÍA` (sola) hasta `IMPORTE TOTAL`, sin contar las que empiezan por `TOTAL ` ni las cabeceras sin importe. Se mapean así: `Término fijo`→`GAS_FIXED_TERM`, `Energía facturada`→`GAS_ENERGY`, `Impuesto sobre gas natural`→`GAS_TAX`, `Alquiler equipos de medida`→`METER_RENTAL`. Cualquier otra → `OTHER`.
- **Líneas que no son conceptos:** `Cargo aplicado` y `Tasa CNMC` aparecen después de `TOTAL IMPORTE FACTURA`, son informativas y no se tratan como conceptos.
- **Periodo:** `Periodo de facturación dd/mm/aaaa - dd/mm/aaaa`. **Emisión:** `Fecha de emisión de factura <fecha en texto>`. **Nº de factura:** `Número de factura`. **Contrato:** `Número de contrato`. **CUPS:** `(CUPS): `.
- **Estimada:** `estimated` es verdadero si aparece `Factura con lectura estimada` o si la línea `Lectura actual:` dice `estimada`.
- **kWh y m³:** `kwh` sale de `Consumo kWh: (real|estimada) <n> kWh`; `m3` de `Consumo en m3: (real|estimada) <n> m3`.
- **Tarifas:** `tariff` sale de `Tarifa de suministro:` (`"TUR.1"`) y `access_tariff` de `TARIFA PEAJE <x>` (`"RL.1"`).
- **IVA:** `IVA <tipo> % s/<base> € <importe> €`. **Total:** `TOTAL IMPORTE FACTURA`.

- [ ] **Step 1: Escribir los tests que fallan.**
  - `test_parses_anonymized_invoice`, con `parse_gas(fixture_text("gas_2026-09"))`:
    - `supply is SupplyType.GAS`, `number == "09260911010000002"`, `contract == "1000000002"`, `cups == "ES0217000000000002BB"`
    - `issue_date == date(2026, 9, 11)`, periodo `(date(2026, 7, 7), date(2026, 9, 7))`
    - `estimated is True`, `total == Decimal("19.20")`, `kwh == Decimal("150.32")`, `m3 == Decimal("13")`
    - IVA `(21, 15.87, 3.33)`; `tariff == "TUR.1"`, `access_tariff == "RL.1"`; `kwh_p1 is None`
    - conceptos `[(GAS_FIXED_TERM, 7.90), (GAS_ENERGY, 6.51), (GAS_TAX, 0.30), (METER_RENTAL, 1.16)]`
    - `check_consistency(inv) == []`
  - `test_missing_period_raises`: quitar la línea `Periodo de facturación` da `InvoiceParseError` con `.field == "period"`.

- [ ] **Step 2: Ejecutar y comprobar que fallan**: `uv run --directory lib pytest tests/test_gas.py -v`. Esperado: FAIL.

- [ ] **Step 3: Implementar `parse_gas`.**

- [ ] **Step 4: Ejecutar y comprobar que pasan**: el mismo comando. Esperado: PASS.

- [ ] **Step 5: Commit**: `git commit -m "feat(lib): parse CurEnergía gas invoices"`.

---

### Task 6: API pública, prueba con facturas locales y publicación en PyPI

**Files:**
- Create: `lib/src/pycurenergia/parser.py`, `lib/tests/test_parser.py`, `lib/tests/test_private_invoices.py`, `.github/workflows/lib-release.yml`
- Modify: `lib/src/pycurenergia/__init__.py`, `lib/README.md`

**Interfaces:**
- Consumes: `extract_text`, `parse_electricity`, `parse_gas`, `check_consistency`.
- Produces (exportados en `pycurenergia.__init__`, con `__all__`):
  - `parse_invoice_text(text: str) -> Invoice`: si el texto contiene `DATOS DE LA FACTURA DE ELECTRICIDAD`, usa el parser de luz; si contiene `FACTURA DE GAS`, el de gas; si no, lanza `UnsupportedInvoiceError`.
  - `parse_invoice_pdf(data: bytes) -> Invoice`
  - Además: `Invoice`, `Concept`, `ConceptKey`, `SupplyType`, `Problem`, `check_consistency`, `InvoiceParseError`, `UnsupportedInvoiceError` y `__version__ = "0.1.0"`.

- [ ] **Step 1: Escribir los tests que fallan.**
  - `test_parser.py`:
    - `test_dispatches_by_type`: las dos fixtures devuelven el `supply` correcto.
    - `test_unknown_text_raises` (Review Focus 5): `parse_invoice_text("Hola, adjunto el folleto")` lanza `UnsupportedInvoiceError`.
    - `test_public_api`: `from pycurenergia import parse_invoice_pdf, Invoice, check_consistency, __version__`.
  - `test_private_invoices.py`: está marcado `skipif` cuando no existe `private/invoices/` (ruta relativa a la raíz del repo), así que en CI no se ejecuta. Parametrizado sobre cada `*.pdf` de esa carpeta, comprueba que `check_consistency(parse_invoice_pdf(path.read_bytes())) == []`. Si algo falla, el mensaje solo incluye el nombre del fichero y los códigos `Problem`, **nunca** el texto.

- [ ] **Step 2: Ejecutar y comprobar que fallan**: `uv run --directory lib pytest tests/test_parser.py -v`. Esperado: FAIL.

- [ ] **Step 3: Implementar `parser.py` y las exportaciones de `__init__.py`.**

- [ ] **Step 4: Ejecutar toda la suite**: `uv run --directory lib pytest -v`. Esperado: todo PASS; con los PDF en `private/`, incluidos los dos de `test_private_invoices`. Después, `uv run --directory lib ruff check .` limpio y `uv build --directory lib`, que genera `lib/dist/pycurenergia-0.1.0.tar.gz` y el `.whl`.

- [ ] **Step 5: Crear `.github/workflows/lib-release.yml`.**
  - Se dispara en `push` de tags `pycurenergia-v*`.
  - Job `build`: `uv build --directory lib` y sube `lib/dist` como artefacto.
  - Job `publish`: `environment: pypi`, `permissions: id-token: write`, descarga el artefacto y usa `pypa/gh-action-pypi-publish@release/v1` con `packages-dir: lib/dist`.
  - Añadir al `lib/README.md` cómo usarla (`parse_invoice_pdf`) y la sección "Publicar" con el **paso manual del usuario**: crear la cuenta en PyPI y un *pending trusted publisher* con proyecto `pycurenergia`, owner `yuuues`, repo `hacs-curenergia`, workflow `lib-release.yml` y entorno `pypi`.

- [ ] **Step 6: Commit**: `git commit -m "feat(lib): public parse API, local invoice check and PyPI release workflow"`. Después, `git push`.

**Fuera de este plan:** etiquetar `pycurenergia-v0.1.0` y publicar en PyPI. Lo hace el usuario cuando haya configurado PyPI y cuando las facturas extra de `private/invoices/` pasen `test_private_invoices`.

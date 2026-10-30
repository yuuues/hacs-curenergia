# pycurenergia

Librería Python que lee las facturas en PDF de CurEnergía (electricidad y gas)
y devuelve sus datos como objetos tipados. Todos los importes, kWh, m³ y
porcentajes son `decimal.Decimal`.

> Proyecto no oficial: no está afiliado, respaldado ni patrocinado por
> CurEnergía.

Licencia MIT.

## Uso

```python
from pycurenergia import check_consistency, parse_invoice_pdf

with open("factura.pdf", "rb") as f:
    invoice = parse_invoice_pdf(f.read())

print(invoice.supply, invoice.total)
print(check_consistency(invoice))  # [] si los importes cuadran
```

- `parse_invoice_pdf(data: bytes)` lee un PDF; `parse_invoice_text(text: str)`
  parsea el texto ya extraído.
- Errores (todos derivan de `Exception`; ninguno incluye texto de la factura en
  su mensaje):
  - `InvoiceReadError`: el PDF no se puede leer (dañado, vacío, cifrado con
    contraseña) o es demasiado grande (más de 10 MiB o de 20 páginas). Solo lo
    lanza `parse_invoice_pdf`; el error original de pypdf queda en
    `__cause__`.
  - `UnsupportedInvoiceError`: el documento no es una factura de luz o de gas,
    o es una factura rectificativa o de abono (no soportadas).
  - `InvoiceParseError` (con el atributo `field`): falta algún dato obligatorio
    o no tiene el formato esperado.
- `check_consistency(invoice)` devuelve una lista de `Problem`; vacía si todo
  cuadra.
- `invoice.energy_price_kwh` es el precio de la energía en €/kWh, o `None` si
  la factura no lo indica.
- Lecturas del contador, como `MeterReading` (`value`, `read_on`, `estimated`),
  o `None` si la factura no las trae o no se entienden (nunca la invalidan):
  en luz, `reading_p1`, `reading_p2` y `reading_p3` (kWh); en gas, `reading_m3`
  y `previous_reading_m3` (m³).

## Publicar

El workflow `.github/workflows/lib-release.yml` construye y publica en PyPI al
subir una etiqueta `pycurenergia-v*` (por ejemplo `pycurenergia-v0.1.0`),
usando *trusted publishing* (sin tokens).

Paso manual previo, una sola vez:

1. Crear la cuenta en [PyPI](https://pypi.org).
2. En PyPI, añadir un *pending trusted publisher* con estos datos:
   - Proyecto: `pycurenergia`
   - Owner: `yuuues`
   - Repositorio: `hacs-curenergia`
   - Workflow: `lib-release.yml`
   - Entorno: `pypi`
3. Crear el entorno `pypi` en los ajustes del repositorio de GitHub y
   configurar en él *required reviewers* (revisores obligatorios), de modo que
   subir una etiqueta por sí solo no publique nada sin una aprobación manual.
4. Etiquetar y subir: `git tag pycurenergia-v0.1.0 && git push origin pycurenergia-v0.1.0`.

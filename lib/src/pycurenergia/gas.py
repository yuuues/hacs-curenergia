"""Lector de facturas de gas de CurEnergía."""

import re
from datetime import date

from pycurenergia._parsing import (
    BOL,
    CUPS,
    LINE_BREAK_RE,
    NUM,
    compact,
    convert,
    search,
    to_decimal,
    to_reading,
)
from pycurenergia.errors import InvoiceParseError
from pycurenergia.models import Concept, ConceptKey, Invoice, MeterReading, SupplyType
from pycurenergia.numbers import parse_dmy, parse_spanish_date

_DATE = r"\d{1,2}\s+de\s+[A-Za-zÁÉÍÓÚáéíóú]+\s+de\s+\d{4}"
_DMY = r"\d{1,2}/\d{1,2}/\d{4}"
_FLAGS = re.MULTILINE

_NUMBER_RE = re.compile(r"Número de factura[ \t]+([\w-]+)")
_ISSUE_DATE_RE = re.compile(rf"Fecha de emisión de factura[ \t]+({_DATE})")
_PERIOD_RE = re.compile(rf"Periodo de facturación[ \t]+({_DMY})[ \t]*-[ \t]*({_DMY})")
_CONTRACT_RE = re.compile(r"Número de contrato:?[ \t]+(\S+)")
_CUPS_RE = re.compile(rf"\(CUPS\):[ \t]*({CUPS})")
_KWH_RE = re.compile(rf"Consumo kWh:[ \t]*(?:real|estimada)[ \t]+({NUM})[ \t]*kWh")
_M3_RE = re.compile(rf"Consumo en m3:[ \t]*(?:real|estimada)[ \t]+({NUM})[ \t]*m3")
_TOTAL_RE = re.compile(rf"TOTAL IMPORTE FACTURA:?[ \t]+({NUM})[ \t]*€")
_VAT_RE = re.compile(
    rf"{BOL}IVA[ \t]+({NUM})[ \t]*%[ \t]*s/[ \t]*({NUM})[ \t]*€[ \t]+({NUM})[ \t]*€",
    _FLAGS,
)
_ESTIMATED_BANNER = "Factura con lectura estimada"
_READING_RE = re.compile(r"Lectura actual:[ \t]*(real|estimada)\b")
_METER_VALUE = rf"(real|estimada)[ \t]+({NUM})[ \t]*m3[ \t]+realizada el[ \t]+({_DMY})"
_CURRENT_METER_RE = re.compile(rf"Lectura actual:[ \t]*{_METER_VALUE}")
_PREVIOUS_METER_RE = re.compile(rf"Lectura anterior:[ \t]*{_METER_VALUE}")
# Otras marcas del tipo de lectura: si alguna es «estimada», la factura lo es.
_ESTIMATED_MARKERS_RE = re.compile(
    r"(?:Consumo kWh:|Consumo en m3:)[ \t]*(real|estimada)\b"
    r"|Energía facturada \((real|estimada)\)"
)
_ENERGY_PRICE_RE = re.compile(
    rf"Energía facturada \([^)\n]*\)[ \t]+{NUM}[ \t]*kWh[ \t]*x[ \t]*({NUM})"
    r"[ \t]*€/kWh"
)
_TARIFF_RE = re.compile(r"Tarifa de suministro:[ \t]*(\S+)")
_ACCESS_TARIFF_RE = re.compile(r"TARIFA PEAJE[ \t]+(\S+)")

# Desde la línea ``ENERGÍA`` (sola) hasta ``IMPORTE TOTAL``.
_SUMMARY_RE = re.compile(
    rf"{BOL}ENERGÍA[ \t]*\n(.*?){BOL}IMPORTE TOTAL\b", _FLAGS | re.DOTALL
)
_SUMMARY_LINE_RE = re.compile(rf"^(.+?)\s+({NUM})\s*€\s*$")
# La etiqueta acaba antes de la primera cantidad decimal («2,01 meses x …»).
_LABEL_QUANTITY_RE = re.compile(r"\s-?\d[\d.]*,\d+")
_LABEL_FOOTNOTE_RE = re.compile(r"\s\(\d\)$")

_CONCEPT_KEYS = (
    ("Término fijo", ConceptKey.GAS_FIXED_TERM),
    ("Energía facturada", ConceptKey.GAS_ENERGY),
    ("Impuesto sobre gas natural", ConceptKey.GAS_TAX),
    ("Alquiler equipos de medida", ConceptKey.METER_RENTAL),
)


def _concept_key(label: str) -> ConceptKey:
    for prefix, key in _CONCEPT_KEYS:
        if label.startswith(prefix):
            return key
    return ConceptKey.OTHER


def _clean_label(label: str) -> str:
    """Quita el detalle «cantidad x precio» y la llamada final tipo ``(1)``."""
    quantity = _LABEL_QUANTITY_RE.search(label)
    if quantity is not None:
        label = label[: quantity.start()]
    return _LABEL_FOOTNOTE_RE.sub("", label.strip()).strip()


def _parse_concepts(text: str) -> tuple[Concept, ...]:
    """Extrae las líneas con importe entre ``ENERGÍA`` e ``IMPORTE TOTAL``.

    Se omiten las cabeceras sin importe y las líneas ``TOTAL …``. ``Cargo
    aplicado`` y ``Tasa CNMC`` quedan fuera: van después del total. Las
    etiquetas desconocidas se conservan como ``ConceptKey.OTHER``. La etiqueta
    es el nombre del concepto, sin el detalle de cantidad y precio ni la llamada
    a nota final (``(1)``).
    """
    block = _SUMMARY_RE.search(text)
    if block is None:
        return ()
    concepts: list[Concept] = []
    for line in LINE_BREAK_RE.split(block.group(1)):
        line = line.strip()
        if line.startswith("TOTAL "):
            continue
        match = _SUMMARY_LINE_RE.match(line)
        if match is None:
            continue
        label, amount = _clean_label(match.group(1)), match.group(2)
        concepts.append(
            Concept(_concept_key(label), label, to_decimal(amount, "concepts"))
        )
    return tuple(concepts)


def _meter_readings(pattern: re.Pattern[str], text: str) -> list[MeterReading]:
    """Lecturas válidas de ``pattern``; las que no se entienden se ignoran."""
    readings: list[MeterReading] = []
    for kind, value, read_on_text in pattern.findall(text):
        try:
            read_on = parse_dmy(read_on_text)
        except ValueError:
            continue
        reading = to_reading(value, read_on, kind == "estimada")
        if reading is not None:
            readings.append(reading)
    return readings


def _by_date(reading: MeterReading) -> date:
    return reading.read_on


def parse_gas(text: str) -> Invoice:
    """Interpreta el texto extraído de una factura de gas.

    Lanza ``InvoiceParseError`` si falta un campo obligatorio: ``number``,
    ``issue_date``, ``period``, ``total``, ``kwh``, ``m3``, ``contract``,
    ``cups``, el IVA (``vat``) o el tipo de lectura (``estimated``: debe
    aparecer ``Lectura actual: real`` o ``estimada``). La factura es estimada si
    aparece ``Factura con lectura estimada`` o si es ``estimada`` alguna
    ``Lectura actual:``, ``Consumo kWh:``, ``Consumo en m3:`` o ``Energía
    facturada (…)``. Si no aparecen, ``tariff`` y ``access_tariff`` valen
    cadena vacía y ``energy_price_kwh`` ``None``. Las lecturas del contador
    nunca invalidan la factura: si no se entienden, valen ``None``; con varias,
    ``reading_m3`` es la más reciente y ``previous_reading_m3`` la más antigua.
    """
    number = search(_NUMBER_RE, text, "number").group(1)

    issue_date_text = search(_ISSUE_DATE_RE, text, "issue_date").group(1)
    issue_date = convert(parse_spanish_date, issue_date_text, "issue_date")

    period = search(_PERIOD_RE, text, "period")
    period_start: date = convert(parse_dmy, period.group(1), "period")
    period_end: date = convert(parse_dmy, period.group(2), "period")

    contract = search(_CONTRACT_RE, text, "contract").group(1)
    cups = compact(search(_CUPS_RE, text, "cups").group(1))
    kwh = to_decimal(search(_KWH_RE, text, "kwh").group(1), "kwh")
    m3 = to_decimal(search(_M3_RE, text, "m3").group(1), "m3")
    total = to_decimal(search(_TOTAL_RE, text, "total").group(1), "total")

    vat = search(_VAT_RE, text, "vat")
    vat_rate, vat_base, vat_amount = (
        to_decimal(vat.group(i), "vat") for i in (1, 2, 3)
    )

    readings = _READING_RE.findall(text)
    if not readings:
        raise InvoiceParseError("estimated")
    markers = [m for pair in _ESTIMATED_MARKERS_RE.findall(text) for m in pair if m]
    estimated = _ESTIMATED_BANNER in text or "estimada" in readings + markers
    energy_price = _ENERGY_PRICE_RE.search(text)
    tariff = _TARIFF_RE.search(text)
    access_tariff = _ACCESS_TARIFF_RE.search(text)

    return Invoice(
        supply=SupplyType.GAS,
        number=number,
        contract=contract,
        cups=cups,
        issue_date=issue_date,
        period_start=period_start,
        period_end=period_end,
        estimated=estimated,
        total=total,
        concepts=_parse_concepts(text),
        vat_rate=vat_rate,
        vat_base=vat_base,
        vat_amount=vat_amount,
        kwh=kwh,
        tariff="" if tariff is None else tariff.group(1),
        access_tariff="" if access_tariff is None else access_tariff.group(1),
        m3=m3,
        energy_price_kwh=(
            None
            if energy_price is None
            else to_decimal(energy_price.group(1), "energy_price_kwh")
        ),
        reading_m3=max(
            _meter_readings(_CURRENT_METER_RE, text), key=_by_date, default=None
        ),
        previous_reading_m3=min(
            _meter_readings(_PREVIOUS_METER_RE, text), key=_by_date, default=None
        ),
    )

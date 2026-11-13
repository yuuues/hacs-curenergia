"""Lector de facturas de gas de CurEnergía."""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

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
# Facturas de regularización: en vez de las líneas «Lectura actual:», «Consumo
# en m3:» y «Consumo kWh:» traen una tabla con una fila por tramo («Lectura
# Real», «Consumo Regularizado»…) y el «Consumo Neto (kWh)».
_CONSUMPTION_ROW_RE = re.compile(
    rf"^[ \t]*({_DMY})[ \t]+({_DMY})[ \t]+(\D+?)[ \t]+({NUM})[ \t]+({NUM})[ \t]+({NUM})"
    rf"[ \t]+{NUM}[ \t]+{NUM}[ \t]+({NUM})[ \t]*$",
    _FLAGS,
)
_NET_KWH_RE = re.compile(rf"Consumo Neto \(kWh\)[ \t]*({NUM})")
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
# Tramo de fechas de las líneas de una regularización: «(06/09/2024-11/03/2025)».
_LABEL_DATES_RE = re.compile(rf"\s*\({_DMY}-{_DMY}\)")
_AMOUNT_ONLY_RE = re.compile(rf"^({NUM})\s*€$")

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
    """Quita el detalle «cantidad x precio», el tramo de fechas y la llamada
    final tipo ``(1)``."""
    quantity = _LABEL_QUANTITY_RE.search(label)
    if quantity is not None:
        label = label[: quantity.start()]
    label = _LABEL_DATES_RE.sub("", label)
    return _LABEL_FOOTNOTE_RE.sub("", label.strip()).strip()


def _parse_concepts(text: str) -> tuple[Concept, ...]:
    """Extrae las líneas con importe entre ``ENERGÍA`` e ``IMPORTE TOTAL``.

    Se omiten las cabeceras sin importe y las líneas ``TOTAL …``. ``Cargo
    aplicado`` y ``Tasa CNMC`` quedan fuera: van después del total. Las
    etiquetas desconocidas se conservan como ``ConceptKey.OTHER``. La etiqueta
    es el nombre del concepto, sin el detalle de cantidad y precio ni la llamada
    a nota final (``(1)``). Si el importe viene solo en su línea, la etiqueta
    son las líneas anteriores sin importe (salvo las cabeceras en mayúsculas).
    """
    block = _SUMMARY_RE.search(text)
    if block is None:
        return ()
    concepts: list[Concept] = []
    pending: list[str] = []
    for line in LINE_BREAK_RE.split(block.group(1)):
        line = line.strip()
        if line.startswith("TOTAL "):
            pending = []
            continue
        amount_only = _AMOUNT_ONLY_RE.match(line)
        if amount_only is not None and pending:
            line = f"{' '.join(pending)} {line}"
        match = _SUMMARY_LINE_RE.match(line)
        if match is None:
            pending = [] if not line or line.isupper() else [*pending, line]
            continue
        pending = []
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


@dataclass(frozen=True)
class _Consumption:
    """Consumos y lecturas de una factura de gas."""

    kwh: Decimal
    m3: Decimal
    estimated: bool
    energy_price_kwh: Decimal | None
    reading_m3: MeterReading | None
    previous_reading_m3: MeterReading | None


def _standard_consumption(text: str) -> _Consumption:
    """Consumos de una factura normal: líneas ``Consumo kWh:``, ``Lectura actual:``…"""
    kwh = to_decimal(search(_KWH_RE, text, "kwh").group(1), "kwh")
    m3 = to_decimal(search(_M3_RE, text, "m3").group(1), "m3")
    readings = _READING_RE.findall(text)
    if not readings:
        raise InvoiceParseError("estimated")
    markers = [m for pair in _ESTIMATED_MARKERS_RE.findall(text) for m in pair if m]
    energy_price = _ENERGY_PRICE_RE.search(text)
    return _Consumption(
        kwh=kwh,
        m3=m3,
        estimated=_ESTIMATED_BANNER in text or "estimada" in readings + markers,
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


def _regularisation_consumption(text: str) -> _Consumption:
    """Factura de regularización: consumos de la tabla de tramos.

    ``kwh`` es el «Consumo Neto (kWh)» (o la suma de los tramos) y ``m3`` la
    suma de los m3 de los tramos; los dos pueden ser negativos si lo ya
    facturado por estimación supera al consumo real. El tipo de lectura sale de
    las filas ``Lectura …``; sin ninguna, lanza ``InvoiceParseError``
    (``estimated``). ``reading_m3`` es la lectura final del tramo ``Lectura …``
    más reciente y ``previous_reading_m3`` su lectura inicial, solo si ese
    tramo es de lectura real. ``energy_price_kwh`` vale ``None``: hay un precio
    por tramo.
    """
    rows = _CONSUMPTION_ROW_RE.findall(text)
    if not rows:
        raise InvoiceParseError("kwh")
    net = _NET_KWH_RE.search(text)
    if net is not None:
        kwh = to_decimal(net.group(1), "kwh")
    else:
        kwh = sum((to_decimal(row[6], "kwh") for row in rows), start=Decimal(0))
    m3 = sum((to_decimal(row[5], "m3") for row in rows), start=Decimal(0))

    lectures: list[tuple[date, date, bool, str, str]] = []
    for start, end, kind, reading_from, reading_to, _m3, _kwh in rows:
        if not kind.startswith("Lectura"):
            continue
        lectures.append(
            (
                convert(parse_dmy, end, "estimated"),
                convert(parse_dmy, start, "estimated"),
                "estimad" in kind.lower(),
                reading_from,
                reading_to,
            )
        )
    if not lectures:
        raise InvoiceParseError("estimated")
    read_on, read_from, is_estimated, reading_from, reading_to = max(lectures)
    estimated = _ESTIMATED_BANNER in text or any(item[2] for item in lectures)

    return _Consumption(
        kwh=kwh,
        m3=m3,
        estimated=estimated,
        energy_price_kwh=None,
        reading_m3=to_reading(reading_to, read_on, is_estimated),
        previous_reading_m3=(
            None if is_estimated else to_reading(reading_from, read_from, False)
        ),
    )


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

    Una factura de regularización (sin ``Consumo kWh:`` y con tabla de tramos)
    se lee con ``_regularisation_consumption``: ``kwh`` y ``m3`` son netos y
    pueden ser negativos.
    """
    number = search(_NUMBER_RE, text, "number").group(1)

    issue_date_text = search(_ISSUE_DATE_RE, text, "issue_date").group(1)
    issue_date = convert(parse_spanish_date, issue_date_text, "issue_date")

    period = search(_PERIOD_RE, text, "period")
    period_start: date = convert(parse_dmy, period.group(1), "period")
    period_end: date = convert(parse_dmy, period.group(2), "period")

    contract = search(_CONTRACT_RE, text, "contract").group(1)
    cups = compact(search(_CUPS_RE, text, "cups").group(1))
    total = to_decimal(search(_TOTAL_RE, text, "total").group(1), "total")

    vat = search(_VAT_RE, text, "vat")
    vat_rate, vat_base, vat_amount = (
        to_decimal(vat.group(i), "vat") for i in (1, 2, 3)
    )

    # Sin «Consumo kWh:» pero con tabla de tramos: factura de regularización.
    if _KWH_RE.search(text) is None and _CONSUMPTION_ROW_RE.search(text):
        consumption = _regularisation_consumption(text)
    else:
        consumption = _standard_consumption(text)
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
        estimated=consumption.estimated,
        total=total,
        concepts=_parse_concepts(text),
        vat_rate=vat_rate,
        vat_base=vat_base,
        vat_amount=vat_amount,
        kwh=consumption.kwh,
        tariff="" if tariff is None else tariff.group(1),
        access_tariff="" if access_tariff is None else access_tariff.group(1),
        m3=consumption.m3,
        energy_price_kwh=consumption.energy_price_kwh,
        reading_m3=consumption.reading_m3,
        previous_reading_m3=consumption.previous_reading_m3,
    )

"""Lector de facturas de electricidad de CurEnergía."""

import re
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
from pycurenergia.numbers import parse_spanish_date

_DATE = r"\d{1,2}\s+de\s+[A-Za-zÁÉÍÓÚáéíóú]+\s+de\s+\d{4}"
_FLAGS = re.MULTILINE

_NUMBER_RE = re.compile(r"Nº Factura:[ \t]*(\d+)\b")
_ISSUE_DATE_RE = re.compile(rf"Nº Factura:[ \t]*\d+\s+emitida\s+el\s+({_DATE})")
_PERIOD_RE = re.compile(rf"Periodo de consumo:\s*({_DATE})\s+a\s+({_DATE})")
_CONTRACT_RE = re.compile(
    r"Referencia del contrato de suministro \([^)]*\):[ \t]*(\d+)\b"
)
_CUPS_RE = re.compile(rf"CUPS:[ \t]*({CUPS})")
_KWH_RE = re.compile(rf"Su consumo en el periodo facturado ha sido:\s*({NUM})\s*kWh")
_KWH_PERIOD_RE = r"Consumo en P{n}:\s*(" + NUM + r")\s*kWh"
_TOTAL_RE = re.compile(rf"TOTAL IMPORTE FACTURA:\s*({NUM})\s*€")
_VAT_RE = re.compile(
    rf"{BOL}IVA\s+({NUM})\s*%\s*s/\s*({NUM})\s*€\s+({NUM})\s*€", _FLAGS
)
_LATE_INTEREST_RE = re.compile(rf"Intereses de demora \(\*\)\s*({NUM})\s*€")
_ESTIMATED_RE = re.compile(r"Lectura actual \((real|estimada)\)")
_METER_HEADER_RE = re.compile(rf"Lectura actual \((real|estimada)\)\s*\(({_DATE})\)")
_METER_PERIOD_RE = r"Lectura en P{n}\b[^:\n]*:\s*(" + NUM + r")\s*kWh"
_ENERGY_PRICE_RE = re.compile(
    rf"Coste de la energía:\s*{NUM}\s*kWh\s*x\s*({NUM})\s*€/kWh"
)
_POWER_RE = r"Potencia contratada periodo {name}:\s*(" + NUM + r")\s*kW"
_TARIFF_RE = re.compile(r"TIPO DE CONTRATO:[ \t]*(\S+)")
_ACCESS_TARIFF_RE = re.compile(
    rf"{BOL}Peajes de transporte y distribución[ \t]*:[ \t]*(\S+)", _FLAGS
)

_SUMMARY_RE = re.compile(
    rf"{BOL}Por potencia contratada\b.*?{BOL}TOTAL IMPORTE FACTURA:",
    _FLAGS | re.DOTALL,
)
_SUMMARY_LINE_RE = re.compile(rf"^(.+?)\s+({NUM})\s*€\s*$")

_CONCEPT_KEYS = {
    "Por potencia contratada": ConceptKey.POWER,
    "Por energía consumida": ConceptKey.ENERGY,
    "Por financiación del bono social": ConceptKey.SOCIAL_BONUS,
    "Impuesto electricidad": ConceptKey.ELECTRICITY_TAX,
    "Alquiler del contador": ConceptKey.METER_RENTAL,
}


def _optional_decimal(pattern: str, text: str, field: str) -> Decimal | None:
    match = re.search(pattern, text)
    return None if match is None else to_decimal(match.group(1), field)


def _parse_concepts(text: str) -> tuple[Concept, ...]:
    """Extrae las líneas del resumen entre ``Por potencia contratada`` y el total.

    La línea de IVA se omite: va en ``vat_*``. Las etiquetas desconocidas se
    conservan como ``ConceptKey.OTHER``.
    """
    block = _SUMMARY_RE.search(text)
    if block is None:
        return ()
    concepts: list[Concept] = []
    for line in LINE_BREAK_RE.split(block.group(0)):
        match = _SUMMARY_LINE_RE.match(line.strip())
        if match is None:
            continue
        label, amount = match.groups()
        if label.startswith("IVA "):
            continue
        key = _CONCEPT_KEYS.get(label, ConceptKey.OTHER)
        concepts.append(Concept(key, label, to_decimal(amount, "concepts")))
    return tuple(concepts)


def _meter_readings(
    text: str,
) -> tuple[MeterReading | None, MeterReading | None, MeterReading | None]:
    """Lecturas de P1, P2 y P3 del bloque ``Lectura actual`` más reciente.

    Lo que no se entiende vale ``None``: una lectura nunca invalida la factura.
    """
    headers = list(_METER_HEADER_RE.finditer(text))
    blocks: list[tuple[date, bool, str]] = []
    for index, header in enumerate(headers):
        try:
            read_on = parse_spanish_date(header.group(2))
        except ValueError:
            continue
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        blocks.append(
            (read_on, header.group(1) == "estimada", text[header.end() : end])
        )
    if not blocks:
        return None, None, None

    read_on, estimated, block = max(blocks, key=lambda item: item[0])

    def period(n: int) -> MeterReading | None:
        match = re.search(_METER_PERIOD_RE.format(n=n), block)
        return None if match is None else to_reading(match.group(1), read_on, estimated)

    return period(1), period(2), period(3)


def parse_electricity(text: str) -> Invoice:
    """Interpreta el texto extraído de una factura de electricidad.

    Lanza ``InvoiceParseError`` si falta un campo obligatorio: ``number``,
    ``issue_date``, ``period``, ``total``, ``kwh``, ``contract``, ``cups``, el
    IVA (``vat``) o el tipo de lectura (``estimated``: debe aparecer
    ``Lectura actual (real)`` o ``(estimada)``). La factura es estimada si
    alguna ``Lectura actual`` lo es. Si no aparecen, ``late_interest`` vale 0,
    ``tariff`` y ``access_tariff`` cadena vacía y los kWh por periodo y
    ``energy_price_kwh`` ``None``; la potencia contratada solo se informa si
    están punta y valle.
    """
    number = search(_NUMBER_RE, text, "number").group(1)

    issue_date_text = search(_ISSUE_DATE_RE, text, "issue_date").group(1)
    issue_date = convert(parse_spanish_date, issue_date_text, "issue_date")

    period = search(_PERIOD_RE, text, "period")
    period_start: date = convert(parse_spanish_date, period.group(1), "period")
    period_end: date = convert(parse_spanish_date, period.group(2), "period")

    contract = search(_CONTRACT_RE, text, "contract").group(1)
    cups = compact(search(_CUPS_RE, text, "cups").group(1))
    kwh = to_decimal(search(_KWH_RE, text, "kwh").group(1), "kwh")
    total = to_decimal(search(_TOTAL_RE, text, "total").group(1), "total")

    vat = search(_VAT_RE, text, "vat")
    vat_rate, vat_base, vat_amount = (
        to_decimal(vat.group(i), "vat") for i in (1, 2, 3)
    )

    kwh_p1, kwh_p2, kwh_p3 = (
        _optional_decimal(_KWH_PERIOD_RE.format(n=n), text, f"kwh_p{n}")
        for n in (1, 2, 3)
    )

    power_peak, power_valley = (
        _optional_decimal(_POWER_RE.format(name=name), text, "contracted_power_kw")
        for name in ("punta", "valle")
    )
    contracted_power_kw = (
        (power_peak, power_valley)
        if power_peak is not None and power_valley is not None
        else ()
    )

    late_interest = _LATE_INTEREST_RE.search(text)
    readings = _ESTIMATED_RE.findall(text)
    if not readings:
        raise InvoiceParseError("estimated")
    energy_price = _ENERGY_PRICE_RE.search(text)
    tariff = _TARIFF_RE.search(text)
    access_tariff = _ACCESS_TARIFF_RE.search(text)
    reading_p1, reading_p2, reading_p3 = _meter_readings(text)

    return Invoice(
        supply=SupplyType.ELECTRICITY,
        number=number,
        contract=contract,
        cups=cups,
        issue_date=issue_date,
        period_start=period_start,
        period_end=period_end,
        estimated="estimada" in readings,
        total=total,
        concepts=_parse_concepts(text),
        vat_rate=vat_rate,
        vat_base=vat_base,
        vat_amount=vat_amount,
        kwh=kwh,
        tariff="" if tariff is None else tariff.group(1),
        access_tariff="" if access_tariff is None else access_tariff.group(1),
        kwh_p1=kwh_p1,
        kwh_p2=kwh_p2,
        kwh_p3=kwh_p3,
        contracted_power_kw=contracted_power_kw,
        late_interest=(
            Decimal(0)
            if late_interest is None
            else to_decimal(late_interest.group(1), "late_interest")
        ),
        energy_price_kwh=(
            None
            if energy_price is None
            else to_decimal(energy_price.group(1), "energy_price_kwh")
        ),
        reading_p1=reading_p1,
        reading_p2=reading_p2,
        reading_p3=reading_p3,
    )

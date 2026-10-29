from datetime import date
from decimal import Decimal

import pytest

from pycurenergia.errors import InvoiceParseError
from pycurenergia.gas import parse_gas
from pycurenergia.models import Concept, ConceptKey, SupplyType
from pycurenergia.validation import Problem, check_consistency

FIXTURE = "gas_2026-09"


def test_parses_anonymized_invoice(fixture_text):
    inv = parse_gas(fixture_text(FIXTURE))

    assert inv.supply is SupplyType.GAS
    assert inv.number == "09260911010000002"
    assert inv.contract == "1000000002"
    assert inv.cups == "ES0217000000000002BB"
    assert inv.issue_date == date(2026, 9, 11)
    assert (inv.period_start, inv.period_end) == (date(2026, 7, 7), date(2026, 9, 7))
    assert inv.estimated is True
    assert inv.total == Decimal("19.20")
    assert inv.kwh == Decimal("150.32")
    assert inv.m3 == Decimal("13")
    assert (inv.vat_rate, inv.vat_base, inv.vat_amount) == (
        Decimal("21"),
        Decimal("15.87"),
        Decimal("3.33"),
    )
    assert inv.tariff == "TUR.1"
    assert inv.access_tariff == "RL.1"
    assert inv.kwh_p1 is None
    assert [(c.key, c.amount) for c in inv.concepts] == [
        (ConceptKey.GAS_FIXED_TERM, Decimal("7.90")),
        (ConceptKey.GAS_ENERGY, Decimal("6.51")),
        (ConceptKey.GAS_TAX, Decimal("0.30")),
        (ConceptKey.METER_RENTAL, Decimal("1.16")),
    ]
    assert check_consistency(inv) == []


def test_charges_after_total_are_not_concepts(fixture_text):
    inv = parse_gas(fixture_text(FIXTURE))

    labels = {c.label for c in inv.concepts}
    assert not any(
        label.startswith(("Cargo aplicado", "Tasa CNMC")) for label in labels
    )
    assert not any(c.label.startswith("TOTAL ") for c in inv.concepts)


def test_unknown_concept_becomes_other(fixture_text):
    text = (
        fixture_text(FIXTURE)
        .replace(
            "Alquiler equipos de medida 1,16 €",
            "Concepto nuevo 1,00 €\nAlquiler equipos de medida 1,16 €",
            1,
        )
        .replace("15,87", "16,87")
        .replace("3,33", "3,54")
        .replace("19,20", "20,41")
    )

    inv = parse_gas(text)

    assert Concept(ConceptKey.OTHER, "Concepto nuevo", Decimal("1.00")) in inv.concepts
    assert check_consistency(inv) == []


def test_concept_labels_drop_quantity_and_footnote(fixture_text):
    inv = parse_gas(fixture_text(FIXTURE))

    assert [c.label for c in inv.concepts] == [
        "Término fijo mensual",
        "Energía facturada (estimada)",
        "Impuesto sobre gas natural (estimado)",
        "Alquiler equipos de medida",
    ]


def test_energy_price(fixture_text):
    assert parse_gas(fixture_text(FIXTURE)).energy_price_kwh == Decimal("0.04329798")


def test_missing_energy_price_is_none(fixture_text):
    text = fixture_text(FIXTURE).replace("Energía facturada", "XX")

    assert parse_gas(text).energy_price_kwh is None


def test_missing_energy_block_is_total_mismatch(fixture_text):
    text = fixture_text(FIXTURE).replace("\nENERGÍA\n", "\nXX\n")

    inv = parse_gas(text)

    assert inv.concepts == ()
    assert check_consistency(inv) == [Problem.TOTAL_MISMATCH]


_ESTIMATED_MARKERS = {
    "Factura con lectura estimada\n": "",
    "Lectura actual: estimada": "Lectura actual: real",
    "Consumo kWh: estimada": "Consumo kWh: real",
    "Consumo en m3: estimada": "Consumo en m3: real",
    "Energía facturada (estimada)": "Energía facturada (real)",
}


def _all_real(text: str) -> str:
    for estimated, real in _ESTIMATED_MARKERS.items():
        text = text.replace(estimated, real)
    return text


def test_real_reading_is_not_estimated(fixture_text):
    assert parse_gas(_all_real(fixture_text(FIXTURE))).estimated is False


@pytest.mark.parametrize(
    "estimated", [m for m in _ESTIMATED_MARKERS if not m.startswith("Factura")]
)
def test_any_estimated_marker_marks_estimated(fixture_text, estimated):
    real = _ESTIMATED_MARKERS[estimated]
    text = _all_real(fixture_text(FIXTURE)).replace(real, estimated)

    assert parse_gas(text).estimated is True


def test_second_estimated_reading_marks_estimated(fixture_text):
    text = _all_real(fixture_text(FIXTURE)).replace(
        "Lectura anterior: real", "Lectura actual: estimada"
    )

    assert parse_gas(text).estimated is True


def test_cups_does_not_swallow_following_text(fixture_text):
    text = fixture_text(FIXTURE).replace(
        "ES 0217 0000 0000 0002 BB", "ES 0217 0000 0000 0002 BB SUMINISTRO"
    )

    assert parse_gas(text).cups == "ES0217000000000002BB"


def test_estimated_banner_alone_marks_estimated(fixture_text):
    text = fixture_text(FIXTURE).replace(
        "Lectura actual: estimada", "Lectura actual: real"
    )

    assert parse_gas(text).estimated is True


def test_estimated_reading_line_alone_marks_estimated(fixture_text):
    text = fixture_text(FIXTURE).replace("Factura con lectura estimada\n", "")

    assert parse_gas(text).estimated is True


@pytest.mark.parametrize("reading", ["Lectura actual: autolectura", "Lectura actual:"])
def test_missing_reading_type_raises(fixture_text, reading):
    text = fixture_text(FIXTURE).replace("Lectura actual: estimada", reading)

    with pytest.raises(InvoiceParseError) as excinfo:
        parse_gas(text)

    assert excinfo.value.field == "estimated"


def test_missing_reading_line_raises_even_with_estimated_banner(fixture_text):
    text = fixture_text(FIXTURE).replace("Lectura actual:", "XX")

    with pytest.raises(InvoiceParseError) as excinfo:
        parse_gas(text)

    assert excinfo.value.field == "estimated"


def test_missing_period_raises(fixture_text):
    lines = fixture_text(FIXTURE).split("\n")
    text = "\n".join(
        line for line in lines if not line.startswith("Periodo de facturación")
    )

    with pytest.raises(InvoiceParseError) as excinfo:
        parse_gas(text)

    assert excinfo.value.field == "period"


@pytest.mark.parametrize(
    ("anchor", "field"),
    [
        ("TOTAL IMPORTE FACTURA", "total"),
        ("Número de factura", "number"),
        ("Fecha de emisión de factura", "issue_date"),
        ("Número de contrato", "contract"),
        ("(CUPS):", "cups"),
        ("Consumo kWh:", "kwh"),
        ("Consumo en m3:", "m3"),
    ],
)
def test_missing_required_field_raises(fixture_text, anchor, field):
    text = fixture_text(FIXTURE).replace(anchor, "XX")

    with pytest.raises(InvoiceParseError) as excinfo:
        parse_gas(text)

    assert excinfo.value.field == field


def test_missing_vat_raises(fixture_text):
    text = fixture_text(FIXTURE).replace("IVA ", "XX ")

    with pytest.raises(InvoiceParseError) as excinfo:
        parse_gas(text)

    assert excinfo.value.field == "vat"


def test_empty_value_does_not_capture_next_line(fixture_text):
    text = fixture_text(FIXTURE).replace(
        "Tarifa de suministro: TUR.1", "Tarifa de suministro:"
    )

    assert parse_gas(text).tariff == ""


def test_anchors_survive_form_feed_instead_of_newline(fixture_text):
    text = (
        fixture_text(FIXTURE)
        .replace("\nENERGÍA\n", "\fENERGÍA\n")
        .replace("\nIMPORTE TOTAL", "\fIMPORTE TOTAL")
        .replace("\nIVA", "\fIVA")
    )

    inv = parse_gas(text)

    assert len(inv.concepts) == 4
    assert inv.vat_amount == Decimal("3.33")
    assert check_consistency(inv) == []

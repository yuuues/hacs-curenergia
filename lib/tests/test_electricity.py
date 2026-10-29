from datetime import date
from decimal import Decimal

import pytest

from pycurenergia.electricity import parse_electricity
from pycurenergia.errors import InvoiceParseError
from pycurenergia.models import Concept, ConceptKey, SupplyType
from pycurenergia.validation import check_consistency

FIXTURE = "electricity_2026-10"


def test_parses_anonymized_invoice(fixture_text):
    inv = parse_electricity(fixture_text(FIXTURE))

    assert inv.supply is SupplyType.ELECTRICITY
    assert inv.number == "09261006010000001"
    assert inv.contract == "100000001"
    assert inv.cups == "ES0031000000000001AA"
    assert inv.issue_date == date(2026, 10, 6)
    # El fin del periodo está partido en dos líneas en la fixture.
    assert (inv.period_start, inv.period_end) == (
        date(2026, 8, 29),
        date(2026, 9, 28),
    )
    assert inv.estimated is False
    assert inv.total == Decimal("102.55")
    assert inv.kwh == Decimal("380.06")
    assert (inv.kwh_p1, inv.kwh_p2, inv.kwh_p3) == (
        Decimal("107.11"),
        Decimal("104.16"),
        Decimal("168.79"),
    )
    assert (inv.vat_rate, inv.vat_base, inv.vat_amount) == (
        Decimal("21"),
        Decimal("84.63"),
        Decimal("17.77"),
    )
    assert inv.tariff == "PVPC"
    assert inv.access_tariff == "2.0TD"
    assert inv.contracted_power_kw == (Decimal("4.6"), Decimal("4.6"))
    assert inv.late_interest == Decimal("0.15")
    assert [(c.key, c.amount) for c in inv.concepts] == [
        (ConceptKey.POWER, Decimal("11.94")),
        (ConceptKey.ENERGY, Decimal("67.07")),
        (ConceptKey.SOCIAL_BONUS, Decimal("0.74")),
        (ConceptKey.ELECTRICITY_TAX, Decimal("4.08")),
        (ConceptKey.OTHER, Decimal("0.15")),
        (ConceptKey.METER_RENTAL, Decimal("0.80")),
    ]
    other = next(c for c in inv.concepts if c.key is ConceptKey.OTHER)
    assert other.label == "Otros"
    assert check_consistency(inv) == []


def test_unknown_concept_becomes_other(fixture_text):
    text = (
        fixture_text(FIXTURE)
        .replace(
            "Alquiler del contador 0,80 €",
            "Concepto nuevo 1,00 €\nAlquiler del contador 0,80 €",
            1,
        )
        .replace("102,55", "103,55")
    )

    inv = parse_electricity(text)

    assert Concept(ConceptKey.OTHER, "Concepto nuevo", Decimal("1.00")) in inv.concepts
    assert check_consistency(inv) == []


def test_estimated_reading(fixture_text):
    text = fixture_text(FIXTURE).replace(
        "Lectura actual (real)", "Lectura actual (estimada)"
    )

    assert parse_electricity(text).estimated is True


def test_missing_number_raises(fixture_text):
    lines = fixture_text(FIXTURE).split("\n")
    text = "\n".join(line for line in lines if not line.startswith("Nº Factura:"))

    with pytest.raises(InvoiceParseError) as excinfo:
        parse_electricity(text)

    assert excinfo.value.field == "number"


def test_missing_late_interest_is_zero(fixture_text):
    text = fixture_text(FIXTURE).replace("Intereses de demora (*) 0,15 €", "")

    assert parse_electricity(text).late_interest == Decimal(0)


@pytest.mark.parametrize(
    ("anchor", "field"),
    [
        ("TOTAL IMPORTE FACTURA:", "total"),
        ("Su consumo en el periodo facturado ha sido:", "kwh"),
        ("Referencia del contrato de suministro", "contract"),
        ("CUPS:", "cups"),
        ("Periodo de consumo:", "period"),
    ],
)
def test_missing_required_field_raises(fixture_text, anchor, field):
    text = fixture_text(FIXTURE).replace(anchor, "XX")

    with pytest.raises(InvoiceParseError) as excinfo:
        parse_electricity(text)

    assert excinfo.value.field == field


def test_missing_vat_raises(fixture_text):
    text = fixture_text(FIXTURE).replace("IVA 21 %", "XX 21 %")

    with pytest.raises(InvoiceParseError) as excinfo:
        parse_electricity(text)

    assert excinfo.value.field == "vat"


def test_any_estimated_reading_marks_estimated(fixture_text):
    # Una segunda «Lectura actual (estimada)» tras la real hace estimada la factura.
    text = fixture_text(FIXTURE).replace(
        "Lectura actual (real) (28 de septiembre de 2026)",
        "Lectura actual (real) (28 de septiembre de 2026)\n"
        "Lectura actual (estimada) (28 de septiembre de 2026)",
    )

    assert parse_electricity(text).estimated is True


def test_energy_price(fixture_text):
    assert parse_electricity(fixture_text(FIXTURE)).energy_price_kwh == Decimal(
        "0.139504"
    )


def test_missing_energy_price_is_none(fixture_text):
    text = fixture_text(FIXTURE).replace("Coste de la energía:", "XX")

    assert parse_electricity(text).energy_price_kwh is None


@pytest.mark.parametrize(
    ("line", "field"),
    [
        ("Nº Factura: 09261006010000001", "number"),
        (
            "Referencia del contrato de suministro (CURENERGÍA COMERCIALIZADOR DE "
            "ÚLTIMO RECURSO S.A.U.): 100000001",
            "contract",
        ),
    ],
)
def test_empty_identifier_does_not_capture_next_line(fixture_text, line, field):
    value = line.rsplit(" ", 1)[1]
    text = fixture_text(FIXTURE).replace(line, line.removesuffix(" " + value), 1)

    with pytest.raises(InvoiceParseError) as excinfo:
        parse_electricity(text)

    assert excinfo.value.field == field


def test_empty_tariff_does_not_capture_next_line(fixture_text):
    text = fixture_text(FIXTURE).replace(
        "TIPO DE CONTRATO: PVPC - MERCADO REGULADO", "TIPO DE CONTRATO:"
    )

    assert parse_electricity(text).tariff == ""


def test_cups_does_not_swallow_following_text(fixture_text):
    text = fixture_text(FIXTURE).replace(
        "ES 0031 0000 0000 0001 AA", "ES 0031 0000 0000 0001 AA SUMINISTRO"
    )

    assert parse_electricity(text).cups == "ES0031000000000001AA"


def test_cups_with_border_point_suffix(fixture_text):
    text = fixture_text(FIXTURE).replace(
        "ES 0031 0000 0000 0001 AA", "ES 0031 0000 0000 0001 AA 1F"
    )

    assert parse_electricity(text).cups == "ES0031000000000001AA1F"


def test_anchors_survive_form_feed_instead_of_newline(fixture_text):
    text = (
        fixture_text(FIXTURE)
        .replace("\nPor potencia contratada", "\fPor potencia contratada")
        .replace("\nAlquiler del contador 0,80", "\fAlquiler del contador 0,80")
        .replace("\nIVA", "\fIVA")
        .replace("\nTOTAL IMPORTE FACTURA:", "\fTOTAL IMPORTE FACTURA:")
        .replace("\nPeajes de transporte", "\fPeajes de transporte")
    )

    inv = parse_electricity(text)

    assert len(inv.concepts) == 6
    assert inv.vat_amount == Decimal("17.77")
    assert inv.access_tariff == "2.0TD"
    assert check_consistency(inv) == []


@pytest.mark.parametrize("reading", ["(autolectura)", "(estimada"])
def test_missing_reading_type_raises(fixture_text, reading):
    text = fixture_text(FIXTURE).replace(
        "Lectura actual (real)", f"Lectura actual {reading}"
    )

    with pytest.raises(InvoiceParseError) as excinfo:
        parse_electricity(text)

    assert excinfo.value.field == "estimated"

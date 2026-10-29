"""Tests de las comprobaciones de coherencia de ``Invoice``."""

from datetime import date
from decimal import Decimal

from pycurenergia.models import Concept, ConceptKey, Invoice, SupplyType
from pycurenergia.validation import Problem, check_consistency


def make_invoice(**overrides) -> Invoice:
    """Factura de luz anonimizada y coherente; ``overrides`` sustituye campos."""
    values = {
        "supply": SupplyType.ELECTRICITY,
        "number": "TEST-0001",
        "contract": "C-0001",
        "cups": "ES0000000000000000XX",
        "issue_date": date(2026, 10, 5),
        "period_start": date(2026, 8, 29),
        "period_end": date(2026, 9, 28),
        "estimated": False,
        "total": Decimal("102.55"),
        "concepts": (
            Concept(ConceptKey.POWER, "Potencia", Decimal("11.94")),
            Concept(ConceptKey.ENERGY, "Energía", Decimal("67.07")),
            Concept(ConceptKey.SOCIAL_BONUS, "Bono social", Decimal("0.74")),
            Concept(ConceptKey.ELECTRICITY_TAX, "Impuesto eléctrico", Decimal("4.08")),
            Concept(ConceptKey.OTHER, "Otros", Decimal("0.15")),
            Concept(ConceptKey.METER_RENTAL, "Alquiler de contador", Decimal("0.80")),
        ),
        "vat_rate": Decimal(21),
        "vat_base": Decimal("84.63"),
        "vat_amount": Decimal("17.77"),
        "kwh": Decimal("380.06"),
        "tariff": "TEST",
        "access_tariff": "2.0TD",
        "kwh_p1": Decimal("107.11"),
        "kwh_p2": Decimal("104.16"),
        "kwh_p3": Decimal("168.79"),
    }
    values.update(overrides)
    return Invoice(**values)


def test_consistent_invoice_has_no_problems():
    assert check_consistency(make_invoice()) == []


def test_total_mismatch():
    inv = make_invoice(total=Decimal("102.60"))
    assert check_consistency(inv) == [Problem.TOTAL_MISMATCH]


def test_rounding_within_tolerance():
    inv = make_invoice(total=Decimal("102.56"))
    assert check_consistency(inv) == []


def test_vat_mismatch():
    inv = make_invoice(vat_amount=Decimal("18.00"), total=Decimal("102.78"))
    assert check_consistency(inv) == [Problem.VAT_MISMATCH]


def test_kwh_periods_mismatch():
    inv = make_invoice(kwh_p3=Decimal(160))
    assert check_consistency(inv) == [Problem.KWH_PERIODS_MISMATCH]


def test_kwh_periods_just_over_tolerance():
    inv = make_invoice(kwh_p3=Decimal("168.81"))
    assert check_consistency(inv) == [Problem.KWH_PERIODS_MISMATCH]


def test_partial_kwh_periods_mismatch():
    inv = make_invoice(kwh_p3=None)
    assert check_consistency(inv) == [Problem.KWH_PERIODS_MISMATCH]


def test_gas_without_periods_skips_kwh_rule():
    inv = make_invoice(kwh_p1=None, kwh_p2=None, kwh_p3=None)
    assert check_consistency(inv) == []


def test_period_inverted():
    inv = make_invoice(period_start=date(2026, 9, 28), period_end=date(2026, 8, 29))
    assert check_consistency(inv) == [Problem.PERIOD_INVERTED]


def test_concept_total():
    inv = make_invoice()
    assert inv.concept_total(ConceptKey.POWER, ConceptKey.ENERGY) == Decimal("79.01")

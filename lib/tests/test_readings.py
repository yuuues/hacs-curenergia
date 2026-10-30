from datetime import date
from decimal import Decimal

import pytest

from pycurenergia import MeterReading
from pycurenergia.electricity import parse_electricity
from pycurenergia.gas import parse_gas

ELECTRICITY = "electricity_2026-10"
GAS = "gas_2026-09"
_SEPTEMBER = date(2026, 9, 28)


def test_electricity_readings(fixture_text):
    inv = parse_electricity(fixture_text(ELECTRICITY))

    assert inv.reading_p1 == MeterReading(Decimal("10000.00"), _SEPTEMBER, False)
    assert inv.reading_p2 == MeterReading(Decimal("20000.00"), _SEPTEMBER, False)
    assert inv.reading_p3 == MeterReading(Decimal("30000.00"), _SEPTEMBER, False)
    assert inv.reading_m3 is None
    assert inv.previous_reading_m3 is None


def test_electricity_estimated_reading(fixture_text):
    text = fixture_text(ELECTRICITY).replace(
        "Lectura actual (real)", "Lectura actual (estimada)"
    )

    inv = parse_electricity(text)

    assert inv.reading_p1 is not None
    assert inv.reading_p1.estimated is True


def test_electricity_keeps_the_latest_reading_block(fixture_text):
    older = (
        "Lectura actual (real) (5 de marzo de 2026)\n"
        "Lectura en P1 (punta): 1,00 kWh Consumo en P1: 1,00 kWh\n"
    )

    inv = parse_electricity(older + fixture_text(ELECTRICITY))

    assert inv.reading_p1 == MeterReading(Decimal("10000.00"), _SEPTEMBER, False)


def test_electricity_missing_period_stays_none(fixture_text):
    text = fixture_text(ELECTRICITY).replace(
        "Lectura en P2 (llano): 20.000,00 kWh ", ""
    )

    inv = parse_electricity(text)

    assert inv.reading_p1 is not None
    assert inv.reading_p2 is None
    assert inv.reading_p3 is not None


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("(28 de septiembre de 2026)", "(sin fecha)"),
        ("(28 de septiembre de 2026)", "(31 de febrero de 2026)"),
        (
            "Lectura en P1 (punta): 10.000,00 kWh",
            "Lectura en P1 (punta): 1.0.0,0,0 kWh",
        ),
    ],
)
def test_electricity_bad_reading_never_breaks_the_invoice(fixture_text, old, new):
    inv = parse_electricity(fixture_text(ELECTRICITY).replace(old, new))

    assert inv.total > 0
    assert inv.reading_p1 is None


def test_gas_readings(fixture_text):
    inv = parse_gas(fixture_text(GAS))

    assert inv.reading_m3 == MeterReading(Decimal(1013), date(2026, 9, 7), True)
    assert inv.previous_reading_m3 == MeterReading(
        Decimal(1000), date(2026, 7, 7), False
    )
    assert inv.reading_p1 is None
    assert inv.reading_p2 is None
    assert inv.reading_p3 is None


def test_gas_uses_the_widest_span_when_there_are_several_blocks(fixture_text):
    extra = (
        "Lectura actual: real 1.005 m3 realizada el 07/08/2026\n"
        "Lectura anterior: real 1.002 m3 realizada el 15/07/2026\n"
    )

    inv = parse_gas(fixture_text(GAS) + extra)

    assert inv.reading_m3 == MeterReading(Decimal(1013), date(2026, 9, 7), True)
    assert inv.previous_reading_m3 == MeterReading(
        Decimal(1000), date(2026, 7, 7), False
    )


@pytest.mark.parametrize(
    ("old", "new", "current", "previous"),
    [
        ("estimada 1.013 m3 realizada el 07/09/2026", "estimada", False, True),
        ("realizada el 07/07/2026", "realizada el 32/07/2026", True, False),
        ("real 1.000 m3", "real 1.0.0,0,0 m3", True, False),
    ],
)
def test_gas_bad_reading_never_breaks_the_invoice(
    fixture_text, old, new, current, previous
):
    inv = parse_gas(fixture_text(GAS).replace(old, new))

    assert inv.total > 0
    assert (inv.reading_m3 is not None) is current
    assert (inv.previous_reading_m3 is not None) is previous

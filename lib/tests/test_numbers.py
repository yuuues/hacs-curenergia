from datetime import date
from decimal import Decimal

import pytest

from pycurenergia.numbers import parse_decimal, parse_dmy, parse_spanish_date


@pytest.mark.parametrize(
    "text,expected",
    [
        ("102,55", Decimal("102.55")),
        ("4.156,35", Decimal("4156.35")),
        ("0,000077", Decimal("0.000077")),
        ("-12,34", Decimal("-12.34")),
        ("4,6", Decimal("4.6")),
        ("2.444", Decimal("2444")),
    ],
)
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

"""Pruebas del redondeo compartido (R23)."""

from decimal import Decimal

import pytest

from custom_components.curenergia.util import money, price, price_per_kwh


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("0.565"), 0.57),  # half-even daría 0.56
        (Decimal("0.575"), 0.58),
        (Decimal("0.564"), 0.56),
        (Decimal("2.5"), 2.5),
        (Decimal("-0.565"), -0.57),  # los empates se alejan de cero
        (Decimal("102.55"), 102.55),
        (Decimal(0), 0.0),
    ],
)
def test_money_rounds_half_up(value, expected):
    assert money(value) == expected


def test_price_has_four_decimals():
    assert price(Decimal("0.12345")) == 0.1235  # half-even daría 0.1234
    assert price(Decimal("0.139504")) == 0.1395


def test_none_stays_none():
    assert money(None) is None
    assert price(None) is None


def test_returns_float():
    assert isinstance(money(Decimal("1")), float)
    assert isinstance(price(Decimal("1")), float)


def test_price_per_kwh():
    assert price_per_kwh(Decimal("102.55"), Decimal("380.06")) == 0.2698
    assert price_per_kwh(Decimal("1"), Decimal(0)) is None

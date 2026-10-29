"""Redondeo compartido por los sensores y la API websocket (R23)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def _to_float(value: Decimal | None, places: int) -> float | None:
    """``value`` redondeado a ``places`` decimales (empates hacia arriba)."""
    if value is None:
        return None
    quantum = Decimal(1).scaleb(-places)
    return float(value.quantize(quantum, rounding=ROUND_HALF_UP))


def money(value: Decimal | None) -> float | None:
    """Euros o kWh como ``float`` con 2 decimales."""
    return _to_float(value, 2)


def price(value: Decimal | None) -> float | None:
    """€/kWh como ``float`` con 4 decimales."""
    return _to_float(value, 4)


def price_per_kwh(total: Decimal, kwh: Decimal) -> float | None:
    """Importe total ÷ kWh (€/kWh); ``None`` si no hay kWh."""
    if kwh == 0:
        return None
    return price(total / kwh)

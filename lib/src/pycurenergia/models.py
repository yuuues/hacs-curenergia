"""Modelo de datos de una factura de CurEnergía."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class SupplyType(StrEnum):
    """Tipo de suministro."""

    ELECTRICITY = "electricity"
    GAS = "gas"


class ConceptKey(StrEnum):
    """Clave normalizada de un concepto facturado."""

    POWER = "power"
    ENERGY = "energy"
    SOCIAL_BONUS = "social_bonus"
    ELECTRICITY_TAX = "electricity_tax"
    METER_RENTAL = "meter_rental"
    GAS_FIXED_TERM = "gas_fixed_term"
    GAS_ENERGY = "gas_energy"
    GAS_TAX = "gas_tax"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Concept:
    """Línea de la factura: clave normalizada, etiqueta original e importe (€)."""

    key: ConceptKey
    label: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class Invoice:
    """Factura ya interpretada.

    Todos los importes, kWh, m³ y porcentajes son ``Decimal``. ``concepts`` no
    incluye el IVA, que va en ``vat_rate``, ``vat_base`` y ``vat_amount``;
    ``vat_rate`` es el porcentaje (21 para «21 %»). ``cups`` va sin espacios.
    ``energy_price_kwh`` es el precio de la energía en €/kWh (``None`` si la
    factura no lo indica).
    """

    supply: SupplyType
    number: str
    contract: str
    cups: str
    issue_date: date
    period_start: date
    period_end: date
    estimated: bool
    total: Decimal
    concepts: tuple[Concept, ...]
    vat_rate: Decimal
    vat_base: Decimal
    vat_amount: Decimal
    kwh: Decimal
    tariff: str
    access_tariff: str
    kwh_p1: Decimal | None = None
    kwh_p2: Decimal | None = None
    kwh_p3: Decimal | None = None
    m3: Decimal | None = None
    contracted_power_kw: tuple[Decimal, ...] = ()
    late_interest: Decimal = Decimal(0)
    energy_price_kwh: Decimal | None = None

    def concept_total(self, *keys: ConceptKey) -> Decimal:
        """Suma el importe de los conceptos cuya clave esté en ``keys``."""
        return sum(
            (c.amount for c in self.concepts if c.key in keys),
            start=Decimal(0),
        )

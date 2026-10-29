"""Comprobaciones de coherencia interna de una factura."""

from decimal import Decimal
from enum import StrEnum

from pycurenergia.models import Invoice

TOLERANCE = Decimal("0.01")
"""Tolerancia (inclusiva) en € y kWh por redondeos de la factura."""


class Problem(StrEnum):
    """Incoherencia detectada en una factura."""

    TOTAL_MISMATCH = "total_mismatch"
    VAT_MISMATCH = "vat_mismatch"
    KWH_PERIODS_MISMATCH = "kwh_periods_mismatch"
    PERIOD_INVERTED = "period_inverted"


def check_consistency(invoice: Invoice) -> list[Problem]:
    """Comprueba la coherencia interna de la factura.

    Devuelve la lista de problemas encontrados; vacía si es coherente. Las
    diferencias de hasta 0,01 (inclusive) se aceptan como redondeo. Si solo
    vienen algunos de ``kwh_p1``/``kwh_p2``/``kwh_p3``, se informa
    ``KWH_PERIODS_MISMATCH``; si no viene ninguno (gas), no se comprueban.
    """
    problems: list[Problem] = []

    concepts_sum = sum((c.amount for c in invoice.concepts), start=Decimal(0))
    if abs(concepts_sum + invoice.vat_amount - invoice.total) > TOLERANCE:
        problems.append(Problem.TOTAL_MISMATCH)

    expected_vat = invoice.vat_rate / 100 * invoice.vat_base
    if abs(expected_vat - invoice.vat_amount) > TOLERANCE:
        problems.append(Problem.VAT_MISMATCH)

    periods = [
        p for p in (invoice.kwh_p1, invoice.kwh_p2, invoice.kwh_p3) if p is not None
    ]
    if periods and (
        len(periods) < 3
        or abs(sum(periods, start=Decimal(0)) - invoice.kwh) > TOLERANCE
    ):
        problems.append(Problem.KWH_PERIODS_MISMATCH)

    if invoice.period_start > invoice.period_end:
        problems.append(Problem.PERIOD_INVERTED)

    return problems

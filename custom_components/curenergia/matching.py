"""Casación de facturas con los totales de e-data (lógica pura, sin Home Assistant)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta, tzinfo
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from pycurenergia import ConceptKey, Invoice, SupplyType

if TYPE_CHECKING:
    from .storage import StoredInvoice

_ONE = Decimal(1)
_HUNDRED = Decimal(100)
_ZERO = Decimal(0)
_DAY = timedelta(days=1)

type Periods = tuple[Decimal | None, Decimal | None, Decimal | None]


class Status(StrEnum):
    """Estado de una factura frente a e-data."""

    OK = "ok"
    MISMATCH = "no_cuadra"
    ESTIMATED = "estimada"
    NO_DATA = "sin_datos"
    UNREADABLE = "no_leida"
    GAS = "gas"


@dataclass(frozen=True)
class Totals:
    """Sumas de e-data en una ventana. ``eur`` es ``None`` si no hay costes."""

    kwh: Decimal
    p1: Decimal | None
    p2: Decimal | None
    p3: Decimal | None
    eur: Decimal | None


# Devuelve ``None`` si no hay e-data o la ventana no está cubierta.
type TotalsProvider = Callable[[datetime, datetime], Awaitable[Totals | None]]


@dataclass(frozen=True)
class Thresholds:
    """Umbrales de marcado (estrictos): kWh absolutos y % de diferencia en €."""

    kwh: Decimal
    eur_pct: Decimal


@dataclass(frozen=True)
class Comparison:
    """Factura (o grupo de facturas) frente a e-data en una misma ventana."""

    group: tuple[str, ...]
    window_start: datetime
    window_end: datetime
    invoice_kwh: Decimal
    invoice_periods: Periods
    invoice_eur: Decimal
    edata: Totals
    delta_kwh: Decimal
    delta_periods: Periods
    delta_eur: Decimal | None
    delta_pct: Decimal | None


@dataclass(frozen=True)
class InvoiceRow:
    """Resultado de la casación de una factura guardada."""

    stored: StoredInvoice
    status: Status
    comparison: Comparison | None
    # Número de la factura real que regulariza esta estimada (si ya llegó).
    in_group_of: str | None = None


def invoice_window(start: date, end: date, tz: tzinfo) -> tuple[datetime, datetime]:
    """Ventana ``[start 00:00, end + 1 día 00:00)`` en la zona horaria ``tz``."""
    return (
        datetime.combine(start, time.min, tzinfo=tz),
        datetime.combine(end + _DAY, time.min, tzinfo=tz),
    )


def comparable_eur(invoice: Invoice) -> Decimal:
    """Importe de la factura en la misma base que los costes de e-data (D2).

    ``(potencia + energía) × (1 + impuesto_eléctrico / (potencia + energía +
    bono_social)) × (1 + IVA / 100)``. Si el denominador es 0, el factor del
    impuesto es 1.
    """
    base = invoice.concept_total(ConceptKey.POWER, ConceptKey.ENERGY)
    taxed_base = base + invoice.concept_total(ConceptKey.SOCIAL_BONUS)
    if taxed_base == _ZERO:
        tax_factor = _ONE
    else:
        tax = invoice.concept_total(ConceptKey.ELECTRICITY_TAX)
        tax_factor = _ONE + tax / taxed_base
    return base * tax_factor * (_ONE + invoice.vat_rate / _HUNDRED)


def _sum_period(values: list[Decimal | None]) -> Decimal | None:
    """Suma de un tramo; ``None`` si alguna factura del grupo no lo desglosa."""
    if any(v is None for v in values):
        return None
    return sum(values, start=_ZERO)


def _diff(invoice: Decimal | None, edata: Decimal | None) -> Decimal | None:
    """Factura − e-data; ``None`` si alguno de los dos no tiene el dato."""
    if invoice is None or edata is None:
        return None
    return invoice - edata


async def _compare(
    group: list[StoredInvoice], provider: TotalsProvider, tz: tzinfo
) -> Comparison | None:
    """Compara un grupo contiguo de facturas con e-data en su ventana combinada."""
    invoices = [s.invoice for s in group]
    start, end = invoice_window(invoices[0].period_start, invoices[-1].period_end, tz)
    edata = await provider(start, end)
    if edata is None:
        return None

    invoice_kwh = sum((i.kwh for i in invoices), start=_ZERO)
    invoice_periods: Periods = (
        _sum_period([i.kwh_p1 for i in invoices]),
        _sum_period([i.kwh_p2 for i in invoices]),
        _sum_period([i.kwh_p3 for i in invoices]),
    )
    invoice_eur = sum((comparable_eur(i) for i in invoices), start=_ZERO)

    delta_eur: Decimal | None = None
    delta_pct: Decimal | None = None
    if edata.eur is not None and edata.eur != _ZERO:
        delta_eur = invoice_eur - edata.eur
        delta_pct = delta_eur * _HUNDRED / edata.eur

    return Comparison(
        group=tuple(i.number for i in invoices),
        window_start=start,
        window_end=end,
        invoice_kwh=invoice_kwh,
        invoice_periods=invoice_periods,
        invoice_eur=invoice_eur,
        edata=edata,
        delta_kwh=invoice_kwh - edata.kwh,
        delta_periods=(
            _diff(invoice_periods[0], edata.p1),
            _diff(invoice_periods[1], edata.p2),
            _diff(invoice_periods[2], edata.p3),
        ),
        delta_eur=delta_eur,
        delta_pct=delta_pct,
    )


def _exceeds(comparison: Comparison, thresholds: Thresholds) -> bool:
    """Si alguna diferencia supera estrictamente su umbral."""
    kwh_deltas = (comparison.delta_kwh, *comparison.delta_periods)
    if any(d is not None and abs(d) > thresholds.kwh for d in kwh_deltas):
        return True
    pct = comparison.delta_pct
    return pct is not None and abs(pct) > thresholds.eur_pct


def _contiguous(group: list[StoredInvoice]) -> bool:
    """Si cada factura empieza el día siguiente al final de la anterior."""
    return all(
        cur.invoice.period_start == prev.invoice.period_end + _DAY
        for prev, cur in zip(group, group[1:], strict=False)
    )


async def match_contract(
    rows: list[StoredInvoice],
    provider: TotalsProvider,
    thresholds: Thresholds,
    tz: tzinfo,
) -> list[InvoiceRow]:
    """Casa las facturas de un contrato con e-data; filas ordenadas por periodo.

    Las estimadas se acumulan en un grupo pendiente que cierra la siguiente
    factura real: se compara la ventana combinada de todo el grupo (D8: si el
    grupo tiene un hueco, una ``no_leida`` o empieza en la estimada más antigua
    guardada, la real queda ``sin_datos``). Las estimadas se marcan siempre
    ``estimada``; las ``no_leida`` también estropean el grupo en curso.
    """
    ordered = sorted(
        rows,
        key=lambda s: (s.invoice.period_start, s.invoice.period_end, s.invoice.number),
    )
    result: list[InvoiceRow] = []
    pending: list[int] = []  # índices (en ``result``) de las estimadas del grupo
    tainted = False  # el grupo en curso contiene una factura ilegible

    for stored in ordered:
        invoice = stored.invoice

        if invoice.supply is SupplyType.GAS:
            result.append(InvoiceRow(stored, Status.GAS, None))
            continue

        if stored.unreadable:
            comparison = await _compare([stored], provider, tz)
            result.append(InvoiceRow(stored, Status.UNREADABLE, comparison))
            # Una ilegible dentro de un grupo (o que pudo ser estimada) impide
            # fiarse de la suma de kWh del grupo.
            if pending or invoice.estimated:
                tainted = True
            continue

        if invoice.estimated:
            comparison = await _compare([stored], provider, tz)
            pending.append(len(result))
            result.append(InvoiceRow(stored, Status.ESTIMATED, comparison))
            continue

        # Factura real: cierra el grupo pendiente (si lo hay).
        group = [result[i].stored for i in pending] + [stored]
        closable = (
            not tainted
            and _contiguous(group)
            # La primera estimada guardada es la más antigua del contrato: no se
            # sabe si había estimadas anteriores sin guardar.
            and not (pending and pending[0] == 0)
        )
        comparison = await _compare(group, provider, tz) if closable else None
        if comparison is None:
            status = Status.NO_DATA
        elif _exceeds(comparison, thresholds):
            status = Status.MISMATCH
        else:
            status = Status.OK
        result.append(InvoiceRow(stored, status, comparison))

        for i in pending:
            result[i] = replace(result[i], in_group_of=invoice.number)
        pending = []
        tainted = False

    return result

"""Tests de la casación de facturas con los totales de e-data.

Los periodos siguen el formato real de CurEnergía: una factura ``D1 a D2`` va
seguida de otra que empieza en ``D2`` (comparten la fecha de la lectura).
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from pycurenergia import Concept, ConceptKey, SupplyType

from custom_components.curenergia.matching import (
    Status,
    Thresholds,
    Totals,
    comparable_eur,
    invoice_window,
    match_contract,
)
from custom_components.curenergia.storage import StoredInvoice, build_stored
from tests.helpers import load_fixture_invoice, make_invoice

MADRID = ZoneInfo("Europe/Madrid")
THRESHOLDS = Thresholds(kwh=Decimal(1))
D = Decimal


def stored(number, start, end, *, estimated=False, **changes):
    """Factura guardada con periodo [start, end] y kWh sin desglose por defecto."""
    changes.setdefault("kwh", D(100))
    changes.setdefault("kwh_p1", None)
    changes.setdefault("kwh_p2", None)
    changes.setdefault("kwh_p3", None)
    invoice = make_invoice(
        number=number,
        period_start=start,
        period_end=end,
        estimated=estimated,
        **changes,
    )
    # Sin build_stored: los kWh/€ inventados no pasarían las comprobaciones.
    return StoredInvoice(invoice=invoice, problems=[], email_total=None)


def window_of(s: StoredInvoice):
    inv = s.invoice
    return invoice_window(inv.period_start, inv.period_end, MADRID)


def totals(kwh, p1=None, p2=None, p3=None, eur=None, *, complete=True):
    return Totals(
        kwh=D(kwh),
        p1=None if p1 is None else D(p1),
        p2=None if p2 is None else D(p2),
        p3=None if p3 is None else D(p3),
        eur=None if eur is None else D(eur),
        complete=complete,
    )


def fake_provider(mapping):
    """Proveedor falso: ``{(inicio, fin): Totals}``; ``None`` si la ventana no está."""

    async def provider(start: datetime, end: datetime):
        return mapping.get((start, end))

    return provider


async def run(rows, mapping, thresholds=THRESHOLDS):
    return await match_contract(rows, fake_provider(mapping), thresholds, MADRID)


# ---------------------------------------------------------------- funciones sueltas


def test_invoice_window_starts_the_day_after_the_first_reading():
    """La lectura de D1 cierra la factura anterior: ``[D1+1 00:00, D2+1 00:00)``."""
    s, e = invoice_window(date(2026, 8, 29), date(2026, 9, 28), MADRID)
    assert (s.isoformat(), e.isoformat()) == (
        "2026-08-30T00:00:00+02:00",
        "2026-09-29T00:00:00+02:00",
    )


def test_invoice_window_spans_dst_change():
    s, e = invoice_window(date(2026, 9, 30), date(2026, 10, 31), MADRID)
    assert (s.isoformat(), e.isoformat()) == (
        "2026-10-01T00:00:00+02:00",
        "2026-11-01T00:00:00+01:00",
    )
    assert e.astimezone(UTC) - s.astimezone(UTC) == timedelta(hours=745)


def test_comparable_eur_grosses_up_taxes():
    inv = make_invoice(
        concepts=(
            Concept(ConceptKey.POWER, "p", D("10")),
            Concept(ConceptKey.ENERGY, "e", D("40")),
            Concept(ConceptKey.SOCIAL_BONUS, "b", D("0")),
            Concept(ConceptKey.ELECTRICITY_TAX, "t", D("2.5")),
        ),
        vat_rate=D("21"),
    )
    assert comparable_eur(inv) == D("50") * D("1.05") * D("1.21")


def test_comparable_eur_with_social_bonus_in_tax_base():
    inv = make_invoice(
        concepts=(
            Concept(ConceptKey.POWER, "p", D("10")),
            Concept(ConceptKey.ENERGY, "e", D("40")),
            Concept(ConceptKey.SOCIAL_BONUS, "b", D("-10")),
            Concept(ConceptKey.ELECTRICITY_TAX, "t", D("2")),
            Concept(ConceptKey.METER_RENTAL, "m", D("1")),
        ),
        vat_rate=D("21"),
    )
    # (10 + 40) * (1 + 2 / (10 + 40 - 10)) * 1.21
    assert comparable_eur(inv) == D("50") * D("1.05") * D("1.21")


def test_comparable_eur_zero_base_means_tax_factor_one():
    inv = make_invoice(
        concepts=(
            Concept(ConceptKey.POWER, "p", D("10")),
            Concept(ConceptKey.ENERGY, "e", D("0")),
            Concept(ConceptKey.SOCIAL_BONUS, "b", D("-10")),
            Concept(ConceptKey.ELECTRICITY_TAX, "t", D("0.5")),
        ),
        vat_rate=D("21"),
    )
    assert comparable_eur(inv) == D("10") * D("1") * D("1.21")


def test_comparable_eur_on_fixture_is_positive():
    assert comparable_eur(load_fixture_invoice("electricity_2026-10")) > 0


# ------------------------------------------------------------- facturas reales


async def test_real_invoice_within_threshold_is_ok():
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4))
    mapping = {window_of(r): totals(101)}  # Δ = -1 exacto
    [row] = await run([r], mapping)
    assert row.status is Status.OK
    assert row.in_group_of is None
    assert row.comparison.delta_kwh == D(-1)
    assert row.comparison.group == ("R",)


async def test_real_invoice_over_kwh_threshold_is_mismatch():
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4))
    mapping = {window_of(r): totals("101.01")}  # Δ = -1.01
    [row] = await run([r], mapping)
    assert row.status is Status.MISMATCH
    assert row.comparison.delta_kwh == D("-1.01")


async def test_single_period_over_threshold_is_mismatch():
    r = stored(
        "R",
        date(2026, 9, 4),
        date(2026, 10, 4),
        kwh_p1=D(40),
        kwh_p2=D(30),
        kwh_p3=D(30),
    )
    mapping = {window_of(r): totals(100, p1=40, p2="28.5", p3="31.5")}
    [row] = await run([r], mapping)
    assert row.status is Status.MISMATCH
    assert row.comparison.delta_kwh == D(0)
    assert row.comparison.delta_periods == (D(0), D("1.5"), D("-1.5"))


async def test_period_compared_only_when_both_have_it():
    r = stored(
        "R",
        date(2026, 9, 4),
        date(2026, 10, 4),
        kwh_p1=D(100),
        kwh_p2=None,
        kwh_p3=None,
    )
    # e-data trae P2 muy distinto, pero la factura no lo desglosa; y viceversa.
    mapping = {window_of(r): totals(100, p1=100, p2=50, p3=None)}
    [row] = await run([r], mapping)
    assert row.status is Status.OK
    assert row.comparison.invoice_periods == (D(100), None, None)
    assert row.comparison.delta_periods == (D(0), None, None)


async def test_period_equal_to_threshold_is_ok():
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4), kwh_p1=D(100))
    mapping = {window_of(r): totals(100, p1=99)}  # Δ P1 = +1 exacto
    [row] = await run([r], mapping)
    assert row.status is Status.OK


def eur_invoice(amount):
    """Factura cuyo importe comparable es exactamente ``amount``."""
    return stored(
        "R",
        date(2026, 9, 4),
        date(2026, 10, 4),
        concepts=(Concept(ConceptKey.ENERGY, "e", D(amount)),),
        vat_rate=D(0),
    )


async def test_eur_delta_is_informational_and_never_marks():
    """Δ € y Δ % se calculan y se muestran, pero no deciden el estado."""
    r = eur_invoice("110")
    [row] = await run([r], {window_of(r): totals("99.5", eur=100)})
    assert row.status is Status.OK
    assert row.comparison.delta_kwh == D("0.5")
    assert row.comparison.delta_eur == D(10)
    assert row.comparison.delta_pct == D(10)


async def test_negative_eur_delta_is_informational():
    r = eur_invoice("97.00")
    [row] = await run([r], {window_of(r): totals(100, eur=100)})
    assert row.status is Status.OK
    assert row.comparison.delta_pct == D("-3")


async def test_kwh_over_threshold_marks_even_with_matching_eur():
    r = eur_invoice("100")
    [row] = await run([r], {window_of(r): totals("98.5", eur=100)})
    assert row.status is Status.MISMATCH
    assert row.comparison.delta_kwh == D("1.5")
    assert row.comparison.delta_pct == D(0)


async def test_missing_edata_costs_ignored():
    r = eur_invoice("500")
    [row] = await run([r], {window_of(r): totals(100, eur=None)})
    assert row.status is Status.OK
    assert row.comparison.delta_eur is None
    assert row.comparison.delta_pct is None
    assert row.comparison.edata.eur is None


async def test_zero_edata_cost_ignored():
    r = eur_invoice("500")
    [row] = await run([r], {window_of(r): totals(100, eur=0)})
    assert row.status is Status.OK
    assert row.comparison.delta_eur is None
    assert row.comparison.delta_pct is None


async def test_missing_edata_costs_still_flags_kwh():
    r = eur_invoice("500")
    [row] = await run([r], {window_of(r): totals(150, eur=None)})
    assert row.status is Status.MISMATCH


async def test_incomplete_window_over_threshold_is_no_data():
    """R24: con horas sin dato en e-data, un descuadre no se puede afirmar."""
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4))
    [row] = await run([r], {window_of(r): totals(150, complete=False)})
    assert row.status is Status.NO_DATA
    assert row.comparison is not None
    assert row.comparison.delta_kwh == D(-50)


async def test_incomplete_window_kwh_over_threshold_is_no_data():
    r = eur_invoice("100")
    [row] = await run([r], {window_of(r): totals("98.5", eur=100, complete=False)})
    assert row.status is Status.NO_DATA
    assert row.comparison.delta_kwh == D("1.5")


async def test_incomplete_window_with_only_eur_delta_is_ok():
    r = eur_invoice("110")
    [row] = await run([r], {window_of(r): totals(100, eur=100, complete=False)})
    assert row.status is Status.OK


async def test_incomplete_window_within_threshold_is_ok():
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4))
    [row] = await run([r], {window_of(r): totals(101, complete=False)})
    assert row.status is Status.OK


async def test_incomplete_combined_window_over_threshold_is_no_data():
    r0 = stored("R0", date(2026, 7, 4), date(2026, 8, 4))
    e = stored("E", date(2026, 8, 4), date(2026, 9, 4), estimated=True)
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4))
    combined = invoice_window(date(2026, 8, 4), date(2026, 10, 4), MADRID)
    rows = await run([r0, e, r], {combined: totals(210, complete=False)})
    assert rows[2].status is Status.NO_DATA
    assert rows[2].comparison.group == ("E", "R")
    assert rows[1].in_group_of == "R"


async def test_provider_none_is_no_data():
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4))
    [row] = await run([r], {})
    assert row.status is Status.NO_DATA
    assert row.comparison is None


# ------------------------------------------------------------------- contigüidad


async def test_reals_sharing_the_boundary_date_are_contiguous():
    """CurEnergía: la siguiente factura empieza el día en que acabó la anterior."""
    r0 = stored("R0", date(2026, 7, 29), date(2026, 8, 29))
    r = stored("R", date(2026, 8, 29), date(2026, 9, 28))
    mapping = {window_of(r0): totals(100), window_of(r): totals(100)}
    rows = await run([r0, r], mapping)
    assert [x.status for x in rows] == [Status.OK, Status.OK]
    assert rows[1].comparison is not None
    assert rows[1].comparison.group == ("R",)
    assert rows[1].comparison.window_start.isoformat() == "2026-08-30T00:00:00+02:00"
    assert rows[1].comparison.window_end.isoformat() == "2026-09-29T00:00:00+02:00"
    # Las ventanas de dos facturas seguidas no se solapan ni dejan hueco.
    assert rows[0].comparison.window_end == rows[1].comparison.window_start


async def test_real_starting_after_previous_end_is_a_gap():
    """R25: ``next.start > prev.end`` es un hueco (falta una factura)."""
    r0 = stored("R0", date(2026, 7, 29), date(2026, 8, 29))
    r = stored("R", date(2026, 9, 5), date(2026, 9, 28))
    rows = await run([r0, r], {window_of(r0): totals(100), window_of(r): totals(100)})
    assert rows[0].status is Status.OK
    assert rows[1].status is Status.NO_DATA
    assert rows[1].comparison is None


async def test_old_next_day_layout_is_a_one_day_gap():
    """Empezar el día después del final anterior deja un día sin facturar."""
    r0 = stored("R0", date(2026, 7, 29), date(2026, 8, 28))
    r = stored("R", date(2026, 8, 29), date(2026, 9, 28))
    rows = await run([r0, r], {window_of(r0): totals(100), window_of(r): totals(100)})
    assert rows[0].status is Status.OK
    assert rows[1].status is Status.NO_DATA
    assert rows[1].comparison is None


async def test_old_next_day_layout_does_not_link_estimated():
    r0 = stored("R0", date(2026, 6, 29), date(2026, 7, 29))
    e = stored("E", date(2026, 7, 30), date(2026, 8, 28), estimated=True)
    r = stored("R", date(2026, 8, 29), date(2026, 9, 28))
    combined = invoice_window(date(2026, 7, 30), date(2026, 9, 28), MADRID)
    rows = await run([r0, e, r], {combined: totals(200)})
    assert rows[1].in_group_of is None
    assert rows[2].status is Status.NO_DATA


# ---------------------------------------------------------------- estimadas


async def test_estimated_never_mismatch():
    e = stored("E", date(2026, 9, 4), date(2026, 10, 4), estimated=True)
    [row] = await run([e], {window_of(e): totals(150)})  # Δ = -50 kWh
    assert row.status is Status.ESTIMATED
    assert row.in_group_of is None
    assert row.comparison is not None
    assert row.comparison.group == ("E",)
    assert row.comparison.delta_kwh == D(-50)


async def test_estimated_without_edata_has_no_comparison():
    e = stored("E", date(2026, 9, 4), date(2026, 10, 4), estimated=True)
    [row] = await run([e], {})
    assert row.status is Status.ESTIMATED
    assert row.comparison is None


async def test_trailing_estimated_waits():
    r = stored("R", date(2026, 8, 4), date(2026, 9, 4))
    e = stored("E", date(2026, 9, 4), date(2026, 10, 4), estimated=True)
    rows = await run([r, e], {window_of(r): totals(100)})
    assert [x.status for x in rows] == [Status.OK, Status.ESTIMATED]
    assert rows[1].in_group_of is None


async def test_real_after_estimates_uses_combined_window():
    r0 = stored("R0", date(2026, 6, 4), date(2026, 7, 4))
    e1 = stored(
        "E1",
        date(2026, 7, 4),
        date(2026, 8, 4),
        estimated=True,
        kwh=D(100),
        kwh_p1=D(10),
        kwh_p2=D(20),
        kwh_p3=D(70),
    )
    e2 = stored(
        "E2",
        date(2026, 8, 4),
        date(2026, 9, 4),
        estimated=True,
        kwh=D(100),
        kwh_p1=D(10),
        kwh_p2=D(20),
        kwh_p3=D(70),
    )
    r = stored(
        "R",
        date(2026, 9, 4),
        date(2026, 10, 4),
        kwh=D(150),
        kwh_p1=D(30),
        kwh_p2=D(40),
        kwh_p3=D(80),
    )
    combined = invoice_window(date(2026, 7, 4), date(2026, 10, 4), MADRID)
    mapping = {
        window_of(r0): totals(100),
        combined: totals(350, p1=50, p2=80, p3=220),
    }
    rows = await run([r, e2, r0, e1], mapping)  # desordenadas a propósito
    assert [x.stored.invoice.number for x in rows] == ["R0", "E1", "E2", "R"]
    r0_row, e1_row, e2_row, r_row = rows

    assert r0_row.status is Status.OK
    assert (e1_row.status, e2_row.status) == (Status.ESTIMATED, Status.ESTIMATED)
    assert e1_row.in_group_of == "R"
    assert e2_row.in_group_of == "R"
    assert e1_row.comparison is None  # su ventana propia no está en el proveedor

    assert r_row.status is Status.OK
    assert r_row.in_group_of is None
    c = r_row.comparison
    assert c.group == ("E1", "E2", "R")
    assert (c.window_start, c.window_end) == combined
    # Del día siguiente al inicio de la primera estimada al siguiente al fin real.
    assert c.window_start.isoformat() == "2026-07-05T00:00:00+02:00"
    assert c.window_end.isoformat() == "2026-10-05T00:00:00+02:00"
    assert c.invoice_kwh == D(350)
    assert c.invoice_periods == (D(50), D(80), D(220))
    assert c.delta_kwh == D(0)
    assert c.delta_periods == (D(0), D(0), D(0))


async def test_combined_window_mismatch():
    e = stored("E", date(2026, 8, 4), date(2026, 9, 4), estimated=True)
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4))
    combined = invoice_window(date(2026, 8, 4), date(2026, 10, 4), MADRID)
    rows = await run(
        [stored("R0", date(2026, 7, 4), date(2026, 8, 4)), e, r],
        {combined: totals(210)},  # factura suma 200 → Δ -10
    )
    assert rows[2].status is Status.MISMATCH
    assert rows[2].comparison.group == ("E", "R")
    assert rows[2].comparison.delta_kwh == D(-10)
    assert rows[1].in_group_of == "R"


async def test_estimated_own_comparison_present_inside_closed_group():
    r0 = stored("R0", date(2026, 7, 4), date(2026, 8, 4))
    e = stored("E", date(2026, 8, 4), date(2026, 9, 4), estimated=True)
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4))
    combined = invoice_window(date(2026, 8, 4), date(2026, 10, 4), MADRID)
    rows = await run([r0, e, r], {window_of(e): totals(90), combined: totals(200)})
    assert rows[1].status is Status.ESTIMATED
    assert rows[1].comparison.delta_kwh == D(10)
    assert rows[1].in_group_of == "R"
    assert rows[2].status is Status.OK


async def test_two_groups_in_a_row():
    rows_in = [
        stored("R0", date(2025, 12, 31), date(2026, 1, 31)),
        stored("E1", date(2026, 1, 31), date(2026, 2, 28), estimated=True),
        stored("R1", date(2026, 2, 28), date(2026, 3, 31)),
        stored("E2", date(2026, 3, 31), date(2026, 4, 30), estimated=True),
        stored("R2", date(2026, 4, 30), date(2026, 5, 31)),
    ]
    g1 = invoice_window(date(2026, 1, 31), date(2026, 3, 31), MADRID)
    g2 = invoice_window(date(2026, 3, 31), date(2026, 5, 31), MADRID)
    rows = await run(rows_in, {g1: totals(200), g2: totals(500)})
    assert [x.status for x in rows] == [
        Status.NO_DATA,  # R0: sin e-data
        Status.ESTIMATED,
        Status.OK,
        Status.ESTIMATED,
        Status.MISMATCH,  # 200 de factura frente a 500
    ]
    assert rows[1].in_group_of == "R1"
    assert rows[3].in_group_of == "R2"
    assert rows[2].comparison.group == ("E1", "R1")
    assert rows[4].comparison.group == ("E2", "R2")


# ------------------------------------------------- grupos que no se pueden cerrar


async def test_group_with_gap_is_no_data():
    r0 = stored("R0", date(2026, 6, 4), date(2026, 7, 4))
    e = stored("E", date(2026, 7, 4), date(2026, 8, 4), estimated=True)
    r = stored("R", date(2026, 8, 6), date(2026, 9, 4))  # faltan 2 días
    combined = invoice_window(date(2026, 7, 4), date(2026, 9, 4), MADRID)
    rows = await run([r0, e, r], {combined: totals(200)})
    assert rows[2].status is Status.NO_DATA
    assert rows[2].comparison is None
    assert rows[1].status is Status.ESTIMATED
    # Con el hueco, la factura que falta pudo ser la que regularizó a E.
    assert rows[1].in_group_of is None


async def test_first_estimated_not_contiguous_with_previous_is_no_data():
    r0 = stored("R0", date(2025, 12, 31), date(2026, 1, 31))
    e = stored("E", date(2026, 2, 28), date(2026, 3, 31), estimated=True)  # falta feb
    r = stored("R", date(2026, 3, 31), date(2026, 4, 30))
    combined = invoice_window(date(2026, 2, 28), date(2026, 4, 30), MADRID)
    rows = await run([r0, e, r], {combined: totals(200)})
    assert rows[2].status is Status.NO_DATA
    assert rows[2].comparison is None
    assert rows[1].status is Status.ESTIMATED
    assert rows[1].in_group_of is None


async def test_real_after_a_gap_is_no_data():
    """R25: falta la factura anterior; pudo regularizar lo que trae esta."""
    r0 = stored("R0", date(2025, 12, 31), date(2026, 1, 31))
    r = stored("R", date(2026, 2, 28), date(2026, 3, 31))  # falta feb
    rows = await run([r0, r], {window_of(r0): totals(100), window_of(r): totals(100)})
    # La más antigua guardada se sigue comparando.
    assert rows[0].status is Status.OK
    assert rows[1].status is Status.NO_DATA
    assert rows[1].comparison is None
    assert rows[1].in_group_of is None


async def test_real_overlapping_previous_is_no_data():
    r0 = stored("R0", date(2025, 12, 31), date(2026, 1, 31))
    r = stored("R", date(2026, 1, 30), date(2026, 2, 28))  # solapa un día
    rows = await run([r0, r], {window_of(r): totals(100)})
    assert rows[1].status is Status.NO_DATA


async def test_real_after_a_gap_following_an_unreadable_is_no_data():
    """La ilegible también cuenta como factura anterior guardada."""
    u = unreadable("U", date(2025, 12, 31), date(2026, 1, 31), estimated=False)
    r = stored("R", date(2026, 2, 28), date(2026, 3, 31))
    rows = await run([u, r], {window_of(r): totals(100)})
    assert rows[0].status is Status.UNREADABLE
    assert rows[1].status is Status.NO_DATA


async def test_real_contiguous_with_an_unreadable_is_compared():
    u = unreadable("U", date(2025, 12, 31), date(2026, 1, 31), estimated=False)
    r = stored("R", date(2026, 1, 31), date(2026, 2, 28))
    rows = await run([u, r], {window_of(r): totals(100)})
    assert rows[1].status is Status.OK


async def test_unreadable_real_after_a_gap_stays_unreadable():
    r0 = stored("R0", date(2025, 12, 31), date(2026, 1, 31))
    u = unreadable("U", date(2026, 2, 28), date(2026, 3, 31), estimated=False)
    rows = await run([r0, u], {window_of(u): totals(100)})
    assert rows[1].status is Status.UNREADABLE
    assert rows[1].comparison is not None


async def test_gap_between_two_estimated_is_no_data():
    r0 = stored("R0", date(2026, 5, 4), date(2026, 6, 4))
    e1 = stored("E1", date(2026, 6, 4), date(2026, 7, 4), estimated=True)
    e2 = stored("E2", date(2026, 8, 4), date(2026, 9, 4), estimated=True)
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4))
    everything = invoice_window(date(2026, 6, 4), date(2026, 10, 4), MADRID)
    rows = await run([r0, e1, e2, r], {everything: totals(300)})
    assert rows[3].status is Status.NO_DATA
    assert rows[1].in_group_of is None
    assert rows[2].in_group_of is None


async def test_overlap_is_not_contiguous():
    r0 = stored("R0", date(2026, 5, 4), date(2026, 6, 4))
    e = stored("E", date(2026, 6, 4), date(2026, 7, 4), estimated=True)
    r = stored("R", date(2026, 7, 3), date(2026, 8, 4))  # solapa un día
    rows = await run(
        [r0, e, r],
        {invoice_window(date(2026, 6, 4), date(2026, 8, 4), MADRID): totals(200)},
    )
    assert rows[2].status is Status.NO_DATA
    assert rows[1].in_group_of is None


async def test_group_starting_at_oldest_estimated_is_no_data():
    e = stored("E", date(2026, 7, 4), date(2026, 8, 4), estimated=True)
    r = stored("R", date(2026, 8, 4), date(2026, 9, 4))
    combined = invoice_window(date(2026, 7, 4), date(2026, 9, 4), MADRID)
    rows = await run([e, r], {combined: totals(200)})
    assert rows[0].status is Status.ESTIMATED
    assert rows[1].status is Status.NO_DATA
    assert rows[1].comparison is None
    assert rows[0].in_group_of == "R"  # contiguo: la real sí las regulariza


def unreadable(number, start, end, *, estimated):
    """Factura ilegible (con incoherencias) de periodo [start, end]."""
    return StoredInvoice(
        invoice=make_invoice(
            number=number,
            period_start=start,
            period_end=end,
            estimated=estimated,
            kwh=D(100),
            kwh_p1=None,
            kwh_p2=None,
            kwh_p3=None,
        ),
        problems=["sum_mismatch"],
        email_total=None,
    )


async def test_unreadable_estimated_in_group_is_no_data():
    r0 = stored("R0", date(2026, 6, 4), date(2026, 7, 4))
    e = stored("E", date(2026, 7, 4), date(2026, 8, 4), estimated=True)
    u = unreadable("U", date(2026, 8, 4), date(2026, 9, 4), estimated=True)
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4))
    combined = invoice_window(date(2026, 7, 4), date(2026, 10, 4), MADRID)
    rows = await run([r0, e, u, r], {combined: totals(300)})
    assert rows[2].status is Status.UNREADABLE
    assert rows[3].status is Status.NO_DATA
    assert rows[3].comparison is None
    assert rows[1].in_group_of == "R"
    assert rows[2].in_group_of == "R"


async def test_unreadable_estimated_alone_makes_closing_real_no_data():
    r0 = stored("R0", date(2026, 6, 4), date(2026, 7, 4))
    u = unreadable("U", date(2026, 7, 4), date(2026, 8, 4), estimated=True)
    r = stored("R", date(2026, 8, 4), date(2026, 9, 4))
    combined = invoice_window(date(2026, 7, 4), date(2026, 9, 4), MADRID)
    rows = await run([r0, u, r], {combined: totals(200)})
    assert rows[1].status is Status.UNREADABLE
    assert rows[1].in_group_of == "R"
    assert rows[2].status is Status.NO_DATA


async def test_unreadable_real_closes_open_group():
    r0 = stored("R0", date(2026, 6, 4), date(2026, 7, 4))
    e = stored("E", date(2026, 7, 4), date(2026, 8, 4), estimated=True)
    u = unreadable("U", date(2026, 8, 4), date(2026, 9, 4), estimated=False)
    r = stored("R", date(2026, 9, 4), date(2026, 10, 4))
    rows = await run([r0, e, u, r], {window_of(r): totals(100)})
    assert rows[1].status is Status.ESTIMATED
    assert rows[1].in_group_of == "U"
    assert rows[2].status is Status.UNREADABLE
    assert rows[2].in_group_of is None
    # La siguiente real empieza un grupo nuevo, comparada en su propia ventana.
    assert rows[3].status is Status.OK
    assert rows[3].comparison.group == ("R",)


async def test_unreadable_real_closing_group_keeps_own_comparison():
    e = stored("E", date(2026, 7, 4), date(2026, 8, 4), estimated=True)
    u = unreadable("U", date(2026, 8, 4), date(2026, 9, 4), estimated=False)
    rows = await run([e, u], {window_of(u): totals(120)})
    assert rows[1].status is Status.UNREADABLE
    assert rows[1].comparison.group == ("U",)
    assert rows[1].comparison.delta_kwh == D(-20)
    assert rows[0].in_group_of == "U"


async def test_unreadable_real_across_a_gap_does_not_link_estimated():
    r0 = stored("R0", date(2026, 6, 4), date(2026, 7, 4))
    e = stored("E", date(2026, 7, 4), date(2026, 8, 4), estimated=True)
    u = unreadable("U", date(2026, 8, 9), date(2026, 9, 4), estimated=False)
    rows = await run([r0, e, u], {})
    assert rows[2].status is Status.UNREADABLE
    assert rows[1].in_group_of is None


async def test_unreadable_has_own_comparison_when_provider_has_it():
    u = StoredInvoice(
        invoice=make_invoice(
            number="U",
            period_start=date(2026, 8, 4),
            period_end=date(2026, 9, 4),
            kwh=D(100),
            kwh_p1=None,
            kwh_p2=None,
            kwh_p3=None,
        ),
        problems=["sum_mismatch"],
        email_total=None,
    )
    [row] = await run([u], {window_of(u): totals(120)})
    assert row.status is Status.UNREADABLE
    assert row.comparison is not None
    assert row.comparison.delta_kwh == D(-20)


async def test_unreadable_without_edata_has_no_comparison():
    u = StoredInvoice(
        invoice=make_invoice(number="U"), problems=["x"], email_total=None
    )
    [row] = await run([u], {})
    assert row.status is Status.UNREADABLE
    assert row.comparison is None


async def test_unreadable_real_between_reals_does_not_taint_next_real():
    r0 = stored("R0", date(2026, 6, 4), date(2026, 7, 4))
    u = StoredInvoice(
        invoice=make_invoice(
            number="U",
            period_start=date(2026, 7, 4),
            period_end=date(2026, 8, 4),
            estimated=False,
        ),
        problems=["x"],
        email_total=None,
    )
    r = stored("R", date(2026, 8, 4), date(2026, 9, 4))
    rows = await run([r0, u, r], {window_of(r): totals(100)})
    assert rows[1].status is Status.UNREADABLE
    assert rows[2].status is Status.OK


# ----------------------------------------------------------------------- gas


async def test_gas_rows_are_gas():
    g1 = build_stored(load_fixture_invoice("gas_2026-09"), None)
    assert g1.invoice.supply is SupplyType.GAS
    rows = await run([g1], {})
    assert [(x.status, x.comparison, x.in_group_of) for x in rows] == [
        (Status.GAS, None, None)
    ]


async def test_gas_provider_is_never_called():
    g1 = build_stored(load_fixture_invoice("gas_2026-09"), None)
    calls = []

    async def provider(start, end):
        calls.append((start, end))

    rows = await match_contract([g1], provider, THRESHOLDS, MADRID)
    assert rows[0].status is Status.GAS
    assert calls == []


async def test_empty_contract():
    assert await run([], {}) == []

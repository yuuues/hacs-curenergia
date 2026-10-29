"""Pruebas de la API websocket de facturas y resumen."""

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pycurenergia import InvoiceParseError, UnsupportedInvoiceError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.curenergia.const import DOMAIN
from custom_components.curenergia.mail import MailConnectionError
from custom_components.curenergia.matching import Totals, comparable_eur
from custom_components.curenergia.util import money, price

from .helpers import FakeMailbox, fake_totals, make_entry, setup_entry

pytestmark = pytest.mark.usefixtures("recorder_mock", "enable_custom_integrations")

ROW_KEYS = {
    "number",
    "supply",
    "issue_date",
    "period_start",
    "period_end",
    "estimated",
    "status",
    "problems",
    "total",
    "kwh",
    "price_kwh",
    "m3",
    "energy_price_kwh",
    "periods",
    "concepts",
    "vat",
    "in_group_of",
    "comparison",
}
COMPARISON_KEYS = {
    "group",
    "window_start",
    "window_end",
    "invoice_kwh",
    "invoice_periods",
    "invoice_eur",
    "edata_kwh",
    "edata_periods",
    "edata_eur",
    "delta_kwh",
    "delta_periods",
    "delta_eur",
    "delta_pct",
}
# El reloj se congela al empezar el test: así el token del cliente websocket
# (creado por la fixture) sigue siendo válido.
FROZEN = pytest.mark.freeze_time("2026-10-29 12:00:00+00:00")

CONTRACT_KEYS = {"entry_id", "contract", "supply", "name", "invoices"}
SUMMARY_KEYS = {
    "billed_12m",
    "kwh_delta_pct",
    "estimated_count",
    "unreadable_emails",
    "unsupported_emails",
    "last_mail_check",
    "mail_error",
}


async def _call(hass: HomeAssistant, hass_ws_client, **payload: Any) -> dict[str, Any]:
    """Envía una orden al websocket y devuelve la respuesta completa."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(payload)
    return await client.receive_json()


def _by_supply(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["supply"]: item for item in result["contracts"]}


async def test_ws_invoices_shape(
    hass: HomeAssistant,
    hass_ws_client,
    mailbox: FakeMailbox,
    make_invoice,
    fixture_invoice,
    madrid_tz,
):
    older = make_invoice(
        number="OLD-1",
        issue_date=date(2026, 9, 5),
        period_start=date(2026, 7, 29),
        period_end=date(2026, 8, 28),
    )
    latest = make_invoice()
    gas = fixture_invoice("gas_2026-09")
    mailbox.add(1, (b"old", older))
    mailbox.add(2, (b"new", latest))
    mailbox.add(3, (b"gas", gas))
    entry = make_entry()
    totals = Totals(
        kwh=Decimal("379.555"),
        p1=Decimal("107.11"),
        p2=Decimal("100.16"),
        p3=None,
        eur=Decimal(80),
    )

    with fake_totals(lambda start, end: totals):
        await setup_entry(hass, entry)
        response = await _call(hass, hass_ws_client, type="curenergia/invoices")

    assert response["success"] is True
    contracts = response["result"]["contracts"]
    assert set(response["result"]) == {"contracts"}
    assert len(contracts) == 2
    for item in contracts:
        assert set(item) == CONTRACT_KEYS
        assert item["entry_id"] == entry.entry_id
        for row in item["invoices"]:
            assert set(row) == ROW_KEYS
    by_supply = _by_supply(response["result"])

    electricity = by_supply["electricity"]
    assert electricity["contract"] == latest.contract
    assert electricity["name"] == "CurEnergía luz"
    # De la más reciente a la más antigua.
    assert [row["number"] for row in electricity["invoices"]] == [
        latest.number,
        "OLD-1",
    ]
    invoice_eur = comparable_eur(latest)
    expected = {
        "number": latest.number,
        "supply": "electricity",
        "issue_date": "2026-10-06",
        "period_start": "2026-08-29",
        "period_end": "2026-09-28",
        "estimated": False,
        "status": "no_cuadra",
        "problems": [],
        "total": 102.55,
        "kwh": 380.06,
        "price_kwh": 0.2698,
        "m3": None,
        "energy_price_kwh": 0.1395,
        "periods": {"p1": 107.11, "p2": 104.16, "p3": 168.79},
        "concepts": [
            {"key": c.key.value, "label": c.label, "amount": money(c.amount)}
            for c in latest.concepts
        ],
        "vat": {"rate": 21.0, "base": 84.63, "amount": 17.77},
        "in_group_of": None,
        "comparison": {
            "group": [latest.number],
            "window_start": "2026-08-29T00:00:00+02:00",
            "window_end": "2026-09-29T00:00:00+02:00",
            "invoice_kwh": 380.06,
            "invoice_periods": {"p1": 107.11, "p2": 104.16, "p3": 168.79},
            "invoice_eur": money(invoice_eur),
            # 379.555 y 0.505 caen justo en el empate: se redondea hacia arriba.
            "edata_kwh": 379.56,
            "edata_periods": {"p1": 107.11, "p2": 100.16, "p3": None},
            "edata_eur": 80.0,
            "delta_kwh": 0.51,
            "delta_periods": {"p1": 0.0, "p2": 4.0, "p3": None},
            "delta_eur": money(invoice_eur - 80),
            "delta_pct": money((invoice_eur - 80) * 100 / 80),
        },
    }
    newest = electricity["invoices"][0]
    assert newest == expected
    assert [c["key"] for c in newest["concepts"]] == [
        c.key.value for c in latest.concepts
    ]

    gas_row = by_supply["gas"]["invoices"][0]
    assert by_supply["gas"]["name"] == "CurEnergía gas"
    assert gas_row["status"] == "gas"
    assert gas_row["supply"] == "gas"
    assert gas_row["estimated"] is True
    assert gas_row["m3"] == 13.0
    assert gas_row["energy_price_kwh"] == price(gas.energy_price_kwh) == 0.0433
    assert gas_row["periods"] is None
    assert gas_row["comparison"] is None
    assert gas_row["total"] == 19.2


async def test_ws_invoices_without_comparison(
    hass: HomeAssistant, hass_ws_client, mailbox: FakeMailbox, make_invoice
):
    invoice = make_invoice()
    mailbox.add(1, (b"luz", invoice))
    await setup_entry(hass, make_entry())

    response = await _call(hass, hass_ws_client, type="curenergia/invoices")

    row = response["result"]["contracts"][0]["invoices"][0]
    assert row["status"] == "sin_datos"
    assert row["comparison"] is None


async def test_ws_invoices_group_and_zero_kwh(
    hass: HomeAssistant, hass_ws_client, mailbox: FakeMailbox, make_invoice
):
    first = make_invoice(
        number="EST-1",
        estimated=True,
        period_start=date(2026, 6, 29),
        period_end=date(2026, 7, 28),
    )
    second = make_invoice(
        number="EST-2",
        estimated=True,
        period_start=date(2026, 7, 29),
        period_end=date(2026, 8, 28),
    )
    real = make_invoice(number="REAL-1")
    zero = make_invoice(
        number="ZERO",
        kwh=Decimal(0),
        kwh_p1=None,
        kwh_p2=None,
        kwh_p3=None,
        period_start=date(2026, 9, 29),
        period_end=date(2026, 10, 28),
    )
    older = make_invoice(
        number="OLDEST",
        period_start=date(2026, 5, 29),
        period_end=date(2026, 6, 28),
    )
    for uid, invoice in enumerate((older, first, second, real, zero), start=1):
        mailbox.add(uid, (b"pdf-%d" % uid, invoice))
    totals = Totals(kwh=Decimal("1"), p1=None, p2=None, p3=None, eur=None)

    with fake_totals(lambda start, end: totals):
        await setup_entry(hass, make_entry())
        response = await _call(hass, hass_ws_client, type="curenergia/invoices")

    rows = {r["number"]: r for r in response["result"]["contracts"][0]["invoices"]}
    assert list(rows) == ["ZERO", "REAL-1", "EST-2", "EST-1", "OLDEST"]
    assert rows["EST-1"]["in_group_of"] == "REAL-1"
    assert rows["EST-2"]["in_group_of"] == "REAL-1"
    assert rows["REAL-1"]["in_group_of"] is None
    assert rows["REAL-1"]["comparison"]["group"] == ["EST-1", "EST-2", "REAL-1"]
    assert rows["ZERO"]["price_kwh"] is None
    assert rows["ZERO"]["periods"] is None
    # Sin costes en e-data no hay diferencia en euros.
    assert rows["REAL-1"]["comparison"]["edata_eur"] is None
    assert rows["REAL-1"]["comparison"]["delta_eur"] is None
    assert rows["REAL-1"]["comparison"]["delta_pct"] is None


async def test_ws_invoices_supply_filter(
    hass: HomeAssistant,
    hass_ws_client,
    mailbox: FakeMailbox,
    make_invoice,
    fixture_invoice,
):
    mailbox.add(1, (b"luz", make_invoice()))
    mailbox.add(2, (b"gas", fixture_invoice("gas_2026-09")))
    await setup_entry(hass, make_entry())

    gas = await _call(hass, hass_ws_client, type="curenergia/invoices", supply="gas")
    luz = await _call(
        hass, hass_ws_client, type="curenergia/invoices", supply="electricity"
    )
    invalid = await _call(
        hass, hass_ws_client, type="curenergia/invoices", supply="water"
    )

    assert [c["supply"] for c in gas["result"]["contracts"]] == ["gas"]
    assert [c["supply"] for c in luz["result"]["contracts"]] == ["electricity"]
    assert invalid["success"] is False
    assert invalid["error"]["code"] == "invalid_format"


async def test_ws_invoices_by_entry(
    hass: HomeAssistant, hass_ws_client, mailbox: FakeMailbox, make_invoice
):
    mailbox.add(1, (b"luz", make_invoice()))
    first = make_entry()
    second = make_entry()
    await setup_entry(hass, first)
    await setup_entry(hass, second)

    everything = await _call(hass, hass_ws_client, type="curenergia/invoices")
    only_second = await _call(
        hass, hass_ws_client, type="curenergia/invoices", entry_id=second.entry_id
    )

    assert {c["entry_id"] for c in everything["result"]["contracts"]} == {
        first.entry_id,
        second.entry_id,
    }
    assert [c["entry_id"] for c in only_second["result"]["contracts"]] == [
        second.entry_id
    ]


async def test_ws_invoices_without_entries(hass: HomeAssistant, hass_ws_client):
    await async_setup_component(hass, DOMAIN, {})

    response = await _call(hass, hass_ws_client, type="curenergia/invoices")

    assert response["success"] is True
    assert response["result"] == {"contracts": []}


@pytest.mark.parametrize("command", ["curenergia/invoices", "curenergia/summary"])
async def test_ws_unknown_entry(
    hass: HomeAssistant, hass_ws_client, mailbox: FakeMailbox, command
):
    await setup_entry(hass, make_entry())

    response = await _call(hass, hass_ws_client, type=command, entry_id="nope")

    assert response["success"] is False
    assert response["error"]["code"] == "not_found"


@pytest.mark.parametrize("command", ["curenergia/invoices", "curenergia/summary"])
async def test_ws_entry_not_loaded(
    hass: HomeAssistant, hass_ws_client, mailbox: FakeMailbox, command
):
    mailbox.error = MailConnectionError("down")
    entry = make_entry()

    await setup_entry(hass, entry, ConfigEntryState.SETUP_RETRY)

    response = await _call(hass, hass_ws_client, type=command, entry_id=entry.entry_id)

    assert response["success"] is False
    assert response["error"]["code"] == "not_found"


@pytest.mark.parametrize("command", ["curenergia/invoices", "curenergia/summary"])
async def test_ws_entry_of_another_domain(
    hass: HomeAssistant, hass_ws_client, mailbox: FakeMailbox, command
):
    await setup_entry(hass, make_entry())
    other = MockConfigEntry(domain="other")
    other.add_to_hass(hass)

    response = await _call(hass, hass_ws_client, type=command, entry_id=other.entry_id)

    assert response["error"]["code"] == "not_found"


@FROZEN
async def test_ws_summary(
    hass: HomeAssistant,
    hass_ws_client,
    mailbox: FakeMailbox,
    make_invoice,
    fixture_invoice,
):
    a = make_invoice(number="A-1")  # 08-29..09-28, emitida 2026-10-06
    # Otros contratos: con huecos entre periodos, la posterior sería sin_datos (R25).
    b = make_invoice(
        number="B-1",
        contract="CT-0000002",
        issue_date=date(2026, 6, 10),
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 31),
    )
    # Fuera de los últimos 365 días: no cuenta.
    old = make_invoice(
        number="D-1",
        contract="CT-0000003",
        issue_date=date(2025, 8, 10),
        period_start=date(2025, 7, 1),
        period_end=date(2025, 7, 31),
    )
    estimated = make_invoice(
        number="C-1",
        estimated=True,
        issue_date=date(2026, 10, 20),
        period_start=date(2026, 9, 29),
        period_end=date(2026, 10, 28),
    )
    gas = fixture_invoice("gas_2026-09")  # estimada, emitida 2026-09-11
    for uid, invoice in enumerate((a, b, old, estimated, gas), start=1):
        mailbox.add(uid, (b"pdf-%d" % uid, invoice))
    mailbox.add(6, (b"bad", InvoiceParseError("number")))
    mailbox.add(7, (b"credit-note", UnsupportedInvoiceError("abono")))
    edata_kwh = {
        date(2026, 8, 29): Decimal("360.06"),  # a: +20
        date(2026, 5, 1): Decimal("380.06"),  # b: 0
        date(2025, 7, 1): Decimal("1"),  # old: fuera del plazo
        date(2026, 9, 29): Decimal("1"),  # estimada: no cuenta
    }

    def provider(start, end):
        kwh = edata_kwh.get(start.date())
        return None if kwh is None else Totals(kwh, None, None, None, None)

    entry = make_entry()
    with fake_totals(provider):
        await setup_entry(hass, entry)
        response = await _call(hass, hass_ws_client, type="curenergia/summary")

    assert response["success"] is True
    summary = response["result"]
    assert set(summary) == SUMMARY_KEYS
    # a + b + estimada + gas (la factura antigua no entra).
    assert summary["billed_12m"] == 326.85
    # (380.06 + 380.06 - 360.06 - 380.06) / 740.12 * 100
    assert summary["kwh_delta_pct"] == 2.7
    assert summary["estimated_count"] == 2
    assert summary["unreadable_emails"] == 1
    assert summary["unsupported_emails"] == 1
    assert summary["last_mail_check"] == "2026-10-29T12:00:00+00:00"
    assert summary["mail_error"] is False

    by_entry = await _call(
        hass, hass_ws_client, type="curenergia/summary", entry_id=entry.entry_id
    )
    assert by_entry["result"] == summary


@FROZEN
async def test_ws_summary_12_month_boundary(
    hass: HomeAssistant, hass_ws_client, mailbox: FakeMailbox, make_invoice
):
    # El día 365 antes de hoy ya queda fuera; el siguiente, dentro.
    outside = make_invoice(number="OUT", issue_date=date(2025, 10, 29))
    inside = make_invoice(number="IN", issue_date=date(2025, 10, 30))
    mailbox.add(1, (b"out", outside))
    mailbox.add(2, (b"in", inside))
    await setup_entry(hass, make_entry())

    response = await _call(hass, hass_ws_client, type="curenergia/summary")

    assert response["result"]["billed_12m"] == 102.55
    assert response["result"]["kwh_delta_pct"] is None


async def test_ws_summary_empty(hass: HomeAssistant, hass_ws_client, mailbox):
    await setup_entry(hass, make_entry())

    response = await _call(hass, hass_ws_client, type="curenergia/summary")

    assert response["result"]["billed_12m"] == 0.0
    assert response["result"]["kwh_delta_pct"] is None
    assert response["result"]["estimated_count"] == 0
    assert response["result"]["last_mail_check"] is not None


@FROZEN
async def test_ws_summary_zero_edata_kwh(
    hass: HomeAssistant, hass_ws_client, mailbox: FakeMailbox, make_invoice
):
    mailbox.add(1, (b"luz", make_invoice()))
    totals = Totals(Decimal(0), None, None, None, None)
    with fake_totals(lambda start, end: totals):
        await setup_entry(hass, make_entry())
        response = await _call(hass, hass_ws_client, type="curenergia/summary")

    assert response["result"]["kwh_delta_pct"] is None


@FROZEN
async def test_ws_summary_mail_error_keeps_last_check(
    hass: HomeAssistant, hass_ws_client, mailbox: FakeMailbox, make_invoice, freezer
):
    mailbox.add(1, (b"luz", make_invoice()))
    entry = make_entry()
    await setup_entry(hass, entry)
    client = await hass_ws_client(hass)  # antes de mover el reloj

    mailbox.error = MailConnectionError("down")
    freezer.move_to("2026-10-29 18:00:00+00:00")
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    await client.send_json_auto_id({"type": "curenergia/summary"})
    response = await client.receive_json()

    assert response["result"]["mail_error"] is True
    assert response["result"]["last_mail_check"] == "2026-10-29T12:00:00+00:00"


@FROZEN
async def test_ws_summary_adds_up_all_entries(
    hass: HomeAssistant, hass_ws_client, mailbox: FakeMailbox, make_invoice, freezer
):
    mailbox.add(1, (b"luz", make_invoice()))
    mailbox.add(2, (b"bad", InvoiceParseError("number")))
    first = make_entry()
    second = make_entry()
    await setup_entry(hass, first)
    client = await hass_ws_client(hass)  # antes de mover el reloj
    freezer.move_to("2026-10-29 13:00:00+00:00")
    await setup_entry(hass, second)
    mailbox.error = MailConnectionError("down")
    await first.runtime_data.async_refresh()
    await hass.async_block_till_done()

    await client.send_json_auto_id({"type": "curenergia/summary"})
    response = await client.receive_json()

    summary = response["result"]
    assert summary["billed_12m"] == 205.1
    assert summary["unreadable_emails"] == 2
    assert summary["last_mail_check"] == "2026-10-29T13:00:00+00:00"
    assert summary["mail_error"] is True

"""Pruebas de los diagnósticos (redactados) de la integración."""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pytest
from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from pycurenergia import InvoiceParseError, UnsupportedInvoiceError
from pycurenergia import __version__ as LIB_VERSION
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)

from custom_components.curenergia.matching import Totals

from .helpers import ENTRY_DATA, FakeMailbox, fake_totals, make_entry, setup_entry

pytestmark = pytest.mark.usefixtures("recorder_mock", "enable_custom_integrations")

BOUNDARY_KEYS = {"base", "start-1d", "start+1d", "end-1d", "end+1d"}


def _kwh_by_window(start: datetime, end: datetime) -> Decimal:
    """kWh de e-data inventados que dependen del día de inicio y de la duración."""
    days = (end.date() - start.date()).days
    return Decimal(days) + Decimal(start.day) / 100


def _totals(start: datetime, end: datetime) -> Totals:
    return Totals(_kwh_by_window(start, end), None, None, None, None)


def _find(result: dict[str, Any], **wanted: Any) -> dict[str, Any]:
    matches = [
        item
        for item in result["invoices"]
        if all(item[key] == value for key, value in wanted.items())
    ]
    assert len(matches) == 1, wanted
    return matches[0]


async def test_diagnostics_redacted(
    hass: HomeAssistant,
    hass_client,
    mailbox: FakeMailbox,
    make_invoice,
    fixture_invoice,
):
    estimated = make_invoice(
        number="EST-NUM-0001",
        estimated=True,
        period_start=date(2026, 7, 29),
        period_end=date(2026, 8, 28),
    )
    real = make_invoice()
    gas = fixture_invoice("gas_2026-09")
    mailbox.add(1, (b"est", estimated))
    mailbox.add(2, (b"real", real))
    mailbox.add(3, (b"gas", gas))
    mailbox.add(4, (b"bad", InvoiceParseError("number")))
    mailbox.add(5, (b"credit-note", UnsupportedInvoiceError("abono")))
    entry = make_entry()

    # Para ``start+1d`` el proveedor no cubre la ventana.
    def provider(start, end):
        if start.date() == date(2026, 7, 30):
            return None
        return _totals(start, end)

    with fake_totals(provider):
        await setup_entry(hass, entry)
        result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    # Nada identificable en la salida.
    dump = json.dumps(result)
    sensitive = (
        ENTRY_DATA["username"],
        ENTRY_DATA["password"],
        real.cups,
        real.contract,
        real.number,
        estimated.number,
        gas.cups,
        gas.contract,
        gas.number,
    )
    for value in sensitive:
        assert value and value not in dump

    assert result["options"] == dict(entry.options)
    assert result["data"] == {**ENTRY_DATA, "username": REDACTED, "password": REDACTED}
    assert result["pycurenergia_version"] == LIB_VERSION
    assert result["mail"] == {
        "uidvalidity": 1,
        "seen": 3,
        "failed": 1,
        "unsupported": 1,
    }

    assert len(result["invoices"]) == 3
    gas_item = _find(result, supply="gas")
    assert gas_item == {
        "supply": "gas",
        "period_start": gas.period_start.isoformat(),
        "period_end": gas.period_end.isoformat(),
        "estimated": True,
        "status": "gas",
        "problems": [],
    }
    estimated_item = _find(result, supply="electricity", estimated=True)
    assert "boundary_deltas" not in estimated_item
    assert estimated_item["status"] == "estimada"

    real_item = _find(result, supply="electricity", estimated=False)
    assert real_item["period_start"] == "2026-08-29"
    assert real_item["period_end"] == "2026-09-28"
    assert real_item["problems"] == []
    # La real cierra el grupo con la estimada: se comparan los kWh del grupo
    # (dos facturas) con la ventana combinada 07-29 .. 09-29 (62 días).
    group_kwh = real.kwh + estimated.kwh

    def delta(days: int, start_day: int) -> float:
        return float(group_kwh - (Decimal(days) + Decimal(start_day) / 100))

    assert set(real_item["boundary_deltas"]) == BOUNDARY_KEYS
    assert real_item["boundary_deltas"] == {
        "base": pytest.approx(delta(62, 29)),
        "start-1d": pytest.approx(delta(63, 28)),
        "start+1d": None,
        "end-1d": pytest.approx(delta(61, 29)),
        "end+1d": pytest.approx(delta(63, 29)),
    }


async def test_diagnostics_boundary_deltas_single_invoice(
    hass: HomeAssistant, hass_client, mailbox: FakeMailbox, make_invoice
):
    real = make_invoice()
    mailbox.add(1, (b"real", real))
    entry = make_entry()

    with fake_totals(_totals):
        await setup_entry(hass, entry)
        result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    deltas = result["invoices"][0]["boundary_deltas"]

    def delta(days: int, start_day: int) -> float:
        return float(real.kwh - (Decimal(days) + Decimal(start_day) / 100))

    # Periodo 08-29 .. 09-28: 31 días.
    assert deltas == {
        "base": pytest.approx(delta(31, 29)),
        "start-1d": pytest.approx(delta(32, 28)),
        "start+1d": pytest.approx(delta(30, 30)),
        "end-1d": pytest.approx(delta(30, 29)),
        "end+1d": pytest.approx(delta(32, 29)),
    }
    assert len(set(deltas.values())) == 5


async def test_diagnostics_without_edata(
    hass: HomeAssistant, hass_client, mailbox: FakeMailbox, make_invoice
):
    mailbox.add(1, (b"real", make_invoice()))
    entry = make_entry()
    await setup_entry(hass, entry)

    result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    assert result["invoices"][0]["status"] == "sin_datos"
    assert result["invoices"][0]["boundary_deltas"] == dict.fromkeys(BOUNDARY_KEYS)


async def test_diagnostics_one_day_period(
    hass: HomeAssistant, hass_client, mailbox: FakeMailbox, make_invoice
):
    one_day = make_invoice(period_start=date(2026, 9, 28), period_end=date(2026, 9, 28))
    mailbox.add(1, (b"real", one_day))
    entry = make_entry()

    with fake_totals(_totals):
        await setup_entry(hass, entry)
        result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    deltas = result["invoices"][0]["boundary_deltas"]
    # Con un solo día, mover el inicio un día hacia delante deja la ventana vacía.
    assert deltas["start+1d"] is None
    assert deltas["end-1d"] is None
    assert deltas["base"] is not None
    assert deltas["start-1d"] is not None
    assert deltas["end+1d"] is not None


async def test_diagnostics_empty(hass: HomeAssistant, hass_client, mailbox):
    entry = make_entry()
    await setup_entry(hass, entry)

    result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    assert result["invoices"] == []
    assert result["mail"] == {
        "uidvalidity": 1,
        "seen": 0,
        "failed": 0,
        "unsupported": 0,
    }

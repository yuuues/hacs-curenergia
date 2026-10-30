"""Tests del almacenamiento de facturas y del estado del buzón."""

import json
from dataclasses import replace
from decimal import Decimal

import pytest
from homeassistant.core import HomeAssistant

from custom_components.curenergia.storage import (
    InvoiceStore,
    MailState,
    StoredInvoice,
    build_stored,
    invoice_from_dict,
    invoice_to_dict,
)

from .helpers import integration_log

ENTRY_ID = "entry123"
STORE_KEY = f"curenergia.{ENTRY_ID}"

pytestmark = pytest.mark.usefixtures("recorder_mock", "enable_custom_integrations")


@pytest.mark.parametrize("name", ["electricity_2026-10", "gas_2026-09"])
def test_invoice_round_trip(fixture_invoice, name):
    inv = fixture_invoice(name)
    data = json.loads(json.dumps(invoice_to_dict(inv)))
    assert invoice_from_dict(data) == inv


def test_invoice_to_dict_is_json_friendly(fixture_invoice):
    data = invoice_to_dict(fixture_invoice("electricity_2026-10"))
    assert isinstance(data["total"], str)
    assert isinstance(data["issue_date"], str)
    assert isinstance(data["supply"], str)
    assert isinstance(data["concepts"], list)
    assert isinstance(data["contracted_power_kw"], list)


def test_invoice_round_trip_optional_fields(make_invoice):
    inv = make_invoice(
        kwh_p1=None,
        kwh_p2=None,
        kwh_p3=None,
        m3=Decimal("1.5"),
        contracted_power_kw=(),
        energy_price_kwh=None,
    )
    assert invoice_from_dict(json.loads(json.dumps(invoice_to_dict(inv)))) == inv


def test_build_stored_flags_email_total_mismatch(fixture_invoice):
    inv = fixture_invoice("electricity_2026-10")
    assert build_stored(inv, inv.total).problems == []
    assert build_stored(inv, inv.total + Decimal("0.02")).problems == [
        "email_total_mismatch"
    ]
    assert build_stored(inv, None).unreadable is False


def test_build_stored_tolerance_is_strict(fixture_invoice):
    inv = fixture_invoice("electricity_2026-10")
    assert build_stored(inv, inv.total + Decimal("0.01")).problems == []
    assert build_stored(inv, inv.total - Decimal("0.01")).problems == []
    assert build_stored(inv, inv.total - Decimal("0.02")).unreadable is True


def test_build_stored_includes_consistency_problems(make_invoice):
    inv = make_invoice(total=Decimal("1.00"))
    stored = build_stored(inv, Decimal("1.00"))
    assert "total_mismatch" in stored.problems
    assert stored.unreadable is True
    assert all(isinstance(p, str) for p in stored.problems)


def test_invoice_without_reading_keys_loads_as_none(fixture_invoice):
    data = invoice_to_dict(fixture_invoice("gas_2026-09"))
    del data["reading_m3"]
    del data["previous_reading_m3"]

    invoice = invoice_from_dict(data)

    assert invoice.reading_m3 is None
    assert invoice.previous_reading_m3 is None


async def test_add_only_replaces_to_complete_readings(
    hass: HomeAssistant, fixture_invoice
):
    gas = fixture_invoice("gas_2026-09")
    without = build_stored(
        replace(gas, reading_m3=None, previous_reading_m3=None), None
    )
    complete = build_stored(gas, None)
    store = InvoiceStore(hass, ENTRY_ID)

    assert store.add(without) is True
    # Sin lecturas tampoco sustituye a otra sin lecturas.
    assert store.add(build_stored(without.invoice, Decimal("1.00"))) is False
    assert store.invoices[gas.number] is without
    assert store.add(complete) is False
    assert store.invoices[gas.number] is complete
    # Una factura con lecturas ya no se toca.
    assert store.add(without) is False
    assert store.invoices[gas.number] is complete


async def test_load_resets_mail_once_when_invoices_lack_the_backfill_mark(
    hass: HomeAssistant, hass_storage, fixture_invoice
):
    store = InvoiceStore(hass, ENTRY_ID)
    await store.async_load()
    store.add(build_stored(fixture_invoice("gas_2026-09"), None))
    store.mail.uidvalidity = 7
    store.mail.seen = {1, 2}
    await store.async_save()
    assert hass_storage[STORE_KEY]["data"]["readings_backfilled"] is True

    kept = InvoiceStore(hass, ENTRY_ID)
    await kept.async_load()
    assert kept.mail.seen == {1, 2}

    del hass_storage[STORE_KEY]["data"]["readings_backfilled"]
    reset = InvoiceStore(hass, ENTRY_ID)
    await reset.async_load()
    assert reset.mail == MailState()
    assert len(reset.invoices) == 1


async def test_store_persists_and_deduplicates(
    hass: HomeAssistant, hass_storage, fixture_invoice, make_invoice
):
    first = build_stored(fixture_invoice("electricity_2026-10"), None)
    gas = build_stored(fixture_invoice("gas_2026-09"), Decimal("12.34"))
    bad = build_stored(make_invoice(number="X-BAD", total=Decimal("1.00")), None)

    store = InvoiceStore(hass, ENTRY_ID)
    await store.async_load()
    assert store.invoices == {}
    assert store.mail == MailState()

    assert store.add(first) is True
    assert store.add(first) is False
    assert store.add(gas) is True
    assert store.add(bad) is True
    # No reemplaza: la factura repetida con otros datos se descarta.
    other = StoredInvoice(first.invoice, ["total_mismatch"], Decimal("9.99"))
    assert store.add(other) is False
    assert store.invoices[first.invoice.number] is first

    store.mail.uidvalidity = 77
    store.mail.folder = "Facturas/Energía"
    store.mail.seen = {1, 2, 30}
    store.mail.failed = {5: "0.1.0", 9: "0.0.9"}
    store.mail.unsupported = {4}
    await store.async_save()

    assert hass_storage[STORE_KEY]["version"] == 1
    # Los datos guardados son JSON puro (claves de dict como str).
    json.dumps(hass_storage[STORE_KEY]["data"])

    loaded = InvoiceStore(hass, ENTRY_ID)
    await loaded.async_load()
    assert loaded.invoices == store.invoices
    assert loaded.mail == store.mail
    assert loaded.mail.failed == {5: "0.1.0", 9: "0.0.9"}
    assert all(isinstance(uid, int) for uid in loaded.mail.failed)
    assert loaded.invoices[bad.invoice.number].problems == bad.problems
    assert loaded.invoices[gas.invoice.number].email_total == Decimal("12.34")
    assert loaded.invoices[first.invoice.number].email_total is None


async def test_reset_mail_clears_state(hass: HomeAssistant, fixture_invoice):
    store = InvoiceStore(hass, ENTRY_ID)
    await store.async_load()
    stored = build_stored(fixture_invoice("electricity_2026-10"), None)
    store.add(stored)
    store.mail.uidvalidity = 5
    store.mail.folder = "INBOX"
    store.mail.seen = {1}
    store.mail.failed = {2: "0.1.0"}
    store.mail.unsupported = {3}

    store.reset_mail()

    assert store.mail == MailState()
    # Las facturas ya guardadas se conservan.
    assert store.invoices == {stored.invoice.number: stored}


async def test_async_remove_deletes_stored_data(
    hass: HomeAssistant, hass_storage, fixture_invoice
):
    store = InvoiceStore(hass, ENTRY_ID)
    await store.async_load()
    store.add(build_stored(fixture_invoice("gas_2026-09"), None))
    await store.async_save()
    assert STORE_KEY in hass_storage

    await store.async_remove()
    assert STORE_KEY not in hass_storage


@pytest.mark.parametrize(
    "corrupt",
    [
        ["not", "a", "dict"],
        {"invoices": {"X": {"invoice": {}}}, "mail": {}},
        {"invoices": {"X": "nope"}},
        {"invoices": {}, "mail": {"seen": 5}},
        {"invoices": {}, "mail": {"failed": {"abc": "0.1.0"}}},
        {"invoices": {}, "mail": "nope"},
        "decimal",
    ],
)
async def test_corrupt_data_starts_empty(
    hass: HomeAssistant, hass_storage, fixture_invoice, caplog, corrupt
):
    if corrupt == "decimal":
        good = build_stored(fixture_invoice("gas_2026-09"), None).to_dict()
        good["invoice"]["total"] = "SECRET-9.9x"
        corrupt = {"invoices": {"SECRET-NUMBER": good}, "mail": {"seen": [1]}}
    hass_storage[STORE_KEY] = {"version": 1, "key": STORE_KEY, "data": corrupt}

    store = InvoiceStore(hass, ENTRY_ID)
    store.mail.seen = {99}
    await store.async_load()

    assert store.invoices == {}
    assert store.mail == MailState()
    log = integration_log(caplog)
    assert "invalid" in log
    assert "SECRET" not in log
    assert "abc" not in log

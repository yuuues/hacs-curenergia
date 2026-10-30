"""Pruebas del esqueleto de la integración."""

import pytest
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration
from pycurenergia import SupplyType

from custom_components.curenergia.const import DOMAIN
from custom_components.curenergia.coordinator import CurenergiaCoordinator
from custom_components.curenergia.mail import MailAuthError, MailConnectionError

from .helpers import FakeMailbox, make_entry, setup_entry

pytestmark = pytest.mark.usefixtures("recorder_mock", "enable_custom_integrations")


async def test_manifest_loads(hass):
    integration = await async_get_integration(hass, DOMAIN)
    assert integration.requirements == ["pycurenergia==0.1.0"]
    assert integration.config_flow is True


def test_fixture_invoice_parses(fixture_invoice):
    assert fixture_invoice("electricity_2026-10").supply is SupplyType.ELECTRICITY
    assert fixture_invoice("gas_2026-09").supply is SupplyType.GAS


def test_make_invoice_replaces_fields(make_invoice, fixture_invoice):
    base = fixture_invoice("electricity_2026-10")
    changed = make_invoice(estimated=not base.estimated)
    assert changed.estimated is not base.estimated
    assert changed.number == base.number


async def test_auth_error_starts_reauth(hass: HomeAssistant, mailbox: FakeMailbox):
    mailbox.error = MailAuthError("IMAP login rejected")
    entry = make_entry()

    await setup_entry(hass, entry, ConfigEntryState.SETUP_ERROR)

    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [flow["context"]["source"] for flow in flows] == [SOURCE_REAUTH]
    assert flows[0]["context"]["entry_id"] == entry.entry_id


async def test_auth_error_after_setup_starts_reauth(
    hass: HomeAssistant, mailbox: FakeMailbox
):
    entry = make_entry()
    await setup_entry(hass, entry)

    mailbox.error = MailAuthError("IMAP login rejected")
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert entry.runtime_data.last_update_success is False
    # Diagnósticos (en memoria): solo la clase del error.
    assert entry.runtime_data.mail_last_error == "MailAuthError"
    assert entry.runtime_data.mail_last_read_complete is False
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [flow["context"]["source"] for flow in flows] == [SOURCE_REAUTH]


async def test_connection_error_on_setup_not_ready(
    hass: HomeAssistant, mailbox: FakeMailbox
):
    mailbox.error = MailConnectionError("Cannot connect to the IMAP server")
    entry = make_entry()

    await setup_entry(hass, entry, ConfigEntryState.SETUP_RETRY)

    assert hass.config_entries.flow.async_progress_by_handler(DOMAIN) == []


async def test_unload_and_remove_entry(
    hass: HomeAssistant, hass_storage, mailbox: FakeMailbox, fixture_invoice
):
    mailbox.add(1, (b"gas", fixture_invoice("gas_2026-09")))
    entry = make_entry()
    await setup_entry(hass, entry)
    key = f"{DOMAIN}.{entry.entry_id}"
    assert key in hass_storage
    assert isinstance(entry.runtime_data, CurenergiaCoordinator)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    # Descargar no borra los datos guardados.
    assert key in hass_storage

    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert key not in hass_storage


async def test_setup_loads_stored_invoices(
    hass: HomeAssistant, hass_storage, mailbox: FakeMailbox, fixture_invoice
):
    gas = fixture_invoice("gas_2026-09")
    mailbox.add(1, (b"gas", gas))
    entry = make_entry()
    await setup_entry(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)

    # Al volver a montar, la factura sale del Store aunque el buzón no la traiga.
    mailbox.messages.clear()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert mailbox.calls[-1] == ("INBOX", frozenset({1}), 1)
    assert list(entry.runtime_data.data.contracts) == [gas.contract]

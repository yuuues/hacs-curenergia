"""Pruebas del botón «Buscar facturas ahora»."""

import pytest
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.curenergia.const import DOMAIN

from .helpers import FakeMailbox, make_entry, setup_entry

pytestmark = pytest.mark.usefixtures("recorder_mock", "enable_custom_integrations")


def _button_id(hass: HomeAssistant, entry_id: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        "button", DOMAIN, f"{entry_id}_check_now"
    )
    assert entity_id is not None
    return entity_id


async def test_button_in_service_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mailbox: FakeMailbox,
):
    entry = make_entry()

    await setup_entry(hass, entry)

    registered = entity_registry.async_get(_button_id(hass, entry.entry_id))
    assert registered.translation_key == "check_now"
    device = device_registry.async_get(registered.device_id)
    assert device.identifiers == {(DOMAIN, entry.entry_id)}
    assert device.entry_type is dr.DeviceEntryType.SERVICE
    assert device.name == "CurEnergía"


async def test_button_requests_refresh(hass: HomeAssistant, mailbox: FakeMailbox):
    entry = make_entry()
    await setup_entry(hass, entry)
    entity_id = _button_id(hass, entry.entry_id)
    calls_before = len(mailbox.calls)

    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert len(mailbox.calls) == calls_before + 1

"""Pruebas del módulo JS servido y del panel de la barra lateral."""

import pytest
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL, DATA_PANELS
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.curenergia.const import CONF_SHOW_PANEL
from custom_components.curenergia.frontend import PANEL_PATH

from .helpers import FakeMailbox, make_entry, setup_entry

pytestmark = pytest.mark.usefixtures(
    "recorder_mock", "enable_custom_integrations", "mailbox"
)

MODULE_URL = "/curenergia_static/curenergia.js?v=0.3.0"


def _second_entry(**options) -> MockConfigEntry:
    base = make_entry(**options)
    return MockConfigEntry(
        domain=base.domain,
        title=base.title,
        unique_id="other@example.es",
        data=dict(base.data),
        options=dict(base.options),
    )


async def test_module_served_and_added(
    hass: HomeAssistant, hass_client: ClientSessionGenerator, mailbox: FakeMailbox
):
    await setup_entry(hass, make_entry())

    response = await (await hass_client()).get("/curenergia_static/curenergia.js")

    assert response.status == 200
    assert "curenergia-panel" in await response.text()
    assert MODULE_URL in hass.data[DATA_EXTRA_MODULE_URL].urls


async def test_panel_registered_for_admins(hass: HomeAssistant):
    await setup_entry(hass, make_entry(**{CONF_SHOW_PANEL: True}))

    panel = hass.data[DATA_PANELS][PANEL_PATH]
    assert panel.require_admin is True
    assert panel.sidebar_icon == "mdi:receipt-text"
    assert panel.sidebar_title == "Facturas"
    custom = panel.config["_panel_custom"]
    assert custom["name"] == "curenergia-panel"
    assert custom["module_url"] == MODULE_URL


async def test_panel_removed_when_option_off(hass: HomeAssistant):
    entry = make_entry()
    await setup_entry(hass, entry)
    assert PANEL_PATH in hass.data[DATA_PANELS]

    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_SHOW_PANEL: False}
    )
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert PANEL_PATH not in hass.data[DATA_PANELS]


async def test_panel_not_registered_when_option_off(hass: HomeAssistant):
    await setup_entry(hass, make_entry(**{CONF_SHOW_PANEL: False}))

    assert PANEL_PATH not in hass.data[DATA_PANELS]


async def test_panel_back_after_option_on(hass: HomeAssistant):
    entry = make_entry(**{CONF_SHOW_PANEL: False})
    await setup_entry(hass, entry)

    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_SHOW_PANEL: True}
    )
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert PANEL_PATH in hass.data[DATA_PANELS]


async def test_panel_kept_while_another_entry_wants_it(hass: HomeAssistant):
    first = make_entry()
    second = _second_entry()
    await setup_entry(hass, first)
    await setup_entry(hass, second)

    await hass.config_entries.async_unload(first.entry_id)
    await hass.async_block_till_done()

    assert PANEL_PATH in hass.data[DATA_PANELS]


async def test_panel_removed_on_last_unload(hass: HomeAssistant):
    first = make_entry()
    second = _second_entry()
    await setup_entry(hass, first)
    await setup_entry(hass, second)

    await hass.config_entries.async_unload(first.entry_id)
    await hass.config_entries.async_unload(second.entry_id)
    await hass.async_block_till_done()

    assert PANEL_PATH not in hass.data[DATA_PANELS]


async def test_panel_ignores_entry_with_option_off(hass: HomeAssistant):
    keeps = make_entry(**{CONF_SHOW_PANEL: False})
    wants = _second_entry()
    await setup_entry(hass, keeps)
    await setup_entry(hass, wants)

    await hass.config_entries.async_unload(wants.entry_id)
    await hass.async_block_till_done()

    assert PANEL_PATH not in hass.data[DATA_PANELS]

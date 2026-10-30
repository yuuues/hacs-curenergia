"""Pruebas del config flow, la reautenticación y las opciones."""

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.selector import SelectSelector, TextSelector
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.curenergia.const import (
    CONF_EDATA_ENTRY,
    CONF_FOLDER,
    CONF_KWH_THRESHOLD,
    CONF_SAVE_PDFS,
    CONF_SCAN_HOURS,
    CONF_SHOW_PANEL,
    DOMAIN,
)
from custom_components.curenergia.mail import MailAuthError, MailConnectionError

pytestmark = pytest.mark.usefixtures("recorder_mock", "enable_custom_integrations")

COMPONENT = Path(__file__).parents[1] / "custom_components" / "curenergia"

USER_INPUT = {
    CONF_HOST: "imap.gmail.com",
    CONF_PORT: 993,
    CONF_USERNAME: "User@Example.es",
    CONF_PASSWORD: "app-password",
}
FOLDERS = ["CurEnergia", "INBOX", "[Gmail]/All Mail"]


@pytest.fixture
def mail_client():
    """Sustituye ``MailClient`` del config flow por un doble."""
    with patch("custom_components.curenergia.config_flow.MailClient") as cls:
        client = cls.return_value
        client.check_login.return_value = None
        client.list_folders.return_value = list(FOLDERS)
        yield client


@pytest.fixture
def setup_entry():
    """Evita montar la entrada de verdad (llega en la tarea 7)."""
    with (
        patch(
            "custom_components.curenergia.async_setup_entry",
            new=AsyncMock(return_value=True),
            create=True,
        ) as setup,
        patch(
            "custom_components.curenergia.async_unload_entry",
            new=AsyncMock(return_value=True),
            create=True,
        ) as unload,
    ):
        yield SimpleNamespace(setup=setup, unload=unload)


async def _load_entry(hass: HomeAssistant, entry: MockConfigEntry, setup_entry) -> None:
    """Monta la entrada (con los dobles) y comprueba el estado inicial."""
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert setup_entry.setup.await_count == 1
    assert setup_entry.unload.await_count == 0


def _assert_reloaded(entry: MockConfigEntry, setup_entry) -> None:
    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert setup_entry.unload.await_count == 1
    assert setup_entry.setup.await_count == 2


def _schema(result) -> dict[str, object]:
    return {str(key): value for key, value in result["data_schema"].schema.items()}


def _entry(**options) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="CurEnergía",
        unique_id="user@example.es@imap.gmail.com",
        data={**USER_INPUT, CONF_USERNAME: "user@example.es"},
        options={
            CONF_FOLDER: "CurEnergia",
            CONF_SCAN_HOURS: 6,
            CONF_KWH_THRESHOLD: 1.0,
            CONF_SHOW_PANEL: True,
            CONF_SAVE_PDFS: False,
            CONF_EDATA_ENTRY: "auto",
            **options,
        },
    )


async def _start_user_flow(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    return result


async def test_user_flow_creates_entry(hass, mail_client, setup_entry):
    result = await _start_user_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "folder"
    folder_field = next(iter(result["data_schema"].schema))
    assert folder_field.default() == "CurEnergia"
    assert isinstance(_schema(result)[CONF_FOLDER], SelectSelector)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER: "CurEnergia"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "CurEnergía"
    assert result["data"] == {
        CONF_HOST: "imap.gmail.com",
        CONF_PORT: 993,
        CONF_USERNAME: "User@Example.es",
        CONF_PASSWORD: "app-password",
    }
    assert result["result"].unique_id == "user@example.es@imap.gmail.com"
    assert result["options"] == {
        CONF_FOLDER: "CurEnergia",
        CONF_SCAN_HOURS: 6,
        CONF_KWH_THRESHOLD: 1.0,
        CONF_SHOW_PANEL: True,
        CONF_SAVE_PDFS: False,
        CONF_EDATA_ENTRY: "auto",
    }
    mail_client.check_login.assert_called_once_with()
    assert setup_entry.setup.await_count == 1


@pytest.mark.parametrize(
    ("exc", "error"),
    [
        (MailAuthError("no"), "invalid_auth"),
        (MailConnectionError("no"), "cannot_connect"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_user_flow_errors(hass, mail_client, setup_entry, caplog, exc, error):
    result = await _start_user_flow(hass)

    mail_client.check_login.side_effect = exc
    with caplog.at_level(logging.DEBUG):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error}
    assert "User@Example.es" not in caplog.text
    assert "imap.gmail.com" not in caplog.text
    assert "app-password" not in caplog.text
    suggested = {
        str(key): (key.description or {}).get("suggested_value")
        for key in result["data_schema"].schema
    }
    assert suggested[CONF_USERNAME] == "User@Example.es"
    assert suggested[CONF_HOST] == "imap.gmail.com"
    assert suggested[CONF_PASSWORD] is None

    mail_client.check_login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "folder"


async def test_user_flow_strips_host_and_username(hass, mail_client, setup_entry):
    result = await _start_user_flow(hass)

    with patch("custom_components.curenergia.config_flow.MailClient") as cls:
        cls.return_value = mail_client
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                **USER_INPUT,
                CONF_HOST: "imap.gmail.com ",
                CONF_USERNAME: " User@Example.es ",
                CONF_PASSWORD: " keep spaces ",
            },
        )
    assert result["step_id"] == "folder"
    assert cls.call_args_list[0].args == (
        "imap.gmail.com",
        993,
        "User@Example.es",
        " keep spaces ",
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER: "INBOX"}
    )
    assert result["result"].unique_id == "user@example.es@imap.gmail.com"
    assert result["data"][CONF_HOST] == "imap.gmail.com"
    assert result["data"][CONF_USERNAME] == "User@Example.es"
    assert result["data"][CONF_PASSWORD] == " keep spaces "


async def test_user_flow_folders_unavailable(hass, mail_client, setup_entry):
    result = await _start_user_flow(hass)
    mail_client.list_folders.side_effect = MailConnectionError("no")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["step_id"] == "folder"
    assert result["errors"] == {"base": "cannot_connect"}
    assert isinstance(_schema(result)[CONF_FOLDER], TextSelector)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER: "INBOX"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"][CONF_FOLDER] == "INBOX"


async def test_user_flow_already_configured(hass, mail_client, setup_entry):
    _entry().add_to_hass(hass)
    result = await _start_user_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mail_client.check_login.assert_not_called()


async def test_reauth_flow(hass, mail_client, setup_entry):
    entry = _entry()
    await _load_entry(hass, entry, setup_entry)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert list(_schema(result)) == [CONF_PASSWORD]

    mail_client.check_login.side_effect = MailAuthError("no")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "wrong"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    mail_client.check_login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new-password"
    assert entry.data[CONF_USERNAME] == "user@example.es"
    await hass.async_block_till_done()
    _assert_reloaded(entry, setup_entry)


async def test_options_flow(hass, mail_client, setup_entry):
    edata = MockConfigEntry(domain="edata", title="Casa", entry_id="edata-1")
    edata.add_to_hass(hass)
    entry = _entry()
    await _load_entry(hass, entry, setup_entry)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert not result.get("errors")
    schema = _schema(result)
    assert isinstance(schema[CONF_FOLDER], SelectSelector)
    edata_options = [o["value"] for o in schema[CONF_EDATA_ENTRY].config["options"]]
    assert edata_options == ["auto", "edata-1"]
    assert "eur_threshold_pct" not in schema

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_FOLDER: "INBOX",
            CONF_SCAN_HOURS: 12,
            CONF_KWH_THRESHOLD: 0.5,
            CONF_SHOW_PANEL: False,
            CONF_SAVE_PDFS: True,
            CONF_EDATA_ENTRY: "edata-1",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {
        CONF_FOLDER: "INBOX",
        CONF_SCAN_HOURS: 12,
        CONF_KWH_THRESHOLD: 0.5,
        CONF_SHOW_PANEL: False,
        CONF_SAVE_PDFS: True,
        CONF_EDATA_ENTRY: "edata-1",
    }
    assert isinstance(entry.options[CONF_SCAN_HOURS], int)
    await hass.async_block_till_done()
    _assert_reloaded(entry, setup_entry)


async def test_entry_with_legacy_eur_threshold_option_still_works(
    hass, mail_client, setup_entry
):
    """Las entradas antiguas conservan ``eur_threshold_pct``: se ignora."""
    entry = _entry(eur_threshold_pct=2.0)
    await _load_entry(hass, entry, setup_entry)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert "eur_threshold_pct" not in _schema(result)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_FOLDER: "INBOX",
            CONF_SCAN_HOURS: 6,
            CONF_KWH_THRESHOLD: 1.0,
            CONF_SHOW_PANEL: True,
            CONF_SAVE_PDFS: False,
            CONF_EDATA_ENTRY: "auto",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert "eur_threshold_pct" not in entry.options
    await hass.async_block_till_done()


async def test_options_flow_keeps_unlisted_values_selectable(
    hass, mail_client, setup_entry
):
    """La carpeta o la entrada de e-data guardadas ya no existen."""
    entry = _entry(**{CONF_FOLDER: "Borrada", CONF_EDATA_ENTRY: "gone"})
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    schema = _schema(result)
    folders = list(schema[CONF_FOLDER].config["options"])
    assert folders == [*FOLDERS, "Borrada"]
    defaults = {str(k): k.default() for k in result["data_schema"].schema}
    assert defaults[CONF_FOLDER] == "Borrada"
    assert defaults[CONF_EDATA_ENTRY] == "auto"


async def test_options_flow_folders_unavailable(hass, mail_client, setup_entry):
    entry = _entry()
    entry.add_to_hass(hass)
    mail_client.list_folders.side_effect = MailConnectionError("no")

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert isinstance(_schema(result)[CONF_FOLDER], TextSelector)
    defaults = {str(k): k.default() for k in result["data_schema"].schema}
    assert defaults[CONF_FOLDER] == "CurEnergia"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_FOLDER: "Facturas/Energía",
            CONF_SCAN_HOURS: 6,
            CONF_KWH_THRESHOLD: 1.0,
            CONF_SHOW_PANEL: True,
            CONF_SAVE_PDFS: False,
            CONF_EDATA_ENTRY: "auto",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_FOLDER] == "Facturas/Energía"
    await hass.async_block_till_done()


def _keys(node, prefix=""):
    if not isinstance(node, dict):
        return {prefix}
    out = set()
    for key, value in node.items():
        out |= _keys(value, f"{prefix}/{key}")
    return out


def test_strings_match_english_translation():
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads(
        (COMPONENT / "translations" / "en.json").read_text(encoding="utf-8")
    )
    spanish = json.loads(
        (COMPONENT / "translations" / "es.json").read_text(encoding="utf-8")
    )
    assert strings == english
    assert _keys(spanish) == _keys(english)

"""Config flow, reautenticación y opciones de CurEnergía."""

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_EDATA_ENTRY,
    CONF_FOLDER,
    CONF_KWH_THRESHOLD,
    CONF_SAVE_PDFS,
    CONF_SCAN_HOURS,
    CONF_SHOW_PANEL,
    DEFAULT_HOST,
    DEFAULT_KWH_THRESHOLD,
    DEFAULT_PORT,
    DEFAULT_SAVE_PDFS,
    DEFAULT_SCAN_HOURS,
    DEFAULT_SHOW_PANEL,
    DOMAIN,
    EDATA_AUTO,
)
from .edata import edata_entries
from .mail import MailAuthError, MailClient, MailConnectionError, default_folder

_LOGGER = logging.getLogger(__name__)

TITLE = "CurEnergía"
README_URL = "https://github.com/yuuues/hacs-curenergia#readme"

_PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


def _number(
    minimum: float, maximum: float, step: float, unit: str = ""
) -> NumberSelector:
    config = NumberSelectorConfig(
        min=minimum, max=maximum, step=step, mode=NumberSelectorMode.BOX
    )
    if unit:
        config["unit_of_measurement"] = unit
    return NumberSelector(config)


async def _async_check_login(
    hass: HomeAssistant, host: str, port: int, username: str, password: str
) -> str | None:
    """Prueba el login. Devuelve la clave del error o ``None`` si va bien."""
    client = MailClient(host, port, username, password)
    try:
        await hass.async_add_executor_job(client.check_login)
    except MailAuthError:
        return "invalid_auth"
    except MailConnectionError:
        return "cannot_connect"
    except Exception:
        # Sin datos del usuario en el mensaje (privacidad).
        _LOGGER.exception("Unexpected error while checking the IMAP login")
        return "unknown"
    return None


async def _async_list_folders(
    hass: HomeAssistant, client: MailClient
) -> list[str] | None:
    """Carpetas del buzón, o ``None`` si no se pueden leer."""
    try:
        return await hass.async_add_executor_job(client.list_folders)
    except (MailAuthError, MailConnectionError):
        return None


def _folder_selector(folders: list[str] | None, current: str) -> Any:
    """Desplegable con las carpetas, o texto libre si no se pudieron leer."""
    if folders is None:
        return TextSelector()
    options = folders if current in folders else [*folders, current]
    return SelectSelector(
        SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
    )


class CurenergiaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Alta de la cuenta de correo, elección de carpeta y reautenticación."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "CurenergiaOptionsFlow":
        """Devuelve el flujo de opciones."""
        return CurenergiaOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pide los datos de la cuenta IMAP y prueba el login."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            username = user_input[CONF_USERNAME].strip()
            await self.async_set_unique_id(f"{username}@{host}".lower())
            self._abort_if_unique_id_configured()
            port = int(user_input[CONF_PORT])
            error = await _async_check_login(
                self.hass, host, port, username, user_input[CONF_PASSWORD]
            )
            if error is None:
                self._data = {
                    CONF_HOST: host,
                    CONF_PORT: port,
                    CONF_USERNAME: username,
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                }
                return await self.async_step_folder()
            errors["base"] = error

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=DEFAULT_HOST): TextSelector(),
                vol.Required(CONF_PORT, default=DEFAULT_PORT): _number(1, 65535, 1),
                vol.Required(CONF_USERNAME): TextSelector(),
                vol.Required(CONF_PASSWORD): _PASSWORD_SELECTOR,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                schema,
                # No se vuelve a sugerir la contraseña rechazada.
                {k: v for k, v in (user_input or {}).items() if k != CONF_PASSWORD},
            ),
            errors=errors,
            # hassfest no admite URL en strings.json: van como marcador.
            description_placeholders={"readme_url": README_URL},
        )

    async def async_step_folder(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Elige la carpeta con las facturas y crea la entrada."""
        if user_input is not None:
            return self.async_create_entry(
                title=TITLE,
                data=self._data,
                options={
                    CONF_FOLDER: user_input[CONF_FOLDER],
                    CONF_SCAN_HOURS: DEFAULT_SCAN_HOURS,
                    CONF_KWH_THRESHOLD: DEFAULT_KWH_THRESHOLD,
                    CONF_SHOW_PANEL: DEFAULT_SHOW_PANEL,
                    CONF_SAVE_PDFS: DEFAULT_SAVE_PDFS,
                    CONF_EDATA_ENTRY: EDATA_AUTO,
                },
            )

        client = MailClient(
            self._data[CONF_HOST],
            self._data[CONF_PORT],
            self._data[CONF_USERNAME],
            self._data[CONF_PASSWORD],
        )
        folders = await _async_list_folders(self.hass, client)
        default = default_folder(folders or [])
        return self.async_show_form(
            step_id="folder",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FOLDER, default=default): _folder_selector(
                        folders, default
                    )
                }
            ),
            errors={} if folders is not None else {"base": "cannot_connect"},
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Empieza la reautenticación."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pide la contraseña nueva."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            error = await _async_check_login(
                self.hass,
                entry.data[CONF_HOST],
                entry.data[CONF_PORT],
                entry.data[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            if error is None:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )
            errors["base"] = error
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): _PASSWORD_SELECTOR}),
            errors=errors,
        )


class CurenergiaOptionsFlow(OptionsFlowWithReload):
    """Opciones de la integración (recarga la entrada al guardarlas)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Muestra y guarda las opciones."""
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_FOLDER: user_input[CONF_FOLDER],
                    CONF_SCAN_HOURS: int(user_input[CONF_SCAN_HOURS]),
                    CONF_KWH_THRESHOLD: float(user_input[CONF_KWH_THRESHOLD]),
                    CONF_SHOW_PANEL: bool(user_input[CONF_SHOW_PANEL]),
                    CONF_SAVE_PDFS: bool(user_input[CONF_SAVE_PDFS]),
                    CONF_EDATA_ENTRY: user_input[CONF_EDATA_ENTRY],
                }
            )

        entry = self.config_entry
        current = entry.options
        client = MailClient(
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
        folders = await _async_list_folders(self.hass, client)
        folder = current.get(CONF_FOLDER, default_folder(folders or []))

        edata_options = [SelectOptionDict(value=EDATA_AUTO, label=EDATA_AUTO)]
        edata_options += [
            SelectOptionDict(value=entry_id, label=title)
            for entry_id, title in edata_entries(self.hass)
        ]
        edata_values = {option["value"] for option in edata_options}
        edata_default = current.get(CONF_EDATA_ENTRY, EDATA_AUTO)
        if edata_default not in edata_values:
            edata_default = EDATA_AUTO

        schema = vol.Schema(
            {
                vol.Required(CONF_FOLDER, default=folder): _folder_selector(
                    folders, folder
                ),
                vol.Required(
                    CONF_SCAN_HOURS,
                    default=current.get(CONF_SCAN_HOURS, DEFAULT_SCAN_HOURS),
                ): _number(1, 24, 1, "h"),
                vol.Required(
                    CONF_KWH_THRESHOLD,
                    default=current.get(CONF_KWH_THRESHOLD, DEFAULT_KWH_THRESHOLD),
                ): _number(0, 100, 0.1, "kWh"),
                vol.Required(
                    CONF_SHOW_PANEL,
                    default=current.get(CONF_SHOW_PANEL, DEFAULT_SHOW_PANEL),
                ): BooleanSelector(),
                vol.Required(
                    CONF_SAVE_PDFS,
                    default=current.get(CONF_SAVE_PDFS, DEFAULT_SAVE_PDFS),
                ): BooleanSelector(),
                vol.Required(CONF_EDATA_ENTRY, default=edata_default): SelectSelector(
                    SelectSelectorConfig(
                        options=edata_options,
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="edata_entry",
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors={} if folders is not None else {"base": "cannot_connect"},
        )

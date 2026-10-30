"""Frontend de la integración: módulo JS compartido y panel de la barra lateral."""

from pathlib import Path
from typing import Any

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import CONF_SHOW_PANEL, DEFAULT_SHOW_PANEL, DOMAIN

STATIC_URL = "/curenergia_static"
MODULE_FILE = "curenergia.js"
PANEL_PATH = "curenergia"
PANEL_ELEMENT = "curenergia-panel"
PANEL_TITLE = "Facturas"
PANEL_ICON = "mdi:receipt-text"

# Una entrada en arranque ya cuenta: ``async_update_panel`` se llama al final de
# ``async_setup_entry``, cuando todavía no ha pasado a ``LOADED``. Una que se
# está descargando (``UNLOAD_IN_PROGRESS``) ya no.
_ACTIVE_STATES = (ConfigEntryState.LOADED, ConfigEntryState.SETUP_IN_PROGRESS)

_MODULE_URL = "module_url"
_PANEL_REGISTERED = "panel_registered"


def _data(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data.setdefault(DOMAIN, {})


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Sirve la carpeta del bundle y lo carga en todas las vistas."""
    integration = await async_get_integration(hass, DOMAIN)
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                STATIC_URL, str(Path(__file__).parent / "frontend"), cache_headers=False
            )
        ]
    )
    module_url = f"{STATIC_URL}/{MODULE_FILE}?v={integration.version}"
    frontend.add_extra_js_url(hass, module_url)
    _data(hass)[_MODULE_URL] = module_url


async def async_update_panel(hass: HomeAssistant) -> None:
    """Registra o quita el panel según las entradas activas que lo quieren."""
    data = _data(hass)
    wanted = any(
        entry.options.get(CONF_SHOW_PANEL, DEFAULT_SHOW_PANEL)
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state in _ACTIVE_STATES
    )
    registered = data.get(_PANEL_REGISTERED, False)
    if wanted and not registered:
        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=PANEL_PATH,
            webcomponent_name=PANEL_ELEMENT,
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            module_url=data[_MODULE_URL],
            require_admin=True,
        )
        data[_PANEL_REGISTERED] = True
    elif not wanted and registered:
        frontend.async_remove_panel(hass, PANEL_PATH, warn_if_unknown=False)
        data[_PANEL_REGISTERED] = False

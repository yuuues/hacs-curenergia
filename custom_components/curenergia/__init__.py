"""Integración CurEnergía Facturas (lectura de facturas desde el correo)."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import CurenergiaConfigEntry, CurenergiaCoordinator
from .storage import InvoiceStore

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Configura la integración (solo mediante entradas de configuración)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: CurenergiaConfigEntry) -> bool:
    """Monta una entrada: carga lo guardado, lee el buzón y crea las entidades."""
    coordinator = CurenergiaCoordinator(hass, entry)
    await coordinator.store.async_load()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CurenergiaConfigEntry) -> bool:
    """Desmonta una entrada (los datos guardados se conservan)."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: CurenergiaConfigEntry) -> None:
    """Borra los datos guardados de una entrada eliminada."""
    await InvoiceStore(hass, entry.entry_id).async_remove()

"""Botón para buscar facturas nuevas en el buzón sin esperar al sondeo."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import CurenergiaConfigEntry, CurenergiaCoordinator
from .entity import MANUFACTURER

PARALLEL_UPDATES = 1


class CheckNowButton(ButtonEntity):
    """Lee el buzón ahora mismo.

    No es una ``CoordinatorEntity`` a propósito: debe seguir disponible cuando
    la última lectura falló, que es cuando se quiere reintentar.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "check_now"

    def __init__(self, coordinator: CurenergiaCoordinator) -> None:
        """Crea el botón de la entrada del ``coordinator``."""
        entry_id = coordinator.config_entry.entry_id
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry_id}_check_now"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=MANUFACTURER,
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_press(self) -> None:
        """Pide un refresco del coordinador."""
        await self._coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CurenergiaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Crea el botón de la entrada."""
    async_add_entities([CheckNowButton(entry.runtime_data)])

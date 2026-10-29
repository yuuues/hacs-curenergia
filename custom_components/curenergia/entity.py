"""Entidad base de los contratos de CurEnergía."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ContractData, CurenergiaCoordinator

MANUFACTURER = "CurEnergía"


def contract_identifier(entry_id: str, contract: str) -> tuple[str, str]:
    """Identificador del dispositivo de un contrato (D6)."""
    return (DOMAIN, f"{entry_id}_{contract}")


def contract_device_info(entry_id: str, data: ContractData) -> DeviceInfo:
    """Datos del dispositivo de un contrato: nombre y tarifa de la última factura."""
    latest = data.latest
    return DeviceInfo(
        identifiers={contract_identifier(entry_id, data.contract)},
        name=data.device_name,
        manufacturer=MANUFACTURER,
        model=None if latest is None else latest.stored.invoice.tariff,
    )


class CurenergiaContractEntity(CoordinatorEntity[CurenergiaCoordinator]):
    """Entidad que pertenece al dispositivo de un contrato."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: CurenergiaCoordinator, contract: str, key: str
    ) -> None:
        """Crea la entidad ``key`` del contrato ``contract``."""
        super().__init__(coordinator)
        entry_id = coordinator.config_entry.entry_id
        self._contract = contract
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry_id}_{contract}_{key}"
        self._attr_device_info = contract_device_info(
            entry_id, coordinator.data.contracts[contract]
        )

    @property
    def contract_data(self) -> ContractData | None:
        """Datos actuales del contrato (``None`` si ya no están)."""
        return self.coordinator.data.contracts.get(self._contract)

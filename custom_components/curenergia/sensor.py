"""Sensores de la última factura de cada contrato."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from pycurenergia import SupplyType

from .coordinator import CurenergiaConfigEntry, CurenergiaCoordinator
from .entity import (
    CurenergiaContractEntity,
    contract_device_info,
    contract_identifier,
)
from .matching import InvoiceRow, Status
from .util import money, price_per_kwh

PARALLEL_UPDATES = 0

EUR = "EUR"
EUR_PER_KWH = "€/kWh"

type Value = float | date | str | None


def _price_kwh(row: InvoiceRow) -> float | None:
    invoice = row.stored.invoice
    return price_per_kwh(invoice.total, invoice.kwh)


def _delta_kwh(row: InvoiceRow) -> float | None:
    return None if row.comparison is None else money(row.comparison.delta_kwh)


def _delta_eur(row: InvoiceRow) -> float | None:
    return None if row.comparison is None else money(row.comparison.delta_eur)


@dataclass(frozen=True, kw_only=True)
class CurenergiaSensorDescription(SensorEntityDescription):
    """Sensor de un dato de la última factura de un contrato."""

    value_fn: Callable[[InvoiceRow], Value]


# Ningún sensor lleva ``state_class``: no se quieren estadísticas de importes.
COMMON_SENSORS: tuple[CurenergiaSensorDescription, ...] = (
    CurenergiaSensorDescription(
        key="total",
        translation_key="total",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=EUR,
        value_fn=lambda row: money(row.stored.invoice.total),
    ),
    CurenergiaSensorDescription(
        key="kwh",
        translation_key="kwh",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda row: money(row.stored.invoice.kwh),
    ),
    CurenergiaSensorDescription(
        key="price_kwh",
        translation_key="price_kwh",
        native_unit_of_measurement=EUR_PER_KWH,
        value_fn=_price_kwh,
    ),
    CurenergiaSensorDescription(
        key="issue_date",
        translation_key="issue_date",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda row: row.stored.invoice.issue_date,
    ),
    CurenergiaSensorDescription(
        key="period_start",
        translation_key="period_start",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda row: row.stored.invoice.period_start,
    ),
    CurenergiaSensorDescription(
        key="period_end",
        translation_key="period_end",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda row: row.stored.invoice.period_end,
    ),
    CurenergiaSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=[status.value for status in Status],
        value_fn=lambda row: row.status.value,
    ),
)

ELECTRICITY_SENSORS: tuple[CurenergiaSensorDescription, ...] = (
    CurenergiaSensorDescription(
        key="delta_kwh",
        translation_key="delta_kwh",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=_delta_kwh,
    ),
    CurenergiaSensorDescription(
        key="delta_eur",
        translation_key="delta_eur",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=EUR,
        value_fn=_delta_eur,
    ),
)


class CurenergiaSensor(CurenergiaContractEntity, SensorEntity):
    """Dato de la última factura de un contrato."""

    entity_description: CurenergiaSensorDescription

    def __init__(
        self,
        coordinator: CurenergiaCoordinator,
        contract: str,
        description: CurenergiaSensorDescription,
    ) -> None:
        """Crea el sensor ``description`` del contrato ``contract``."""
        super().__init__(coordinator, contract, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Value:
        """Valor de la última factura; ``None`` si el contrato no tiene ninguna."""
        data = self.contract_data
        latest = None if data is None else data.latest
        if latest is None:
            return None
        return self.entity_description.value_fn(latest)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CurenergiaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Crea los sensores de cada contrato, también los que aparezcan después."""
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def _sync_contracts() -> None:
        contracts = coordinator.data.contracts
        _sync_devices(hass, entry, coordinator)
        new = sorted(set(contracts) - known)
        if not new:
            return
        known.update(new)
        entities: list[CurenergiaSensor] = []
        for contract in new:
            descriptions = COMMON_SENSORS
            if contracts[contract].supply is SupplyType.ELECTRICITY:
                descriptions += ELECTRICITY_SENSORS
            entities.extend(
                CurenergiaSensor(coordinator, contract, description)
                for description in descriptions
            )
        async_add_entities(entities)

    _sync_contracts()
    entry.async_on_unload(coordinator.async_add_listener(_sync_contracts))


def _sync_devices(
    hass: HomeAssistant,
    entry: CurenergiaConfigEntry,
    coordinator: CurenergiaCoordinator,
) -> None:
    """Pone al día nombre y modelo de los dispositivos ya creados.

    Un segundo contrato del mismo suministro cambia el nombre del primero (D6),
    y la tarifa de la última factura puede cambiar.
    """
    registry = dr.async_get(hass)
    devices = {
        identifier: device
        for device in dr.async_entries_for_config_entry(registry, entry.entry_id)
        for identifier in device.identifiers
    }
    for contract, data in coordinator.data.contracts.items():
        device = devices.get(contract_identifier(entry.entry_id, contract))
        if device is None:
            continue
        info = contract_device_info(entry.entry_id, data)
        if device.name != info["name"] or device.model != info["model"]:
            registry.async_update_device(
                device.id, name=info["name"], model=info["model"]
            )

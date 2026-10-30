"""Pruebas de los sensores de la última factura de cada contrato."""

from collections.abc import Callable, Iterator
from dataclasses import replace
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pycurenergia import Invoice

from custom_components.curenergia.const import DOMAIN
from custom_components.curenergia.coordinator import CurenergiaCoordinator
from custom_components.curenergia.matching import Status, Totals, comparable_eur

from .helpers import FakeMailbox, make_entry, setup_entry

pytestmark = pytest.mark.usefixtures("recorder_mock", "enable_custom_integrations")

ELECTRICITY_KEYS = {
    "total",
    "kwh",
    "price_kwh",
    "issue_date",
    "period_start",
    "period_end",
    "status",
    "delta_kwh",
    "delta_eur",
}
GAS_KEYS = ELECTRICITY_KEYS - {"delta_kwh", "delta_eur"}


@pytest.fixture
def edata_totals() -> Iterator[Callable[[Totals | None], None]]:
    """Sustituye el proveedor de e-data por uno que devuelve siempre ``Totals``."""
    current: list[Totals | None] = [None]

    async def totals_provider(self, cups):
        async def provider(start, end):
            return current[0]

        return provider

    def set_totals(totals: Totals | None) -> None:
        current[0] = totals

    with patch.object(CurenergiaCoordinator, "async_totals_provider", totals_provider):
        yield set_totals


def _totals(invoice: Invoice, **changes) -> Totals:
    """Totales de e-data iguales a los de la factura (salvo ``changes``)."""
    values = {"kwh": invoice.kwh, "p1": None, "p2": None, "p3": None, "eur": None}
    values.update(changes)
    return Totals(**values)


def _entity_id(hass: HomeAssistant, entry_id: str, contract: str, key: str) -> str:
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{entry_id}_{contract}_{key}"
    )
    assert entity_id is not None, key
    return entity_id


def _device(hass: HomeAssistant, entry_id: str, contract: str):
    identifier = (DOMAIN, f"{entry_id}_{contract}")
    devices = [
        device
        for device in dr.async_entries_for_config_entry(dr.async_get(hass), entry_id)
        if identifier in device.identifiers
    ]
    assert len(devices) <= 1
    return devices[0] if devices else None


def _sensor_entries(hass: HomeAssistant, entry_id: str, contract: str):
    registry = er.async_get(hass)
    return [
        e
        for e in er.async_entries_for_config_entry(registry, entry_id)
        if e.domain == "sensor" and e.unique_id.startswith(f"{entry_id}_{contract}_")
    ]


async def test_contract_sensors_created(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice, fixture_invoice
):
    elec = make_invoice(estimated=False)
    gas = fixture_invoice("gas_2026-09")
    mailbox.add(1, (b"luz", elec))
    mailbox.add(2, (b"gas", gas))
    entry = make_entry()

    await setup_entry(hass, entry)

    luz = _sensor_entries(hass, entry.entry_id, elec.contract)
    assert {e.unique_id for e in luz} == {
        f"{entry.entry_id}_{elec.contract}_{key}" for key in ELECTRICITY_KEYS
    }
    assert {e.translation_key for e in luz} == ELECTRICITY_KEYS
    assert len(luz) == 9
    gas_entries = _sensor_entries(hass, entry.entry_id, gas.contract)
    assert {e.unique_id for e in gas_entries} == {
        f"{entry.entry_id}_{gas.contract}_{key}" for key in GAS_KEYS
    }
    assert len(gas_entries) == 7


async def test_sensor_values_latest_invoice(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice, edata_totals
):
    older = make_invoice(
        estimated=False,
        number="OLD-1",
        period_start=date(2026, 7, 29),
        period_end=date(2026, 8, 29),
        total=Decimal("1.00"),
        kwh=Decimal("1.0"),
    )
    latest = make_invoice(estimated=False)
    mailbox.add(1, (b"old", older))
    mailbox.add(2, (b"new", latest))
    edata_totals(_totals(latest))
    entry = make_entry()

    await setup_entry(hass, entry)

    def state(key: str):
        return hass.states.get(_entity_id(hass, entry.entry_id, latest.contract, key))

    assert float(state("total").state) == round(float(latest.total), 2)
    assert float(state("kwh").state) == round(float(latest.kwh), 2)
    assert float(state("price_kwh").state) == round(float(latest.total / latest.kwh), 4)
    assert state("issue_date").state == latest.issue_date.isoformat()
    assert state("period_start").state == latest.period_start.isoformat()
    assert state("period_end").state == latest.period_end.isoformat()
    assert state("status").state == "ok"
    assert float(state("delta_kwh").state) == 0.0
    assert state("total").attributes["device_class"] == SensorDeviceClass.MONETARY
    assert state("total").attributes["unit_of_measurement"] == "EUR"
    assert state("kwh").attributes["device_class"] == SensorDeviceClass.ENERGY
    assert state("kwh").attributes["unit_of_measurement"] == "kWh"
    assert state("price_kwh").attributes["unit_of_measurement"] == "€/kWh"
    assert "device_class" not in state("price_kwh").attributes
    assert state("status").attributes["options"] == [s.value for s in Status]


async def test_price_kwh_unknown_without_energy(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice
):
    elec = make_invoice(estimated=False, kwh=Decimal(0))
    mailbox.add(1, (b"luz", elec))
    entry = make_entry()

    await setup_entry(hass, entry)

    state = hass.states.get(
        _entity_id(hass, entry.entry_id, elec.contract, "price_kwh")
    )
    assert state.state == STATE_UNKNOWN


async def test_delta_sensors_from_comparison(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice, edata_totals
):
    elec = make_invoice(estimated=False)
    mailbox.add(1, (b"luz", elec))
    edata_totals(
        _totals(
            elec,
            kwh=elec.kwh - Decimal("0.567"),
            eur=comparable_eur(elec) - Decimal("1.234"),
        )
    )
    entry = make_entry()

    await setup_entry(hass, entry)

    kwh = hass.states.get(_entity_id(hass, entry.entry_id, elec.contract, "delta_kwh"))
    eur = hass.states.get(_entity_id(hass, entry.entry_id, elec.contract, "delta_eur"))
    assert float(kwh.state) == 0.57
    assert kwh.attributes["device_class"] == SensorDeviceClass.ENERGY
    assert kwh.attributes["unit_of_measurement"] == "kWh"
    assert float(eur.state) == 1.23
    assert eur.attributes["device_class"] == SensorDeviceClass.MONETARY
    assert eur.attributes["unit_of_measurement"] == "EUR"


async def test_delta_sensors_unknown_without_comparison(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice
):
    elec = make_invoice(estimated=False)
    mailbox.add(1, (b"luz", elec))
    entry = make_entry()

    await setup_entry(hass, entry)

    for key in ("delta_kwh", "delta_eur"):
        state = hass.states.get(_entity_id(hass, entry.entry_id, elec.contract, key))
        assert state.state == STATE_UNKNOWN
    status = hass.states.get(_entity_id(hass, entry.entry_id, elec.contract, "status"))
    assert status.state == Status.NO_DATA.value


async def test_gas_sensors(hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice):
    gas = fixture_invoice("gas_2026-09")
    mailbox.add(1, (b"gas", gas))
    entry = make_entry()

    await setup_entry(hass, entry)

    status = hass.states.get(_entity_id(hass, entry.entry_id, gas.contract, "status"))
    assert status.state == "gas"
    total = hass.states.get(_entity_id(hass, entry.entry_id, gas.contract, "total"))
    assert float(total.state) == round(float(gas.total), 2)


async def test_no_state_class(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice, fixture_invoice
):
    mailbox.add(1, (b"luz", make_invoice(estimated=False)))
    mailbox.add(2, (b"gas", fixture_invoice("gas_2026-09")))
    entry = make_entry()

    await setup_entry(hass, entry)

    registry = er.async_get(hass)
    sensors = [
        e
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if e.domain == "sensor"
    ]
    assert len(sensors) == 16
    for sensor in sensors:
        assert "state_class" not in hass.states.get(sensor.entity_id).attributes


async def test_new_contract_adds_entities(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice, fixture_invoice
):
    gas = fixture_invoice("gas_2026-09")
    mailbox.add(1, (b"gas", gas))
    entry = make_entry()
    await setup_entry(hass, entry)
    elec = make_invoice(estimated=False)
    assert _sensor_entries(hass, entry.entry_id, elec.contract) == []

    mailbox.add(2, (b"luz", elec))
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert len(_sensor_entries(hass, entry.entry_id, elec.contract)) == 9
    assert len(_sensor_entries(hass, entry.entry_id, gas.contract)) == 7
    state = hass.states.get(_entity_id(hass, entry.entry_id, elec.contract, "total"))
    assert float(state.state) == round(float(elec.total), 2)


async def test_two_electricity_contracts_named_by_suffix(
    hass: HomeAssistant,
    mailbox: FakeMailbox,
    make_invoice,
    fixture_invoice,
):
    first = make_invoice(estimated=False, number="A1", contract="CT-0001234")
    second = make_invoice(estimated=False, number="B1", contract="CT-0005678")
    gas = fixture_invoice("gas_2026-09")
    mailbox.add(1, (b"a", first))
    mailbox.add(2, (b"b", second))
    mailbox.add(3, (b"gas", gas))
    entry = make_entry()

    await setup_entry(hass, entry)

    names = {}
    for contract in (first.contract, second.contract, gas.contract):
        device = _device(hass, entry.entry_id, contract)
        assert device is not None
        names[contract] = device.name
        assert device.manufacturer == "CurEnergía"
    assert names == {
        "CT-0001234": "CurEnergía luz 1234",
        "CT-0005678": "CurEnergía luz 5678",
        gas.contract: "CurEnergía gas",
    }
    device = _device(hass, entry.entry_id, "CT-0001234")
    assert device.model == first.tariff
    entity_id = _entity_id(hass, entry.entry_id, "CT-0001234", "total")
    assert entity_id.startswith("sensor.curenergia_luz_1234_")


async def test_second_contract_of_same_supply_renames_first_device(
    hass: HomeAssistant,
    mailbox: FakeMailbox,
    make_invoice,
):
    first = make_invoice(estimated=False, number="A1", contract="CT-0001234")
    mailbox.add(1, (b"a", first))
    entry = make_entry()
    await setup_entry(hass, entry)
    assert _device(hass, entry.entry_id, "CT-0001234").name == "CurEnergía luz"

    mailbox.add(
        2, (b"b", make_invoice(estimated=False, number="B1", contract="CT-0005678"))
    )
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert _device(hass, entry.entry_id, "CT-0001234").name == "CurEnergía luz 1234"
    assert _device(hass, entry.entry_id, "CT-0005678").name == "CurEnergía luz 5678"


async def test_sensors_tolerate_missing_invoices(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice
):
    elec = make_invoice(estimated=False)
    mailbox.add(1, (b"luz", elec))
    entry = make_entry()
    await setup_entry(hass, entry)
    coordinator = entry.runtime_data
    contract = coordinator.data.contracts[elec.contract]
    total = _entity_id(hass, entry.entry_id, elec.contract, "total")

    # Contrato sin facturas: los sensores quedan sin valor.
    empty = replace(contract, rows=[])
    coordinator.async_set_updated_data(
        replace(coordinator.data, contracts={elec.contract: empty})
    )
    await hass.async_block_till_done()
    assert hass.states.get(total).state == STATE_UNKNOWN

    # Contrato que desaparece de los datos.
    coordinator.async_set_updated_data(replace(coordinator.data, contracts={}))
    await hass.async_block_till_done()
    assert hass.states.get(total).state == STATE_UNKNOWN

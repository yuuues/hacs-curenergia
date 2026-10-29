"""Pruebas del esqueleto de la integración."""

from homeassistant.loader import async_get_integration
from pycurenergia import SupplyType

from custom_components.curenergia.const import DOMAIN


async def test_manifest_loads(hass):
    integration = await async_get_integration(hass, DOMAIN)
    assert integration.requirements == ["pycurenergia==0.1.0"]
    assert integration.config_flow is True


def test_fixture_invoice_parses(fixture_invoice):
    assert fixture_invoice("electricity_2026-10").supply is SupplyType.ELECTRICITY
    assert fixture_invoice("gas_2026-09").supply is SupplyType.GAS


def test_make_invoice_replaces_fields(make_invoice, fixture_invoice):
    base = fixture_invoice("electricity_2026-10")
    changed = make_invoice(estimated=not base.estimated)
    assert changed.estimated is not base.estimated
    assert changed.number == base.number

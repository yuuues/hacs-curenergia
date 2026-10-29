"""Fixtures comunes de los tests de la integración."""

from collections.abc import Callable

import pytest
from homeassistant.core import HomeAssistant
from pycurenergia import Invoice

from .helpers import load_fixture_invoice
from .helpers import make_invoice as _make_invoice


@pytest.fixture
async def madrid_tz(hass: HomeAssistant) -> None:
    """Fija la zona horaria de Home Assistant a Europe/Madrid."""
    await hass.config.async_set_time_zone("Europe/Madrid")


@pytest.fixture
def fixture_invoice() -> Callable[[str], Invoice]:
    """Devuelve una función que parsea una fixture de ``lib/tests/fixtures``."""
    return load_fixture_invoice


@pytest.fixture
def make_invoice() -> Callable[..., Invoice]:
    """Devuelve ``tests.helpers.make_invoice``."""
    return _make_invoice

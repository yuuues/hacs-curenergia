"""Fixtures comunes de los tests de la integración."""

from collections.abc import Callable, Iterator
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pycurenergia import Invoice

from .helpers import FakeMailbox, load_fixture_invoice
from .helpers import make_invoice as _make_invoice


@pytest.fixture
def mailbox() -> Iterator[FakeMailbox]:
    """Sustituye el IMAP y el parser de PDF del coordinador por un buzón falso."""
    box = FakeMailbox()
    with (
        patch(
            "custom_components.curenergia.coordinator.MailClient", return_value=box
        ) as client_cls,
        patch(
            "custom_components.curenergia.coordinator.parse_invoice_pdf",
            side_effect=box.parse,
        ),
    ):
        box.client_cls = client_cls
        yield box


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

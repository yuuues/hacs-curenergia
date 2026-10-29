"""Utilidades de test: facturas construidas a partir de las fixtures anonimizadas."""

from collections.abc import Callable, Collection, Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pycurenergia import Invoice, parse_invoice_text
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.curenergia.const import (
    CONF_EDATA_ENTRY,
    CONF_EUR_THRESHOLD_PCT,
    CONF_FOLDER,
    CONF_KWH_THRESHOLD,
    CONF_SAVE_PDFS,
    CONF_SCAN_HOURS,
    CONF_SHOW_PANEL,
    DOMAIN,
    EDATA_AUTO,
)
from custom_components.curenergia.coordinator import CurenergiaCoordinator
from custom_components.curenergia.mail import (
    DEFAULT_FETCH_LIMIT,
    FetchResult,
    MailMessage,
)
from custom_components.curenergia.matching import Totals

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "lib" / "tests" / "fixtures"

ENTRY_DATA = {
    CONF_HOST: "imap.example.es",
    CONF_PORT: 993,
    CONF_USERNAME: "user@example.es",
    CONF_PASSWORD: "app-password",
}


def integration_log(caplog: Any) -> str:
    """Texto de los registros de la integración (sin los del arnés de tests)."""
    return "\n".join(
        record.getMessage()
        for record in caplog.records
        if record.name.startswith("custom_components.curenergia")
    )


def make_entry(**options: Any) -> MockConfigEntry:
    """Entrada de CurEnergía con las opciones por defecto (y los cambios dados)."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="CurEnergía",
        unique_id=ENTRY_DATA[CONF_USERNAME],
        data=dict(ENTRY_DATA),
        options={
            CONF_FOLDER: "INBOX",
            CONF_SCAN_HOURS: 6,
            CONF_KWH_THRESHOLD: 1.0,
            CONF_EUR_THRESHOLD_PCT: 2.0,
            CONF_SHOW_PANEL: True,
            CONF_SAVE_PDFS: False,
            CONF_EDATA_ENTRY: EDATA_AUTO,
            **options,
        },
    )


async def setup_entry(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    state: ConfigEntryState = ConfigEntryState.LOADED,
) -> None:
    """Añade y monta la entrada, y comprueba el estado resultante."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is state


class FakeMailbox:
    """Buzón falso: sustituye a ``MailClient`` y a ``parse_invoice_pdf``.

    Cada PDF es un ``bytes`` cualquiera; ``pdfs`` dice qué devuelve el parser
    para él (una ``Invoice``) o qué excepción lanza.
    """

    def __init__(self) -> None:
        self.uidvalidity = 1
        # UID → mensaje; ``None`` para correos que ``MailClient`` descarta
        # (otro remitente o FETCH vacío): están en ``all_uids`` sin mensaje.
        self.messages: dict[int, MailMessage | None] = {}
        self.pdfs: dict[bytes, Invoice | Exception] = {}
        self.error: Exception | None = None
        # UID de más de 15 MB: ``MailClient`` no los descarga (R26).
        self.oversized: set[int] = set()
        # Se llama con el número de la llamada a ``fetch`` (1, 2…) al empezarla.
        self.on_fetch: Callable[[int], None] | None = None
        self.calls: list[tuple[str, frozenset[int], int | None]] = []
        self.parsed: list[bytes] = []
        # Doble de la clase ``MailClient`` (lo pone la fixture ``mailbox``).
        self.client_cls: Any = None

    def add(
        self,
        uid: int,
        *pdfs: tuple[bytes, Invoice | Exception],
        email_total: Decimal | None = None,
    ) -> None:
        """Añade el correo ``uid`` con sus PDF (``(contenido, resultado)``)."""
        for data, result in pdfs:
            self.pdfs[data] = result
        self.messages[uid] = MailMessage(
            uid=uid, email_total=email_total, pdfs=tuple(data for data, _ in pdfs)
        )

    def fetch(
        self,
        folder: str,
        skip_uids: Collection[int],
        uidvalidity: int | None,
        limit: int = DEFAULT_FETCH_LIMIT,
    ) -> FetchResult:
        """Imita ``MailClient.fetch`` (``uidvalidity``, tamaño y lotes)."""
        skip = frozenset(skip_uids)
        self.calls.append((folder, skip, uidvalidity))
        if self.on_fetch is not None:
            self.on_fetch(len(self.calls))
        if self.error is not None:
            raise self.error
        if uidvalidity != self.uidvalidity:
            skip = frozenset()
        new = sorted(set(self.messages) - skip)
        wanted = [uid for uid in new if uid not in self.oversized]
        batch = wanted[:limit]
        return FetchResult(
            uidvalidity=self.uidvalidity,
            all_uids=frozenset(self.messages),
            messages=tuple(
                message for uid in batch if (message := self.messages[uid]) is not None
            ),
            fetched=frozenset(batch),
            oversized=frozenset(new) & frozenset(self.oversized),
            remaining=len(wanted) > len(batch),
        )

    def parse(self, data: bytes) -> Invoice:
        """Imita ``parse_invoice_pdf``."""
        self.parsed.append(data)
        result = self.pdfs[data]
        if isinstance(result, Exception):
            raise result
        return result


def load_fixture_invoice(name: str) -> Invoice:
    """Parsea ``lib/tests/fixtures/<name>.txt`` (p. ej. ``electricity_2026-10``)."""
    text = (FIXTURES_DIR / f"{name}.txt").read_text(encoding="utf-8")
    return parse_invoice_text(text)


def make_invoice(**changes: Any) -> Invoice:
    """Factura de luz de la fixture con los campos indicados sustituidos."""
    return replace(load_fixture_invoice("electricity_2026-10"), **changes)


@contextmanager
def fake_totals(
    provider: Callable[[datetime, datetime], Totals | None],
) -> Iterator[None]:
    """Sustituye el proveedor de e-data de todos los contratos por ``provider``."""

    async def totals_provider(self: CurenergiaCoordinator, cups: str):
        async def wrapped(start: datetime, end: datetime) -> Totals | None:
            return provider(start, end)

        return wrapped

    with patch.object(CurenergiaCoordinator, "async_totals_provider", totals_provider):
        yield

"""Pruebas del coordinador: lectura del buzón, ingesta y casación."""

import copy
import errno
import logging
import os
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pycurenergia import (
    InvoiceParseError,
    InvoiceReadError,
    SupplyType,
    UnsupportedInvoiceError,
    __version__,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.curenergia.const import CONF_EDATA_ENTRY, EDATA_AUTO
from custom_components.curenergia.coordinator import (
    ContractData,
    CurenergiaCoordinator,
)
from custom_components.curenergia.mail import MailConnectionError
from custom_components.curenergia.matching import InvoiceRow, Status, Totals
from custom_components.curenergia.storage import InvoiceStore, MailState, build_stored

from .helpers import (
    ENTRY_DATA,
    FakeMailbox,
    integration_log,
    make_entry,
    setup_entry,
)

pytestmark = pytest.mark.usefixtures("recorder_mock", "enable_custom_integrations")

STORE_KEY = "curenergia.{}"
VERSION_ATTR = "custom_components.curenergia.coordinator.LIB_VERSION"


def _real(invoice):
    """La misma factura, con periodo real (no estimada)."""
    return replace(invoice, estimated=False)


async def _setup(hass: HomeAssistant, **options) -> CurenergiaCoordinator:
    entry = make_entry(**options)
    await setup_entry(hass, entry)
    return entry.runtime_data


async def test_first_refresh_stores_invoices(
    hass: HomeAssistant, hass_storage, mailbox: FakeMailbox, fixture_invoice
):
    elec = _real(fixture_invoice("electricity_2026-10"))
    gas = fixture_invoice("gas_2026-09")
    mailbox.add(1, (b"pdf-luz", elec), email_total=elec.total)
    mailbox.add(2, (b"pdf-gas", gas))

    coordinator = await _setup(hass)

    host, port, username, password = mailbox.client_cls.call_args.args
    assert (host, port, username, password) == tuple(ENTRY_DATA.values())
    assert mailbox.calls == [("INBOX", frozenset(), None)]
    assert coordinator.update_interval == timedelta(hours=6)

    store = coordinator.store
    assert set(store.invoices) == {elec.number, gas.number}
    assert store.invoices[elec.number].email_total == elec.total
    assert store.mail.seen == {1, 2}
    assert store.mail.uidvalidity == 1
    assert store.mail.folder == "INBOX"
    saved = hass_storage[STORE_KEY.format(coordinator.config_entry.entry_id)]
    assert saved["data"]["mail"]["seen"] == [1, 2]
    assert set(saved["data"]["invoices"]) == {elec.number, gas.number}

    data = coordinator.data
    assert set(data.contracts) == {elec.contract, gas.contract}
    luz = data.contracts[elec.contract]
    assert luz.supply is SupplyType.ELECTRICITY
    assert luz.device_name == "CurEnergía luz"
    assert [row.status for row in luz.rows] == [Status.NO_DATA]
    assert luz.latest is luz.rows[0]
    gas_data = data.contracts[gas.contract]
    assert gas_data.device_name == "CurEnergía gas"
    assert [row.status for row in gas_data.rows] == [Status.GAS]
    assert data.unreadable_emails == 0
    assert data.unsupported_emails == 0
    assert data.mail_error is False
    assert data.last_mail_check is not None


async def test_duplicate_invoice_kept_once(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice
):
    elec = _real(fixture_invoice("electricity_2026-10"))
    mailbox.add(1, (b"first", elec), email_total=elec.total)
    mailbox.add(2, (b"forwarded", elec), email_total=Decimal("1.00"))

    coordinator = await _setup(hass)

    store = coordinator.store
    assert list(store.invoices) == [elec.number]
    # Se conserva la del primer UID (la del reenvío tendría otro importe).
    assert store.invoices[elec.number].email_total == elec.total
    assert store.invoices[elec.number].problems == []
    assert store.mail.seen == {1, 2}
    assert len(coordinator.data.contracts[elec.contract].rows) == 1


async def test_message_without_pdf_marked_seen(
    hass: HomeAssistant, mailbox: FakeMailbox
):
    mailbox.add(1)  # aviso del remitente, sin PDF
    mailbox.messages[2] = None  # descartado por MailClient (otro remitente)

    coordinator = await _setup(hass)

    assert coordinator.store.invoices == {}
    assert coordinator.store.mail.seen == {1, 2}
    assert coordinator.data.contracts == {}

    await coordinator.async_refresh()
    assert mailbox.calls[-1] == ("INBOX", frozenset({1, 2}), 1)


def _batched_mailbox(mailbox: FakeMailbox, make_invoice) -> tuple[str, str]:
    """25 correos nuevos: facturas en los UID 1 y 25, avisos en el resto."""
    first = make_invoice(estimated=False, number="N-01")
    last = make_invoice(estimated=False, number="N-25")
    mailbox.add(1, (b"first", first))
    for uid in range(2, 25):
        mailbox.add(uid)
    mailbox.add(25, (b"last", last))
    return first.number, last.number


async def test_entry_with_legacy_eur_threshold_option_loads(
    hass: HomeAssistant, hass_storage, mailbox: FakeMailbox, fixture_invoice
):
    """Una entrada antigua con ``eur_threshold_pct`` en las opciones se ignora."""
    elec = _real(fixture_invoice("electricity_2026-10"))
    mailbox.add(1, (b"pdf-luz", elec), email_total=elec.total)

    coordinator = await _setup(hass, eur_threshold_pct=2.0)

    assert set(coordinator.store.invoices) == {elec.number}
    assert coordinator.last_update_success


async def test_first_sync_downloads_in_batches(
    hass: HomeAssistant, hass_storage, mailbox: FakeMailbox, make_invoice
):
    first, last = _batched_mailbox(mailbox, make_invoice)
    entry = make_entry()
    key = STORE_KEY.format(entry.entry_id)
    saved_before_second_batch: dict = {}

    def on_fetch(call: int) -> None:
        if call == 2:
            saved_before_second_batch.update(copy.deepcopy(hass_storage[key]))

    mailbox.on_fetch = on_fetch
    await setup_entry(hass, entry)

    # R26: lotes de 20; el segundo ya salta los UID del primero.
    assert mailbox.calls == [
        ("INBOX", frozenset(), None),
        ("INBOX", frozenset(range(1, 21)), 1),
    ]
    # El Store se guardó tras el primer lote.
    assert saved_before_second_batch["data"]["mail"]["seen"] == list(range(1, 21))
    assert list(saved_before_second_batch["data"]["invoices"]) == [first]

    store = entry.runtime_data.store
    assert store.mail.seen == set(range(1, 26))
    assert set(store.invoices) == {first, last}
    saved = hass_storage[key]["data"]
    assert saved["mail"]["seen"] == list(range(1, 26))
    assert set(saved["invoices"]) == {first, last}


async def test_failure_in_second_batch_keeps_first_batch(
    hass: HomeAssistant, hass_storage, mailbox: FakeMailbox, make_invoice
):
    first, last = _batched_mailbox(mailbox, make_invoice)
    entry = make_entry()
    key = STORE_KEY.format(entry.entry_id)

    def on_fetch(call: int) -> None:
        if call == 2:
            raise MailConnectionError("Cannot connect to the IMAP server (OSError)")

    mailbox.on_fetch = on_fetch
    # R21: el primer lote ya guardó una factura, así que la entrada carga.
    await setup_entry(hass, entry)

    coordinator = entry.runtime_data
    assert coordinator.data.mail_error is True
    store = coordinator.store
    assert store.mail.seen == set(range(1, 21))
    assert set(store.invoices) == {first}
    saved = hass_storage[key]["data"]
    assert saved["mail"]["seen"] == list(range(1, 21))
    assert set(saved["invoices"]) == {first}

    # El siguiente refresco sigue donde se quedó.
    mailbox.on_fetch = None
    await coordinator.async_refresh()
    assert mailbox.calls[-1] == ("INBOX", frozenset(range(1, 21)), 1)
    assert coordinator.data.mail_error is False
    assert store.mail.seen == set(range(1, 26))
    assert set(store.invoices) == {first, last}


PARTIAL_READ = "The mailbox was not fully read"


async def test_batch_cap_stops_and_resumes_on_next_refresh(
    hass: HomeAssistant, hass_storage, mailbox: FakeMailbox, caplog
):
    for uid in range(1, 46):
        mailbox.add(uid)
    entry = make_entry()
    key = STORE_KEY.format(entry.entry_id)

    with (
        patch("custom_components.curenergia.coordinator.MAX_BATCHES_PER_REFRESH", 2),
        caplog.at_level(logging.WARNING),
    ):
        await setup_entry(hass, entry)

        # R31: dos lotes de 20 y se para; los UID 41..45 no se dan por vistos.
        assert len(mailbox.calls) == 2
        coordinator = entry.runtime_data
        assert coordinator.store.mail.seen == set(range(1, 41))
        assert hass_storage[key]["data"]["mail"]["seen"] == list(range(1, 41))
        assert coordinator.data.mail_error is False
        assert coordinator.mail_folder_messages == 45
        assert coordinator.mail_last_read_complete is False
        records = [r for r in caplog.records if PARTIAL_READ in r.getMessage()]
        assert len(records) == 1
        assert records[0].levelno == logging.WARNING
        assert records[0].args in ((), None)

        await coordinator.async_refresh()

    assert mailbox.calls[-1] == ("INBOX", frozenset(range(1, 41)), 1)
    assert coordinator.store.mail.seen == set(range(1, 46))
    assert coordinator.mail_last_read_complete is True
    assert coordinator.mail_last_error is None


async def test_batch_without_progress_stops_the_loop(
    hass: HomeAssistant, mailbox: FakeMailbox, caplog
):
    for uid in range(1, 4):
        mailbox.add(uid)
    real_fetch = mailbox.fetch

    def stuck_fetch(*args, **kwargs):
        # Servidor que no deja avanzar: dice que quedan correos pero no da ninguno.
        result = real_fetch(*args, **kwargs)
        return replace(result, messages=(), fetched=frozenset(), remaining=True)

    mailbox.fetch = stuck_fetch  # type: ignore[method-assign]
    with caplog.at_level(logging.WARNING):
        coordinator = await _setup(hass)

    assert len(mailbox.calls) == 1
    # Sin R16: los UID no descargados no se marcan como vistos.
    assert coordinator.store.mail.seen == set()
    assert coordinator.mail_folder_messages == 3
    assert coordinator.mail_last_read_complete is False
    records = [r for r in caplog.records if PARTIAL_READ in r.getMessage()]
    assert len(records) == 1


async def test_oversized_message_counted_as_unsupported(
    hass: HomeAssistant, mailbox: FakeMailbox, caplog
):
    mailbox.add(1)
    mailbox.add(2)
    mailbox.oversized = {2}

    with caplog.at_level(logging.WARNING):
        coordinator = await _setup(hass)

    mail = coordinator.store.mail
    assert mail.seen == {1}
    assert mail.unsupported == {2}
    assert coordinator.data.unsupported_emails == 1
    assert "UID 2: the message is larger than 15 MB" in integration_log(caplog)

    await coordinator.async_refresh()
    assert mailbox.calls[-1] == ("INBOX", frozenset({1, 2}), 1)
    assert coordinator.store.mail.unsupported == {2}


async def test_parse_error_recorded_and_retried_on_new_version(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice, caplog
):
    elec = _real(fixture_invoice("electricity_2026-10"))
    mailbox.add(1, (b"bad-1", InvoiceParseError("number")))
    mailbox.add(2, (b"bad-2", InvoiceReadError("damaged")))
    mailbox.add(3, (b"good", elec))

    with caplog.at_level(logging.WARNING):
        coordinator = await _setup(hass)

    mail = coordinator.store.mail
    assert mail.failed == {1: __version__, 2: __version__}
    assert mail.seen == {3}
    assert coordinator.data.unreadable_emails == 2
    assert "UID 1" in caplog.text
    assert "UID 2" in caplog.text

    # Misma versión: no se reintenta.
    await coordinator.async_refresh()
    assert mailbox.calls[-1][1] == frozenset({1, 2, 3})
    assert mailbox.parsed == [b"bad-1", b"bad-2", b"good"]

    # Otra versión de la librería: se reintentan; uno ya se lee.
    mailbox.pdfs[b"bad-1"] = elec
    with patch(VERSION_ATTR, "9.9.9"):
        await coordinator.async_refresh()

    assert mailbox.calls[-1][1] == frozenset({3})
    assert mailbox.parsed[3:] == [b"bad-1", b"bad-2"]
    mail = coordinator.store.mail
    assert mail.failed == {2: "9.9.9"}
    assert mail.seen == {1, 3}
    # El duplicado (UID 1 trae la misma factura que el 3) no se guarda dos veces.
    assert list(coordinator.store.invoices) == [elec.number]
    assert coordinator.data.unreadable_emails == 1


async def test_unexpected_parser_error_recorded_as_failed(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice, caplog
):
    elec = _real(fixture_invoice("electricity_2026-10"))
    mailbox.add(4, (b"weird", RuntimeError(f"SECRET page text {elec.number}")))
    mailbox.add(5, (b"good", elec))

    with caplog.at_level(logging.DEBUG):
        coordinator = await _setup(hass)

    # El refresco sigue con el resto de correos (R17).
    assert coordinator.last_update_success is True
    mail = coordinator.store.mail
    assert mail.failed == {4: __version__}
    assert mail.seen == {5}
    assert list(coordinator.store.invoices) == [elec.number]
    assert coordinator.data.unreadable_emails == 1
    records = [
        r for r in caplog.records if r.name.startswith("custom_components.curenergia")
    ]
    warning = [r for r in records if "UID 4" in r.getMessage()]
    assert len(warning) == 1
    assert warning[0].levelno == logging.WARNING
    assert "RuntimeError" in warning[0].getMessage()
    assert warning[0].exc_info is None
    log = integration_log(caplog)
    assert "SECRET" not in log
    assert elec.number not in log

    # Se reintenta solo con otra versión de la librería.
    await coordinator.async_refresh()
    assert mailbox.parsed.count(b"weird") == 1
    with patch(VERSION_ATTR, "9.9.9"):
        await coordinator.async_refresh()
    assert mailbox.parsed.count(b"weird") == 2
    assert coordinator.store.mail.failed == {4: "9.9.9"}


async def test_unsupported_not_retried(hass: HomeAssistant, mailbox: FakeMailbox):
    mailbox.add(1, (b"credit-note", UnsupportedInvoiceError("abono")))

    coordinator = await _setup(hass)

    mail = coordinator.store.mail
    assert mail.unsupported == {1}
    assert mail.seen == set()
    assert mail.failed == {}
    assert coordinator.data.unsupported_emails == 1

    with patch(VERSION_ATTR, "9.9.9"):
        await coordinator.async_refresh()
    assert mailbox.calls[-1][1] == frozenset({1})
    assert mailbox.parsed == [b"credit-note"]
    assert coordinator.data.unsupported_emails == 1


async def test_message_with_failed_and_unsupported_pdfs_is_failed(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice
):
    elec = _real(fixture_invoice("electricity_2026-10"))
    mailbox.add(
        1,
        (b"ok", elec),
        (b"credit-note", UnsupportedInvoiceError("abono")),
        (b"bad", InvoiceParseError("total")),
    )
    mailbox.add(2, (b"ok-2", elec), (b"credit-note-2", UnsupportedInvoiceError("x")))

    coordinator = await _setup(hass)

    mail = coordinator.store.mail
    # Un PDF ilegible manda: se reintentará con otra versión.
    assert mail.failed == {1: __version__}
    assert mail.unsupported == {2}
    assert mail.seen == set()
    assert list(coordinator.store.invoices) == [elec.number]


async def test_uidvalidity_change_reprocesses_without_duplicates(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice
):
    elec = _real(fixture_invoice("electricity_2026-10"))
    gas = fixture_invoice("gas_2026-09")
    mailbox.add(1, (b"luz", elec))
    mailbox.add(2, (b"gas", gas))
    mailbox.add(3, (b"bad", InvoiceReadError("damaged")))
    coordinator = await _setup(hass)
    assert coordinator.store.mail.failed == {3: __version__}

    # El servidor renumera la carpeta.
    mailbox.uidvalidity = 2
    mailbox.messages.clear()
    mailbox.add(10, (b"luz", elec))
    mailbox.add(11, (b"gas", gas))
    await coordinator.async_refresh()

    # Se pide con el estado viejo; MailClient lo ignora al no cuadrar UIDVALIDITY.
    assert mailbox.calls[-1] == ("INBOX", frozenset({1, 2, 3}), 1)
    mail = coordinator.store.mail
    assert mail.uidvalidity == 2
    assert mail.seen == {10, 11}
    assert mail.failed == {}
    assert mail.folder == "INBOX"
    assert set(coordinator.store.invoices) == {elec.number, gas.number}
    assert all(len(c.rows) == 1 for c in coordinator.data.contracts.values())


async def test_folder_change_resets_mail_state(
    hass: HomeAssistant, hass_storage, mailbox: FakeMailbox, fixture_invoice
):
    elec = _real(fixture_invoice("electricity_2026-10"))
    entry = make_entry(folder="Facturas/Energía")
    hass_storage[STORE_KEY.format(entry.entry_id)] = {
        "version": 1,
        "key": STORE_KEY.format(entry.entry_id),
        "data": {
            "invoices": {},
            "mail": {
                "uidvalidity": 1,
                "folder": "INBOX",
                "seen": [1, 2],
                "failed": {"3": "0.0.1"},
                "unsupported": [4],
            },
        },
    }
    mailbox.add(1, (b"luz", elec))

    await setup_entry(hass, entry)

    coordinator = entry.runtime_data
    assert mailbox.calls == [("Facturas/Energía", frozenset(), None)]
    mail = coordinator.store.mail
    assert mail.folder == "Facturas/Energía"
    assert mail.seen == {1}
    assert mail.failed == {}
    assert mail.unsupported == set()
    assert list(coordinator.store.invoices) == [elec.number]


async def test_connection_error_later_keeps_data(
    hass: HomeAssistant, hass_storage, mailbox: FakeMailbox, fixture_invoice, caplog
):
    elec = _real(fixture_invoice("electricity_2026-10"))
    mailbox.add(1, (b"luz", elec))
    mailbox.add(2, (b"bad", InvoiceReadError("damaged")))
    coordinator = await _setup(hass)
    before = coordinator.data
    store = coordinator.store
    mail_before = MailState.from_dict(store.mail.to_dict())
    invoices_before = dict(store.invoices)
    key = STORE_KEY.format(coordinator.config_entry.entry_id)
    saved_before = copy.deepcopy(hass_storage[key])

    mailbox.error = MailConnectionError("Cannot connect to the IMAP server (OSError)")
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    data = coordinator.data
    assert data.mail_error is True
    assert data.contracts == before.contracts
    assert data.last_mail_check == before.last_mail_check
    assert data.unreadable_emails == 1
    records = [r for r in caplog.records if "mailbox" in r.getMessage()]
    assert len(records) == 1
    assert records[0].levelno == logging.WARNING
    assert records[0].name == "custom_components.curenergia.coordinator"
    assert "Cannot connect to the IMAP server (OSError)" in records[0].getMessage()
    # Ni el estado del buzón ni las facturas cambian, ni se reescribe el Store.
    assert store.mail == mail_before
    assert store.invoices == invoices_before
    assert hass_storage[key] == saved_before

    mailbox.error = None
    await coordinator.async_refresh()
    assert coordinator.data.mail_error is False
    assert coordinator.data.last_mail_check >= before.last_mail_check


async def test_unexpected_fetch_error_later_keeps_data(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice, caplog
):
    elec = _real(fixture_invoice("electricity_2026-10"))
    mailbox.add(1, (b"luz", elec))
    coordinator = await _setup(hass)
    before = coordinator.data

    mailbox.error = RuntimeError(f"SECRET {elec.number}")
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await coordinator.async_refresh()

    # R22: igual que un fallo de conexión (D5).
    assert coordinator.last_update_success is True
    assert coordinator.data.mail_error is True
    assert coordinator.data.contracts == before.contracts
    records = [
        r
        for r in caplog.records
        if r.name.startswith("custom_components.curenergia")
        and r.levelno >= logging.WARNING
    ]
    assert len(records) == 1
    assert records[0].levelno == logging.WARNING
    assert "RuntimeError" in records[0].getMessage()
    assert records[0].exc_info is None
    assert "SECRET" not in caplog.text


def _stored_payload(entry_id: str, *invoices) -> dict:
    return {
        "version": 1,
        "key": STORE_KEY.format(entry_id),
        "data": {
            "invoices": {
                inv.number: build_stored(inv, None).to_dict() for inv in invoices
            },
            "mail": {"uidvalidity": 1, "folder": "INBOX", "seen": [1]},
            "readings_backfilled": True,
        },
    }


async def test_stored_invoices_get_their_readings_once(
    hass: HomeAssistant, hass_storage, mailbox: FakeMailbox, fixture_invoice
):
    gas = fixture_invoice("gas_2026-09")
    without = replace(gas, reading_m3=None, previous_reading_m3=None)
    entry = make_entry()
    payload = _stored_payload(entry.entry_id, without)
    del payload["data"]["readings_backfilled"]
    hass_storage[STORE_KEY.format(entry.entry_id)] = payload
    mailbox.add(1, (b"gas", gas))

    await setup_entry(hass, entry)

    coordinator = entry.runtime_data
    # Se vuelve a leer el correo ya visto, sin duplicar la factura.
    assert mailbox.calls == [("INBOX", frozenset(), None)]
    assert mailbox.parsed == [b"gas"]
    assert list(coordinator.store.invoices) == [gas.number]
    assert coordinator.store.invoices[gas.number].invoice.reading_m3 == gas.reading_m3
    assert coordinator.store.mail.seen == {1}
    await coordinator.store.async_save()
    assert hass_storage[STORE_KEY.format(entry.entry_id)]["data"]["readings_backfilled"]

    # Solo una vez: un nuevo arranque ya no relee nada.
    reloaded = InvoiceStore(hass, entry.entry_id)
    await reloaded.async_load()
    assert reloaded.mail.seen == {1}


@pytest.mark.parametrize(
    "error",
    [MailConnectionError("Cannot connect to the IMAP server"), RuntimeError("x")],
)
async def test_mail_error_on_setup_serves_stored_invoices(
    hass: HomeAssistant, hass_storage, mailbox: FakeMailbox, fixture_invoice, error
):
    gas = fixture_invoice("gas_2026-09")
    entry = make_entry()
    hass_storage[STORE_KEY.format(entry.entry_id)] = _stored_payload(
        entry.entry_id, gas
    )
    mailbox.error = error

    # R21: con facturas guardadas, el primer refresco no falla.
    await setup_entry(hass, entry)

    data = entry.runtime_data.data
    assert data.mail_error is True
    assert data.last_mail_check is None
    assert list(data.contracts) == [gas.contract]


@pytest.mark.parametrize(
    "error",
    [MailConnectionError("Cannot connect to the IMAP server"), RuntimeError("SECRET")],
)
async def test_mail_error_on_setup_with_empty_store_retries(
    hass: HomeAssistant, mailbox: FakeMailbox, caplog, error
):
    mailbox.error = error

    await setup_entry(hass, make_entry(), ConfigEntryState.SETUP_RETRY)

    assert "SECRET" not in caplog.text


async def test_email_total_used_only_with_a_single_pdf(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice
):
    elec = _real(fixture_invoice("electricity_2026-10"))
    gas = fixture_invoice("gas_2026-09")
    # R20: con dos PDF no se sabe a cuál corresponde el importe del correo.
    mailbox.add(1, (b"luz", elec), (b"gas", gas), email_total=elec.total)

    coordinator = await _setup(hass)

    invoices = coordinator.store.invoices
    assert invoices[elec.number].email_total is None
    assert invoices[gas.number].email_total is None
    assert invoices[gas.number].problems == build_stored(gas, None).problems


async def test_build_stored_error_recorded_as_failed(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice, caplog
):
    elec = _real(fixture_invoice("electricity_2026-10"))
    mailbox.add(1, (b"luz", elec))

    with (
        patch(
            "custom_components.curenergia.coordinator.build_stored",
            side_effect=ValueError(f"SECRET {elec.number}"),
        ),
        caplog.at_level(logging.WARNING),
    ):
        coordinator = await _setup(hass)

    assert coordinator.store.invoices == {}
    assert coordinator.store.mail.failed == {1: __version__}
    log = integration_log(caplog)
    assert "UID 1" in log
    assert "ValueError" in log
    assert "SECRET" not in caplog.text


async def test_save_pdfs_partial_write_removed(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice, tmp_path, caplog
):
    hass.config.config_dir = str(tmp_path)
    elec = _real(fixture_invoice("electricity_2026-10"))
    mailbox.add(2, (b"%PDF-luz", elec))
    real_open = Path.open

    class FailingFile:
        def __init__(self, file):
            self._file = file

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self._file.close()

        def write(self, data):
            self._file.write(data[:3])
            raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))

    def fake_open(self, mode="r", *args, **kwargs):
        file = real_open(self, mode, *args, **kwargs)
        return FailingFile(file) if mode == "xb" else file

    with (
        patch.object(Path, "open", fake_open),
        caplog.at_level(logging.WARNING),
    ):
        coordinator = await _setup(hass, save_pdfs=True)

    assert list(coordinator.store.invoices) == [elec.number]
    assert list((tmp_path / "curenergia").iterdir()) == []
    log = integration_log(caplog)
    assert "UID 2" in log
    assert "OSError" in log
    assert elec.number not in log


async def test_save_pdfs_option_writes_file(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice, tmp_path
):
    hass.config.config_dir = str(tmp_path)
    elec = _real(fixture_invoice("electricity_2026-10"))
    gas = fixture_invoice("gas_2026-09")
    mailbox.add(1, (b"%PDF-luz", elec))
    mailbox.add(2, (b"%PDF-reenvio", elec))
    mailbox.add(3, (b"%PDF-gas", gas))
    mailbox.add(4, (b"%PDF-roto", InvoiceReadError("damaged")))

    await _setup(hass, save_pdfs=True)

    folder = tmp_path / "curenergia"
    assert sorted(p.name for p in folder.iterdir()) == sorted(
        [f"{elec.number}.pdf", f"{gas.number}.pdf"]
    )
    assert (folder / f"{elec.number}.pdf").read_bytes() == b"%PDF-luz"
    assert (folder / f"{gas.number}.pdf").read_bytes() == b"%PDF-gas"


async def test_save_pdfs_disabled_writes_nothing(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice, tmp_path
):
    hass.config.config_dir = str(tmp_path)
    mailbox.add(1, (b"%PDF-luz", _real(fixture_invoice("electricity_2026-10"))))

    await _setup(hass)

    assert not (tmp_path / "curenergia").exists()


async def test_save_pdfs_error_logged_without_data(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice, tmp_path, caplog
):
    hass.config.config_dir = str(tmp_path)
    (tmp_path / "curenergia").write_text("not a folder")
    elec = _real(fixture_invoice("electricity_2026-10"))
    mailbox.add(7, (b"%PDF-luz", elec))

    with caplog.at_level(logging.WARNING):
        coordinator = await _setup(hass, save_pdfs=True)

    assert list(coordinator.store.invoices) == [elec.number]
    assert coordinator.store.mail.seen == {7}
    log = integration_log(caplog)
    assert "UID 7" in log
    assert elec.number not in log
    assert str(tmp_path) not in log


async def test_save_pdfs_rejects_unsafe_number(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice, tmp_path, caplog
):
    config = tmp_path / "config"
    config.mkdir()
    hass.config.config_dir = str(config)
    evil = make_invoice(estimated=False, number="../evil")
    long = make_invoice(estimated=False, number="A" * 65, contract="CT-2")
    mailbox.add(8, (b"%PDF-evil", evil))
    mailbox.add(9, (b"%PDF-long", long))

    with caplog.at_level(logging.WARNING):
        coordinator = await _setup(hass, save_pdfs=True)

    # Las facturas se guardan en el Store; los PDF no se escriben en ningún sitio.
    assert set(coordinator.store.invoices) == {"../evil", "A" * 65}
    assert [p for p in tmp_path.rglob("*") if p.is_file()] == []
    log = integration_log(caplog)
    assert "UID 8" in log
    assert "UID 9" in log
    assert "evil" not in log
    assert "A" * 65 not in log


async def test_save_pdfs_never_overwrites(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice, tmp_path, caplog
):
    hass.config.config_dir = str(tmp_path)
    folder = tmp_path / "curenergia"
    folder.mkdir()
    elec = _real(fixture_invoice("electricity_2026-10"))
    (folder / f"{elec.number}.pdf").write_bytes(b"original")
    mailbox.add(1, (b"%PDF-luz", elec))

    with caplog.at_level(logging.WARNING):
        coordinator = await _setup(hass, save_pdfs=True)

    assert list(coordinator.store.invoices) == [elec.number]
    assert (folder / f"{elec.number}.pdf").read_bytes() == b"original"
    assert "UID 1" not in integration_log(caplog)


async def test_save_pdfs_refuses_symlink_out_of_folder(
    hass: HomeAssistant, mailbox: FakeMailbox, fixture_invoice, tmp_path, caplog
):
    hass.config.config_dir = str(tmp_path)
    folder = tmp_path / "curenergia"
    folder.mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"outside")
    elec = _real(fixture_invoice("electricity_2026-10"))
    (folder / f"{elec.number}.pdf").symlink_to(outside)
    mailbox.add(3, (b"%PDF-luz", elec))

    with caplog.at_level(logging.WARNING):
        await _setup(hass, save_pdfs=True)

    assert outside.read_bytes() == b"outside"
    log = integration_log(caplog)
    assert "UID 3" in log
    assert elec.number not in log


async def test_unreadable_invoice_logged_without_data(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice, caplog
):
    bad = make_invoice(estimated=False, total=Decimal("1.00"))
    mailbox.add(5, (b"bad", bad), email_total=Decimal("2.00"))
    mailbox.add(6, (b"bad-again", bad))

    with caplog.at_level(logging.DEBUG):
        coordinator = await _setup(hass)

    stored = coordinator.store.invoices[bad.number]
    assert stored.unreadable
    rows = coordinator.data.contracts[bad.contract].rows
    assert [row.status for row in rows] == [Status.UNREADABLE]
    messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    unreadable = [m for m in messages if "UID 5" in m]
    assert len(unreadable) == 1
    assert all(code in unreadable[0] for code in stored.problems)
    # Solo una vez: la copia del UID 6 no es una factura nueva.
    assert not [m for m in messages if "UID 6" in m]
    log = integration_log(caplog)
    for secret in (bad.number, bad.contract, bad.cups, "1.00", "2.00"):
        assert secret not in log


async def test_matching_uses_edata_provider_and_thresholds(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice
):
    elec = make_invoice(estimated=False)
    edata = MockConfigEntry(
        domain="edata", data={"cups": elec.cups.lower(), "scups": "ABCD"}
    )
    edata.add_to_hass(hass)
    mailbox.add(1, (b"luz", elec))
    windows = []

    async def provider(start, end):
        windows.append((start, end))
        return Totals(
            kwh=elec.kwh - Decimal("0.6"), p1=None, p2=None, p3=None, eur=None
        )

    with patch(
        "custom_components.curenergia.coordinator.make_provider",
        return_value=provider,
    ) as make:
        coordinator = await _setup(hass, kwh_threshold=0.5)

    make.assert_called_once_with(hass, "abcd")
    assert len(windows) == 1
    row = coordinator.data.contracts[elec.contract].rows[0]
    # |Δ| = 0,6 kWh > 0,5 (umbral de las opciones).
    assert row.status is Status.MISMATCH
    assert row.comparison.delta_kwh == Decimal("0.6")


async def test_matching_threshold_is_strict(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice
):
    elec = make_invoice(estimated=False)
    MockConfigEntry(
        domain="edata", data={"cups": elec.cups, "scups": "abcd"}
    ).add_to_hass(hass)
    mailbox.add(1, (b"luz", elec))

    async def provider(start, end):
        return Totals(
            kwh=elec.kwh - Decimal("0.5"), p1=None, p2=None, p3=None, eur=None
        )

    with patch(
        "custom_components.curenergia.coordinator.make_provider",
        return_value=provider,
    ):
        coordinator = await _setup(hass, kwh_threshold=0.5)

    assert coordinator.data.contracts[elec.contract].rows[0].status is Status.OK


def _tagging_make_provider(used: list[tuple[str, str]]):
    """Doble de ``make_provider``: anota qué id de e-data usa cada ventana."""

    def make(hass, edata_id):
        async def provider(start, end):
            used.append((edata_id, start.date().isoformat()))
            return None

        provider.edata_id = edata_id
        return provider

    return make


async def test_totals_provider_override_and_missing(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice
):
    elec = make_invoice(estimated=False)
    other = MockConfigEntry(domain="edata", data={"cups": "ES-OTHER", "scups": "WXYZ"})
    other.add_to_hass(hass)
    mailbox.add(1, (b"luz", elec))
    used: list[tuple[str, str]] = []

    with patch(
        "custom_components.curenergia.coordinator.make_provider",
        side_effect=_tagging_make_provider(used),
    ):
        coordinator = await _setup(hass, edata_entry=other.entry_id)
        # Único contrato de luz sin e-data por CUPS: se usa el vínculo manual.
        assert [edata_id for edata_id, _ in used] == ["wxyz"]
        provider = await coordinator.async_totals_provider(elec.cups.lower())
        assert provider.edata_id == "wxyz"
        # Un CUPS que no es el de ese contrato no recibe el vínculo manual.
        assert await coordinator.async_totals_provider("ES-SOMETHING-ELSE") is None

        hass.config_entries.async_update_entry(
            coordinator.config_entry,
            options={**coordinator.config_entry.options, CONF_EDATA_ENTRY: EDATA_AUTO},
        )
        assert await coordinator.async_totals_provider(elec.cups) is None


async def test_override_only_for_the_single_unmatched_contract(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice
):
    matched = make_invoice(estimated=False, number="A1", contract="CT-A", cups="ES-A")
    unmatched = make_invoice(estimated=False, number="B1", contract="CT-B", cups="ES-B")
    MockConfigEntry(domain="edata", data={"cups": "ES-A", "scups": "AAAA"}).add_to_hass(
        hass
    )
    manual = MockConfigEntry(domain="edata", data={"cups": "ES-X", "scups": "XXXX"})
    manual.add_to_hass(hass)
    mailbox.add(1, (b"a", matched))
    mailbox.add(2, (b"b", unmatched))
    used: list[tuple[str, str]] = []

    with patch(
        "custom_components.curenergia.coordinator.make_provider",
        side_effect=_tagging_make_provider(used),
    ):
        coordinator = await _setup(hass, edata_entry=manual.entry_id)
        assert sorted(edata_id for edata_id, _ in used) == ["aaaa", "xxxx"]
        assert (await coordinator.async_totals_provider("ES-A")).edata_id == "aaaa"
        assert (await coordinator.async_totals_provider("ES-B")).edata_id == "xxxx"


async def test_override_applies_to_contracts_sharing_the_unmatched_cups(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice
):
    old = make_invoice(estimated=False, number="A1", contract="CT-A", cups="ES-M")
    new = make_invoice(estimated=False, number="B1", contract="CT-B", cups="es-m")
    manual = MockConfigEntry(domain="edata", data={"cups": "ES-X", "scups": "XXXX"})
    manual.add_to_hass(hass)
    mailbox.add(1, (b"a", old))
    mailbox.add(2, (b"b", new))
    used: list[tuple[str, str]] = []

    with patch(
        "custom_components.curenergia.coordinator.make_provider",
        side_effect=_tagging_make_provider(used),
    ):
        coordinator = await _setup(hass, edata_entry=manual.entry_id)
        # R19b: mismo CUPS = mismo contador; el vínculo manual vale para ambos.
        assert [edata_id for edata_id, _ in used] == ["xxxx", "xxxx"]
        assert (await coordinator.async_totals_provider("ES-M")).edata_id == "xxxx"


async def test_override_unmatched_cups_compared_by_first_20_characters(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice
):
    old = make_invoice(
        estimated=False, number="A1", contract="CT-A", cups="ES0000000000000000MM"
    )
    new = make_invoice(
        estimated=False, number="B1", contract="CT-B", cups="es0000000000000000mm1F"
    )
    manual = MockConfigEntry(
        domain="edata", data={"cups": "ES0000000000000000XX", "scups": "XXXX"}
    )
    manual.add_to_hass(hass)
    mailbox.add(1, (b"a", old))
    mailbox.add(2, (b"b", new))
    used: list[tuple[str, str]] = []

    with patch(
        "custom_components.curenergia.coordinator.make_provider",
        side_effect=_tagging_make_provider(used),
    ):
        await _setup(hass, edata_entry=manual.entry_id)
        # R28: el mismo CUPS de 20 caracteres, con y sin sufijo, es un contador.
        assert [edata_id for edata_id, _ in used] == ["xxxx", "xxxx"]


async def test_override_ignored_when_entry_is_auto_linked_to_another_cups(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice
):
    matched = make_invoice(
        estimated=False, number="A1", contract="CT-A", cups="ES0000000000000000AA"
    )
    unmatched = make_invoice(
        estimated=False, number="B1", contract="CT-B", cups="ES0000000000000000BB"
    )
    # La entrada guarda el CUPS de 22 caracteres: casa con A por sus 20 primeros.
    linked = MockConfigEntry(
        domain="edata", data={"cups": "ES0000000000000000AA1F", "scups": "AAAA"}
    )
    linked.add_to_hass(hass)
    mailbox.add(1, (b"a", matched))
    mailbox.add(2, (b"b", unmatched))
    used: list[tuple[str, str]] = []

    with patch(
        "custom_components.curenergia.coordinator.make_provider",
        side_effect=_tagging_make_provider(used),
    ):
        coordinator = await _setup(hass, edata_entry=linked.entry_id)
        # R29: la entrada ya es de A; no se usa también para B.
        assert [edata_id for edata_id, _ in used] == ["aaaa"]
        assert await coordinator.async_totals_provider(unmatched.cups) is None

    statuses = {
        contract: data.rows[0].status
        for contract, data in coordinator.data.contracts.items()
    }
    assert statuses["CT-B"] is Status.NO_DATA


async def test_override_ignored_with_several_unmatched_contracts(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice
):
    first = make_invoice(estimated=False, number="A1", contract="CT-A", cups="ES-A")
    second = make_invoice(estimated=False, number="B1", contract="CT-B", cups="ES-B")
    manual = MockConfigEntry(domain="edata", data={"cups": "ES-X", "scups": "XXXX"})
    manual.add_to_hass(hass)
    mailbox.add(1, (b"a", first))
    mailbox.add(2, (b"b", second))

    with patch("custom_components.curenergia.coordinator.make_provider") as make:
        coordinator = await _setup(hass, edata_entry=manual.entry_id)
        assert await coordinator.async_totals_provider("ES-A") is None
        assert await coordinator.async_totals_provider("ES-B") is None

    make.assert_not_called()
    rows = [c.rows[0].status for c in coordinator.data.contracts.values()]
    assert rows == [Status.NO_DATA, Status.NO_DATA]


async def test_device_names_and_latest(
    hass: HomeAssistant, mailbox: FakeMailbox, make_invoice, fixture_invoice
):
    first = make_invoice(estimated=False, number="A1", contract="CT-0001234")
    later = make_invoice(
        estimated=False,
        number="A2",
        contract="CT-0001234",
        period_start=date(2026, 9, 28),
        period_end=date(2026, 10, 28),
    )
    second = make_invoice(estimated=False, number="B1", contract="CT-0005678")
    gas = fixture_invoice("gas_2026-09")
    mailbox.add(1, (b"a2", later))
    mailbox.add(2, (b"a1", first))
    mailbox.add(3, (b"b1", second))
    mailbox.add(4, (b"gas", gas))

    coordinator = await _setup(hass)

    contracts = coordinator.data.contracts
    assert contracts["CT-0001234"].device_name == "CurEnergía luz 1234"
    assert contracts["CT-0005678"].device_name == "CurEnergía luz 5678"
    assert contracts[gas.contract].device_name == "CurEnergía gas"
    assert contracts["CT-0001234"].latest.stored.invoice.number == "A2"


def test_contract_data_latest_empty(fixture_invoice):
    data = ContractData(
        contract="CT", supply=SupplyType.GAS, rows=[], device_name="CurEnergía gas"
    )
    assert data.latest is None
    stored = build_stored(fixture_invoice("gas_2026-09"), None)
    row = InvoiceRow(stored, Status.GAS, None)
    assert ContractData("CT", SupplyType.GAS, [row], "CurEnergía gas").latest is row

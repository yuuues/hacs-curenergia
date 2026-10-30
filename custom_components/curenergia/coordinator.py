"""Coordinador: lee el buzón, guarda las facturas nuevas y las casa con e-data."""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from pycurenergia import (
    InvoiceParseError,
    InvoiceReadError,
    SupplyType,
    UnsupportedInvoiceError,
    parse_invoice_pdf,
)
from pycurenergia import __version__ as LIB_VERSION

from .const import (
    CONF_EDATA_ENTRY,
    CONF_EUR_THRESHOLD_PCT,
    CONF_FOLDER,
    CONF_KWH_THRESHOLD,
    CONF_SAVE_PDFS,
    CONF_SCAN_HOURS,
    DEFAULT_SAVE_PDFS,
    DOMAIN,
    EDATA_AUTO,
)
from .edata import cups_key, edata_entry_cups_key, find_edata_id, make_provider
from .mail import (
    FetchResult,
    MailAuthError,
    MailClient,
    MailConnectionError,
    MailMessage,
)
from .matching import InvoiceRow, Thresholds, Totals, TotalsProvider, match_contract
from .storage import InvoiceStore, StoredInvoice, build_stored

_LOGGER = logging.getLogger(__name__)

# R31: lotes de correo como mucho por refresco (unos 1000 correos).
MAX_BATCHES_PER_REFRESH = 50

# R18: números de factura que se pueden usar como nombre de fichero.
_SAFE_NUMBER = re.compile(r"[A-Za-z0-9_-]{1,64}")

type CurenergiaConfigEntry = ConfigEntry[CurenergiaCoordinator]

# D6: nombre del dispositivo de cada contrato según su suministro.
_DEVICE_NAMES = {
    SupplyType.ELECTRICITY: "CurEnergía luz",
    SupplyType.GAS: "CurEnergía gas",
}


@dataclass(frozen=True)
class ContractData:
    """Facturas casadas de un contrato."""

    contract: str
    supply: SupplyType
    rows: list[InvoiceRow]
    device_name: str

    @property
    def latest(self) -> InvoiceRow | None:
        """La factura con el periodo más reciente (mayor ``period_end``)."""
        return max(
            self.rows, key=lambda row: row.stored.invoice.period_end, default=None
        )


@dataclass(frozen=True)
class CoordinatorData:
    """Resultado de un refresco."""

    contracts: dict[str, ContractData]
    # Correos con algún PDF que no se pudo leer (D4).
    unreadable_emails: int
    # Correos con facturas no soportadas: rectificativas, abonos (D4).
    unsupported_emails: int
    # Última lectura correcta del buzón (en esta ejecución de HA).
    last_mail_check: datetime | None
    # El último intento de leer el buzón falló por conexión (D5).
    mail_error: bool


async def _no_totals(start: datetime, end: datetime) -> Totals | None:
    """Proveedor para contratos sin e-data: nunca hay datos."""
    return None


class _UnsafePathError(Exception):
    """La ruta del PDF saldría de la carpeta de PDF."""


def _save_pdf(folder: Path, name: str, data: bytes) -> None:
    """Guarda ``data`` como ``folder/name`` sin salir de ``folder`` ni sobrescribir.

    Si el fichero ya existe, se da por guardado y no se toca.
    """
    folder.mkdir(parents=True, exist_ok=True)
    root = folder.resolve()
    path = (root / name).resolve()
    if path.parent != root:
        raise _UnsafePathError
    try:
        file = path.open("xb")
    except FileExistsError:
        return
    try:
        with file:
            file.write(data)
    except OSError:
        # No se deja un PDF a medias (se daría por guardado para siempre).
        path.unlink(missing_ok=True)
        raise


class CurenergiaCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Sondea el buzón y mantiene las facturas casadas de una entrada."""

    config_entry: CurenergiaConfigEntry

    def __init__(self, hass: HomeAssistant, entry: CurenergiaConfigEntry) -> None:
        """Prepara el coordinador de la entrada ``entry``."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(hours=entry.options[CONF_SCAN_HOURS]),
        )
        self.store = InvoiceStore(hass, entry.entry_id)
        # Diagnósticos del buzón, solo en memoria (no van al Store).
        # UID del remitente que devolvió el último SEARCH.
        self.mail_folder_messages: int | None = None
        # El último refresco leyó la carpeta hasta el final.
        self.mail_last_read_complete = False
        # Clase de la excepción del último fallo del correo (sin su mensaje).
        self.mail_last_error: str | None = None

    async def async_totals_provider(self, cups: str) -> TotalsProvider | None:
        """Proveedor de sumas de e-data para ``cups``; ``None`` si no hay e-data."""
        edata_id = self._edata_id(cups)
        if edata_id is None:
            return None
        return make_provider(self.hass, edata_id)

    def _edata_id(self, cups: str) -> str | None:
        """Id de e-data de ``cups`` (R19).

        Primero se busca por CUPS. El vínculo manual de las opciones solo se
        aplica si ``cups`` es el único CUPS de luz guardado que no tiene
        e-data por CUPS (aunque lo compartan varios contratos), y si la
        entrada elegida no está ya vinculada por CUPS a otro CUPS de luz
        guardado (R29).
        """
        edata_id = find_edata_id(self.hass, cups, None)
        if edata_id is not None:
            return edata_id
        override = self.config_entry.options.get(CONF_EDATA_ENTRY, EDATA_AUTO)
        if override == EDATA_AUTO:
            return None
        # R19b: se cuentan CUPS distintos (contratos con el mismo CUPS son el
        # mismo contador; R28: por sus 20 primeros caracteres).
        electricity = {
            cups_key(stored.invoice.cups)
            for stored in self.store.invoices.values()
            if stored.invoice.supply is SupplyType.ELECTRICITY
        }
        unmatched = {
            key for key in electricity if find_edata_id(self.hass, key, None) is None
        }
        if unmatched != {cups_key(cups)}:
            return None
        # R29: la entrada elegida ya está vinculada por CUPS a otro contador.
        if edata_entry_cups_key(self.hass, override) in electricity:
            return None
        return find_edata_id(self.hass, cups, override)

    async def _async_update_data(self) -> CoordinatorData:
        options = self.config_entry.options
        folder = options[CONF_FOLDER]
        if self.store.mail.folder != folder:
            # R4: el estado del buzón es de otra carpeta.
            self.store.reset_mail()
            self.store.mail.folder = folder

        data = self.config_entry.data
        client = MailClient(
            data[CONF_HOST], data[CONF_PORT], data[CONF_USERNAME], data[CONF_PASSWORD]
        )
        save_pdfs = options.get(CONF_SAVE_PDFS, DEFAULT_SAVE_PDFS)
        # R26: por lotes, guardando el Store tras cada uno; si falla un lote,
        # lo ya guardado se queda. R31: como mucho MAX_BATCHES_PER_REFRESH
        # lotes, y se para si un lote no avanza; el resto, en el siguiente sondeo.
        complete = False
        batch = 0
        while True:
            batch += 1
            mail = self.store.mail
            retry_later = {
                uid for uid, version in mail.failed.items() if version == LIB_VERSION
            }
            skip = mail.seen | mail.unsupported | retry_later
            try:
                result = await self.hass.async_add_executor_job(
                    client.fetch, folder, frozenset(skip), mail.uidvalidity
                )
            except MailAuthError as err:
                self._record_mail_failure(err)
                raise ConfigEntryAuthFailed(
                    "The IMAP server rejected the login"
                ) from err
            except Exception as err:  # noqa: BLE001
                self._record_mail_failure(err)
                return await self._async_mail_failed(err)

            self.mail_folder_messages = len(result.all_uids)
            await self._async_ingest_batch(result, folder, save_pdfs)
            if not result.remaining:
                complete = True
                break
            if not result.fetched or batch == MAX_BATCHES_PER_REFRESH:
                break
            await self.store.async_save()

        self.mail_last_read_complete = complete
        if complete:
            self._forget_and_mark_seen(result.all_uids)
        else:
            # Sin R16: los UID que faltan no se pueden dar por vistos.
            _LOGGER.warning(
                "The mailbox was not fully read; the rest will be read on the "
                "next check"
            )
        await self.store.async_save()

        return await self._async_build_data(
            mail_error=False, last_mail_check=dt_util.utcnow()
        )

    def _record_mail_failure(self, err: Exception) -> None:
        """Anota el fallo para los diagnósticos: solo la clase (R22)."""
        self.mail_last_error = type(err).__name__
        self.mail_last_read_complete = False

    def _forget_and_mark_seen(self, all_uids: frozenset[int]) -> None:
        """Tras leer todo el buzón: olvida los UID que ya no están en la
        carpeta y marca el resto como vistos (R16)."""
        mail = self.store.mail
        mail.failed = {
            uid: version for uid, version in mail.failed.items() if uid in all_uids
        }
        mail.unsupported &= all_uids
        mail.seen = set(all_uids - mail.failed.keys() - mail.unsupported)

    async def _async_mail_failed(self, err: Exception) -> CoordinatorData:
        """Fallo al leer el buzón: se sirven las facturas guardadas (D5, R21).

        Sin facturas guardadas en el primer refresco, lanza ``UpdateFailed``.
        """
        # R22: un error inesperado cuenta como fallo de conexión. Su mensaje
        # podría llevar datos, así que solo se registra la clase.
        if isinstance(err, MailConnectionError):
            reason = str(err)
        else:
            reason = type(err).__name__
        if self.data is None and not self.store.invoices:
            raise UpdateFailed(f"Cannot read the mailbox: {reason}") from None
        _LOGGER.warning("Cannot read the mailbox, keeping stored invoices: %s", reason)
        return await self._async_build_data(
            mail_error=True,
            last_mail_check=None if self.data is None else self.data.last_mail_check,
        )

    async def _async_ingest_batch(
        self, result: FetchResult, folder: str, save_pdfs: bool
    ) -> None:
        """Guarda las facturas de un lote y marca sus UID (R26)."""
        if result.uidvalidity != self.store.mail.uidvalidity:
            # Los UID guardados ya no valen: se olvidan (las facturas se quedan).
            self.store.reset_mail()
            self.store.mail.folder = folder
            self.store.mail.uidvalidity = result.uidvalidity

        for message in result.messages:
            await self._async_ingest(message, save_pdfs)

        mail = self.store.mail
        # Solo los UID de este lote: el resto se marca al acabar (R16).
        mail.seen |= result.fetched - mail.failed.keys() - mail.unsupported
        for uid in sorted(result.oversized):
            _LOGGER.warning("UID %s: the message is larger than 15 MB; skipped", uid)
        mail.unsupported |= result.oversized

    async def _async_ingest(self, message: MailMessage, save_pdfs: bool) -> None:
        """Lee los PDF de un correo y guarda las facturas nuevas."""
        mail = self.store.mail
        failed = unsupported = False
        # R20: el importe del correo solo identifica la factura si hay un PDF.
        email_total = message.email_total if len(message.pdfs) == 1 else None
        for pdf in message.pdfs:
            try:
                invoice = await self.hass.async_add_executor_job(parse_invoice_pdf, pdf)
                stored = build_stored(invoice, email_total)
            except (InvoiceParseError, InvoiceReadError):
                _LOGGER.warning("UID %s: an invoice PDF could not be read", message.uid)
                failed = True
                continue
            except UnsupportedInvoiceError:
                _LOGGER.debug("UID %s: unsupported invoice type", message.uid)
                unsupported = True
                continue
            except Exception as err:  # noqa: BLE001
                # R17/R22: como ``InvoiceReadError``. Ni mensaje ni traza:
                # podrían llevar texto de la factura.
                _LOGGER.warning(
                    "UID %s: unexpected error reading an invoice PDF (%s)",
                    message.uid,
                    type(err).__name__,
                )
                failed = True
                continue

            if not self.store.add(stored):
                continue
            if stored.unreadable:
                _LOGGER.warning(
                    "UID %s: the invoice has inconsistencies: %s",
                    message.uid,
                    ", ".join(stored.problems),
                )
            if save_pdfs:
                await self._async_save_pdf(message.uid, invoice.number, pdf)

        mail.failed.pop(message.uid, None)
        mail.unsupported.discard(message.uid)
        if failed:
            mail.failed[message.uid] = LIB_VERSION
        elif unsupported:
            mail.unsupported.add(message.uid)

    async def _async_save_pdf(self, uid: int, number: str, pdf: bytes) -> None:
        """Guarda el PDF de una factura nueva (opción ``save_pdfs``).

        R18: el número sale del texto del PDF y no es de fiar.
        """
        if not _SAFE_NUMBER.fullmatch(number):
            _LOGGER.warning(
                "UID %s: the invoice number is not a safe file name; PDF not saved",
                uid,
            )
            return
        folder = Path(self.hass.config.path(DOMAIN))
        try:
            await self.hass.async_add_executor_job(
                _save_pdf, folder, f"{number}.pdf", pdf
            )
        except _UnsafePathError:
            _LOGGER.warning(
                "UID %s: the PDF path leaves the PDF folder; PDF not saved", uid
            )
        except OSError as err:
            # El mensaje de ``OSError`` lleva la ruta (con el número de factura).
            _LOGGER.warning(
                "UID %s: cannot save the invoice PDF (%s)", uid, type(err).__name__
            )

    async def _async_build_data(
        self, *, mail_error: bool, last_mail_check: datetime | None
    ) -> CoordinatorData:
        """Agrupa por contrato las facturas guardadas y las casa con e-data."""
        by_contract: defaultdict[str, list[StoredInvoice]] = defaultdict(list)
        for stored in self.store.invoices.values():
            by_contract[stored.invoice.contract].append(stored)

        options = self.config_entry.options
        thresholds = Thresholds(
            kwh=Decimal(str(options[CONF_KWH_THRESHOLD])),
            eur_pct=Decimal(str(options[CONF_EUR_THRESHOLD_PCT])),
        )
        tz = dt_util.get_default_time_zone()
        supplies = {
            contract: invoices[0].invoice.supply
            for contract, invoices in by_contract.items()
        }
        per_supply = Counter(supplies.values())

        contracts: dict[str, ContractData] = {}
        for contract in sorted(by_contract):
            invoices = by_contract[contract]
            supply = supplies[contract]
            provider = await self.async_totals_provider(invoices[0].invoice.cups)
            rows = await match_contract(
                invoices, provider or _no_totals, thresholds, tz
            )
            name = _DEVICE_NAMES[supply]
            if per_supply[supply] > 1:
                name = f"{name} {contract[-4:]}"
            contracts[contract] = ContractData(
                contract=contract, supply=supply, rows=rows, device_name=name
            )

        mail = self.store.mail
        return CoordinatorData(
            contracts=contracts,
            unreadable_emails=len(mail.failed),
            unsupported_emails=len(mail.unsupported),
            last_mail_check=last_mail_check,
            mail_error=mail_error,
        )

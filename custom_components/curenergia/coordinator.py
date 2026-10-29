"""Coordinador: lee el buzón, guarda las facturas nuevas y las casa con e-data."""

from __future__ import annotations

import logging
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
from .edata import find_edata_id, make_provider
from .mail import MailAuthError, MailClient, MailConnectionError, MailMessage
from .matching import InvoiceRow, Thresholds, Totals, TotalsProvider, match_contract
from .storage import InvoiceStore, StoredInvoice, build_stored

_LOGGER = logging.getLogger(__name__)

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


def _save_pdf(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


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

    async def async_totals_provider(self, cups: str) -> TotalsProvider | None:
        """Proveedor de sumas de e-data para ``cups``; ``None`` si no hay e-data."""
        override = self.config_entry.options.get(CONF_EDATA_ENTRY, EDATA_AUTO)
        edata_id = find_edata_id(
            self.hass, cups, None if override == EDATA_AUTO else override
        )
        if edata_id is None:
            return None
        return make_provider(self.hass, edata_id)

    async def _async_update_data(self) -> CoordinatorData:
        options = self.config_entry.options
        folder = options[CONF_FOLDER]
        if self.store.mail.folder != folder:
            # R4: el estado del buzón es de otra carpeta.
            self.store.reset_mail()
            self.store.mail.folder = folder

        mail = self.store.mail
        skip = (
            mail.seen
            | mail.unsupported
            | {uid for uid, version in mail.failed.items() if version == LIB_VERSION}
        )
        data = self.config_entry.data
        client = MailClient(
            data[CONF_HOST], data[CONF_PORT], data[CONF_USERNAME], data[CONF_PASSWORD]
        )
        try:
            result = await self.hass.async_add_executor_job(
                client.fetch, folder, frozenset(skip), mail.uidvalidity
            )
        except MailAuthError as err:
            raise ConfigEntryAuthFailed("The IMAP server rejected the login") from err
        except MailConnectionError as err:
            if self.data is None:
                raise UpdateFailed(str(err)) from err
            # D5: se siguen sirviendo las facturas guardadas.
            _LOGGER.warning("Cannot read the mailbox, keeping stored invoices: %s", err)
            return await self._async_build_data(
                mail_error=True, last_mail_check=self.data.last_mail_check
            )

        if result.uidvalidity != self.store.mail.uidvalidity:
            # Los UID guardados ya no valen: se olvidan (las facturas se quedan).
            self.store.reset_mail()
            self.store.mail.folder = folder
            self.store.mail.uidvalidity = result.uidvalidity

        save_pdfs = options.get(CONF_SAVE_PDFS, DEFAULT_SAVE_PDFS)
        for message in result.messages:
            await self._async_ingest(message, save_pdfs)

        mail = self.store.mail
        # Se olvidan los UID que ya no están en la carpeta.
        mail.failed = {
            uid: version
            for uid, version in mail.failed.items()
            if uid in result.all_uids
        }
        mail.unsupported &= result.all_uids
        # R16: el resto de UID de la carpeta quedan vistos.
        mail.seen = set(result.all_uids - mail.failed.keys() - mail.unsupported)
        await self.store.async_save()

        return await self._async_build_data(
            mail_error=False, last_mail_check=dt_util.utcnow()
        )

    async def _async_ingest(self, message: MailMessage, save_pdfs: bool) -> None:
        """Lee los PDF de un correo y guarda las facturas nuevas."""
        mail = self.store.mail
        failed = unsupported = False
        for pdf in message.pdfs:
            try:
                invoice = await self.hass.async_add_executor_job(parse_invoice_pdf, pdf)
            except (InvoiceParseError, InvoiceReadError):
                _LOGGER.warning("UID %s: an invoice PDF could not be read", message.uid)
                failed = True
                continue
            except UnsupportedInvoiceError:
                _LOGGER.debug("UID %s: unsupported invoice type", message.uid)
                unsupported = True
                continue

            stored = build_stored(invoice, message.email_total)
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
        """Guarda el PDF de una factura nueva (opción ``save_pdfs``)."""
        path = Path(self.hass.config.path(DOMAIN, f"{number}.pdf"))
        try:
            await self.hass.async_add_executor_job(_save_pdf, path, pdf)
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

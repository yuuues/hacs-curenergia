"""Almacenamiento persistente de facturas y estado del buzón."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from pycurenergia import (
    Concept,
    ConceptKey,
    Invoice,
    SupplyType,
    check_consistency,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1

# Diferencia máxima (€) entre el importe del correo y el total de la factura.
EMAIL_TOTAL_TOLERANCE = Decimal("0.01")
PROBLEM_EMAIL_TOTAL_MISMATCH = "email_total_mismatch"


def _dec(value: str | None) -> Decimal | None:
    return None if value is None else Decimal(value)


def _str(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def invoice_to_dict(invoice: Invoice) -> dict[str, Any]:
    """Convierte una factura en un diccionario serializable a JSON."""
    return {
        "supply": invoice.supply.value,
        "number": invoice.number,
        "contract": invoice.contract,
        "cups": invoice.cups,
        "issue_date": invoice.issue_date.isoformat(),
        "period_start": invoice.period_start.isoformat(),
        "period_end": invoice.period_end.isoformat(),
        "estimated": invoice.estimated,
        "total": str(invoice.total),
        "concepts": [
            {"key": c.key.value, "label": c.label, "amount": str(c.amount)}
            for c in invoice.concepts
        ],
        "vat_rate": str(invoice.vat_rate),
        "vat_base": str(invoice.vat_base),
        "vat_amount": str(invoice.vat_amount),
        "kwh": str(invoice.kwh),
        "tariff": invoice.tariff,
        "access_tariff": invoice.access_tariff,
        "kwh_p1": _str(invoice.kwh_p1),
        "kwh_p2": _str(invoice.kwh_p2),
        "kwh_p3": _str(invoice.kwh_p3),
        "m3": _str(invoice.m3),
        "contracted_power_kw": [str(p) for p in invoice.contracted_power_kw],
        "late_interest": str(invoice.late_interest),
        "energy_price_kwh": _str(invoice.energy_price_kwh),
    }


def invoice_from_dict(data: dict[str, Any]) -> Invoice:
    """Reconstruye una factura a partir de ``invoice_to_dict``."""
    return Invoice(
        supply=SupplyType(data["supply"]),
        number=data["number"],
        contract=data["contract"],
        cups=data["cups"],
        issue_date=date.fromisoformat(data["issue_date"]),
        period_start=date.fromisoformat(data["period_start"]),
        period_end=date.fromisoformat(data["period_end"]),
        estimated=data["estimated"],
        total=Decimal(data["total"]),
        concepts=tuple(
            Concept(
                key=ConceptKey(c["key"]),
                label=c["label"],
                amount=Decimal(c["amount"]),
            )
            for c in data["concepts"]
        ),
        vat_rate=Decimal(data["vat_rate"]),
        vat_base=Decimal(data["vat_base"]),
        vat_amount=Decimal(data["vat_amount"]),
        kwh=Decimal(data["kwh"]),
        tariff=data["tariff"],
        access_tariff=data["access_tariff"],
        kwh_p1=_dec(data.get("kwh_p1")),
        kwh_p2=_dec(data.get("kwh_p2")),
        kwh_p3=_dec(data.get("kwh_p3")),
        m3=_dec(data.get("m3")),
        contracted_power_kw=tuple(Decimal(p) for p in data["contracted_power_kw"]),
        late_interest=Decimal(data["late_interest"]),
        energy_price_kwh=_dec(data.get("energy_price_kwh")),
    )


@dataclass
class StoredInvoice:
    """Factura guardada junto con sus incoherencias detectadas."""

    invoice: Invoice
    problems: list[str]
    email_total: Decimal | None

    @property
    def unreadable(self) -> bool:
        """Si la factura tiene incoherencias, no se puede fiar de sus datos."""
        return bool(self.problems)

    def to_dict(self) -> dict[str, Any]:
        """Serializa a un diccionario JSON."""
        return {
            "invoice": invoice_to_dict(self.invoice),
            "problems": list(self.problems),
            "email_total": _str(self.email_total),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StoredInvoice:
        """Reconstruye desde ``to_dict``."""
        return cls(
            invoice=invoice_from_dict(data["invoice"]),
            problems=list(data["problems"]),
            email_total=_dec(data.get("email_total")),
        )


@dataclass
class MailState:
    """Estado del buzón: qué UID ya se han procesado."""

    uidvalidity: int | None = None
    # UID ya procesados (con factura guardada o sin PDF).
    seen: set[int] = field(default_factory=set)
    # UID cuyo PDF no se pudo leer → versión de pycurenergia del intento.
    failed: dict[int, str] = field(default_factory=dict)
    # UID de facturas no soportadas (rectificativas, abonos); no se reintentan.
    unsupported: set[int] = field(default_factory=set)
    # Carpeta a la que corresponde el estado.
    folder: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serializa a un diccionario JSON (las claves de ``failed`` pasan a str)."""
        return {
            "uidvalidity": self.uidvalidity,
            "folder": self.folder,
            "seen": sorted(self.seen),
            "failed": {str(uid): ver for uid, ver in sorted(self.failed.items())},
            "unsupported": sorted(self.unsupported),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MailState:
        """Reconstruye desde ``to_dict``."""
        return cls(
            uidvalidity=data.get("uidvalidity"),
            seen=set(data.get("seen", [])),
            failed={int(uid): ver for uid, ver in data.get("failed", {}).items()},
            unsupported=set(data.get("unsupported", [])),
            folder=data.get("folder"),
        )


def build_stored(invoice: Invoice, email_total: Decimal | None) -> StoredInvoice:
    """Comprueba la coherencia de la factura y el importe del correo."""
    problems = [str(p) for p in check_consistency(invoice)]
    if (
        email_total is not None
        and abs(email_total - invoice.total) > EMAIL_TOTAL_TOLERANCE
    ):
        problems.append(PROBLEM_EMAIL_TOTAL_MISMATCH)
    return StoredInvoice(invoice=invoice, problems=problems, email_total=email_total)


class InvoiceStore:
    """Facturas y estado del buzón de una entrada, guardados en un ``Store``."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Prepara el almacén de la entrada ``entry_id``."""
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"curenergia.{entry_id}"
        )
        self.invoices: dict[str, StoredInvoice] = {}
        self.mail = MailState()

    async def async_load(self) -> None:
        """Carga los datos guardados (si los hay)."""
        data = await self._store.async_load()
        self.invoices = {}
        self.mail = MailState()
        if not data:
            return
        try:
            invoices = {
                number: StoredInvoice.from_dict(item)
                for number, item in data.get("invoices", {}).items()
            }
            mail = MailState.from_dict(data.get("mail", {}))
        except (AttributeError, KeyError, TypeError, ValueError, ArithmeticError):
            # R15: todo se puede volver a leer del buzón. Sin datos en el log.
            _LOGGER.warning(
                "The stored CurEnergía data is invalid; starting with an empty store"
            )
            return
        self.invoices = invoices
        self.mail = mail

    def add(self, stored: StoredInvoice) -> bool:
        """Guarda la factura; ``False`` si ya existía ese número (no se reemplaza)."""
        number = stored.invoice.number
        if number in self.invoices:
            return False
        self.invoices[number] = stored
        return True

    def reset_mail(self) -> None:
        """Olvida el estado del buzón (las facturas guardadas se conservan)."""
        self.mail = MailState()

    async def async_save(self) -> None:
        """Escribe los datos en disco."""
        await self._store.async_save(
            {
                "invoices": {n: s.to_dict() for n, s in self.invoices.items()},
                "mail": self.mail.to_dict(),
            }
        )

    async def async_remove(self) -> None:
        """Borra los datos guardados."""
        await self._store.async_remove()

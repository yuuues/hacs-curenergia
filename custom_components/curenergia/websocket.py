"""API websocket: facturas y resumen para la tarjeta y el panel.

Cualquier usuario autenticado puede leerla (D7), como los sensores.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pycurenergia import SupplyType

from .const import DOMAIN
from .coordinator import CurenergiaConfigEntry
from .matching import Comparison, InvoiceRow, Periods, Status
from .util import money, price, price_per_kwh

# Plazo del resumen: facturas emitidas en los últimos
# 365 días, sin contar el día que hace exactamente 365.
SUMMARY_DAYS = 365

# Estados cuya comparación entra en la diferencia de kWh del resumen.
_COMPARED = (Status.OK, Status.MISMATCH)

INVOICES_COMMAND = f"{DOMAIN}/invoices"
SUMMARY_COMMAND = f"{DOMAIN}/summary"


@websocket_api.websocket_command(
    {
        vol.Required("type"): INVOICES_COMMAND,
        vol.Optional("entry_id"): str,
        vol.Optional("supply"): vol.In([supply.value for supply in SupplyType]),
    }
)
@websocket_api.async_response
async def ws_invoices(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Facturas de cada contrato, de la más reciente a la más antigua."""
    entries = _select_entries(hass, msg.get("entry_id"))
    if entries is None:
        _send_not_found(connection, msg)
        return
    supply = msg.get("supply")
    contracts = [
        {
            "entry_id": entry.entry_id,
            "contract": data.contract,
            "supply": data.supply.value,
            "name": data.device_name,
            "invoices": [
                _row(row) for row in sorted(data.rows, key=_sort_key, reverse=True)
            ],
        }
        for entry in entries
        for data in entry.runtime_data.data.contracts.values()
        if supply is None or data.supply.value == supply
    ]
    connection.send_result(msg["id"], {"contracts": contracts})


@websocket_api.websocket_command(
    {vol.Required("type"): SUMMARY_COMMAND, vol.Optional("entry_id"): str}
)
@websocket_api.async_response
async def ws_summary(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Resumen de los últimos 12 meses y del estado del buzón."""
    entries = _select_entries(hass, msg.get("entry_id"))
    if entries is None:
        _send_not_found(connection, msg)
        return

    cutoff = dt_util.now().date() - timedelta(days=SUMMARY_DAYS)
    billed = Decimal(0)
    estimated_count = 0
    invoice_kwh = Decimal(0)
    edata_kwh = Decimal(0)
    unreadable = unsupported = 0
    checks = []
    mail_error = False
    for entry in entries:
        data = entry.runtime_data.data
        unreadable += data.unreadable_emails
        unsupported += data.unsupported_emails
        mail_error = mail_error or data.mail_error
        if data.last_mail_check is not None:
            checks.append(data.last_mail_check)
        for contract in data.contracts.values():
            for row in contract.rows:
                invoice = row.stored.invoice
                if invoice.issue_date <= cutoff:
                    continue
                billed += invoice.total
                if invoice.estimated:
                    estimated_count += 1
                    continue
                if row.status in _COMPARED and row.comparison is not None:
                    invoice_kwh += row.comparison.invoice_kwh
                    edata_kwh += row.comparison.edata.kwh

    kwh_delta_pct = None
    if edata_kwh != 0:
        kwh_delta_pct = money((invoice_kwh - edata_kwh) / edata_kwh * 100)
    connection.send_result(
        msg["id"],
        {
            "billed_12m": money(billed),
            "kwh_delta_pct": kwh_delta_pct,
            "estimated_count": estimated_count,
            "unreadable_emails": unreadable,
            "unsupported_emails": unsupported,
            "last_mail_check": max(checks).isoformat() if checks else None,
            "mail_error": mail_error,
        },
    )


def async_register_websocket(hass: HomeAssistant) -> None:
    """Registra las órdenes websocket de la integración."""
    websocket_api.async_register_command(hass, ws_invoices)
    websocket_api.async_register_command(hass, ws_summary)


def _select_entries(
    hass: HomeAssistant, entry_id: str | None
) -> list[CurenergiaConfigEntry] | None:
    """Entradas cargadas pedidas; ``None`` si ``entry_id`` no es una de ellas."""
    loaded = hass.config_entries.async_loaded_entries(DOMAIN)
    if entry_id is None:
        return loaded
    selected = [entry for entry in loaded if entry.entry_id == entry_id]
    return selected or None


def _send_not_found(
    connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Entry not found")


def _sort_key(row: InvoiceRow) -> tuple[date, date, str]:
    invoice = row.stored.invoice
    return (invoice.period_start, invoice.period_end, invoice.number)


def _periods(values: Periods) -> dict[str, float | None]:
    p1, p2, p3 = (money(value) for value in values)
    return {"p1": p1, "p2": p2, "p3": p3}


def _row(row: InvoiceRow) -> dict[str, Any]:
    stored = row.stored
    invoice = stored.invoice
    kwh_periods = (invoice.kwh_p1, invoice.kwh_p2, invoice.kwh_p3)
    return {
        "number": invoice.number,
        "supply": invoice.supply.value,
        "issue_date": invoice.issue_date.isoformat(),
        "period_start": invoice.period_start.isoformat(),
        "period_end": invoice.period_end.isoformat(),
        "estimated": invoice.estimated,
        "status": row.status.value,
        "problems": list(stored.problems),
        "total": money(invoice.total),
        "kwh": money(invoice.kwh),
        "price_kwh": price_per_kwh(invoice.total, invoice.kwh),
        "m3": money(invoice.m3),
        "energy_price_kwh": price(invoice.energy_price_kwh),
        "periods": (
            None
            if all(value is None for value in kwh_periods)
            else _periods(kwh_periods)
        ),
        "concepts": [
            {"key": c.key.value, "label": c.label, "amount": money(c.amount)}
            for c in invoice.concepts
        ],
        "vat": {
            "rate": money(invoice.vat_rate),
            "base": money(invoice.vat_base),
            "amount": money(invoice.vat_amount),
        },
        "in_group_of": row.in_group_of,
        "comparison": None if row.comparison is None else _comparison(row.comparison),
    }


def _comparison(comparison: Comparison) -> dict[str, Any]:
    edata = comparison.edata
    return {
        "group": list(comparison.group),
        "window_start": comparison.window_start.isoformat(),
        "window_end": comparison.window_end.isoformat(),
        "invoice_kwh": money(comparison.invoice_kwh),
        "invoice_periods": _periods(comparison.invoice_periods),
        "invoice_eur": money(comparison.invoice_eur),
        "edata_kwh": money(edata.kwh),
        "edata_periods": _periods((edata.p1, edata.p2, edata.p3)),
        "edata_eur": money(edata.eur),
        "delta_kwh": money(comparison.delta_kwh),
        "delta_periods": _periods(comparison.delta_periods),
        "delta_eur": money(comparison.delta_eur),
        "delta_pct": money(comparison.delta_pct),
    }

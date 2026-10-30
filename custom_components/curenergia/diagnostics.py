"""Diagnósticos de una entrada (con los datos personales ocultos)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pycurenergia import SupplyType
from pycurenergia import __version__ as LIB_VERSION

from .coordinator import CurenergiaConfigEntry, CurenergiaCoordinator
from .matching import InvoiceRow, invoice_window
from .util import money

TO_REDACT = {
    "username",
    "password",
    # R27: el servidor y la carpeta pueden identificar al usuario.
    "host",
    "folder",
    "cups",
    "contract",
    "number",
}

_DAY = timedelta(days=1)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: CurenergiaConfigEntry
) -> dict[str, Any]:
    """Opciones, estado del buzón y facturas (por índice, sin identificarlas)."""
    coordinator = entry.runtime_data
    mail = coordinator.store.mail
    invoices: list[dict[str, Any]] = []
    for contract in coordinator.data.contracts.values():
        for row in contract.rows:
            invoice = row.stored.invoice
            item: dict[str, Any] = {
                "supply": invoice.supply.value,
                "period_start": invoice.period_start.isoformat(),
                "period_end": invoice.period_end.isoformat(),
                "estimated": invoice.estimated,
                "status": row.status.value,
                "problems": list(row.stored.problems),
            }
            if invoice.supply is SupplyType.ELECTRICITY and not invoice.estimated:
                item["boundary_deltas"] = await _boundary_deltas(
                    coordinator, contract.rows, row
                )
            invoices.append(item)

    return async_redact_data(
        {
            "options": dict(entry.options),
            "data": dict(entry.data),
            "pycurenergia_version": LIB_VERSION,
            "mail": {
                "uidvalidity": mail.uidvalidity,
                "seen": len(mail.seen),
                "failed": len(mail.failed),
                "unsupported": len(mail.unsupported),
            },
            "invoices": invoices,
        },
        TO_REDACT,
    )


async def _boundary_deltas(
    coordinator: CurenergiaCoordinator, rows: list[InvoiceRow], row: InvoiceRow
) -> dict[str, float | None]:
    """Δ kWh (factura − e-data) con la ventana de la factura y con las fronteras
    desplazadas un día (§9.3).

    ``base`` es la ventana de la comparación (``[D1 + 1 día, D2 + 1 día)``); las
    otras mueven un día su inicio o su final. Si la factura cierra un grupo de
    estimadas, la ventana y los kWh son los del grupo, como en la comparación.
    ``None`` si no hay e-data, no cubre la ventana o la ventana queda vacía.
    """
    invoice = row.stored.invoice
    group = [
        other.stored.invoice for other in rows if other.in_group_of == invoice.number
    ]
    group.append(invoice)
    start = min(item.period_start for item in group)
    end = invoice.period_end
    kwh = sum(item.kwh for item in group)

    windows = {
        "base": (start, end),
        "start-1d": (start - _DAY, end),
        "start+1d": (start + _DAY, end),
        "end-1d": (start, end - _DAY),
        "end+1d": (start, end + _DAY),
    }
    provider = await coordinator.async_totals_provider(invoice.cups)
    tz = dt_util.get_default_time_zone()
    deltas: dict[str, float | None] = {}
    for key, (window_start, window_end) in windows.items():
        totals = None
        # ``invoice_window`` va de ``inicio + 1`` a ``fin + 1``: vacía si no
        # hay al menos un día entre las dos fechas.
        if provider is not None and window_start < window_end:
            totals = await provider(*invoice_window(window_start, window_end, tz))
        deltas[key] = None if totals is None else money(kwh - totals.kwh)
    return deltas

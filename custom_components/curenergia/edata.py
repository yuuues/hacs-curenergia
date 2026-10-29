"""Lectura de las estadísticas a largo plazo de e-data desde el recorder."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    StatisticsRow,
    statistics_during_period,
)
from homeassistant.core import HomeAssistant

from .matching import Totals, TotalsProvider

EDATA_DOMAIN = "edata"

_HOUR = timedelta(hours=1)


def edata_entries(hass: HomeAssistant) -> list[tuple[str, str]]:
    """Pares ``(entry_id, title)`` de las entradas de e-data."""
    return [
        (entry.entry_id, entry.title)
        for entry in hass.config_entries.async_entries(EDATA_DOMAIN)
    ]


def find_edata_id(
    hass: HomeAssistant, cups: str, override_entry_id: str | None
) -> str | None:
    """Id de estadísticas de la entrada de e-data (``scups`` en minúsculas)."""
    if override_entry_id is not None:
        entry = hass.config_entries.async_get_entry(override_entry_id)
        if entry is None or entry.domain != EDATA_DOMAIN:
            return None
    else:
        wanted = cups.upper()
        entry = next(
            (
                candidate
                for candidate in hass.config_entries.async_entries(EDATA_DOMAIN)
                if str(candidate.data.get("cups", "")).upper() == wanted
            ),
            None,
        )
        if entry is None:
            return None
    scups = entry.data.get("scups")
    return str(scups).lower() if scups else None


def _decimal(value: float) -> Decimal:
    return Decimal(str(round(value, 6)))


def _covered(rows: list[StatisticsRow], start: datetime, end: datetime) -> bool:
    """Cobertura de Datadis (D3), con horas reales transcurridas."""
    if not rows:
        return False
    hours = int((end - start) / _HOUR)
    first = datetime.fromtimestamp(rows[0]["start"], tz=UTC)
    last = datetime.fromtimestamp(rows[-1]["start"], tz=UTC)
    return (
        len(rows) >= hours - 2 and first < start + 2 * _HOUR and last >= end - 3 * _HOUR
    )


def _sum_states(rows: list[StatisticsRow] | None) -> Decimal | None:
    """Suma de los valores horarios, o ``None`` si no hay filas."""
    values = [row["state"] for row in rows or () if row.get("state") is not None]
    return _decimal(math.fsum(values)) if values else None


def _totals(
    hass: HomeAssistant, edata_id: str, start: datetime, end: datetime
) -> Totals | None:
    # Se suman los valores horarios (``state``) en vez de usar ``change`` de
    # ``statistic_during_period``: éste resta la suma de la hora anterior a la
    # ventana y, en las series dispersas (P1..P3), si esa hora no tiene fila
    # parte de la primera fila de la ventana y pierde su valor. Además recorta
    # el fin de la ventana a "ahora".
    ids = {
        suffix: f"{EDATA_DOMAIN}:{edata_id}_{suffix}"
        for suffix in (
            "consumption",
            "p1_consumption",
            "p2_consumption",
            "p3_consumption",
            "power_cost",
            "energy_cost",
        )
    }
    stats = statistics_during_period(
        hass, start, end, set(ids.values()), "hour", None, {"state"}
    )
    consumption = stats.get(ids["consumption"])
    if not consumption or not _covered(consumption, start, end):
        return None
    kwh = _sum_states(consumption)
    if kwh is None:
        return None
    power = _sum_states(stats.get(ids["power_cost"]))
    energy = _sum_states(stats.get(ids["energy_cost"]))
    return Totals(
        kwh=kwh,
        p1=_sum_states(stats.get(ids["p1_consumption"])),
        p2=_sum_states(stats.get(ids["p2_consumption"])),
        p3=_sum_states(stats.get(ids["p3_consumption"])),
        eur=None if power is None or energy is None else power + energy,
    )


def make_provider(hass: HomeAssistant, edata_id: str) -> TotalsProvider:
    """Crea el proveedor de sumas de e-data para una ventana ``[start, end)``."""

    async def provider(start: datetime, end: datetime) -> Totals | None:
        return await get_instance(hass).async_add_executor_job(
            _totals, hass, edata_id, start, end
        )

    return provider

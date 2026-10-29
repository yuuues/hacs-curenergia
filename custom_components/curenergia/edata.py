"""Lectura de las estadísticas a largo plazo de e-data desde el recorder.

Las sumas se calculan sumando el valor horario (``state``), que es el valor de
esa hora que escribe e-data, y no con ``change`` de ``statistic_during_period``:
éste resta la suma de la hora anterior a la ventana, de modo que en las series
dispersas (P1..P3, con filas solo en sus horas) pierde el valor de la primera
fila, y además recorta el fin de la ventana a "ahora".
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    StatisticsRow,
    statistics_during_period,
)
from homeassistant.config_entries import ConfigEntry
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


def cups_key(cups: str) -> str:
    """CUPS para comparar (R28): los 20 primeros caracteres, en mayúsculas.

    El CUPS puede llevar 2 caracteres más (el punto frontera) según quién lo
    escriba; los 20 primeros identifican el contador.
    """
    return cups.upper()[:20]


def _edata_entry(hass: HomeAssistant, entry_id: str) -> ConfigEntry | None:
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != EDATA_DOMAIN:
        return None
    return entry


def edata_entry_cups_key(hass: HomeAssistant, entry_id: str) -> str | None:
    """``cups_key`` del CUPS de la entrada de e-data ``entry_id`` (si existe)."""
    entry = _edata_entry(hass, entry_id)
    if entry is None:
        return None
    return cups_key(str(entry.data.get("cups", "")))


def find_edata_id(
    hass: HomeAssistant, cups: str, override_entry_id: str | None
) -> str | None:
    """Id de estadísticas de la entrada de e-data (``scups`` en minúsculas)."""
    if override_entry_id is not None:
        entry = _edata_entry(hass, override_entry_id)
        if entry is None:
            return None
    else:
        wanted = cups_key(cups)
        entry = next(
            (
                candidate
                for candidate in hass.config_entries.async_entries(EDATA_DOMAIN)
                if cups_key(str(candidate.data.get("cups", ""))) == wanted
            ),
            None,
        )
        if entry is None:
            return None
    scups = entry.data.get("scups")
    return str(scups).lower() if scups else None


def _decimal(value: float) -> Decimal:
    return Decimal(str(round(value, 6)))


def _real_hours(start: datetime, end: datetime) -> int:
    """Horas reales transcurridas en ``[start, end)``.

    En UTC: con la misma ``tzinfo`` en ambos extremos, restar sobre la hora
    local ignora el cambio de hora.
    """
    return int((end.astimezone(UTC) - start.astimezone(UTC)) / _HOUR)


def _values(rows: list[StatisticsRow] | None) -> list[StatisticsRow]:
    """Filas con valor horario."""
    return [row for row in rows or () if row.get("state") is not None]


def _covered(rows: list[StatisticsRow] | None, start: datetime, end: datetime) -> bool:
    """Cobertura de Datadis (D3), con horas reales transcurridas.

    Toda la aritmética es en UTC: con la misma ``tzinfo`` en ambos extremos,
    restar o sumar horas sobre la hora local ignora el cambio de hora.
    """
    values = _values(rows)
    if not values:
        return False
    start_utc = start.astimezone(UTC)
    end_utc = end.astimezone(UTC)
    hours = _real_hours(start, end)
    first = datetime.fromtimestamp(values[0]["start"], tz=UTC)
    last = datetime.fromtimestamp(values[-1]["start"], tz=UTC)
    return (
        len(values) >= hours - 2
        and first < start_utc + 2 * _HOUR
        and last >= end_utc - 3 * _HOUR
    )


def _sum_states(rows: list[StatisticsRow] | None) -> Decimal | None:
    """Suma de los valores horarios, o ``None`` si no hay filas."""
    values = [row["state"] for row in _values(rows)]
    return _decimal(math.fsum(values)) if values else None


def _covered_sum(
    rows: list[StatisticsRow] | None, start: datetime, end: datetime
) -> Decimal | None:
    """Suma de la serie si cubre la ventana (D3); si no, ``None``."""
    return _sum_states(rows) if _covered(rows, start, end) else None


def _totals(
    hass: HomeAssistant, edata_id: str, start: datetime, end: datetime
) -> Totals | None:
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
    kwh = _covered_sum(consumption, start, end)
    if kwh is None:
        return None
    # R24: los costes solo valen si ambas series cumplen la misma cobertura.
    power = _covered_sum(stats.get(ids["power_cost"]), start, end)
    energy = _covered_sum(stats.get(ids["energy_cost"]), start, end)
    eur = None if power is None or energy is None else power + energy
    return Totals(
        kwh=kwh,
        p1=_sum_states(stats.get(ids["p1_consumption"])),
        p2=_sum_states(stats.get(ids["p2_consumption"])),
        p3=_sum_states(stats.get(ids["p3_consumption"])),
        eur=eur,
        complete=len(_values(consumption)) == _real_hours(start, end),
    )


def make_provider(hass: HomeAssistant, edata_id: str) -> TotalsProvider:
    """Crea el proveedor de sumas de e-data para una ventana ``[start, end)``."""

    async def provider(start: datetime, end: datetime) -> Totals | None:
        return await get_instance(hass).async_add_executor_job(
            _totals, hass, edata_id, start, end
        )

    return provider

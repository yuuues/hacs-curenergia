"""Pruebas de la lectura de estadísticas de e-data desde el recorder."""

from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.curenergia.edata import (
    EDATA_DOMAIN,
    edata_entries,
    find_edata_id,
    make_provider,
)

MADRID = ZoneInfo("Europe/Madrid")


# El recorder debe crearse antes que ``hass``.
pytestmark = pytest.mark.usefixtures("recorder_mock", "enable_custom_integrations")


def _entry(hass: HomeAssistant, cups: str, scups: str, title: str = "e-data"):
    entry = MockConfigEntry(
        domain=EDATA_DOMAIN, data={"cups": cups, "scups": scups}, title=title
    )
    entry.add_to_hass(hass)
    return entry


def _hours(start: datetime, end: datetime) -> list[datetime]:
    """Inicios de hora (aware, hora real) en ``[start, end)``."""
    moments = []
    moment = start.astimezone(ZoneInfo("UTC"))
    stop = end.astimezone(ZoneInfo("UTC"))
    while moment < stop:
        moments.append(moment)
        moment += timedelta(hours=1)
    return moments


async def _write(
    hass: HomeAssistant,
    suffix: str,
    values: dict[datetime, float],
    *,
    unit: str = "kWh",
) -> None:
    """Escribe una estadística externa ``edata:abcd_<suffix>`` con suma acumulada."""
    total = 0.0
    rows = []
    for start in sorted(values):
        total += values[start]
        rows.append(StatisticData(start=start, state=values[start], sum=total))
    async_add_external_statistics(
        hass,
        StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=suffix,
            source=EDATA_DOMAIN,
            statistic_id=f"{EDATA_DOMAIN}:abcd_{suffix}",
            unit_class="energy" if unit == "kWh" else None,
            unit_of_measurement=unit,
        ),
        rows,
    )


async def _write_month(
    hass: HomeAssistant,
    first: datetime,
    last: datetime,
    *,
    costs: bool = True,
) -> None:
    """1 kWh/h (P1 de 10 a 14 h, P2 el resto, sin P3) y 0,1 €/h por coste."""
    moments = _hours(first, last)
    local = [m.astimezone(MADRID) for m in moments]
    await _write(hass, "consumption", dict.fromkeys(moments, 1.0))
    await _write(
        hass,
        "p1_consumption",
        {m: 1.0 for m, loc in zip(moments, local, strict=True) if 10 <= loc.hour < 14},
    )
    await _write(
        hass,
        "p2_consumption",
        {
            m: 1.0
            for m, loc in zip(moments, local, strict=True)
            if not 10 <= loc.hour < 14
        },
    )
    if costs:
        await _write(hass, "power_cost", dict.fromkeys(moments, 0.1), unit="EUR")
        await _write(hass, "energy_cost", dict.fromkeys(moments, 0.1), unit="EUR")
    await async_wait_recording_done(hass)


async def test_find_edata_id_by_cups(hass):
    _entry(hass, "ES0000000000000000AA", "00AA")
    _entry(hass, "ES1111111111111111BB", "11BB")
    assert find_edata_id(hass, "es0000000000000000aa", None) == "00aa"
    assert find_edata_id(hass, "ES1111111111111111BB", None) == "11bb"
    assert find_edata_id(hass, "ES9999999999999999ZZ", None) is None


async def test_find_edata_id_override_and_missing(hass):
    first = _entry(hass, "ES0000000000000000AA", "00AA")
    second = _entry(hass, "ES1111111111111111BB", "11BB")
    other = MockConfigEntry(domain="otro", data={"cups": "ES0000000000000000AA"})
    other.add_to_hass(hass)

    assert find_edata_id(hass, "ES0000000000000000AA", second.entry_id) == "11bb"
    assert find_edata_id(hass, "ES0000000000000000AA", first.entry_id) == "00aa"
    assert find_edata_id(hass, "ES0000000000000000AA", "no-existe") is None
    # Una entrada de otra integración no vale como e-data.
    assert find_edata_id(hass, "ES0000000000000000AA", other.entry_id) is None


async def test_edata_entries(hass):
    first = _entry(hass, "ES0000000000000000AA", "00AA", title="Casa")
    second = _entry(hass, "ES1111111111111111BB", "11BB", title="Local")
    MockConfigEntry(domain="otro", title="Otra").add_to_hass(hass)
    assert sorted(edata_entries(hass)) == sorted(
        [(first.entry_id, "Casa"), (second.entry_id, "Local")]
    )


async def test_provider_sums_window(hass, madrid_tz):
    # Con historia anterior: la ventana no empieza en la primera fila.
    await _write_month(
        hass, datetime(2026, 8, 1, tzinfo=MADRID), datetime(2026, 10, 1, tzinfo=MADRID)
    )
    provider = make_provider(hass, "abcd")

    totals = await provider(
        datetime(2026, 9, 1, tzinfo=MADRID), datetime(2026, 10, 1, tzinfo=MADRID)
    )

    assert totals is not None
    assert totals.kwh == Decimal(720)
    assert totals.p1 == Decimal(120)
    assert totals.p2 == Decimal(600)
    assert totals.p3 is None
    assert totals.eur == Decimal(144)


async def test_provider_sums_window_at_start_of_history(hass, madrid_tz):
    await _write_month(
        hass, datetime(2026, 9, 1, tzinfo=MADRID), datetime(2026, 10, 1, tzinfo=MADRID)
    )
    provider = make_provider(hass, "abcd")

    totals = await provider(
        datetime(2026, 9, 1, tzinfo=MADRID), datetime(2026, 10, 1, tzinfo=MADRID)
    )

    assert totals is not None
    assert totals.kwh == Decimal(720)
    assert totals.p1 == Decimal(120)
    assert totals.p2 == Decimal(600)
    assert totals.p3 is None
    assert totals.eur == Decimal(144)


async def test_provider_dst_october_window_covered(hass, madrid_tz):
    start = datetime(2026, 10, 1, tzinfo=MADRID)
    end = datetime(2026, 11, 1, tzinfo=MADRID)
    utc = ZoneInfo("UTC")
    assert end.astimezone(utc) - start.astimezone(utc) == timedelta(hours=745)
    await _write_month(hass, start, end)
    provider = make_provider(hass, "abcd")

    totals = await provider(start, end)

    assert totals is not None
    assert totals.kwh == Decimal(745)


async def test_provider_incomplete_end_is_none(hass, madrid_tz):
    start = datetime(2026, 9, 1, tzinfo=MADRID)
    end = datetime(2026, 10, 1, tzinfo=MADRID)
    await _write_month(hass, start, end - timedelta(hours=10))
    provider = make_provider(hass, "abcd")

    assert await provider(start, end) is None


async def test_provider_incomplete_start_is_none(hass, madrid_tz):
    start = datetime(2026, 9, 1, tzinfo=MADRID)
    end = datetime(2026, 10, 1, tzinfo=MADRID)
    await _write_month(hass, start + timedelta(hours=10), end)
    provider = make_provider(hass, "abcd")

    assert await provider(start, end) is None


async def test_provider_without_data_is_none(hass, madrid_tz):
    provider = make_provider(hass, "abcd")
    assert (
        await provider(
            datetime(2026, 9, 1, tzinfo=MADRID), datetime(2026, 10, 1, tzinfo=MADRID)
        )
        is None
    )


async def test_provider_tolerates_small_gaps(hass, madrid_tz):
    """Se admiten hasta 2 horas sin fila dentro de la ventana (D3)."""
    start = datetime(2026, 9, 1, tzinfo=MADRID)
    end = datetime(2026, 10, 1, tzinfo=MADRID)
    moments = _hours(start, end)
    kept = dict.fromkeys(moments[:100] + moments[102:], 1.0)
    await _write(hass, "consumption", kept)
    await async_wait_recording_done(hass)
    provider = make_provider(hass, "abcd")

    totals = await provider(start, end)

    assert totals is not None
    assert totals.kwh == Decimal(718)
    assert totals.p1 is None
    assert totals.eur is None


async def test_provider_without_costs_has_eur_none(hass, madrid_tz):
    start = datetime(2026, 9, 1, tzinfo=MADRID)
    end = datetime(2026, 10, 1, tzinfo=MADRID)
    await _write_month(hass, start, end, costs=False)
    provider = make_provider(hass, "abcd")

    totals = await provider(start, end)

    assert totals is not None
    assert totals.kwh == Decimal(720)
    assert totals.eur is None


async def test_provider_with_only_one_cost_has_eur_none(hass, madrid_tz):
    start = datetime(2026, 9, 1, tzinfo=MADRID)
    end = datetime(2026, 10, 1, tzinfo=MADRID)
    await _write_month(hass, start, end, costs=False)
    await _write(hass, "power_cost", dict.fromkeys(_hours(start, end), 0.1), unit="EUR")
    await async_wait_recording_done(hass)
    provider = make_provider(hass, "abcd")

    totals = await provider(start, end)

    assert totals is not None
    assert totals.eur is None


async def _consumption_rows(hass, moments: list[datetime]) -> None:
    await _write(hass, "consumption", dict.fromkeys(moments, 1.0))
    await async_wait_recording_done(hass)


@pytest.mark.parametrize(
    ("start", "end", "real_hours"),
    [
        (
            datetime(2026, 10, 1, tzinfo=MADRID),
            datetime(2026, 11, 1, tzinfo=MADRID),
            745,
        ),
        (datetime(2026, 3, 1, tzinfo=MADRID), datetime(2026, 4, 1, tzinfo=MADRID), 743),
        (
            datetime(2026, 9, 1, tzinfo=MADRID),
            datetime(2026, 10, 1, tzinfo=MADRID),
            720,
        ),
    ],
    ids=["october-745h", "march-743h", "september-720h"],
)
@pytest.mark.parametrize(("missing", "covered"), [(2, True), (3, False)])
async def test_provider_min_rows_boundary(
    hass, madrid_tz, start, end, real_hours, missing, covered
):
    """D3: al menos ``horas reales - 2`` filas (misma ZoneInfo en ambos extremos)."""
    moments = _hours(start, end)
    assert len(moments) == real_hours
    await _consumption_rows(hass, moments[:10] + moments[10 + missing :])
    provider = make_provider(hass, "abcd")

    totals = await provider(start, end)

    if covered:
        assert totals is not None
        assert totals.kwh == Decimal(real_hours - missing)
    else:
        assert totals is None


@pytest.mark.parametrize(
    ("first_offset", "covered"), [(1, True), (2, False), (3, False)]
)
async def test_provider_first_row_must_start_before_two_hours(
    hass, madrid_tz, first_offset, covered
):
    start = datetime(2026, 9, 1, tzinfo=MADRID)
    end = datetime(2026, 10, 1, tzinfo=MADRID)
    await _consumption_rows(hass, _hours(start, end)[first_offset:])
    provider = make_provider(hass, "abcd")

    assert (await provider(start, end) is not None) is covered


@pytest.mark.parametrize(("last_offset", "covered"), [(3, True), (4, False)])
async def test_provider_last_row_must_start_at_or_after_end_minus_three_hours(
    hass, madrid_tz, last_offset, covered
):
    """El último inicio de hora es ``end - last_offset`` horas."""
    start = datetime(2026, 9, 1, tzinfo=MADRID)
    end = datetime(2026, 10, 1, tzinfo=MADRID)
    moments = _hours(start, end)
    await _consumption_rows(hass, moments[: len(moments) - (last_offset - 1)])
    provider = make_provider(hass, "abcd")

    assert (await provider(start, end) is not None) is covered

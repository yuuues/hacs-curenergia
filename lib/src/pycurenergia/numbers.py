"""Análisis de números y fechas en formato español."""

import re
from datetime import date
from decimal import Decimal

_DECIMAL_RE = re.compile(r"-?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?")
_SPANISH_DATE_RE = re.compile(r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})")
_DMY_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")

_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def parse_decimal(text: str) -> Decimal:
    """Convierte un número español (``1.234,56``) en ``Decimal``.

    El punto es separador de miles y la coma el decimal; admite signo ``-``.
    Lanza ``ValueError`` si el texto no es un número válido.
    """
    cleaned = text.strip()
    if not _DECIMAL_RE.fullmatch(cleaned):
        raise ValueError(f"Número español no válido: {text!r}")
    return Decimal(cleaned.replace(".", "").replace(",", "."))


def parse_spanish_date(text: str) -> date:
    """Convierte ``5 de agosto de 2026`` en ``date``.

    Acepta cualquier espacio en blanco, saltos de línea incluidos, entre
    palabras. Lanza ``ValueError`` si la entrada no es válida.
    """
    match = _SPANISH_DATE_RE.fullmatch(text.strip().lower())
    if match is None:
        raise ValueError(f"Fecha textual no válida: {text!r}")
    day, month_name, year = match.groups()
    month = _MONTHS.get(month_name)
    if month is None:
        raise ValueError(f"Mes desconocido en la fecha: {text!r}")
    return date(int(year), month, int(day))


def parse_dmy(text: str) -> date:
    """Convierte ``dd/mm/aaaa`` en ``date``. Lanza ``ValueError`` si no es válida."""
    match = _DMY_RE.fullmatch(text.strip())
    if match is None:
        raise ValueError(f"Fecha dd/mm/aaaa no válida: {text!r}")
    day, month, year = match.groups()
    return date(int(year), int(month), int(day))

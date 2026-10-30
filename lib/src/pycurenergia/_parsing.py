"""Utilidades comunes a los lectores de facturas."""

import re
from collections.abc import Callable
from datetime import date
from decimal import Decimal

from pycurenergia.errors import InvoiceParseError
from pycurenergia.models import MeterReading
from pycurenergia.numbers import parse_decimal

NUM = r"-?\d[\d.]*(?:,\d+)?"
"""Patrón de un número en formato español (se interpreta con ``parse_decimal``)."""

BOL = r"(?:^|(?<=\f))"
"""Inicio de línea (con ``re.MULTILINE``) o justo tras un ``\\f``.

Las páginas se unen con ``\\f``, que puede quedar en mitad de una línea.
"""

CUPS = r"ES(?:[ \t]?\d){16}[ \t]?[A-Z]{2}(?:[ \t]?\d[A-Z])?\b"
"""CUPS: ``ES``, 16 dígitos, 2 letras de control y sufijo opcional (dígito y
letra), con espacios o tabuladores sueltos entre grupos."""

LINE_BREAK_RE = re.compile(r"[\n\f]")
"""Separa líneas tanto por ``\\n`` como por ``\\f`` (salto de página)."""


def compact(value: str) -> str:
    """Quita todo el espacio en blanco de ``value`` (p. ej. el CUPS)."""
    return re.sub(r"\s+", "", value)


def search(pattern: re.Pattern[str], text: str, field: str) -> re.Match[str]:
    """Busca ``pattern`` o lanza ``InvoiceParseError`` indicando ``field``."""
    match = pattern.search(text)
    if match is None:
        raise InvoiceParseError(field)
    return match


def convert[T](parse: Callable[[str], T], value: str, field: str) -> T:
    """Aplica ``parse`` a ``value``; un ``ValueError`` pasa a ``InvoiceParseError``."""
    try:
        return parse(value)
    except ValueError as exc:
        raise InvoiceParseError(
            field, f"Valor no válido en {field!r}: {value!r}"
        ) from exc


def to_decimal(value: str, field: str) -> Decimal:
    """Convierte un número español a ``Decimal`` o lanza ``InvoiceParseError``."""
    return convert(parse_decimal, value, field)


def to_reading(value: str, read_on: date, estimated: bool) -> MeterReading | None:
    """Crea una lectura del contador; ``None`` si el número no es válido."""
    try:
        return MeterReading(to_decimal(value, "reading"), read_on, estimated)
    except InvoiceParseError:
        return None

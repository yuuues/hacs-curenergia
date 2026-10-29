"""Utilidades de test: facturas construidas a partir de las fixtures anonimizadas."""

from dataclasses import replace
from pathlib import Path
from typing import Any

from pycurenergia import Invoice, parse_invoice_text

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "lib" / "tests" / "fixtures"


def load_fixture_invoice(name: str) -> Invoice:
    """Parsea ``lib/tests/fixtures/<name>.txt`` (p. ej. ``electricity_2026-10``)."""
    text = (FIXTURES_DIR / f"{name}.txt").read_text(encoding="utf-8")
    return parse_invoice_text(text)


def make_invoice(**changes: Any) -> Invoice:
    """Factura de luz de la fixture con los campos indicados sustituidos."""
    return replace(load_fixture_invoice("electricity_2026-10"), **changes)

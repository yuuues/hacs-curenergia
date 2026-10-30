"""Lector de facturas en PDF de CurEnergía."""

from importlib.metadata import version

from .errors import InvoiceParseError, InvoiceReadError, UnsupportedInvoiceError
from .models import Concept, ConceptKey, Invoice, MeterReading, SupplyType
from .parser import parse_invoice_pdf, parse_invoice_text
from .validation import Problem, check_consistency

__version__ = version("pycurenergia")

__all__ = [
    "Concept",
    "ConceptKey",
    "Invoice",
    "InvoiceParseError",
    "InvoiceReadError",
    "MeterReading",
    "Problem",
    "SupplyType",
    "UnsupportedInvoiceError",
    "__version__",
    "check_consistency",
    "parse_invoice_pdf",
    "parse_invoice_text",
]

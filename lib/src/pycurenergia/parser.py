"""API pública: detecta el tipo de factura y delega en su parser."""

import re

from .electricity import parse_electricity
from .errors import UnsupportedInvoiceError
from .gas import parse_gas
from .models import Invoice
from .text import extract_text

_ELECTRICITY_MARKER = "DATOS DE LA FACTURA DE ELECTRICIDAD"
_GAS_MARKER = "FACTURA DE GAS"
_CORRECTIVE_RE = re.compile(r"FACTURA\s+(?:RECTIFICATIVA|DE\s+ABONO)", re.IGNORECASE)


def parse_invoice_text(text: str) -> Invoice:
    """Parsea el texto ya extraído de una factura de luz o de gas.

    Lanza ``UnsupportedInvoiceError`` si no es una factura de luz ni de gas, o
    si es una factura rectificativa o de abono (no soportadas), e
    ``InvoiceParseError`` si falta un campo obligatorio.
    """
    if _CORRECTIVE_RE.search(text):
        raise UnsupportedInvoiceError(
            "Factura rectificativa o de abono: este tipo no está soportado"
        )
    if _ELECTRICITY_MARKER in text:
        return parse_electricity(text)
    if _GAS_MARKER in text:
        return parse_gas(text)
    raise UnsupportedInvoiceError("El texto no es una factura de luz ni de gas")


def parse_invoice_pdf(data: bytes) -> Invoice:
    """Parsea el contenido de un PDF de factura de CurEnergía.

    Además de los errores de ``parse_invoice_text``, lanza ``InvoiceReadError``
    si el PDF no se puede leer (dañado, cifrado, vacío o demasiado grande).
    """
    return parse_invoice_text(extract_text(data))

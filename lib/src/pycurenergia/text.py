"""Extracción del texto de un PDF de factura."""

from io import BytesIO

from pypdf import PdfReader

from pycurenergia.errors import InvoiceReadError

MAX_PDF_BYTES = 10 * 1024 * 1024
"""Tamaño máximo admitido del PDF (10 MiB); una factura real ocupa mucho menos."""

MAX_PAGES = 20
"""Número máximo de páginas admitido; una factura real tiene 4."""


def extract_text(pdf: bytes) -> str:
    """Devuelve el texto de todas las páginas del PDF.

    Las páginas se separan con un salto de página (``"\\f"``); una página sin
    texto extraíble aporta una cadena vacía. Lanza ``InvoiceReadError`` si el
    PDF supera ``MAX_PDF_BYTES`` o ``MAX_PAGES``, o si no se puede leer
    (dañado, vacío, cifrado con contraseña...).
    """
    if len(pdf) > MAX_PDF_BYTES:
        raise InvoiceReadError(
            f"El PDF ocupa más de {MAX_PDF_BYTES // (1024 * 1024)} MiB"
        )
    # El PDF es una entrada no confiable: cualquier fallo de pypdf (incluido el
    # descifrado) se convierte en InvoiceReadError, sin copiar su mensaje.
    try:
        reader = PdfReader(BytesIO(pdf))
        pages = reader.pages
        page_count = len(pages)
    except Exception as exc:
        raise InvoiceReadError("No se pudo leer el PDF") from exc
    if page_count > MAX_PAGES:
        raise InvoiceReadError(f"El PDF tiene más de {MAX_PAGES} páginas")
    try:
        return "\f".join(page.extract_text() or "" for page in pages)
    except Exception as exc:
        raise InvoiceReadError("No se pudo extraer el texto del PDF") from exc

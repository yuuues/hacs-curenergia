"""Excepciones de la biblioteca."""


class InvoiceParseError(Exception):
    """No se pudo extraer un campo de la factura.

    ``field`` indica qué campo falló.
    """

    def __init__(self, field: str, message: str | None = None) -> None:
        self.field = field
        super().__init__(message or f"No se pudo leer el campo {field!r}")


class UnsupportedInvoiceError(Exception):
    """El PDF no es una factura de un tipo soportado."""


class InvoiceReadError(Exception):
    """No se pudo leer el PDF: dañado, cifrado, vacío o demasiado grande.

    El mensaje nunca incluye texto del PDF; la excepción original de la
    biblioteca de PDF, si la hay, queda en ``__cause__``.
    """

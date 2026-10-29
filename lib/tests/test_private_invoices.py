"""Comprueba las facturas reales del usuario (``private/invoices/``).

No se ejecuta en CI: la carpeta está fuera de git. Los mensajes de fallo solo
incluyen el nombre del fichero, el tipo de excepción, el campo y los códigos de
``Problem``; nunca el texto de la factura.
"""

from pathlib import Path

import pytest

from pycurenergia import (
    InvoiceParseError,
    InvoiceReadError,
    UnsupportedInvoiceError,
    check_consistency,
    parse_invoice_pdf,
)

INVOICES_DIR = Path(__file__).resolve().parents[2] / "private" / "invoices"
PDFS = sorted(INVOICES_DIR.glob("*.pdf")) if INVOICES_DIR.is_dir() else []


def check_invoice(name: str, data: bytes) -> None:
    """Parsea y valida ``data``; si falla, informa solo de ``name`` y el tipo.

    ``from None`` corta la cadena de excepciones: sin él, pytest mostraría el
    mensaje original (y su ``__cause__``) aunque ``pytrace`` sea False.
    """
    try:
        invoice = parse_invoice_pdf(data)
    except (InvoiceParseError, InvoiceReadError, UnsupportedInvoiceError) as exc:
        field = getattr(exc, "field", None)
        detail = f" field={field}" if field else ""
        msg = f"{name}: {type(exc).__name__}{detail}"
        raise pytest.fail.Exception(msg, pytrace=False) from None
    except Exception as exc:
        # Cualquier otro error: nunca mostrar su mensaje ni la traza.
        msg = f"{name}: {type(exc).__name__}"
        raise pytest.fail.Exception(msg, pytrace=False) from None

    problems = check_consistency(invoice)
    assert problems == [], f"{name}: {[p.value for p in problems]}"


@pytest.mark.skipif(not INVOICES_DIR.is_dir(), reason="private/invoices/ no existe")
@pytest.mark.parametrize("path", PDFS, ids=[p.name for p in PDFS])
def test_private_invoice_is_consistent(path):
    check_invoice(path.name, path.read_bytes())


def assert_not_rendered(excinfo, *secrets: str) -> None:
    """Ningún ``secret`` aparece en el fallo tal como lo muestra pytest.

    ``style="value"`` es el formato que usa pytest con ``pytrace=False``; el
    estilo largo incluye además la cadena de excepciones completa. Los secretos
    se construyen por concatenación para que no aparezcan literalmente en el
    código fuente que el estilo largo también muestra.
    """
    for style in ("value", "long"):
        rendered = str(excinfo.getrepr(style=style))
        for secret in secrets:
            assert secret not in rendered, style


def test_unexpected_error_reports_only_name_and_type(monkeypatch):
    secret = "TEXTO PRIVADO " + "DE LA FACTURA"

    def boom(data: bytes):
        raise KeyError(secret)

    monkeypatch.setattr(f"{__name__}.parse_invoice_pdf", boom)

    with pytest.raises(pytest.fail.Exception) as excinfo:
        check_invoice("factura.pdf", b"")

    assert str(excinfo.value) == "factura.pdf: KeyError"
    assert excinfo.value.pytrace is False
    # El fallo no arrastra la excepción original: pytest mostraría su mensaje
    # en la cadena aunque ``pytrace`` sea False.
    assert excinfo.value.__suppress_context__ is True
    assert_not_rendered(excinfo, secret)


def test_known_error_does_not_chain_original_message(monkeypatch):
    cause_text = "TEXTO PRIVADO " + "DEL PDF"
    error_text = "Mensaje de " + "InvoiceReadError"

    def boom(data: bytes):
        try:
            raise ValueError(cause_text)
        except ValueError as cause:
            raise InvoiceReadError(error_text) from cause

    monkeypatch.setattr(f"{__name__}.parse_invoice_pdf", boom)

    with pytest.raises(pytest.fail.Exception) as excinfo:
        check_invoice("factura.pdf", b"")

    assert str(excinfo.value) == "factura.pdf: InvoiceReadError"
    assert excinfo.value.pytrace is False
    assert excinfo.value.__suppress_context__ is True
    assert_not_rendered(excinfo, cause_text, error_text)

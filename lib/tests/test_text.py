from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from pycurenergia import (
    InvoiceReadError,
    UnsupportedInvoiceError,
    parse_invoice_pdf,
    parse_invoice_text,
)
from pycurenergia.text import MAX_PAGES, MAX_PDF_BYTES, extract_text


def _pdf(pages: list[list[str]]) -> bytes:
    """PDF con una página por elemento de ``pages`` y una línea por cadena."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    for lines in pages:
        text = pdf.beginText(20, A4[1] - 20)
        text.setFont("Helvetica", 4, leading=4)
        for line in lines:
            text.textLine(line)
        pdf.drawText(text)
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _two_page_pdf() -> bytes:
    return _pdf([["Página uno"], ["Página dos"]])


def test_extract_text_joins_pages_with_formfeed():
    pages = extract_text(_two_page_pdf()).split("\f")

    assert len(pages) == 2
    assert "Página uno" in pages[0]
    assert "Página dos" in pages[1]


@pytest.mark.parametrize("data", [b"not a pdf", b""], ids=["garbage", "empty"])
def test_unreadable_pdf_raises_read_error(data):
    with pytest.raises(InvoiceReadError):
        parse_invoice_pdf(data)


def test_encrypted_pdf_raises_read_error():
    writer = PdfWriter(clone_from=PdfReader(BytesIO(_two_page_pdf())))
    writer.encrypt(user_password="secreto", algorithm="RC4-128")
    buffer = BytesIO()
    writer.write(buffer)

    with pytest.raises(InvoiceReadError):
        parse_invoice_pdf(buffer.getvalue())


def test_too_many_pages_raises_read_error():
    data = _pdf([[f"Página {n}"] for n in range(MAX_PAGES + 1)])

    with pytest.raises(InvoiceReadError, match=str(MAX_PAGES)):
        extract_text(data)


def test_too_large_pdf_raises_read_error():
    with pytest.raises(InvoiceReadError):
        extract_text(_two_page_pdf() + b"\0" * MAX_PDF_BYTES)


def test_read_error_message_has_no_pdf_text():
    with pytest.raises(InvoiceReadError) as excinfo:
        extract_text(b"%PDF-1.7 NOMBRE SECRETO")

    assert "SECRETO" not in str(excinfo.value)


def test_non_invoice_pdf_is_unsupported():
    with pytest.raises(UnsupportedInvoiceError):
        parse_invoice_pdf(_two_page_pdf())


def test_parse_invoice_pdf_end_to_end(fixture_text):
    # El texto anonimizado de la fixture de gas, dibujado en un PDF sintético.
    text = fixture_text("gas_2026-09")
    pdf = _pdf([page.split("\n") for page in text.split("\f")])

    assert parse_invoice_pdf(pdf) == parse_invoice_text(text)

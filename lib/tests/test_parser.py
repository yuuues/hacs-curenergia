import pytest

from pycurenergia import SupplyType, UnsupportedInvoiceError, parse_invoice_text


@pytest.mark.parametrize(
    ("name", "supply"),
    [
        ("electricity_2026-10", SupplyType.ELECTRICITY),
        ("gas_2026-09", SupplyType.GAS),
    ],
)
def test_dispatches_by_type(fixture_text, name, supply):
    assert parse_invoice_text(fixture_text(name)).supply == supply


def test_unknown_text_raises():
    with pytest.raises(UnsupportedInvoiceError):
        parse_invoice_text("Hola, adjunto el folleto")


@pytest.mark.parametrize(
    "marker", ["FACTURA RECTIFICATIVA", "Factura de abono", "factura\nrectificativa"]
)
@pytest.mark.parametrize("name", ["electricity_2026-10", "gas_2026-09"])
def test_corrective_or_credit_invoice_is_unsupported(fixture_text, name, marker):
    text = f"{marker}\n{fixture_text(name)}"

    with pytest.raises(UnsupportedInvoiceError, match="rectificativa o de abono"):
        parse_invoice_text(text)


def test_pypdf_floor_excludes_versions_with_known_dos():
    # pypdf < 6.0 tiene CVE de denegación de servicio (p. ej. CVE-2025-55197).
    from importlib.metadata import requires

    assert "pypdf>=6.0" in (requires("pycurenergia") or [])


def test_public_api():
    import importlib.metadata

    import pycurenergia

    assert pycurenergia.__version__ == "0.1.0"
    assert pycurenergia.__version__ == importlib.metadata.version("pycurenergia")
    assert all(hasattr(pycurenergia, name) for name in pycurenergia.__all__)
    assert {
        "parse_invoice_pdf",
        "parse_invoice_text",
        "Invoice",
        "Concept",
        "ConceptKey",
        "SupplyType",
        "Problem",
        "check_consistency",
        "InvoiceParseError",
        "InvoiceReadError",
        "UnsupportedInvoiceError",
        "__version__",
    } <= set(pycurenergia.__all__)

"""Tests del UTF-7 modificado de IMAP."""

import pytest

from custom_components.curenergia.imap_utf7 import decode, encode


@pytest.mark.parametrize(
    ("plain", "wire"),
    [
        ("INBOX", "INBOX"),
        ("Facturas/Energía", "Facturas/Energ&AO0-a"),
        ("A&B", "A&-B"),
        ("[Gmail]/Todos", "[Gmail]/Todos"),
        ("日本", "&ZeVnLA-"),
        ("Año y más", "A&APE-o y m&AOE-s"),
        ("😀", "&2D3eAA-"),
    ],
)
def test_utf7_round_trip(plain: str, wire: str) -> None:
    assert encode(plain) == wire
    assert decode(wire) == plain


def test_decode_ampersand_only() -> None:
    assert decode("&-") == "&"


def test_decode_unterminated_sequence_is_left_untouched() -> None:
    assert decode("abc&AO0") == "abc&AO0"


def test_slash_in_base64_is_written_as_comma() -> None:
    # U+3FFF -> bytes 3F FF -> base64 "P/8=" -> "&P,8-"
    assert encode("㿿") == "&P,8-"
    assert decode("&P,8-") == "㿿"

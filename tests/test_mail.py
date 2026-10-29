"""Tests del cliente IMAP de solo lectura."""

import imaplib
import ssl
from decimal import Decimal

import pytest

from custom_components.curenergia.const import SENDER
from custom_components.curenergia.mail import (
    MailAuthError,
    MailClient,
    MailConnectionError,
    default_folder,
    parse_email_total,
)

from .fake_imap import FAKE_PDF, FakeFolder, FakeIMAP, build_message

WIRE = "Facturas/Energ&AO0-a"
HTML = "<td>Importe: 1.058,40&nbsp;€</td>"


def make_client(fake: FakeIMAP, password: str = "ok") -> MailClient:
    return MailClient(
        "imap.test",
        993,
        "usuario-secreto",
        password,
        imap_factory=lambda host, port: fake,
    )


def make_fake() -> FakeIMAP:
    messages = {
        1: build_message(html=HTML, pdfs=(FAKE_PDF,)),
        2: build_message(html="<p>Importe: 20,00 €</p>", pdfs=(FAKE_PDF, FAKE_PDF)),
    }
    return FakeIMAP(
        {
            "INBOX": FakeFolder(1, {}),
            "[Gmail]": FakeFolder(1, {}, noselect=True),
            WIRE: FakeFolder(7, messages),
        }
    )


def test_list_folders_decodes_and_skips_noselect() -> None:
    folders = make_client(make_fake()).list_folders()
    assert folders == ["Facturas/Energía", "INBOX"]
    assert "[Gmail]" not in folders


def test_list_folders_accepts_quoted_and_unquoted_names() -> None:
    fake = FakeIMAP(
        {
            "INBOX": FakeFolder(1),
            "[Gmail]/All Mail": FakeFolder(1),
            "Con espacio": FakeFolder(1),
        }
    )
    assert make_client(fake).list_folders() == [
        "Con espacio",
        "INBOX",
        "[Gmail]/All Mail",
    ]


def test_list_folders_accepts_literal_names() -> None:
    fake = FakeIMAP({"INBOX": FakeFolder(1)})
    fake.list = lambda: (  # type: ignore[method-assign]
        "OK",
        [(b'(\\HasNoChildren) "/" {10}', b"Facturas 24"), b")"],
    )
    assert make_client(fake).list_folders() == ["Facturas 24"]


def test_fetch_selects_readonly_with_quoted_utf7_name() -> None:
    fake = make_fake()
    make_client(fake).fetch("Facturas/Energía", [], None)
    assert fake.selected == (f'"{WIRE}"', True)
    assert fake.search_args == (None, "FROM", f'"{SENDER}"')


def test_fetch_returns_messages_and_pdfs() -> None:
    result = make_client(make_fake()).fetch("Facturas/Energía", [], 7)
    assert result.uidvalidity == 7
    assert result.all_uids == frozenset({1, 2})
    assert [m.uid for m in result.messages] == [1, 2]
    assert result.messages[0].email_total == Decimal("1058.40")
    assert result.messages[0].pdfs == (FAKE_PDF,)
    assert result.messages[1].email_total == Decimal("20.00")
    assert len(result.messages[1].pdfs) == 2


def test_fetch_uses_body_peek_and_skips_known_uids() -> None:
    fake = make_fake()
    result = make_client(fake).fetch("Facturas/Energía", {1}, 7)
    assert [uid for uid, _ in fake.fetched_commands] == ["2"]
    assert all("BODY.PEEK[]" in spec for _, spec in fake.fetched_commands)
    assert result.all_uids == frozenset({1, 2})
    assert [m.uid for m in result.messages] == [2]


def test_fetch_ignores_skip_when_uidvalidity_changed() -> None:
    fake = make_fake()
    result = make_client(fake).fetch("Facturas/Energía", {1, 2}, 999)
    assert [uid for uid, _ in fake.fetched_commands] == ["1", "2"]
    assert result.uidvalidity == 7
    assert [m.uid for m in result.messages] == [1, 2]


def test_fetch_ignores_skip_when_uidvalidity_unknown() -> None:
    fake = make_fake()
    make_client(fake).fetch("Facturas/Energía", {1, 2}, None)
    assert [uid for uid, _ in fake.fetched_commands] == ["1", "2"]


def test_fetch_drops_message_from_other_sender() -> None:
    fake = FakeIMAP(
        {
            "INBOX": FakeFolder(
                3,
                {
                    1: build_message(
                        sender="otro@ejemplo.es", html=HTML, pdfs=(FAKE_PDF,)
                    ),
                    2: build_message(
                        sender=SENDER.upper(), html=HTML, pdfs=(FAKE_PDF,)
                    ),
                },
            )
        }
    )
    result = make_client(fake).fetch("INBOX", [], None)
    assert result.all_uids == frozenset({1, 2})
    assert [m.uid for m in result.messages] == [2]


def test_fetch_message_without_pdf_has_empty_pdfs() -> None:
    fake = FakeIMAP({"INBOX": FakeFolder(3, {5: build_message(html="<p>Aviso</p>")})})
    result = make_client(fake).fetch("INBOX", [], None)
    assert result.messages[0].pdfs == ()
    assert result.messages[0].email_total is None


def test_fetch_prefers_plain_text_for_total() -> None:
    raw = build_message(
        plain="Importe: 10,00 €", html="<p>Importe: 99,00 €</p>", pdfs=(FAKE_PDF,)
    )
    fake = FakeIMAP({"INBOX": FakeFolder(3, {1: raw})})
    result = make_client(fake).fetch("INBOX", [], None)
    assert result.messages[0].email_total == Decimal("10.00")
    assert result.messages[0].pdfs == (FAKE_PDF,)


def test_fetch_detects_pdf_by_filename_extension() -> None:
    from email.message import EmailMessage

    msg = EmailMessage()
    msg["From"] = SENDER
    msg.set_content("hola")
    msg.add_attachment(
        FAKE_PDF, maintype="application", subtype="octet-stream", filename="Factura.PDF"
    )
    fake = FakeIMAP({"INBOX": FakeFolder(3, {1: msg.as_bytes()})})
    result = make_client(fake).fetch("INBOX", [], None)
    assert result.messages[0].pdfs == (FAKE_PDF,)


def test_fetch_unknown_folder_raises_connection_error() -> None:
    fake = make_fake()
    with pytest.raises(MailConnectionError):
        make_client(fake).fetch("No existe", [], None)
    assert fake.logged_out


def test_parse_email_total_from_html() -> None:
    assert parse_email_total("<td>Importe: 1.058,40&nbsp;€</td>") == Decimal("1058.40")
    assert parse_email_total("<td>Importe:</td><td><b>7,05</b> €</td>") == Decimal(
        "7.05"
    )
    assert parse_email_total("sin importe") is None


def test_check_login_logs_in_and_out() -> None:
    fake = make_fake()
    make_client(fake).check_login()
    assert fake.logged_in and fake.logged_out


def test_login_rejected_raises_auth_error() -> None:
    fake = make_fake()
    with pytest.raises(MailAuthError) as err:
        make_client(fake, password="mala-clave").check_login()
    assert "usuario-secreto" not in str(err.value)
    assert "mala-clave" not in str(err.value)
    assert fake.logged_out


def test_socket_error_raises_connection_error() -> None:
    def factory(host: str, port: int) -> imaplib.IMAP4:
        raise OSError("boom usuario-secreto")

    client = MailClient("imap.test", 993, "usuario-secreto", "ok", imap_factory=factory)
    with pytest.raises(MailConnectionError) as err:
        client.check_login()
    assert "usuario-secreto" not in str(err.value)


def test_ssl_error_after_login_raises_connection_error() -> None:
    fake = make_fake()

    def boom(*args: object, **kwargs: object) -> None:
        raise ssl.SSLError("eof")

    fake.list = boom  # type: ignore[method-assign]
    with pytest.raises(MailConnectionError):
        make_client(fake).list_folders()
    assert fake.logged_out


def test_imap_error_after_login_raises_connection_error() -> None:
    fake = make_fake()

    def boom(*args: object, **kwargs: object) -> None:
        raise imaplib.IMAP4.error("fallo")

    fake.select = boom  # type: ignore[method-assign]
    with pytest.raises(MailConnectionError):
        make_client(fake).fetch("INBOX", [], None)
    assert fake.logged_out


def test_default_folder_prefers_curenergia_label() -> None:
    assert default_folder(["INBOX", "[Gmail]/All Mail", "CurEnergía"]) == "CurEnergía"
    assert (
        default_folder(["INBOX", "[Gmail]/All Mail", "facturas/CURENERGIA"])
        == "facturas/CURENERGIA"
    )
    assert default_folder(["INBOX", "[Gmail]/All Mail"]) == "[Gmail]/All Mail"
    assert default_folder(["INBOX"]) == "INBOX"


def test_default_factory_uses_ha_ssl_context_and_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[tuple, dict]] = []

    def fake_ssl(*args: object, **kwargs: object) -> FakeIMAP:
        calls.append((args, kwargs))
        return make_fake()

    monkeypatch.setattr(imaplib, "IMAP4_SSL", fake_ssl)
    MailClient("imap.test", 993, "u", "ok").check_login()
    ((args, kwargs),) = calls
    assert args == ("imap.test", 993)
    assert isinstance(kwargs["ssl_context"], ssl.SSLContext)
    assert kwargs["timeout"] == 30


def test_login_abort_is_connection_error_not_auth_error() -> None:
    fake = make_fake()

    def boom(*args: object, **kwargs: object) -> None:
        raise imaplib.IMAP4.abort("socket error: EOF")

    fake.login = boom  # type: ignore[method-assign]
    with pytest.raises(MailConnectionError) as err:
        make_client(fake).check_login()
    assert not isinstance(err.value, MailAuthError)
    assert "usuario-secreto" not in str(err.value)
    assert fake.logged_out


def test_login_oserror_is_connection_error() -> None:
    fake = make_fake()

    def boom(*args: object, **kwargs: object) -> None:
        raise ssl.SSLError("reset")

    fake.login = boom  # type: ignore[method-assign]
    with pytest.raises(MailConnectionError):
        make_client(fake).check_login()
    assert fake.logged_out


def test_fetch_falls_back_to_html_when_plain_has_no_total() -> None:
    raw = build_message(plain="Hola", html=HTML, pdfs=(FAKE_PDF,))
    fake = FakeIMAP({"INBOX": FakeFolder(3, {1: raw})})
    result = make_client(fake).fetch("INBOX", [], None)
    assert result.messages[0].email_total == Decimal("1058.40")


def test_list_folders_survives_malformed_utf7_name() -> None:
    fake = FakeIMAP({"INBOX": FakeFolder(1), "Mal&AA-": FakeFolder(1)})
    assert make_client(fake).list_folders() == ["INBOX", "Mal&AA-"]


def test_list_folders_drops_names_with_line_breaks() -> None:
    fake = FakeIMAP({"INBOX": FakeFolder(1), "A&AAo-B": FakeFolder(1)})
    assert make_client(fake).list_folders() == ["INBOX"]


def test_fetch_rejects_folder_with_line_break() -> None:
    fake = make_fake()
    with pytest.raises(MailConnectionError):
        make_client(fake).fetch("A\r\nB", [], None)
    assert fake.selected is None
    assert fake.logged_out


def test_fetch_escapes_quote_and_backslash_in_select_name() -> None:
    name = 'A"B' + chr(92) + "C"
    fake = FakeIMAP({name: FakeFolder(4, {})})
    make_client(fake).fetch(name, [], None)
    assert fake.selected == ('"A' + chr(92) + '"B' + chr(92) * 2 + 'C"', True)

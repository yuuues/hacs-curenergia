"""IMAP falso en memoria con las mismas formas de respuesta que ``imaplib``."""

from __future__ import annotations

import imaplib
from dataclasses import dataclass, field
from email.message import EmailMessage

from custom_components.curenergia.const import SENDER

FAKE_PDF = b"%PDF-1.4 fake"


@dataclass
class FakeFolder:
    """Carpeta del servidor falso (la clave en ``FakeIMAP.folders`` va en UTF-7)."""

    uidvalidity: int
    messages: dict[int, bytes] = field(default_factory=dict)
    noselect: bool = False


def build_message(
    *,
    sender: str = SENDER,
    subject: str = "Aviso",
    html: str | None = None,
    plain: str | None = None,
    pdfs: tuple[bytes, ...] = (),
) -> bytes:
    """Construye un correo RFC 822 con texto/HTML opcional y PDFs adjuntos."""
    msg = EmailMessage()
    msg["From"] = f"CurEnergia <{sender}>"
    msg["To"] = "cliente@ejemplo.es"
    msg["Subject"] = subject
    if plain is not None:
        msg.set_content(plain)
        if html is not None:
            msg.add_alternative(html, subtype="html")
    elif html is not None:
        msg.set_content(html, subtype="html")
    else:
        msg.set_content("")
    for index, data in enumerate(pdfs):
        msg.add_attachment(
            data,
            maintype="application",
            subtype="pdf",
            filename=f"factura_{index}.pdf",
        )
    return msg.as_bytes()


class FakeIMAP:
    """Sustituto de ``imaplib.IMAP4`` para los tests."""

    def __init__(self, folders: dict[str, FakeFolder], password: str = "ok") -> None:
        self.folders = folders
        self.password = password
        self.selected: tuple[str, bool] | None = None
        self.fetched_commands: list[tuple[str, str]] = []
        self.search_args: tuple | None = None
        self.logged_in = False
        self.logged_out = False
        self._current: FakeFolder | None = None

    def login(self, user: str, password: str) -> tuple[str, list[bytes]]:
        if password != self.password:
            raise imaplib.IMAP4.error("[AUTHENTICATIONFAILED] Invalid credentials")
        self.logged_in = True
        return "OK", [b"LOGIN completed"]

    def list(self) -> tuple[str, list[bytes]]:
        lines = []
        for name, folder in self.folders.items():
            flags = "\\Noselect" if folder.noselect else "\\HasNoChildren"
            quoted = name.replace("\\", "\\\\").replace('"', '\\"')
            if " " in name or "[" in name or '"' in name:
                lines.append(f'({flags}) "/" "{quoted}"'.encode("ascii"))
            else:
                lines.append(f'({flags}) "/" {name}'.encode("ascii"))
        return "OK", lines

    def select(
        self, mailbox: str = "INBOX", readonly: bool = False
    ) -> tuple[str, list[bytes]]:
        self.selected = (mailbox, readonly)
        name = mailbox[1:-1] if mailbox.startswith('"') else mailbox
        folder = self.folders.get(name)
        if folder is None or folder.noselect:
            return "NO", [b"[NONEXISTENT] Unknown Mailbox"]
        self._current = folder
        return "OK", [str(len(folder.messages)).encode()]

    def response(self, code: str) -> tuple[str, list[bytes | None]]:
        if code == "UIDVALIDITY" and self._current is not None:
            return code, [str(self._current.uidvalidity).encode()]
        return code, [None]

    def uid(self, command: str, *args: str | None) -> tuple[str, list]:
        assert self._current is not None
        if command == "SEARCH":
            self.search_args = args
            uids = " ".join(str(uid) for uid in sorted(self._current.messages))
            return "OK", [uids.encode()]
        if command == "FETCH":
            uid, spec = args
            assert isinstance(uid, str)
            self.fetched_commands.append((uid, str(spec)))
            raw = self._current.messages[int(uid)]
            header = f"{uid} (UID {uid} BODY[] {{{len(raw)}}}".encode()
            return "OK", [(header, raw), b")"]
        raise AssertionError(f"unexpected UID command {command}")

    def logout(self) -> tuple[str, list[bytes]]:
        self.logged_out = True
        return "BYE", [b"Logging out"]

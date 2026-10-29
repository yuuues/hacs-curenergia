"""Cliente IMAP de solo lectura para los correos de facturas de CurEnergía."""

from __future__ import annotations

import html
import imaplib
import re
import ssl
import unicodedata
from collections.abc import Callable, Collection, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
from email import message_from_bytes
from email.message import EmailMessage
from email.policy import default as default_policy
from email.utils import parseaddr

from pycurenergia.numbers import parse_decimal

from . import imap_utf7
from .const import SENDER

_IMAP_TIMEOUT = 30
# R26: los correos más grandes no se descargan (se cuentan como no soportados).
MAX_MESSAGE_BYTES = 15 * 1024 * 1024
# R26: correos que se descargan como mucho en cada ``fetch``.
DEFAULT_FETCH_LIMIT = 20
_SIZE_RE = re.compile(rb"RFC822\.SIZE (\d+)")
_UID_RE = re.compile(rb"UID (\d+)")
_TAG_RE = re.compile(r"<[^>]*>")
_TOTAL_RE = re.compile(r"Importe:\s*([\d.]+,\d{2})\s*€")
_LIST_RE = re.compile(r"^\((?P<flags>[^)]*)\)\s+(?:\"[^\"]*\"|NIL)\s+(?P<name>.+)$")


class MailAuthError(Exception):
    """El servidor IMAP rechazó las credenciales."""


class MailConnectionError(Exception):
    """No se pudo hablar con el servidor IMAP."""


@dataclass(frozen=True)
class MailMessage:
    """Correo del remitente de CurEnergía."""

    uid: int
    email_total: Decimal | None
    pdfs: tuple[bytes, ...]


@dataclass(frozen=True)
class FetchResult:
    """Resultado de leer una carpeta."""

    uidvalidity: int
    # Todos los UID del remitente en la carpeta.
    all_uids: frozenset[int]
    # Correos del remitente descargados en este lote (``fetched`` sin los que
    # se descartan: otro remitente o respuesta vacía).
    messages: tuple[MailMessage, ...]
    # UID descargados en este lote, tengan mensaje o no.
    fetched: frozenset[int]
    # UID nuevos de más de ``MAX_MESSAGE_BYTES``: no se descargan.
    oversized: frozenset[int]
    # Quedan UID nuevos (no demasiado grandes) por descargar.
    remaining: bool


def _default_factory(host: str, port: int) -> imaplib.IMAP4:
    # Import diferido: el resto del módulo no depende de Home Assistant.
    from homeassistant.util.ssl import get_default_context

    return imaplib.IMAP4_SSL(
        host, port, ssl_context=get_default_context(), timeout=_IMAP_TIMEOUT
    )


def parse_email_total(body: str) -> Decimal | None:
    """Extrae el importe ``Importe: N,NN €`` de un cuerpo de correo (texto o HTML)."""
    text = html.unescape(_TAG_RE.sub("", body))
    match = _TOTAL_RE.search(text)
    if match is None:
        return None
    return parse_decimal(match.group(1))


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def default_folder(folders: list[str]) -> str:
    """Elige la carpeta por defecto: CurEnergía, ``[Gmail]/All Mail`` o ``INBOX``."""
    for folder in folders:
        if "curenergia" in _fold(folder):
            return folder
    if "[Gmail]/All Mail" in folders:
        return "[Gmail]/All Mail"
    return "INBOX"


def _as_text(data: bytes | str) -> str:
    return data if isinstance(data, str) else data.decode("utf-8", errors="replace")


def _unquote(name: str) -> str:
    if len(name) >= 2 and name[0] == '"' and name[-1] == '"':
        return re.sub(r"\\(.)", r"\1", name[1:-1])
    return name


def _parse_list_line(line: bytes | str | tuple) -> tuple[str, str] | None:
    """Devuelve ``(flags, nombre en UTF-7)`` de una línea de ``LIST``."""
    if isinstance(line, tuple):
        # Respuesta con literal: (b'(flags) "/" {n}', b'nombre').
        flags = re.match(r"\((?P<flags>[^)]*)\)", _as_text(line[0]))
        if flags is None:
            return None
        return flags.group("flags"), _as_text(line[1])
    match = _LIST_RE.match(_as_text(line).strip())
    if match is None:
        return None
    return match.group("flags"), _unquote(match.group("name").strip())


def _message_text(msg: EmailMessage, subtype: str) -> str | None:
    for part in msg.walk():
        if part.get_content_type() != f"text/{subtype}":
            continue
        if part.get_content_disposition() == "attachment":
            continue
        try:
            return str(part.get_content())
        except (LookupError, UnicodeError, KeyError):
            payload = part.get_payload(decode=True)
            if isinstance(payload, bytes):
                return payload.decode("utf-8", errors="replace")
    return None


def _is_pdf(part: EmailMessage) -> bool:
    if part.get_content_type() == "application/pdf":
        return True
    filename = part.get_filename()
    return bool(filename) and filename.lower().endswith(".pdf")


def _parse_message(uid: int, raw: bytes) -> MailMessage | None:
    msg = message_from_bytes(raw, policy=default_policy)
    sender = parseaddr(str(msg.get("From", "")))[1].lower()
    if sender != SENDER:
        return None
    pdfs: list[bytes] = []
    for part in msg.walk():
        if part.is_multipart() or not _is_pdf(part):
            continue
        payload = part.get_payload(decode=True)
        if isinstance(payload, bytes):
            pdfs.append(payload)
    total = None
    for subtype in ("plain", "html"):
        body = _message_text(msg, subtype)
        total = parse_email_total(body) if body is not None else None
        if total is not None:
            break
    return MailMessage(uid=uid, email_total=total, pdfs=tuple(pdfs))


def _sizes_from_fetch(data: list) -> dict[int, int]:
    """``UID → RFC822.SIZE`` de la respuesta de ``UID FETCH (RFC822.SIZE)``."""
    sizes: dict[int, int] = {}
    for item in data:
        if not isinstance(item, bytes):
            continue
        uid = _UID_RE.search(item)
        size = _SIZE_RE.search(item)
        if uid is not None and size is not None:
            sizes[int(uid.group(1))] = int(size.group(1))
    return sizes


def _raw_from_fetch(data: list) -> bytes | None:
    for item in data:
        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], bytes):
            return item[1]
    return None


class MailClient:
    """Cliente IMAP síncrono (pensado para ejecutarse en el executor)."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        *,
        imap_factory: Callable[[str, int], imaplib.IMAP4] | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._factory = imap_factory or _default_factory

    @contextmanager
    def _session(self) -> Iterator[imaplib.IMAP4]:
        """Conecta y hace login; siempre intenta ``logout``.

        Los mensajes de las excepciones no incluyen usuario ni contraseña.
        """
        try:
            conn = self._factory(self._host, self._port)
        except (OSError, imaplib.IMAP4.error) as err:
            raise MailConnectionError(
                f"Cannot connect to the IMAP server ({type(err).__name__})"
            ) from None
        try:
            try:
                conn.login(self._username, self._password)
            except (imaplib.IMAP4.abort, OSError) as err:
                raise MailConnectionError(
                    f"IMAP connection failed during login ({type(err).__name__})"
                ) from None
            except imaplib.IMAP4.error:
                raise MailAuthError("IMAP login rejected") from None
            try:
                yield conn
            except (OSError, ssl.SSLError, imaplib.IMAP4.error) as err:
                raise MailConnectionError(
                    f"IMAP connection failed ({type(err).__name__})"
                ) from None
        finally:
            try:
                conn.logout()
            except (OSError, imaplib.IMAP4.error):
                pass

    def check_login(self) -> None:
        """Comprueba que las credenciales son válidas."""
        with self._session():
            pass

    def list_folders(self) -> list[str]:
        """Devuelve los nombres de carpeta seleccionables, decodificados y ordenados."""
        with self._session() as conn:
            status, data = conn.list()
            if status != "OK":
                raise MailConnectionError("IMAP LIST failed")
            names: list[str] = []
            for line in data:
                if line is None:
                    continue
                parsed = _parse_list_line(line)
                if parsed is None:
                    continue
                flags, wire = parsed
                if "\\noselect" in flags.lower():
                    continue
                try:
                    name = imap_utf7.decode(wire)
                except ValueError:
                    # UTF-7 mal formado: se usa el nombre tal cual.
                    name = wire
                if "\r" in name or "\n" in name:
                    continue  # no se puede seleccionar con seguridad
                names.append(name)
            return sorted(names)

    def fetch(
        self,
        folder: str,
        skip_uids: Collection[int],
        uidvalidity: int | None,
        limit: int = DEFAULT_FETCH_LIMIT,
    ) -> FetchResult:
        """Lee los correos del remitente en ``folder`` sin marcarlos como leídos.

        Si ``uidvalidity`` no coincide con el del servidor, ``skip_uids`` se ignora.

        R26: primero pide el tamaño de los UID nuevos; los de más de
        ``MAX_MESSAGE_BYTES`` no se descargan (``oversized``). Del resto
        descarga como mucho ``limit``, en orden ascendente; ``remaining`` dice
        si quedan más.
        """
        with self._session() as conn:
            if "\r" in folder or "\n" in folder:
                raise MailConnectionError("Invalid IMAP folder name")
            wire = imap_utf7.encode(folder)
            quoted = wire.replace("\\", "\\\\").replace('"', '\\"')
            status, _ = conn.select(f'"{quoted}"', readonly=True)
            if status != "OK":
                raise MailConnectionError("Cannot select the IMAP folder")
            _, validity = conn.response("UIDVALIDITY")
            try:
                server_validity = int(validity[0])
            except (TypeError, ValueError):
                raise MailConnectionError("IMAP server gave no UIDVALIDITY") from None

            status, found = conn.uid("SEARCH", None, "FROM", f'"{SENDER}"')
            if status != "OK":
                raise MailConnectionError("IMAP SEARCH failed")
            all_uids = frozenset(int(u) for u in (found[0] or b"").split())

            skip = (
                frozenset(skip_uids) if uidvalidity == server_validity else frozenset()
            )
            new = sorted(all_uids - skip)
            oversized: frozenset[int] = frozenset()
            if new:
                uid_set = ",".join(str(uid) for uid in new)
                status, data = conn.uid("FETCH", uid_set, "(RFC822.SIZE)")
                if status != "OK":
                    raise MailConnectionError("IMAP FETCH failed")
                sizes = _sizes_from_fetch(data)
                oversized = frozenset(
                    uid for uid in new if sizes.get(uid, 0) > MAX_MESSAGE_BYTES
                )
            wanted = [uid for uid in new if uid not in oversized]
            batch = wanted[:limit]

            messages: list[MailMessage] = []
            for uid in batch:
                status, data = conn.uid("FETCH", str(uid), "(BODY.PEEK[])")
                if status != "OK":
                    raise MailConnectionError("IMAP FETCH failed")
                raw = _raw_from_fetch(data)
                if raw is None:
                    continue
                parsed = _parse_message(uid, raw)
                if parsed is not None:
                    messages.append(parsed)
            return FetchResult(
                uidvalidity=server_validity,
                all_uids=all_uids,
                messages=tuple(messages),
                fetched=frozenset(batch),
                oversized=oversized,
                remaining=len(wanted) > len(batch),
            )

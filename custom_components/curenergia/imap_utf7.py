"""UTF-7 modificado de IMAP (RFC 3501 §5.1.3) para nombres de carpeta."""

from base64 import b64decode, b64encode


def _is_printable_ascii(char: str) -> bool:
    return 0x20 <= ord(char) <= 0x7E


def _encode_run(run: str) -> str:
    raw = b64encode(run.encode("utf-16-be")).decode("ascii")
    return "&" + raw.rstrip("=").replace("/", ",") + "-"


def encode(name: str) -> str:
    """Convierte un nombre de carpeta Unicode a UTF-7 modificado."""
    out: list[str] = []
    run: list[str] = []
    for char in name:
        if _is_printable_ascii(char):
            if run:
                out.append(_encode_run("".join(run)))
                run.clear()
            out.append("&-" if char == "&" else char)
        else:
            run.append(char)
    if run:
        out.append(_encode_run("".join(run)))
    return "".join(out)


def _decode_run(chunk: str) -> str:
    padded = chunk.replace(",", "/")
    padded += "=" * (-len(padded) % 4)
    return b64decode(padded).decode("utf-16-be")


def decode(name: str) -> str:
    """Convierte un nombre de carpeta en UTF-7 modificado a Unicode."""
    out: list[str] = []
    pos = 0
    while pos < len(name):
        start = name.find("&", pos)
        if start == -1:
            out.append(name[pos:])
            break
        out.append(name[pos:start])
        end = name.find("-", start + 1)
        if end == -1:
            # Secuencia sin cerrar: se deja tal cual.
            out.append(name[start:])
            break
        chunk = name[start + 1 : end]
        out.append("&" if not chunk else _decode_run(chunk))
        pos = end + 1
    return "".join(out)

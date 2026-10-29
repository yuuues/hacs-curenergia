"""Anonimiza el texto de una factura de CurEnergía para usarlo como fixture.

Uso:
    anonymize.py PDF --out TXT [--secrets SECRETS]
    anonymize.py --check TXT... [--secrets SECRETS]

Los valores reales y sus sustitutos se leen de ``private/secrets.toml``
(excluido de git)::

    [replace]
    "valor real" = "valor falso"

    [drop]
    patterns = ["regex que elimina la línea entera"]

El script no se empaqueta con la librería.
"""

import argparse
import re
import sys
import tomllib
from pathlib import Path

from pycurenergia.text import extract_text

DEFAULT_SECRETS = Path(__file__).parents[2] / "private" / "secrets.toml"
FAKE_NIF = "00000000T"

_NIF_RE = re.compile(r"\b\d{8}[A-Z]\b")
_LONG_DIGITS_RE = re.compile(r"\d{20,}")
_WORD_RE = re.compile(r"[^\W\d_]{4,}")
_SYMBOL_CHARS = frozenset("\t[]{}<>@_=^~|\\")
_ALLOWED_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    "áéíóúüñÁÉÍÓÚÜÑçÇªº"
    ".,:;()/%€-'\"*+&!?¿¡"
)


def _is_noise(line: str) -> bool:
    """Indica si la línea es un código de barras o texto de una fuente de glifos."""
    if _LONG_DIGITS_RE.search(line):
        return True
    visible = [c for c in line if not c.isspace()]
    outside = sum(1 for c in visible if c not in _ALLOWED_CHARS)
    if outside * 2 > len(visible):
        return True
    return not _WORD_RE.search(line) and any(c in _SYMBOL_CHARS for c in line)


def drop_noise_lines(text: str, patterns: list[str] | None = None) -> str:
    """Elimina las líneas de códigos de barras y glifos sin sentido.

    ``patterns`` son expresiones regulares adicionales: se elimina toda línea
    en la que alguna de ellas encuentre coincidencia. Cada página (separada por
    ``"\\f"``) se trata por separado para no perder los saltos de página, que
    pypdf deja a veces en mitad de una línea.
    """
    extra = [re.compile(p) for p in patterns or []]

    def keep(line: str) -> bool:
        return not _is_noise(line) and not any(p.search(line) for p in extra)

    pages = text.split("\f")
    return "\f".join("\n".join(filter(keep, page.split("\n"))) for page in pages)


def apply_replacements(text: str, mapping: dict[str, str]) -> str:
    """Sustituye cada valor real por su valor falso.

    Las claves se prueban de la más larga a la más corta, en una sola pasada,
    así que un valor falso nunca se vuelve a sustituir.
    """
    if not mapping:
        return text
    keys = sorted(mapping, key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(k) for k in keys))
    return pattern.sub(lambda m: mapping[m.group(0)], text)


def mask_nif(text: str) -> str:
    """Sustituye cualquier NIF (8 dígitos y una letra) por ``00000000T``."""
    return _NIF_RE.sub(FAKE_NIF, text)


def find_leaks(text: str, mapping: dict[str, str]) -> list[tuple[int, str]]:
    """Busca valores reales que hayan quedado en el texto.

    Devuelve ``(nº de línea, valor real)``, ordenado por línea. Cada valor se
    busca sin distinguir mayúsculas, tal cual y sin espacios en cada línea, y
    además en todo el texto sin ningún espacio en blanco (saltos de línea y de
    página, tabuladores y espacios duros incluidos), para detectar valores
    partidos entre líneas; en ese caso la línea es la de su comienzo. También se
    informa de cualquier NIF distinto de ``00000000T``.
    """
    needles = []
    for real in mapping:
        forms = {real.casefold(), real.replace(" ", "").casefold()}
        needles.append((real, {f for f in forms if f}))
    leaks = []
    reported = set()
    lines = text.split("\n")
    for number, line in enumerate(lines, start=1):
        folded = line.casefold()
        for real, forms in needles:
            if any(f in folded for f in forms):
                leaks.append((number, real))
                reported.add(real)
        for nif in _NIF_RE.findall(line):
            if nif != FAKE_NIF:
                leaks.append((number, nif))

    # Texto sin espacios en blanco, con la línea de origen de cada carácter.
    chars = [
        (folded, number)
        for number, line in enumerate(lines, start=1)
        for c in line
        if not c.isspace()
        for folded in c.casefold()
    ]
    squeezed = "".join(c for c, _ in chars)
    for real in mapping:
        needle = "".join(c for c in real if not c.isspace()).casefold()
        if real in reported or not needle:
            continue
        index = squeezed.find(needle)
        if index >= 0:
            leaks.append((chars[index][1], real))
    leaks.sort(key=lambda leak: leak[0])
    return leaks


def load_secrets(path: Path) -> tuple[dict[str, str], list[str]]:
    """Lee ``[replace]`` y ``[drop] patterns`` del fichero de secretos.

    Lanza ``ValueError`` si el formato no es válido: ``[replace]`` debe ser una
    tabla de cadenas no vacías y ``[drop] patterns`` una lista de cadenas no
    vacías. Los mensajes nunca incluyen los valores del fichero.
    """
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    error = f"{path.name} no válido: "
    replace = data.get("replace", {})
    if not isinstance(replace, dict):
        raise ValueError(error + "[replace] debe ser una tabla")
    for index, (real, fake) in enumerate(replace.items(), start=1):
        if not real.strip() or not isinstance(fake, str) or not fake.strip():
            raise ValueError(
                error + f"la clave nº {index} de [replace] o su valor no es "
                "una cadena no vacía"
            )
    drop = data.get("drop", {})
    patterns = drop.get("patterns", []) if isinstance(drop, dict) else None
    if not isinstance(patterns, list) or not all(
        isinstance(p, str) and p for p in patterns
    ):
        raise ValueError(error + "[drop] patterns debe ser una lista de cadenas")
    return dict(replace), list(patterns)


def anonymize(text: str, mapping: dict[str, str], patterns: list[str]) -> str:
    """Aplica en orden: limpieza de ruido, sustituciones y máscara de NIF."""
    return mask_nif(apply_replacements(drop_noise_lines(text, patterns), mapping))


def _report(name: str, leaks: list[tuple[int, str]], mapping: dict[str, str]) -> None:
    """Informa de cada fuga sin mostrar nunca el valor real.

    Un valor de ``[replace]`` se identifica por su posición en el fichero de
    secretos; un NIF, solo por su longitud.
    """
    keys = list(mapping)
    for number, value in leaks:
        if value in mapping:
            what = f"clave nº {keys.index(value) + 1} de [replace] sin anonimizar"
        else:
            what = f"NIF sin enmascarar ({len(value)} caracteres)"
        print(f"{name}:{number}: {what}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "inputs", nargs="+", type=Path, help="PDF a anonimizar, o TXT con --check"
    )
    parser.add_argument("--out", type=Path, help="fichero de texto de salida")
    parser.add_argument(
        "--check", action="store_true", help="solo comprueba fixtures ya generadas"
    )
    parser.add_argument("--secrets", type=Path, default=DEFAULT_SECRETS)
    args = parser.parse_args(argv)
    # La consola de Windows puede no ser UTF-8; mejor escapar que fallar al informar.
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(errors="backslashreplace")
    if not args.secrets.is_file():
        parser.error(f"no existe el fichero de secretos {args.secrets}")

    try:
        mapping, patterns = load_secrets(args.secrets)
    except ValueError as exc:
        parser.error(str(exc))

    if args.check:
        failed = False
        for path in args.inputs:
            leaks = find_leaks(path.read_text(encoding="utf-8"), mapping)
            _report(str(path), leaks, mapping)
            failed = failed or bool(leaks)
        return 1 if failed else 0

    if len(args.inputs) != 1 or args.out is None:
        parser.error("hay que indicar un único PDF y --out")
    text = anonymize(extract_text(args.inputs[0].read_bytes()), mapping, patterns)
    leaks = find_leaks(text, mapping)
    if leaks:
        _report(str(args.inputs[0]), leaks, mapping)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

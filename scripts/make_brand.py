"""Genera las imágenes de marca de la integración (carpeta ``brand/``).

Icono genérico: una hoja de factura con tres líneas y un rayo ámbar en la
esquina inferior derecha, sobre un cuadrado redondeado. No usa logos ni colores
de CurEnergía. La salida es determinista para una versión dada de Pillow: el
suavizado de bordes puede cambiar algún píxel entre versiones.

    uv run --with pillow python scripts/make_brand.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "curenergia" / "brand"

# Se dibuja sobre un lienzo de SUPERSAMPLE veces el tamaño final y se reduce,
# para que los bordes salgan suavizados.
SUPERSAMPLE = 4

AMBER = "#FFB300"

# (placa, hoja, líneas)
LIGHT = ("#455A64", "#FFFFFF", "#B0BEC5")
DARK = ("#263238", "#CFD8DC", "#78909C")

# Rayo en un rectángulo unitario (x, y) -> se coloca en BOLT_BOX.
BOLT_POINTS = [(0.62, 0.0), (0.12, 0.56), (0.46, 0.56), (0.34, 1.0), (0.9, 0.40), (0.54, 0.40)]
BOLT_BOX = (56.0, 52.0, 36.0, 42.0)  # x, y, ancho, alto (sobre un lienzo de 100)
BOLT_OUTLINE = 3.0


def render(size: int, palette: tuple[str, str, str]) -> Image.Image:
    plate, sheet, lines = palette
    big = size * SUPERSAMPLE
    u = big / 100  # una unidad del diseño, en píxeles del lienzo grande

    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((0, 0, big - 1, big - 1), radius=22 * u, fill=plate)
    draw.rounded_rectangle((22 * u, 14 * u, 72 * u, 86 * u), radius=5 * u, fill=sheet)
    for y, x_end in ((30, 64), (42, 64), (54, 50)):
        draw.rounded_rectangle(
            (30 * u, (y - 2.5) * u, x_end * u, (y + 2.5) * u), radius=2.5 * u, fill=lines
        )

    bx, by, bw, bh = BOLT_BOX
    bolt = [((bx + px * bw) * u, (by + py * bh) * u) for px, py in BOLT_POINTS]
    # Contorno del color de la placa para separar el rayo de la hoja.
    draw.polygon(bolt, fill=plate, outline=plate, width=round(BOLT_OUTLINE * u))
    draw.polygon(bolt, fill=AMBER)

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = {
        "icon.png": (256, LIGHT),
        "icon@2x.png": (512, LIGHT),
        "logo.png": (256, LIGHT),
        "logo@2x.png": (512, LIGHT),
        "dark_icon.png": (256, DARK),
        "dark_logo.png": (256, DARK),
    }
    for name, (size, palette) in targets.items():
        render(size, palette).save(OUT_DIR / name, format="PNG", optimize=True)
        print(OUT_DIR / name)


if __name__ == "__main__":
    main()

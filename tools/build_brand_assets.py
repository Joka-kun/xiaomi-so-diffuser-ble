"""Build the Home Assistant brand icon from the transparent SO S5 SVG master.

No wide logo is shipped: Home Assistant automatically falls back to the square
icon for its integration logo. This avoids a tiny diffuser on a full-width banner.
"""
from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "assets"
DEST = ROOT / "custom_components" / "so_diffuser_ble" / "brand"

BRAND_IMAGES = (
    ("icon.png", "brand-icon.svg", (256, 256)),
    ("icon@2x.png", "brand-icon.svg", (512, 512)),
)


def render_svg(source: str, size: tuple[int, int]) -> Image.Image:
    artwork = (SOURCE / source).read_bytes()
    if any(token in artwork.lower() for token in (b"<script", b"<image", b"<text")):
        raise ValueError(f"Brand master must be self-contained vector geometry: {source}")
    raster = cairosvg.svg2png(
        bytestring=artwork, output_width=size[0], output_height=size[1]
    )
    with Image.open(BytesIO(raster)) as im:
        return im.convert("RGBA")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for filename, source, size in BRAND_IMAGES:
        image = render_svg(source, size)
        image.save(DEST / filename, format="PNG", optimize=True)
        print(f"Generated {filename}: {size[0]}x{size[1]}")
    # Remove the obsolete blue banner. HA uses icon.png as a logo fallback.
    for filename in ("logo.png", "logo@2x.png", "dark_logo.png", "dark_logo@2x.png"):
        (DEST / filename).unlink(missing_ok=True)


if __name__ == "__main__":
    main()

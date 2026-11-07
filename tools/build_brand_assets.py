"""Render first-party SO Diffuser BLE brand assets for Home Assistant.

Single vector source for every output. No AI/API/network calls or Home Assistant
credentials are required. Run after installing CairoSVG and Pillow.
"""
from __future__ import annotations

from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "assets"
DEST = ROOT / "custom_components" / "so_diffuser_ble" / "brand"


def render(svg: Path, name: str, size: tuple[int, int]) -> None:
    path = DEST / name
    cairosvg.svg2png(
        url=str(svg),
        write_to=str(path),
        output_width=size[0],
        output_height=size[1],
    )
    with Image.open(path) as image:
        if image.size != size or image.mode != "RGBA":
            raise ValueError(f"Invalid brand artwork: {name} ({image.size}, {image.mode})")
        image.verify()


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for name, svg, size in (
        ("icon.png", "brand-icon.svg", (256, 256)),
        ("icon@2x.png", "brand-icon.svg", (512, 512)),
        ("logo.png", "brand-logo.svg", (720, 240)),
        ("logo@2x.png", "brand-logo.svg", (960, 320)),
    ):
        render(SOURCE / svg, name, size)
        print(f"Generated {name}: {size[0]}x{size[1]}")


if __name__ == "__main__":
    main()

# Brand and Marketplace icon

This project ships Home Assistant brand assets generated from its own editable SVG artwork.

- `docs/assets/brand-icon.svg` — canonical icon artwork
- `docs/assets/brand-logo.svg` — canonical logo artwork
- `custom_components/so_diffuser_ble/brand/icon.png` — 256 × 256
- `custom_components/so_diffuser_ble/brand/icon@2x.png` — 512 × 512
- `custom_components/so_diffuser_ble/brand/logo.png` — 720 × 240 (shortest side 240)
- `custom_components/so_diffuser_ble/brand/logo@2x.png` — 960 × 320 (shortest side 320)

Regenerate deterministically with `python -m pip install cairosvg pillow` and `python tools/build_brand_assets.py`.

Home Assistant 2026.3+ displays these local brand images **after installation**.

**Before installation in the Marketplace/HACS:** the shared catalog's brands service reads assets from released **catalogued repositories**, which is not the same as a custom repository added by URL. Shipping `brand/icon.png` and publishing a release are necessary publisher steps, but **do not guarantee** an icon in the custom-repository search/add dialog. First-time public catalog indexing requires a separate submission to `hacs/default` and review. Icon/CDN caching may delay propagation.

No official Home Assistant logo or false affiliation is used in the artwork.

Source: https://contributors.home-assistant.io/marketplace/guides/integrations/ .

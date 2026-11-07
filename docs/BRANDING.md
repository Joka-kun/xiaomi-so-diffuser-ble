# Brand and Marketplace icon

This project ships Home Assistant brand assets generated from its own editable SVG artwork.

- `docs/assets/brand-icon.svg` — canonical icon artwork
- `docs/assets/brand-logo.svg` — canonical logo artwork
- `custom_components/so_diffuser_ble/brand/icon.png` — 256 × 256
- `custom_components/so_diffuser_ble/brand/icon@2x.png` — 512 × 512
- `custom_components/so_diffuser_ble/brand/logo.png` — 720 × 240 (shortest side 240)
- `custom_components/so_diffuser_ble/brand/logo@2x.png` — 960 × 320 (shortest side 320)

Regenerate deterministically with `python -m pip install cairosvg pillow` and `python tools/build_brand_assets.py`.

## Premium visual system (November 2026)

The seven illustrations and four installed integration images have been redesigned together in a cinematic midnight / sapphire / amethyst style. They are original vector artwork, not official Xiaomi or Home Assistant logos.

| Artwork | Intended purpose | Visual contract |
| --- | --- | --- |
| `hero.svg` | GitHub README banner across all six languages | Distinctive diffuser, mist and luminous RGB ring, readable branding |
| `brand-icon.svg` | Source for installed HA square icon | Recognizable diffuser silhouette at small sizes |
| `brand-logo.svg` | Source for installed HA landscape wordmark | Stable English product name and visual identity |
| `connection-flow.svg` | Setup guide | Exact four-step sequence, Xiaomi Cloud only during provisioning |
| `control-preview.svg` | README controls illustration | **Conceptual illustration, not a real HA screenshot**; Power above Backlight |
| `migration.svg` | Safe domain transition | Backup, remove old entry through HA UI, install, verify |
| `model-family.svg` | Compatibility overview | SO S5 is field-reported; eight other profiles remain **experimental** |

Base colors: midnight `#070A16`, indigo `#101931`, sapphire `#548EFF`, cyan `#4DE6F6`, violet `#A077FA`, rose `#FF8ABC`, warm metallic highlight `#FFE8BB`. Background artwork stays embedded in the SVG; no external fonts, images, scripts or network requests are used.

**Rendering discipline:** Keep SVGs as the editable source of truth. If either vector changes, rebuild and commit all affected PNG sizes in the same PR. Do not rename brand filenames, relocate documentation graphics or silently replace a released tag. Automated checks cover XML integrity, image sizes, and project links, while visual inspection at 256 px and 512 px remains part of review.

Home Assistant 2026.3+ displays these local brand images **after installation**.

**Before installation in the Marketplace/HACS:** the shared catalog's brands service reads assets from released **catalogued repositories**, which is not the same as a custom repository added by URL. Shipping `brand/icon.png` and publishing a release are necessary publisher steps, but **do not guarantee** an icon in the custom-repository search/add dialog. First-time public catalog indexing requires a separate submission to `hacs/default` and review. Icon/CDN caching may delay propagation.

No official Home Assistant logo or false affiliation is used in the artwork.

Source: https://contributors.home-assistant.io/marketplace/guides/integrations/ .

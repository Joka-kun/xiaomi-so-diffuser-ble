# Brand and Marketplace icon

This project ships Home Assistant brand assets generated from its own editable SVG artwork.

- `docs/assets/brand-icon.svg` — canonical icon artwork
- `docs/assets/brand-logo.svg` — canonical logo artwork
- `custom_components/so_diffuser_ble/brand/icon.png` — 256 × 256
- `custom_components/so_diffuser_ble/brand/icon@2x.png` — 512 × 512
- `custom_components/so_diffuser_ble/brand/logo.png` — 720 × 240 (shortest side 240)
- `custom_components/so_diffuser_ble/brand/logo@2x.png` — 960 × 320 (shortest side 320)

Regenerate deterministically with `python -m pip install cairosvg pillow` and `python tools/build_brand_assets.py`.

## Noir visual system (November 2026)

Seven editable SVG illustrations and four Home Assistant PNG assets share one restrained cinematic-noir identity: charcoal surfaces, brushed ceramic, atmospheric vapour, graphite shadows, subdued ice-blue secondary light and a narrow amber base glow. These are original conceptual illustrations, not photographs or official Xiaomi/Home Assistant logos.

| Artwork | Intended purpose | Visual contract |
| --- | --- | --- |
| `hero.svg` | GitHub README banner across all six languages | Atmospheric ceramic diffuser with amber-lit base; readable product identity, no fabricated UI |
| `brand-icon.svg` | Source for installed HA square icon | Recognizable diffuser silhouette at small sizes |
| `brand-logo.svg` | Source for installed HA landscape wordmark | Stable English product name and visual identity |
| `connection-flow.svg` | Setup guide | Exact four-step sequence, Xiaomi Cloud only during provisioning |
| `control-preview.svg` | README controls illustration | **Conceptual illustration, not a real HA screenshot**; Power above Backlight |
| `migration.svg` | Safe domain transition | Backup, remove old entry through HA UI, install, verify |
| `model-family.svg` | Compatibility overview | SO S5 is field-reported; eight other profiles remain **experimental** |

Noir palette: near-black `#06090C`, dark graphite `#10151A`, silver ceramic `#E6E8E4`, muted blue-grey `#98A4A7`, amber `#D6B17D`. There are no rainbow gradients, cartoon steam strokes or brightly colored cards. Mist is softly blurred and lighting is intentionally restrained. SVG visuals are fully self-contained: no external fonts, images, scripts, tracking or network requests.

**Rendering discipline:** Keep SVGs as the editable source of truth. If either vector changes, rebuild and commit all affected PNG sizes in the same PR. Do not rename brand filenames, relocate documentation graphics or silently replace a released tag. Automated checks cover XML integrity, image sizes, and project links, while visual inspection at 256 px and 512 px remains part of review.

Home Assistant 2026.3+ displays these local brand images **after installation**.

**Before installation in the Marketplace/HACS:** the shared catalog's brands service reads assets from released **catalogued repositories**, which is not the same as a custom repository added by URL. Shipping `brand/icon.png` and publishing a release are necessary publisher steps, but **do not guarantee** an icon in the custom-repository search/add dialog. First-time public catalog indexing requires a separate submission to `hacs/default` and review. Icon/CDN caching may delay propagation.

No official Home Assistant logo or false affiliation is used in the artwork.

Source: https://contributors.home-assistant.io/marketplace/guides/integrations/ .

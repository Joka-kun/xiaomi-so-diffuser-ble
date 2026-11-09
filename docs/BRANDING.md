# Visual identity

## Public GitHub presentation

All six README translations display **exactly two illustrations**:

1. `docs/assets/hero.svg` — the S5-inspired front cover, retained unchanged.
2. `docs/assets/connection-four-steps.png` — the author-supplied connection journey, retained unchanged.

The English and Russian installation guides also keep the earlier `connection-flow.svg` diagram. The new infographic is **additional**, not a replacement. Compatibility statements are Markdown text, never embedded as status badges in artwork.

**README reading order:** short feature summary → HACS installation prerequisite → connection-heading + full-width four-step PNG → four numbered instructions matching **Discover / Authorize / Verify / Control** → OAuth callback tip → compatibility. Installation in HACS is a prerequisite, **not one of the pictured four pairing stages**. The detailed installation guides may retain both visuals.

The cover is conceptual art rather than an actual Xiaomi photograph or a Home Assistant screenshot. Its near-square, light-colored S5 body, dark circular display and lower-right button are based on [Xiaomi's device reference](https://home.mi.com/views/deviceReset.html?locale=en&model=bwj.diffuser.s5). See also [the MIoT specification](https://home.miot-spec.com/spec/bwj.diffuser.s5).

## Asset inventory

| Asset | Role |
| --- | --- |
| `docs/assets/hero.svg` | Main README cover (do not replace without review) |
| `docs/assets/connection-four-steps.png` | Second README illustration and additional installation-guide figure |
| `docs/assets/connection-flow.svg` | Original setup diagram in the English and Russian installation guides |
| `docs/assets/migration.svg` | Technical migration illustration |
| `docs/assets/brand-icon.svg` | Close-cropped S5 icon with transparent background; also used as the HA logo fallback |
| `docs/assets/product.webp`, `hero.webp` | Preserved historical WebP style studies, no longer used by the icon builder |
| `docs/assets/overview.svg`, `control-preview.svg`, `model-family.svg` and other WebP studies | Retained design sources; not displayed in the public README |
| `custom_components/so_diffuser_ble/brand/` | 256/512 px icon PNGs; no wide logo, allowing HA to use its icon fallback |

**Artwork integrity:** `connection-four-steps.png` is 2048 × 682; SHA-256 `244c47e8571025a8661fac9cf0e238a001288b09c63db84a18ff2c9a97817e65`. It is supplied as an original PNG and must not be silently recompressed, substituted or removed.

## Images in Marketplace **before installation**

Home Assistant serves installed custom-integration images through its local
Brands API. **The Marketplace tile before installation is different:** it
fetches `https://brands.home-assistant.io/marketplace/so_diffuser_ble/icon.png`.
The official [Marketplace publishing guide](https://contributors.home-assistant.io/marketplace/guides/integrations/)
and [brands service](https://github.com/home-assistant/brands#marketplace-icons)
specify that an hourly indexer discovers icons at
`custom_components/so_diffuser_ble/brand/` **in the latest GitHub release**.

The v1.0.5 release includes `icon.png` (256 × 256) and
`icon@2x.png` (512 × 512) in that exact directory; these are tested
for PNG format, size, transparency and render integrity. No duplicated
`custom_integrations/` asset needs to be uploaded to
`home-assistant/brands`. The Marketplace's index, GitHub availability,
browser cache and CDN are separate dependencies.

To diagnose a generic **icon not available** tile, check the public
[Marketplace icon endpoint](https://brands.home-assistant.io/marketplace/so_diffuser_ble/icon.png):
a valid response has HTTP 200 and content type `image/png`; a 404 means
the service considers the icon absent, and 503 means availability is not
currently known. The index runs about hourly. Browser/CDN cache may lag.
Seeing the correct asset in Git, passing HACS validation, or receiving a
placeholder does **not** certify the pre-install Marketplace image is live.
Keep testing until the tile on a clean (not installed) listing renders the
actual icon, or collect HTTP status and timestamp for an upstream issue.

## Rebuild installed-brand PNGs

The Python builder rasterizes the **single, transparent S5 icon master**. The previous white product blended into its pale blue backing at Home Assistant's actual integration-tile size. The updated artwork follows [Xiaomi's official S5 body reference](https://home.mi.com/views/deviceReset.html?locale=en&model=bwj.diffuser.s5): rounded off-white case, a black circular display with thin champagne rim, and the small bottom-right button. Its silhouette now fills most of the 256px canvas, with a clear grey contour suitable for both light and dark HA themes.

The light-blue tile background, fake mist, Bluetooth badge and the full-width decorative banner are **not part of the shipped brand**. Home Assistant's official [brand-image specification](https://contributors.home-assistant.io/core/integrations/brands/) prefers transparency and explicitly permits omitting the wide `logo.png` when the icon is the correct mark; the square icon is then reused automatically.

```bash
python -m pip install pillow cairosvg
python tools/build_brand_assets.py
```

Outputs: `icon.png` (256 × 256) and `icon@2x.png` (512 × 512), both RGBA with transparent corners. `logo.png` and `logo@2x.png` are intentionally **deleted** to avoid an empty panoramic presentation. The vector master, generated PNGs and deletion must be committed together. CI checks pixels and transparency. The README hero and four-stage connection graphic are unchanged.

## Design and publishing rules

- Keep artwork captions in English; translate explanatory prose in Markdown instead.
- Do not put *experimental*, model certification claims or invented control states inside illustrations.
- Do not portray the conceptual graphics as a tested device screenshot or a firmware diagram.
- Keep images static and self-contained; no remote image resources, scripts or tracking.
- Do not claim a HACS catalog thumbnail is guaranteed by local brand files. Marketplace catalog branding is handled separately.
- Before publication, inspect the rendered README at GitHub's normal desktop and narrow/mobile widths and run the checks in [Testing](TESTING.md).

Only S5 has a user-reported physical success. The pictured BLE process explains intended onboarding; it does not prove other SO profiles work on hardware.

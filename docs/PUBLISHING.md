# Publishing and Marketplace visibility

This repository publishes one Home Assistant custom integration: `so_diffuser_ble`.

## First public release

- **Version:** `1.0.0` in `manifest.json` and the `v1.0.0` GitHub release tag.
- **Release notes:** [RELEASE_NOTES.md](RELEASE_NOTES.md).
- **Brand assets:** [BRANDING.md](BRANDING.md) documents the 256/512 px icon and logo images.
- **Release state:** `v1.0.0` is already published. Its one-time release workflow was retired after use; existing tags and releases are preserved. Future releases require a reviewed maintainer-authored source/branding commit and a matching GitHub Release. CI checks must never commit changes back to `main`.
- **Catalog index:** a separate contribution to `hacs/default` is required for all users to discover this integration without adding its URL manually. The catalog review can take time.

## Important licensing gate

The repository currently has **no owner-selected OSI-approved license**. HACS validation reports this as a failure; adding a decorative `LICENSE` file without an authorized licensing decision would not solve the legal issue. Catalog submission should not be attempted before the owner explicitly selects a license and HACS validation passes.

The Home Assistant local icon becomes available after installation. An icon displayed **before installation** is resolved by the catalog's brand service, not by a README picture or a GitHub profile image. A public release plus `brand/icon.png` is necessary preparation but does not force an image into a custom-repository dialog.

## Quality and testing

- The code preserves the `so_diffuser_ble` package and existing entity unique-ID suffixes; only the localized on/off switch label changes; the power entity ID and command remain unchanged.
- Tested model: S5 has user-reported real operation. All other listed SO models remain experimental and require real hardware acceptance.
- Run `python -m pytest -q`, Hassfest and HACS validation before publishing functional changes. Repository licensing remains an explicit owner decision.
- Do not publish device tokens, MAC addresses, private HCI captures or OAuth callbacks.

Sources: [Marketplace integration publishing](https://contributors.home-assistant.io/marketplace/guides/integrations/), [Releases](https://contributors.home-assistant.io/marketplace/guides/releases/), [Catalog review](https://contributors.home-assistant.io/marketplace/guides/catalog/).

# Publishing and Marketplace visibility

This repository publishes one Home Assistant custom integration: `so_diffuser_ble`.

## First public release

- **Version:** `1.0.0` in `manifest.json` and the `v1.0.0` GitHub release tag.
- **Release notes:** [RELEASE_NOTES.md](RELEASE_NOTES.md).
- **Brand assets:** [BRANDING.md](BRANDING.md) documents the 256/512 px icon and logo images.
- **Release state:** `v1.0.0` is already published. Its one-time release workflow was retired after use; existing tags and releases are preserved. Future releases require a reviewed maintainer-authored source/branding commit and a matching GitHub Release. CI checks must never commit changes back to `main`.
- **Catalog index:** a separate contribution to `hacs/default` is required for all users to discover this integration without adding its URL manually. The catalog review can take time.

## License and catalog validation

This project is distributed under the [MIT License](../LICENSE), approved by the repository owner (copyright 2026 Joka-kun). GitHub Topics now include `home-assistant`, `hacs`, `bluetooth`, `xiaomi` and `diffuser`. Run HACS validation after merging to verify the current repository metadata. A passing validation does not automatically add a custom repository to the public catalog; catalog submission and review are separate steps.

The Home Assistant local icon becomes available after installation. An icon displayed **before installation** is resolved by the catalog's brand service, not by a README picture or a GitHub profile image. A public release plus `brand/icon.png` is necessary preparation but does not force an image into a custom-repository dialog.

## Quality and testing

- The code preserves the `so_diffuser_ble` package and existing entity unique-ID suffixes; only the localized on/off switch label changes; the power entity ID and command remain unchanged.
- Tested model: S5 has user-reported real operation. All other listed SO models remain experimental and require real hardware acceptance.
- Run `python -m pytest -q`, Hassfest and HACS validation before publishing functional changes. The root [MIT license](../LICENSE) must remain present.
- Do not publish device tokens, MAC addresses, private HCI captures or OAuth callbacks.

Sources: [Marketplace integration publishing](https://contributors.home-assistant.io/marketplace/guides/integrations/), [Releases](https://contributors.home-assistant.io/marketplace/guides/releases/), [Catalog review](https://contributors.home-assistant.io/marketplace/guides/catalog/).

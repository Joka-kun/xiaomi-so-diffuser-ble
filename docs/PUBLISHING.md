# Publishing and Marketplace visibility

This repository publishes one Home Assistant custom integration: `so_diffuser_ble`.

## Published release and source state

- **Published v1.0.5:** [GitHub Release](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.5) points to tested main commit `14a1fbe6f7f98c158f2cc39c7ed0140fc455ef30`. Manifest, pyproject and Xiaomi OAuth User-Agent all report `1.0.5`. Both required main Tests and Validate passed. The prior v1.0.4 remains available for rollback; no earlier tag was moved.
- **Release notes:** [RELEASE_NOTES.md](RELEASE_NOTES.md) describe the release without provisional wording.
- **Brand assets:** [BRANDING.md](BRANDING.md) documents the 256/512 px icon and logo images.
- **Release state:** [v1.0.1](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.1) was published on 2026-11-07 from commit `523e6fb51bbce0b36445df7607fe711fe8c7dd61`. The [publication workflow](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/runs/42412328738) successfully ran Python tests, Hassfest and HACS validation before creating the tag and release. Its temporary workflow file is now removed. No CI job pushed source commits to `main`.
- **Release provenance:** the old `v1.0.0` snapshot predates the MIT license; the new immutable `v1.0.1` tag includes MIT licensing and the latest source fixes. Neither tag should be moved. Catalog admission and physical hardware verification are independent tasks.
- **Catalog index:** [hacs/default#13656](https://github.com/hacs/default/pull/13656) was approved and merged on 2026-11-09. The official HACS search is now the primary installation method; indexing may take several hours. The repository URL remains a fallback.

## Historical source / release mismatch — resolved 2026-11-07

The existing `v1.0.0` GitHub Release resolves to `22071bacebecf0aeb076d3bc7e21de476481c394`, while validated `main` after PR #15 is `c6f7a140345996f1963e3963a5cc0f808f2ad841` (15 commits later). The release snapshot **does not contain** the current root MIT `LICENSE`, later token-store robustness fix or current GitHub artwork. HACS release selection is independent of successful `main` Actions checks.

For the **next feature or maintenance release after v1.0.5**:

1. Perform the [physical S5 acceptance plan](AUDIT_2026-11-07.md#physical-s5-release-gate) and document the evidence; mark other models experimental.
2. Create a **new** version (higher than `1.0.4`) and synchronize `custom_components/so_diffuser_ble/manifest.json`, `pyproject.toml`, documentation, and source user-agent version. Update version-specific tests.
3. Verify the candidate commit contains `LICENSE`, all intended `brand/` assets, the current token-store fix and matching release notes.
4. Require successful Python, Hassfest and HACS Actions on that *exact* commit. Record the commit SHA and corresponding `vX.Y.Z` tag.
5. Create a new GitHub Release without modifying existing tags. Check a clean Home Assistant installation and an upgrade before promoting it.
6. Separately verify catalog inclusion and Marketplace branding after publication. A passing HACS validation alone does not submit or publish catalog metadata.

GitHub branch protection is currently disabled for `main`; enabling required checks and pull-request reviews needs repository administration permissions and is a separate maintenance task.

## License and catalog validation

This project is distributed under the [MIT License](../LICENSE), approved by the repository owner (copyright 2026 Joka-kun). GitHub Topics now include `home-assistant`, `hacs`, `bluetooth`, `xiaomi` and `diffuser`. HACS validation on the current `main` passes all 10 checks; rerun it for future changes. A passing validation does not automatically add a custom repository to the public catalog; catalog submission and review are separate steps.

The Home Assistant local icon becomes available after installation. An icon displayed **before installation** is resolved by the catalog's brand service, not by a README picture or a GitHub profile image. A public release plus `brand/icon.png` is necessary preparation but does not force an image into a custom-repository dialog.

## Quality and testing

- The code preserves the `so_diffuser_ble` package and existing entity unique-ID suffixes; only the localized on/off switch label changes; the power entity ID and command remain unchanged.
- Tested model: S5 has user-reported real operation. All other listed SO models remain experimental and require real hardware acceptance.
- Run `python -m pytest -q`, Hassfest and HACS validation before publishing functional changes. The root [MIT license](../LICENSE) must remain present.
- Do not publish device tokens, MAC addresses, private HCI captures or OAuth callbacks.

Sources: [Marketplace integration publishing](https://contributors.home-assistant.io/marketplace/guides/integrations/), [Releases](https://contributors.home-assistant.io/marketplace/guides/releases/), [Catalog review](https://contributors.home-assistant.io/marketplace/guides/catalog/).

## v1.0.1 publication evidence

- GitHub Release: [v1.0.1](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.1) (normal release, not a draft or pre-release).
- Tag and release source commit: `523e6fb51bbce0b36445df7607fe711fe8c7dd61`.
- Independent one-time pipeline: [Publish v1.0.1](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/runs/42412328738) — all validation and publication jobs passed.
- Temporary write-enabled release workflow removed in PR #18 after publication. The permanent Tests and Validate workflows are still read-only.
- S5 regression for this exact release, migration from the old domain, and local control after WAN disconnection remain **unverified** in this audit. No claim of full hardware validation is made.

Protect `main` through GitHub Settings → Rules → Rulesets; the currently connected GitHub tooling has no action for administrative repository rules.

## v1.0.2 Home Assistant artwork release

- GitHub Release: [v1.0.2](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.2), published 2026-11-07.
- Immutable release commit: `99bde0ffa98243466a8d9f204aff23882c33f43e`.
- Release verification: [one-time v1.0.2 workflow](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/runs/42414802991) completed with Python tests, Hassfest, HACS and publication successful.
- The branch-only image generator and one-time release publisher were removed from `main` after publishing. The permanent Tests and Validate workflows have read-only permissions.
- Four shipped PNGs are built from the paired text-free S5 SVG masters; the GitHub hero and user-supplied connection diagram were not replaced.
- Users can update the custom HACS integration to `v1.0.2`. Home Assistant may retain cached icons until refreshing the browser; Marketplace pre-install thumbnails require separate catalog indexing.
- Physical S5 acceptance and other SO hardware remain separate, unverified gates.

## v1.0.3 Home Assistant branding — published

The new `brand-icon.svg` and `brand-logo.svg` intentionally contain **no Bluetooth glyph, cyan/violet neon effects, text or copied device UI**. Their four Home Assistant PNG outputs match the canonical vector sources and retain all required sizes. Only the local installed-integration branding changes, not the README hero or installation diagram.

The artwork-branch-only generator created the PNGs; its temporary workflow was removed before the release. [Published v1.0.3](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.3) points to immutable source commit `e747a81efa2d55a137d800164aab29c5c95b6b59`. [One-time release CI](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/runs/42416763907) passed Python, Hassfest and HACS before publishing. The release workflow has now been removed; permanent workflows remain read-only. Previous tags and public README artwork were not modified.


## v1.0.4 transparent S5 icon release

The official [Xiaomi S5 reference](https://home.mi.com/views/deviceReset.html?locale=en&model=bwj.diffuser.s5) establishes the physical silhouette. The official [Home Assistant brands reference](https://contributors.home-assistant.io/core/integrations/brands/) prefers transparency and confirms that the icon is reused when no wide logo exists. The previous bright-blue backing and panoramic banner are deliberately removed. The new SVG, both PNGs and absence of logos are tested.

[v1.0.4](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.4) was published after [the release pipeline](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/runs/42419020857) successfully ran Python, Hassfest, HACS, and GitHub Release creation on commit `8866f11bb3b6a139d9dadea57284e26ca846d9f8`. The one-time publisher is retired here, leaving permanent read-only CI. Historical releases remain unchanged.

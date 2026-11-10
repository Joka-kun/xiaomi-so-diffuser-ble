# Project status

**As of 2026-11-10 · GitHub Release v1.0.7 published · Interactive SO Bluetooth search · Official Marketplace catalog merged**

This page distinguishes **source implementation**, **field reports** and **hardware verification**. Previous detailed implementation notes are preserved in [the dated snapshot](history/STATUS_2026-11-07.md).

| Area | Confirmed | Not yet confirmed |
| --- | --- | --- |
| S5 OAuth / BLE | User-reported working S5 control in the live HA canary with the BLE recovery code and a brief observed disconnect/reconnect; the same recovery code ships in v1.0.5. | 8–24-hour sleep/reconnect, BLE radio silence, and WAN-off control have not been independently certified |
| Other SO models | Published MIoT IDs and capability descriptions; experimental onboarding implemented | Their real advertisement names, GATT authentication and physical commands |
| Device detection | v1.0.7 adds a 10-second discovery step and manual fallback using HA's Bluetooth manager; exact-name models appear first and generic candidates are labelled unverified | Live scanning/adapter availability and detection of unnamed S5 devices on the user's hardware |
| Token security | Temporary Xiaomi OAuth code, per-address 12-byte GATT token saved only after S5-derived BLE proof; v1.0.6 uses `so_diffuser_ble_tokens.json` with no legacy fallback | Hardware acceptance of cloud-token retrieval on relatives and physical re-provisioning after the breaking change |
| UI features | User-reported native RGB effect working on S5; separate On/Off and Backlight controls; optional HA color palettes, diagnostics and model-gated controls | 1.0.0 software palette acceptance on real S5, effects on other models and disconnect handling on hardware |
| Migration | Single generic-domain folder; new universal address-keyed store intentionally does not read old S5 files | Fresh Xiaomi sign-in, existing HA entity-ID migration and multi-device physical acceptance after this change |
| Publication | [v1.0.7](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.7) published from tested commit `0b46537bf22d0192efd23c1ed96fc2c39da2ef9b` after Tests/Validate passed. Marketplace icon was observed after deleting stale negative-cache files in the user's HA installation | Actual BLE search on device, physical multi-device setup, long-idle reconnect and non-S5 models still pending |

## Repository audit — 2026-11-07

[GitHub Release v1.0.1](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.1) is published at commit `523e6fb51bbce0b36445df7607fe711fe8c7dd61`. It includes later safeguards, MIT licensing and the updated graphics. Physical S5 regression and Marketplace catalog review are still independent acceptance tasks.

The [post-PR #15 audit](AUDIT_2026-11-07.md#repository-wide-verification-after-pr-15-2026-11-07) verified **132 Python tests plus 64 subtests**, Hassfest and HACS validation on `main`. README layouts, the two public illustrations and the original installation SVG remain intact. **Resolved publishing gap:** the newer source is now available in immutable `v1.0.1`, including its MIT license and token-store fix. The previous `v1.0.0` tag is preserved for history. **Still open:** S5 hardware acceptance, catalog inclusion, and GitHub branch protection. See [publishing](PUBLISHING.md#v101-publication-evidence).

## 1.0.4 S5 icon visibility

The candidate replaces the light-blue tile with a tight transparent S5 product silhouette. The true black circular display, bronze rim and recessed button stay visible at small HA integration-card sizes. The unnecessary horizontal logo is removed in favor of Home Assistant's documented square-icon fallback. These are artwork changes only, not new BLE or hardware validation. [GitHub Release v1.0.4](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.4) includes the new transparent icon for HACS installations.

## 1.0.3 Home Assistant styling

The integration icon and wide device logo now use the same white S5 illustration on a calm, light-blue background, closer to the native Home Assistant aesthetic. The old Bluetooth symbol, dark neon styling and violet decoration were removed. The README artwork is unchanged. [GitHub Release v1.0.3](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.3) is published from tested commit `e747a81`; HACS users can update to the refreshed installed branding. This is **not** new physical hardware verification.

## 1.0.2 Home Assistant branding

The square integration icon and wide device header logo now share the same text-free S5 silhouette, cyan/violet color language and editable SVG masters. This is **visual-only**: no new BLE commands or compatibility claims. The README hero and four-stage connection artwork remain unchanged. [GitHub Release v1.0.2](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.2) now includes these images; HACS users can update to this published version. A browser refresh may be needed to clear the icon cache.

## Language and experiment update

The public GitHub page now offers **English, Russian, German, Spanish, French and Simplified Chinese**. These are README translations; the HA configuration dialog itself currently has English/Russian translations only.

Every registered SO MIoT schema has an idle-time `3.4 = 0` value. On non-S5 models 1.0.0 exposes it as an **experimental zero-pause** switch after explicit model opt-in and authenticated BLE setup. Actual firmware duty cycles remain unconfirmed. A new always-readable Bluetooth connection diagnostic distinguishes disconnected hardware from merely unavailable command entities. Raw native schedule writes remain disabled.

## 1.0.0 setup improvements

The main switch is now labelled **On/Off** (Russian: a short on/off label) to clarify its behavior and sort above Backlight in the stock Russian device view. The LED backlight remains independent. Existing entity unique IDs are preserved. The built-in Automatic Gradient RGB cycle is now advertised through `LightEntityFeature.EFFECT`; this exposes an already mapped device mode, not a new unverified protocol command.

The Xiaomi OAuth setup dialog gives the safe browser-hostname replacement procedure when `homeassistant.local` cannot resolve. BLE errors distinguish failed connection establishment from failed authenticated GATT login and advise users to turn on the diffuser, close Mi Home and temporarily disable their phone's Bluetooth. Physical testing of the updated wizard is still pending.

## 1.0.0 lighting update

Two additional effects, **Color Cycle (HA)** and **Sunset (HA)**, are implemented as opt-in slow software palettes through the existing validated RGB color property. They use a single managed task with one color write every eight seconds; switching effect, turning the LED off, losing BLE or unloading the entity stops the task. They do **not** add undocumented vendor mode values and are **not** independent of HA. Native Automatic Gradient continues running on the device. The user has confirmed that the native effect works on S5; the new software palettes remain untested on physical hardware.

## What discovery means

1. **Bluetooth candidate:** the advertisement has an *exact known SO name*. This is not cryptographic identity, and other genuine SO devices may advertise different names.
2. **Cloud model selected:** the user picks an exact allowlisted Xiaomi MIoT model. A detected model mismatch is rejected.
3. **Physical proof:** selected device GATT token authenticates to the BLE device. Only then is the secret stored locally.
4. **Usable control:** physical power/spray must be observed on the real model. This final level is not automatically inferred from a successful login.

S5 has a user-reported earlier success. **No non-S5 device has passed level 4** in this project.

## Breaking domain change

Former domain `so_s5` was model-specific. Public release 1.0.0 uses `so_diffuser_ble` to support a family while maintaining one HACS integration per repository. Home Assistant does **not** automatically reassign existing config entries to a different domain; you must use the [migration guide](MIGRATION.md). New development source uses `/config/.storage/so_diffuser_ble_tokens.json`; old S5 token files are no longer read, copied or removed. Re-provision through Xiaomi for each diffuser after updating to a release containing this change.

## Outstanding hardware and release checks

- Validate domain migration on a real S5 installation (including HA entity IDs and automation effects).
- Verify restart + WAN-off BLE operation.
- Confirm emitted BLE names and physical controls on one relative before declaring it supported.
- MIT License and repository topics are in place; all 10 HACS validation checks pass on `main`. Catalog admission is separate from CI success.
- Keep secrets, MACs and one-time OAuth callbacks out of public issues and docs.

[Quick start](../README.md) · [Russian guide](../README_RU.md) · [Model matrix](COMPATIBILITY.md) · [Roadmap](../ROADMAP.md) · [Historical protocol evidence](research/HCI_CAPTURE_ANALYSIS.md)

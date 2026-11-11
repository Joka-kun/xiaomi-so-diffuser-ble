# Roadmap

**Updated 2026-11-11 · Current release: v1.0.8 (`so_diffuser_ble`) · Hardware acceptance pending**

The old S5-only roadmap is preserved as [dated research history](docs/history/ROADMAP_2026-11-07.md). This page lists **current** decisions, validated outcomes and outstanding work only.

## Delivered in source

- [x] Official HACS/Marketplace catalog entry accepted in [hacs/default#13656](https://github.com/hacs/default/pull/13656); public [v1.0.8](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.8) explicitly requests a 10-second active HA Bluetooth sweep during the nearby-device setup search. Real-hardware acceptance remains separate.

- [x] One-time Xiaomi OAuth, exact cloud model selection, 12-byte device GATT token with real BLE challenge, private local credential store.
- [x] SO S5 local power, spray timing, RGB lighting, battery, charging and S5-only LongSpray. First real S5 OAuth setup and basic operation **reported by user on the earlier build**.
- [x] Explicit profiles for S5 and eight related SO models; experimental opt-in, exact-name BLE discovery and per-model entities.
- [x] New generic integration domain `so_diffuser_ble`, package path and single HACS-managed integration directory.
- [x] Since v1.0.6, use only `/config/.storage/so_diffuser_ble_tokens.json` for runtime BLE credentials. Legacy `/config/.storage/so_s5_ble_tokens.json` and `/config/so_s5_token` remain **untouched but are not read**; devices relying on them require fresh Xiaomi OAuth provisioning. See [migration guide](docs/MIGRATION.md).
- [x] Guard against duplicate old `so_s5` config entries for the same BLE address. Model ID in the Xiaomi account must match a known advertisement's model.
- [x] Reorganize the GitHub README/docs into illustrated instructions in six languages (EN/RU/DE/ES/FR/ZH-CN); archive historical S5-specific implementation reports.
- [x] Normalize English technical prose, add dedicated Russian installation/compatibility/migration guides, separate the Russian HCI source from its canonical English translation, and enforce language boundaries in CI.
- [x] Retain model-specific protocol evidence and tests without publishing secrets.
- [x] Expose experimental zero-pause mode from published `3.4 = 0` across the SO catalog, explicitly labeled on unverified models.
- [x] Add BLE connection diagnostic that stays available when disconnected.
- [x] Expose S5's native Automatic Gradient color cycle in HA and simplify BLE/OAuth setup guidance. Distinguish failed BLE links from failed GATT authentication.
- [x] Rename the primary control **On/Off** so it alphabetically precedes the Backlight control in Russian HA. Preserve the same unique ID and command mapping.
- [x] Add two optional, slow HA-driven RGB palettes on the existing fixed-property channel, with single-task lifetime, cancellation, and disconnect handling.

## S5 icon contrast correction — 2026-11-08

- [x] Compare against the official Xiaomi S5 front reference; preserve its circular black display and lower-right button.
- [x] Remove the low-contrast pastel-blue tile, fake mist and obsolete wide banner; use transparent HA icon fallback.
- [x] Rebuild the icon at 256/512px and enforce alpha/pixel-regression tests.
- [x] Published [v1.0.4](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.4) from CI-reviewed commit `8866f11`; previous tags preserved.

## Home Assistant branding — 2026-11-08

- [x] Replace cyberpunk/BT-decorated icon and wide logo with a shared SO S5 light-blue HA-style identity.
- [x] Rasterize four standard PNG dimensions from self-contained SVGs and check image equality in CI.
- [x] Publish reviewed [v1.0.3](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.3) from verified commit `e747a81`, retaining v1.0.2 and earlier tags.

## Source audit and release readiness (2026-11-07)

- [x] Audit local BLE session, fixed-property command/read-back, OAuth state checks, entity lifecycle, private token storage and CI workflows against source files and tests.
- [x] Prevent a non-regular FIFO token store from blocking HA executor threads. Add an offline regression test for both read and save paths.
- [x] Align the Xiaomi OAuth request's public User-Agent version with `manifest.json`, verified by a synthetic HTTP test.
- [x] Record evidence, severity and reproducible acceptance checks in [the technical audit](docs/AUDIT_2026-11-07.md).
- [ ] Verify this source revision on physical S5 before expanding the field-confirmed compatibility claims.
- [x] Publish reviewed [v1.0.1](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.1) from tested license-bearing commit `523e6fb`, retaining immutable `v1.0.0`.
- [x] Published [v1.0.2](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases/tag/v1.0.2) from verified commit `99bde0f` with new icon/logo. Previous tags unchanged; Marketplace catalog visibility is separate.
- [ ] Independently verify reported BLE state transitions, reconnect/restart, WAN-off and the two HA-driven lighting effects; no synthetic test substitutes for hardware.

## Must verify before inviting general upgrades

- [ ] Test a clean v1.0.8 installation and upgrades from pre-v1.0.6 with the [migration guide](docs/MIGRATION.md). Confirm the old files remain untouched, fresh Xiaomi OAuth provisions a device-bound token in the new store, and no retired `so_s5` entry competes for the same BLE address.
- [ ] Check Home Assistant's entity registry after re-adding S5 and restore any changed entity IDs or automations. **A domain change is not an automatic config-entry migration.**
- [ ] Test S5 OFF/ON, spray timing, RGB, restart/reconnection and operation after WAN is disconnected.
- [ ] Re-test the Russian/English Xiaomi wizard and manual OAuth callback in Home Assistant UI; verify custom HA address redirect and the new BLE error guidance.
- [x] A user has reported that the native light effect works on physical S5; its exact long-term behavior has not been measured.
- [ ] Verify the two new HA palette effects on physical S5, including interruption, reconnect, battery behavior and UI display order.
- [ ] Verify the actual Bluetooth advertised names/MiBeacon PIDs of relatives S2/S6/S7/S8/S9/S1 Pro/S1/S19; the current exact-name matcher may not recognize all real devices.
- [ ] For each non-S5, independently confirm BLE handshake, encrypted notifications and physical power on/off. A shared MIoT schema **does not** establish working transport.
- [ ] On S1 Pro, verify whether temperature property 3.10 arrives and which unit the firmware uses; otherwise hide it.
- [ ] Measure actual `3.4=0` spray duty cycle **per model**, and preserve the last positive pause through restart without unverified writes.
- [ ] Expand Home Assistant integration-dialog and entity translations beyond the existing EN/RU; the GitHub guides are already in six languages.
- [x] Adopt the owner-approved [MIT License](LICENSE). Verify HACS publication checks after the licensing commit.
- [ ] Before any future functional release, complete S5 regression and migration testing. Keep unverified non-S5 models clearly marked experimental.

## Product policy

- **Auto discovery:** exact known BLE names only; no generic Xiaomi FE95 wildcard. Some genuine SO models may need manual Bluetooth address entry.
- **Provisioning:** exact cloud model + live device-token BLE proof. Non-S5 requires explicit experimental consent.
- **Runtime:** local Bluetooth control, not recurring Xiaomi Cloud API calls. No account passwords/refresh tokens stored.
- **Entities:** expose published capabilities with explicit warnings for experimental zero-pause modes. Identical MIoT property numbers are not proof of identical physical firmware behaviour. Native device schedules remain off; use HA automations.
- **Compatibility:** S5 = field-reported functional earlier source; S2/S6/S7/S8/S9/S1 Pro/S1/S19 = experimental.

## Project references

[Installation](docs/INSTALLATION.md) · [Migration](docs/MIGRATION.md) · [Compatibility](docs/COMPATIBILITY.md) · [Technical investigation](docs/MULTI_MODEL_ARCHITECTURE.md) · [Security](SECURITY.md) · [CI](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions)

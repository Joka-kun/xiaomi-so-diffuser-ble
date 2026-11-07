# Roadmap

**Updated 2026-11-07 · Current source: 1.0.0 (`so_diffuser_ble`) · Not a stable release**

The old S5-only roadmap is preserved as [dated research history](docs/history/ROADMAP_2026-11-07.md). This page lists **current** decisions, validated outcomes and outstanding work only.

## Delivered in source

- [x] One-time Xiaomi OAuth, exact cloud model selection, 12-byte device GATT token with real BLE challenge, private local credential store.
- [x] SO S5 local power, spray timing, RGB lighting, battery, charging and S5-only LongSpray. First real S5 OAuth setup and basic operation **reported by user on the earlier build**.
- [x] Explicit profiles for S5 and eight related SO models; experimental opt-in, exact-name BLE discovery and per-model entities.
- [x] New generic integration domain `so_diffuser_ble`, package path and single HACS-managed integration directory.
- [x] Legacy-token read compatibility: `/config/.storage/so_s5_ble_tokens.json` and `/config/so_s5_token` remain **untouched**.
- [x] Guard against duplicate old `so_s5` config entries for the same BLE address. Model ID in the Xiaomi account must match a known advertisement's model.
- [x] Reorganize the GitHub README/docs into illustrated instructions in six languages (EN/RU/DE/ES/FR/ZH-CN); archive historical S5-specific implementation reports.
- [x] Normalize English technical prose, add dedicated Russian installation/compatibility/migration guides, separate the Russian HCI source from its canonical English translation, and enforce language boundaries in CI.
- [x] Retain model-specific protocol evidence and tests without publishing secrets.
- [x] Expose experimental zero-pause mode from published `3.4 = 0` across the SO catalog, explicitly labeled on unverified models.
- [x] Add BLE connection diagnostic that stays available when disconnected.
- [x] Expose S5's native Automatic Gradient color cycle in HA and simplify BLE/OAuth setup guidance. Distinguish failed BLE links from failed GATT authentication.
- [x] Rename the primary control **On/Off** so it alphabetically precedes the Backlight control in Russian HA. Preserve the same unique ID and command mapping.
- [x] Add two optional, slow HA-driven RGB palettes on the existing fixed-property channel, with single-task lifetime, cancellation, and disconnect handling.

## Source audit and release readiness (2026-11-07)

- [x] Audit local BLE session, fixed-property command/read-back, OAuth state checks, entity lifecycle, private token storage and CI workflows against source files and tests.
- [x] Prevent a non-regular FIFO token store from blocking HA executor threads. Add an offline regression test for both read and save paths.
- [x] Align the Xiaomi OAuth request's public User-Agent version with `manifest.json`, verified by a synthetic HTTP test.
- [x] Record evidence, severity and reproducible acceptance checks in [the technical audit](docs/AUDIT_2026-11-07.md).
- [ ] Verify this source revision on physical S5 before expanding the field-confirmed compatibility claims.
- [ ] Publish a **new release from a licensed and tested commit** before expecting HACS to distribute post-`v1.0.0` fixes. Do not move or overwrite the published `v1.0.0` tag.
- [ ] Independently verify reported BLE state transitions, reconnect/restart, WAN-off and the two HA-driven lighting effects; no synthetic test substitutes for hardware.

## Must verify before inviting general upgrades

- [ ] Install the **1.0.0 general-domain release** on a test Home Assistant instance, following the [migration guide](docs/MIGRATION.md). Confirm old tokens are reused without loss and the old entry does not compete for BLE.
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

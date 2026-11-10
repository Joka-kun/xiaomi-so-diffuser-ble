# Changelog

## 1.0.6 — universal per-device BLE credentials (2026-11-10)

- Replace the S5-named credential file with the universal `/config/.storage/so_diffuser_ble_tokens.json` store, keyed by exact Bluetooth MAC address.
- Remove all runtime fallback to `so_s5_token` and `so_s5_ble_tokens.json`. Previously configured diffusers using those files will need fresh Xiaomi OAuth provisioning; the old files are not read or deleted.
- Preserve independent Home Assistant config entries and BLE sessions for multiple SO diffusers; loading or replacing one token does not authorize or change any other device.
- Clarify onboarding copy, document the deliberate credential incompatibility, and add unit/integration regressions. No new model's BLE protocol is certified.

## 1.0.5 — BLE reconnect responsiveness and official HACS listing (2026-11-09)

- Ship the already-merged, synthetic-tested S5 BLE session recovery changes: power commands wait for a reconnect through the **single existing GATT connection owner**, rather than failing immediately after link loss.
- Wake reconnect attempts through exact-address Bluetooth advertisements and a bounded retry timer. Keep the diagnostic BLE-connection indicator truthful; never automatically replay an uncertain MIoT write.
- Preserve existing device tokens, entities, spray/RGB behavior and experimental warnings for non-S5 models.
- Update English and Russian installation instructions for official HACS catalog inclusion.
- Scope of validation: Home Assistant live canary successfully installed; S5 real operation and a brief BLE reconnect have been user-observed, but **8–24-hour radio-sleep recovery and WAN-off tests are not physically certified**.


## 1.0.4 — Transparent, readable S5 icon (2026-11-08)

- Replaced the pale blue tile with a large, close-cropped S5 product mark on transparent PNG, following Xiaomi's official white body/black circular face design.
- Improved its outline, warm rim and button readability in small Home Assistant integration cards on light and dark themes.
- Removed the unrelated panoramic logo; Home Assistant uses the icon as the logo fallback.
- Regenerated and tested the 256/512 px brand assets without changing BLE, OAuth, devices or README artwork.


## 1.0.3 — Home Assistant soft-blue branding (2026-11-08)

- Replace the square integration icon and wide device-header logo with restrained, light-blue HA-style illustrations of the same SO S5.
- Remove the Bluetooth emblem, violet/cyberpunk treatment and decorative text from the installed branding.
- Rebuild the four standard PNG assets deterministically from new SVG masters; README and setup artwork remain untouched.
- No changes to BLE protocol, OAuth, device entities or supported model claims.


## 1.0.2 — Unified SO S5 visual identity (2026-11-08)

- Replace the integration icon and wide device-page logo with one coherent, text-free SO S5 visual identity.
- Canonical assets are standalone SVG vector masters; Home Assistant PNGs are deterministic generated outputs tested at both standard and 2× sizes.
- Preserve the README hero and the original four-step installation artwork.
- No BLE protocol, authentication, configuration domain, entity or hardware-support changes.


## 1.0.1 — Maintenance update (2026-11-07)

- Safeguard BLE token-store reads against blocking non-regular files; retain strict permissions and atomic writes.
- Synchronize the Xiaomi OAuth request User-Agent with the integration version.
- Ship MIT license, updated S5 artwork, four-step onboarding graphic and six-language documentation in the release snapshot.
- Refresh GitHub Actions and add privacy-aware issue and pull-request templates.
- No new BLE command mappings or new confirmed device models. S5 full hardware regression and all non-S5 tests remain pending.


## 1.0.0 — Xiaomi SO Diffuser BLE (2026-11-07)

- Integration domain `so_diffuser_ble`; the earlier `so_s5` development package is no longer shipped.
- S5 local BLE controls: **On/Off**, spray timing, continuous/zero-pause mode, RGB Backlight, native Automatic Gradient and opt-in HA color palettes.
- One-time Xiaomi OAuth setup and physical GATT token verification; ordinary control is local.
- Exact SO discovery and explicitly experimental profiles for S1, S1 Pro, S2, S6, S7, S8, S9 and S19.
- Home Assistant brand assets, integration packaging and multilingual setup documentation.
- Automated regression suite and Hassfest verification. Actual hardware support for other models is **not yet proven**.

**Migration:** Old `so_s5` Home Assistant entries do not automatically become `so_diffuser_ble`. See [the migration guide](docs/MIGRATION.md) and preserve private tokens.

Historical development changes are archived at [docs/history/CHANGELOG_pre_public.md](docs/history/CHANGELOG_pre_public.md). For current limitations and next steps, see [STATUS](docs/STATUS.md) and [ROADMAP](ROADMAP.md).

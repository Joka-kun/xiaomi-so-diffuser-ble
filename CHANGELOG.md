# Changelog

## 1.0.0 — First public release (2026-11-07)

- First public GitHub release for **Xiaomi SO Diffuser BLE**. The integration domain is `so_diffuser_ble`; the previous `so_s5` development package is no longer shipped.
- S5 local BLE controls: **On/Off**, spray timing, continuous/zero-pause mode, RGB Backlight, native Automatic Gradient and opt-in HA color palettes.
- One-time Xiaomi OAuth setup and physical GATT token verification; ordinary control is local.
- Exact SO discovery and explicitly experimental profiles for S1, S1 Pro, S2, S6, S7, S8, S9 and S19.
- New coherent graphics, refreshed 256/512px brand icons and logos, and six maintained GitHub guides (EN, RU, DE, ES, FR, ZH-CN).
- Automated regression suite and Hassfest verification. Actual hardware support for other models is **not yet proven**.

**Migration:** Old `so_s5` Home Assistant entries do not automatically become `so_diffuser_ble`. See [the migration guide](docs/MIGRATION.md) and preserve private tokens.

Historical development changes are archived at [docs/history/CHANGELOG_pre_public.md](docs/history/CHANGELOG_pre_public.md). For current limitations and next steps, see [STATUS](docs/STATUS.md) and [ROADMAP](ROADMAP.md).

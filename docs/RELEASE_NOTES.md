# Xiaomi SO Diffuser BLE — v1.0.6

Universal per-device BLE credential storage, independent setup for multiple SO diffusers, and refreshed Marketplace release metadata.

## What changed

- **Universal token store:** Home Assistant now uses only `/config/.storage/so_diffuser_ble_tokens.json`, with separate 12-byte GATT tokens keyed by each diffuser's Bluetooth address.
- **Multiple diffusers:** Add the integration once per physical BLE address. Each device gets its own HA config entry, connection coordinator and token. Replacing one token cannot authorize another device.
- **No global S5 fallback:** The former `/config/so_s5_token` and `/config/.storage/so_s5_ble_tokens.json` are no longer read or imported. A missing credential fails closed rather than silently applying a token from another diffuser.
- **Updated setup and documentation:** Existing saved-token selection refers to this diffuser's own token; English and Russian docs explain the intentional breaking change and reauthorization flow.
- **Marketplace branding:** The published release contains `custom_components/so_diffuser_ble/brand/icon.png` (256×256) and `icon@2x.png` (512×512). Marketplace pre-install icons are indexed separately by the Home Assistant brands service and may take time to refresh.

## Important: breaking change on upgrade

**Existing installations that rely on either old S5 token file must sign in to Xiaomi again for each physical diffuser.** The integration does not read, copy, rename or delete old secrets, and it will not use a token belonging to a different Bluetooth address.

Before upgrading an existing installation, create a full Home Assistant backup and record any affected entity IDs and automations. After updating, use **Settings → Devices & services → Xiaomi SO Diffuser BLE → Reconfigure → Sign in with Xiaomi**, choose the exact physical device, and complete its BLE authentication. On a clean install, add each diffuser separately from **Settings → Devices & services → Add integration → Xiaomi SO Diffuser BLE**.

This release does **not** perform automatic config-entry domain migration from `so_s5`. See [migration guidance](MIGRATION.md).

## Evidence and limitations

Automated unit and integration tests cover address-keyed tokens, independent two-device coordinator lifecycles, strict private file permissions, refusal to read old files, and prevention of cross-device fallback. GitHub Tests, HACS and Hassfest checks must pass for the published commit. **Synthetic tests are not a substitute for physical acceptance.**

The **SO S5** has user-reported functioning controls and a brief BLE reconnect. Other SO models remain experimental; their cryptographic BLE login and physical control are not certified. Recovery after **8–24 hours** of radio silence and local operation with WAN disconnected are not independently certified. Actual simultaneous connection capacity depends on the Bluetooth adapter or proxy.

## Install

In **Settings → Marketplace** (formerly HACS), search for **Xiaomi SO Diffuser BLE** and install **v1.0.6**. On existing systems review the breaking change above before updating. Normal commands use local Bluetooth after successful one-time Xiaomi OAuth provisioning.

Independent community integration, not affiliated with Xiaomi or Home Assistant.

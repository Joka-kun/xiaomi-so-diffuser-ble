# Universal SO diffuser credentials: breaking change

The public integration uses one Home Assistant domain, `so_diffuser_ble`, for all supported SO/BWJ diffuser models. Each physical diffuser has a separate Home Assistant config entry and a device-specific Bluetooth token.

## New storage (no automatic migration)

The **only runtime token store** is `/config/.storage/so_diffuser_ble_tokens.json`. Its keys are normalized Bluetooth addresses; the file is written atomically with owner-only permissions (0600). A token is never used for a different address.

The former `/config/.storage/so_s5_ble_tokens.json` and `/config/so_s5_token` files are **not read, imported, renamed, overwritten or deleted**. An installation that relied on either one must sign in to Xiaomi again for each diffuser to provision its new address-bound token. A missing new token is a setup error, **not** permission to reuse another device's token.

This is an intentional loss of legacy credential compatibility. It is not a way to transfer credentials from one diffuser to another. Never copy token values to a public issue or log.

## Existing Home Assistant installations

1. Create a full **Backups** snapshot in Home Assistant. Record entity IDs and automations before altering a config entry.
2. If an entry still uses the retired `so_s5` domain, remove that entry using **Settings → Devices & services**, then install the `so_diffuser_ble` integration. The new domain is not automatically migrated by Home Assistant.
3. If an entry already uses `so_diffuser_ble`, use **Reconfigure → Sign in with Xiaomi** to obtain a fresh device-specific token. If it is unavailable, check that the device is powered on and connectable over BLE.
4. Repeat the setup for each physical diffuser, selecting its exact Xiaomi model and Bluetooth address. A new config entry is required for every additional diffuser.
5. Verify on/off operation on each device, restart Home Assistant, and check that every device reconnects independently. Restore entity IDs or automation references through the Home Assistant UI when necessary.

**Never edit `core.config_entries` or entity-registry JSON manually.** Never run old `so_s5` and new `so_diffuser_ble` entries against the same Bluetooth address. Existing old token files remain untouched for a possible rollback, but are not supported for new authentication.

## Multi-device behavior

Two S5 diffusers, or different models, can coexist when they have different BLE addresses and independent tokens. The configuration flow deduplicates entries by address. The coordinator opens a separate BLE session for each entry, subject to Bluetooth adapter/proxy connection capacity.

Only the S5 transport is currently field-reported working. Other listed SO models are experimental and need explicit opt-in and a successful live GATT authentication before their token is saved. Xiaomi Cloud listing alone is not evidence of compatibility.

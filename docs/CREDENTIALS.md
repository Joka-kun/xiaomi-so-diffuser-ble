# Per-device BLE credentials

## One universal store for multiple SO diffusers

The integration reads and writes **only** `/config/.storage/so_diffuser_ble_tokens.json`. Its internal `version: 1` record holds a `devices` mapping from normalized BLE MAC address to that device's 12-byte (24 hexadecimal character) GATT Standard Auth token.

Each diffuser receives its **own credential**. A missing address entry causes a `token_missing` error; the code never silently reuses another device's token. The private file is atomically replaced with permissions 0600. Raw device tokens are not stored in Home Assistant config entries or public logs.

The obsolete `/config/.storage/so_s5_ble_tokens.json` and `/config/so_s5_token` are **not read or automatically imported**. Existing installations relying on these files need fresh Xiaomi sign-in for each device. See [breaking-change instructions](MIGRATION.md).

## Add a diffuser

1. In **Settings → Marketplace** (formerly HACS), install **Xiaomi SO Diffuser BLE**.
2. Open **Settings → Devices & services → Add integration** and choose the exact physical diffuser or enter its Bluetooth address.
3. Select **Sign in with Xiaomi**, choose the account region and the **same physical device** from the account list.
4. The integration retrieves that device's 12-byte token and proves it against the selected BLE address using a real GATT authentication. Only a successful proof permits saving the token.
5. Verify the diffuser's physical power control. Repeat **Add integration** for each additional diffuser: every entry uses a distinct BLE address and token.

To reuse a token already saved in the **new universal store** for an S5, the setup wizard offers **Use this diffuser's saved token** and repeats the live GATT proof. Experimental non-S5 models require Xiaomi sign-in and explicit opt-in rather than this shortcut.

## Important limitations and security

- **S5** has field-reported successful control. The other eight model profiles remain experimental, even if Xiaomi Cloud lists the device.
- The BLE GATT token is **not** the Xiaomi OAuth access/refresh token, a Xiaomi account password or `BLE_DATA.beaconkey`.
- If the physical address or cloud model does not match the selected device, provisioning must fail without storing the token.
- Bluetooth proxies must support active connections. Actual connection concurrency depends on the adapter/proxy; no fixed supported-device count has been proven.
- Never paste tokens, private callback URLs or complete Xiaomi device exports into public tickets.
- `tools/import_xiaomi_token.py` is a standalone historical extractor helper; its output is **not** used as an integration credential source. Normal onboarding uses the built-in verified Xiaomi OAuth flow.

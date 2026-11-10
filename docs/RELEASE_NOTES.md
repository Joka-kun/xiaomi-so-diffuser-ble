# Xiaomi SO Diffuser BLE — v1.0.7

An explicit Bluetooth search and retry flow for pairing SO/BWJ diffusers through Home Assistant.

## What changed

- **Search nearby devices (10 seconds):** setup offers Bluetooth search even if no diffuser with a known advertisement name was previously seen. A progress step listens for new advertisements through Home Assistant's existing Bluetooth adapters and ESPHome Bluetooth proxies.
- **Review nearby candidates:** choose a discovered device from the results. Exact known SO names appear first; unrecognized or unnamed connectable devices are marked **unverified** rather than silently hidden.
- **Retry or manual entry:** run the scan again, or enter the device's Bluetooth MAC address manually. A search failure returns to the picker with a useful message rather than aborting setup.
- **No relaxation of authentication:** Xiaomi OAuth must identify the exact physical model. A live BLE GATT token proof still binds credentials to that address; experimental models still require opt-in. No other nearby BLE device is automatically trusted.
- **Previous v1.0.6 storage preserved:** every configured diffuser keeps its own token in `/config/.storage/so_diffuser_ble_tokens.json`. This release does not introduce a credential or entity migration.

## How to use

1. Install/update **Xiaomi SO Diffuser BLE v1.0.7** through **Settings → Marketplace** (formerly HACS), and restart Home Assistant if prompted.
2. Open **Settings → Devices & services → Add integration → Xiaomi SO Diffuser BLE**.
3. Choose **Search nearby devices (10 seconds)**, then select your diffuser. You can retry or use **Enter Bluetooth address manually**.
4. Log in to Xiaomi to retrieve the selected physical device's BLE token; verify that the diffuser physically responds to On/Off before automations.

## Troubleshooting and limitations

This is an advertisement listener inside the Home Assistant Bluetooth manager, **not a second BLE scanner**. An actively scanning, connectable Bluetooth adapter or ESPHome Bluetooth proxy must be present and within radio range. Turn on the diffuser and, if the phone is holding its BLE link, close Mi Home or temporarily disable phone Bluetooth.

Selecting an unrecognized Bluetooth device does not establish SO compatibility. Cryptographic GATT authentication and verified cloud model selection are mandatory. Only S5 physical control is currently field-reported working; the other model profiles remain experimental. Long-idle (8–24 hour) reconnect and offline WAN testing are not fully certified.

The new flow has synthetic test coverage for zero matches, fresh advertisements, unknown candidates, scanner errors, bounded results and callback cleanup. Real hardware search is a separate acceptance test. For details see [English installation guide](INSTALLATION.md) or [Russian guide](ru/INSTALLATION.md).

Independent community project, not affiliated with Xiaomi or Home Assistant.

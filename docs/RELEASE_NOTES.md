# Xiaomi SO Diffuser BLE — v1.0.8

Fix the **Search nearby devices (10 seconds)** action on Home Assistant Bluetooth scanners configured in **Auto** mode.

## Fix

In v1.0.7, the setup wizard subscribed to nearby-device advertisements for 10 seconds but did not request an *active* scan window from Home Assistant. Auto-mode adapters usually scan passively, which can omit the scan-response details needed to identify a diffuser.

The wizard now calls Home Assistant's supported `bluetooth.async_request_active_scan(hass, 10)` while its advertisement callback is registered. The HA Bluetooth manager schedules the active sweep across eligible adapters and Bluetooth proxies, without running a competing Bleak scanner. The picker still supports retries and manual MAC entry.

## Safety and compatibility

- All existing device entries and the per-address token store `/config/.storage/so_diffuser_ble_tokens.json` remain unchanged; no migration is needed from v1.0.7.
- Unrecognized Bluetooth devices remain **unverified** until Xiaomi Cloud identifies the exact model and live GATT authentication proves the token matches its physical address.
- Only S5 has user-reported working controls; other SO/BWJ models remain explicitly experimental.
- The change fixes an onboarding issue. It does **not** change the host's Realtek/BlueZ USB firmware, recovery watchdog or scan hardware. Physical field validation of this active sweep is pending.
- S5 long-idle (8–24 hours) reconnection and multi-device hardware behavior have not been independently certified.

## Installation and test

1. Update to **v1.0.8** in **Home Assistant → Settings → Marketplace**, then restart Home Assistant if prompted.
2. Go to **Settings → Devices & services → Add integration → Xiaomi SO Diffuser BLE**.
3. Choose **Search nearby devices (10 seconds)**. The UI requests an active Bluetooth scan through the Home Assistant manager. Select a discovered SO/BWJ model or retry.
4. If nothing appears, check the host's Bluetooth adapter, signal strength, Bluetooth proxy and scanning mode. A scan cannot repair a USB/firmware fault. You may still enter the diffuser's Bluetooth address manually.
5. Complete Xiaomi sign-in, select the matching physical device and verify real On/Off control before automations.

## Verification

The regression test calls the actual discovery-flow method with a mock Home Assistant Bluetooth manager and asserts that an active scan request occurs for exactly 10 seconds. Tests, Hassfest and HACS validation are release gates. Physical BLE reception is an independent acceptance test.

Further details: [English installation instructions](INSTALLATION.md) and [Russian installation instructions](ru/INSTALLATION.md).

Independent community integration. Not affiliated with Xiaomi or Home Assistant.

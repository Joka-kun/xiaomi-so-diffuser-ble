# Architecture

> **Historical snapshot (2026-11-07).** User-interface labels below are rendered in English for readability; the original Russian spellings are preserved in the repository's Git history. This is not current installation guidance.


## SO-family expansion in 0.4.0

The public HA domain deliberately stays `so_s5` to preserve existing device identities and automations. Model identity and feature availability are separated from the S5-derived GATT transport:

- `models.py` contains an explicit nine-model catalog. S5 is field-confirmed; eight relatives are **experimental**. Unknown MIoT model IDs do not pass.
- `config_flow.py` enumerates exact cloud candidate models and requires an additional confirmation page for non-S5 entries, followed by a physical **GATT Standard Auth** proof. It cannot be bypassed by editing a friendly device name. New config entries store `miot_model` and `experimental_protocol` but no secrets.
- Runtime `__init__.py` enforces the model/opt-in gate again. Legacy S5 entries without the new keys default to S5. The old S5-token fallback remains intact.
- `coordinator.py`, `light.py`, `sensor.py`, and `switch.py` gate property interpretation and entities by profile. S1 and S19 do not get RGB controls, S1 Pro may expose signed temperature 3.10, and unverified relatives do **not** expose vendor LongSpray.
- Exact SO model strings are offered as additional Bluetooth matchers; unknown advertisement formats require manual Bluetooth address entry. No broad FE95 scanning is enabled.
- The current `S5ReadOnlyClient`/`S5ControlClient` implementation remains the **S5-derived transport**. A second model may fail its handshake or differ in light/spray semantics. This 0.4.0 source only offers an opt-in *trial* path, **not** eight hardware-verified devices.

The long-term extension point is a separate authenticated transport implementation per protocol family; an unrelated Xiaomi Mesh or Aroma-Link diffuser cannot safely inherit SO Standard Auth merely because it appears in a Xiaomi account. See [multi-model research and acceptance matrix](docs/MULTI_MODEL_ARCHITECTURE.md).



## Provisioning vs runtime

```text
ONE-TIME SETUP (or Reconfigure)
HA Bluetooth discovery → select S5 BLE address
             │
             ▼
Open Xiaomi OAuth authorization URL in browser
             │  short-lived authorization code → HA local webhook
             ▼
Xiaomi OAuth token → cloud device-list API (exact model bwj.diffuser.s5)
             │  select DID + 24-hex token, without guessing by name
             ▼
Fresh BLE Standard Auth / HMAC proof against chosen device
             │  only on success
             ▼
/config/.storage/so_s5_ble_tokens.json (mode 0600)
             │  per-BLE-address token
             │  fallback: legacy /config/so_s5_token
             ▼
NORMAL RUNTIME
HA config entry (address only) → HA Bluetooth → Bleak → FE95 GATT
             │
             ▼
S5 Standard Auth → HKDF/HMAC → AES-CCM
             │
             ▼
MIoT Spec-v2 fixed-property controls
             ├── Diffuser power on/off (2.1004)
             ├── spray duration (3.3)
             ├── pause / continuous spraying (3.4)
             ├── light (3.8)
             └── RGB colour (3.9)
```

## Boundaries

- OAuth2 and cloud device listing happen **only during explicit setup or reconfigure**. No password, service cookie, refresh token or cloud device list is persisted; the OAuth access token exists only for the setup task.
- The browser callback is a state-validated, one-time, expiring Home Assistant webhook. A successful server reply **does not** prove the GATT credential; the following BLE login does.
- The production client accepts only named fixed-property writes. It has no generic MIoT write method, pairing/reset API or schedule/timer setters.
- Runtime credentials are loaded by BLE address, with old global token file as fallback; no secrets in config entries or normal logs.
- The offline capture decoder is diagnostic, not part of the runtime connection path. `3.5` and `3.7` remain in historical capture analysis only.
- The official Xiaomi OAuth interface can change; this implementation still needs a real account + actual device test before a stable release.

## Connection lifecycle

Home Assistant resolves the configured address through its Bluetooth manager. `bleak_retry_connector` establishes the GATT connection with pairing disabled. The client authenticates, starts one notification reader, and only then permits the fixed property command path. Every property write waits for both a successful SetPropertyResp and an exact matching PropertyChanged read-back. Disconnects clear live entity values and trigger bounded reconnect backoff.

## Light state model

The vendor UI encodes the master light enable state in bit 7 of property `3.8`. The lower seven bits carry the steady brightness level or the Automatic Gradient mode marker. HA brightness is translated between its 0–255 scale and the vendor's 1–100 scale. OFF clears bit 7 while retaining the lower bits, matching the Mi Home UI; the next ON restores the previous mode/level. Automatic Gradient mode does not report a fake 100% brightness value.

## Pause state model

Property `3.4` accepts 3–30 and the app's special `LongSpray=0` value. HA presents the ordinary pause as a 3–30 minute slider and the special mode as a separate switch. The last non-zero pause is retained in memory for the duration of the integration runtime; if it is unknown when LongSpray is disabled, the switch restores the documented minimum value of 3.

# Testing and acceptance

## Automated tests

Install the test dependencies and run:

```bash
python -m pip install -r requirements_test.txt
python -m pytest -q
```

The suite covers:

- Token-file format and permissions.
- BLE address validation.
- Fixed MIoT property encodings and command allowlist.
- AES-CCM vectors, login derivation and MIoT Spec-v2 parsing.
- Fake-GATT command response/read-back handling, including stale `PropertyChanged` before correct read-back and required timeout on never-matching read-back.
- Light brightness conversion, master OFF, mode restore, RGB and Automatic Gradient mode restrictions.
- Pause slider and continuous spraying state transitions (the original `LongSpray` protocol value).
- Removal of only retired timer/schedule entities.
- Credential importer selection, permissions, overwrite protection and secret omission.
- Built-in OAuth2 authorization URL, region selection, cloud device-list parsing and pagination using fake HTTPS responses.
- Rejected wrong models / wrong-length tokens, one-time callback with CSRF state check and replay rejection.
- Private per-address credential storage, 0600 permissions, legacy fallback, malformed-file handling and in-place reconfigure flow structure.
- Explicit SO model catalog: known model filtering, unknown-model fail-closed behaviour, experimental opt-in, light/no-light capabilities, S1 Pro temperature, and shared experimental zero-pause controls plus BLE connection diagnostics.

## Experimental SO-family hardware acceptance (not yet performed)

The current 1.0.0 source lists **known SO-family model candidates** from Xiaomi Cloud and requires affirmative experimental consent for every non-S5 model. No non-S5 model has passed physical BLE testing. The expected outcomes for each candidate are:

1. Cloud inventory returns an *exact catalog model*, not just a friendly name. Unknown Xiaomi models, malformed/incorrect-size tokens and generic FE95 advertisements are rejected.
2. Before a non-S5 token is written, the wizard requires deliberate opt-in. Declining cannot create an integration entry or write any BLE properties.
3. The selected BLE device must complete the S5-derived GATT Standard Auth proof. If incompatible, the setup must fail **without creating a nonworking device entry** or deleting existing S5 tokens.
4. Only after a valid authenticated session, verify model-specific read-back and physical power off/on under supervision. Repeat with spray timing and RGB only if the model publishes it.
5. S1/S19 must expose **no light**. S1 Pro can show a read-only temperature sensor only if it sends the signed `3.10` notification. Non-S5 models may expose an **experimental zero-pause switch** after opt-in and GATT proof; actual physical mode semantics must be checked before using automations. The diagnostic BLE connection entity should show OFF rather than Unavailable during a disconnect.
6. After reboot and offline WAN tests, record exact model ID, firmware, masked BLE transport errors, property observations and **physical** result. Do not publish tokens, OAuth URLs, raw HCI or device identifiers.

See [architecture and per-model criteria](MULTI_MODEL_ARCHITECTURE.md).

## Supplied-capture verification

During preparation, the supplied original HCI capture was verified locally using the token from the private extractor export. The public repository contains neither file. Result:

- Both login HMAC proofs verified.
- 3/3 outgoing and 269/269 incoming AES-CCM frames authenticated.
- 3 outgoing MIoT SetProperty requests parsed.
- 266 PropertyChanged and 3 SetPropertyResp messages parsed.
- All 3 SetPropertyResp transaction IDs matched their requests and all result codes were zero.
- 2,394 property values decoded.

To repeat this on a private machine, use `tools/verify_capture.py` with a private 0600 token file and the original btsnoop capture.

## Live deployment baseline (2026-11-07)

Before testing new OAuth provisioning, the operator checked the HA Docker deployment **after intentionally removing** the legacy S5 installation:

- Both expected token paths and the `so_s5` component directory were absent.
- The persisted `core.config_entries` registry had **zero** entries for domain `so_s5`.
- No repository reference was found in the inspected HACS storage files.
- Five other custom components remained installed; the unrelated built-in `xiaomi_ble` records were not removed.
- The HA Python runtime after restart, historical alternative domains, and orphaned entity/device registry entries were **not** independently checked.

This validates **clean disk/entry state only**, not new-software deployment or live Xiaomi authentication. Use a **fresh Add integration** after installing the new code (not Reconfigure). If OAuth fails, the old token is no longer present for fallback. Do not record an OAuth provisioning success until a real account and S5 have passed the criteria below.

The privacy-sanitized field report and follow-up checklist are in [historical deployment audit](history/DEPLOYMENT_AUDIT_2026-11-07.md).

## First user-reported live acceptance — 2026-11-07

**Confirmed by operator report:** fresh installation after removing both token files; SO S5 discovered; Xiaomi browser OAuth authentication and setup completed, and the diffuser works. An unreachable `homeassistant.local:8123` final callback destination was resolved by replacing **only the browser hostname** with the HA server's LAN host, without modifying the callback path, `code` or `state`. **Not yet verified:** the private token's existence/permissions after reboot, WAN-off control, precise LongSpray duty cycle or other models. The manual pasted-redirect form was not the successful field-tested path.

See [spray-mode experiment](SPRAY_MODES_AND_COMPATIBILITY.md) and [historical deployment audit](history/DEPLOYMENT_AUDIT_2026-11-07.md). The user-shared OAuth URL contains one-time credentials and must never be copied into tests, fixtures or public documentation.

## New token-provisioning hardware acceptance (remaining tests after first reported OAuth success)

1. **Browser OAuth:** open Add integration or Reconfigure on an existing entry; select region and complete Xiaomi login. Confirm the local `homeassistant.local:8123` callback is reachable and returns to the HA setup dialog. A timeout/cancel must leave previous credentials intact.
2. **Cloud identity:** the list must include only exact-model SO S5 with a valid 12-byte token. Verify the selected cloud DID using a distinct name where possible; do not match by name alone.
3. **Cryptographic binding:** try one correct and one deliberately wrong *synthetic* token against a test S5; correct succeeds, wrong fails, and the wrong token is never persisted. Never upload real credentials to an issue.
4. **Persistence:** inspect privately that `/config/.storage/so_s5_ble_tokens.json` is present with owner-only permissions and no OAuth access/refresh token. Do **not** publish file contents.
5. **Migration:** use **Reconfigure** on an existing entry with `/config/so_s5_token`. Confirm same entity unique IDs, successful HA reload and a BLE reconnect with the saved per-device token. Preserve the legacy file until after post-restart testing.
6. **Offline test:** disable WAN after setup (not the LAN/BLE network). Verify local power, pause and continuous mode still work and no new Xiaomi OAuth request occurs on reconnection.
7. **Multiple devices:** acquire separate S5 credentials for two different BLE addresses and prove no token cross-use or lost update after reconnect.
8. **Failure conditions:** simulate unauthorized cloud API, wrong account/region, missing token, phone BLE takeover, stale callback and API pagination loops. Errors must be redacted and non-destructive.

No actual Xiaomi credentials or Bluetooth HCI capture have been used to validate this new flow in GitHub Actions.

## Hardware acceptance still required

Automated tests and captured protocol frames do not prove the diffuser's physical behaviour. Before describing a future release as hardware-stable, test:

1. Spray duration at 3, a middle value and 30 seconds.
2. Pause at 3, a middle value and 30 minutes.
3. Continuous spraying `3.4 = 0` on/off and restoration of the previous pause. User confirmed continuous spray physically on 2026-11-07; repeated off/on and cross-firmware acceptance remain open.
4. Light brightness at low, mid and max values.
5. Full OFF from steady and Automatic Gradient modes; confirm no visible backlight.
6. ON after OFF; confirm the previous brightness/mode is restored.
7. RGB changes in steady mode and rejection while Automatic Gradient is active.
8. Phone app connection takeover and HA reconnect.
9. Operation with WAN disconnected after credentials have already been installed.

Also re-test the user-reported `switch/turn_off` false error after updating: the device may briefly report its old state before the final state; no false mismatch error should occur, while true no-read-back failures must still time out. Record the device firmware, exact values, HA state/read-back and independent physical observation for each test.

## S5 BLE command recovery (review branch, 2026-11-08)

See [source audit and field acceptance](BLE_RECOVERY_AUDIT_2026-11-08.md).
The offline `tests/test_ble_command_recovery.py` suite exercises the actual
S5Coordinator class with fake BLE and Home Assistant objects: a power command
waking a missing session, concurrent commands using one connection, an
ambiguous write not being replayed, advertisement-triggered recovery, orderly
unload and rejecting unknown commands. These are synthetic transport tests,
not confirmation of the S5's 24-hour standby radio behaviour.

Command-only power availability is intentional: when disconnected its value
may be unknown, but users can still request a new connection. Failed physical
reachability or authentication must cause an explicit command error.

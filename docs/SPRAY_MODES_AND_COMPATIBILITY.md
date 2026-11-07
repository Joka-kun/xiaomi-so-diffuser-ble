# Spray modes, related SO models and scheduling policy

**Research date:** 2026-11-07  
**Physical spray-mode target:** `bwj.diffuser.s5` / SO Smart Aroma Diffuser S5. **SO 0.6.0 expands the experimental zero-pause control to the known family**; the comparison is now maintained in [MULTI_MODEL_ARCHITECTURE.md](MULTI_MODEL_ARCHITECTURE.md).  
**Evidence levels:** `MIoT spec` (published metadata), `source code` (this repository), `original app UI` (previous reverse-engineering notes), `field report` (operator's S5), and `untested`. These are deliberately distinct.

## 1. Controls: explain exactly what is switched

| Entity | Meaning | S5 property | Behaviour |
| --- | --- | --- | --- |
| **Power** | Device on/off, **not** an action-only button | `2.1004` | `0 = Off`, `1 = On`; stateful HA `switch` |
| **Spray duration** | Duration of an emission pulse | `3.3` | 3–30 seconds in the Mi Home UI |
| **Spray pause** | Time between emissions in periodic mode | `3.4` | 3–30 minutes in the original S5 UI |
| **Continuous mode (S5)** | Enables the vendor's special `LongSpray` mode | `3.4` | Write `0`; disabling restores the last known positive pause, or defaults to 3 minutes |
| **Lighting** | RGB colour, brightness and gradient | `3.8`, `3.9` | Independently controlled from device power |

The public MIoT property schema itself admits `3.4 = 0…30`; the **meaning of zero** comes from the **original app's `LongSpray` option**, mapped by the existing repository reverse-engineering notes. The user previously observed practically continuous emission at value zero. That does **not** establish that the atomizer motor literally remains powered without a break or for how long it does so.

**Important:** `3.3` and `3.4` are distinct. The integration's `S5LongSpraySwitch.async_turn_on()` only writes `idle_time = 0`; it does **not** change the configured pulse duration `fragrance_out_time`. The device firmware alone determines the mechanical on/off pattern when `idle_time = 0`.

### Why continuous spraying may appear irregular

The following are **hypotheses, not verified S5 firmware internals**:

1. The firmware may interpret zero as a special mode rather than as a mathematically zero-length idle interval. It might run uninterrupted, rapidly repeat short bursts, apply protection pauses or use another vendor-defined pattern.
2. `fragrance_out_time` (`3.3`) retains its previous value; a user may observe different output patterns after changing duration, even when `3.4` stays at zero.
3. Home Assistant maps all `3.4 = 0` to a binary continuous-mode switch, while the regular pause slider intentionally shows no ordinary numeric value. This is a UI representation, **not** a spray sensor.
4. The prior pause is remembered **only in RAM** by the current coordinator. If HA is restarted when `3.4=0`, turning off continuous mode may use the fallback **3 minutes**, even if the previously selected pause was longer. This is a **known limitation worth addressing**, not evidence of a BLE command failure.
5. Power toggles, phone Mi Home BLE takeover, reconnects, scheduling already stored in the device, battery status and firmware-specific duty-cycle rules could also change what is observed. None was established as the cause of the operator's new report.

The current driver does not implement the atomizer's physical duty cycle in software. It sends fixed MIoT property writes and receives state notifications. It does not schedule rapid spray pulses itself.

### Reproducible, low-impact hardware acceptance experiment

**Do not run long unattended spray tests or deliberately breathe concentrated output.** Test briefly in a ventilated area, keeping people away from the outlet.

| Experiment | Input | Observe and record |
| --- | --- | --- |
| A: Ordinary interval | `3.3=3` seconds, `3.4=3` minutes, `Power=On` | Does the physical spray stop after ~3 seconds? The device property should read back positive pause. |
| B: Vendor `LongSpray` | Keep `3.3=3`; enable the S5 continuous-mode switch (`3.4=0`) | Observe only a short controlled sample (~30–60 seconds): truly uninterrupted output, short pulses with zero idle, or another pattern? |
| C: Duration interaction | While `3.4=0`, try `3.3=5` seconds | Does the actual pattern change? Avoid assuming a result in advance. |
| D: Return to normal | Disable the switch, verify `3.4` read-back | Did the last positive pause return? If previous pause was not observed in this HA runtime, current code falls back to 3 minutes. |
| E: Restart | Note the positive pause, enable `3.4=0`, restart HA, disable special mode | Does HA fall back to 3 minutes rather than the previous pause? This would confirm the current volatile-memory limitation. |
| F: Device timer influence | Compare with existing Mi Home schedule disabled/enabled *without changing undocumented MIoT timer registers from HA* | Is the apparent anomaly caused by pre-existing device-side schedule/weekday settings? |

Independent acceptance requires physical observations **plus** timestamped HA state changes (`3.3`, `3.4`, `2.1004`) and, if necessary, redacted BLE notifications. Never publish an account authorization code, device token or raw capture.

## 2. Related SO / BWJ device models — candidate matrix (historic baseline; see current registry)

Published Xiaomi MIoT schemas are remarkably similar, but our code's **exact BLE advertisement match and GATT Standard Auth protocol have only been targeted at S5**. The table below assesses **property compatibility, not confirmed runtime support**.

| Marketed model | Xiaomi model ID | Property profile compared with S5 | Our current compatibility |
| --- | --- | --- | --- |
| SO S5 | `bwj.diffuser.s5` | Reference: `2.1004` and `3.1–3.9` | **Supported target; user reports successful real OAuth-based setup; additional spray tests pending** |
| SO S2 | `bwj.diffuser.h10` | Same basic property numbers, including light/colour | **Candidate only** |
| SO S7 | `bwj.diffuser.bw11` | Same basic property numbers, including light/colour | **Candidate only** |
| SO S8 | `bwj.diffuser.s8` | Same basic property numbers, including light/colour | **Candidate only** |
| SO S9 | `bwj.diffuser.s9` | Same basic property numbers, including light/colour | **Candidate only** |
| SO S19 | `bwj.diffuser.s19` | Shared power/spray/pause/scheduling fields; no light/colour properties in the published schema | **Partial-property candidate only** |
| SO S1 | `bwj.diffuser.k09` | Shared power/spray/pause/scheduling fields; no light/colour properties in the published schema | **Partial-property candidate only** |

Do not infer support for **all** Xiaomi fragrance devices. Other vendor models (for example `xiaomi.diffuser.xw2iv`) may use Bluetooth Mesh, different security transports, different SIIDs/PIIDs and different timings, and require their own driver.

**Source 0.6.0 includes explicit experimental profiles (including SO S6 and SO S1 Pro), an opt-in setup gate, GATT token validation and a zero-pause switch for each recognized model. Actual duty cycles outside S5 have not been measured.** This is a trial mechanism, not confirmed BLE support. Before marking another model *confirmed*, obtain its actual BLE advertisement/FE95 MiBeacon product ID, exact GATT proof, notification framing and physical power control. S1/S19 omit RGB; S1 Pro adds temperature 3.10. See [full evidence table, adapter plan and test gates](MULTI_MODEL_ARCHITECTURE.md). No generic BLE scanner and no cloud-name-only credential binding are introduced.

## 3. Scheduling policy

**Decision for current integration:** keep the standard **Home Assistant Automations** workflow as the primary schedule UI, and do **not** restore the native Mi Home timer master, 12 time windows and weekday toggle entities by default.

Reasons:

- HA offers time/day schedules, conditions, scenes and notifications with one automation editor, rather than duplicating a firmware-specific timer UI.
- The original S5 scheduler uses `3.5` (a uint16 time-window mask) and `3.7` (weekday/repeat mask). A past private BLE capture verified successful writes to these properties, **not full bidirectional timing semantics, persistence or conflict resolution**.
- Re-enabling untested schedule writes could introduce device/HA double scheduling or overwrite Mi Home configurations.
- **Trade-off:** HA automations require HA to run and connect over BLE at trigger time. A validated native timer might continue operating without HA or network, which would justify a future *opt-in* hardware scheduling feature.
- A future optional device-side scheduling module should follow a capture-backed spec, check current masks read-only first, and be gated by explicit opt-in, backup/restore and hardware acceptance.

### Suggested HA automation model

Use HA time or schedule helpers to switch the diffuser's Power entity on/off at desired periods. Configure a **positive pause** and pulse duration in the diffuser itself. Do not create an HA automation that fires every few seconds as a substitute for the diffuser's own internal spray cycle.

## 4. OAuth success and token provenance, observed 2026-11-07

- Before first setup, the operator's own Docker audit showed that **neither** `/config/so_s5_token` **nor** `/config/.storage/so_s5_ble_tokens.json` existed, and there was no `so_s5` config entry.
- The operator subsequently selected the discovered S5 and completed Xiaomi sign-in via our HA OAuth flow. The browser initially could not reach `homeassistant.local:8123` for the callback. Replacing only the browser's destination host with the Home Assistant's working **LAN address**, while keeping the exact callback path and `code/state` query, completed the callback. **Never publish these one-time values.**
- The operator reported that setup and the diffuser now work. This is **field-reported live success**, stronger than the earlier mocked API tests, but is not an independent post-restart, WAN-off and multi-firmware acceptance.
- The source path is `XiaomiOAuth.exchange_code()` → `get_s5_devices()` → `async_validate_s5_token()` → `save_device_token()` → `load_device_token()`. The selected S5's `device.token`, **not** the OAuth access token, is the 12-byte key used for local BLE.
- `load_device_token()` first looks up the Bluetooth address in `.storage/so_s5_ble_tokens.json`; it reads the legacy global file only when there is no per-device entry. Because both files were absent **before** the successful new install, the original local token was **not** a viable source for this setup.
- This code path should be verified separately through a **redacted file existence/permissions check** and a post-HA-restart reconnection. Never log or publish the token or OAuth redirect.
- `homeassistant.local` is part of the OAuth `redirect_uri` used to exchange the code, so changing the OAuth parameter itself to arbitrary LAN IP may be rejected by Xiaomi. The operator's successful workaround altered **only the final browser callback destination**.

## 5. Sources

- Home Assistant developer guidance: [Naming entities](https://contributors.home-assistant.io/core/entities/naming/), [Switch entities](https://contributors.home-assistant.io/core/entities/switch/), [Home Assistant automations](https://www.home-assistant.io/docs/automation/).
- Published MIoT device schemas: [S5](https://home.miot-spec.com/spec/bwj.diffuser.s5), [S2](https://home.miot-spec.com/spec/bwj.diffuser.h10), [S7](https://home.miot-spec.com/spec/bwj.diffuser.bw11), [S8](https://home.miot-spec.com/spec/bwj.diffuser.s8), [S9](https://home.miot-spec.com/spec/bwj.diffuser.s9), [S19](https://home.miot-spec.com/spec/bwj.diffuser.s19), [S1](https://home.miot-spec.com/spec/bwj.diffuser.k09).
- This repository: `client.py`, `coordinator.py`, `switch.py`, `number.py`, `config_flow.py`, `xiaomi_oauth.py`, `token_store.py`, `docs/PROTOCOL.md`.

# SO S5 Bluetooth recovery: source audit and acceptance gate

Date: 2026-11-08. Scope: BLE connection lifecycle only.
Status: **proposed and synthetic-tested; NOT field-proven on physical S5**.
Deployment: **merged to `main` and installed as a live Home Assistant canary on 2026-11-08**. Long-idle physical S5 recovery is not verified; no versioned release published.

## User-observed failure

When an S5 is switched off for a long time, its active BLE connection disappears.
The previous S5Coordinator made a background reconnect attempt every 2–30 s,
but the regular Home Assistant entities were marked unavailable as soon as the
GATT session closed. Any power command that somehow reached the coordinator
was rejected before a fresh connection could be attempted.

This is an integration-level defect. It is **not evidence** that the physical
S5 radio remains reachable after extended standby.

## Primary sources examined

- [Our S5Coordinator](../custom_components/so_diffuser_ble/coordinator.py):
  session owner, fixed property writes, reconnect loop, GATT auth and read-back.
- [Scent Assistant device.py](https://github.com/mr-sparks/scent-assistant/blob/main/custom_components/scent_assistant/device.py):
  connect-on-demand, adapter/proxy reachability, failure cooldown, BLE lock,
  cleanup and stale GATT cache handling.
- [Scent Assistant __init__.py](https://github.com/mr-sparks/scent-assistant/blob/main/custom_components/scent_assistant/__init__.py):
  Bluetooth advertisements triggering initial-state recovery, bounded by a timer.
- [SmartAromaDiffuser protocol.py](https://github.com/menjan/SmartAromaDiffuser/blob/main/custom_components/smartaromadiffuser/protocol.py):
  configurable idle disconnect, serialized requests, stale callbacks,
  no blind replay of uncertain writes.
- [SwitchBot coordinator](https://github.com/home-assistant/core/blob/dev/homeassistant/components/switchbot/coordinator.py):
  HA's ActiveBluetoothDataUpdateCoordinator, advertisement-driven state,
  unavailable transitions.
- [XW002 Xiaomi GATT/MQTT bridge](https://github.com/clairefiorettiythzr6802-eng/xiaomi-diffuser-ble/blob/main/python/bridge.py):
  persistent BLE session and fixed-delay recovery with a different credential
  scheme; not a drop-in alternative to S5.
- [HA Bluetooth proxy stale-link report](https://github.com/home-assistant/core/issues/187087):
  reported but not confirmed as applicable to this environment.

The older, privately held S5 HCI capture authenticated a successful session.
It does not establish advertisement behaviour or radio availability after
8–24 hours with spraying turned off.

## Narrow patch in this review branch

1. Retain exactly **one** connection owner: the existing background task.
   User commands wake that task and wait up to 35 seconds for an authenticated
   session. They do not create a second BleakClient.
2. Keep the **power** switch command-capable even while its state is unknown.
   The diagnostic BLE-connection binary sensor still reports the real link
   state. Other entities keep their previous disconnected/unavailable policy.
   `available=True` for the power command is **not** a claim of physical
   radio reachability: a command still fails explicitly if S5 is unreachable.
3. Use a Home Assistant Bluetooth advertisement callback with an exact
   address matcher and ACTIVE scan mode to wake reconnection promptly. Limit
   advertisement-triggered wake events to once per 10 seconds, retain a 2–30
   second fallback timer and clear changed-advertisement history after closing
   a GATT session where the HA API supports it (static payloads may otherwise
   fail to trigger callbacks).
4. Serialize whole command lifetimes with one asyncio lock, including the
   initial wait for reconnection. Preserve S5's existing MIoT GATT token,
   authenticated read-back and property allowlist.
5. After a write with an uncertain result, abort the session and report an
   error. **Never replay the command automatically**.
6. Unsubscribe Bluetooth callbacks, cancel session tasks and wake pending
   commands when the integration is unloaded.

A successful Python test is not a physical BLE acceptance result.

## Invariants for code review

- No parallel GATT owners, even under simultaneous power commands.
- No command sent before `S5ControlClient.iter_messages()` has activated
  its authenticated read-back listener.
- A failed or ambiguous write is issued at most once.
- The sole session owner retires the broken link.
- HA shutdown does not leave outstanding command waiters indefinitely.
- Existing credentials, unique IDs, RGB, spray settings and model opt-in
  stay unchanged.
- Production HA configuration, network and peripherals are not modified.

## Field-test decision tree

Instrument the same S5 across all trials; mask BLE addresses and never
publish raw HCI/session keys/tokens.

| Independent observation | Interpretation | Next action |
| --- | --- | --- |
| BLE advertisements present, new GATT auth succeeds | Recoverable integration/session issue | Measure command latency, validate patch |
| BLE advertisements present, GATT connection fails | Adapter/proxy/other app/GATT-state issue | Compare phone access, BlueZ, proxy allocation |
| BLE advertisements absent from independent scanner | May be device radio sleep or RF range | Check power state and repeat at short range |
| Another scanner sees S5 but HA does not | HA adapter/proxy/routing issue | Diagnose scanner reachability and stale links |
| GATT auth works, property response absent | Protocol or notification issue | Do not blindly resend; capture sanitized timings |

### Physical acceptance protocol

With a stable, documented BLE receiver and independent scan observation:

1. Verify known-good ON -> OFF -> ON and save baseline command latency.
2. Keep diffuser OFF for 10 min, 1 h, 8 h and 24 h; attempt ON **without**
   touching the device. Record actual spray, advertisement visibility,
   successful BLE auth and command/read-back outcome.
3. Disconnect BLE during authentication, during notification read and
   after a property write. Ensure no duplicate physical action.
4. Restart Home Assistant; test recovery and competing Mi Home access.
5. Repeat after WAN disconnection (LAN and HA Bluetooth still active).
6. Record failures as failures, including inaccessible radio.

Release criteria: deterministic tests and GitHub checks pass **and**
physical S5 recovers without manual interaction under its actual BLE radio
behaviour. Do not merge or advertise a long-idle fix based solely on CI.

## Live Home Assistant canary installation (2026-11-08)

The coordinator, power-switch entity and Bluetooth manifest dependency change
were applied to the existing Home Assistant installation using
SHA-256-guarded one-occurrence edits and automatic per-change backups.
Only the Home Assistant container was restarted. Docker subsequently
reported the Home Assistant container as running.

**Evidence boundary:** the installation completed and Home Assistant remained
running after restart. Available Docker logs did not independently show a
fresh authenticated S5 session, successful BLE power command or physical
ON/OFF result. Neither CI nor container uptime proves the 8–24-hour
standby-radio behaviour.

The locally installed integration still declares version `1.0.4`;
no versioned GitHub release has been published. The manual canary files
could be replaced by a subsequent HACS update.

The hardware acceptance gate remains open until an actual S5 power
command has been verified physically after a lost BLE session.

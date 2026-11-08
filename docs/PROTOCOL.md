# S5 protocol notes

## Scope and evidence

The implementation targets the SO Smart Aroma Diffuser S5 (`bwj.diffuser.s5`) over its FE95 BLE GATT service. Evidence is separated into:

- **Capture-verified:** fields, HMAC proofs, AES-CCM tags and MIoT frames decoded from the supplied HCI capture.
- **Plugin-derived:** UI property mappings and value encodings extracted from the original Mi Home React Native bundle.
- **User-tested on physical hardware:** `3.4 = 0` appeared to produce continuous spraying on the user's SO S5 (reported 2026-11-07); the user subsequently described apparently irregular output. The precise pulse/duty cycle and cross-firmware behavior have **not** been measured.
- **Not yet fully hardware-accepted:** pause restoration, full spray timing range and light behaviors of the newer HA setters.

The original plugin bundle, raw HCI capture and credential values are not included in this repository.

## Authentication and encrypted data

The S5 capture shows the token-based Standard Auth sequence on FE95, followed by MIoT data-channel traffic. The 12-byte token from the Xiaomi extractor's `token` field reproduced both login HMAC-SHA256 proofs. With the derived session keys, all 272 captured AES-CCM frames authenticated:

| Direction | Frames | Result |
|---|---:|---|
| HA/app → diffuser | 3 | 3/3 authenticated and parsed |
| Diffuser → HA/app | 269 | 269/269 authenticated and parsed |
| **Total** | **272** | **272/272 authenticated** |

The 269 incoming frames comprise 266 `PropertyChanged` messages and 3 `SetPropertyResp` messages. All three response transaction IDs match their requests and all three result codes are zero. The 266 property notifications contain 2,394 property values. The three captured outgoing requests were:

| SIID / PIID | Type | Value | Meaning in the original UI |
|---|---:|---:|---|
| `3 / 5` | uint16 | `2054` | Timer schedule property; no HA control now |
| `3 / 5` | uint16 | `4095` | Timer schedule property; no HA control now |
| `3 / 7` | uint8 | `255` | Repeat/day mask; no HA control now |

This validates the token-based crypto profile for this capture. It does not prove that all device firmware revisions behave identically, that the device's physical mechanism acted, or that the entire Mi Home app is cloud-independent. The S5's post-login parcel framing differs from the referenced Yunmi kettle implementation; that driver is not reused as an S5 sender.

## Extractor token versus BLE beacon key

The Xiaomi Cloud Tokens Extractor emits the device `token` and, for supported BLE devices, a separate `BLE_DATA.beaconkey`. The S5 GATT login proof accepts the 12-byte/24-hex-character `token`. The separate beacon key is not a replacement for the GATT token and is not consumed by this integration. It was also tested as a candidate against the captured S5 login transcript and failed the HMAC proof checks.

## Property map

| Property | Type | UI-derived meaning | Current HA exposure |
|---|---|---|---|
| `2.1004` | uint8 | Work mode: 0 stopped / 1 operating; LED backlight separate | Work-mode switch |
| `3.1` | uint8 | Battery level | Diagnostic sensor |
| `3.2` | uint8 | Charging status; UI labels 0/1/2 | Diagnostic sensor |
| `3.3` | uint8 | Spray duration, UI range 3–30 seconds | Number slider |
| `3.4` | uint8 | Pause 3–30 minutes; special zero-pause mode (`LongSpray=0`), physical duty cycle unmeasured | Pause slider plus the S5 continuous-mode switch or an explicitly experimental zero-pause switch on relatives |
| `3.5` | uint16 | Timer time-window mask | Not exposed; no setter |
| `3.6` | uint32 | Unix time path in the plugin; not used by this integration | Not exposed |
| `3.7` | uint8 | Weekday/timer mask | Not exposed; no setter |
| `3.8` | uint8 | Light state/brightness/Automatic Gradient bit field | HA light |
| `3.9` | uint32 | RGB colour value | HA light RGB |

The unit labels for `3.3` and `3.4` come from the original app UI. The cached MIoT schema does not declare those units. The user observed continuous-looking spray at `3.4 = 0` but later reported an unusual pattern. This establishes an empirical operating mode, not uninterrupted atomizer motor activity. The 3–30 timing ranges and firmware variants are not yet fully measured.

## Light property `3.8`

The original UI labels this effect **Automatic Gradient**; the vendor bundle uses internal identifiers containing `BreathingLight`. The original UI uses:

- Bit 7 (`0x80`) as the master light enable bit.
- Low seven bits for the selected steady brightness (1–100).
- Low-seven-bit values above 100 as the Automatic Gradient mode marker.
- `238` (`0xEE`) as the Automatic Gradient mode ON value.
- `228` (`0xE4`) as the Automatic Gradient mode OFF/revert value. This still has bit 7 set and is **not** the master light OFF state.
- The master light OFF action clears bit 7: `current_value & 0x7F`. For example, `238 → 110` and `228 → 100`. The low bits retain the selected mode/level so it can be restored on ON.

**HA effect exposure:** the light entity now declares `LightEntityFeature.EFFECT`, so the existing Automatic Gradient effect appears in Home Assistant's light effect selector. During the hardware-driven color cycle, its color mode is reported as ON/OFF rather than a manually adjustable RGB color. No additional BLE commands or color-loop scheduler are introduced.

**Optional HA-driven palettes (1.0.0):** The device's only established autonomous color-cycle mode remains `3.8=238`. Two additional user-selected HA effects operate in steady-light mode, using the previously mapped `3.9` RGB command at intervals of eight seconds. They use no new firmware mode values and stop on HA entity unload, LED off or BLE disconnection. A user reports the native gradient works; the new software effects still require hardware acceptance. The two light modes are independent of the diffuser's primary on/off switch.

HA brightness is mapped from 0–255 to the device's 1–100 scale. HA brightness 0 is treated as OFF. The light entity returns no brightness value in Automatic Gradient mode instead of pretending the mode is 100% steady brightness. RGB writes are allowed only when the master light is on in steady mode.

The source code and synthetic tests validate these encodings. Physical brightness and OFF acceptance still require a diffuser-side test.

## Pause property `3.4`

The original UI offers values 3–30 and a special `LongSpray` option represented by 0. The current HA integration exposes:

- A 3–30 minute slider for ordinary pause values.
- A separate S5 continuous-mode switch for the special value `0` (and an experimental equivalent for other SO models).
- When LongSpray is turned off, restore the last non-zero pause received or set during this HA runtime; if no previous value is known, use 3.

The app label and value mapping are confirmed from the UI bundle. **Zero is a special firmware mode**, not an HA software loop. The controller writes only `3.4=0` and leaves spray duration `3.3` unchanged. The physical cycle during this mode, including whether the motor stops between short pulses, is not yet identified. The user reports possible irregular behaviour; avoid declaring a precise duty cycle until short controlled hardware measurements are logged. When leaving this mode, the previous positive pause is remembered only in HA RAM; after restart the code may restore the default **3 minutes**. See [measured-test plan and model matrix](SPRAY_MODES_AND_COMPATIBILITY.md).

## Asynchronous read-back and stale notifications

MIoT `PropertyChanged` is not correlated with a specific write transaction ID. A stale value can arrive between a successful setter and a later notification of the requested value. The client now ignores a different value **for the pending confirmation only**, keeps the coordinator informed of notifications, and waits for the exact requested state within the existing deadline. A nonzero `SetPropertyResp`, invalid value type or read-back timeout still fails the operation. Tests cover old `3.4=0` before new pause `3.4=5`, and old power ON before OFF; hardware re-test is pending.


## Related SO models: schema similarity is not wire compatibility

Public MIoT schemas for SO S2 (`bwj.diffuser.h10`), S7 (`bwj.diffuser.bw11`), S8 (`bwj.diffuser.s8`) and S9 (`bwj.diffuser.s9`) publish matching `2.1004` power and `3.1–3.9` device fields; S1/S19 show the matching power/spray/timer fields without the same light/colour list. This is compelling evidence for **potential shared protocol semantics**, not proof that their BLE advertisements, GATT authentication, encryption or notification framing accept S5 commands.

In **0.6.0**, exact-match cloud and BLE candidate profiles now include eight additional SO models. Every non-S5 model requires affirmative experimental consent and a fresh GATT auth proof before token storage; incompatible models fail closed. Device-specific physical command semantics remain unverified. There is still no generic FE95 wildcard. Full table and architecture: [multi-model design](MULTI_MODEL_ARCHITECTURE.md); S5-specific duty-cycle analysis: [spray modes and compatibility](SPRAY_MODES_AND_COMPATIBILITY.md).

## Device-native schedule registers and HA automation policy

Historical capture confirmed successful writes to the S5's `3.5` 16-bit time-window property and `3.7` 8-bit weekday/repeat mask. Their full encoding and persistence/overlap with HA automations have **not** been verified. No runtime setter for either remains exposed. Prefer Home Assistant scheduling for now; consider native autonomous schedules as an opt-in future feature only after capture-backed verification and explicit conflict rules.

## Production write allowlist

The production `S5ControlClient` only exposes named setters for:

- `2.1004` power
- `3.3` spray duration
- `3.4` pause / LongSpray
- `3.8` light
- `3.9` RGB colour

There is no arbitrary property setter. Timer and schedule setters (`3.5`, `3.7`) were removed in 0.3.0. The offline decoder still understands historical captured values for audit purposes.

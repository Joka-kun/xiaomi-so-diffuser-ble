# Multi-model SO diffuser support: protocol evidence, implementation and test gates

**Research baseline: 0.4.0 · Current experimental build: 0.6.0**  
**Do not equate Xiaomi Cloud inventory or MIoT schema coverage with actual local BLE control.**

## Why Xiaomi Miot could see a device but not operate it

Xiaomi accounts enumerate devices through cloud metadata and MIoT-Spec describes intended properties/actions. Neither establishes a working transport for those properties. The `al-one/hass-xiaomi-miot` README explicitly recommends **cloud mode** for BLE/Zigbee and warns that **LAN mode** can leave unsupported devices unavailable. The official Xiaomi Home integration separately lists **Bluetooth devices** among unsupported categories. The built-in Home Assistant `xiaomi_ble` integration is predominantly MiBeacon advertisement/event decoding and explicitly excludes BLE Mesh.

Our S5 implementation instead authenticates a direct FE95 GATT session using the device's **12-byte Standard Auth token**, handles authenticated AES-CCM MIoT Spec-v2 property notifications, and sends bounded fixed-property commands. A second model can have the *same property IDs* and still use another GATT handshake, UUID map, encryption key size, notification framing or interpretation of light/spray modes.

### Comparison with similar community projects

| Project | Useful pattern | What cannot be copied blindly |
| --- | --- | --- |
| [al-one/hass-xiaomi-miot](https://github.com/al-one/hass-xiaomi-miot) | Account inventory and dynamic MIoT schemas, cloud vs local mode | Device visibility does not establish local BLE write support; model-wide generic MIoT setters may be unavailable |
| [XiaoMi/ha_xiaomi_home](https://github.com/XiaoMi/ha_xiaomi_home) | Official OAuth2, region-aware inventory, standards-based entity mapping | Official integration says Bluetooth products are not currently supported for control |
| [Home Assistant xiaomi_ble](https://www.home-assistant.io/integrations/xiaomi_ble) | Shared Bluetooth scanning and encrypted MiBeacon decoding | Broadcast sensors/events are not direct interactive GATT control or Mesh |
| [menjan/SmartAromaDiffuser](https://github.com/menjan/SmartAromaDiffuser) | Conservative single-family protocol support, active BLE proxy, explicit physical compatibility | A326's EE03/EE02 protocol is *not* SO's authenticated FE95 MIoT channel |
| [mr-sparks/scent-assistant](https://github.com/mr-sparks/scent-assistant) | Pluggable vendor transports and **capability-dependent** entity sets, individual hardware tests | Aroma-Link/Tuya/Scent Marketing packet formats differ entirely from SO |
| [clairefiorettiythzr6802-eng/xiaomi-diffuser-ble](https://github.com/clairefiorettiythzr6802-eng/xiaomi-diffuser-ble) | Another Mi Home fragrance appliance with direct GATT, cryptographic proof and detailed captures | The `xiaomi.diffuser.xw002` project's documented security-chip ECDH/`gatt_ltmk` handshake differs from S5's captured token-based Standard Auth; neither token nor sender can be assumed interchangeable |

**Design decision:** share model-independent HA wiring and registry, but keep **transport adapters and exact device capabilities** separately testable. A common MIoT property description is a capability candidate, not a protocol certification.

## SO family: actual published schema comparison

All model IDs below have published Xiaomi MIoT-Spec metadata and are listed as **Bluetooth** in the device catalog. None of the relatives has been validated on physical hardware with our exact S5 GATT client. Their cloud tokens must also be checked for 12-byte length.

| Product | Xiaomi MIoT model | Power | Spray secs 3.3 / idle 3.4 | Battery/charge | RGB 3.8/3.9 | Temperature 3.10 | BLE status in our project |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SO S5 | `bwj.diffuser.s5` | 2.1004 | Yes | Yes | Yes | No | **S5 GATT field-confirmed** |
| SO S6 | `bwj.diffuser.s6` | 2.1004 | Yes | Yes | Yes | No | **Experimental** |
| SO S2 | `bwj.diffuser.h10` | 2.1004 | Yes | Yes | Yes | No | **Experimental** |
| SO S7 | `bwj.diffuser.bw11` | 2.1004 | Yes | Yes | Yes | No | **Experimental** |
| SO S8 | `bwj.diffuser.s8` | 2.1004 | Yes | Yes | Yes | No | **Experimental** |
| SO S9 | `bwj.diffuser.s9` | 2.1004 | Yes | Yes | Yes | No | **Experimental** |
| SO S1 Pro | `bwj.diffuser.s1pro` | 2.1004 | Yes | Yes | Yes | **int8, -9…80 °C** | **Experimental** |
| SO S1 | `bwj.diffuser.k09` | 2.1004 | Yes | Yes | **No** | No | **Experimental** |
| SO S19 | `bwj.diffuser.s19` | 2.1004 | Yes | Yes | **No** | No | **Experimental** |

SO S1/S19 specs also contain timer/weekday and time fields despite lacking RGB. All family models include scheduling properties 3.5, 3.6 and 3.7; **their native scheduling semantics are not implemented or enabled**. For S1 Pro, the temperature property is exposed only if the device actually sends a corresponding signed int8 PropertyChanged notification. No speculative polling/temperature writes are introduced.

Sources (property data): [S5](https://home.miot-spec.com/spec/bwj.diffuser.s5), [S6](https://home.miot-spec.com/spec/bwj.diffuser.s6), [S2](https://home.miot-spec.com/spec/bwj.diffuser.h10), [S7](https://home.miot-spec.com/spec/bwj.diffuser.bw11), [S8](https://home.miot-spec.com/spec/bwj.diffuser.s8), [S9](https://home.miot-spec.com/spec/bwj.diffuser.s9), [S1 Pro](https://home.miot-spec.com/spec/bwj.diffuser.s1pro), [S1](https://home.miot-spec.com/spec/bwj.diffuser.k09), [S19](https://home.miot-spec.com/spec/bwj.diffuser.s19).

## Implementation (profiles introduced in 0.4.0, expanded in 0.6.0)

| Layer | Implementation | Safety gate |
| --- | --- | --- |
| Explicit catalog | `models.py` `ModelProfile`, `MODEL_PROFILES`, exact advertisement names | No generic `bwj.diffuser.*` or FE95 wildcard; unknown models fail closed |
| Xiaomi account enumeration | `xiaomi_oauth.py` `get_so_devices` and `extract_so_devices` | Exact allowlisted cloud model and 24-hex token only; legacy `get_s5_devices` unchanged for consumers |
| UI onboarding | `config_flow.py` chooses discovered SO address (manual fallback), then Xiaomi account device | For **non-S5 models**, separate `experimental_confirm` step requiring affirmative consent |
| BLE proof | `provisioning.py` verifies chosen token against **selected physical BLE address** with S5 Standard Auth | No credential saved when login fails. An accepted login alone does not certify every command's semantics |
| Persistent HA config | Entry retains `address` plus `miot_model`, `experimental_protocol` | Existing entries without model remain **S5**. Runtime rejects an unknown model or experimental model without persisted opt-in |
| BLE runtime | `coordinator.py` receives explicit model profile; S5 command allowlist stays bounded | No arbitrarily exposed SIID/PIID write service, native timer or reset commands |
| Device identity | `entity.py` reports the model; S5 entity unique IDs stay unchanged | Experimental models clearly marked in device name |
| Per-model entities | `light.py` only for models whose schema contains RGB; `sensor.py` optional S1 Pro temperature | S1/S19 receive no RGB; experimental profiles may set the published zero-pause value `3.4 = 0` after explicit opt-in, without claiming identical physical behaviour |

In 0.6.0 all nine registered SO profiles expose the published bounded `3.4 = 0` value. The non-S5 entity is explicitly labelled as an **experimental zero-pause** switch; a read-only BLE connectivity binary sensor also helps diagnose transport problems. Native schedules and unrestricted property writes remain disabled.

This **implements an experimental path to add family models**, not a claim that eight other diffusers have been proven to work. For all non-S5 models, the wizard demands exact model selection and explicit acceptance. If the GATT Standard Auth handshake cannot be completed, the wizard rejects provisioning rather than silently creating a nonfunctional device as Xiaomi Miot may have done in the user's earlier experience.

### How to try a relative device without sacrificing a working S5

1. Install the current development source and restart Home Assistant. Keep existing S5 entries and their token store.
2. Add **Xiaomi SO Diffuser BLE** as a *new* device. Use detected exact-model BLE name if advertised, or enter its own BLE address manually. Different models may not advertise their Xiaomi MIoT model string; fallback is expected.
3. Sign in via Xiaomi and select the corresponding SO model in the cloud list. The *source of truth* for the selected model is Xiaomi's exact `model` field, not the friendly name.
4. For a non-S5 model, read and explicitly confirm the **experimental protocol warning**. The app will attempt a cryptographic BLE login to the exact selected device address before saving anything.
5. If login fails, do **not** pair/reset/unbind the device or substitute `BLE_DATA.beaconkey`; report only the redacted error reason and model ID. The model remains **unsupported for local control** until a capture-backed transport adapter is added.
6. If login succeeds, verify available entities and test **power off/on first with direct physical observation**. Then test spray duration/normal pause; test RGB only if this model has light properties. Do not enable unattended schedules or automations yet.
7. Reboot HA and validate token reuse without Xiaomi Cloud; complete the offline WAN test only after basic functions are stable.

## Why other protocols remain separate

An unrelated Xiaomi diffuser or Aroma-Link device cannot be enabled by extending `MODEL_PROFILES` alone. A new transport needs an independently verified authenticated connection and its own command implementation, such as security-chip ECDH vs S5 token HMAC, BLE Mesh gateway, Wi-Fi `miio`, or vendor GATT. This is a **future adapter design task**. It is unsafe to infer protocol compatibility from shared Xiaomi account ownership or fragrance-diffuser categories.

## Exit criteria before moving a model from Experimental to Confirmed

- Raw manufacturer model ID and exact BLE advertisement/MiBeacon PID verified on at least one real sample.
- Known-valid device GATT token length and Standard Auth proof confirmed, or another adapter correctly implemented.
- AES-CCM notification framing and MIoT property read-back checked, including state on power cycle.
- Power OFF and ON physically verified; numeric timing ranges and units checked separately.
- Verify RGB/gradient and zero-idle physical timing **individually** before declaring any model confirmed; never assume a successful MIoT write proves identical firmware behaviour. Temperature remains read-only. Native scheduling is not exposed.
- Repeat after HA restart, Mi Home phone takeover and network disconnection; no account password or cloud OAuth token stored.
- Per-model redacted tests and capture-derived fixtures maintained in CI; secrets and device identifiers excluded.
- Only then set `confirmed_gatt=True` for that **exact model** in `models.py` and document firmware/test environment.

Current evidence: **S5 real OAuth setup works per operator report; other SO devices have not been operated with this branch**. The new model catalog and opt-in are source features pending a real-device acceptance run on relatives.

## Future architecture steps

The existing BLE client class still has S5-derived transport and property handling. Long-term improvements are to separate `SOStandardAuthTransport` from `ModelProfile`, then add different transport implementations only after real captures. Next add per-model metrics and a secret-free connection-status diagnostic, an opt-in *read-only* GATT identification probe before permitting setters, and an evidence-based capability cache per model/firmware. Do **not** grow this into an unrestricted MIoT command console.

**Domain update:** development 0.6.0 uses the general `so_diffuser_ble` domain and folder. Because existing HA config entries cannot simply change domains, user migration is deliberate and documented in [MIGRATION.md](MIGRATION.md). Existing GATT token filenames are kept readable; entity IDs and automation references must be checked during migration. HACS still sees one integration package.

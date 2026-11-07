# SO Smart Aroma Diffuser S5 — HCI capture analysis

**Research date: 2026-11-06.** This analysis is based on an operator-supplied HCI capture and corresponding Mi Home screenshots. The raw capture and credentials are **not** published. The [original Russian-language research notes](../ru/research/HCI_CAPTURE_ANALYSIS.md) remain available for traceability. Version references below describe the **historical capture/research baseline**, not the current integration release.

## Executive summary

The capture contains a successful FE95 GATT connection and an authenticated token-based login: `A4` → authentication exchange on characteristic `0019` → `CMD_LOGIN` / `CFM_LOGIN_OK`. The selected local device `token` verified both HMAC-SHA256 login proofs and all **272 AES-CCM tags** (three outgoing and 269 incoming data frames). This establishes a candidate cryptographic key schedule for these frames, **not** proof that the atomizer physically performed a command.

The Yunmi reference implementation and MiAuth use related Xiaomi token-login cryptography, but the S5 trace differs in its **missing post-login `F0` exchange** and parcel sizing. Neither project provides a drop-in S5 command sender.[25][40][41]

The separate local `ble_key` **did not** verify the observed GATT login proofs and is therefore not the verified GATT login token. The token extractor distinguishes `device["token"]` from `BLE_DATA.beaconkey`, while the pinned `xiaomi-ble 1.16.1` MiBeacon parser accepts a separate `bindkey` for encrypted advertisements.[34][35][46] These facts do **not** establish whether `ble_key` equals the MiBeacon bindkey or whether it is needed for this S5's advertising packets: advertising-to-GATT address correlation and S5 advertisement decryption were not demonstrated. No secret or derived key appears in this report.

## Capture format and integrity

| Check | Result |
| --- | --- |
| Size | 132,932 bytes |
| SHA-256 | `6c8e321a505da60e99efcb45d387056a268e9b965a598c6f3edbb02b3883ab31` |
| Header | `btsnoop\0`; version `1`; data link `1002` (HCI UART/H4) |
| Records | 2,137 complete: 111 HCI Commands, 644 HCI ACL Data, 1,382 HCI Events |
| Integrity | No truncated records, declared dropped packets or trailing bytes |
| UTC interval | 2026-11-04 00:40:57.388–00:45:29.565 (272.177 seconds) |

This is a **host-side HCI snoop**, not an over-the-air RF capture. It exposes HCI/GATT ATT traffic but not radio retransmissions, nor does it prove that a particular advertising report belongs to the connected peer.

## Connection, services and GATT characteristics

One successful LE Connection Complete event occurred at `00:40:58.952 UTC`, with the host in the central role. The connection handle is intentionally omitted. No disconnect event appears before the capture ends; subsequent state is unknown.

Discovered services: `0x1800`, `0x1801`, `0xFE95`; `0x180F` was absent. ATT discovery yielded these **session-specific value handles**, not permanent characteristic addresses:

| Short UUID | Value handle | Advertised properties |
| --- | ---: | --- |
| `0004` | `0010` | Read |
| `0005` | `0012` | Read, notify |
| `0010` | `0015` | Write without response, notify |
| `0019` | `0018` | Write without response, notify |
| `0017` | `001B` | Write, notify, extended properties |
| `0018` | `001E` | Write without response, notify, extended properties |
| `001A` | `0021` | Write without response, notify |
| `001B` | `0024` | Write without response, notify |
| `001C` | `0027` | Write without response, notify |

These UUIDs and properties agree with the read-only Home Assistant GATT inventory probe. An additional early exchange on `001C` occurred, but its payload and purpose were not established.

### Advertisement-to-connection attribution

The capture contains **942 extended-advertising reports** using one random-address/type tuple that differs from the public-address tuple in the connection event. None contains an FE95 service-data advertisement element. The report deliberately exposes no addresses. Consequently, direct attribution of these advertisements to the connected GATT peer is **not confirmed**. FE95 characteristics and timing of Mi Home screenshots support, but do not independently prove, the S5 session identification.

## Authentication exchange and cryptographic comparison

Observed FE95 events:

| Time (UTC) | Direction / channel | Observation |
| --- | --- | --- |
| `00:41:01.017` | Host → `0010` | Write Command `A4` (one byte), authentication initialization |
| `00:41:01.098`, `.197` | Peer → `0019` | Two authentication frames, marker `00 00 04`, lengths 6 and 244 bytes; sensitive continuation bytes withheld |
| `00:41:01.122`, `.219` | Host → `0019` | Two matching protocol echoes with marker `00 00 05`; bodies match after the marker substitution, values redacted |
| After initialization | `0019` | Send-key/send-info headers, a 16-byte random-key parcel, 32-byte login-info parcel, remote-key/remote-info frames, and RCV_RDY/RCV_OK control flow; HMAC/key bytes withheld |
| `00:41:01.452` | Host → `0010` | `CMD_LOGIN = 24 00 00 00` |
| `00:41:01.928` | Peer → `0010` | `CFM_LOGIN_OK = 21 00 00 00` |

The `A4` → `0019` exchange → `CMD_LOGIN` / `CFM_LOGIN_OK` sequence is consistent with the token-based Xiaomi family documented by Yunmi reference A.[24][25] MiAuth independently uses the `mible-login-info`/HMAC family, but its source does not prove an identical wire handshake.[39][40][41]

A successful login marker alone would not validate the key schedule; the two HMAC proofs and all authenticated data tags do. The `authType=4` setting in the app bundle is a separate OTA parameter and is not evidence for this conclusion.

**Do not identify a protocol from the initial `A4` alone.** The unrelated XW002 code also sends `A4`, but subsequently uses P-256 ECDH/`gatt_ltmk`, a `0x50` login and UUID `0016` with MNG/CTR framing.[26][28] The S5 trace instead uses `0019` authentication and `CMD_LOGIN`/`CFM_LOGIN_OK`; no XW002 `0016` or `0x50` request was observed. Shared ACK bytes or `001A/001B` identifiers do not justify reusing XW002 crypto or application packets.

No SMP L2CAP CID `0x0006`, LE LTK-request subevent, HCI Encryption Change or LE Start Encryption was observed in the recorded event stream: link-layer pairing/encryption is not established by this capture.

Reference A derives 64 bytes through HKDF-SHA256 with `salt=rand||remote_key` and `info=mible-login-info`; login proofs use HMAC-SHA256, and data uses AES-CCM with a four-byte tag, no AAD, and nonce `IV4||00000000||counter_LE32`.[25] MiAuth uses related login crypto but sends commands over an M365/UART `55AB` AES-CCM/CRC16 envelope, **not S5 MIoT Spec-v2 packets**.[39][40][41]

With the verified S5 device token, both HMAC proofs and all **3 outgoing + 269 incoming = 272 AES-CCM tags** authenticated. This establishes the cryptographic profile for the supplied frames only.

## Encrypted MIoT data channel and offline decoding

Three completed single-parcel outgoing transfers were observed on `001A`/`001B`. The offline decoder first verifies the login proofs and authentication tags, then decodes properties without printing ciphertext, tokens or derived keys:

| Time (UTC) | Outgoing parcel length | Parcel counter | Authenticated request | Nearest 21-byte `001B` notification |
| --- | ---: | ---: | --- | --- |
| `00:43:05.427` | 21 bytes | 0 | SIID 3 / PIID 5, uint16 `2054` | `00:43:05.606`, counter 124 |
| `00:43:21.074` | 21 bytes | 1 | SIID 3 / PIID 5, uint16 `4095` | `00:43:21.208`, counter 141 |
| `00:43:27.853` | 20 bytes | 2 | SIID 3 / PIID 7, uint8 `255` | `00:43:27.934`, counter 149 |

A six-byte header `00 00 00 00 01 00` precedes each parcel, followed by `RCV_RDY`. The parcel carries index `01 00`, a 16-bit little-endian counter and encrypted bytes, followed by `RCV_OK`. All three decrypted requests are MIoT Spec-v2 single-property writes. Reference A uses 18-byte chunks, whereas the first two S5 parcel payloads after the index contain **19 bytes in one parcel**. A shared cryptographic key schedule does not make the chunking policies interchangeable.[25]

The capture contains exactly six outgoing Write Commands to handle `0021` (UUID `001A`): three header/parcel pairs. No writes occur there in the roughly two minutes after login and before the first property write. In particular, the encrypted post-login `F0` used by Yunmi reference A is **absent**. This is an application-layer difference, not a contradiction of shared login cryptography.[25]

Incoming notifications use prefix `00 00 02 00`, a 16-bit little-endian counter, and ciphertext plus tag. Of 269 frames, 266 have ATT length 74 (68 encrypted bytes) and three have length 21 (15 encrypted bytes); with a four-byte tag, plaintext lengths are 64 and 11 bytes respectively. Each counter from 1 through 269 appears once, but the HCI record order is not strictly increasing: short frames 124/141/149 precede long frames 123/140/148. The decoder therefore uses **each frame's own counter**, not the capture order. All 269 receive `00 00 03 00` ACKs. An ACK confirms transport handling, **not physical action**.

The XW002 P-256 ECDH/`gatt_ltmk` and UUID `0016` pathway was not observed.[26][28] The S5 app bundle issues property commands through `Bluetooth.spec.setPropertiesValue`; the checked extracted JavaScript modules did not reveal the underlying crypto derivation.

## MIoT schema and source-bundle property mapping

The exact device URN `urn:miot-spec-v2:device:diffuser:0000A01E:bwj-s5:1` was compared with cached MIoT schema version 1/minor 1, `_updated_time=2026-11-03T03:59:34Z`. This is a schema mirror/cache, **not firmware source**. The generic MIoT `access=[]` field is empty; `gatt-access` is a separate extension. Timing units are not specified by this schema.[29][30][32]

| Property | SIID / PIID | Type and range | `gatt-access` | App bundle key |
| --- | --- | --- | --- | --- |
| `status` | 2 / 1004 | uint8, Off=0 / On=1 | Read/write/notify | `workStatus` (`prop.2.1004`) |
| `fragrance-out-time` | 3 / 3 | uint8, 3–30, step 1 | Read/write/notify | `fragranceOutTime` |
| `idle-time` | 3 / 4 | uint8, 0–30, step 1 | Read/write/notify | `idleTime` |
| `auto-power-on` | 3 / 5 | uint16, 1–65535, step 1 | Read/write/notify | `autoPowerTime` |
| `unixtime` | 3 / 6 | uint32, 1–4294967295, step 1 | Write only | `prop.3.6` absent from checked UI map |
| `repeat` | 3 / 7 | uint8, 0–255, step 1 | Read/write/notify | `repeat` |
| `light` | 3 / 8 | uint8, 0–255, step 1 | Read/write/notify | `light` |
| `color` | 3 / 9 | uint32, 0–16777215, step 1 | Read/write/notify | `color` |

The `module_10025.js` extracted plugin contains the mapping; `module_10226.js` uses bit 128 as the UI `timeSwitch` flag for `repeat`. This describes plugin behavior, **not verified firmware semantics**. Captured `auto-power-on` values 2054 and 4095 must not be assigned time units from the schema alone; `repeat=255` likewise remains a raw value. `unixtime` is write-only in the schema and absent from the checked UI map, so read/restore assumptions are unjustified.

The three transactions correlate in time with screenshots at 00:42–00:43, but neither screenshots nor successful `SetPropertyResp code=0` with matching `PropertyChanged` values prove the physical response of the atomizer.

## Pinned upstream source comparison

| Project | Pinned commit | Relevant finding / compatibility boundary |
| --- | --- | --- |
| `hass-yunmi-kettle-ble` | `0b3db91e30c7b1cafe287c7c049c481e233ddef1` | Token HKDF/HMAC/CCM and post-login `F0`/18-byte chunk policy. S5 passes crypto checks but differs in post-login traffic and parcel sizing; not a drop-in sender.[24][25] |
| `miauth` | `7df4f35c258f926ce396df3691d7f91d86ad761e` | Same token `mible-login-info`/HMAC login family, but separate M365/UART `55AB`/AES-CCM/CRC16 command framing; not the S5 MIoT sender.[39][40][41] |
| `Xiaomi-cloud-tokens-extractor` | `c4db715dace9806e905153c2977608873e8ab7c9` | Extractor rather than BLE sender; distinguishes `token` and `BLE_DATA.beaconkey`.[34][35] |
| `xiaomi-diffuser-ble` (XW002) | `96268a53e3c8ba4443dd322ecaede606ec7c89c6` | P-256 ECDH/`gatt_ltmk`, UUID `0016` and `0x50` login; only initial `A4` overlaps.[26][27][28] |

The pinned `xiaomi-ble 1.16.1` MiBeacon parser takes a `bindkey`; whether it relates to the extractor's `BLE_DATA.beaconkey` or the local `ble_key` cannot be proven from these data. What was disproved is the latter's suitability for **the observed GATT login**.[46]

## Unauthenticated visibility and cloud independence

- A separate **read-only GATT probe** connected to an FE95 candidate and enumerated services without secure login. It performed no proprietary MIoT reads. This proves only BLE link/service discovery.
- Advertisements in the capture were not directly correlated with the connected GATT peer, and S5 MiBeacon payloads were not decrypted. Unauthenticated advertisement content and its precise semantics remain unknown.
- The three decoded requests travelled over **local GATT/MIoT** after token login. The HCI capture contains no contemporaneous WAN/IP evidence; it cannot prove that the entire Mi Home app works without cloud access. A WAN-off test, token lifetime and rotation were not established at capture time.

## Offline decoder, tests and historical integration baseline

`tools/s5_payload_decoder.py` accepts token bytes in memory, verifies both HMAC login proofs and AES-CCM tags, and parses MIoT Spec-v2 `SetProperty`, `SetPropertyResp` and `PropertyChanged`. It does not emit secret tokens, session keys or ciphertext. `tools/verify_capture.py` accepts a private mode-0600 token file and emits redacted verification status and property metadata.

Results of the **capture-specific verification**:

- Login HMAC proofs verified.
- TX 3/3 frames authenticated and parsed; RX 269/269 frames authenticated and parsed.
- RX messages: 266 `PropertyChanged`, 3 `SetPropertyResp`.
- All three response transaction IDs matched their requests, and all three result codes were zero.
- 2,394 `PropertyChanged` values decoded.
- Captured writes: `3.5=2054`, `3.5=4095`, `3.7=255`.

**Historical version notes:** The production client at version 0.3.0 exposed fixed setters only for `2.1004`, `3.3`, `3.4`, `3.8` and `3.9`; timer/setter registers `3.5` and `3.7` remained out of the public HA control surface. At that stage, the standalone test suite had passed 57 tests and 48 subtests. Before that, 0.2.0 had registered 26 entities including timers; 0.3.0 removed them. These are dated research observations **not statements about the current 0.6.0 installation**.

## Conclusions and limits

**Supported by this capture:** btsnoop integrity; FE95 characteristics; both HMAC proofs; 272/272 AES-CCM tags; three MIoT `SetProperty` requests; three zero response codes; 266 `PropertyChanged` messages; and the source app's property mapping.

**Not established:** direct advertising-to-GATT address identity; physical effects of `3.3`, `3.4`, `3.8`, `3.9`; actual brightness/OFF and atomizer cadence; LongSpray motor duty cycle; independent HA BLE read-back on the original capture date; token expiry/rotation; and operation with WAN disconnected. A user's RGB report is not equivalent to independent hardware acceptance.

No new Bluetooth scan, device pairing/reset, or physical property write was performed for this original research. Do not treat synthetic tests, ACKs or matching property read-back as proof of physical command execution.

## Sources

[24] https://github.com/opravdin/hass-yunmi-kettle-ble/blob/0b3db91e30c7b1cafe287c7c049c481e233ddef1/PROTOCOL.md — Yunmi kettle BLE protocol at pinned commit
[25] https://github.com/opravdin/hass-yunmi-kettle-ble/blob/0b3db91e30c7b1cafe287c7c049c481e233ddef1/custom_components/yunmi_kettle/protocol.py — Yunmi kettle auth implementation at pinned commit
[26] https://github.com/clairefiorettiythzr6802-eng/xiaomi-diffuser-ble/blob/96268a53e3c8ba4443dd322ecaede606ec7c89c6/python/miot_ble_specv2.py — XW002 MIoT BLE Spec-v2 at pinned commit
[27] https://github.com/clairefiorettiythzr6802-eng/xiaomi-diffuser-ble/blob/96268a53e3c8ba4443dd322ecaede606ec7c89c6/python/bridge.py — XW002 bridge at pinned commit
[28] https://github.com/clairefiorettiythzr6802-eng/xiaomi-diffuser-ble/blob/96268a53e3c8ba4443dd322ecaede606ec7c89c6/python/channel.py — XW002 channel/auth implementation at pinned commit
[29] https://miot-spec.org/miot-spec-v2/instance?type=urn%3Amiot-spec-v2%3Adevice%3Adiffuser%3A0000A01E%3Abwj-s5%3A1 — MIoT spec instance for exact SO S5 URN
[30] https://iot.mi.com/new/doc/accesses/direct-access/other-platform-access/control-api — Xiaomi IoT Control API / MIoT-Spec documentation
[32] https://home.miot-spec.com/spec/bwj.diffuser.s5 — Community MIoT schema mirror for bwj.diffuser.s5
[34] https://raw.githubusercontent.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/v1.5.1/token_extractor.py — Xiaomi Cloud token extractor pinned source
[35] https://raw.githubusercontent.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/v1.5.1/README.md — Xiaomi Cloud token extractor pinned README
[39] https://github.com/dnandha/miauth/blob/7df4f35c258f926ce396df3691d7f91d86ad761e/doc/README.md — MiAuth BLE authentication protocol/crypto documentation
[40] https://github.com/dnandha/miauth/blob/7df4f35c258f926ce396df3691d7f91d86ad761e/lib/python/miauth/mi/micrypto.py — MiAuth Python crypto implementation
[41] https://github.com/dnandha/miauth/blob/7df4f35c258f926ce396df3691d7f91d86ad761e/lib/python/miauth/mi/miclient.py — MiAuth Python BLE client implementation
[46] https://raw.githubusercontent.com/Bluetooth-Devices/xiaomi-ble/416fc828fc2a008f7fcab14513c27e50bb782099/src/xiaomi_ble/parser.py — Bluetooth-Devices xiaomi-ble v1.16.1 MiBeacon parser, pinned commit 416fc828
[49] https://raw.githubusercontent.com/home-assistant/core/2026.10.4/homeassistant/components/bluetooth/api.py — Home Assistant Core 2026.10.4 Bluetooth API

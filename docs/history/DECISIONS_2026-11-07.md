# Design decisions

## D-001 — Xiaomi Cloud is not part of the HA runtime

Use the external Xiaomi Cloud Tokens Extractor for one-time credential retrieval. The integration consumes a local 12-byte token file and uses BLE at runtime. Account passwords and QR authentication are never handled by the HA custom component.

## D-002 — GATT token and beacon key are different credentials

The extractor exports a device `token` and may export `BLE_DATA.beaconkey`. The supplied S5 capture validates the 12-byte token for the GATT login proofs and AES-CCM session. The 16-byte beacon key candidate fails the captured login HMAC checks; it is not substituted for the token and is not stored by this project.

## D-003 — Schedule UI is out of scope

The original UI contains timer, two-hour windows and weekdays, but the owner does not want those controls. Remove their entities and their production setters. Keep the historical `3.5`/`3.7` capture analysis for protocol documentation only.

## D-004 — Pause is a slider plus explicit LongSpray mode

The app presents `3.4` values 3–30 as minute choices and the special `LongSpray=0`. HA therefore exposes a 3–30 minute slider and a separate switch for the special value. When leaving LongSpray, restore the last non-zero value; if none is known, use 3.

## D-005 — Light OFF means clearing the master enable bit

The Mi Home UI clears bit 7 to turn the light off while preserving the low bits. The HA light mirrors this, maps HA brightness 1–255 to the S5 1–100 range, treats brightness zero as OFF, and restores the previous mode/level on ON. Automatic Gradient mode does not expose a fabricated brightness value.

## D-006 — Fixed property allowlist only

No generic MIoT write interface. Production setters are limited to power, spray duration, pause, light and RGB colour. The timer/schedule properties are excluded.

## D-007 — Protocol evidence is not physical acceptance

HMAC/AEAD validation, SetPropertyResp and PropertyChanged read-back prove protocol integrity and property acknowledgement only. Physical spray cadence and visible lighting must be checked independently before a release is called hardware-accepted.

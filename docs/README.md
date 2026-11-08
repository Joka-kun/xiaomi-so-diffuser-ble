# Documentation

Start with the [installation guide](INSTALLATION.md) or the [Russian installation guide](ru/INSTALLATION.md). The [six-language README](../README.md) provides a short overview and the four-step setup illustration.

## Getting started

| Topic | Guide |
| --- | --- |
| Install, authorize Xiaomi and connect over BLE | [Installation](INSTALLATION.md) · [Russian guide](ru/INSTALLATION.md) |
| Check supported features and model-specific uncertainty | [Compatibility matrix](COMPATIBILITY.md) · [Russian matrix](ru/COMPATIBILITY.md) |
| Move from the legacy `so_s5` integration | [Migration](MIGRATION.md) · [Russian migration](ru/MIGRATION.md) |
| Solve login, token or Bluetooth problems | [Installation FAQ](INSTALLATION.md#common-questions) · [Credentials](CREDENTIALS.md) |

## Technical reference

| Topic | Reference |
| --- | --- |
| Model isolation, onboarding and cryptographic proof | [Architecture](MULTI_MODEL_ARCHITECTURE.md) |
| BLE packet and property details | [Protocol](PROTOCOL.md) · [Spray modes](SPRAY_MODES_AND_COMPATIBILITY.md) |
| Research based on redacted HCI evidence | [English analysis](research/HCI_CAPTURE_ANALYSIS.md) · [Original Russian analysis](ru/research/HCI_CAPTURE_ANALYSIS.md) |
| Test coverage and physical acceptance procedure | [Testing](TESTING.md) · [Source audit](AUDIT_2026-11-07.md) |

## Project maintenance

[Status](STATUS.md) · [Roadmap](../ROADMAP.md) · [Contributing](../CONTRIBUTING.md) · [Language policy](LANGUAGE_POLICY.md) · [Branding](BRANDING.md) · [Release notes](RELEASE_NOTES.md) · [Publishing](PUBLISHING.md) · [Security](../SECURITY.md) · [Historical snapshots](history/README.md)

**Evidence levels matter:** an exact Bluetooth advertisement, a successful authenticated GATT handshake and physically observed device control are different results. Only the SO S5 has a user-reported real-device success; other model profiles remain experimental.

The current integration domain is `so_diffuser_ble`. The dated records under `history/` are retained for traceability but must not replace current installation instructions.

# Documentation

This is the **single entry point** for project documentation. For guides with illustrations choose [English](../README.md) · [Russian](../README_RU.md) · [German](../README_DE.md) · [Spanish](../README_ES.md) · [French](../README_FR.md) · [Simplified Chinese](../README_ZH_CN.md).

| Need | Read |
| --- | --- |
| Install a diffuser | [Installation](INSTALLATION.md) |
| Read installation guidance in Russian | [Russian user guides](ru/README.md) |
| See which SO devices can work | [Model compatibility](COMPATIBILITY.md) |
| Understand the OAuth and BLE proof | [Technical architecture](MULTI_MODEL_ARCHITECTURE.md) |
| Diagnose a token or spray problem | [Credentials](CREDENTIALS.md) · [Protocol](PROTOCOL.md) |
| Run tests / contribute | [Testing](TESTING.md) |
| See current unverified items | [Project status](STATUS.md) · [Roadmap](../ROADMAP.md) |
| Review the current source-level audit and release blockers | [Technical audit](AUDIT_2026-11-07.md) |
| Review source-level cryptographic research | [English HCI analysis](research/HCI_CAPTURE_ANALYSIS.md) · [Original Russian research](ru/research/HCI_CAPTURE_ANALYSIS.md) |
| Prepare HACS publication | [Release checklist](PUBLISHING.md) |
| Understand reuse and redistribution terms | [MIT License](../LICENSE) |
| Contribute translations or fix language consistency | [Language and terminology policy](LANGUAGE_POLICY.md) |
| View brand icons and catalog status | [Branding](BRANDING.md) |
| Read first public release notes | [Release notes](RELEASE_NOTES.md) |

**Confidence language:** *discovered* = Bluetooth advertisement matched; *authenticated* = Xiaomi token passed GATT Standard Auth against the physical address; *physically verified* = a device command was observed working on that model. Only S5 has a reported real-device success so far.

**Domain:** `so_diffuser_ble`. Credentials persist independently of the public name. For legacy installations, a separate [technical migration reference](MIGRATION.md) remains available; new users can follow the standard installation guide.

Legacy research and project reports are kept as historical evidence, not as competing installation instructions. The current README and installation/migration guides take precedence.

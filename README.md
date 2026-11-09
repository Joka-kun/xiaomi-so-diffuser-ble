<p align="center"><img src="docs/assets/hero.svg" alt="Local Bluetooth control of SO / BWJ aroma diffusers for Home Assistant." width="100%"></p>

<p align="center"><a href="README.md">English</a> &nbsp;·&nbsp; <a href="README_RU.md">Русский</a> &nbsp;·&nbsp; <a href="README_DE.md">Deutsch</a> &nbsp;·&nbsp; <a href="README_FR.md">Français</a> &nbsp;·&nbsp; <a href="README_ES.md">Español</a> &nbsp;·&nbsp; <a href="README_ZH_CN.md">中文</a></p>

<p align="center">
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/Joka-kun/xiaomi-so-diffuser-ble/tests.yml?branch=main&amp;label=tests&amp;style=flat-square" alt="Tests"></a>
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases"><img src="https://img.shields.io/github/v/release/Joka-kun/xiaomi-so-diffuser-ble?label=release&amp;style=flat-square" alt="Latest release"></a>
  <a href="https://www.home-assistant.io/integrations/marketplace/"><img src="https://img.shields.io/badge/Marketplace-listed-18A4CB?style=flat-square&amp;logo=homeassistant&amp;logoColor=white" alt="Marketplace listing"></a>
  <a href="docs/COMPATIBILITY.md"><img src="https://img.shields.io/badge/control-local%20BLE-0F766E?style=flat-square" alt="Local BLE"></a>
</p>

# Xiaomi SO Diffuser BLE

**Community-maintained Home Assistant Marketplace integration for local Bluetooth control of SO / BWJ aroma diffusers.**

> **SO S5** has user-reported working controls and native color cycling. Other SO models remain **experimental**, not certified.

## Features

- **On/Off** — spray operation
- **Spray** — duration, pause, zero-pause option
- **Backlight** — RGB, native gradient and optional HA color palettes
- **Xiaomi sign-in** — one-time device token; local BLE afterwards

## Quick start

**Install:** In **Settings → Marketplace** (formerly **HACS**), search for **Xiaomi SO Diffuser BLE** and install this community integration.

**Before pairing:** Use a Bluetooth adapter capable of active connections or an active Home Assistant Bluetooth proxy. Turn on the diffuser.

### Connection in four steps

<p align="center"><img src="docs/assets/connection-four-steps.png" alt="Four stages: discover the diffuser, authorize with Xiaomi, verify the BLE token and control locally" width="100%"></p>

1. **Discover** — In Home Assistant, open **Settings → Devices & services → Add integration → Xiaomi SO Diffuser BLE**. Select the exact diffuser, or use manual Bluetooth address entry if discovery does not find it.
2. **Authorize** — Sign in to your Xiaomi account and select the **same physical diffuser**. For a non-S5 model, accept the experimental-model warning only if you understand its limitations.
3. **Verify** — The integration automatically uses the device-specific token to authenticate over BLE. A token is saved only after the device passes the GATT authentication check.
4. **Control** — Test **On/Off** on the actual device before creating automations. Once configured, normal commands use local Bluetooth rather than Xiaomi Cloud.

If Xiaomi redirects to an unreachable `homeassistant.local`, replace only the **host of the final browser callback URL** with the address of your HA server. Leave the webhook path and authorization parameters unchanged. Do not publish that callback.

## Model compatibility

- **S5 — real-device results reported**
- **S1, S1 Pro, S2, S6, S7, S8, S9, S19 — experimental BLE profiles**

Lighting: **Steady**, **Automatic Gradient** (native), **Color Cycle (HA)** and **Sunset (HA)**. The HA effects require an active connection.

## Documentation

[Installation](docs/INSTALLATION.md) · [Model compatibility](docs/COMPATIBILITY.md) · [Troubleshooting](docs/INSTALLATION.md#common-questions) · [Documentation index](docs/README.md) · [Roadmap](ROADMAP.md)

---

[MIT](LICENSE)

*An independent community integration. Not affiliated with Xiaomi or the Home Assistant project.*

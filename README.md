<p align="center"><img src="docs/assets/hero.svg" alt="Local Bluetooth control of SO / BWJ aroma diffusers for Home Assistant." width="100%"></p>

<p align="center"><a href="README.md">English</a> &nbsp;·&nbsp; <a href="README_RU.md">Русский</a> &nbsp;·&nbsp; <a href="README_DE.md">Deutsch</a> &nbsp;·&nbsp; <a href="README_FR.md">Français</a> &nbsp;·&nbsp; <a href="README_ES.md">Español</a> &nbsp;·&nbsp; <a href="README_ZH_CN.md">中文</a></p>

<p align="center">
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml"><img src="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases"><img src="https://img.shields.io/github/v/release/Joka-kun/xiaomi-so-diffuser-ble?label=release" alt="Latest release"></a>
  <a href="docs/COMPATIBILITY.md"><img src="https://img.shields.io/badge/control-local%20BLE-04B4C7" alt="Local BLE"></a>
</p>

# Xiaomi SO Diffuser BLE

**Local Bluetooth control of SO / BWJ aroma diffusers for Home Assistant.**

> **SO S5** has user-reported working controls and native color cycling. Other SO models remain **experimental**, not certified.

| | |
| --- | --- |
| <span>⏻</span> | **On/Off** — spray operation |
| <span>〰</span> | **Spray** — duration, pause, zero-pause option |
| <span>◉</span> | **Backlight** — RGB, native gradient and optional HA color palettes |
| <span>↗</span> | **Xiaomi sign-in** — one-time device token; local BLE afterwards |

## Quick start

1. Install this repository from **HACS / Marketplace** as an **Integration**.
2. Add **Xiaomi SO Diffuser BLE** in Home Assistant. Turn the diffuser on, then select the device.
3. Sign in via Xiaomi and select the exact diffuser. Confirm any experimental-model warning.
4. Test the physical **On/Off** switch before creating automations.

If Xiaomi redirects to an unreachable `homeassistant.local`, replace only the **host of the final browser callback URL** with the address of your HA server. Leave the webhook path and authorization parameters unchanged. Do not publish that callback.

![Controls preview](docs/assets/control-preview.svg)

*Illustrative interface, not a live Home Assistant screenshot.*

## Model compatibility

![Model compatibility — SO S5, S1, S1 Pro, S2, S6, S7, S8, S9, S19](docs/assets/model-family.svg)

- **S5 — real-device results reported**
- **S1, S1 Pro, S2, S6, S7, S8, S9, S19 — experimental BLE profiles**

Lighting: **Steady**, **Automatic Gradient** (native), **Color Cycle (HA)** and **Sunset (HA)**. The HA effects require an active connection.

## Documentation

[Installation](docs/INSTALLATION.md) · [Model matrix](docs/COMPATIBILITY.md) · [Architecture](docs/MULTI_MODEL_ARCHITECTURE.md) · [Release notes](docs/RELEASE_NOTES.md) · [Roadmap](ROADMAP.md)

---

*An independent community integration. Not affiliated with Xiaomi or the Home Assistant project.*

<p align="center"><img src="docs/assets/hero.svg" alt="Lokale Bluetooth-Steuerung für SO-/BWJ-Aromadiffusoren in Home Assistant." width="100%"></p>

<p align="center"><a href="README.md">English</a> &nbsp;·&nbsp; <a href="README_RU.md">Русский</a> &nbsp;·&nbsp; <a href="README_DE.md">Deutsch</a> &nbsp;·&nbsp; <a href="README_FR.md">Français</a> &nbsp;·&nbsp; <a href="README_ES.md">Español</a> &nbsp;·&nbsp; <a href="README_ZH_CN.md">中文</a></p>

<p align="center">
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml"><img src="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases"><img src="https://img.shields.io/github/v/release/Joka-kun/xiaomi-so-diffuser-ble?label=release" alt="Latest release"></a>
  <a href="docs/COMPATIBILITY.md"><img src="https://img.shields.io/badge/control-local%20BLE-04B4C7" alt="Local BLE"></a>
</p>

# Xiaomi SO Diffuser BLE

**Lokale Bluetooth-Steuerung für SO-/BWJ-Aromadiffusoren in Home Assistant.**

> **SO S5** wurde bereits auf einem echten Gerät getestet. Weitere SO-Modelle sind weiterhin **experimentell**.

| | |
| --- | --- |
| <span>⏻</span> | **Ein/Aus** — Duftabgabe starten und stoppen |
| <span>〰</span> | **Sprühmodus** — Dauer, Pause und Null-Pause |
| <span>◉</span> | **Beleuchtung** — RGB, nativer Farbverlauf und HA-Effekte |
| <span>↗</span> | **Xiaomi-Anmeldung** — einmaliger Geräte-Token, danach lokal |

## Schnellstart

1. Repository über **HACS / Marketplace** als **Integration** installieren.
2. **Xiaomi SO Diffuser BLE** in Home Assistant hinzufügen, Diffusor einschalten und auswählen.
3. Bei Xiaomi anmelden und das passende Gerät wählen. Bei anderen Modellen die experimentelle Nutzung bestätigen.
4. Ein-/Ausschalten am echten Gerät prüfen, bevor Automationen aktiviert werden.

Falls der Xiaomi-Rücksprung zu `homeassistant.local` nicht funktioniert, in der **fertigen Browseradresse nur die Serveradresse** auf den erreichbaren HA-Host ändern. Webhook-Pfad und Parameter unverändert lassen; den Link nicht teilen.

![Vorschau der Bedienelemente](docs/assets/control-preview.svg)

*Schematische Darstellung, kein Screenshot eines laufenden Home Assistant.*

## Unterstützte Modelle

![Unterstützte Modelle — SO S5, S1, S1 Pro, S2, S6, S7, S8, S9, S19](docs/assets/model-family.svg)

- **S5 — vom Nutzer praktisch bestätigt**
- **S1, S1 Pro, S2, S6, S7, S8, S9, S19 — experimentelle BLE-Profile**

Lichtmodi: **Dauerlicht**, **Automatischer Farbverlauf** (im Gerät), **Farbwechsel (HA)** und **Sonnenuntergang (HA)**. Die HA-Effekte benötigen eine aktive Verbindung.

## Dokumentation

[Installation (Englisch)](docs/INSTALLATION.md) · [Kompatibilität (Englisch)](docs/COMPATIBILITY.md) · [Technik (Englisch)](docs/MULTI_MODEL_ARCHITECTURE.md) · [Versionshinweise (Englisch)](docs/RELEASE_NOTES.md)

---

*Unabhängiges Community-Projekt, nicht von Xiaomi oder Home Assistant betrieben.*

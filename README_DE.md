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

## Funktionen

- **Ein/Aus** — Duftabgabe starten und stoppen
- **Sprühmodus** — Dauer, Pause und Null-Pause
- **Beleuchtung** — RGB, nativer Farbverlauf und HA-Effekte
- **Xiaomi-Anmeldung** — einmaliger Geräte-Token, danach lokal

## Schnellstart

**Installation:** Unter **HACS / Marketplace → Benutzerdefinierte Repositories** `https://github.com/Joka-kun/xiaomi-so-diffuser-ble` als **Integration** hinzufügen und installieren. Home Assistant bei Aufforderung neu starten.

**Vor der Verbindung:** Ein Bluetooth-Adapter für aktive Verbindungen oder ein aktiver Home-Assistant-Bluetooth-Proxy ist nötig. Den Diffusor einschalten.

### Verbindung in vier Schritten

<p align="center"><img src="docs/assets/connection-four-steps.png" alt="Vier Schritte: Erkennen, Xiaomi-Anmeldung, BLE-Token prüfen und lokal steuern" width="100%"></p>

1. **Erkennen** — In Home Assistant unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** Xiaomi SO Diffuser BLE öffnen und das genaue Gerät auswählen. Falls nötig, die Bluetooth-Adresse manuell eingeben.
2. **Autorisieren** — Im Xiaomi-Konto anmelden und **denselben physischen Diffusor** auswählen. Bei anderen Modellen als S5 die Einschränkungen des experimentellen Profils beachten.
3. **Verifizieren** — Die Integration prüft das gerätespezifische Token automatisch durch BLE-GATT-Authentifizierung. Es wird erst nach erfolgreicher Prüfung gespeichert.
4. **Steuern** — **Ein/Aus** am echten Gerät testen, bevor Automationen eingerichtet werden. Danach laufen normale Befehle lokal über Bluetooth, nicht über die Xiaomi Cloud.

Falls der Xiaomi-Rücksprung zu `homeassistant.local` nicht funktioniert, in der **fertigen Browseradresse nur die Serveradresse** auf den erreichbaren HA-Host ändern. Webhook-Pfad und Parameter unverändert lassen; den Link nicht teilen.

## Unterstützte Modelle

- **S5 — vom Nutzer praktisch bestätigt**
- **S1, S1 Pro, S2, S6, S7, S8, S9, S19 — experimentelle BLE-Profile**

Lichtmodi: **Dauerlicht**, **Automatischer Farbverlauf** (im Gerät), **Farbwechsel (HA)** und **Sonnenuntergang (HA)**. Die HA-Effekte benötigen eine aktive Verbindung.

## Dokumentation

[Installation (Englisch)](docs/INSTALLATION.md) · [Kompatibilität (Englisch)](docs/COMPATIBILITY.md) · [Dokumentation (Englisch)](docs/README.md) · [Änderungsprotokoll (Englisch)](CHANGELOG.md)

---

[MIT](LICENSE)

*Unabhängiges Community-Projekt, nicht von Xiaomi oder Home Assistant betrieben.*

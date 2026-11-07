# Xiaomi SO Diffuser BLE — first public release

A new, cleaned-up publication of the SO/BWJ aroma diffuser integration for Home Assistant. This is the **first public GitHub Release** of the current multi-model project, version **1.0.0**.

## What is included

- Local BLE control of SO S5: on/off, spray duration and pause, continuous/zero-pause mode, battery and charging status.
- Xiaomi OAuth provisioning with local device GATT token verification; normal commands run via Bluetooth rather than recurring cloud calls.
- RGB Backlight: steady color, device-native Automatic Gradient (user-confirmed on S5), and optional Home Assistant Color Cycle / Sunset software palettes.
- The primary switch is named **«Вкл/Выкл»** in the Russian UI; Backlight remains a separate control.
- A refreshed graphical identity, README/compatibility diagrams, Home Assistant brand icons and six current README languages.
- Explicit, opt-in experimental catalog profiles for SO S1, S1 Pro, S2, S6, S7, S8, S9 and S19.

## Compatibility

**SO S5:** the operator has reported real-world success with OAuth, BLE control and the native RGB gradient. The final visual refresh and optional HA-driven palettes are covered by automated tests but have not undergone full hardware acceptance.

**Other models:** experimental. An account listing and shared MIoT property names do not establish identical BLE authentication or physical actuator behavior.

## Install

1. Add `https://github.com/Joka-kun/xiaomi-so-diffuser-ble` to the Marketplace/HACS as a custom **Integration** repository.
2. Install release `v1.0.0` and restart Home Assistant if prompted.
3. Choose **Xiaomi SO Diffuser BLE**, sign in to Xiaomi and select your exact physical device.
4. If the browser cannot open the default `homeassistant.local` OAuth callback, replace only the final URL's host with the accessible HA address, preserving all webhook parameters.
5. Check the real on/off switch before enabling automations.

If you previously used the old `so_s5` **domain**, read [the migration guide](https://github.com/Joka-kun/xiaomi-so-diffuser-ble/blob/main/docs/MIGRATION.md). Do not delete stored BLE credentials or manually edit HA registries.

The current project is community maintained and is not affiliated with Xiaomi or Home Assistant.

## Verification

Python tests, Hassfest and HACS checks are run in GitHub Actions. Hardware verification remains model-specific; this release is **not a claim** that all nine SO devices have passed physical tests.

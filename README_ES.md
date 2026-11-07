<p align="center"><img src="docs/assets/hero.svg" alt="Control local por Bluetooth de difusores SO / BWJ en Home Assistant." width="100%"></p>

<p align="center"><a href="README.md">English</a> &nbsp;·&nbsp; <a href="README_RU.md">Русский</a> &nbsp;·&nbsp; <a href="README_DE.md">Deutsch</a> &nbsp;·&nbsp; <a href="README_FR.md">Français</a> &nbsp;·&nbsp; <a href="README_ES.md">Español</a> &nbsp;·&nbsp; <a href="README_ZH_CN.md">中文</a></p>

<p align="center">
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml"><img src="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases"><img src="https://img.shields.io/github/v/release/Joka-kun/xiaomi-so-diffuser-ble?label=release" alt="Latest release"></a>
  <a href="docs/COMPATIBILITY.md"><img src="https://img.shields.io/badge/control-local%20BLE-04B4C7" alt="Local BLE"></a>
</p>

# Xiaomi SO Diffuser BLE

**Control local por Bluetooth de difusores SO / BWJ en Home Assistant.**

> **SO S5** tiene resultados reales confirmados por un usuario. Los demás modelos son **experimentales**.

| | |
| --- | --- |
| <span>⏻</span> | **Encender/apagar** — funcionamiento del difusor |
| <span>〰</span> | **Pulverización** — duración, pausa y modo sin pausa |
| <span>◉</span> | **Luz** — RGB, gradiente nativo y efectos de HA |
| <span>↗</span> | **Inicio de sesión Xiaomi** — token inicial; control BLE local |

## Primeros pasos

1. Instala el repositorio mediante **HACS / Marketplace**, tipo **Integración**.
2. Añade **Xiaomi SO Diffuser BLE** a Home Assistant, enciende el difusor y selecciónalo.
3. Inicia sesión en Xiaomi y elige el aparato correspondiente. Confirma la advertencia experimental cuando corresponda.
4. Comprueba físicamente el encendido y apagado antes de automatizar.

Si Xiaomi devuelve una dirección `homeassistant.local` inaccesible, cambia **solo la dirección del servidor en la URL final del navegador**. Conserva la ruta del webhook y sus parámetros; no compartas el enlace.

![Vista previa de controles](docs/assets/control-preview.svg)

*Ilustración de la interfaz; no es una captura de una instalación real.*

## Compatibilidad

![Compatibilidad — SO S5, S1, S1 Pro, S2, S6, S7, S8, S9, S19](docs/assets/model-family.svg)

- **S5 — funcionamiento real confirmado por usuario**
- **S1, S1 Pro, S2, S6, S7, S8, S9, S19 — perfiles BLE experimentales**

Iluminación: **Luz fija**, **Gradiente automático** (nativo), **Cambio de colores (HA)** y **Atardecer (HA)**. Los efectos HA necesitan una conexión activa.

## Documentación

[Instalación (inglés)](docs/INSTALLATION.md) · [Modelos (inglés)](docs/COMPATIBILITY.md) · [Arquitectura (inglés)](docs/MULTI_MODEL_ARCHITECTURE.md) · [Notas de lanzamiento (inglés)](docs/RELEASE_NOTES.md)

---

[MIT](LICENSE)

*Proyecto independiente de la comunidad; no afiliado a Xiaomi ni a Home Assistant.*

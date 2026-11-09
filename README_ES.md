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

## Funciones

- **Encender/apagar** — funcionamiento del difusor
- **Pulverización** — duración, pausa y modo sin pausa
- **Luz** — RGB, gradiente nativo y efectos de HA
- **Inicio de sesión Xiaomi** — token inicial; control BLE local

## Primeros pasos

**Instalación:** en **Ajustes → Marketplace** (antes **HACS**), busca **Xiaomi SO Diffuser BLE** e instala la integración desde el catálogo.

**Antes de conectar:** necesitas un adaptador Bluetooth que admita conexiones activas o un proxy Bluetooth activo de Home Assistant. Enciende el difusor.

### Conexión en cuatro pasos

<p align="center"><img src="docs/assets/connection-four-steps.png" alt="Cuatro pasos: detección, autorización Xiaomi, verificación del token BLE y control local" width="100%"></p>

1. **Detectar** — en Home Assistant, ve a **Ajustes → Dispositivos y servicios → Añadir integración → Xiaomi SO Diffuser BLE** y selecciona el difusor exacto. Si no aparece, introduce manualmente su dirección Bluetooth.
2. **Autorizar** — inicia sesión en Xiaomi y selecciona **el mismo dispositivo físico**. Para modelos distintos del S5, revisa la advertencia de compatibilidad experimental.
3. **Verificar** — la integración comprueba automáticamente el token propio del dispositivo mediante autenticación BLE GATT. Solo lo guarda si la verificación tiene éxito.
4. **Controlar** — prueba **Encender/apagar** en el dispositivo real antes de crear automatizaciones. Después, los comandos habituales funcionan por Bluetooth local, sin Xiaomi Cloud.

Si Xiaomi devuelve una dirección `homeassistant.local` inaccesible, cambia **solo la dirección del servidor en la URL final del navegador**. Conserva la ruta del webhook y sus parámetros; no compartas el enlace.

## Compatibilidad

- **S5 — funcionamiento real confirmado por usuario**
- **S1, S1 Pro, S2, S6, S7, S8, S9, S19 — perfiles BLE experimentales**

Iluminación: **Luz fija**, **Gradiente automático** (nativo), **Cambio de colores (HA)** y **Atardecer (HA)**. Los efectos HA necesitan una conexión activa.

## Documentación

[Instalación (inglés)](docs/INSTALLATION.md) · [Compatibilidad (inglés)](docs/COMPATIBILITY.md) · [Documentación (inglés)](docs/README.md) · [Historial (inglés)](CHANGELOG.md)

---

[MIT](LICENSE)

*Proyecto independiente de la comunidad; no afiliado a Xiaomi ni a Home Assistant.*

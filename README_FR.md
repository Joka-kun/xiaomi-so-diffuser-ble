<p align="center"><img src="docs/assets/hero.svg" alt="Contrôle Bluetooth local des diffuseurs SO / BWJ dans Home Assistant." width="100%"></p>

<p align="center"><a href="README.md">English</a> &nbsp;·&nbsp; <a href="README_RU.md">Русский</a> &nbsp;·&nbsp; <a href="README_DE.md">Deutsch</a> &nbsp;·&nbsp; <a href="README_FR.md">Français</a> &nbsp;·&nbsp; <a href="README_ES.md">Español</a> &nbsp;·&nbsp; <a href="README_ZH_CN.md">中文</a></p>

<p align="center">
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml"><img src="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases"><img src="https://img.shields.io/github/v/release/Joka-kun/xiaomi-so-diffuser-ble?label=release" alt="Latest release"></a>
  <a href="docs/COMPATIBILITY.md"><img src="https://img.shields.io/badge/control-local%20BLE-04B4C7" alt="Local BLE"></a>
</p>

# Xiaomi SO Diffuser BLE

**Contrôle Bluetooth local des diffuseurs SO / BWJ dans Home Assistant.**

> **SO S5** a été testé sur un appareil réel. Les autres modèles restent **expérimentaux**.

| | |
| --- | --- |
| <span>⏻</span> | **Marche/arrêt** — commande de la diffusion |
| <span>〰</span> | **Diffusion** — durée, pause et mode sans pause |
| <span>◉</span> | **Éclairage** — RGB, dégradé intégré et effets HA |
| <span>↗</span> | **Connexion Xiaomi** — jeton initial, puis Bluetooth local |

## Démarrage rapide

1. Installez ce dépôt via **HACS / Marketplace** comme **Intégration**.
2. Ajoutez **Xiaomi SO Diffuser BLE** dans Home Assistant, allumez le diffuseur et sélectionnez-le.
3. Connectez-vous à Xiaomi et choisissez le bon appareil. Confirmez l'avertissement expérimental si nécessaire.
4. Vérifiez physiquement la marche et l'arrêt avant toute automatisation.

Si Xiaomi renvoie vers une adresse `homeassistant.local` inaccessible, remplacez **uniquement l'adresse du serveur dans l'URL finale du navigateur**. Conservez le chemin du webhook et ses paramètres; ne partagez pas ce lien.

![Aperçu des commandes](docs/assets/control-preview.svg)

*Schéma de l'interface, pas une capture d'écran d'une installation réelle.*

## Compatibilité des modèles

![Compatibilité des modèles — SO S5, S1, S1 Pro, S2, S6, S7, S8, S9, S19](docs/assets/model-family.svg)

- **S5 — essai réel confirmé par l'utilisateur**
- **S1, S1 Pro, S2, S6, S7, S8, S9, S19 — profils BLE expérimentaux**

Éclairage : **Lumière fixe**, **Dégradé automatique** (natif), **Cycle des couleurs (HA)** et **Coucher de soleil (HA)**. Les effets HA nécessitent une connexion active.

## Documentation

[Installation (anglais)](docs/INSTALLATION.md) · [Compatibilité (anglais)](docs/COMPATIBILITY.md) · [Architecture (anglais)](docs/MULTI_MODEL_ARCHITECTURE.md) · [Notes de version (anglais)](docs/RELEASE_NOTES.md)

---

[MIT](LICENSE)

*Projet communautaire indépendant, sans affiliation à Xiaomi ni Home Assistant.*

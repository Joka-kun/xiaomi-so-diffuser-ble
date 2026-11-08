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

## Fonctionnalités

- **Marche/arrêt** — commande de la diffusion
- **Diffusion** — durée, pause et mode sans pause
- **Éclairage** — RGB, dégradé intégré et effets HA
- **Connexion Xiaomi** — jeton initial, puis Bluetooth local

## Démarrage rapide

**Installation :** dans **HACS / Marketplace → Dépôts personnalisés**, ajoutez `https://github.com/Joka-kun/xiaomi-so-diffuser-ble` en tant qu'**Intégration** et installez-la. Redémarrez Home Assistant si demandé.

**Avant l'association :** utilisez un adaptateur Bluetooth capable d'établir des connexions ou un proxy Bluetooth actif de Home Assistant. Allumez le diffuseur.

### Connexion en quatre étapes

<p align="center"><img src="docs/assets/connection-four-steps.png" alt="Quatre étapes : découverte, autorisation Xiaomi, vérification BLE et contrôle local" width="100%"></p>

1. **Découvrir** — dans Home Assistant, ouvrez **Paramètres → Appareils et services → Ajouter une intégration → Xiaomi SO Diffuser BLE**, puis sélectionnez le diffuseur exact. S'il n'apparaît pas, entrez son adresse Bluetooth manuellement.
2. **Autoriser** — connectez-vous au compte Xiaomi et choisissez **le même appareil physique**. Pour un modèle autre que S5, prenez connaissance de l'avertissement expérimental.
3. **Vérifier** — l'intégration authentifie automatiquement le jeton propre à l'appareil par BLE GATT. Le jeton n'est enregistré qu'après vérification réussie.
4. **Contrôler** — testez **Marche/arrêt** sur le diffuseur avant de créer des automatisations. Ensuite, les commandes ordinaires passent par le Bluetooth local, sans Xiaomi Cloud.

Si Xiaomi renvoie vers une adresse `homeassistant.local` inaccessible, remplacez **uniquement l'adresse du serveur dans l'URL finale du navigateur**. Conservez le chemin du webhook et ses paramètres; ne partagez pas ce lien.

## Compatibilité des modèles

- **S5 — essai réel confirmé par l'utilisateur**
- **S1, S1 Pro, S2, S6, S7, S8, S9, S19 — profils BLE expérimentaux**

Éclairage : **Lumière fixe**, **Dégradé automatique** (natif), **Cycle des couleurs (HA)** et **Coucher de soleil (HA)**. Les effets HA nécessitent une connexion active.

## Documentation

[Installation (anglais)](docs/INSTALLATION.md) · [Compatibilité (anglais)](docs/COMPATIBILITY.md) · [Documentation (anglais)](docs/README.md) · [Historique (anglais)](CHANGELOG.md)

---

[MIT](LICENSE)

*Projet communautaire indépendant, sans affiliation à Xiaomi ni Home Assistant.*

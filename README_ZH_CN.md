<p align="center"><img src="docs/assets/hero.svg" alt="通过本地蓝牙将 SO / BWJ 香薰机接入 Home Assistant。" width="100%"></p>

<p align="center"><a href="README.md">English</a> &nbsp;·&nbsp; <a href="README_RU.md">Русский</a> &nbsp;·&nbsp; <a href="README_DE.md">Deutsch</a> &nbsp;·&nbsp; <a href="README_FR.md">Français</a> &nbsp;·&nbsp; <a href="README_ES.md">Español</a> &nbsp;·&nbsp; <a href="README_ZH_CN.md">中文</a></p>

<p align="center">
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/Joka-kun/xiaomi-so-diffuser-ble/tests.yml?branch=main&amp;label=tests&amp;style=flat-square" alt="测试"></a>
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases"><img src="https://img.shields.io/github/v/release/Joka-kun/xiaomi-so-diffuser-ble?label=release&amp;style=flat-square" alt="最新版本"></a>
  <a href="https://www.home-assistant.io/integrations/marketplace/"><img src="https://img.shields.io/badge/Marketplace-listed-18A4CB?style=flat-square&amp;logo=homeassistant&amp;logoColor=white" alt="已收录 Marketplace"></a>
  <a href="docs/COMPATIBILITY.md"><img src="https://img.shields.io/badge/control-local%20BLE-0F766E?style=flat-square" alt="本地 BLE"></a>
</p>

# Xiaomi SO Diffuser BLE

**通过本地蓝牙将 SO / BWJ 香薰机接入 Home Assistant。**

> **SO S5** 的主要功能和原生灯效已有用户实测；其他 SO 型号仍为**实验性支持**。

## 功能

- **开/关** — 控制喷香工作
- **喷香设置** — 时长、间隔和零间隔模式
- **背光** — RGB、设备渐变及 HA 灯效
- **小米登录** — 初次获取设备令牌，之后本地 BLE 控制

## 快速安装

**安装：**打开 **设置 → Marketplace**（原 **HACS**），搜索 **Xiaomi SO Diffuser BLE**，并从目录中安装此集成。

**连接前：**请确保有支持主动连接的蓝牙适配器或已启用的 Home Assistant 蓝牙代理，并打开香薰机。

### 四步完成连接

<p align="center"><img src="docs/assets/connection-four-steps.png" alt="四个步骤：发现设备、小米授权、BLE 令牌验证和本地控制" width="100%"></p>

1. **发现设备** — 在 Home Assistant 中打开**设置 → 设备与服务 → 添加集成 → Xiaomi SO Diffuser BLE**，选择对应的香薰机。如未自动发现，可手动输入蓝牙地址。
2. **授权登录** — 登录小米账号，并选择**同一台实体设备**。S5 以外的型号需要了解并确认实验性兼容提示。
3. **验证连接** — 集成通过 BLE GATT 自动校验该设备专属令牌，仅在验证成功后保存令牌。
4. **本地控制** — 创建自动化之前，先在实体设备上测试**开/关**。完成初次配置后，日常命令通过本地蓝牙执行，不依赖 Xiaomi Cloud。

若小米登录后无法访问 `homeassistant.local`，请在**浏览器最终回调网址**中仅替换服务器地址，保留 webhook 路径及所有参数。请勿公开含授权码的链接。

## 兼容型号

- **S5 — 用户已在真实设备上验证**
- **S1、S1 Pro、S2、S6、S7、S8、S9、S19 — 实验性 BLE 配置**

灯效：**常亮**、设备原生**自动渐变**、**颜色轮换（HA）**和**日落配色（HA）**。HA 灯效需要保持蓝牙连接。

## 文档

[安装（英文）](docs/INSTALLATION.md) · [兼容性（英文）](docs/COMPATIBILITY.md) · [文档索引（英文）](docs/README.md) · [更新记录（英文）](CHANGELOG.md)

---

[MIT](LICENSE)

*独立社区项目，与小米或 Home Assistant 官方无关联。*

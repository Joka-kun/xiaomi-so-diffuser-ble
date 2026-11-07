<p align="center"><img src="docs/assets/hero.svg" alt="Локальное управление аромадиффузорами SO / BWJ через Bluetooth в Home Assistant." width="100%"></p>

<p align="center"><a href="README.md">English</a> &nbsp;·&nbsp; <a href="README_RU.md">Русский</a> &nbsp;·&nbsp; <a href="README_DE.md">Deutsch</a> &nbsp;·&nbsp; <a href="README_FR.md">Français</a> &nbsp;·&nbsp; <a href="README_ES.md">Español</a> &nbsp;·&nbsp; <a href="README_ZH_CN.md">中文</a></p>

<p align="center">
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml"><img src="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases"><img src="https://img.shields.io/github/v/release/Joka-kun/xiaomi-so-diffuser-ble?label=release" alt="Latest release"></a>
  <a href="docs/COMPATIBILITY.md"><img src="https://img.shields.io/badge/control-local%20BLE-04B4C7" alt="Local BLE"></a>
</p>

# Xiaomi SO Diffuser BLE

**Локальное управление аромадиффузорами SO / BWJ через Bluetooth в Home Assistant.**

> **SO S5** — работа управления и встроенного перелива цветов подтверждена пользователем. Другие модели SO пока **экспериментальные**.

| | |
| --- | --- |
| <span>⏻</span> | **Вкл/Выкл** — запуск и остановка распыления |
| <span>〰</span> | **Распыление** — длительность, пауза и режим нулевой паузы |
| <span>◉</span> | **Подсветка** — RGB, встроенный градиент и эффекты HA |
| <span>↗</span> | **Вход Xiaomi** — получение токена при настройке; затем локальная работа |

## Быстрая установка

1. Установите репозиторий через **HACS / Маркетплейс** как **интеграцию**.
2. Добавьте **Xiaomi SO Diffuser BLE** в Home Assistant. Включите диффузор и выберите его.
3. Авторизуйтесь в Xiaomi и выберите именно свой прибор. Экспериментальные модели требуют подтверждения.
4. Проверьте реальное включение и выключение до настройки автоматизаций.

Если Xiaomi возвращает на недоступный `homeassistant.local`, замените **только адрес сервера в конечной ссылке браузера** на свой адрес HA. Путь вебхука и параметры авторизации не изменяйте. Ссылку с кодом никому не отправляйте.

![Предпросмотр управления](docs/assets/control-preview.svg)

*Схема интерфейса, а не скриншот работающей установки.*

## Совместимость моделей

![Совместимость моделей — SO S5, S1, S1 Pro, S2, S6, S7, S8, S9, S19](docs/assets/model-family.svg)

- **S5 — есть подтверждение работы на реальном устройстве**
- **S1, S1 Pro, S2, S6, S7, S8, S9, S19 — экспериментальные профили BLE**

Подсветка: **Постоянный свет**, **Автоматический градиент** (встроенный), **Смена цветов (HA)** и **Закат (HA)**. Программным эффектам нужна работающая связь.

## Документация

[Установка](docs/ru/INSTALLATION.md) · [Совместимость](docs/ru/COMPATIBILITY.md) · [Миграция](docs/ru/MIGRATION.md) · [Исследование протокола](docs/ru/research/HCI_CAPTURE_ANALYSIS.md) · [История изменений](CHANGELOG.md)

---

[MIT](LICENSE)

*Независимая разработка сообщества. Проект не связан с Xiaomi или Home Assistant.*

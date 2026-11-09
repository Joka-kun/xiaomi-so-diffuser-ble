<p align="center"><img src="docs/assets/hero.svg" alt="Локальное управление аромадиффузорами SO / BWJ через Bluetooth в Home Assistant." width="100%"></p>

<p align="center"><a href="README.md">English</a> &nbsp;·&nbsp; <a href="README_RU.md">Русский</a> &nbsp;·&nbsp; <a href="README_DE.md">Deutsch</a> &nbsp;·&nbsp; <a href="README_FR.md">Français</a> &nbsp;·&nbsp; <a href="README_ES.md">Español</a> &nbsp;·&nbsp; <a href="README_ZH_CN.md">中文</a></p>

<p align="center">
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/Joka-kun/xiaomi-so-diffuser-ble/tests.yml?branch=main&amp;label=tests&amp;style=flat-square" alt="Тесты"></a>
  <a href="https://github.com/Joka-kun/xiaomi-so-diffuser-ble/releases"><img src="https://img.shields.io/github/v/release/Joka-kun/xiaomi-so-diffuser-ble?label=release&amp;style=flat-square" alt="Последний релиз"></a>
  <a href="https://www.home-assistant.io/integrations/marketplace/"><img src="https://img.shields.io/badge/Marketplace-listed-18A4CB?style=flat-square&amp;logo=homeassistant&amp;logoColor=white" alt="В каталоге Marketplace"></a>
  <a href="docs/COMPATIBILITY.md"><img src="https://img.shields.io/badge/control-local%20BLE-0F766E?style=flat-square" alt="Локальный BLE"></a>
</p>

# Xiaomi SO Diffuser BLE

**Xiaomi SO Diffuser BLE — пользовательская интеграция из каталога Home Assistant Marketplace для локального управления аромадиффузорами SO / BWJ через Bluetooth.**

> **SO S5** — работа управления и встроенного перелива цветов подтверждена пользователем. Другие модели SO пока **экспериментальные**.

## Возможности

- **Вкл/Выкл** — запуск и остановка распыления
- **Распыление** — длительность, пауза и режим нулевой паузы
- **Подсветка** — RGB, встроенный градиент и эффекты HA
- **Вход Xiaomi** — получение токена при настройке; затем локальная работа

## Быстрая установка

**Установка:** открой **Настройки → Marketplace** (ранее **HACS**), найди **Xiaomi SO Diffuser BLE** и установи интеграцию из каталога.

**Перед подключением:** нужен Bluetooth-адаптер с поддержкой активного соединения или активный Bluetooth-прокси Home Assistant. Включите диффузор.

### Подключение в четыре этапа

<p align="center"><img src="docs/assets/connection-four-steps.png" alt="Четыре этапа: поиск диффузора, вход Xiaomi, проверка BLE-токена и локальное управление" width="100%"></p>

1. **Поиск** — откройте **Настройки → Устройства и службы → Добавить интеграцию → Xiaomi SO Diffuser BLE** и выберите именно свой диффузор. Если он не обнаружен, используйте ручной ввод Bluetooth-адреса.
2. **Авторизация** — войдите в аккаунт Xiaomi и выберите **тот же физический прибор**. Для моделей кроме S5 подтвердите предупреждение об экспериментальной совместимости, если принимаете ограничения.
3. **Проверка** — интеграция автоматически проверяет токен конкретного устройства через BLE-аутентификацию GATT. Токен сохраняется только после успешной проверки.
4. **Управление** — проверьте **Вкл/Выкл** на реальном приборе, прежде чем создавать автоматизации. После настройки обычные команды работают локально по Bluetooth, без Xiaomi Cloud.

Если Xiaomi возвращает на недоступный `homeassistant.local`, замените **только адрес сервера в конечной ссылке браузера** на свой адрес HA. Путь вебхука и параметры авторизации не изменяйте. Ссылку с кодом никому не отправляйте.

## Совместимость моделей

- **S5 — есть подтверждение работы на реальном устройстве**
- **S1, S1 Pro, S2, S6, S7, S8, S9, S19 — экспериментальные профили BLE**

Подсветка: **Постоянный свет**, **Автоматический градиент** (встроенный), **Смена цветов (HA)** и **Закат (HA)**. Программным эффектам нужна работающая связь.

## Документация

[Установка](docs/ru/INSTALLATION.md) · [Совместимость](docs/ru/COMPATIBILITY.md) · [Миграция](docs/ru/MIGRATION.md) · [Документация](docs/ru/README.md) · [История изменений](CHANGELOG.md)

---

[MIT](LICENSE)

*Независимая разработка сообщества. Проект не связан с Xiaomi или Home Assistant.*

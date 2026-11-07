# SO Smart Aroma Diffuser S5 — HCI capture analysis

Дата обновления: 2026-11-06. Анализ выполнен по пользовательскому HCI capture и соответствующим скриншотам Mi Home. Исходный capture не включён в публичный проект.

## Краткий вывод

В трассе есть успешное FE95 GATT connection и secure-login `A4` → AUTH `0019` → `CMD_LOGIN`/`CFM_LOGIN_OK`. Локальный `token` прошёл оба HMAC-SHA256 proofs и все 272 AES-CCM tags; это подтверждает кандидатный key schedule для этих кадров, но не физическое действие. Yunmi reference A и MiAuth используют общий Xiaomi `mi` token-login family, однако S5 отличается от Yunmi отсутствием post-login `F0` и другим chunk sizing; ни один reference не является готовым S5 sender.[25][40][41]

`ble_key` не прошёл оба GATT login proofs и не является проверенным GATT login token. В pinned token extractor поля `device["token"]` и `BLE_DATA.beaconkey` разделены; HA's pinned `xiaomi-ble 1.16.1` parser принимает отдельный `bindkey` для encrypted MiBeacon payloads.[34][35][46] Это не устанавливает равенство локального `ble_key` с `bindkey` или его необходимость для S5: advertising reports не коррелированы с GATT peer, а S5 advertising decrypt не проверялся. Атрибуция соединённого peer к S5 по-прежнему опирается на пользовательский контекст и FE95 profile, а не на прямую address correlation. Ни один секрет или derived key не включён в документы.

## Формат и целостность файла

| Проверка | Результат |
|---|---|
| Размер | 132 932 байта |
| SHA-256 | `6c8e321a505da60e99efcb45d387056a268e9b965a598c6f3edbb02b3883ab31` |
| Заголовок | magic `btsnoop\0`, version `1`, datalink `1002` (HCI UART/H4) |
| Записи | 2 137 полных records: 111 HCI Command, 644 HCI ACL Data, 1 382 HCI Event |
| Целостность записи | 0 усечённых записей, 0 заявленных dropped packets, 0 хвостовых байтов |
| Временной диапазон | 2026-11-04 00:40:57.388–00:45:29.565 UTC (272.177 с) |

Это host-side HCI snoop, не RF over-the-air capture. Он позволяет читать HCI/GATT ATT-трафик, но не показывает эфирные повторы и сам по себе не доказывает, что каждый наблюдаемый advertising report относится к подключённому peer.

## Соединение и GATT

- В `00:40:58.952 UTC` зарегистрирован один успешный LE Connection Complete: роль central, connection handle в отчёте намеренно не публикуется. В конце файла нет события disconnect; состояние после остановки захвата неизвестно.
- Обнаружены сервисы `0x1800`, `0x1801` и `0xFE95`; `0x180F` отсутствует.
- FE95 value handles восстановлены из ATT discovery. Это handles данной сессии, не постоянные адреса характеристик:

| UUID | Value handle | Объявленные свойства |
|---|---:|---|
| `0004` | `0010` | read |
| `0005` | `0012` | read, notify |
| `0010` | `0015` | write without response, notify |
| `0019` | `0018` | write without response, notify |
| `0017` | `001B` | write, notify, extended properties |
| `0018` | `001E` | write without response, notify, extended properties |
| `001A` | `0021` | write without response, notify |
| `001B` | `0024` | write without response, notify |
| `001C` | `0027` | write without response, notify |

UUID set/properties согласуются с read-only GATT inventory из HA probe. Отдельно в начале сессии есть дополнительный обмен на `001C`; его payload/назначение здесь не установлены.

### Advertising и идентификация peer

Захвачено 942 extended-advertising reports, но они используют один random-address/type tuple, не совпадающий с public-address tuple в Connection Complete; в этих reports не найден FE95 service-data AD element. Ни один адрес не сохраняется или печатается. Поэтому адресная привязка рекламы к подключённому peer **не подтверждена**. FE95 GATT и временное совпадение со скриншотами поддерживают атрибуцию к сессии Mi Home, но не заменяют прямую адресную корреляцию.

## Secure login и сравнение протоколов

Наблюдаемые кадры на FE95:

| Время UTC | Направление/канал | Наблюдение |
|---|---|---|
| `00:41:01.017` | host → `0010` | Write Command `A4` (1 байт), auth-init |
| `00:41:01.098`, `.197` | peer → `0019` | два AUTH frame с marker `00 00 04` (длины 6 и 244 байта; секретные продолжения опущены) |
| `00:41:01.122`, `.219` | host → `0019` | два точных protocol echo с marker `00 00 05`; тела совпадают после замены marker, значения не раскрыты |
| после auth-init | `0019` | подтверждены send-key/send-info headers, 16-byte random-key parcel, 32-byte login-info parcel, peer remote-key/remote-info frames и RCV_RDY/RCV_OK control flow; байты ключей/HMAC скрыты |
| `00:41:01.452` | host → `0010` | `CMD_LOGIN` = `24 00 00 00` |
| `00:41:01.928` | peer → `0010` | `CFM_LOGIN_OK` = `21 00 00 00` |

Последовательность `A4` → AUTH `0019` → `CMD_LOGIN`/`CFM_LOGIN_OK` и key/info exchange совпадают с token-based login family, описанной в Yunmi reference A.[24][25]

MiAuth независимо использует ту же `mible-login-info`/HMAC crypto family, но его исходники не доказывают полного совпадения wire handshake с S5.[39][40][41]

Принятый login marker сам по себе не доказывает key schedule; отдельное подтверждение дают оба проверенных HMAC proofs и все AEAD tags ниже. `authType=4` в plugin bundle остаётся отдельной OTA-настройкой и не является основанием auth-вывода.

Важная оговорка: XW002-код тоже отправляет начальный `A4`, поэтому сам `A4` не различает модели. Его дальнейший путь использует P-256 ECDH/`gatt_ltmk`, отдельный `0x50` login и UUID `0016` с MNG/CTR framing.[26][28] В S5 capture после `A4` идут `0019` AUTH frames и `CMD_LOGIN`/`CFM_LOGIN_OK`; UUID `0016` и XW002 `0x50` login request не наблюдаются. Это исключает данный XW002 flow из этой трассы, но не переносит автоматически Yunmi application layer на S5. Общие `001A/001B` или ACK-байты не являются основанием переносить XW002 crypto/payload.

В HCI event stream нет SMP L2CAP CID `0x0006`, LE LTK-request subevent или HCI Encryption Change / LE Start Encryption: link-layer pairing/encryption в записи не наблюдается.

Reference A выводит 64-byte material через HKDF-SHA256 с `salt=rand||remote_key`, `info=mible-login-info`; login proofs — HMAC-SHA256, data — AES-CCM с 4-byte tag, без AAD, nonce=`IV4||00000000||counter_LE32`.[25]

MiAuth использует тот же login family, но его post-login commands идут в собственном M365/UART framing `55AB` с AES-CCM и CRC16, а не как S5 MIoT Spec-v2 packets.[39][40][41]

В защищённой локальной проверке S5 token воспроизвёл оба HMAC proofs, а 3 исходящих и 269 входящих data frames прошли AES-CCM authentication (272/272 tags). Это подтверждает crypto profile для данной capture, не совместимость чужого application sender со всеми S5 sessions.

## MIoT data-channel traffic и offline decoder

После login на `001A/001B` наблюдаются три завершённых однопакетных исходящих transfer. Offline decoder проверил login proofs и AEAD tags, затем расшифровал payload; ciphertext, token и derived keys не выводятся:

| Время UTC | `001A` parcel write | Counter из parcel | Authenticated MIoT request | Ближайшая 21-byte notification, `001B` |
|---|---:|---:|---|---|
| `00:43:05.427` | 21 байт | `0` | SIID 3 / PIID 5, uint16 = `2054` | `00:43:05.606`, counter `124` |
| `00:43:21.074` | 21 байт | `1` | SIID 3 / PIID 5, uint16 = `4095` | `00:43:21.208`, counter `141` |
| `00:43:27.853` | 20 байт | `2` | SIID 3 / PIID 7, uint8 = `255` | `00:43:27.934`, counter `149` |

У всех запросов перед parcel есть 6-byte header `00 00 00 00 01 00`, затем `RCV_RDY`; parcel имеет index `01 00`, 16-bit little-endian counter и encrypted bytes, затем приходит `RCV_OK`. После успешной аутентификации распарсены три single-property MIoT Spec-v2 requests, как указано в таблице. Reference A дробит payload на chunks по 18 байт; в S5 первые два payload после parcel index имеют по 19 байт и переданы одним parcel. Поэтому crypto profile совпал, но framing/chunk policy не является drop-in sender.[25]

В capture ровно шесть исходящих Write Commands на handle `0021`/UUID `001A`: три header+parcel пары; до первого запроса через ~2 минуты после login на `001A` записей нет. В частности, отсутствует encrypted `F0`, который reference A отправляет сразу после `CFM_LOGIN_OK`. Это отдельное различие уровня post-login application flow; оно не опровергает общий login family и не позволяет переносить поведение kettle-драйвера на S5.[25]

Входящие direct notifications имеют prefix `00 00 02 00`, затем 16-bit little-endian counter и ciphertext+tag. Из 269 кадров — 266 значений ATT length 74 (encrypted part 68 байт) и 3 length 21 (encrypted part 15 байт); для 4-byte tag candidate это plaintext длины 64 и 11. Counters содержат каждый номер `1…269` ровно один раз, но HCI record order не монотонен: три коротких frames `124/141/149` стоят перед длинными `123/140/148`. Поэтому decoder использует counter из каждого кадра, а не предполагает счётчик по порядку записей. Все 269 кадров получают `00 00 03 00` ACK; ACK — только transport/protocol evidence, не физическое выполнение.

XW002 path не переносится: он использует P-256 ECDH/`gatt_ltmk`, собственные HKDF/nonce и login на `0016`; в S5 capture нет `0016` или `0x50` login request.[26][28] В S5 bundle property requests идут через native `Bluetooth.spec.setPropertiesValue`; crypto derivation в проверенных extracted JS modules не найден.

## MIoT schema и mapping из исходного bundle

Для точного URN `urn:miot-spec-v2:device:diffuser:0000A01E:bwj-s5:1` локально сверена cache schema version 1/minor 1, `_updated_time=2026-11-03T03:59:34Z`. Это MIoT schema mirror/cache, не firmware source. Во всех свойствах ниже generic MIoT `access=[]`; отдельное `gatt-access` — extension. Schema не содержит unit для временных значений.[29][30][32]

| Schema name | SIID/PIID | Format; range/enum | `gatt-access` | Extracted bundle key |
|---|---:|---|---|---|
| `status` | 2/1004 | uint8; Off=0, On=1 | read/write/notify | `workStatus` (`prop.2.1004`) |
| `fragrance-out-time` | 3/3 | uint8; 3–30, step 1 | read/write/notify | `fragranceOutTime` |
| `idle-time` | 3/4 | uint8; 0–30, step 1 | read/write/notify | `idleTime` |
| `auto-power-on` | 3/5 | uint16; 1–65535, step 1 | read/write/notify | `autoPowerTime` |
| `unixtime` | 3/6 | uint32; 1–4294967295, step 1 | write only | `prop.3.6` not present in checked UI map |
| `repeat` | 3/7 | uint8; 0–255, step 1 | read/write/notify | `repeat` |
| `light` | 3/8 | uint8; 0–255, step 1 | read/write/notify | `light` |
| `color` | 3/9 | uint32; 0–16777215, step 1 | read/write/notify | `color` |

The exact plugin mapping appears in extracted `module_10025.js`; `module_10226.js` uses bit `128` as its UI `timeSwitch` flag for `repeat`. This is plugin behavior, not a proven firmware semantic. Captured `auto-power-on` values `2054` and `4095` are not converted to time units; `repeat=255` remains a raw value. `unixtime` is schema-marked write-only and was not present in the checked UI map; do not use it for any read/restore assumption.

The three transactions align in time with provided Mi Home screenshots (`00:42`–`00:43`), but those screenshots do not independently establish physical effect. `SetPropertyResp code=0` and matching `PropertyChanged` values are protocol/property read-back only.

## Pinned upstream source audit (comparative, not driver reuse)

| Upstream | Exact pinned commit | Source-level finding and S5 boundary |
|---|---|---|
| `hass-yunmi-kettle-ble` | `0b3db91e30c7b1cafe287c7c049c481e233ddef1` | Reference A implements the token HKDF/HMAC/CCM family and post-login `F0`/18-byte chunk policy. S5 passes crypto checks but lacks `F0` and has 19-byte parcels; not a drop-in sender.[24][25] |
| `miauth` | `7df4f35c258f926ce396df3691d7f91d86ad761e` | Its `micrypto.py`/`miclient.py` implement the same token-based `mible-login-info` + HMAC login family, then a separate M365/UART `55AB`/AES-CCM/CRC16 data envelope; not an S5 MIoT Spec-v2 sender. Exact full SHA verified.[39][40][41] |
| `Xiaomi-cloud-tokens-extractor` | `c4db715dace9806e905153c2977608873e8ab7c9` | A credential extractor, not a BLE transport implementation; `token` and `BLE_DATA.beaconkey` are emitted as separate fields.[34][35] |
| `xiaomi-diffuser-ble` (XW002) | `96268a53e3c8ba4443dd322ecaede606ec7c89c6` | XW002-specific P-256 ECDH/`gatt_ltmk`, UUID `0016` and `0x50` path; the trace shares only the initial `A4`, not those later steps.[26][27][28] |

The pinned HA `xiaomi-ble 1.16.1` parser accepts a `bindkey` for encrypted MiBeacon advertisement parsing.[46] That API field is not proven equivalent to the extractor's `BLE_DATA.beaconkey` or the local `ble_key`; with no S5 advertising-to-GATT peer correlation, the local `ble_key` is disproven only as the captured GATT login token, not established as required or unnecessary for S5 advertisement decryption.

## Доступ без token и граница Cloud-независимости

- В уже выполненном read-only GATT probe подключение к FE95 candidate и перечисление GATT services прошли без secure login; proprietary MIoT reads не выполнялись. Это подтверждает только link/service discovery, не доступность свойств до авторизации.
- В capture есть advertising reports, но нет прямой address/service-data correlation с подключённым GATT peer; S5 MiBeacon payload не расшифровывался. Безтокенная видимость/семантика рекламы для этого S5 остаётся неизвестной.
- Три расшифрованных операции идут как локальный GATT/MIoT data-channel traffic после token login. HCI capture не показывает параллельную IP/WAN-активность, поэтому он не доказывает полную Cloud-независимость приложения; WAN-off тест, срок жизни и обновление token не проверялись.

## Offline decoder and client tests

`tools/s5_payload_decoder.py` accepts token bytes only in memory, verifies both login HMAC proofs before AES-CCM, and parses the actual MIoT Spec-v2 SetProperty, SetPropertyResp and PropertyChanged layouts. It never returns token, session keys or ciphertext bytes. `tools/verify_capture.py` reads a private 0600 token file and prints only redacted verification status and decoded property metadata.

Re-run during preparation against the supplied capture produced:

- Login HMAC proofs: verified.
- TX: 3/3 frames authenticated and parsed.
- RX: 269/269 frames authenticated and parsed.
- RX message types: 266 PropertyChanged and 3 SetPropertyResp.
- SetPropertyResp transaction IDs match the three requests; result codes: 3/3 zero.
- PropertyChanged values: 2,394 decoded.
- TX properties: `3.5=2054`, `3.5=4095`, `3.7=255`.

The production client in 0.3.0 exposes only fixed setters for `2.1004`, `3.3`, `3.4`, `3.8` and `3.9`. The historical `3.5`/`3.7` values remain in this capture analysis but timer/schedule setters have been removed from the HA integration. Fake-GATT tests verify command framing, successful response handling and matching read-back; they do not prove physical action.

The current standalone project test run passed 57 tests and 48 subtests. The raw capture and token are not part of the public project.

## HA integration status

Version 0.2.0 was previously installed as a development baseline and registered 26 entities, including timer/schedule controls. Version 0.3.0 removes those controls and has not yet been installed on the live Home Assistant instance. The previous deployment's host, backup paths and other private operational details are intentionally omitted from this public research note.

## Conclusions and remaining limits

**Confirmed for this capture:** btsnoop integrity, FE95 GATT handles, token-based login HMAC proofs, 272/272 AES-CCM tags, three decoded MIoT SetProperty requests, three successful SetPropertyResp codes, 266 PropertyChanged messages and the original UI property mappings.

**Not confirmed:** direct address attribution of the connected GATT peer; physical effect of `3.3`, `3.4`, `3.8` and `3.9`; visible brightness/OFF behaviour; spray cadence; LongSpray behaviour; authenticated live read-back after an independent HA connection; token expiry/rotation; and full WAN-off operation. User-reported RGB operation is not an independent hardware acceptance test.

No new BLE scan, pairing, reset or physical property write was performed while preparing the 0.3.0 source. Do not treat ACKs, SetPropertyResp, PropertyChanged or synthetic tests as proof of physical effect.


## Sources

[24] https://github.com/opravdin/hass-yunmi-kettle-ble/blob/0b3db91e30c7b1cafe287c7c049c481e233ddef1/PROTOCOL.md — Yunmi kettle BLE protocol at pinned commit
[25] https://github.com/opravdin/hass-yunmi-kettle-ble/blob/0b3db91e30c7b1cafe287c7c049c481e233ddef1/custom_components/yunmi_kettle/protocol.py — Yunmi kettle auth implementation at pinned commit
[26] https://github.com/clairefiorettiythzr6802-eng/xiaomi-diffuser-ble/blob/96268a53e3c8ba4443dd322ecaede606ec7c89c6/python/miot_ble_specv2.py — XW002 MIoT BLE Spec-v2 at pinned commit
[27] https://github.com/clairefiorettiythzr6802-eng/xiaomi-diffuser-ble/blob/96268a53e3c8ba4443dd322ecaede606ec7c89c6/python/bridge.py — XW002 bridge at pinned commit
[28] https://github.com/clairefiorettiythzr6802-eng/xiaomi-diffuser-ble/blob/96268a53e3c8ba4443dd322ecaede606ec7c89c6/python/channel.py — XW002 channel/auth implementation at pinned commit
[29] https://miot-spec.org/miot-spec-v2/instance?type=urn%3Amiot-spec-v2%3Adevice%3Adiffuser%3A0000A01E%3Abwj-s5%3A1 — MIoT spec instance for exact SO S5 URN
[30] https://iot.mi.com/new/doc/accesses/direct-access/other-platform-access/control-api — Xiaomi IoT Control API / MIoT-Spec documentation
[32] https://home.miot-spec.com/spec/bwj.diffuser.s5 — Community MIoT schema mirror for bwj.diffuser.s5
[34] https://raw.githubusercontent.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/v1.5.1/token_extractor.py — Xiaomi Cloud token extractor pinned source
[35] https://raw.githubusercontent.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/v1.5.1/README.md — Xiaomi Cloud token extractor pinned README
[39] https://github.com/dnandha/miauth/blob/7df4f35c258f926ce396df3691d7f91d86ad761e/doc/README.md — MiAuth BLE authentication protocol/crypto documentation
[40] https://github.com/dnandha/miauth/blob/7df4f35c258f926ce396df3691d7f91d86ad761e/lib/python/miauth/mi/micrypto.py — MiAuth Python crypto implementation
[41] https://github.com/dnandha/miauth/blob/7df4f35c258f926ce396df3691d7f91d86ad761e/lib/python/miauth/mi/miclient.py — MiAuth Python BLE client implementation
[46] https://raw.githubusercontent.com/Bluetooth-Devices/xiaomi-ble/416fc828fc2a008f7fcab14513c27e50bb782099/src/xiaomi_ble/parser.py — Bluetooth-Devices xiaomi-ble v1.16.1 MiBeacon parser, pinned commit 416fc828
[49] https://raw.githubusercontent.com/home-assistant/core/2026.10.4/homeassistant/components/bluetooth/api.py — Home Assistant Core 2026.10.4 Bluetooth API

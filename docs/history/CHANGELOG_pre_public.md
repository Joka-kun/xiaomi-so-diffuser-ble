# Changelog

## 0.6.2 — primary switch and optional software color palettes (2026-11-07)

- Rename the scent-diffuser power entity from **Work mode** to **On/Off** (Russian: a concise on/off label). Keep its original `power` unique ID and MIoT setter. The Russian control name alphabetically precedes Backlight in the standard HA device list; user-customized entity names may override this order.
- Offer two additional **HA-driven** light effects: **Color Cycle** and **Sunset**. Each starts only when selected, sends an existing bounded `3.9` RGB command no more often than every eight seconds, and stops on lighting off, BLE disconnection or unload.
- Preserve **native Automatic Gradient** as the recommended standalone hardware effect, with no extra BLE mode values. HA palettes are not guaranteed to work without running HA and a live local BLE session.
- Add async regression tests for switching effects, rejecting invalid RGB combinations, task cancellation, BLE disconnect and stable entity IDs.
- A user confirmed the native gradient works on their S5; physical acceptance of these new HA palettes and final device-page ordering is still outstanding.

## 0.6.1 — simpler setup and native RGB effect in Home Assistant (2026-11-07)

- Renamed the main on/off entity to **Work mode** because it controls diffuser operation, while the RGB backlight is independent. Preserved entity unique IDs and MIoT command mapping.
- Fixed the missing `LightEntityFeature.EFFECT` declaration. Home Assistant now exposes the previously implemented **Automatic Gradient** color cycle in the light effects menu, using the existing `3.8 = 238` hardware command. During the gradient the light reports ON/OFF color mode rather than an adjustable static RGB color. No new protocol writes were invented.
- Simplified English/Russian onboarding instructions, removed the lengthy hardware confidence note from the cloud-device selection page, and added concise guidance for replacing an unreachable `homeassistant.local` hostname **in the final OAuth browser callback**, keeping the path and parameters intact.
- Added device-on and Mi Home / phone-Bluetooth contention advice. Separated **BLE connection failure** from **GATT token-proof failure** so a busy link does not incorrectly imply an invalid token.
- Updated the six language READMEs and added regression tests for effect discovery and BLE failure-stage classification. **Hardware acceptance of this update remains pending.**

- Standardized active technical documentation and the changelog to English prose while preserving machine-readable identifiers, protocol evidence and historical measurements.
- Added dedicated Russian installation, compatibility, migration and documentation-index pages; the Russian README now links to Russian guidance rather than English pages with untranslated captions.
- Localized navigation labels and illustration captions across six READMEs. The GitHub language selector retains native-spelling language names; its summary uses the current page's language.
- Split the HCI investigation into a canonical English analysis and a preserved Russian-language source. Historical UI labels in archived English reports were translated for readability; the originals remain in Git history.
- Added [documentation language policy](docs/LANGUAGE_POLICY.md) and regression tests for Cyrillic prose in active English docs, missing translations and broken localized links.
- The documentation-localization changes below did not alter BLE commands or credentials; the 0.6.1 UI changes above are listed separately.

## 0.6.0 — multilingual documentation and expanded SO experiments (2026-11-07)

- Simplified all six public README pages (English, Russian, German, Spanish, French, Simplified Chinese). Removed old-domain upgrade instructions and legacy token file paths from the public landing pages; the separate technical migration/credential references remain available for existing installations.
- Enabled the documented MIoT idle-time special value `3.4 = 0` for all nine SO family profiles, **only after the existing experimental opt-in and live BLE authentication for non-S5 devices**. The non-S5 switch is explicitly labelled as an experimental zero-pause control. S5's continuous-mode switch and entity unique IDs are unchanged. Actual physical spray cycle on relatives remains unknown.
- Added an always-readable read-only **BLE connectivity diagnostic binary sensor** for troubleshooting transport problems without any extra GATT writes.
- Retained common spray controls, battery/charging and RGB/gradient where the published model schema supports them; S1/S19 remain without RGB, S1 Pro temperature remains read-only. No speculative native schedule register writes were added.
- Extended offline regression tests for exact model gates, six public language links, the zero-pause label, BLE diagnostic availability and HA platform lifecycle. The existing per-address BLE token file remains unchanged.
- Updated compatibility, architecture, installation, testing, status and roadmap docs. This version is still **experimental**; no new physical model acceptance has been performed.

## 0.5.0 — general SO diffuser domain and repository cleanup (2026-11-07)

- **BREAKING CHANGE:** integration folder and domain renamed from `so_s5` to **`so_diffuser_ble`**. Home Assistant does not automatically migrate config entries across domains. Existing users must back up HA, remove the old entry via the UI, install the new single HACS integration and verify entity IDs/automations. See [migration instructions](docs/MIGRATION.md).
- Existing GATT credential filenames remain **unchanged and readable** to preserve working token material. The integration neither deletes nor prints them.
- The setup flow now checks for a still-registered `so_s5` entry controlling the same BLE address and refuses duplicate connections. Known advertised model and selected Xiaomi Cloud model must agree.
- Reorganized public documentation into a concise illustrated English README, a full Russian README, model matrix, docs index and single migration/installation guides.
- Added original SVG model-family and migration diagrams beside the existing hero/connection-flow assets; no proprietary product photos or unverified compatibility claims.
- Archived superseded S5-only onboarding notes and dated status/roadmap snapshots under `docs/history`. Test and research evidence retained.
- Kept exactly **one** `custom_components` integration directory as required by HACS. Current generic-domain source is **not yet accepted on physical hardware**; only earlier S5 code has user-reported live success.
- **Still pending:** owner-selected LICENSE, a real S5 migration regression and proof of Bluetooth authentication/control on relatives.

## 0.4.0 — experimental SO-family model provisioning (2026-11-07)

**New source capabilities, not a stable hardware-certified release.** The operator has not installed or run this multi-model build.

- Studied Xiaomi Miot, official Xiaomi Home, built-in Xiaomi BLE, Scent Assistant, SmartAromaDiffuser and the independent Xiaomi diffuser BLE/MQTT bridge. Documented the key failure mode: Xiaomi Cloud can list a BLE device and publish MIoT property schemas without providing any working local command transport.
- Added exact `ModelProfile` registry for **nine SO/BWJ models**: field-reported S5, plus experimental S6, S2, S7, S8, S9, S1 Pro, S1 and S19. Public sources: Xiaomi MIoT-Spec property catalog; **no new BLE hardware compatibility was proven**.
- Extended OAuth device enumeration to exactly those model IDs, with token-length validation. S5-only helper is kept for compatibility; no global Xiaomi device-category scanner.
- Added `experimental_confirm` step requiring affirmative opt-in when trying a non-S5 model. The selected real BLE device must complete the existing Standard Auth challenge before the per-address token is saved. Unknown models and unapproved config entries fail closed.
- Stored `miot_model` and `experimental_protocol` alongside the BLE address in new HA entries. Existing S5 entries lacking these fields continue to default safely to S5. Public integration domain `so_s5`, device unique IDs and existing stored GATT tokens remain unchanged.
- Added exact additional BLE advertisement IDs and manual Bluetooth-address fallback. Advertised names/PIDs on physical relatives still require verification.
- Added capability-aware entities: do not create RGB lights for S1/S19; S1 Pro may show read-only signed temperature `3.10` if notified; the S5-only `LongSpray` switch is hidden on all unvalidated relatives. No native schedule or arbitrary SIID/PIID setters added.
- Added regression tests for the catalog, experimental opt-in, cloud model filtering and coordinator/profile behaviour. CI: **90 pytest tests + 64 subtests passed**, Python compilation and Hassfest passed; HACS still fails the pre-existing missing-license requirement.
- Added [multi-model design and analogous-project research](docs/MULTI_MODEL_ARCHITECTURE.md); updated README, status, roadmap, onboarding, installation, tests and protocol docs.
- **Known limitation:** the BLE transport is still derived from S5; related models may fail authentication or have differing light/spray command semantics even when their MIoT property maps match. Hardware proof is required **per model** before claiming full support.

## Unreleased — first live OAuth success and UX research (2026-11-07)

- **Field success reported:** after a clean S5 installation with no legacy token or `so_s5` config entry, the operator completed real Xiaomi OAuth2 sign-in and reports the diffuser works. The automatic callback required changing only the final **browser** URL hostname from an unreachable `homeassistant.local` to the HA LAN host, preserving the callback path and authorization parameters. No one-time code/token is included in project files.
- **Confirmed token provenance in source:** a temporary Xiaomi OAuth access token retrieves the selected S5's **12-byte device GATT token**; the integration performs a real BLE auth proof and saves that per-address token. Future BLE sessions use the saved GATT token, not OAuth credentials and not the previous legacy token (which was absent during initial setup).
- **UI:** changed the main on/off switch from a device-name label to a dedicated **Power** label, retaining its existing entity unique ID and stateful on/off behavior. Bumped the development manifest to **0.3.1** for users updating the HACS-installed source; no stable release has been published. Kept the vendor `LongSpray` mode as a separate continuous-mode control.
- **User onboarding:** updated RU/EN help strings to remove obsolete token-file prerequisites and explain the observed LAN-host callback workaround. The separate manually pasted-URL fallback has not been field-tested.
- **Protocol review:** `LongSpray` writes `3.4=0` (special zero pause) without changing `3.3` pulse duration. The exact physical duty cycle is still unmeasured; the operator reports possible irregular spray. The last normal pause is RAM-only and may revert to 3 minutes after HA restart.
- **Potential model expansion:** published SO S2/S7/S8/S9 MIoT property schemas closely match S5, while S1/S19 have reduced light capability. BLE authentication and device-specific capabilities remain **unverified**; no additional model was enabled.
- **Scheduling decision:** keep device-native unverified timer masks disabled and rely on HA automations by default; consider optional autonomous scheduling after detailed capture-backed tests.
- Added [spray modes, model-compatibility and schedule report](docs/SPRAY_MODES_AND_COMPATIBILITY.md), updated protocol, installation, status, onboarding and roadmap. This milestone does **not** establish post-reboot/WAN-off acceptance or a stable release.

## Unreleased — verified local installation baseline (2026-11-07, documentation)

- Recorded an operator-supplied, read-only HA Docker audit after intentional removal of the old component and token: both token files and the `so_s5` component directory are absent, with **zero** persisted `so_s5` configuration entries.
- Confirmed the new source manifest's **display name `Xiaomi SO Diffuser BLE`** and **domain `so_s5`**; the earlier removed installation's historical display name cannot be recovered from the deleted manifest.
- The checked instance must follow **fresh Add integration** after installation and HA restart; **Reconfigure** remains the supported path for other installations with an existing `so_s5` entry.
- No live OAuth, cloud device list, BLE token validation, component installation or physical control acceptance took place during this file-only audit. The deleted old token cannot provide a fallback on this instance.
- Updated [deployment audit](docs/history/DEPLOYMENT_AUDIT_2026-11-07.md), [status](docs/STATUS.md), [installation](docs/INSTALLATION.md), [onboarding](docs/history/ONBOARDING_2026-11-07.md), and [roadmap](ROADMAP.md) while keeping private host/device data out of public files. **No runtime code changes** in this documentation update.

## Unreleased — Xiaomi OAuth token onboarding and S5 switch naming

- Implemented one-time browser-based Xiaomi OAuth2 authorization from HA's config flow, state-validated expiring callback, region selection and device-token retrieval via paginated Xiaomi Home API.
- Filter cloud candidates by exact `bwj.diffuser.s5` model and validated 24-hex GATT token; require a fresh real S5 BLE login before storing it.
- Save only private per-Bluetooth-address GATT tokens in `/config/.storage/so_s5_ble_tokens.json` with mode 0600. OAuth access/refresh credentials and account passwords are **not persisted**.
- Keep the previous `/config/so_s5_token` as a fallback; new **Reconfigure** flow allows existing devices to migrate without losing entity IDs or automations. No automatic deletion of a working token.
- Earlier in the development cycle, the power switch used a generic on-label and then the device name; the original continuous-mode switch retained its unique ID.
- Added mock tests covering OAuth callback state/replay protection, cloud device/token filters, pagination, storage permissions and migration. GitHub CI on 2026-11-07: **80 pytest tests + 56 subtests passed**, compileall and Hassfest passed; HACS only fails due to the absent license. **Live Xiaomi account + physical BLE acceptance remain pending.**
- Xiaomi OAuth sign-in uses Xiaomi's browser page, not an embedded QR image. Automatic return uses `homeassistant.local:8123`; a separate manually pasted callback URL with strict URI/state checks supports Docker setups without mDNS.
- Existing project license is still missing, blocking HACS validation.

## Unreleased — BLE behaviour fixes and discovery improvements

- Earlier in this development cycle, the power entity was renamed several times. Its unique ID was preserved, as was the separate S5 continuous-mode entity.
- Fixed the false `S5 property read-back did not match the request` error caused by stale PropertyChanged notifications arriving before a matching final value. Still requires a successful response and exact matching read-back or times out.
- Added regression coverage for updated switch labels; existing synthetic stale-notification tests cover pause and power.
- Recorded the user’s direct observation that `3.4 = 0` causes continuous spraying on their SO S5, with repeat hardware acceptance pending.
- Clarified that a saved `/config/so_s5_token` is still necessary and should not be deleted before a verified new provisioning flow.
- GitHub Actions on 2026-11-07: **63 pytest tests and 48 subtests passed**; Hassfest passed. HACS still needs an approved project license; repository topics are configured.

- Updated [project status](docs/STATUS.md) with a user-reported S5 discovery observation and a code-level explanation of BLE token authentication; the physical meaning of the former LongSpray mode was subsequently confirmed by the user as continuous spraying.

- Added a conservative Home Assistant Bluetooth discovery matcher for specifically identified S5 advertisements.
- Added automatic discovery confirmation, a nearby-device chooser, and manual address fallback.
- Added English and Russian setup translations and regression checks.
- The initial Bluetooth discovery phase preceded the new OAuth2 onboarding code described above; see [current onboarding](docs/history/ONBOARDING_2026-11-07.md).


## 0.3.0 — 2026-11-06

### Repository publication
- Initial public source tree prepared for `Joka-kun/xiaomi-so-diffuser-ble` with tests, HACS metadata, bilingual translations, and CI workflows.
- This is a development build; physical hardware acceptance, license selection, and stable GitHub release are pending.


### Changed
- Removed the timer master, 12 two-hour schedule windows and seven weekday switches.
- Removed `3.5` auto-power-time and `3.7` repeat setters from the production allowlist.
- Replaced the pause dropdown with a 3–30 minute number slider and a separate LongSpray switch (`3.4 = 0`).
- Reworked the light entity to follow the original Mi Home bit-field semantics.
- Added exact cleanup of retired timer/schedule/select entity-registry entries; the Power entity is retained.

### Fixed
- HA brightness is mapped to the S5 1–100 range; zero is treated as OFF.
- OFF clears the light enable bit while retaining the last mode/level; ON restores it.
- Automatic Gradient mode no longer reports a false 100% brightness value.
- RGB writes are blocked in Automatic Gradient mode and can be combined with a brightness request that switches back to steady mode.
- The offline decoder now parses the actual MIoT Spec-v2 request/response/notification layouts instead of a stale candidate envelope.

### Added
- Safe importer for Xiaomi Cloud Tokens Extractor JSON. It writes only the 24-hex-character S5 GATT token and enforces mode 0600.
- Offline capture verifier that never prints token, BLE key, derived keys or ciphertext.
- Tests for light state transitions, LongSpray/pause behaviour, credential import and entity-registry migration.

### Validation
- 57 pytest tests passed; 48 subtests passed.
- Supplied HCI capture: both login HMAC proofs verified; 3/3 TX and 269/269 RX AES-CCM tags authenticated; 266 PropertyChanged and 3 SetPropertyResp frames parsed; all response transaction IDs matched and all three result codes were zero.
- No 0.3.0 physical-device test or live HA deployment was performed.

## 0.2.0 — historical baseline

- Initial HA-native active BLE control client with token-based S5 authentication.
- Power, timing, schedule, light and sensor entities.
- Authenticated property writes waited for SetPropertyResp and exact PropertyChanged read-back.

The historical 0.2.0 deployment notes are not the current 0.3.0 feature description.

# Documentation language and terminology policy

**Canonical technical documentation: English.** The main technical guides, protocol analyses, changelog, roadmap, source-code comments and tests are authored in English. A technical identifier (such as `MIoT`, `BLE`, `OAuth2`, `SIID/PIID`, `bwj.diffuser.s5` or a Python symbol) is preserved unchanged in every language.

**User-facing translations: one language per page.**

| Language | Entry point | Installation / compatibility / migration |
| --- | --- | --- |
| English | [README](../README.md) | [Technical docs](README.md) |
| Russian | [Russian README](../README_RU.md) | [Russian guides](ru/README.md) |
| German | [German README](../README_DE.md) | Extended technical docs are in English |
| Spanish | [Spanish README](../README_ES.md) | Extended technical docs are in English |
| French | [French README](../README_FR.md) | Extended technical docs are in English |
| Simplified Chinese | [Simplified Chinese README](../README_ZH_CN.md) | Extended technical docs are in English |

Six actively maintained README languages: English, Russian, German, French, Spanish and Simplified Chinese. The centered language selector uses native-language text links between the cover and status badges. Each public README includes the same two approved illustrations: the cover and the four-step connection graphic. Older Italian, Japanese and Brazilian Portuguese drafts are preserved in Git history, but are no longer part of the current documentation set.

## Editorial rules

1. Write complete paragraphs, headings, lists and link captions in the page's declared language. **Do not** mix English documentation link captions into Russian, German, Spanish, French or Chinese guides.
2. Product names and machine-readable identifiers are not translated. Avoid translating API keys, model IDs, filesystem paths, GitHub actions, `GATT` packet fields or numeric property numbers.
3. In English technical docs, describe user-interface entities in English (for example **Power**, **Spray pause**, **Experimental zero-pause mode**). Their actual Home Assistant UI translations are defined by code and translations, not by an English report.
4. Distinguish **listed in Xiaomi Cloud**, **passed BLE authentication** and **physically verified operation**. Never advertise experimental family profiles as confirmed simply because their MIoT property maps match.
5. When the original source is in another language, keep that source in its language-specific folder and provide a separate canonical English technical report, citing the origin. Do not silently alter captured measurements or historical conclusions.
6. Dated files under `docs/history/` are **archived snapshots**, not installation instructions or current version documentation. When necessary, refer to them from the current summary rather than copying outdated instructions.
7. Do not publish private credentials, device addresses, OAuth redirect codes or raw HCI captures in either language. Localization must not reveal information excluded from the original.

## Quality checks

`tests/test_project_docs.py` verifies all language links and page references, safe inline SVG, and a consistent README language selector. A documentation-language regression check also ensures that English technical documentation does not accidentally accumulate untranslated Cyrillic prose. Historical snapshots and the deliberately preserved Russian research source are explicitly excluded from that English-only check.

**Contribution workflow:** see [CONTRIBUTING](../CONTRIBUTING.md); update canonical English material first, then translate impacted user-facing guides. If a translation is not updated, mark it as out of date rather than inserting untranslated English text into it.

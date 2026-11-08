# Contributing

Thanks for helping improve Xiaomi SO Diffuser BLE. This is an independent Home Assistant integration; contributions must be grounded in reproducible behavior and must not include private Xiaomi or Bluetooth credentials.

## Before opening an issue

- Check the [installation guide](docs/INSTALLATION.md), [model compatibility](docs/COMPATIBILITY.md), and [known limitations](docs/STATUS.md).
- Include your Home Assistant version, integration source or release version, the **model name** (for example S5), the operation attempted, the expected result, and what actually happened.
- If possible, state whether Bluetooth discovery, Xiaomi account selection, authenticated BLE pairing or *physical* device control failed. These are different stages.
- Do **not** post real BLE MAC addresses, GATT tokens, one-time Xiaomi OAuth callback URLs, QR login data, cloud exports, raw HCI/btsnoop traces, account identifiers or private network details. See [SECURITY.md](SECURITY.md).

The S5 has a user-reported successful physical setup on an earlier source revision. S1, S1 Pro, S2, S6, S7, S8, S9 and S19 are experimental until each model passes separate hardware acceptance. Do not mark a device supported based only on a cloud listing or a shared MIoT property number.

## Development workflow

1. Fork the repository and branch from the current `main`.
2. Keep changes focused. Avoid modifying the BLE protocol, credential storage, or entity identifiers while making documentation or artwork-only changes.
3. Install test dependencies with `python -m pip install -r requirements_test.txt` and run `python -m pytest -q`.
4. Check that Home Assistant Hassfest and HACS Validation pass on the pull request. For physical behavior, follow [the acceptance checklist](docs/TESTING.md).
5. Update the affected English documentation and translate affected public instructions where practical. Do not mix English paragraphs into localized pages. See [language policy](docs/LANGUAGE_POLICY.md).
6. Describe what changed, how it was tested, which devices were physically observed, and what remains unverified in the pull request.

## Artwork

The existing S5 cover, author-provided four-step PNG and older connection SVG are intentionally preserved. Review [BRANDING.md](docs/BRANDING.md) before editing artwork. Do not regenerate or replace these files incidentally during a docs cleanup.

## Releases

Changes merged to `main` do not retroactively update a published GitHub tag or the version HACS installs. Release publication is a separate reviewed step documented in [PUBLISHING.md](docs/PUBLISHING.md).

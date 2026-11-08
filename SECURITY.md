# Security and privacy

## Never commit

- `/config/so_s5_token`
- Xiaomi Cloud Tokens Extractor JSON exports
- `token`, `BLE_DATA.beaconkey`, derived session keys or account passwords
- QR login material, cookies or service tokens
- Raw HCI/btsnoop captures, PCAPs or BLE traces
- The original Mi Home `main.bundle` or redistributed vendor plugin files
- Private device identifiers, addresses, hostnames or local network details

The repository `.gitignore` blocks common private artifact names and capture extensions. Review `git status` and the complete diff before every push.

## Token file

The runtime token file must be a regular file with owner-only permissions (`0600` or stricter). The integration rejects symlinks, non-regular files, malformed values and group/world access. The importer writes a new file atomically with mode `0600` and does not display the token.

## Credential acquisition

The built-in Home Assistant setup flow redirects users to Xiaomi's own OAuth login page, then temporarily exchanges the one-time authorization code and queries Xiaomi's device list through the HA-managed HTTP session. It does **not** collect Xiaomi passwords or persist OAuth access/refresh tokens. Only the device-specific 12-byte GATT token is saved in private HA storage after a real BLE authentication proof. An external Xiaomi Cloud Tokens Extractor remains an optional legacy fallback; its JSON output is sensitive and must never be published.

## Runtime boundary

After provisioning, normal device control and status updates use local BLE, not repeated Xiaomi Cloud calls. Explicit setup or reconfiguration can contact Xiaomi Cloud. The device token authenticates the S5-compatible FE95 GATT session and AES-CCM data channel; it must not be logged or published.

## Diagnostics

`tools/verify_capture.py` prints only authentication status, frame counts and decoded property values. It does not print token, BLE key, session keys or ciphertext. Raw captures should still be treated as private traffic and kept out of public issue attachments.

## Reporting issues

Before attaching logs, remove Bluetooth addresses, device IDs, token file paths that reveal private layouts, and any raw capture. Share the Home Assistant version, integration version, redacted error category and the exact action that failed.

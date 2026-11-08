# Security and privacy

## Experimental relatives — permission and protocol boundary

Development source 0.4.0 introduces exact cloud candidates for eight SO relatives, but **does not certify their actual BLE command compatibility**. An experimental device requires explicit user acknowledgment and a successful live Standard Auth login against the selected Bluetooth address before a device token is persisted. The config entry records only the declared model and opt-in flag alongside its address. Runtime checks these fields again; unknown models and manually configured experimental models without permission are rejected. A discovered S6/S1/S19 cannot silently reuse the legacy S5-only token path.

**The first successful BLE login establishes credential/device correspondence, not the physical meaning of all MIoT writes.** Do not automate unverified models unattended. No blanket FE95 matcher, arbitrary property setter or unsupported Xiaomi Mesh transport is exposed. Collect only redacted error categories/model IDs for support. [Details](MULTI_MODEL_ARCHITECTURE.md).



## Never commit

- `/config/so_s5_token`
- `/config/.storage/so_s5_ble_tokens.json`
- Xiaomi Cloud Tokens Extractor JSON exports
- `token`, `BLE_DATA.beaconkey`, derived session keys or account passwords
- QR login material, cookies or service tokens
- Raw HCI/btsnoop captures, PCAPs or BLE traces
- The original Mi Home `main.bundle` or redistributed vendor plugin files
- Private device identifiers, addresses, hostnames or local network details

The repository `.gitignore` blocks common private artifact names and capture extensions. Review `git status` and the complete diff before every push.

## Token file

Runtime credential files must be regular owner-only files (`0600` or stricter). The old single-token importer remains available; the new per-address store uses a private 0600 JSON file under HA `.storage` and serialized atomic writes. Config entries contain addresses only. Do not publish or manually change the stored tokens.

## Credential acquisition

The new setup flow initiates a browser-based Xiaomi OAuth2 Authorization Code login through Xiaomi's own website. The integration temporarily handles a one-time authorization code and the OAuth access token to retrieve the device list; it **does not ask for or persist a password, refresh token or account cookie**. The webhook has a random identifier, state validation and 300-second lifetime. Only an S5 GATT token that passes a **live BLE HMAC login** is persisted. The operator reports successful live Xiaomi OAuth and a working S5. Broader region compatibility, token expiry/rotation, persisted token permissions after reboot and WAN-off operation remain unverified. The external extractor remains an alternative.

## Runtime boundary

**Setup/reconfiguration only:** HTTPS calls to Xiaomi OAuth and device-list APIs. **Normal operation:** local BLE only; no recurring cloud access, password or refresh-token storage. The 12-byte GATT token authenticates the S5's FE95 GATT session and AES-CCM data channel. Browser OAuth callback to `http://homeassistant.local:8123` is a local HTTP redirect; use a trusted LAN, and never expose HA's callback or tokens in public logs. Actual WAN-off resilience remains an acceptance test.

## Diagnostics

`tools/verify_capture.py` prints only authentication status, frame counts and decoded property values. It does not print token, BLE key, session keys or ciphertext. Raw captures should still be treated as private traffic and kept out of public issue attachments.

## Reporting issues

Before attaching logs, remove Bluetooth addresses, device IDs, token file paths that reveal private layouts, and any raw capture. Share the Home Assistant version, integration version, redacted error category and the exact action that failed.

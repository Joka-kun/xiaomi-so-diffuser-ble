# Credential acquisition

## Which models can fetch a token in 0.4.0?

The OAuth wizard now lists **exact SO model IDs** from a nine-model catalog. S5 remains the only device with field-reported control. S6, S2, S7, S8, S9, S1 Pro, S1 and S19 are **experimental** and require explicit acknowledgement plus a successful *real* BLE Standard Auth proof before the selected 12-byte token is saved. Xiaomi Cloud displaying a device is **not** evidence of local controllability. The legacy file `/config/so_s5_token` is for earlier S5 entries; for a discovered non-S5 model the wizard requires Xiaomi account selection rather than silently treating a saved S5 file as its credential.

The authorization access token is temporary and never replaces the locally stored device GATT token. See [model-specific onboarding](MULTI_MODEL_ARCHITECTURE.md).



## New: built-in Xiaomi OAuth2 setup (unreleased, hardware acceptance pending)

After updating the integration, use **Add integration** or **Reconfigure** on an existing SO S5 entry. Select **Sign in with Xiaomi**, choose your Mi Home account region, follow the OAuth link, select the exact-model SO S5 device, and let Home Assistant verify the 12-byte GATT token directly over BLE. **No Xiaomi password or OAuth refresh token is stored.**

The private per-device credential path is `/config/.storage/so_s5_ble_tokens.json` (0600, keyed by BLE address). Existing `/config/so_s5_token` files remain readable until users complete and verify migration; they are **not auto-deleted**. The operator has now reported a successful *real* Xiaomi browser OAuth setup and working S5, following an unreachable `homeassistant.local` callback workaround. Post-restart token persistence and WAN-off control remain untested. For expected errors, callback host requirements and verification criteria, see [Onboarding](ONBOARDING.md).

## Legacy standalone extractor (fallback)

Use the external [Xiaomi Cloud Tokens Extractor](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor). The latest public release observed during preparation is [v1.5.1](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/releases/tag/v1.5.1). Its README documents interactive username/password and QR-code login, region selection, and JSON output.

The legacy fallback imports the extractor's JSON output. The new HA flow independently implements OAuth2 against Xiaomi's published HA endpoint and does not reuse or vendor the extractor's login source.

## Export

Download the upstream release/source and run its interactive extractor. For the Python source, install the upstream `requirements.txt`, then run:

```bash
python3 token_extractor.py --output xiaomi-cloud-export.json
```

The extractor asks for Xiaomi account authentication and region. Its upstream CLI can print token/key values to the terminal as well as write the JSON export, so run it in a private terminal and treat scrollback as sensitive. Keep the resulting JSON private: it may contain credentials for multiple devices. Do not paste the account password, QR authentication data, JSON export or token into chat or a public issue.

## Import only the S5 GATT token

From this repository root:

```bash
python3 tools/import_xiaomi_token.py \
  --input xiaomi-cloud-export.json \
  --output ./so_s5_token
```

The resulting file is already mode `0600` and contains no newline. Copy it into the Home Assistant configuration root as `/config/so_s5_token` (or write directly to that path if the command is being run in an environment where `/config` is the HA configuration directory). For a host-mounted HA config directory, use `install -m 600 ./so_s5_token /path/to/ha-config/so_s5_token`.

If multiple S5 devices are in the export, pass the exact device ID:

```bash
python3 tools/import_xiaomi_token.py \
  --input xiaomi-cloud-export.json \
  --output ./so_s5_token \
  --did 'DEVICE_ID_FROM_YOUR_PRIVATE_EXPORT'
```

The importer:

- Selects only model `bwj.diffuser.s5`.
- Requires exactly 24 hexadecimal characters (12 bytes) in the device `token` field.
- Writes only that token, lowercase and without a newline.
- Sets file permissions to `0600`.
- Refuses to overwrite an existing file unless `--replace` is explicitly supplied.
- Never prints the secret value.
- Does not import or use `BLE_DATA.beaconkey`.

Home Assistant first reads the per-address private token if provisioned, otherwise falls back to `/config/so_s5_token`. The GATT token is never stored in the HA config entry.

## Why the token, not `BLE_DATA.beaconkey`?

The supplied S5 HCI capture independently verifies the 12-byte `token` against both login HMAC proofs and all 272 AES-CCM tags. The extractor's `BLE_DATA.beaconkey` is a distinct field for BLE beacon encryption; it was separately tested against the captured S5 login transcript and failed both HMAC proof checks. Do not substitute one for the other.

## Rotation and expiry

Token expiry/rotation has not been measured for this S5. If authentication begins failing, do not repeatedly pair or reset the diffuser. Prefer **Reconfigure → Sign in with Xiaomi** and validate the replacement token against the real S5. The external extractor/legacy file remains a fallback. Do not delete the old file until live migration and a HA restart have been verified. A WAN-off test is still required.

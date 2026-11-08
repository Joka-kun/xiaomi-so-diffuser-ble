# Xiaomi SO family onboarding — source implementation and acceptance

Updated: 2026-11-07. The operator reported **successful S5 OAuth/browser setup on the earlier source** but has **not installed the experimental 0.4.0 multi-model code**. Eight SO relatives are now selectable with explicit experimental consent and a BLE token check; none has been physically accepted.

## Current clean HA deployment (operator audit, 2026-11-07)

The current installation was intentionally cleared of the previous local SO S5 component and credentials. The read-only audit found **no** `/config/custom_components/so_s5` folder, `/config/so_s5_token`, or `/config/.storage/so_s5_ble_tokens.json`, and **zero** persisted `so_s5` config entries. Other custom integrations and the separate built-in `xiaomi_ble` domain remain installed and must not be conflated with our project.

**Subsequent field update:** the operator completed a fresh Add integration setup using Xiaomi browser OAuth and reports that the S5 now operates. The **Reconfigure** instructions below still apply to other HA installations with an existing `so_s5` entry. The pre-setup legacy token was absent, so the successful new path did not depend on it. Do not publish the OAuth redirect URL or GATT token.

See [deployment audit](DEPLOYMENT_AUDIT_2026-11-07.md) for the clean baseline and follow-up; [spray/compatibility analysis](SPRAY_MODES_AND_COMPATIBILITY.md) documents the new reported success, remaining physical unknowns and model coverage.

## New installation

1. Install/update the integration and restart HA. Use **Settings → Devices & services → Add integration → Xiaomi SO Diffuser BLE**.
2. Select the detected SO device (exact registered Bluetooth name) or enter its Bluetooth address manually. FE95 alone does not identify a supported model; some relatives may advertise a different name and require manual address entry.
3. Select **Sign in with Xiaomi** and the exact Xiaomi Home account region.
4. Open the Xiaomi authorization link from HA; sign in **on Xiaomi's own site**. The browser returns to the local HA callback at `http://homeassistant.local:8123/api/webhook/<random>`.
5. The integration exchanges a short-lived authorization code, fetches the paginated Xiaomi device list and filters exact SO/BWJ model IDs listed in [the 0.4.0 catalog](MULTI_MODEL_ARCHITECTURE.md). Each candidate must contain a valid **24-hex-character GATT token**.
6. Choose the cloud device corresponding to the physical diffuser. S5 uses the verified path. For any **other SO model**, first acknowledge its **experimental** status in the extra confirmation screen. Then the selected token **must pass a GATT Standard Auth challenge against the physical BLE device** before storage; a correct device name or similar MIoT schema is not enough to certify local control.
7. Only a GATT token proven by the chosen physical BLE device is written to the private per-address file. OAuth access/refresh tokens, Xiaomi password and account cookies are **not persisted**. A new HA config entry stores Bluetooth address, exact MIoT model and explicit experimental opt-in flag (no credential bytes).
8. Subsequent reconnections read the saved local GATT token and use only BLE for controls.

There is **no embedded QR-image scanner** in this release; the OAuth authorization link opens the Xiaomi sign-in page, which may offer Xiaomi's own account/QR methods. We have not claimed that Xiaomi's QR flow is physically verified for this integration.

## Experimental SO model flow (0.4.0, not yet field-tested)

| Candidate | Source capability profile | Result |
| --- | --- | --- |
| S6, S2, S7, S8, S9 | Power, pulse/pause, battery/charging, RGB | Experimental; GATT must prove compatibility |
| S1 Pro | Above plus **read-only temperature 3.10** when reported | Experimental |
| S1, S19 | Power, pulse/pause, battery/charging, **no RGB** | Experimental |

Non-S5 devices require the **experimental confirmation** checkbox after cloud selection. Model name matching and correct GATT token prove access to *that physical device*, **not** correctness of every setter. The `3.4=0` LongSpray control is hidden for relatives until measured. If login fails, no new credential is saved and setup does not claim the device works. For experimental models that pass login, validate power on/off under supervision before using light or timing changes.

An unknown Xiaomi/Mijia diffuser, another BLE Mesh product, and a Xiaomi `xiaomi.diffuser.xw002` device are **not** part of this allowlist; they may require a different BLE security protocol. Never choose a different cloud device to bypass failed authentication.

## Existing installation — no entity deletion

Use **Settings → Devices & services → Xiaomi SO Diffuser BLE → menu (⋮) → Reconfigure** on the existing integration entry and select the Xiaomi OAuth method. After cloud provisioning and real BLE token authentication, HA reloads the **same entry**. Switch entity unique IDs and your existing automations are preserved. **Do not remove and re-add the integration just to migrate its token.**

Old installs continue to use `/config/so_s5_token` if no per-device token is present. This old global file is never automatically deleted: remove it only after successful migration of *every* S5 that previously depended on it, a HA reload/restart, and repeated local control tests.

## Token storage and boundaries

- Preferred path: `/config/.storage/so_s5_ble_tokens.json`, private mode **0600**, keyed by uppercase Bluetooth address. Writes are serialized and atomic.
- Fallback for old entries: `/config/so_s5_token` (existing 0600 credential).
- Each new S5 token is validated **before** it is written; failed BLE authentication does not overwrite a working token.
- If the phone owns the S5 BLE connection, close Mi Home and retry. The probe does not pair or reset the diffuser.
- The cloud `BLE_DATA.beaconkey` does **not** substitute for the device's GATT token.
- Only the temporary OAuth access token is needed to enumerate devices. Its lifetime is limited to this setup task; no cloud refresh token is retained.
- OAuth uses the publicly documented Xiaomi Home for HA application identifier and its local HA redirect convention. Xiaomi controls authorization policies and can change these endpoints; this interoperability is **not verified with a live account** in our repository.

## Preconditions and known limitations

- The Home Assistant server must have outbound HTTPS access to `account.xiaomi.com` and the selected `{region}.ha.api.io.mi.com` host.
- Default **automatic** login redirects the browser to **`http://homeassistant.local:8123`**. **Field-confirmed solution:** if the callback page cannot be reached, change just the hostname in the final *browser URL* to the accessible HA LAN IP/host, preserving `/api/webhook/...`, `code` and `state`. The operator completed automatic callback this way. Do **not** change the OAuth request's registered `redirect_uri` parameter. Alternatively, choose **Xiaomi sign-in — paste redirect URL** and paste the original callback into the wizard; this separate fallback has not yet been tested on the operator's HA. Either kind of callback URL is a one-time credential: never publish it.
- The Xiaomi cloud must actually return the S5 with a **12-byte GATT token**. If it omits or rejects the device/token, the integration fails closed and the old token remains usable.
- The callback is a random one-time webhook, with state validation and a five-minute expiry. It never echoes the code or token and is unregistered when the setup task completes.
- The integration can handle multiple S5 entries by separate locally verified tokens. Moving a configured diffuser to a changed/randomized BLE address is not automated and needs further testing.
- Failed token validation shows an error. The user can choose another S5 from the cloud list; no name-only association is attempted.
- The operator now reports working real Xiaomi login and S5 setup. However, **post-restart token loading, WAN-off operation, irregular `LongSpray` duty cycle, multi-account/region interoperability and other SO models** are not fully validated. Source remains experimental.

## Confirmed implementation path and current evidence

The operator's clean pre-install audit found **no** previous S5 token file and no per-device store. After successful Xiaomi OAuth, the code exchanges an authorization code for a **temporary cloud access token**, queries the account device list for exact-model `bwj.diffuser.s5`, selects its **24-character hex GATT token**, proves it against the chosen BLE device, and saves **only the GATT token** in the per-address private store. At every normal reconnect `coordinator.py` loads that saved GATT token. The cloud access token is never used for ordinary BLE control.

The first successful operator test has been reported, but it is still necessary to check the new private store's existence and permissions **without exposing contents**, then restart HA and verify control with internet access disconnected.

## Acceptance matrix

| Test | Expected result |
| --- | --- |
| Fresh HA config without legacy token | OAuth flow offers account/region and completes without external extractor |
| Xiaomi account without S5 | No GATT token is stored; user sees a clear error |
| Wrong S5 token/cloud DID | BLE Standard Auth fails; no new file entry created |
| Correct S5 token | Real GATT authentication succeeds before per-device token is saved |
| HA restart / WAN disabled | Device reconnects and remains controllable via BLE without OAuth |
| Reconfigure installed S5 | Existing config entry and entity IDs remain intact |
| Existing legacy-only S5 | Continues to work as before; no file deletion |
| Two different S5 devices | Each address obtains and uses its own verified token |
| Expired or replayed OAuth callback | Rejected; no secret leaked to the UI or logs |

See [credentials](CREDENTIALS.md), [security](SECURITY.md), [test plan](TESTING.md), [status](STATUS.md) and [roadmap](../ROADMAP.md).

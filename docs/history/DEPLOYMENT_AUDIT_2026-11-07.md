# Deployment audit — clean Home Assistant S5 installation state

> **Historical snapshot (2026-11-07).** User-interface labels below are rendered in English for readability; the original Russian spellings are preserved in the repository's Git history. This is not current installation guidance.


**Date:** 2026-11-07  
**Evidence:** operator-supplied output of read-only commands run inside a Home Assistant Docker container. The repository itself has no access to the operator's HA host.  
**Scope:** local deployment state, **not** Xiaomi OAuth interoperability or S5 device acceptance.

## Project identity vs previous installation identity

The **current source** manifest `custom_components/so_s5/manifest.json` declares:

| Item | Current source value |
| --- | --- |
| Display name | `Xiaomi SO Diffuser BLE` |
| Integration domain | `so_s5` |
| GitHub repository | `Joka-kun/xiaomi-so-diffuser-ble` |
| Directory expected after installation | `/config/custom_components/so_s5` |

These values establish the **current project's identity**, but do **not** prove what an earlier, already removed, manually installed integration was historically named. The previous folder and its manifest are no longer present to inspect. Do not invent or retroactively assert an old display name.

## Confirmed local state after manual cleanup

The operator explicitly removed the legacy token and the integration directory. A subsequent container-side read-only audit confirmed:

| Check | Result |
| --- | --- |
| `/config/so_s5_token` | **Absent** |
| `/config/custom_components/so_s5` | **Absent** |
| `/config/.storage/so_s5_ble_tokens.json` | **Absent** |
| `domain == "so_s5"` entries in `/config/.storage/core.config_entries` | **0** |
| Text reference to `joka-kun/xiaomi-so-diffuser-ble` in scanned, readable `/config/.storage/hacs*` files under the audit size limit | **Not found** |
| Other custom integration manifests | **5 present**; none was `so_s5` |

The audit found other configured integrations, including the separate built-in `xiaomi_ble` domain; **those are not the SO S5 custom integration** and must not be removed as part of this procedure.

The HA Docker container's `/config` is backed by a persistent host mount. The host-side storage path, device identifiers, usernames, IP addresses, credentials, and other local topology are intentionally omitted from this public record.

### What these checks do and do not establish

- **Established:** the listed S5 files are absent from the checked container filesystem, and the persisted config-entry registry contains zero entries for the **current** `so_s5` domain.
- **Not established:** whether a historical version used a *different* domain; whether any orphaned entities or device-registry records exist under other domains; whether HACS has other records not covered by the file scan; and whether Home Assistant still has old Python code in memory if it was not restarted.
- **Not done:** installed the current code, created a new S5 config entry, authenticated against a live Xiaomi account, tested the S5 GATT handshake, or completed post-restart/WAN-off acceptance.

**Result:** treat this particular HA instance as a **fresh installation candidate** for the current `so_s5` project, rather than an in-place **Reconfigure** migration. Neither the old token nor the new per-device token exists on this checked deployment.

## Follow-up: first live Xiaomi OAuth and S5 success — 2026-11-07

After the initial clean filesystem and config-entry audit, the operator installed the current integration, selected the advertised SO S5, signed in on Xiaomi's website and reported that the diffuser works. The final OAuth browser callback was initially unreachable at `homeassistant.local:8123`; the operator changed **only the destination hostname in the browser address bar** to the reachable Home Assistant LAN host, preserving the path and OAuth parameters, and authentication completed.

This is the first operator-confirmed live account/setup success, **not** independent proof of post-restart credential persistence, WAN-off operation, precise atomizer duty cycle or support for other models. The new private token file and its permissions have not yet been inspected after this setup. No account code, token or LAN identity is recorded here.

For follow-up installations, upgrade the development code (current manifest version **0.3.1**), restart HA to load the renamed Power switch, and verify token persistence after restart. A working configuration entry now exists per the operator's report, so **future** account/token maintenance should use **Reconfigure**, not deleting the new working entry.

## Historical next-step checklist from the initial clean audit (completed or superseded where noted)

1. Install `Joka-kun/xiaomi-so-diffuser-ble` as a **HACS custom repository** (or manually if HACS rejects the development repository); confirm that `/config/custom_components/so_s5/manifest.json` now exists and declares `"domain": "so_s5"`, `"name": "Xiaomi SO Diffuser BLE"`.
2. Restart HA so it actually loads the new integration files. Do not assume deleting/replacing files restarts already-loaded Python code.
3. Select **Settings → Devices & services → Add integration → Xiaomi SO Diffuser BLE**. Because no `so_s5` config entry currently exists, do **not** look for **Reconfigure** on this instance.
4. Pick an advertised SO S5, or provide its Bluetooth address. Select the correct Xiaomi account region, then use Xiaomi OAuth. If the automatic `homeassistant.local` callback is inaccessible, use the **paste browser redirect URL** option; that one-time URL must never appear in public logs/issues.
5. Verify the cloud device list contains the correct `bwj.diffuser.s5` device and that its device token passes the *actual* fresh Bluetooth GATT authentication **before** saving it.
6. Only after successful setup: verify an available entity, physical on/off and continuous-spray behaviour, HA restart/reconnect, token persistence and operation without WAN access. A newly saved token belongs at `/config/.storage/so_s5_ble_tokens.json`, with restrictive permissions.
7. Capture only **redacted** error categories and test results in project docs. Do not publish Xiaomi OAuth callback URLs, tokens, device MACs, HCI captures, or host-specific filesystem paths.

**Fallback warning:** because the old `/config/so_s5_token` was deliberately removed, this installation has no existing local credential to fall back to if the OAuth flow fails. A legacy rollback would require restoring a securely backed-up token or re-extracting one.

## Release gates

The last pre-audit GitHub Actions run completed **80 pytest tests and 56 subtests**, Python compilation, and Hassfest. Those are offline/software checks; they are **not** a live end-to-end Home Assistant + Xiaomi + S5 test.

HACS validation still fails the missing **project LICENSE** check. The project is not considered hardware-accepted or a stable published release.

See [installation](INSTALLATION.md), [onboarding](ONBOARDING.md), [status](STATUS.md), [roadmap](../ROADMAP.md) and [publishing](PUBLISHING.md).

# Xiaomi SO Diffuser BLE — v1.0.5

Local BLE reconnect improvements and official HACS Marketplace support.

## What's new

- **S5 power recovery:** Home Assistant's On/Off command can now wait for the single BLE connection owner to reconnect and authenticate when the previous GATT session has dropped. It no longer fails immediately solely because the connection is temporarily unavailable.
- **Advertisement-assisted recovery:** Exact-address connectable Bluetooth advertisements can wake the existing session owner, with rate limiting and the established bounded retry loop.
- **Safe write behavior:** Commands remain serialized; an uncertain BLE write is never automatically replayed. The BLE connection diagnostic still reports the actual connection state and does not equate a command being offered with the physical radio being reachable.
- **No destructive migration:** Existing model selections, BLE tokens, entity IDs, RGB/spray controls and explicit experimental-model opt-ins are unchanged.
- **Official HACS catalog:** [PR #13656](https://github.com/hacs/default/pull/13656) has been approved and merged. Search for **Xiaomi SO Diffuser BLE** directly in HACS; use the custom repository URL only if a catalog refresh is pending.

## Evidence and limits

Automated Python tests and HACS/Hassfest validate logic and packaging. A live HA canary received the three BLE recovery changes, and S5 operation was user-reported working, including a brief reconnect. **Physical recovery after 8–24 hours in standby, behavior when the S5 stops advertising, recovery with WAN disconnected, and non-S5 hardware are not certified.** The integration cannot wake a radio that is physically silent.

## Upgrade

Update **Xiaomi SO Diffuser BLE** to **v1.0.5** via HACS, restart Home Assistant if requested and retain your existing device configuration. Do not delete private BLE tokens or re-pair devices merely to update. If the S5 cannot reconnect, observe the BLE diagnostic and the proxy/adapter; do not assume an API acknowledgement proves physical spray operation.

Independent community project, not affiliated with Xiaomi or Home Assistant.

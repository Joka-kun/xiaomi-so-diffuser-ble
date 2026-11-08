"""Prove a cloud-provisioned token against the chosen physical S5 before storage."""
from __future__ import annotations

import asyncio
from contextlib import suppress

from bleak import BleakClient
from bleak_retry_connector import establish_connection
from homeassistant.components import bluetooth

from .client import S5ReadOnlyClient
from .xiaomi_oauth import XiaomiProvisioningError


async def async_validate_s5_token(hass, address: str, token: bytes) -> None:
    """Connect, complete S5 HMAC Standard Auth, then release the GATT link."""
    device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), connectable=True
    )
    if device is None:
        raise XiaomiProvisioningError("ble_not_available")
    client = None
    try:
        try:
            client = await asyncio.wait_for(
                establish_connection(
                    BleakClient, device, "SO diffuser token verification", pair=False
                ),
                timeout=25,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            # A busy/unreachable BLE link is not evidence of a bad device token.
            raise XiaomiProvisioningError("ble_connection_failed") from None

        try:
            verifier = S5ReadOnlyClient(client, token, timeout=8, auth_quiet=1)
            await asyncio.wait_for(verifier.authenticate(), timeout=45)
            if not verifier.authenticated:
                raise XiaomiProvisioningError("ble_auth_failed")
        except asyncio.CancelledError:
            raise
        except XiaomiProvisioningError:
            raise
        except Exception:
            # A connection succeeded, but the GATT login could not be proven.
            # Never expose key material, raw frames or exception payloads.
            raise XiaomiProvisioningError("ble_auth_failed") from None
    finally:
        if client is not None:
            with suppress(Exception):
                await client.disconnect()

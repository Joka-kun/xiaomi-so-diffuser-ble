#!/usr/bin/env python3
"""Bounded read-only S5 BLE probe: FE95 scan, GATT inventory, standard battery only.

No pairing, Xiaomi authentication, proprietary MIoT requests, or GATT writes.
"""
from __future__ import annotations

import argparse
import asyncio
import re
import sys
from typing import Any

FE95 = "0000fe95-0000-1000-8000-00805f9b34fb"
BATTERY_SERVICE = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL = "00002a19-0000-1000-8000-00805f9b34fb"


def bluez_options(adapter: str | None) -> dict[str, dict[str, str]]:
    return {"bluez": {"adapter": adapter}} if adapter else {}


def is_uuid16(value: str, short: int) -> bool:
    normalized = value.lower().replace("-", "")
    return normalized in {f"{short:04x}", f"0000{short:04x}00001000800000805f9b34fb"}


def choose_candidate(candidates: list[tuple[str, Any]], address_hint: str | None = None) -> tuple[str, Any]:
    if address_hint:
        matches = [item for item in candidates if item[0].lower() == address_hint.lower()]
    else:
        matches = candidates
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one FE95 candidate, found {len(matches)}")
    return matches[0]


def scrub(text: str, addresses: list[str]) -> str:
    for address in addresses:
        if address:
            text = re.sub(re.escape(address), "[REDACTED]", text, flags=re.IGNORECASE)
    return text.replace("\n", " ")[:300]


async def probe(scan_seconds: float, address_hint: str | None, adapter: str) -> int:
    from bleak import BleakClient, BleakScanner

    bleak_kwargs = bluez_options(adapter)
    print(f"adapter={adapter}")
    found = await BleakScanner.discover(timeout=scan_seconds, return_adv=True, **bleak_kwargs)
    all_addresses = list(found)
    candidates: list[tuple[str, Any, Any]] = []
    for address, (device, advertisement) in found.items():
        advertised = set(advertisement.service_uuids or ()) | set((advertisement.service_data or {}).keys())
        if any(is_uuid16(uuid, 0xFE95) for uuid in advertised):
            candidates.append((address, device, advertisement))

    print(f"scan_seconds={scan_seconds:g} total_devices={len(found)} fe95_candidates={len(candidates)}")
    try:
        address, device, advertisement = choose_candidate(
            [(item[0], item) for item in candidates], address_hint
        )[1]
    except RuntimeError as exc:
        print(f"selection=blocked reason={exc}")
        return 2

    name = advertisement.local_name or device.name or ""
    print(f"selected_name={name or '[none]'} rssi={advertisement.rssi}")
    client = BleakClient(device, timeout=15, **bleak_kwargs)
    try:
        await client.connect()
        print("connected=true")
        services = client.services
        for service in sorted(services, key=lambda item: item.uuid):
            print(f"service={service.uuid}")
            for characteristic in sorted(service.characteristics, key=lambda item: item.uuid):
                props = ",".join(sorted(characteristic.properties))
                print(f"  characteristic={characteristic.uuid} properties={props}")
        if any(service.uuid.lower() == BATTERY_SERVICE for service in services):
            chars = [c for s in services if s.uuid.lower() == BATTERY_SERVICE for c in s.characteristics]
            battery_char = next((c for c in chars if c.uuid.lower() == BATTERY_LEVEL), None)
            if battery_char and "read" in battery_char.properties:
                raw = await client.read_gatt_char(BATTERY_LEVEL)
                if len(raw) == 1:
                    print(f"standard_battery_percent={raw[0]}")
                else:
                    print(f"standard_battery_read_length={len(raw)}; value_not_interpreted")
            else:
                print("standard_battery_readable=false")
        else:
            print("standard_battery_service=absent")
        return 0
    except Exception as exc:  # report bounded, address-redacted diagnostic only
        print(f"probe_error={type(exc).__name__}: {scrub(str(exc), all_addresses)}")
        return 1
    finally:
        if client.is_connected:
            await client.disconnect()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-seconds", type=float, default=8.0)
    parser.add_argument("--adapter", default="hci0", help="BlueZ adapter (default: hci0)")
    parser.add_argument("--address", help="optional one-time observed address if multiple FE95 devices are nearby")
    args = parser.parse_args()
    if not 3 <= args.scan_seconds <= 20:
        parser.error("--scan-seconds must be between 3 and 20")
    try:
        return asyncio.run(probe(args.scan_seconds, args.address, args.adapter))
    except Exception as exc:
        print(f"probe_error={type(exc).__name__}: {scrub(str(exc), [args.address or ''])}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

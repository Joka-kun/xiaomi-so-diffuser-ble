"""Pure validation for the one address field stored by the config flow."""
from __future__ import annotations

import re

_ADDRESS_RE = re.compile(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}")


def validate_ble_address(value: str) -> str:
    if not isinstance(value, str) or _ADDRESS_RE.fullmatch(value) is None:
        raise ValueError("Bluetooth address must be six colon-separated hexadecimal octets")
    return value

"""Private, per-Bluetooth-address SO diffuser GATT credential store.

Each diffuser uses its own address-bound token. There is no fallback to
single-device S5 files or automatic credential migration.
Never serialize tokens into config entries, errors or diagnostics.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import tempfile
import threading

from .config import validate_ble_address
from .credentials import TokenFileError
from .protocol import decode_token_hex

PRIVATE_FILENAME = "so_diffuser_ble_tokens.json"
_STORE_LOCK = threading.Lock()


def _private_path(config_dir: str | Path) -> Path:
    return Path(config_dir) / ".storage" / PRIVATE_FILENAME


def _address_key(address: str) -> str:
    return validate_ble_address(address).upper()


def _read_tokens(config_dir: str | Path) -> dict[str, str]:
    path = _private_path(config_dir)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    except FileNotFoundError:
        return {}
    with os.fdopen(fd, "r", encoding="ascii") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise TokenFileError("type")
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise TokenFileError("permissions")
        if info.st_size > 100_000:
            raise TokenFileError("format")
        try:
            data = json.load(handle)
        except (ValueError, UnicodeError):
            raise TokenFileError("format") from None
    if not isinstance(data, dict) or data.get("version") != 1:
        raise TokenFileError("format")
    devices = data.get("devices")
    if not isinstance(devices, dict):
        raise TokenFileError("format")
    output = {}
    for address, token in devices.items():
        try:
            key = _address_key(address)
            decode_token_hex(token)
        except (ValueError, TypeError):
            raise TokenFileError("format") from None
        output[key] = token.lower()
    return output


def has_device_token(config_dir: str | Path, address: str) -> bool:
    return _address_key(address) in _read_tokens(config_dir)


def load_device_token(config_dir: str | Path, address: str) -> bytes:
    """Only return the credential bound to the requested BLE address."""
    token = _read_tokens(config_dir).get(_address_key(address))
    if token is None:
        raise TokenFileError("missing")
    return decode_token_hex(token)


def save_device_token(config_dir: str | Path, address: str, token: bytes) -> None:
    """Atomically save only the GATT token after a verified live BLE login."""
    if not isinstance(token, bytes) or len(token) != 12:
        raise ValueError("SO diffuser GATT token must be exactly 12 bytes")
    key = _address_key(address)
    with _STORE_LOCK:
        devices = _read_tokens(config_dir)
        devices[key] = token.hex()
        path = _private_path(config_dir)
        parent = path.parent
        if parent.is_symlink():
            raise TokenFileError("type")
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not parent.is_dir():
            raise TokenFileError("type")
        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(prefix=".so_diffuser_ble_", dir=parent)
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="ascii") as output:
                json.dump({"version": 1, "devices": devices}, output, sort_keys=True)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
            temporary = None
        finally:
            if temporary is not None:
                os.unlink(temporary)

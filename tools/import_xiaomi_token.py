#!/usr/bin/env python3
"""Import the S5 12-byte token from Xiaomi Cloud Tokens Extractor JSON.

This utility does not authenticate to Xiaomi Cloud. Run the upstream extractor
separately, then use this tool to select one bwj.diffuser.s5 device and write
only its 24-hex-character GATT token to a mode-0600 file.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator

MODEL = "bwj.diffuser.s5"
TOKEN_RE = re.compile(r"^[0-9a-fA-F]{24}$")


def iter_devices(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if all(key in value for key in ("model", "did", "token")):
            yield value
        for key in ("homes", "devices"):
            nested = value.get(key)
            if isinstance(nested, (list, dict)):
                yield from iter_devices(nested)
    elif isinstance(value, list):
        for item in value:
            yield from iter_devices(item)


def mask_identifier(value: str | None) -> str:
    if not value:
        return "(missing)"
    return value[:4] + "…" + value[-4:] if len(value) > 10 else "…"


def select_device(
    payload: Any, *, model: str = MODEL, did: str | None = None, mac: str | None = None
) -> dict[str, Any]:
    matches = [d for d in iter_devices(payload) if d.get("model") == model]
    if did:
        matches = [d for d in matches if str(d.get("did", "")) == did]
    if mac:
        matches = [d for d in matches if str(d.get("mac", "")).lower() == mac.lower()]
    if not matches:
        raise ValueError(f"No {model} device with the requested selector was found")
    if len(matches) > 1:
        choices = ", ".join(mask_identifier(str(d.get("did", ""))) for d in matches)
        raise ValueError(f"More than one {model} device found ({choices}); pass --did")
    device = matches[0]
    token = device.get("token")
    if not isinstance(token, str) or not TOKEN_RE.fullmatch(token):
        raise ValueError("Selected S5 record does not contain a 24-character hexadecimal token")
    return device


def write_token(path: Path, token: str, *, replace: bool = False) -> None:
    if not TOKEN_RE.fullmatch(token):
        raise ValueError("token must be exactly 24 hexadecimal characters")
    parent = path.parent
    if not parent.is_dir():
        raise ValueError(f"output directory does not exist: {parent}")
    if path.exists() or path.is_symlink():
        if not replace:
            raise FileExistsError(f"refusing to overwrite existing file: {path} (use --replace)")
        if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError("refusing to replace a symlink or non-regular token path")

    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
    temp_path = Path(temp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="ascii", newline="") as stream:
            stream.write(token.lower())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
        os.chmod(path, 0o600)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        temp_path.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON written by Xiaomi Cloud Tokens Extractor")
    parser.add_argument("--output", required=True, type=Path, help="Destination token file, e.g. /config/so_s5_token")
    parser.add_argument("--did", help="Exact device ID when the account contains multiple S5 devices")
    parser.add_argument("--mac", help="Exact Bluetooth MAC when the account contains multiple S5 devices")
    parser.add_argument("--model", default=MODEL, help=argparse.SUPPRESS)
    parser.add_argument("--replace", action="store_true", help="Replace an existing regular token file")
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        device = select_device(payload, model=args.model, did=args.did, mac=args.mac)
        write_token(args.output, device["token"], replace=args.replace)
    except (OSError, json.JSONDecodeError, ValueError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2

    mode = stat.S_IMODE(args.output.stat().st_mode)
    print(f"Selected model: {device['model']}")
    print(f"Device ID: {mask_identifier(str(device.get('did', '')))}")
    print(f"Token file: {args.output} (mode {mode:04o}); secret value not displayed")
    print("Only the 12-byte S5 GATT token was imported; BLE_DATA.beaconkey was not used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

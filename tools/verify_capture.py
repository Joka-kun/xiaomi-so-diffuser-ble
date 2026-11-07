#!/usr/bin/env python3
"""Verify an S5 btsnoop capture using a private 0600 token file."""
from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from custom_components.so_diffuser_ble.credentials import TokenFileError, load_token_file
from s5_payload_decoder import decode_capture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, type=Path, help="Original btsnoop HCI capture")
    parser.add_argument("--token-file", required=True, type=Path, help="Private 0600 file with the 24-hex S5 token")
    args = parser.parse_args(argv)

    try:
        token = load_token_file(args.token_file)
        result = decode_capture(args.capture, token)
    except (OSError, ValueError, TokenFileError) as err:
        print(f"Verification failed: {err}", file=sys.stderr)
        return 2
    finally:
        if "token" in locals():
            del token

    tx_ok = sum(frame.authenticated is True for frame in result.tx)
    rx_ok = sum(frame.authenticated is True for frame in result.rx)
    types = collections.Counter(frame.message_type for frame in result.rx)
    print(f"Capture status: {result.status}")
    print(f"Login HMAC proofs: {'verified' if result.auth_verified else 'not verified'}")
    print(f"TX frames: {tx_ok}/{len(result.tx)} authenticated and parsed")
    print(f"RX frames: {rx_ok}/{len(result.rx)} authenticated")
    print(f"RX message types: {dict(types)}")
    print("Authenticated S5 property requests:")
    for frame in result.tx:
        for prop in frame.properties:
            print(f"  SIID={prop.siid} PIID={prop.piid} type={prop.vtype} value={prop.value}")
    response_codes = [code for frame in result.rx for _, _, code in frame.response_codes]
    if response_codes:
        print(f"SetPropertyResp success codes: {sum(code == 0 for code in response_codes)}/{len(response_codes)}")
        tx_ids = [frame.transaction_id for frame in result.tx]
        response_ids = [
            frame.transaction_id for frame in result.rx if frame.message_type == "SetPropertyResp"
        ]
        print(f"SetPropertyResp transaction IDs match requests: {response_ids == tx_ids}")
    changed_count = sum(
        len(frame.properties) for frame in result.rx if frame.message_type == "PropertyChanged"
    )
    print(f"PropertyChanged values parsed: {changed_count}")
    print("No token, BLE key, session key, or ciphertext was printed.")
    return 0 if result.status == "decoded" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Offline decoder for the S5 capture's token-authenticated MIoT Spec-v2 traffic.

The decoder accepts a token in memory, validates both captured login HMACs and
all AES-CCM tags, and returns decoded property metadata only. It never returns
session keys or ciphertext bytes.
"""
from __future__ import annotations

import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.so_diffuser_ble.client import _decode_value, parse_miot_message
from custom_components.so_diffuser_ble.protocol import (
    AuthenticationError,
    PayloadAuthenticationError,
    _AuthMaterial,
    _session_keys,
    ccm_nonce,
    decrypt_ccm,
    hkdf_sha256,
    parse_set_property_response,
)

# These ATT handles are specific to the supplied HCI capture.
_AUTH_HANDLE = 0x0018
_TX_HANDLE = 0x0021
_RX_HANDLE = 0x0024
_HDR_SEND_KEY = bytes.fromhex("0000000b0100")
_HDR_SEND_INFO = bytes.fromhex("0000000a0100")
_TX_HEADER = bytes.fromhex("000000000100")
_RCV_RDY = bytes.fromhex("00000101")
_RCV_OK = bytes.fromhex("00000100")


@dataclass(frozen=True)
class PropertyValue:
    siid: int
    piid: int
    vtype: int
    value: int | float | str | bytes | bool


@dataclass(frozen=True)
class FrameResult:
    counter: int
    encrypted_length: int
    authenticated: bool | None = None
    message_type: str | None = None
    properties: tuple[PropertyValue, ...] = ()
    response_codes: tuple[tuple[int, int, int], ...] = ()
    parse_error: str | None = None
    transaction_id: int | None = None


@dataclass(frozen=True)
class CaptureResult:
    status: str
    auth_verified: bool | None
    tx: tuple[FrameResult, ...]
    rx: tuple[FrameResult, ...]


@dataclass(frozen=True)
class _CipherFrame:
    counter: int
    ciphertext: bytes


def parse_miot_set_request(packet: bytes) -> tuple[PropertyValue, ...]:
    """Parse the MIoT Spec-v2 SetProperty request used by the S5 client."""
    if len(packet) < 6:
        raise ValueError("MIoT request is too short")
    header = int.from_bytes(packet[:2], "little")
    if header >> 12 != 2 or header & 0x0FFF != len(packet) or packet[4] != 0:
        raise ValueError("invalid MIoT Spec-v2 SetProperty request header")
    body = packet[5:]
    if not body:
        raise ValueError("MIoT SetProperty request has no property count")
    count = body[0]
    offset = 1
    properties: list[PropertyValue] = []
    for _ in range(count):
        if len(body) - offset < 5:
            raise ValueError("truncated MIoT SetProperty property header")
        siid = body[offset]
        piid = int.from_bytes(body[offset + 1 : offset + 3], "little")
        type_length = int.from_bytes(body[offset + 3 : offset + 5], "little")
        value_type = (type_length >> 12) & 0x0F
        value_length = type_length & 0x0FFF
        offset += 5
        if value_length > len(body) - offset:
            raise ValueError("truncated MIoT SetProperty value")
        raw = body[offset : offset + value_length]
        value = _decode_value(value_type, raw)
        properties.append(PropertyValue(siid, piid, value_type, value))
        offset += value_length
    if offset != len(body):
        raise ValueError("unexpected trailing MIoT SetProperty bytes")
    return tuple(properties)


def _att_events(path: str | Path):
    data = Path(path).read_bytes()
    if len(data) < 16 or data[:8] != b"btsnoop\x00":
        raise ValueError("not a btsnoop capture")
    version, datalink = struct.unpack_from(">II", data, 8)
    if version != 1 or datalink != 1002:
        raise ValueError("unsupported btsnoop version or datalink")
    pos = 16
    while pos < len(data):
        if len(data) - pos < 24:
            raise ValueError("truncated btsnoop record header")
        original, included, flags, drops, _timestamp = struct.unpack_from(">IIIIQ", data, pos)
        pos += 24
        if included != original or pos + included > len(data):
            raise ValueError("truncated HCI record")
        if drops:
            raise ValueError("capture reports dropped HCI packets")
        packet = data[pos : pos + included]
        pos += included
        if not packet or packet[0] != 0x02:
            continue
        if len(packet) < 9 or struct.unpack_from("<H", packet, 3)[0] != len(packet) - 5:
            raise ValueError("invalid HCI ACL record")
        l2cap_len, cid = struct.unpack_from("<HH", packet, 5)
        if cid != 0x0004:
            continue
        if l2cap_len != len(packet) - 9:
            raise ValueError("fragmented ATT packets are unsupported")
        att = packet[9:]
        if len(att) < 3 or att[0] not in (0x52, 0x1B):
            continue
        handle = struct.unpack_from("<H", att, 1)[0]
        yield ("in" if flags & 1 else "out", att[0], handle, att[3:])
    if pos != len(data):
        raise ValueError("trailing bytes after btsnoop records")


def _one(items, label: str) -> bytes:
    if len(items) != 1:
        raise ValueError(f"capture must contain exactly one {label}; found {len(items)}")
    return items[0]


def _auth_material(events) -> _AuthMaterial:
    auth = [event for event in events if event[2] == _AUTH_HANDLE]
    if sum(direction == "out" and op == 0x52 and value == _HDR_SEND_KEY
           for direction, op, _, value in auth) != 1:
        raise ValueError("capture lacks a unique key-transfer header")
    if sum(direction == "out" and op == 0x52 and value == _HDR_SEND_INFO
           for direction, op, _, value in auth) != 1:
        raise ValueError("capture lacks a unique login-info header")
    rand = _one([value[2:] for direction, op, _, value in auth
                 if direction == "out" and op == 0x52 and len(value) == 18
                 and value[:2] == b"\x01\x00"], "client random parcel")
    remote_key = _one([value[4:20] for direction, op, _, value in auth
                       if direction == "in" and op == 0x1B and len(value) == 20
                       and value[:4] == bytes.fromhex("0000020d")], "device key parcel")
    remote_info = _one([value[4:36] for direction, op, _, value in auth
                        if direction == "in" and op == 0x1B and len(value) == 36
                        and value[:4] == bytes.fromhex("0000020c")], "device login proof")
    login_info = _one([value[2:] for direction, op, _, value in auth
                       if direction == "out" and op == 0x52 and len(value) == 34
                       and value[:2] == b"\x01\x00"], "client login proof")
    return _AuthMaterial(rand, remote_key, remote_info, login_info)


def _tx_frames(events) -> tuple[_CipherFrame, ...]:
    frames = []
    state = None
    for direction, op, handle, value in events:
        if handle != _TX_HANDLE:
            continue
        if direction == "out" and op == 0x52 and value == _TX_HEADER:
            if state is not None:
                raise ValueError("overlapping MIoT request transfers")
            expected = int.from_bytes(value[4:6], "little")
            if expected != 1:
                raise ValueError("multi-parcel MIoT requests are unsupported")
            state = "ready"
        elif state == "ready" and direction == "in" and op == 0x1B and value == _RCV_RDY:
            state = "parcel"
        elif state == "parcel" and direction == "out" and op == 0x52:
            if len(value) < 8 or value[:2] != b"\x01\x00":
                raise ValueError("invalid MIoT request parcel")
            counter = int.from_bytes(value[2:4], "little")
            frames.append(_CipherFrame(counter, value[4:]))
            state = "ack"
        elif state == "ack" and direction == "in" and op == 0x1B and value == _RCV_OK:
            state = None
    if state is not None:
        raise ValueError("incomplete MIoT request transfer")
    return tuple(frames)


def _rx_frames(events) -> tuple[_CipherFrame, ...]:
    frames = []
    for direction, op, handle, value in events:
        if (direction == "in" and op == 0x1B and handle == _RX_HANDLE
                and len(value) >= 10 and value[:4] == bytes.fromhex("00000200")):
            counter = int.from_bytes(value[4:6], "little")
            frames.append(_CipherFrame(counter, value[6:]))
    return tuple(frames)


def _decode_frames(
    frames, key: bytes, iv: bytes, *, direction: str
) -> tuple[FrameResult, ...]:
    results = []
    for frame in frames:
        try:
            plaintext = decrypt_ccm(key, iv, frame.counter, frame.ciphertext)
        except PayloadAuthenticationError:
            results.append(FrameResult(frame.counter, len(frame.ciphertext), False))
            continue

        try:
            if direction == "tx":
                properties = parse_miot_set_request(plaintext)
                transaction_id = int.from_bytes(plaintext[2:4], "little")
                results.append(FrameResult(
                    frame.counter, len(frame.ciphertext), True, "SetProperty", properties,
                    transaction_id=transaction_id,
                ))
            else:
                try:
                    message = parse_miot_message(plaintext)
                except ValueError:
                    transaction_id, response_codes = parse_set_property_response(plaintext)
                    results.append(FrameResult(
                        frame.counter, len(frame.ciphertext), True,
                        "SetPropertyResp", (), response_codes,
                        transaction_id=transaction_id,
                    ))
                else:
                    properties = tuple(
                        PropertyValue(p.siid, p.piid, p.value_type, p.value)
                        for p in message.properties
                    )
                    results.append(FrameResult(
                        frame.counter, len(frame.ciphertext), True,
                        message.name, properties,
                        transaction_id=message.transaction_id,
                    ))
        except ValueError as err:
            results.append(FrameResult(
                frame.counter, len(frame.ciphertext), True, parse_error=str(err)
            ))
    return tuple(results)


def decode_capture(path: str | Path, token: bytes | None = None) -> CaptureResult:
    """Inspect the pinned capture; never returns keys, tokens, or ciphertext bytes."""
    events = tuple(_att_events(path))
    auth = _auth_material(events)
    tx = _tx_frames(events)
    rx = _rx_frames(events)
    if not tx:
        raise ValueError("capture contains no supported MIoT request transactions")
    if token is None:
        return CaptureResult(
            "blocked_missing_token", None,
            tuple(FrameResult(f.counter, len(f.ciphertext)) for f in tx),
            tuple(FrameResult(f.counter, len(f.ciphertext)) for f in rx),
        )
    if not isinstance(token, (bytes, bytearray)) or len(token) != 12:
        raise ValueError("S5 capture verification requires the 12-byte token")
    keys = _session_keys(bytes(token), auth)
    tx_results = _decode_frames(tx, keys.app_key, keys.app_iv, direction="tx")
    rx_results = _decode_frames(rx, keys.dev_key, keys.dev_iv, direction="rx")
    all_frames = tx_results + rx_results
    if all(frame.authenticated is True for frame in all_frames):
        if not all(frame.message_type is not None and frame.parse_error is None for frame in all_frames):
            status = "payload_parse_failed"
        else:
            tx_ids = [frame.transaction_id for frame in tx_results]
            responses = [frame for frame in rx_results if frame.message_type == "SetPropertyResp"]
            response_ids = [frame.transaction_id for frame in responses]
            response_codes = [code for frame in responses for _, _, code in frame.response_codes]
            if response_ids != tx_ids:
                status = "response_mismatch"
            elif any(code != 0 for code in response_codes):
                status = "command_rejected"
            else:
                status = "decoded"
    else:
        status = "payload_auth_failed"
    return CaptureResult(status, True, tx_results, rx_results)

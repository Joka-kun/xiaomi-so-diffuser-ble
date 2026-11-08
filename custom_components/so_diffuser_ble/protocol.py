"""Capture-verified auth/framing helpers and fixed UI-property encoders."""
from __future__ import annotations

import hashlib
import hmac
import re
import struct
from dataclasses import dataclass


class AuthenticationError(ValueError):
    """A captured S5 login proof did not match the supplied token."""


class PayloadAuthenticationError(Exception):
    """An AES-CCM authentication tag did not validate."""


@dataclass(frozen=True)
class _AuthMaterial:
    rand: bytes
    remote_key: bytes
    remote_info: bytes
    login_info: bytes


@dataclass(frozen=True)
class _SessionKeys:
    dev_key: bytes
    app_key: bytes
    dev_iv: bytes
    app_iv: bytes


def decode_token_hex(text: str) -> bytes:
    if not isinstance(text, str) or re.fullmatch(r"[0-9a-fA-F]{24}", text) is None:
        raise ValueError("S5 token file must contain exactly 24 hexadecimal characters")
    return bytes.fromhex(text)


def hkdf_sha256(ikm: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    if not 0 <= length <= 255 * hashlib.sha256().digest_size:
        raise ValueError("HKDF output length is out of range")
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    output = bytearray()
    block = b""
    for counter in range(1, (length + 31) // 32 + 1):
        block = hmac.new(prk, block + info + bytes([counter]), hashlib.sha256).digest()
        output.extend(block)
    return bytes(output[:length])


def ccm_nonce(iv: bytes, counter: int) -> bytes:
    if len(iv) != 4 or not 0 <= counter <= 0xFFFFFFFF:
        raise ValueError("invalid S5 AES-CCM IV or counter")
    return iv + bytes(4) + struct.pack("<I", counter)


def decrypt_ccm(key: bytes, iv: bytes, counter: int, ciphertext: bytes) -> bytes:
    if len(key) != 16 or len(ciphertext) < 4:
        raise ValueError("invalid S5 AES-CCM key or ciphertext length")
    try:
        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives.ciphers.aead import AESCCM
    except ImportError as exc:
        raise RuntimeError("the cryptography package is required for AES-CCM") from exc
    try:
        return AESCCM(key, tag_length=4).decrypt(ccm_nonce(iv, counter), ciphertext, None)
    except InvalidTag as exc:
        raise PayloadAuthenticationError("S5 AES-CCM tag validation failed") from exc


def _session_keys(token: bytes, auth: _AuthMaterial) -> _SessionKeys:
    if not isinstance(token, bytes) or not token:
        raise ValueError("S5 token must be non-empty bytes")
    salt = auth.rand + auth.remote_key
    material = hkdf_sha256(token, salt, b"mible-login-info", 64)
    keys = _SessionKeys(material[:16], material[16:32], material[32:36], material[36:40])
    remote_proof = hmac.new(keys.dev_key, auth.remote_key + auth.rand, hashlib.sha256).digest()
    login_proof = hmac.new(keys.app_key, salt, hashlib.sha256).digest()
    if not hmac.compare_digest(remote_proof, auth.remote_info):
        raise AuthenticationError("S5 device login proof rejected the token")
    if not hmac.compare_digest(login_proof, auth.login_info):
        raise AuthenticationError("S5 client login proof rejected the token")
    return keys


def derive_login_material(
    token: bytes, rand: bytes, remote_key: bytes, remote_info: bytes
) -> tuple[bytes, _SessionKeys]:
    if len(rand) != 16 or len(remote_key) != 16 or len(remote_info) != 32:
        raise ValueError("invalid S5 login transcript lengths")
    salt = rand + remote_key
    material = hkdf_sha256(token, salt, b"mible-login-info", 64)
    login_info = hmac.new(material[16:32], salt, hashlib.sha256).digest()
    auth = _AuthMaterial(rand, remote_key, remote_info, login_info)
    return login_info, _session_keys(token, auth)


LIGHT_ENABLE_BIT = 0x80
LIGHT_VALUE_MASK = 0x7F
LIGHT_MAX_BRIGHTNESS = 100
LIGHT_GRADIENT_ON = 238
LIGHT_GRADIENT_OFF = 228


FIXED_PROPERTIES = {
    "power": (2, 1004, 1, 1, 0, 1),
    "fragrance_out_time": (3, 3, 1, 1, 3, 30),
    "idle_time": (3, 4, 1, 1, 0, 30),
    "light": (3, 8, 1, 1, 0, 255),
    "color": (3, 9, 5, 4, 0, 0xFFFFFF),
}


def light_is_on(value: int | None) -> bool:
    """Return the main light-enable bit used by the Mi Home UI."""
    return type(value) is int and bool(value & LIGHT_ENABLE_BIT)


def light_is_gradient(value: int | None) -> bool:
    """Mi Home Automatic Gradient uses low-seven-bit values above 100.

    The original plugin calls this internal state ``isBreathingLight``.
    """
    return type(value) is int and (value & LIGHT_VALUE_MASK) > LIGHT_MAX_BRIGHTNESS


def light_brightness_to_ha(value: int | None) -> int | None:
    """Convert an enabled steady-light value to HA's 0..255 brightness scale."""
    if not light_is_on(value) or light_is_gradient(value):
        return None
    level = value & LIGHT_VALUE_MASK
    if not 1 <= level <= LIGHT_MAX_BRIGHTNESS:
        return None
    return round(level * 255 / LIGHT_MAX_BRIGHTNESS)


def light_value_from_ha_brightness(brightness: int) -> int:
    """Encode HA brightness 1..255 as the S5 1..100 value plus enable bit."""
    if type(brightness) is not int or not 1 <= brightness <= 255:
        raise ValueError("HA brightness must be an integer from 1 to 255")
    level = max(1, min(LIGHT_MAX_BRIGHTNESS, round(brightness * LIGHT_MAX_BRIGHTNESS / 255)))
    return LIGHT_ENABLE_BIT | level


def light_value_off(current: int | None) -> int:
    """Mirror Mi Home's OFF action: clear bit 7 and preserve the selected mode/level."""
    if current is None:
        return 0
    if type(current) is not int or not 0 <= current <= 255:
        raise ValueError("invalid S5 light state")
    return current & LIGHT_VALUE_MASK


def light_value_restore(current: int | None) -> int:
    """Re-enable the last selected light mode/level, defaulting to steady 100%."""
    if current is None:
        return LIGHT_ENABLE_BIT | LIGHT_MAX_BRIGHTNESS
    if type(current) is not int or not 0 <= current <= 255:
        raise ValueError("invalid S5 light state")
    level = current & LIGHT_VALUE_MASK
    if level == 0:
        level = LIGHT_MAX_BRIGHTNESS
    return LIGHT_ENABLE_BIT | level


def encode_fixed_property_set(transaction_id: int, name: str, value: int) -> bytes:
    """Encode only the explicitly mapped S5 UI properties."""
    if type(transaction_id) is not int or not 0 <= transaction_id <= 0xFFFF:
        raise ValueError("MIoT transaction id is out of range")
    if name not in FIXED_PROPERTIES or type(value) is not int:
        raise ValueError("unsupported S5 property or value type")
    siid, piid, value_type, width, minimum, maximum = FIXED_PROPERTIES[name]
    if not minimum <= value <= maximum or (name == "idle_time" and value in (1, 2)):
        raise ValueError("S5 property value is outside the UI allowlist")
    if name == "light" and not (value <= 100 or value == 110 or 128 <= value <= 228 or value == 238):
        raise ValueError("S5 light value is outside the UI allowlist")

    body = (
        b"\x01"
        + bytes([siid])
        + struct.pack("<H", piid)
        + struct.pack("<H", (value_type << 12) | width)
        + value.to_bytes(width, "little")
    )
    return struct.pack("<HHB", 0x2000 | (5 + len(body)), transaction_id, 0) + body


def encode_power_set(transaction_id: int, enabled: bool) -> bytes:
    """Encode the bundle-mapped 2.1004 uint8 switch payload; physical effect is unverified."""
    if type(enabled) is not bool:
        raise TypeError("power state must be bool")
    return encode_fixed_property_set(transaction_id, "power", int(enabled))


def encrypt_tx_parcel(app_key: bytes, app_iv: bytes, counter: int, plaintext: bytes) -> bytes:
    if len(app_key) != 16 or len(app_iv) != 4:
        raise ValueError("invalid S5 application key or IV")
    if type(counter) is not int or not 0 <= counter <= 0xFFFF:
        raise ValueError("S5 parcel counter is out of range")
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESCCM
    except ImportError as exc:
        raise RuntimeError("the cryptography package is required for AES-CCM") from exc
    ciphertext = AESCCM(app_key, tag_length=4).encrypt(
        ccm_nonce(app_iv, counter), plaintext, None
    )
    return b"\x01\x00" + struct.pack("<H", counter) + ciphertext


def parse_set_property_response(packet: bytes) -> tuple[int, tuple[tuple[int, int, int], ...]]:
    if len(packet) < 6:
        raise ValueError("MIoT response is too short")
    header = int.from_bytes(packet[:2], "little")
    if header >> 12 != 2 or header & 0x0FFF != len(packet) or packet[4] != 1:
        raise ValueError("invalid S5 SetPropertyResp header")
    body = packet[5:]
    if not body or len(body) != 1 + 5 * body[0]:
        raise ValueError("invalid S5 SetPropertyResp body")
    results = tuple(
        (
            body[offset],
            int.from_bytes(body[offset + 1 : offset + 3], "little"),
            int.from_bytes(body[offset + 3 : offset + 5], "little"),
        )
        for offset in range(1, len(body), 5)
    )
    return int.from_bytes(packet[2:4], "little"), results

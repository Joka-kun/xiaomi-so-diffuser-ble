import hashlib
import hmac
import struct
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from s5_payload_decoder import (
    AuthenticationError,
    PayloadAuthenticationError,
    ccm_nonce,
    decode_capture,
    decrypt_ccm,
    hkdf_sha256,
    parse_miot_set_request,
)

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESCCM
except ImportError:
    AESCCM = None


def _record(direction, opcode, handle, value):
    att = bytes([opcode]) + struct.pack("<H", handle) + value
    l2cap = struct.pack("<HH", len(att), 4) + att
    acl = struct.pack("<HH", 0x2040, len(l2cap)) + l2cap
    packet = b"\x02" + acl
    flags = 1 if direction == "in" else 0
    return struct.pack(">IIIIQ", len(packet), len(packet), flags, 0, 0) + packet


def _miot_packet(opcode, transaction_id, siid, piid, value_type, value, width):
    body = (
        b"\x01"
        + bytes([siid])
        + piid.to_bytes(2, "little")
        + ((value_type << 12) | width).to_bytes(2, "little")
        + value.to_bytes(width, "little")
    )
    length = 5 + len(body)
    return (0x2000 | length).to_bytes(2, "little") + transaction_id.to_bytes(2, "little") + bytes([opcode]) + body


def _set_response(transaction_id, siid, piid, result_code):
    body = b"\x01" + bytes([siid]) + piid.to_bytes(2, "little") + result_code.to_bytes(2, "little")
    length = 5 + len(body)
    return (0x2000 | length).to_bytes(2, "little") + transaction_id.to_bytes(2, "little") + b"\x01" + body


def _synthetic_capture(token, *, response_transaction_delta=0, response_code=0):
    rand = bytes(range(16))
    remote_key = bytes(range(16, 32))
    salt = rand + remote_key
    material = hkdf_sha256(token, salt, b"mible-login-info", 64)
    dev_key, app_key = material[:16], material[16:32]
    dev_iv, app_iv = material[32:36], material[36:40]
    remote_info = hmac.new(dev_key, remote_key + rand, hashlib.sha256).digest()
    login_info = hmac.new(app_key, salt, hashlib.sha256).digest()

    requests = (
        (3, 5, 3, 2054, 2),
        (3, 5, 3, 4095, 2),
        (3, 7, 1, 255, 1),
    )
    events = [
        ("out", 0x52, 0x0018, bytes.fromhex("0000000b0100")),
        ("in", 0x1B, 0x0018, bytes.fromhex("00000101")),
        ("out", 0x52, 0x0018, b"\x01\x00" + rand),
        ("in", 0x1B, 0x0018, bytes.fromhex("00000100")),
        ("in", 0x1B, 0x0018, bytes.fromhex("0000020d") + remote_key),
        ("out", 0x52, 0x0018, bytes.fromhex("00000300")),
        ("in", 0x1B, 0x0018, bytes.fromhex("0000020c") + remote_info),
        ("out", 0x52, 0x0018, bytes.fromhex("00000300")),
        ("out", 0x52, 0x0018, bytes.fromhex("0000000a0100")),
        ("in", 0x1B, 0x0018, bytes.fromhex("00000101")),
        ("out", 0x52, 0x0018, b"\x01\x00" + login_info),
        ("in", 0x1B, 0x0018, bytes.fromhex("00000100")),
    ]

    rx_counter = 1
    for tx_counter, (siid, piid, value_type, value, width) in enumerate(requests):
        tx_plaintext = _miot_packet(0, tx_counter + 1, siid, piid, value_type, value, width)
        tx_ciphertext = AESCCM(app_key, tag_length=4).encrypt(
            ccm_nonce(app_iv, tx_counter), tx_plaintext, None
        )
        events.extend([
            ("out", 0x52, 0x0021, bytes.fromhex("000000000100")),
            ("in", 0x1B, 0x0021, bytes.fromhex("00000101")),
            ("out", 0x52, 0x0021, b"\x01\x00" + tx_counter.to_bytes(2, "little") + tx_ciphertext),
            ("in", 0x1B, 0x0021, bytes.fromhex("00000100")),
        ])

        for response in (
            _set_response(tx_counter + 1 + response_transaction_delta, siid, piid, response_code),
            _miot_packet(4, tx_counter + 1, siid, piid, value_type, value, width),
        ):
            rx_ciphertext = AESCCM(dev_key, tag_length=4).encrypt(
                ccm_nonce(dev_iv, rx_counter), response, None
            )
            events.append((
                "in", 0x1B, 0x0024,
                bytes.fromhex("00000200") + rx_counter.to_bytes(2, "little") + rx_ciphertext,
            ))
            rx_counter += 1

    return b"btsnoop\x00" + struct.pack(">II", 1, 1002) + b"".join(
        _record(*event) for event in events
    )


class S5PayloadDecoderTests(unittest.TestCase):
    def test_hkdf_matches_rfc5869_case_1(self):
        ikm = bytes.fromhex("0b" * 22)
        salt = bytes.fromhex("000102030405060708090a0b0c")
        info = bytes.fromhex("f0f1f2f3f4f5f6f7f8f9")
        expected = bytes.fromhex(
            "3cb25f25faacd57a90434f64d0362f2a"
            "2d2d0a90cf1a5a4c5db02d56ecc4c5bf"
            "34007208d5b887185865"
        )
        self.assertEqual(hkdf_sha256(ikm, salt, info, 42), expected)

    def test_s5_nonce_layout_is_12_bytes(self):
        self.assertEqual(
            ccm_nonce(bytes.fromhex("a0a1a2a3"), 1),
            bytes.fromhex("a0a1a2a30000000001000000"),
        )

    @unittest.skipIf(AESCCM is None, "cryptography package is required")
    def test_aes_ccm_fixed_vector_decrypts_and_authenticates(self):
        key = bytes(range(16))
        ciphertext_and_tag = bytes.fromhex("00dc4a31be547aaa53329148eb734edfd0")
        expected = bytes.fromhex("0d20340000010305000230ff0f")
        self.assertEqual(
            decrypt_ccm(key, bytes.fromhex("a0a1a2a3"), 1, ciphertext_and_tag),
            expected,
        )
        damaged = ciphertext_and_tag[:-1] + bytes([ciphertext_and_tag[-1] ^ 1])
        with self.assertRaises(PayloadAuthenticationError):
            decrypt_ccm(key, bytes.fromhex("a0a1a2a3"), 1, damaged)

    def test_miot_set_request_parser_reads_spec_v2_property(self):
        packet = _miot_packet(0, 43, 3, 5, 3, 2054, 2)
        parsed = parse_miot_set_request(packet)
        self.assertEqual(len(parsed), 1)
        self.assertEqual((parsed[0].siid, parsed[0].piid, parsed[0].vtype, parsed[0].value), (3, 5, 3, 2054))

    @unittest.skipIf(AESCCM is None, "cryptography package is required")
    def test_synthetic_capture_verifies_auth_and_decodes_requests_responses(self):
        token = bytes(range(12))
        payload = _synthetic_capture(token)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.btsnoop"
            path.write_bytes(payload)
            result = decode_capture(path, token)

        self.assertEqual(result.status, "decoded")
        self.assertTrue(result.auth_verified)
        self.assertEqual(tuple(frame.counter for frame in result.tx), (0, 1, 2))
        self.assertEqual(len(result.rx), 6)
        self.assertTrue(all(frame.authenticated for frame in result.tx + result.rx))
        self.assertEqual(
            [frame.properties[0].value for frame in result.tx],
            [2054, 4095, 255],
        )
        responses = [frame for frame in result.rx if frame.message_type == "SetPropertyResp"]
        changes = [frame for frame in result.rx if frame.message_type == "PropertyChanged"]
        self.assertEqual(len(responses), 3)
        self.assertEqual(
            [frame.transaction_id for frame in responses],
            [frame.transaction_id for frame in result.tx],
        )
        self.assertTrue(all(code == 0 for frame in responses for _, _, code in frame.response_codes))
        self.assertEqual(len(changes), 3)


    @unittest.skipIf(AESCCM is None, "cryptography package is required")
    def test_response_transaction_mismatch_is_not_reported_as_success(self):
        payload = _synthetic_capture(bytes(range(12)), response_transaction_delta=1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.btsnoop"
            path.write_bytes(payload)
            result = decode_capture(path, bytes(range(12)))
        self.assertEqual(result.status, "response_mismatch")

    @unittest.skipIf(AESCCM is None, "cryptography package is required")
    def test_nonzero_set_property_response_is_not_reported_as_success(self):
        payload = _synthetic_capture(bytes(range(12)), response_code=1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.btsnoop"
            path.write_bytes(payload)
            result = decode_capture(path, bytes(range(12)))
        self.assertEqual(result.status, "command_rejected")

    @unittest.skipIf(AESCCM is None, "cryptography package is required")
    def test_wrong_token_fails_login_proof(self):
        payload = _synthetic_capture(bytes(range(12)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.btsnoop"
            path.write_bytes(payload)
            with self.assertRaises(AuthenticationError):
                decode_capture(path, bytes(range(1, 13)))


if __name__ == "__main__":
    unittest.main()

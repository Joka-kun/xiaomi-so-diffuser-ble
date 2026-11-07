import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import custom_components.so_diffuser_ble.client as s5
from tools.s5_payload_decoder import hkdf_sha256


class MiotParserTests(unittest.TestCase):
    def test_property_changed_decodes_uint16_value(self):
        # MIoT Spec-v2 PropertyChanged: SIID 3, PIID 5, uint16=2054.
        body = (
            b"\x01"
            + b"\x03"
            + (5).to_bytes(2, "little")
            + ((3 << 12) | 2).to_bytes(2, "little")
            + (2054).to_bytes(2, "little")
        )
        payload_len = 5 + len(body)
        packet = (0x2000 | payload_len).to_bytes(2, "little") + b"\x01\x00\x04" + body

        parse = getattr(s5, "parse_miot_message", None)
        self.assertTrue(callable(parse), "MIoT Spec-v2 parser is not implemented")
        if not callable(parse):
            return
        result = parse(packet)

        self.assertEqual(result.name, "PropertyChanged")
        self.assertEqual(len(result.properties), 1)
        self.assertEqual(
            (result.properties[0].siid, result.properties[0].piid,
             result.properties[0].value_type, result.properties[0].value),
            (3, 5, 3, 2054),
        )

    def test_login_material_reproduces_both_hmac_proofs(self):
        import hashlib
        import hmac
        token = bytes(range(12))
        rand = bytes(range(16, 32))
        remote_key = bytes(range(32, 48))
        salt = rand + remote_key
        material = hkdf_sha256(token, salt, b"mible-login-info", 64)
        remote_info = hmac.new(material[:16], remote_key + rand, hashlib.sha256).digest()
        expected_login_info = hmac.new(material[16:32], salt, hashlib.sha256).digest()

        derive = getattr(s5, "_derive_login_material", None)
        self.assertTrue(callable(derive), "S5 login proof derivation is not implemented")
        if not callable(derive):
            return
        login_info, keys = derive(token, rand, remote_key, remote_info)

        self.assertEqual(login_info, expected_login_info)
        self.assertEqual(len(keys.dev_key), 16)
        self.assertEqual(len(keys.app_key), 16)


class ReadOnlyClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_client_accepts_the_capture_verified_12_byte_token(self):
        client_type = getattr(s5, "S5ReadOnlyClient", None)
        self.assertTrue(callable(client_type), "S5 read-only GATT client is not implemented")

        class DummyGatt:
            start_notify = write_gatt_char = lambda *args, **kwargs: None

        client = client_type(DummyGatt(), bytes(range(12)))
        self.assertFalse(client.authenticated)

    async def test_client_rejects_unverified_token_lengths(self):
        client_type = s5.S5ReadOnlyClient

        class DummyGatt:
            start_notify = write_gatt_char = lambda *args, **kwargs: None

        for token in (bytes(range(11)), bytes(range(16))):
            with self.subTest(length=len(token)), self.assertRaisesRegex(ValueError, "12 bytes"):
                client_type(DummyGatt(), token)

    @unittest.skipUnless(importlib.util.find_spec("cryptography"), "cryptography required")
    async def test_authenticated_listener_never_writes_properties(self):
        import hashlib
        import hmac
        from cryptography.hazmat.primitives.ciphers.aead import AESCCM
        client_type = getattr(s5, "S5ReadOnlyClient", None)
        self.assertTrue(callable(client_type), "S5 read-only GATT client is not implemented")
        if not callable(client_type):
            return

        control = "00000010-0000-1000-8000-00805f9b34fb"
        auth = "00000019-0000-1000-8000-00805f9b34fb"
        data_tx = "0000001a-0000-1000-8000-00805f9b34fb"
        data_rx = "0000001b-0000-1000-8000-00805f9b34fb"
        cmd_login = bytes.fromhex("24000000")
        hdr_key = bytes.fromhex("0000000b0100")
        hdr_info = bytes.fromhex("0000000a0100")
        rcv_rdy = bytes.fromhex("00000101")
        rcv_ok = bytes.fromhex("00000100")
        ack_data = bytes.fromhex("00000300")
        cfm_login = bytes.fromhex("21000000")
        token = bytes(range(12))

        class FakeGatt:
            is_connected = True

            def __init__(self):
                self.callbacks = {}
                self.writes = []
                self.control_writes = []
                self.remote_key = bytes(range(64, 80))
                self.remote_info = None
                self.login_info = None
                self.keys = None
                self.remote_key_sent = False
                self.remote_info_sent = False
                self.login_info_verified = False
                self.cmd_login_seen = False
                self.flow_error = False

            async def start_notify(self, uuid, callback):
                self.callbacks[uuid] = callback

            def emit(self, uuid, data):
                self.callbacks[uuid](None, bytearray(data))

            async def write_gatt_char(self, uuid, data, response=False):
                data = bytes(data)
                self.writes.append((uuid, data, response))
                if uuid == control:
                    self.control_writes.append(data)
                if uuid == control and data == b"\xA4":
                    self.emit(auth, b"\x00\x00\x04\x00ab")
                    self.emit(auth, b"\x00\x00\x04\x01" + bytes(240))
                elif uuid == control and data == cmd_login:
                    self.cmd_login_seen = True
                elif uuid == auth and data == hdr_key:
                    if not self.cmd_login_seen:
                        self.flow_error = True
                    self.emit(auth, rcv_rdy)
                elif uuid == auth and len(data) == 18 and data[:2] == b"\x01\x00":
                    rand = data[2:]
                    salt = rand + self.remote_key
                    material = hkdf_sha256(token, salt, b"mible-login-info", 64)
                    self.keys = (material[:16], material[16:32], material[32:36], material[36:40])
                    self.remote_info = hmac.new(material[:16], self.remote_key + rand, hashlib.sha256).digest()
                    self.login_info = hmac.new(material[16:32], salt, hashlib.sha256).digest()
                    self.emit(auth, rcv_ok)
                    self.emit(auth, b"\x00\x00\x02\x0d" + self.remote_key)
                    self.remote_key_sent = True
                elif uuid == auth and data == ack_data and self.remote_key_sent and not self.remote_info_sent:
                    self.emit(auth, b"\x00\x00\x02\x0c" + self.remote_info)
                    self.remote_info_sent = True
                elif uuid == auth and data == hdr_info:
                    self.emit(auth, rcv_rdy)
                elif uuid == auth and len(data) == 34 and data[:2] == b"\x01\x00":
                    self.login_info_verified = data[2:] == self.login_info
                    if self.login_info_verified:
                        self.emit(auth, rcv_ok)
                        self.emit(control, cfm_login)

        fake = FakeGatt()
        reader = client_type(fake, token, timeout=0.2, auth_quiet=0.01)
        self.assertFalse(hasattr(reader, "set_property"))
        self.assertFalse(hasattr(reader, "write_property"))

        await reader.authenticate()
        self.assertTrue(fake.login_info_verified)
        self.assertFalse(fake.flow_error)
        self.assertEqual(fake.control_writes, [b"\xA4", cmd_login])
        self.assertEqual(
            [data for uuid, data, _ in fake.writes if uuid == auth and data[:3] == b"\x00\x00\x05"],
            [b"\x00\x00\x05\x00ab", b"\x00\x00\x05\x01" + bytes(240)],
        )
        self.assertEqual(
            [data for uuid, data, _ in fake.writes if uuid == data_tx], []
        )

        fake.writes.clear()
        device_key, _, device_iv, _ = fake.keys
        body = b"\x01\x03\x05\x00" + ((3 << 12) | 2).to_bytes(2, "little") + (2054).to_bytes(2, "little")
        packet_len = 5 + len(body)
        plaintext = (0x2000 | packet_len).to_bytes(2, "little") + b"\x01\x00\x04" + body
        counter = 9
        nonce = device_iv + bytes(4) + counter.to_bytes(4, "little")
        ciphertext = AESCCM(device_key, tag_length=4).encrypt(nonce, plaintext, None)
        fake.emit(data_rx, b"\x00\x00\x02\x00" + counter.to_bytes(2, "little") + ciphertext)

        stream = reader.iter_property_changes(timeout=0.2)
        message = await anext(stream)
        await stream.aclose()
        self.assertEqual(message.properties[0].value, 2054)
        data_writes = [(uuid, value) for uuid, value, _ in fake.writes if uuid == data_rx]
        self.assertEqual(data_writes, [(data_rx, ack_data)])
        self.assertEqual(
            [data for uuid, data, _ in fake.writes if uuid == data_tx], []
        )


if __name__ == "__main__":
    unittest.main()

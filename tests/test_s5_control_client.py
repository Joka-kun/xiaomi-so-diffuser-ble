import asyncio
import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.so_diffuser_ble.client import ProtocolTimeout, S5ClientError, S5ControlClient
from custom_components.so_diffuser_ble.protocol import _SessionKeys, encode_fixed_property_set, encode_power_set


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "cryptography required")
class S5ControlClientTests(unittest.IsolatedAsyncioTestCase):
    def _property_packet(self, opcode, transaction_id, value, key=(2, 1004), value_type=1, width=1):
        siid, piid = key
        if opcode == 1:
            body = b"\x01" + bytes([siid]) + piid.to_bytes(2, "little") + int(value).to_bytes(2, "little")
        else:
            type_length = (value_type << 12) | width
            body = b"\x01" + bytes([siid]) + piid.to_bytes(2, "little") + type_length.to_bytes(2, "little") + int(value).to_bytes(width, "little")
        return (0x2000 | (5 + len(body))).to_bytes(2, "little") + transaction_id.to_bytes(2, "little") + bytes([opcode]) + body

    async def _run_set_power(self, response_code=0, reported_state=True):
        return await self._run_set(
            "set_power", True, "power", (2, 1004), 1, 1,
            response_code=response_code,
            reported_value=None if reported_state is None else int(reported_state),
        )

    async def _run_set(self, method, value, name, key, value_type, width, response_code=0, reported_value=None, reported_values=None):
        from cryptography.hazmat.primitives.ciphers.aead import AESCCM

        token = bytes(range(12))
        keys = _SessionKeys(bytes(range(16)), bytes(range(16, 32)), bytes.fromhex("a0a1a2a3"), bytes.fromhex("b0b1b2b3"))
        client_type = S5ControlClient
        data_tx, data_rx = client_type.UUID_DATA_TX, client_type.UUID_DATA_RX
        ready, accepted = bytes.fromhex("00000101"), bytes.fromhex("00000100")
        tx_header = client_type.TX_HEADER
        test_case = self

        class FakeGatt:
            is_connected = True

            def __init__(self):
                self.callbacks = {}
                self.writes = []
                self.command = None

            async def start_notify(self, uuid, callback):
                self.callbacks[uuid] = callback

            def emit(self, uuid, data):
                self.callbacks[uuid](None, bytearray(data))

            def encrypt_rx(self, plaintext, counter):
                nonce = keys.dev_iv + bytes(4) + counter.to_bytes(4, "little")
                ciphertext = AESCCM(keys.dev_key, tag_length=4).encrypt(nonce, plaintext, None)
                return client_type.DIRECT_DATA_PREFIX + counter.to_bytes(2, "little") + ciphertext

            async def write_gatt_char(self, uuid, data, response=False):
                data = bytes(data)
                self.writes.append((uuid, data, response))
                if uuid == data_tx and data == tx_header:
                    self.emit(data_tx, ready)
                    return
                if uuid != data_tx:
                    return
                counter = int.from_bytes(data[2:4], "little")
                nonce = keys.app_iv + bytes(4) + counter.to_bytes(4, "little")
                self.command = AESCCM(keys.app_key, tag_length=4).decrypt(nonce, data[4:], None)
                transaction_id = int.from_bytes(self.command[2:4], "little")
                self.emit(data_tx, accepted)
                self.emit(
                    data_rx,
                    self.encrypt_rx(test_case._property_packet(1, transaction_id, response_code, key), 5),
                )
                if response_code == 0:
                    values = reported_values if reported_values is not None else (
                        (reported_value,) if reported_value is not None else ()
                    )
                    for index, observed_value in enumerate(values):
                        self.emit(
                            data_rx,
                            self.encrypt_rx(
                                test_case._property_packet(
                                    4, 0, observed_value, key, value_type, width
                                ),
                                6 + index,
                            ),
                        )

        fake = FakeGatt()
        client = client_type(fake, token, timeout=0.2)
        client._keys = keys
        client._authenticated = True
        await client._start_notifications()

        async def consume():
            async for _ in client.iter_messages(timeout=1):
                pass

        listener = asyncio.create_task(consume())
        await asyncio.sleep(0)
        try:
            await getattr(client, method)(value, timeout=0.5)
        finally:
            listener.cancel()
            await asyncio.gather(listener, return_exceptions=True)
        return fake, client

    async def test_set_power_waits_for_success_response_and_matching_readback(self):
        fake, _ = await self._run_set_power(response_code=0, reported_state=True)
        self.assertEqual(fake.command, encode_power_set(1, True))
        self.assertEqual([data for uuid, data, _ in fake.writes if uuid == S5ControlClient.UUID_DATA_TX][0], S5ControlClient.TX_HEADER)
        self.assertEqual(len([1 for uuid, _, _ in fake.writes if uuid == S5ControlClient.UUID_DATA_TX]), 2)
        self.assertEqual([data for uuid, data, _ in fake.writes if uuid == S5ControlClient.UUID_DATA_RX], [S5ControlClient.ACK_DATA, S5ControlClient.ACK_DATA])

    async def test_set_power_rejects_nonzero_set_response(self):
        with self.assertRaises(S5ClientError):
            await self._run_set_power(response_code=1, reported_state=None)

    async def test_set_power_times_out_if_readback_never_matches(self):
        with self.assertRaisesRegex(ProtocolTimeout, "read-back"):
            await self._run_set_power(response_code=0, reported_state=False)

    async def test_stale_long_spray_state_before_new_pause_is_not_an_error(self):
        # Reproduces: switch.turn_off successfully restores the pause,
        # but an earlier PropertyChanged(3.4=0) arrives first.
        fake, _ = await self._run_set(
            "set_idle_time", 5, "idle_time", (3, 4), 1, 1,
            reported_values=(0, 5),
        )
        self.assertEqual(fake.command, encode_fixed_property_set(1, "idle_time", 5))

    async def test_stale_power_state_before_acknowledged_new_state_is_ignored(self):
        fake, _ = await self._run_set(
            "set_power", False, "power", (2, 1004), 1, 1,
            reported_values=(1, 0),
        )
        self.assertEqual(fake.command, encode_fixed_property_set(1, "power", 0))

    async def test_all_fixed_ui_setters_match_the_synthetic_response_and_readback(self):
        cases = (
            ("set_fragrance_out_time", "fragrance_out_time", 9, (3, 3), 1, 1),
            ("set_idle_time", "idle_time", 3, (3, 4), 1, 1),
            ("set_idle_time", "idle_time", 0, (3, 4), 1, 1),
            ("set_light", "light", 238, (3, 8), 1, 1),
            ("set_color", "color", 0x123456, (3, 9), 5, 4),
        )
        for method, name, value, key, value_type, width in cases:
            with self.subTest(property=name):
                fake, _ = await self._run_set(method, value, name, key, value_type, width, reported_value=value)
                self.assertEqual(fake.command, encode_fixed_property_set(1, name, value))

    async def test_timer_and_schedule_setters_are_not_exposed(self):
        self.assertFalse(hasattr(S5ControlClient, "set_auto_power_time"))
        self.assertFalse(hasattr(S5ControlClient, "set_repeat"))


if __name__ == "__main__":
    unittest.main()

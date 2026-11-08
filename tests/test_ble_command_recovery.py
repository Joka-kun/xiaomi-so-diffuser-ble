"""Offline fault-injection tests for the real S5 connection lifecycle.

No Home Assistant instance, Bluetooth adapter, token or physical S5 is used.
"""
from __future__ import annotations

import ast
import asyncio
from contextlib import suppress
import logging
from pathlib import Path
from types import SimpleNamespace
import unittest

BASE = Path(__file__).resolve().parents[1] / "custom_components" / "so_diffuser_ble"


class FakeClientError(Exception):
    pass


class FakeHAError(Exception):
    pass


class FakeBleakClient:
    def __init__(self, callback):
        self.callback = callback
        self.is_connected = True
        self.disconnected = asyncio.Event()

    async def disconnect(self):
        if self.is_connected:
            self.is_connected = False
            self.disconnected.set()
            self.callback(self)


class FakeS5Session:
    sessions = []
    fail_next_write = False

    def __init__(self, client, token):
        assert token == b"synthetic-only"
        self.client = client
        self.writes = []
        self.sessions.append(self)

    async def authenticate(self):
        assert self.client.is_connected

    def iter_messages(self):
        async def _messages():
            await self.client.disconnected.wait()
            if False:
                yield None
        return _messages()

    async def set_power(self, enabled):
        self.writes.append(enabled)
        if FakeS5Session.fail_next_write:
            FakeS5Session.fail_next_write = False
            raise FakeClientError("synthetic lost acknowledgement")


class FakeBluetooth:
    BluetoothScanningMode = SimpleNamespace(ACTIVE="active")

    def __init__(self):
        self.connectable = False
        self.lookup_called = asyncio.Event()
        self.callback = None
        self.unsubscribed = 0
        self.connection_count = 0
        self.cleared_history = 0
        self.clients = []

    def async_ble_device_from_address(self, _hass, address, connectable):
        assert address == "AA:BB:CC:DD:EE:FF" and connectable
        self.lookup_called.set()
        return object() if self.connectable else None

    def async_register_callback(self, _hass, callback, matcher, mode):
        assert matcher == {"address": "AA:BB:CC:DD:EE:FF", "connectable": True}
        assert mode == "active"
        self.callback = callback

        def unsubscribe():
            self.unsubscribed += 1
            self.callback = None

        return unsubscribe

    def async_clear_advertisement_history(self, _hass, address):
        assert address == "AA:BB:CC:DD:EE:FF"
        self.cleared_history += 1

    async def establish(self, _cls, _device, _name, *, disconnected_callback, pair):
        assert pair is False
        self.connection_count += 1
        client = FakeBleakClient(disconnected_callback)
        self.clients.append(client)
        return client


class FakeHass:
    config = SimpleNamespace(path=lambda: "/synthetic-ha-config")

    async def async_add_executor_job(self, _func, *_args):
        return b"synthetic-only"

    def async_create_task(self, coroutine):
        return asyncio.create_task(coroutine)


def load_real_coordinator(bluetooth):
    tree = ast.parse((BASE / "coordinator.py").read_text(encoding="utf-8"))
    future = next(node for node in tree.body
                  if isinstance(node, ast.ImportFrom) and node.module == "__future__")
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == "S5Coordinator")
    namespace = {
        "asyncio": asyncio,
        "callback": lambda function: function,
        "suppress": suppress,
        "_LOGGER": logging.getLogger(__name__),
        "bluetooth": bluetooth,
        "BleakClient": FakeBleakClient,
        "establish_connection": bluetooth.establish,
        "HomeAssistantError": FakeHAError,
        "S5ClientError": FakeClientError,
        "S5ControlClient": FakeS5Session,
        "load_device_token": lambda *_args: b"synthetic-only",
        "DEFAULT_MODEL": "bwj.diffuser.s5",
        "get_profile": lambda _model: SimpleNamespace(light=True, temperature=False),
        "light_is_on": lambda _value: True,
        "light_is_gradient": lambda _value: False,
    }
    exec(compile(ast.Module(body=[future, cls], type_ignores=[]),
                 "<actual S5Coordinator>", "exec"), namespace)
    return namespace["S5Coordinator"]


class BLERecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        FakeS5Session.sessions = []
        FakeS5Session.fail_next_write = False
        self.bt = FakeBluetooth()
        self.cls = load_real_coordinator(self.bt)
        self.coordinator = self.cls(FakeHass(), "AA:BB:CC:DD:EE:FF")
        self.coordinator.async_start()
        await asyncio.wait_for(self.bt.lookup_called.wait(), timeout=1)
        self.assertFalse(self.coordinator.connected)

    async def asyncTearDown(self):
        await self.coordinator.async_shutdown()

    async def test_power_command_connects_when_session_was_unavailable(self):
        self.bt.connectable = True
        await asyncio.wait_for(self.coordinator.async_set_power(True), timeout=2)
        self.assertEqual(self.bt.connection_count, 1)
        self.assertEqual(FakeS5Session.sessions[0].writes, [True])
        self.assertTrue(self.coordinator.connected)

    async def test_parallel_commands_share_one_session(self):
        self.bt.connectable = True
        await asyncio.wait_for(asyncio.gather(
            self.coordinator.async_set_power(True),
            self.coordinator.async_set_power(False),
        ), timeout=2)
        self.assertEqual(self.bt.connection_count, 1)
        self.assertEqual(FakeS5Session.sessions[0].writes, [True, False])

    async def test_lost_ack_retires_session_without_replaying_write(self):
        self.bt.connectable = True
        FakeS5Session.fail_next_write = True
        with self.assertRaisesRegex(FakeHAError, "synthetic lost acknowledgement"):
            await asyncio.wait_for(self.coordinator.async_set_power(True), timeout=2)
        first = FakeS5Session.sessions[0]
        await asyncio.wait_for(first.client.disconnected.wait(), timeout=2)
        self.assertEqual(first.writes, [True])
        self.assertEqual(self.bt.cleared_history, 1)
        await asyncio.wait_for(self.coordinator.async_set_power(False), timeout=2)
        self.assertEqual([write for s in FakeS5Session.sessions for write in s.writes],
                         [True, False])
        self.assertGreaterEqual(self.bt.connection_count, 2)

    async def test_queued_command_cannot_reuse_aborting_session(self):
        self.bt.connectable = True
        FakeS5Session.fail_next_write = True
        results = await asyncio.wait_for(asyncio.gather(
            self.coordinator.async_set_power(True),
            self.coordinator.async_set_power(False),
            return_exceptions=True,
        ), timeout=2)
        self.assertIsInstance(results[0], FakeHAError)
        self.assertIsNone(results[1])
        self.assertGreaterEqual(len(FakeS5Session.sessions), 2)
        self.assertEqual(FakeS5Session.sessions[0].writes, [True])
        self.assertEqual([write for session in FakeS5Session.sessions
                          for write in session.writes], [True, False])

    async def test_advertisement_wakes_retry_and_unsubscribes_at_shutdown(self):
        self.bt.connectable = True
        assert self.bt.callback is not None
        self.bt.callback(None, None)
        await asyncio.wait_for(self.coordinator._connected_event.wait(), timeout=2)
        self.assertEqual(self.bt.connection_count, 1)
        await self.coordinator.async_shutdown()
        self.assertEqual(self.bt.unsubscribed, 1)
        self.assertIsNone(self.bt.callback)

    async def test_shutdown_interrupts_pending_command_without_ble_write(self):
        pending = asyncio.create_task(self.coordinator.async_set_power(True))
        await asyncio.sleep(0)
        await self.coordinator.async_shutdown()
        with self.assertRaises(FakeHAError):
            await asyncio.wait_for(pending, timeout=2)
        self.assertEqual(self.bt.connection_count, 0)

    async def test_unknown_command_is_rejected_before_connection(self):
        with self.assertRaises(ValueError):
            await self.coordinator._async_command("format_device", True)
        self.assertEqual(self.bt.connection_count, 0)


def test_power_entity_accepts_commands_without_a_persistent_gatt_session():
    tree = ast.parse((BASE / "switch.py").read_text(encoding="utf-8"))
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == "S5PowerSwitch")
    prop = next(node for node in cls.body
                if isinstance(node, ast.FunctionDef) and node.name == "available")
    assert any(isinstance(node, ast.Return) for node in ast.walk(prop))
    fake_base = type("S5Entity", (), {
        "__init__": lambda self, coordinator, *_args: setattr(self, "coordinator", coordinator),
    })
    namespace = {"S5Entity": fake_base, "SwitchEntity": type("SwitchEntity", (), {})}
    exec(compile(ast.Module(body=[cls], type_ignores=[]),
                 "<actual S5PowerSwitch>", "exec"), namespace)
    entity = namespace["S5PowerSwitch"](SimpleNamespace(connected=False, power=None))
    assert entity.available is True
    assert entity.is_on is None


if __name__ == "__main__":
    unittest.main()

"""Run the real Bluetooth setup-flow discovery methods with a mocked HA scanner.

No radio, network, Xiaomi credentials or private MAC addresses are used.
"""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

from custom_components.so_diffuser_ble.models import advertised_model

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "custom_components" / "so_diffuser_ble" / "config_flow.py"
)


def _load_discovery_methods(bluetooth, sleep):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    klass = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "S5ConfigFlow"
    )
    names = {
        "_remember_candidate",
        "_refresh_candidates",
        "_async_search_nearby",
        "async_step_search",
        "async_step_user",
    }
    methods = [
        node for node in klass.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in names
    ]
    assert len(methods) == len(names)
    isolated_class = ast.ClassDef(
        name="DiscoveryFlow", bases=[], keywords=[], body=methods, decorator_list=[]
    )
    namespace = {
        "__name__": "__discovery_test__",
        "bluetooth": bluetooth,
        "asyncio": SimpleNamespace(sleep=sleep),
        "advertised_model": advertised_model,
        "is_so_candidate_advertisement": lambda info: advertised_model(
            getattr(info, "name", None)
        ) is not None,
        "validate_ble_address": _validate,
        "vol": SimpleNamespace(
            Required=lambda value: value,
            In=lambda choices: choices,
            Schema=lambda fields: fields,
        ),
    }
    constants = [
        node for node in tree.body if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id in {
                "_CHOOSE_DEVICE", "_SEARCH", "_MANUAL",
                "_SEARCH_SECONDS", "_MAX_SCAN_RESULTS",
            }
            for target in node.targets
        )
    ]
    isolated = ast.fix_missing_locations(ast.Module(
        body=[
            ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
            *constants,
            isolated_class,
        ], type_ignores=[]
    ))
    exec(compile(isolated, str(SOURCE), "exec"), namespace)
    return namespace["DiscoveryFlow"]


def _validate(address):
    if not isinstance(address, str) or not re.fullmatch(
        r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}", address, re.I
    ):
        raise ValueError("invalid address")
    return address


class FakeBluetooth:
    BluetoothScanningMode = SimpleNamespace(ACTIVE="active")

    def __init__(self):
        self.cached = []
        self.callback = None
        self.unsubscribed = False
        self.matcher = object()
        self.mode = None
        self.fail = False
        self.active_requests = []
        self.sleep = None

    async def async_request_active_scan(self, hass, duration):
        self.active_requests.append(duration)
        assert self.sleep is not None
        await self.sleep(duration)

    def async_discovered_service_info(self, hass, connectable=True):
        assert connectable is True
        return list(self.cached)

    def async_register_callback(self, hass, callback, matcher, mode):
        if self.fail:
            raise OSError("adapter not available")
        self.callback = callback
        self.matcher = matcher
        self.mode = mode

        def remove():
            self.unsubscribed = True
            self.callback = None

        return remove

    def emit(self, name, address):
        info = SimpleNamespace(name=name, address=address)
        self.cached.append(info)
        if self.callback:
            self.callback(info, object())


class DiscoveryFlowTests(unittest.IsolatedAsyncioTestCase):
    def make_flow(self, bluetooth, sleep):
        bluetooth.sleep = sleep
        cls = _load_discovery_methods(bluetooth, sleep)

        class Flow(cls):
            def __init__(self):
                self.hass = SimpleNamespace(
                    config=SimpleNamespace(language="ru"),
                    async_create_task=asyncio.create_task,
                )
                self._discovered = {}
                self._show_all_candidates = False
                self._search_task = None
                self._search_error = None
                self._discovered_model = None
                self._bluetooth_address = None
                self.context = {}

            def async_show_form(self, **kwargs):
                return {"type": "form", **kwargs}

            def async_show_progress(self, **kwargs):
                return {"type": "progress", **kwargs}

            def async_show_progress_done(self, **kwargs):
                return {"type": "progress_done", **kwargs}

            def async_abort(self, **kwargs):
                return {"type": "abort", **kwargs}

            async def async_step_bluetooth_confirm(self):
                return {"type": "confirmed", "address": self._bluetooth_address}

            async def async_step_manual(self):
                return {"type": "manual"}

        return Flow()

    async def test_no_matches_still_offers_scan_and_manual(self):
        bt = FakeBluetooth()

        async def sleep(seconds):
            self.assertEqual(seconds, 10)

        flow = self.make_flow(bt, sleep)
        form = await flow.async_step_user()
        choices = form["data_schema"]["device"]
        self.assertEqual(form["type"], "form")
        self.assertEqual(set(choices), {"__search__", "__manual__"})
        self.assertEqual(form["description_placeholders"]["count"], "0")
        self.assertEqual((await flow.async_step_user({"device": "__manual__"}))["type"], "manual")

    async def test_search_listens_for_new_advertisements_and_unsubscribes(self):
        bt = FakeBluetooth()
        bt.cached.append(SimpleNamespace(
            name="Xiaomi unknown", address="AA:BB:CC:DD:EE:01"
        ))

        async def sleep(seconds):
            self.assertEqual(seconds, 10)
            bt.emit("SO Smart Aroma Diffuser S5", "AA:BB:CC:DD:EE:02")
            bt.emit(None, "AA:BB:CC:DD:EE:03")
            bt.emit("Mi Home", "invalid-address")
            await asyncio.sleep(0)

        flow = self.make_flow(bt, sleep)
        first = await flow.async_step_user()
        self.assertEqual(set(first["data_schema"]["device"]), {"__search__", "__manual__"})
        progress = await flow.async_step_user({"device": "__search__"})
        self.assertEqual(progress["type"], "progress")
        await flow._search_task
        self.assertIsNone(bt.callback)
        self.assertTrue(bt.unsubscribed)
        self.assertIsNone(bt.matcher)
        self.assertEqual(bt.mode, bt.BluetoothScanningMode.ACTIVE)
        self.assertEqual(bt.active_requests, [10], "AUTO scanner must get a real active sweep")
        done = await flow.async_step_search()
        self.assertEqual(done["next_step_id"], "user")
        form = await flow.async_step_user()
        choices = form["data_schema"]["device"]
        self.assertEqual(form["description_placeholders"]["count"], "3")
        self.assertEqual(
            list(choices)[1], "AA:BB:CC:DD:EE:02",
            "exact SO model must be first",
        )
        self.assertIn("не подтверждено", choices["AA:BB:CC:DD:EE:01"])
        self.assertIn("Без имени", choices["AA:BB:CC:DD:EE:03"])
        result = await flow.async_step_user({"device": "AA:BB:CC:DD:EE:01"})
        self.assertEqual(result["type"], "confirmed")
        self.assertEqual(flow._bluetooth_address, "AA:BB:CC:DD:EE:01")
        self.assertIsNone(flow._discovered_model)
        self.assertTrue(flow._show_all_candidates)

    async def test_search_failure_is_actionable_not_permanent_abort(self):
        bt = FakeBluetooth()
        bt.fail = True

        async def sleep(seconds):
            raise AssertionError("scan should not reach sleep")

        flow = self.make_flow(bt, sleep)
        progress = await flow.async_step_user({"device": "__search__"})
        self.assertEqual(progress["type"], "progress")
        try:
            await flow._search_task
        except OSError:
            pass
        done = await flow.async_step_search()
        self.assertEqual(done["type"], "progress_done")
        form = await flow.async_step_user()
        self.assertEqual(form["errors"], {"base": "scan_unavailable"})
        self.assertEqual(bt.active_requests, [], "failed subscription must not schedule a scan")
        self.assertIn("__manual__", form["data_schema"]["device"])
        self.assertIn("__search__", form["data_schema"]["device"])
        self.assertEqual((await flow.async_step_user())["errors"], {})

    async def test_scan_cap_preserves_exact_so_candidates(self):
        bt = FakeBluetooth()

        async def sleep(seconds):
            return None

        flow = self.make_flow(bt, sleep)
        for n in range(65):
            flow._remember_candidate(
                SimpleNamespace(name="Other BLE", address=f"AA:BB:CC:DD:EE:{n:02X}"),
                include_unrecognized=True,
            )
        self.assertEqual(len(flow._discovered), 60)
        flow._remember_candidate(
            SimpleNamespace(name="bwj.diffuser.s5", address="BB:BB:CC:DD:EE:FF"),
            include_unrecognized=True,
        )
        self.assertEqual(len(flow._discovered), 60)
        self.assertIn("BB:BB:CC:DD:EE:FF", flow._discovered)


if __name__ == "__main__":
    unittest.main()

"""Test actual coordinator property handling without importing Home Assistant."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from custom_components.so_diffuser_ble.models import get_profile

BASE = Path(__file__).resolve().parents[1] / "custom_components" / "so_diffuser_ble"


def _isolated_update_properties():
    """Compile the actual coordinator implementation with postponed annotations."""
    tree = ast.parse((BASE / "coordinator.py").read_text(encoding="utf-8"))
    future = next(node for node in tree.body
                  if isinstance(node, ast.ImportFrom) and node.module == "__future__")
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == "S5Coordinator")
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                  and node.name == "_update_properties")
    namespace = {}
    exec(compile(ast.Module(body=[future, method], type_ignores=[]),
                 "<actual SO coordinator>", "exec"), namespace)
    return namespace["_update_properties"]


def _coordinator(model):
    fields = {
        "profile": get_profile(model), "power": None, "battery_level": None,
        "charging_status": None, "fragrance_out_time": None,
        "idle_time": None, "last_idle_time": None,
        "light": None, "color": None, "temperature": None,
    }
    receiver = SimpleNamespace(**fields)
    calls = []
    receiver._notify = lambda: calls.append(True)
    return receiver, calls


def _message(siid, piid, type_code, value):
    return SimpleNamespace(properties=[
        SimpleNamespace(siid=siid, piid=piid, value_type=type_code, value=value)
    ])


def test_s1_pro_temperature_only_when_model_declares_it():
    update = _isolated_update_properties()
    pro, notifications = _coordinator("bwj.diffuser.s1pro")
    update(pro, _message(3, 10, 2, -5))
    assert pro.temperature == -5
    assert notifications == [True]

    s5, notifications = _coordinator("bwj.diffuser.s5")
    update(s5, _message(3, 10, 2, -5))
    assert s5.temperature is None
    assert notifications == []


def test_no_rgb_for_s1_and_s19_even_if_unexpected_property_is_received():
    update = _isolated_update_properties()
    for model in ("bwj.diffuser.k09", "bwj.diffuser.s19"):
        device, notifications = _coordinator(model)
        update(device, _message(3, 8, 1, 238))
        update(device, _message(3, 9, 5, 0x00AABBCC))
        assert device.light is None
        assert device.color is None
        assert notifications == []


def test_family_power_is_readable_and_s5_lighting_unchanged():
    update = _isolated_update_properties()
    for model in ("bwj.diffuser.s5", "bwj.diffuser.s6", "bwj.diffuser.k09"):
        device, notifications = _coordinator(model)
        update(device, _message(2, 1004, 1, 1))
        assert device.power is True
        assert notifications
    s5, notifications = _coordinator("bwj.diffuser.s5")
    update(s5, _message(3, 8, 1, 238))
    assert s5.light == 238


def test_platform_setup_has_capability_gates():
    light = (BASE / "light.py").read_text(encoding="utf-8")
    sensor = (BASE / "sensor.py").read_text(encoding="utf-8")
    switch = (BASE / "switch.py").read_text(encoding="utf-8")
    assert "if entry.runtime_data.profile.light:" in light
    assert "if coordinator.profile.temperature:" in sensor
    assert "if coordinator.profile.long_spray:" in switch


def test_config_entry_runtime_guard_fails_closed_for_unknown_or_unapproved_model():
    source = (BASE / "__init__.py").read_text(encoding="utf-8")
    flow = (BASE / "config_flow.py").read_text(encoding="utf-8")
    assert "assert_model_opt_in(" in source
    assert "assert_model_opt_in(self._model, self._experimental_confirmed)" in flow
    assert "async_step_experimental_confirm" in flow
    assert "await async_validate_s5_token(" in flow
    assert flow.index("await async_validate_s5_token(") < flow.index("save_device_token, self.hass.config.path()")

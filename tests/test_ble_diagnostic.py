"""Connectivity diagnostic remains visible while experimental BLE is down."""
import ast
from pathlib import Path
from types import SimpleNamespace

BASE = Path(__file__).resolve().parents[1] / "custom_components/so_diffuser_ble"


def _actual_class():
    tree = ast.parse((BASE / "binary_sensor.py").read_text(encoding="utf-8"))
    cls = next(x for x in tree.body
               if isinstance(x, ast.ClassDef) and x.name == "SOConnectionBinarySensor")

    class BaseEntity:
        def __init__(self, coordinator, key, name, icon, category):
            self.coordinator = coordinator
            self._attr_unique_id = key
            self._attr_name = name

    ns = {
        "S5Entity": BaseEntity,
        "BinarySensorEntity": type("BinarySensorEntity", (), {}),
        "BinarySensorDeviceClass": SimpleNamespace(CONNECTIVITY="connectivity"),
        "EntityCategory": SimpleNamespace(DIAGNOSTIC="diagnostic"),
    }
    exec(compile(ast.Module(body=[cls], type_ignores=[]),
                 "<actual SO binary diagnostic>", "exec"), ns)
    return ns["SOConnectionBinarySensor"]


def test_diagnostic_reports_disconnected_then_connected_without_unavailable_state():
    cls = _actual_class()
    coordinator = SimpleNamespace(connected=False)
    entity = cls(coordinator)
    assert entity.available is True
    assert entity.is_on is False
    coordinator.connected = True
    assert entity.available is True
    assert entity.is_on is True


def test_ha_registration_includes_binary_sensor():
    text = (BASE / "const.py").read_text(encoding="utf-8")
    assert '"binary_sensor"' in text

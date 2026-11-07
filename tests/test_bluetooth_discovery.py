"""Offline checks for S5-only discovery; no HA instance or secrets required."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "custom_components" / "so_diffuser_ble"


def _isolated_matcher():
    """Run the real discovery predicate without loading Home Assistant."""
    source = (BASE / "config_flow.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    future = next(
        node for node in module.body
        if isinstance(node, ast.ImportFrom) and node.module == "__future__"
    )
    names = next(
        node for node in module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_S5_NAMES"
                for target in node.targets)
    )
    matcher = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "is_s5_advertisement"
    )
    isolated = ast.Module(body=[future, names, matcher], type_ignores=[])
    namespace: dict = {}
    exec(compile(isolated, "<isolated S5 discovery>", "exec"), namespace)
    return namespace["is_s5_advertisement"]


def test_s5_names_only():
    matches = _isolated_matcher()
    for name in ("bwj.diffuser.s5", "BWJ.DIFFUSER.S5", "SO Smart Aroma Diffuser S5"):
        assert matches(SimpleNamespace(name=name))
    for name in ("", None, "bwj.diffuser.s6", "Xiaomi Bluetooth", "Mi Smart Kettle", "bwj.diffuser.s5.fake"):
        assert not matches(SimpleNamespace(name=name))
    assert not matches(SimpleNamespace())


def test_manifest_does_not_claim_generic_xiaomi_ble():
    manifest = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
    matchers = manifest["bluetooth"]
    assert matchers
    assert all(matcher.get("connectable") is True for matcher in matchers)
    assert all(matcher.get("local_name") for matcher in matchers)
    assert not any(matcher.get("service_uuid") == "0000fe95-0000-1000-8000-00805f9b34fb"
                   and "local_name" not in matcher for matcher in matchers)


def test_translations_cover_device_picker_confirmation_and_manual_fallback():
    for lang in ("en", "ru"):
        translation = json.loads(
            (BASE / "translations" / f"{lang}.json").read_text(encoding="utf-8")
        )["config"]
        steps = translation["step"]
        assert steps["user"]["data"]["device"]
        assert steps["manual"]["data"]["address"]
        assert steps["bluetooth_confirm"]["title"]
        assert translation["error"]["token_missing"]
        assert translation["abort"]["already_configured"]

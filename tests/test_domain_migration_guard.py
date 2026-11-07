"""Guard generic-domain onboarding against an active so_s5 session."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

PATH = Path(__file__).resolve().parents[1] / "custom_components/so_diffuser_ble/config_flow.py"


def _isolated_legacy_guard():
    ast_module = ast.parse(PATH.read_text(encoding="utf-8"))
    cls = next(x for x in ast_module.body
               if isinstance(x, ast.ClassDef) and x.name == "S5ConfigFlow")
    method = next(x for x in cls.body
                  if isinstance(x, ast.FunctionDef)
                  and x.name == "_legacy_entry_conflicts")
    methods_module = ast.Module(body=[method], type_ignores=[])
    namespace = {"CONF_ADDRESS": "address"}
    exec(compile(methods_module, "<actual migration guard>", "exec"), namespace)
    return namespace["_legacy_entry_conflicts"]


def _hass_with_legacy_entries(*addresses):
    def entries(domain):
        assert domain == "so_s5"
        return [SimpleNamespace(data={"address": addr}) for addr in addresses]
    return SimpleNamespace(config_entries=SimpleNamespace(async_entries=entries))


def test_old_domain_same_address_is_rejected_without_new_session():
    guard = _isolated_legacy_guard()
    flow = SimpleNamespace(hass=_hass_with_legacy_entries("aa:bb:cc:dd:ee:ff"))
    assert guard(flow, "AA:BB:CC:DD:EE:FF") is True


def test_different_legacy_device_and_no_entries_do_not_block_new_model():
    guard = _isolated_legacy_guard()
    flow = SimpleNamespace(hass=_hass_with_legacy_entries("AA:BB:CC:DD:EE:11"))
    assert guard(flow, "AA:BB:CC:DD:EE:FF") is False
    empty = SimpleNamespace(hass=_hass_with_legacy_entries())
    assert guard(empty, "AA:BB:CC:DD:EE:FF") is False


def test_duplicate_guard_precedes_any_token_write():
    text = PATH.read_text(encoding="utf-8")
    cls = ast.parse(text)
    flow = next(x for x in cls.body
                if isinstance(x, ast.ClassDef) and x.name == "S5ConfigFlow")
    methods = {x.name: ast.unparse(x) for x in flow.body
               if isinstance(x, ast.AsyncFunctionDef)}
    assert "_legacy_entry_conflicts" in methods["_async_finish"]
    assert "_legacy_entry_conflicts" in methods["async_step_credentials"]
    provision = methods["_async_try_provision"]
    assert provision.index("_legacy_entry_conflicts") < provision.index("save_device_token")
    assert provision.index("model_mismatch") < provision.index("save_device_token")

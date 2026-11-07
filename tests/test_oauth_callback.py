"""Exercise the real OAuth callback code with no HA installation or secrets."""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
import secrets
from types import SimpleNamespace
import unittest

FLOW_SOURCE = (
    Path(__file__).resolve().parents[1] /
    "custom_components" / "so_diffuser_ble" / "config_flow.py"
).read_text(encoding="utf-8")


class FakeResponse:
    def __init__(self, *, text, status=200, **kwargs):
        self.text = text
        self.status = status
        self.headers = kwargs.get("headers", {})


def isolated_callback():
    """Compile the actual HA webhook function into a standalone test namespace."""
    source = ast.parse(FLOW_SOURCE)
    node = next(n for n in source.body if isinstance(n, ast.AsyncFunctionDef)
                and n.name == "_handle_oauth_callback")
    compiled = ast.Module(body=[node], type_ignores=[])
    ns = {
        "secrets": secrets,
        "web": SimpleNamespace(Response=FakeResponse),
        "DOMAIN": "so_diffuser_ble",
        "_OAUTH_CALLBACKS": "oauth_callbacks",
    }
    exec(compile(compiled, "<actual OAuth callback>", "exec"), ns)
    return ns["_handle_oauth_callback"]


class CallbackTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.code_future = asyncio.get_running_loop().create_future()
        self.hass = SimpleNamespace(data={
            "so_diffuser_ble": {"oauth_callbacks": {
                "id": {"state": "secure-state", "future": self.code_future}
            }}
        })
        self.callback = isolated_callback()

    async def test_valid_state_is_one_time_and_does_not_echo_code(self):
        request = SimpleNamespace(query={"state": "secure-state", "code": "SECRET"})
        result = await self.callback(self.hass, "id", request)
        self.assertEqual(result.status, 200)
        self.assertEqual(self.code_future.result(), "SECRET")
        self.assertNotIn("SECRET", result.text)
        self.assertEqual(result.headers["Cache-Control"], "no-store")
        replay = await self.callback(self.hass, "id", request)
        self.assertEqual(replay.status, 400)

    async def test_wrong_state_or_missing_code_rejected(self):
        for query in ({"state": "wrong", "code": "SECRET"},
                      {"state": "secure-state"}, {}):
            response = await self.callback(self.hass, "id",
                                           SimpleNamespace(query=query))
            self.assertEqual(response.status, 400)
            self.assertFalse(self.code_future.done())

    async def test_unknown_webhook_rejected(self):
        response = await self.callback(
            self.hass, "unknown",
            SimpleNamespace(query={"state": "secure-state", "code": "SECRET"}),
        )
        self.assertEqual(response.status, 400)


def test_flow_has_migration_and_verification_before_store():
    source = ast.parse(FLOW_SOURCE)
    cls = next(n for n in source.body if isinstance(n, ast.ClassDef)
               and n.name == "S5ConfigFlow")
    methods = {n.name: n for n in cls.body if isinstance(n, ast.AsyncFunctionDef)}
    assert "async_step_reconfigure" in methods
    assert "async_step_credentials" in methods
    assert "async_step_oauth" in methods
    assert "async_step_cloud_device" in methods
    text = ast.unparse(methods["_async_try_provision"])
    assert text.index("await async_validate_s5_token(") < text.index("save_device_token")
    assert "_async_finish" in text
    assert "async_step_experimental_confirm" in methods
    assert "acknowledge" in ast.unparse(methods["async_step_experimental_confirm"])
    assert "async_update_reload_and_abort" in ast.unparse(methods["_async_finish"])

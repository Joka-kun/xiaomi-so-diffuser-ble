"""Exercise actual Bluetooth proof stages without a Home Assistant installation."""
from __future__ import annotations

import ast
import asyncio
from contextlib import suppress
from functools import wraps
from pathlib import Path
from types import SimpleNamespace

import pytest


def run_async(fn):
    """Run coroutine tests without a dependency on pytest-asyncio."""
    @wraps(fn)
    def wrapped():
        return asyncio.run(fn())
    return wrapped


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "custom_components" / "so_diffuser_ble" / "provisioning.py"
).read_text(encoding="utf-8")


class ProvisioningError(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class FakeClient:
    def __init__(self):
        self.disconnected = False

    async def disconnect(self):
        self.disconnected = True


def _proof(available=True, fail_connect=False, fail_auth=False, authenticated=True):
    node = next(
        x for x in ast.parse(SOURCE).body
        if isinstance(x, ast.AsyncFunctionDef) and x.name == "async_validate_s5_token"
    )
    client = FakeClient()
    calls = []

    async def connect(*args, **kwargs):
        calls.append("connect")
        if fail_connect:
            raise OSError("sensitive-ble-error")
        return client

    class Verifier:
        def __init__(self, *args, **kwargs):
            self.authenticated = authenticated

        async def authenticate(self):
            calls.append("auth")
            if fail_auth:
                raise RuntimeError("sensitive-gatt-frame")

    namespace = {
        "asyncio": asyncio,
        "suppress": suppress,
        "bluetooth": SimpleNamespace(
            async_ble_device_from_address=lambda *a, **kw: object() if available else None
        ),
        "establish_connection": connect,
        "BleakClient": type("BleakClient", (), {}),
        "S5ReadOnlyClient": Verifier,
        "XiaomiProvisioningError": ProvisioningError,
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), "<actual provisioning>", "exec"), namespace)
    return namespace["async_validate_s5_token"], client, calls


@run_async
async def test_offline_device_is_not_called_wrong_token():
    proof, client, calls = _proof(available=False)
    with pytest.raises(ProvisioningError) as exc:
        await proof(None, "AA:BB:CC:DD:EE:FF", b"t" * 12)
    assert exc.value.reason == "ble_not_available"
    assert calls == []


@run_async
async def test_busy_bluetooth_fails_at_connection_stage_without_claiming_bad_token():
    proof, client, calls = _proof(fail_connect=True)
    with pytest.raises(ProvisioningError) as exc:
        await proof(None, "AA:BB:CC:DD:EE:FF", b"t" * 12)
    assert exc.value.reason == "ble_connection_failed"
    assert calls == ["connect"]
    assert "sensitive" not in str(exc.value)


@run_async
async def test_failed_gatt_login_has_distinct_error_and_disconnects():
    proof, client, calls = _proof(fail_auth=True)
    with pytest.raises(ProvisioningError) as exc:
        await proof(None, "AA:BB:CC:DD:EE:FF", b"t" * 12)
    assert exc.value.reason == "ble_auth_failed"
    assert calls == ["connect", "auth"]
    assert client.disconnected is True


@run_async
async def test_false_authenticated_flag_rejected_after_connect():
    proof, client, calls = _proof(authenticated=False)
    with pytest.raises(ProvisioningError) as exc:
        await proof(None, "AA:BB:CC:DD:EE:FF", b"t" * 12)
    assert exc.value.reason == "ble_auth_failed"
    assert client.disconnected is True


@run_async
async def test_valid_local_login_disconnects_after_proof_without_writes():
    proof, client, calls = _proof()
    assert await proof(None, "AA:BB:CC:DD:EE:FF", b"t" * 12) is None
    assert calls == ["connect", "auth"]
    assert client.disconnected is True

"""HA Bluetooth connection lifecycle for the S5 fixed UI properties."""
from __future__ import annotations

import asyncio
from contextlib import suppress
import logging

from bleak import BleakClient
from bleak_retry_connector import establish_connection
from homeassistant.components import bluetooth
from homeassistant.exceptions import HomeAssistantError

from .client import MiotMessage, S5ClientError, S5ControlClient
from .token_store import load_device_token
from .models import DEFAULT_MODEL, get_profile
from .protocol import light_is_gradient, light_is_on

_LOGGER = logging.getLogger(__name__)


class S5Coordinator:
    def __init__(self, hass, address: str, model: str = DEFAULT_MODEL) -> None:
        self.profile = get_profile(model)
        self.hass = hass
        self.address = address
        self.connected = False
        self.power: bool | None = None
        self.battery_level: int | None = None
        self.charging_status: int | None = None
        self.temperature: int | None = None
        self.fragrance_out_time: int | None = None
        self.idle_time: int | None = None
        self.last_idle_time: int | None = None
        self.light: int | None = None
        self.color: int | None = None
        self._listeners = set()
        self._session: S5ControlClient | None = None
        self._task: asyncio.Task | None = None
        self._retry_delay = 2.0

    def add_listener(self, callback):
        self._listeners.add(callback)
        return lambda: self._listeners.discard(callback)

    def _notify(self) -> None:
        for callback in tuple(self._listeners):
            callback()

    def async_start(self) -> None:
        if self._task is None:
            self._task = self.hass.async_create_task(self._run())

    async def async_shutdown(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def async_set_power(self, enabled: bool) -> None:
        await self._async_command("set_power", enabled)

    async def async_set_fragrance_out_time(self, value: int) -> None:
        await self._async_command("set_fragrance_out_time", value)

    async def async_set_idle_time(self, value: int) -> None:
        await self._async_command("set_idle_time", value)
        if value > 0:
            self.last_idle_time = value

    async def async_set_light_value(self, value: int) -> None:
        if not self.profile.light:
            raise HomeAssistantError("SO model does not expose light control")
        await self._async_command("set_light", value)

    async def async_set_color(self, value: int) -> None:
        if not self.profile.light:
            raise HomeAssistantError("SO model does not expose RGB control")
        if not light_is_on(self.light) or light_is_gradient(self.light):
            raise HomeAssistantError("Turn on steady light before setting its color")
        await self._async_command("set_color", value)

    async def _async_command(self, method: str, value) -> None:
        session = self._session
        if not self.connected or session is None:
            raise HomeAssistantError("SO diffuser is not connected over local Bluetooth")
        methods = {
            "set_power": session.set_power,
            "set_fragrance_out_time": session.set_fragrance_out_time,
            "set_idle_time": session.set_idle_time,
            "set_light": session.set_light,
            "set_color": session.set_color,
        }
        command = methods.get(method)
        if command is None:
            raise ValueError("SO command is outside the fixed property allowlist")
        try:
            await command(value)
        except S5ClientError as err:
            raise HomeAssistantError(str(err)) from err

    async def _run(self) -> None:
        while True:
            try:
                await self._run_session()
            except asyncio.CancelledError:
                raise
            except Exception as err:
                _LOGGER.debug("SO local BLE session unavailable (%s)", type(err).__name__)
            await asyncio.sleep(self._retry_delay)
            self._retry_delay = min(self._retry_delay * 2, 30.0)

    async def _run_session(self) -> None:
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address.upper(), connectable=True
        )
        if ble_device is None:
            raise S5ClientError("Bluetooth address is not currently available to Home Assistant")
        token = await self.hass.async_add_executor_job(
            load_device_token, self.hass.config.path(), self.address
        )

        disconnected = asyncio.Event()
        ble_client = await establish_connection(
            BleakClient,
            ble_device,
            "Xiaomi SO Diffuser BLE",
            disconnected_callback=lambda _client: disconnected.set(),
            pair=False,
        )
        try:
            session = S5ControlClient(ble_client, token)
            del token
            await session.authenticate()
            self._retry_delay = 2.0
            self._session = session
            self.connected = True
            self._clear_properties()
            self._notify()

            reader = session.iter_messages()
            listener_task = self.hass.async_create_task(self._consume(reader))
            disconnect_task = self.hass.async_create_task(disconnected.wait())
            tasks = (listener_task, disconnect_task)
            try:
                done, _pending = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED
                )
                if listener_task in done:
                    listener_task.result()
                raise S5ClientError("Bluetooth connection ended")
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            self._session = None
            self.connected = False
            self._clear_properties()
            self._notify()
            with suppress(Exception):
                await ble_client.disconnect()

    async def _consume(self, reader) -> None:
        async for message in reader:
            self._update_properties(message)

    def _clear_properties(self) -> None:
        self.power = self.battery_level = self.charging_status = self.temperature = None
        self.fragrance_out_time = self.idle_time = None
        self.light = self.color = None

    def _update_properties(self, message: MiotMessage) -> None:
        property_types = {
            (2, 1004): (1, "power"),
            (3, 1): (1, "battery_level"),
            (3, 2): (1, "charging_status"),
            (3, 3): (1, "fragrance_out_time"),
            (3, 4): (1, "idle_time"),
            (3, 8): (1, "light"),
            (3, 9): (5, "color"),
            (3, 10): (2, "temperature"),
        }
        changed = False
        for prop in message.properties:
            spec = property_types.get((prop.siid, prop.piid))
            if spec is None or prop.value_type != spec[0] or type(prop.value) is not int:
                continue
            name = spec[1]
            if name in ("light", "color") and not self.profile.light:
                continue
            if name == "temperature" and not self.profile.temperature:
                continue
            if name == "power":
                if prop.value not in (0, 1):
                    continue
                value = bool(prop.value)
            elif name == "battery_level":
                if not 0 <= prop.value <= 100:
                    continue
                value = prop.value
            elif name == "charging_status":
                if prop.value not in (0, 1, 2):
                    continue
                value = prop.value
            elif name == "fragrance_out_time":
                if not 3 <= prop.value <= 30:
                    continue
                value = prop.value
            elif name == "idle_time":
                if prop.value != 0 and not 3 <= prop.value <= 30:
                    continue
                value = prop.value
                if value > 0:
                    self.last_idle_time = value
            elif name == "light":
                if not (prop.value <= 100 or prop.value == 110 or 128 <= prop.value <= 228 or prop.value == 238):
                    continue
                value = prop.value
            elif name == "color":
                if not 0 <= prop.value <= 0xFFFFFF:
                    continue
                value = prop.value
            elif name == "temperature":
                if not -9 <= prop.value <= 80:
                    continue
                value = prop.value
            else:
                continue
            if getattr(self, name) != value:
                setattr(self, name, value)
                changed = True
        if changed:
            self._notify()

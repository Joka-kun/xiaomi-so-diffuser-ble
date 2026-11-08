import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _ha_stubs():
    homeassistant = types.ModuleType("homeassistant")
    homeassistant.__path__ = []
    components = types.ModuleType("homeassistant.components")
    components.__path__ = []
    light_module = types.ModuleType("homeassistant.components.light")
    light_module.ColorMode = type("ColorMode", (), {"RGB": "rgb", "ONOFF": "onoff"})
    light_module.LightEntityFeature = type("LightEntityFeature", (), {"EFFECT": 4})
    light_module.LightEntity = type("LightEntity", (), {})
    number_module = types.ModuleType("homeassistant.components.number")
    number_module.NumberEntity = type("NumberEntity", (), {})
    number_module.NumberMode = type("NumberMode", (), {"SLIDER": "slider"})
    switch_module = types.ModuleType("homeassistant.components.switch")
    switch_module.SwitchEntity = type("SwitchEntity", (), {})
    ha_const = types.ModuleType("homeassistant.const")
    ha_const.UnitOfTime = type("UnitOfTime", (), {"SECONDS": "s", "MINUTES": "min"})
    exceptions = types.ModuleType("homeassistant.exceptions")
    exceptions.HomeAssistantError = type("HomeAssistantError", (Exception,), {})
    helpers = types.ModuleType("homeassistant.helpers")
    helpers.__path__ = []
    entity_module = types.ModuleType("homeassistant.helpers.entity")
    entity_module.Entity = type("Entity", (), {})
    entity_module.DeviceInfo = lambda **kwargs: kwargs
    entity_module.EntityCategory = type("EntityCategory", (), {"CONFIG": "config", "DIAGNOSTIC": "diagnostic"})
    return {
        "homeassistant": homeassistant,
        "homeassistant.components": components,
        "homeassistant.components.light": light_module,
        "homeassistant.components.number": number_module,
        "homeassistant.components.switch": switch_module,
        "homeassistant.const": ha_const,
        "homeassistant.exceptions": exceptions,
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.entity": entity_module,
    }


with patch.dict(sys.modules, _ha_stubs()):
    light_module = importlib.import_module("custom_components.so_diffuser_ble.light")
    number_module = importlib.import_module("custom_components.so_diffuser_ble.number")
    switch_module = importlib.import_module("custom_components.so_diffuser_ble.switch")


class FakeCoordinator:
    def __init__(self, *, light=None, color=None, idle_time=None, last_idle_time=None):
        self.address = "AA:BB:CC:DD:EE:FF"
        self.light = light
        self.color = color
        self.idle_time = idle_time
        self.last_idle_time = last_idle_time
        self.calls = []
        self.connected = True

    async def async_set_light_value(self, value):
        self.calls.append(("light", value))
        self.light = value

    async def async_set_color(self, value):
        self.calls.append(("color", value))
        self.color = value

    async def async_set_idle_time(self, value):
        self.calls.append(("idle_time", value))
        self.idle_time = value
        if value > 0:
            self.last_idle_time = value

    async def async_set_fragrance_out_time(self, value):
        self.calls.append(("fragrance_out_time", value))


class S5LightEntityTests(unittest.IsolatedAsyncioTestCase):
    async def test_off_clears_enable_bit_and_next_on_restores_gradient_mode(self):
        coordinator = FakeCoordinator(light=238)
        light = light_module.S5Light(coordinator)
        self.assertEqual(light.effect, light_module.EFFECT_GRADIENT)
        self.assertEqual(light._attr_supported_features, 4)
        self.assertEqual(light.color_mode, "onoff")
        self.assertIsNone(light.brightness)
        self.assertIsNone(light.rgb_color)

        await light.async_turn_off()
        self.assertEqual(coordinator.calls[-1], ("light", 110))
        self.assertFalse(light.is_on)
        self.assertIsNone(light.effect)

        await light.async_turn_on()
        self.assertEqual(coordinator.calls[-1], ("light", 238))
        self.assertTrue(light.is_on)
        self.assertEqual(light.effect, light_module.EFFECT_GRADIENT)

    async def test_steady_brightness_maps_to_1_to_100_and_zero_means_off(self):
        coordinator = FakeCoordinator(light=50)
        light = light_module.S5Light(coordinator)
        await light.async_turn_on()
        self.assertEqual(coordinator.calls[-1], ("light", 178))
        self.assertEqual(light.brightness, 128)
        self.assertEqual(light.color_mode, "rgb")

        await light.async_turn_on(brightness=255)
        self.assertEqual(coordinator.calls[-1], ("light", 228))
        await light.async_turn_on(brightness=1)
        self.assertEqual(coordinator.calls[-1], ("light", 129))
        await light.async_turn_on(brightness=0)
        self.assertEqual(coordinator.calls[-1], ("light", 1))
        self.assertFalse(light.is_on)

    async def test_rgb_is_applied_after_steady_mode_is_enabled(self):
        coordinator = FakeCoordinator(light=50)
        light = light_module.S5Light(coordinator)
        await light.async_turn_on(rgb_color=(1, 2, 3))
        self.assertEqual(coordinator.calls, [("light", 178), ("color", 0x010203)])

    async def test_rgb_is_rejected_in_gradient_mode_without_writes(self):
        coordinator = FakeCoordinator(light=238)
        light = light_module.S5Light(coordinator)
        with self.assertRaises(ValueError):
            await light.async_turn_on(rgb_color=(1, 2, 3))
        self.assertEqual(coordinator.calls, [])

    async def test_rgb_and_brightness_can_switch_gradient_to_steady(self):
        coordinator = FakeCoordinator(light=238)
        light = light_module.S5Light(coordinator)
        await light.async_turn_on(brightness=255, rgb_color=(4, 5, 6))
        self.assertEqual(coordinator.calls, [("light", 228), ("color", 0x040506)])


    def _attach_fake_hass(self, light):
        light.hass = types.SimpleNamespace(async_create_task=asyncio.create_task)
        light.async_write_ha_state = lambda: None

    async def test_software_palettes_use_only_existing_color_and_steady_light_commands(self):
        coordinator = FakeCoordinator(light=238)
        light = light_module.S5Light(coordinator)
        self._attach_fake_hass(light)
        with patch.object(light_module, "PALETTE_INTERVAL_SECONDS", 0.01):
            await light.async_turn_on(effect=light_module.EFFECT_COLORS)
            self.assertEqual(coordinator.calls[:2], [
                ("light", 228),
                ("color", light_module.SOFTWARE_PALETTES[light_module.EFFECT_COLORS][0]),
            ])
            self.assertEqual(light.effect, light_module.EFFECT_COLORS)
            await asyncio.sleep(0.024)
            self.assertGreaterEqual(len(coordinator.calls), 4)
            self.assertTrue(all(kind in ("color", "light") for kind, _ in coordinator.calls))
            await light.async_turn_on(effect=light_module.EFFECT_GRADIENT)
            self.assertEqual(coordinator.calls[-1], ("light", 238))
            self.assertEqual(light.effect, light_module.EFFECT_GRADIENT)
            count = len(coordinator.calls)
            await asyncio.sleep(0.03)
            self.assertEqual(len(coordinator.calls), count)
            self.assertIsNone(light._palette_task)

    async def test_software_cycle_stops_on_turn_off_and_preserves_existing_key(self):
        coordinator = FakeCoordinator(light=228)
        light = light_module.S5Light(coordinator)
        self._attach_fake_hass(light)
        self.assertEqual(light._attr_unique_id, "aabbccddeeff_light")
        with patch.object(light_module, "PALETTE_INTERVAL_SECONDS", 0.01):
            await light.async_turn_on(effect=light_module.EFFECT_SUNSET)
            await light.async_turn_off()
            self.assertFalse(light.is_on)
            self.assertIsNone(light._palette_task)
            count = len(coordinator.calls)
            await asyncio.sleep(0.025)
            self.assertEqual(len(coordinator.calls), count)

    async def test_palette_does_not_loop_after_bluetooth_disconnect(self):
        coordinator = FakeCoordinator(light=228)
        light = light_module.S5Light(coordinator)
        self._attach_fake_hass(light)
        with patch.object(light_module, "PALETTE_INTERVAL_SECONDS", 0.01):
            await light.async_turn_on(effect=light_module.EFFECT_COLORS)
            coordinator.connected = False
            await asyncio.sleep(0.035)
            self.assertIsNone(light._palette_task)
            self.assertEqual([kind for kind, _ in coordinator.calls], ["color"])

    async def test_palette_rejects_simultaneous_rgb_and_does_not_start_task(self):
        coordinator = FakeCoordinator(light=228)
        light = light_module.S5Light(coordinator)
        self._attach_fake_hass(light)
        with self.assertRaises(ValueError):
            await light.async_turn_on(
                effect=light_module.EFFECT_SUNSET, rgb_color=(2, 3, 4)
            )
        self.assertIsNone(light._palette_task)
        self.assertEqual(coordinator.calls, [])

    async def test_plain_turn_on_preserves_running_palette_and_steady_rgb_selection_stops_it(self):
        coordinator = FakeCoordinator(light=228)
        light = light_module.S5Light(coordinator)
        self._attach_fake_hass(light)
        with patch.object(light_module, "PALETTE_INTERVAL_SECONDS", 0.01):
            await light.async_turn_on(effect=light_module.EFFECT_COLORS)
            task = light._palette_task
            await light.async_turn_on()
            self.assertIs(light._palette_task, task)
            await light.async_turn_on(effect=light_module.EFFECT_STEADY)
            self.assertIsNone(light._palette_task)
            self.assertEqual(light.effect, light_module.EFFECT_STEADY)


class S5PauseEntityTests(unittest.IsolatedAsyncioTestCase):
    def test_power_and_continuous_spray_entity_labels(self):
        coordinator = FakeCoordinator(idle_time=0)
        power = switch_module.S5PowerSwitch(coordinator)
        continuous = switch_module.S5LongSpraySwitch(coordinator)
        self.assertEqual(power._attr_name, "Вкл/Выкл")
        self.assertLess(power._attr_name, "Подсветка")
        self.assertEqual(power._attr_unique_id, "aabbccddeeff_power")
        self.assertEqual(continuous._attr_name, "Непрерывное распыление")
        self.assertEqual(continuous._attr_unique_id, "aabbccddeeff_long_spray")

    def test_experimental_zero_pause_has_clear_warning_and_stable_unique_id(self):
        coordinator = FakeCoordinator(idle_time=0)
        coordinator.profile = types.SimpleNamespace(experimental=True, name="SO S6")
        entity = switch_module.S5LongSpraySwitch(coordinator)
        self.assertEqual(entity._attr_name, "Нулевая пауза (эксперимент)")
        self.assertEqual(entity._attr_unique_id, "aabbccddeeff_long_spray")

    async def test_long_spray_switch_saves_and_restores_last_pause(self):
        coordinator = FakeCoordinator(idle_time=5, last_idle_time=5)
        switch = switch_module.S5LongSpraySwitch(coordinator)
        self.assertFalse(switch.is_on)
        await switch.async_turn_on()
        self.assertTrue(switch.is_on)
        self.assertEqual(coordinator.calls[-1], ("idle_time", 0))
        await switch.async_turn_off()
        self.assertFalse(switch.is_on)
        self.assertEqual(coordinator.calls[-1], ("idle_time", 5))

    async def test_long_spray_switch_uses_minimum_pause_if_no_previous_value_exists(self):
        coordinator = FakeCoordinator(idle_time=0)
        switch = switch_module.S5LongSpraySwitch(coordinator)
        await switch.async_turn_off()
        self.assertEqual(coordinator.calls[-1], ("idle_time", 3))

    async def test_idle_time_is_a_minutes_slider_and_long_spray_is_not_faked_as_zero(self):
        coordinator = FakeCoordinator(idle_time=5, last_idle_time=5)
        number = number_module.S5SettingNumber(
            coordinator, "idle_time", "Пауза", "mdi:timer", "idle_time",
            "async_set_idle_time", 3, 30, "min", zero_as_unknown=True,
        )
        self.assertEqual(number._attr_mode, "slider")
        self.assertEqual(number.native_value, 5)
        coordinator.idle_time = 0
        self.assertIsNone(number.native_value)
        await number.async_set_native_value(12)
        self.assertEqual(coordinator.calls[-1], ("idle_time", 12))

    async def test_idle_time_rejects_values_outside_vendor_range(self):
        coordinator = FakeCoordinator(idle_time=5)
        number = number_module.S5SettingNumber(
            coordinator, "idle_time", "Пауза", "mdi:timer", "idle_time",
            "async_set_idle_time", 3, 30, "min", zero_as_unknown=True,
        )
        for value in (2, 31, 3.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                await number.async_set_native_value(value)


if __name__ == "__main__":
    unittest.main()

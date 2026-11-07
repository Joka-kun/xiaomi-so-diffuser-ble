import asyncio
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from custom_components.so_diffuser_ble import async_setup_entry, async_unload_entry


class SetupCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_setup_cleans_only_retired_entities_and_shuts_down(self):
        homeassistant = types.ModuleType("homeassistant")
        homeassistant.__path__ = []
        ha_const = types.ModuleType("homeassistant.const")

        class Platform:
            SWITCH = "switch"
            NUMBER = "number"
            LIGHT = "light"
            SENSOR = "sensor"
            BINARY_SENSOR = "binary_sensor"
            SELECT = "select"

        ha_const.Platform = Platform
        helpers = types.ModuleType("homeassistant.helpers")
        helpers.__path__ = []
        entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")

        class Entry:
            def __init__(self, domain, unique_id, entity_id, config_entry_id="entry-1"):
                self.domain = domain
                self.unique_id = unique_id
                self.entity_id = entity_id
                self.config_entry_id = config_entry_id

        class Registry:
            def __init__(self):
                self.entries = [
                    Entry("switch", "aabbccddeeff_timer_enabled", "switch.old_timer"),
                    *[
                        Entry(
                            "switch",
                            f"aabbccddeeff_schedule_{start:02d}_{start + 2:02d}",
                            f"switch.old_schedule_{start:02d}",
                        )
                        for start in range(0, 24, 2)
                    ],
                    *[
                        Entry("switch", f"aabbccddeeff_repeat_{index}", f"switch.old_weekday_{index}")
                        for index in range(7)
                    ],
                    Entry("select", "aabbccddeeff_idle_time", "select.old_idle"),
                    Entry("switch", "aabbccddeeff_power", "switch.so_s5_diffuser_power"),
                    Entry("switch", "other_device_timer_enabled", "switch.other_timer"),
                ]
                self.removed = []

            def async_remove(self, entity_id):
                self.removed.append(entity_id)
                self.entries = [e for e in self.entries if e.entity_id != entity_id]

        registry = Registry()
        entity_registry.async_get = lambda hass: registry
        entity_registry.async_entries_for_config_entry = lambda reg, entry_id: [
            e for e in reg.entries if e.config_entry_id == entry_id
        ]
        helpers.entity_registry = entity_registry

        coordinator_module = types.ModuleType("custom_components.so_diffuser_ble.coordinator")

        class FakeCoordinator:
            instance = None

            def __init__(self, hass, address, model="bwj.diffuser.s5"):
                self.shutdown_called = False
                FakeCoordinator.instance = self

            def async_start(self):
                pass

            async def async_shutdown(self):
                self.shutdown_called = True

        coordinator_module.S5Coordinator = FakeCoordinator

        class FakeConfigEntries:
            def __init__(self):
                self.forward_started = asyncio.Event()
                self.forwarded_platforms = None

            async def async_forward_entry_setups(self, entry, platforms):
                self.forwarded_platforms = platforms
                self.forward_started.set()
                await asyncio.Event().wait()

        class FakeHass:
            def __init__(self):
                self.config_entries = FakeConfigEntries()

            def async_create_task(self, coroutine):
                return asyncio.create_task(coroutine)

        class FakeEntry:
            entry_id = "entry-1"
            data = {"address": "AA:BB:CC:DD:EE:FF"}
            runtime_data = None

        hass = FakeHass()
        entry = FakeEntry()
        modules = {
            "homeassistant": homeassistant,
            "homeassistant.const": ha_const,
            "homeassistant.helpers": helpers,
            "homeassistant.helpers.entity_registry": entity_registry,
            "custom_components.so_diffuser_ble.coordinator": coordinator_module,
        }
        with patch.dict(sys.modules, modules):
            setup_task = asyncio.create_task(async_setup_entry(hass, entry))
            await asyncio.wait_for(hass.config_entries.forward_started.wait(), timeout=1)
            setup_task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await setup_task

        self.assertTrue(FakeCoordinator.instance.shutdown_called)
        self.assertEqual(hass.config_entries.forwarded_platforms, ["switch", "number", "light", "sensor", "binary_sensor"])
        expected_removed = {"switch.old_timer", "select.old_idle"}
        expected_removed.update(f"switch.old_schedule_{start:02d}" for start in range(0, 24, 2))
        expected_removed.update(f"switch.old_weekday_{index}" for index in range(7))
        self.assertEqual(set(registry.removed), expected_removed)
        remaining = {e.entity_id for e in registry.entries}
        self.assertIn("switch.so_s5_diffuser_power", remaining)
        self.assertIn("switch.other_timer", remaining)


class LegacySelectUnloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_unload_includes_legacy_select_platform(self):
        homeassistant = types.ModuleType("homeassistant")
        homeassistant.__path__ = []
        ha_const = types.ModuleType("homeassistant.const")

        class Platform:
            SWITCH = "switch"
            NUMBER = "number"
            LIGHT = "light"
            SENSOR = "sensor"
            BINARY_SENSOR = "binary_sensor"
            SELECT = "select"

        ha_const.Platform = Platform

        class Runtime:
            shutdown_called = False

            async def async_shutdown(self):
                self.shutdown_called = True

        class ConfigEntries:
            platforms = None

            async def async_unload_platforms(self, entry, platforms):
                self.platforms = platforms
                return True

        class Hass:
            config_entries = ConfigEntries()

        class Entry:
            runtime_data = Runtime()

        hass = Hass()
        entry = Entry()
        with patch.dict(sys.modules, {
            "homeassistant": homeassistant,
            "homeassistant.const": ha_const,
        }):
            result = await async_unload_entry(hass, entry)

        self.assertTrue(result)
        self.assertEqual(hass.config_entries.platforms, ["switch", "number", "light", "sensor", "binary_sensor", "select"])
        self.assertTrue(entry.runtime_data.shutdown_called)


if __name__ == "__main__":
    unittest.main()

"""Integration-level proof that two SO diffusers have independent HA runtimes."""
from __future__ import annotations

import asyncio
import sys
import types
import unittest
from unittest.mock import patch

from custom_components.so_diffuser_ble import async_setup_entry, async_unload_entry


class MultipleDiffuserEntryTests(unittest.IsolatedAsyncioTestCase):
    async def test_two_addresses_have_separate_coordinators_and_unload(self):
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
        entity_registry.async_get = lambda hass: object()
        entity_registry.async_entries_for_config_entry = lambda registry, entry_id: []
        helpers.entity_registry = entity_registry

        coordinator_module = types.ModuleType(
            "custom_components.so_diffuser_ble.coordinator"
        )

        class FakeCoordinator:
            def __init__(self, hass, address, model):
                self.address = address
                self.model = model
                self.starts = 0
                self.shutdowns = 0

            def async_start(self):
                self.starts += 1

            async def async_shutdown(self):
                self.shutdowns += 1

        coordinator_module.S5Coordinator = FakeCoordinator

        class FakeConfigEntries:
            def __init__(self):
                self.forwarded = []
                self.unloaded = []

            async def async_forward_entry_setups(self, entry, platforms):
                self.forwarded.append((entry.entry_id, tuple(platforms)))

            async def async_unload_platforms(self, entry, platforms):
                self.unloaded.append((entry.entry_id, tuple(platforms)))
                return True

        class FakeHass:
            def __init__(self):
                self.config_entries = FakeConfigEntries()

        class Entry:
            def __init__(self, entry_id, address):
                self.entry_id = entry_id
                self.data = {"address": address, "miot_model": "bwj.diffuser.s5"}
                self.runtime_data = None

        first = Entry("diffuser-1", "AA:BB:CC:DD:EE:01")
        second = Entry("diffuser-2", "AA:BB:CC:DD:EE:02")
        hass = FakeHass()
        modules = {
            "homeassistant": homeassistant,
            "homeassistant.const": ha_const,
            "homeassistant.helpers": helpers,
            "homeassistant.helpers.entity_registry": entity_registry,
            "custom_components.so_diffuser_ble.coordinator": coordinator_module,
        }
        with patch.dict(sys.modules, modules):
            results = await asyncio.gather(
                async_setup_entry(hass, first),
                async_setup_entry(hass, second),
            )
            self.assertEqual(results, [True, True])
            self.assertIsNot(first.runtime_data, second.runtime_data)
            self.assertEqual(first.runtime_data.address, first.data["address"])
            self.assertEqual(second.runtime_data.address, second.data["address"])
            self.assertEqual(first.runtime_data.starts, 1)
            self.assertEqual(second.runtime_data.starts, 1)
            self.assertEqual(len(hass.config_entries.forwarded), 2)
            self.assertTrue(await async_unload_entry(hass, first))
            self.assertEqual(first.runtime_data.shutdowns, 1)
            self.assertEqual(second.runtime_data.shutdowns, 0)
            self.assertTrue(await async_unload_entry(hass, second))
            self.assertEqual(second.runtime_data.shutdowns, 1)


if __name__ == "__main__":
    unittest.main()

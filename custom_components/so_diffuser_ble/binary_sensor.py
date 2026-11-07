"""Connection-state diagnostic for the entire SO family.

Unlike command entities this entity remains available during BLE disconnects,
so failed experimental connections are visible in the HA UI.
"""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import S5Entity


class SOConnectionBinarySensor(S5Entity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator) -> None:
        super().__init__(
            coordinator,
            "ble_connected",
            "BLE-соединение",
            "mdi:bluetooth-connect",
            EntityCategory.DIAGNOSTIC,
        )

    @property
    def available(self) -> bool:
        # Show offline/disconnected rather than becoming unavailable.
        return True

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.connected)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([SOConnectionBinarySensor(entry.runtime_data)])

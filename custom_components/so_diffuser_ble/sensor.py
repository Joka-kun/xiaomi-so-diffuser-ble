"""Read-only battery and charging indicators reported by S5."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity import EntityCategory

from .entity import S5Entity


CHARGING_LABELS = {0: "Не заряжается", 1: "Заряжается", 2: "Заряжен"}


class S5BatterySensor(S5Entity, SensorEntity):
    _attr_name = "Заряд батареи"
    _attr_icon = "mdi:battery"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "battery", self._attr_name, self._attr_icon, EntityCategory.DIAGNOSTIC)

    @property
    def native_value(self):
        return self.coordinator.battery_level


class S5ChargingSensor(S5Entity, SensorEntity):
    _attr_name = "Состояние зарядки"
    _attr_icon = "mdi:battery-charging"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charging_status", self._attr_name, self._attr_icon, EntityCategory.DIAGNOSTIC)

    @property
    def native_value(self):
        value = self.coordinator.charging_status
        return CHARGING_LABELS.get(value) if value is not None else None

    @property
    def extra_state_attributes(self):
        return {"status_code": self.coordinator.charging_status}


class SOTemperatureSensor(S5Entity, SensorEntity):
    """S1 Pro-only property 3.10 (int8); read-only, when notified."""

    _attr_name = "Температура"
    _attr_icon = "mdi:thermometer"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "temperature", self._attr_name, self._attr_icon, EntityCategory.DIAGNOSTIC)

    @property
    def native_value(self):
        return self.coordinator.temperature


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = entry.runtime_data
    entities = [S5BatterySensor(coordinator), S5ChargingSensor(coordinator)]
    if coordinator.profile.temperature:
        entities.append(SOTemperatureSensor(coordinator))
    async_add_entities(entities)

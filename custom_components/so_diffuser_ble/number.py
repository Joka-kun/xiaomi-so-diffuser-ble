"""Slider controls for the S5 spray duration and between-spray pause."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from .entity import S5Entity


class S5SettingNumber(S5Entity, NumberEntity):
    def __init__(
        self, coordinator, key, name, icon, attr, setter, minimum, maximum, unit, *, zero_as_unknown=False
    ) -> None:
        super().__init__(coordinator, key, name, icon, EntityCategory.CONFIG)
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = unit
        self._attr_mode = NumberMode.SLIDER
        self._attr_entity_registry_enabled_default = True
        self.attr = attr
        self.setter = setter
        self.zero_as_unknown = zero_as_unknown

    @property
    def native_value(self):
        value = getattr(self.coordinator, self.attr)
        if self.zero_as_unknown and value == 0:
            return None
        return value

    async def async_set_native_value(self, value: float) -> None:
        if type(value) not in (int, float) or not float(value).is_integer():
            raise ValueError("S5 setting must be a whole number")
        value = int(value)
        if not self._attr_native_min_value <= value <= self._attr_native_max_value:
            raise ValueError("S5 setting is outside the supported range")
        await getattr(self.coordinator, self.setter)(value)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = entry.runtime_data
    async_add_entities([
        S5SettingNumber(
            coordinator,
            "fragrance_out_time",
            "Время распыления",
            "mdi:weather-windy",
            "fragrance_out_time",
            "async_set_fragrance_out_time",
            3,
            30,
            UnitOfTime.SECONDS,
        ),
        S5SettingNumber(
            coordinator,
            "idle_time",
            "Пауза между распылениями",
            "mdi:timer-sand",
            "idle_time",
            "async_set_idle_time",
            3,
            30,
            UnitOfTime.MINUTES,
            zero_as_unknown=True,
        ),
    ])

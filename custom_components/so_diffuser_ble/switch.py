"""Power and the source-plugin LongSpray mode."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory

from .entity import S5Entity


class S5PowerSwitch(S5Entity, SwitchEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "power", "Вкл/Выкл", "mdi:power")

    @property
    def is_on(self):
        return self.coordinator.power

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_power(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_power(False)


class S5LongSpraySwitch(S5Entity, SwitchEntity):
    _attr_name = "Непрерывное распыление"
    _attr_icon = "mdi:weather-windy"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        experimental = getattr(getattr(coordinator, "profile", None), "experimental", False)
        name = "Нулевая пауза (эксперимент)" if experimental else self._attr_name
        super().__init__(coordinator, "long_spray", name, self._attr_icon, EntityCategory.CONFIG)

    @property
    def is_on(self):
        value = self.coordinator.idle_time
        return None if value is None else value == 0

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_idle_time(0)

    async def async_turn_off(self, **kwargs) -> None:
        value = self.coordinator.last_idle_time or 3
        if not 3 <= value <= 30:
            raise HomeAssistantError("The previous SO diffuser pause is unknown; choose a pause value first")
        await self.coordinator.async_set_idle_time(value)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = entry.runtime_data
    entities = [S5PowerSwitch(coordinator)]
    if coordinator.profile.long_spray:
        entities.append(S5LongSpraySwitch(coordinator))
    async_add_entities(entities)

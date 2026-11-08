"""Shared HA identity and listener lifecycle for S5 entities."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo, Entity, EntityCategory

from .const import DOMAIN
from .models import get_profile


class S5Entity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator, key: str, name: str, icon: str, category=None) -> None:
        self.coordinator = coordinator
        profile = getattr(coordinator, "profile", None) or get_profile()
        self._attr_unique_id = f"{coordinator.address.replace(':', '').lower()}_{key}"
        self._attr_name = name
        self._attr_icon = icon
        if category is not None:
            self._attr_entity_category = category
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address.upper())},
            name="Xiaomi SO Diffuser BLE" if not profile.experimental else f"{profile.name} (experimental)",
            manufacturer="SO / BWJ",
            model=profile.name,
        )

    @property
    def available(self) -> bool:
        return self.coordinator.connected

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.coordinator.add_listener(self.async_write_ha_state))

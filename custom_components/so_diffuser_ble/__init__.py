"""Home Assistant entry points and one-time cleanup of retired UI entities."""
from __future__ import annotations

from .const import PLATFORMS
from .models import CONF_MODEL, CONF_EXPERIMENTAL, DEFAULT_MODEL, assert_model_opt_in


def _remove_legacy_entities(hass, entry) -> None:
    """Remove only this config entry's retired timer/schedule/select entities."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    address_key = entry.data["address"].replace(":", "").lower()
    legacy_switch_keys = {"timer_enabled"}
    legacy_switch_keys.update(
        f"schedule_{start:02d}_{start + 2:02d}" for start in range(0, 24, 2)
    )
    legacy_switch_keys.update(f"repeat_{index}" for index in range(7))
    obsolete = {f"{address_key}_{key}" for key in legacy_switch_keys}
    obsolete_select = f"{address_key}_idle_time"

    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (entity.domain == "switch" and entity.unique_id in obsolete) or (
            entity.domain == "select" and entity.unique_id == obsolete_select
        ):
            registry.async_remove(entity.entity_id)


async def async_setup_entry(hass, entry) -> bool:
    from homeassistant.const import Platform

    from .coordinator import S5Coordinator

    _remove_legacy_entities(hass, entry)
    profile = assert_model_opt_in(
        entry.data.get(CONF_MODEL, DEFAULT_MODEL),
        entry.data.get(CONF_EXPERIMENTAL, False),
    )
    coordinator = S5Coordinator(hass, entry.data["address"], profile.model)
    entry.runtime_data = coordinator
    coordinator.async_start()
    platforms = [getattr(Platform, platform.upper()) for platform in PLATFORMS]
    try:
        await hass.config_entries.async_forward_entry_setups(entry, platforms)
    except BaseException:
        await coordinator.async_shutdown()
        raise
    return True


async def async_unload_entry(hass, entry) -> bool:
    from homeassistant.const import Platform

    platforms = [getattr(Platform, platform.upper()) for platform in PLATFORMS]
    # SELECT was used by v0.2.0; unload it during an in-place integration reload.
    platforms.append(Platform.SELECT)
    if not await hass.config_entries.async_unload_platforms(entry, platforms):
        return False
    await entry.runtime_data.async_shutdown()
    return True

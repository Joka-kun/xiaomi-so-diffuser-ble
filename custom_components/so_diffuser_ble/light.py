"""SO RGB light: steady color and native device-controlled color cycle."""
from __future__ import annotations

import asyncio
from contextlib import suppress
import logging

from homeassistant.components.light import ColorMode, LightEntity, LightEntityFeature

from .entity import S5Entity
from .protocol import (
    LIGHT_GRADIENT_OFF,
    LIGHT_GRADIENT_ON,
    LIGHT_ENABLE_BIT,
    LIGHT_MAX_BRIGHTNESS,
    LIGHT_VALUE_MASK,
    light_brightness_to_ha,
    light_is_gradient,
    light_is_on,
    light_value_from_ha_brightness,
    light_value_off,
    light_value_restore,
)


EFFECT_STEADY = "Постоянный свет"
EFFECT_GRADIENT = "Автоматический градиент"
EFFECT_COLORS = "Смена цветов (HA)"
EFFECT_SUNSET = "Закат (HA)"

# These are optional, slow HA-driven palettes. They use the already verified
# fixed-color MIoT 3.9 setter, not speculative device firmware effect values.
# The native device gradient is preferable for smooth/offline color cycling.
PALETTE_INTERVAL_SECONDS = 8
SOFTWARE_PALETTES: dict[str, tuple[int, ...]] = {
    EFFECT_COLORS: (0xFF2424, 0xFF9C22, 0xFFE02B, 0x36D85D, 0x287BFF, 0xA94DFF),
    EFFECT_SUNSET: (0xFFB45C, 0xFF8335, 0xFF5B6E, 0xD257A5, 0x9455C0),
}
_LOGGER = logging.getLogger(__name__)


class S5Light(S5Entity, LightEntity):
    _attr_name = "Подсветка"
    _attr_icon = "mdi:lightbulb"
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_effect_list = [EFFECT_STEADY, EFFECT_GRADIENT, *SOFTWARE_PALETTES]
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "light", self._attr_name, self._attr_icon)
        self._palette_task: asyncio.Task | None = None
        self._palette_effect: str | None = None

    @property
    def is_on(self):
        return None if self.coordinator.light is None else light_is_on(self.coordinator.light)

    @property
    def color_mode(self):
        if not self.is_on:
            return None
        # During device-controlled color cycling, RGB is not user-adjustable.
        return ColorMode.ONOFF if light_is_gradient(self.coordinator.light) else ColorMode.RGB

    @property
    def brightness(self):
        return light_brightness_to_ha(self.coordinator.light)

    @property
    def rgb_color(self):
        if light_is_gradient(self.coordinator.light):
            return None
        value = self.coordinator.color
        return None if value is None else ((value >> 16) & 255, (value >> 8) & 255, value & 255)

    @property
    def effect(self):
        value = self.coordinator.light
        if not light_is_on(value):
            return None
        if light_is_gradient(value):
            return EFFECT_GRADIENT
        if self._palette_task is not None and not self._palette_task.done():
            return self._palette_effect
        return EFFECT_STEADY

    async def _stop_palette(self) -> None:
        """Cancel and join the active color loop before another light command."""
        task = self._palette_task
        self._palette_task = None
        self._palette_effect = None
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    async def _run_palette(self, colors: tuple[int, ...]) -> None:
        """At most one color write every eight seconds; stop on disconnect/off."""
        task = asyncio.current_task()
        index = 1
        try:
            while True:
                await asyncio.sleep(PALETTE_INTERVAL_SECONDS)
                if (
                    not self.coordinator.connected
                    or not light_is_on(self.coordinator.light)
                    or light_is_gradient(self.coordinator.light)
                ):
                    return
                await self.coordinator.async_set_color(colors[index])
                index = (index + 1) % len(colors)
        except asyncio.CancelledError:
            raise
        except Exception as err:
            _LOGGER.debug("SO software color effect stopped (%s)", type(err).__name__)
        finally:
            if self._palette_task is task:
                self._palette_task = None
                self._palette_effect = None
                if self.hass is not None:
                    self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        await self._stop_palette()
        await super().async_will_remove_from_hass()

    async def async_turn_on(self, **kwargs) -> None:
        effect = kwargs.get("effect")
        rgb = kwargs.get("rgb_color")
        brightness = kwargs.get("brightness")
        current = self.coordinator.light

        if effect not in (None, EFFECT_STEADY, EFFECT_GRADIENT, *SOFTWARE_PALETTES):
            raise ValueError("unsupported S5 light effect")
        if rgb is not None and effect in (EFFECT_GRADIENT, *SOFTWARE_PALETTES):
            raise ValueError("RGB cannot be changed while choosing a cycling effect")
        if brightness is not None and (
            type(brightness) is not int or not 0 <= brightness <= 255
        ):
            raise ValueError("S5 brightness must be an integer from 0 to 255")
        if rgb is not None and effect is None and brightness is None and light_is_gradient(current):
            raise ValueError("Switch S5 to steady light before setting its color")
        if rgb is not None and (
            not isinstance(rgb, (tuple, list))
            or len(rgb) != 3
            or any(type(channel) is not int or not 0 <= channel <= 255 for channel in rgb)
        ):
            raise ValueError("S5 RGB color must contain three bytes")

        if brightness == 0:
            if rgb is not None:
                raise ValueError("S5 color cannot be changed while turning the light off")
            await self.async_turn_off()
            return

        if (
            self._palette_task is not None
            and effect is None and rgb is None and brightness is None
        ):
            # A plain light.turn_on must not unintentionally cancel a cycle.
            return

        await self._stop_palette()

        if effect in SOFTWARE_PALETTES:
            # Existing bounded MIoT commands only: steady light plus RGB color.
            if brightness is not None:
                value = light_value_from_ha_brightness(brightness)
                await self.coordinator.async_set_light_value(value)
            elif light_is_gradient(current):
                await self.coordinator.async_set_light_value(LIGHT_GRADIENT_OFF)
            elif not light_is_on(current):
                await self.coordinator.async_set_light_value(light_value_restore(current))
            palette = SOFTWARE_PALETTES[effect]
            # First write is awaited: a rejected color will not launch a loop.
            await self.coordinator.async_set_color(palette[0])
            self._palette_effect = effect
            self._palette_task = self.hass.async_create_task(self._run_palette(palette))
            return

        if effect == EFFECT_GRADIENT:
            await self.coordinator.async_set_light_value(LIGHT_GRADIENT_ON)
        elif effect == EFFECT_STEADY:
            level = current & LIGHT_VALUE_MASK if current is not None else 0
            if brightness is not None:
                value = light_value_from_ha_brightness(brightness)
            elif not 1 <= level <= LIGHT_MAX_BRIGHTNESS:
                value = LIGHT_GRADIENT_OFF
            else:
                value = LIGHT_ENABLE_BIT | level
            await self.coordinator.async_set_light_value(value)
        elif brightness is not None:
            await self.coordinator.async_set_light_value(light_value_from_ha_brightness(brightness))
        elif not light_is_on(current):
            await self.coordinator.async_set_light_value(light_value_restore(current))

        if rgb is not None:
            await self.coordinator.async_set_color((rgb[0] << 16) | (rgb[1] << 8) | rgb[2])

    async def async_turn_off(self, **kwargs) -> None:
        await self._stop_palette()
        # The vendor UI clears bit 7. This disables the LED while retaining the
        # previous brightness/mode so the next ON can restore it.
        await self.coordinator.async_set_light_value(light_value_off(self.coordinator.light))


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    if entry.runtime_data.profile.light:
        async_add_entities([S5Light(entry.runtime_data)])

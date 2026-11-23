"""Select platform (IR Mode) for Local S02000 Camera."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import S02000CameraCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: S02000CameraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([S02000IRModeSelect(coordinator)])


class S02000IRModeSelect(CoordinatorEntity[S02000CameraCoordinator], SelectEntity):
    """Select entity for IR Night Vision mode (auto / day / night)."""

    _attr_has_entity_name = True
    _attr_name = "IR Mode"
    _attr_icon = "mdi:weather-night"
    _attr_options = ["auto", "day", "night"]

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_ir_mode"
        self._attr_device_info = coordinator.device_info

    @property
    def current_option(self) -> str | None:
        return (self.coordinator.data or {}).get("night_mode")

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_ir_mode(option)

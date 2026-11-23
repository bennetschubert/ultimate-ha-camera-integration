"""Sensor platform (IR State) for Local S02000 Camera."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
    async_add_entities([S02000IRStateSensor(coordinator)])


class S02000IRStateSensor(CoordinatorEntity[S02000CameraCoordinator], SensorEntity):
    """Shows live IR night/day state."""

    _attr_has_entity_name = True
    _attr_name = "IR State"
    _attr_icon = "mdi:eye"

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_ir_state"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> str | None:
        return (self.coordinator.data or {}).get("night_state")

"""Binary sensor platform (Motion Detection) for Local S02000 Camera."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    async_add_entities(
        [
            S02000MotionBinarySensor(coordinator),
            S02000SoundBinarySensor(coordinator),
        ]
    )


class S02000MotionBinarySensor(
    CoordinatorEntity[S02000CameraCoordinator], BinarySensorEntity
):
    """On-camera motion detector."""

    _attr_has_entity_name = True
    _attr_name = "Motion"
    _attr_device_class = BinarySensorDeviceClass.MOTION

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_motion"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get("motion", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "motion_score": int((self.coordinator.data or {}).get("motion_score", 0))
        }


class S02000SoundBinarySensor(
    CoordinatorEntity[S02000CameraCoordinator], BinarySensorEntity
):
    """On-camera sound / cry detector."""

    _attr_has_entity_name = True
    _attr_name = "Sound"
    _attr_device_class = BinarySensorDeviceClass.SOUND

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sound"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get("sound", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "sound_level": int((self.coordinator.data or {}).get("sound_level", 0))
        }

"""Sensor platform (IR State) for Local S02000 Camera."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
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
            S02000IRStateSensor(coordinator),
            S02000SoundLevelSensor(coordinator),
            S02000BrightnessSensor(coordinator),
        ]
    )


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


class S02000SoundLevelSensor(CoordinatorEntity[S02000CameraCoordinator], SensorEntity):
    """Live microphone noise level (0-100%)."""

    _attr_has_entity_name = True
    _attr_name = "Sound Level"
    _attr_icon = "mdi:waveform"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sound_level"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> int:
        return int((self.coordinator.data or {}).get("sound_level", 0))


class S02000BrightnessSensor(CoordinatorEntity[S02000CameraCoordinator], SensorEntity):
    """Estimated ambient brightness (0-100%) derived from ISP auto-exposure."""

    _attr_has_entity_name = True
    _attr_name = "Brightness"
    _attr_icon = "mdi:brightness-6"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_brightness"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> int:
        return int((self.coordinator.data or {}).get("brightness", 0))

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        return {"exposure": int((self.coordinator.data or {}).get("exposure", 0))}

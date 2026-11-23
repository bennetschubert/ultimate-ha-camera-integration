"""Number platform (Pan/Tilt angles & PTZ Step Size) for Local S02000 Camera."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEGREE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PAN_MAX_DEG, TILT_MAX_DEG
from .coordinator import S02000CameraCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: S02000CameraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            S02000PanNumber(coordinator),
            S02000TiltNumber(coordinator),
            S02000StepSizeNumber(coordinator),
            S02000MotionSensitivityNumber(coordinator),
            S02000SoundSensitivityNumber(coordinator),
        ]
    )


class S02000PanNumber(CoordinatorEntity[S02000CameraCoordinator], NumberEntity):
    """Current & target Pan angle in degrees."""

    _attr_has_entity_name = True
    _attr_name = "Pan Angle"
    _attr_icon = "mdi:pan-horizontal"
    _attr_native_unit_of_measurement = DEGREE
    _attr_native_min_value = 0.0
    _attr_native_max_value = PAN_MAX_DEG
    _attr_native_step = 5.0
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_pan_angle"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        return self.coordinator.pan_deg()

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_pan_deg(value)


class S02000TiltNumber(CoordinatorEntity[S02000CameraCoordinator], NumberEntity):
    """Current & target Tilt angle in degrees."""

    _attr_has_entity_name = True
    _attr_name = "Tilt Angle"
    _attr_icon = "mdi:pan-vertical"
    _attr_native_unit_of_measurement = DEGREE
    _attr_native_min_value = 0.0
    _attr_native_max_value = TILT_MAX_DEG
    _attr_native_step = 5.0
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_tilt_angle"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        return self.coordinator.tilt_deg()

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_tilt_deg(value)


class S02000StepSizeNumber(CoordinatorEntity[S02000CameraCoordinator], NumberEntity):
    """Step size for directional PTZ buttons."""

    _attr_has_entity_name = True
    _attr_name = "PTZ Step Size"
    _attr_icon = "mdi:axis-arrow"
    _attr_native_min_value = 50
    _attr_native_max_value = 1000
    _attr_native_step = 50
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_ptz_steps"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        return float(self.coordinator.ptz_steps)

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.ptz_steps = int(value)
        self.async_write_ha_state()


class S02000MotionSensitivityNumber(
    CoordinatorEntity[S02000CameraCoordinator], NumberEntity
):
    """On-camera motion detection sensitivity (1-100)."""

    _attr_has_entity_name = True
    _attr_name = "Motion Sensitivity"
    _attr_icon = "mdi:motion-sensor"
    _attr_native_min_value = 1
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_motion_sensitivity"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        return float((self.coordinator.data or {}).get("motion_sensitivity", 50))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_motion_sensitivity(int(value))


class S02000SoundSensitivityNumber(
    CoordinatorEntity[S02000CameraCoordinator], NumberEntity
):
    """On-camera sound / cry detection sensitivity (1-100)."""

    _attr_has_entity_name = True
    _attr_name = "Sound Sensitivity"
    _attr_icon = "mdi:ear-hearing"
    _attr_native_min_value = 1
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sound_sensitivity"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        return float((self.coordinator.data or {}).get("sound_sensitivity", 50))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_sound_sensitivity(int(value))

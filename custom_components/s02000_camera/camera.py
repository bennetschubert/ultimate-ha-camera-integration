"""Camera platform for Local S02000 Camera."""

from __future__ import annotations

from homeassistant.components.camera import Camera, CameraEntityFeature
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
    async_add_entities([S02000Camera(coordinator)])


class S02000Camera(CoordinatorEntity[S02000CameraCoordinator], Camera):
    """RTSP camera entity unified with PTZ and IR controls under one Device."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_camera"
        self._attr_device_info = coordinator.device_info
        self.stream_options["rtsp_transport"] = "tcp"

    async def stream_source(self) -> str:
        return self.coordinator.rtsp_url

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        return None

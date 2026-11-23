"""Media Player platform (Speaker / TTS playback) for Local S02000 Camera."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    async_process_play_media_url,
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
    async_add_entities([S02000SpeakerMediaPlayer(coordinator)])


class S02000SpeakerMediaPlayer(
    CoordinatorEntity[S02000CameraCoordinator], MediaPlayerEntity
):
    """Camera speaker entity supporting TTS and audio playback."""

    _attr_has_entity_name = True
    _attr_name = "Speaker"
    _attr_icon = "mdi:speaker"
    _attr_supported_features = MediaPlayerEntityFeature.PLAY_MEDIA

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_speaker"
        self._attr_device_info = coordinator.device_info
        self._playing = False

    @property
    def state(self) -> MediaPlayerState:
        return MediaPlayerState.PLAYING if self._playing else MediaPlayerState.IDLE

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        url = async_process_play_media_url(self.hass, media_id)
        self._playing = True
        self.async_write_ha_state()
        try:
            await self.coordinator.async_play_audio_url(url)
        finally:
            self._playing = False
            self.async_write_ha_state()

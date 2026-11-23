"""Media Player platform (Speaker / TTS playback + volume) for Local S02000 Camera."""

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
    """Camera speaker entity supporting TTS, audio playback, volume, and mute."""

    _attr_has_entity_name = True
    _attr_name = "Speaker"
    _attr_icon = "mdi:speaker"
    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
    )

    def __init__(self, coordinator: S02000CameraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_speaker"
        self._attr_device_info = coordinator.device_info
        self._playing = False
        self._pre_mute_volume = 0.7

    @property
    def state(self) -> MediaPlayerState:
        return MediaPlayerState.PLAYING if self._playing else MediaPlayerState.IDLE

    @property
    def volume_level(self) -> float:
        vol = int((self.coordinator.data or {}).get("volume", 70))
        return max(0.0, min(1.0, vol / 100.0))

    @property
    def is_volume_muted(self) -> bool:
        return self.volume_level == 0.0

    async def async_set_volume_level(self, volume: float) -> None:
        if volume > 0:
            self._pre_mute_volume = volume
        await self.coordinator.async_set_volume(volume)

    async def async_mute_volume(self, mute: bool) -> None:
        if mute:
            if self.volume_level > 0:
                self._pre_mute_volume = self.volume_level
            await self.coordinator.async_set_volume(0.0)
        else:
            await self.coordinator.async_set_volume(self._pre_mute_volume or 0.7)

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

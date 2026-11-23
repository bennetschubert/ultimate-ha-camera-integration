"""Button platform (PTZ directions) for Local S02000 Camera."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import S02000CameraCoordinator

PTZ_BUTTONS: tuple[tuple[str, str, str], ...] = (
    ("left", "Pan Left", "mdi:arrow-left-bold"),
    ("right", "Pan Right", "mdi:arrow-right-bold"),
    ("up", "Tilt Up", "mdi:arrow-up-bold"),
    ("down", "Tilt Down", "mdi:arrow-down-bold"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: S02000CameraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [S02000PTZButton(coordinator, d, name, icon) for d, name, icon in PTZ_BUTTONS]
    )


class S02000PTZButton(CoordinatorEntity[S02000CameraCoordinator], ButtonEntity):
    """Directional PTZ button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: S02000CameraCoordinator,
        direction: str,
        name: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._direction = direction
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.entry.entry_id}_ptz_{direction}"
        self._attr_device_info = coordinator.device_info

    async def async_press(self) -> None:
        await self.coordinator.async_ptz_dir(self._direction)

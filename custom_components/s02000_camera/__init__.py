"""Local S02000 Camera integration."""

from __future__ import annotations

import asyncio
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PLATFORMS
from .coordinator import S02000CameraCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SHOW_PIP = "show_pip"
SHOW_PIP_SCHEMA = vol.Schema(
    {
        vol.Required("pipup_url"): cv.string,
        vol.Optional("stream_url", default=""): cv.string,
        vol.Optional("title", default="Baby Monitor"): cv.string,
        vol.Optional("message", default=""): cv.string,
        vol.Optional("duration", default=30): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=14400)
        ),
        vol.Optional("position", default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=4)
        ),
        vol.Optional("width", default=480): vol.All(
            vol.Coerce(int), vol.Range(min=160, max=1280)
        ),
        vol.Optional("height", default=270): vol.All(
            vol.Coerce(int), vol.Range(min=90, max=720)
        ),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Local S02000 Camera from a config entry."""
    coordinator = S02000CameraCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.async_start_sse()

    if not hass.services.has_service(DOMAIN, SERVICE_SHOW_PIP):

        async def _handle_show_pip(call: ServiceCall) -> None:
            session = async_get_clientsession(hass)
            stream_url = call.data["stream_url"]
            if stream_url:
                payload = {
                    "duration": call.data["duration"],
                    "position": call.data["position"],
                    "title": call.data["title"],
                    "titleColor": "#ffffff",
                    "titleSize": 16,
                    "message": call.data["message"],
                    "messageColor": "#dddddd",
                    "messageSize": 12,
                    "backgroundColor": "#dd111111",
                    "media": {
                        "web": {
                            "uri": stream_url,
                            "width": call.data["width"],
                            "height": call.data["height"],
                        }
                    },
                }
            else:
                # Dismiss / hide any active PiP overlay immediately
                payload = {
                    "duration": 1,
                    "position": call.data["position"],
                    "title": "",
                    "message": "",
                    "backgroundColor": "#00000000",
                }
            try:
                async with asyncio.timeout(5):
                    async with session.post(
                        call.data["pipup_url"], json=payload
                    ) as resp:
                        if resp.status >= 400:
                            _LOGGER.warning(
                                "PiPup returned HTTP %s: %s",
                                resp.status,
                                await resp.text(),
                            )
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Failed to send PiPup overlay: %s", err)

        hass.services.async_register(
            DOMAIN, SERVICE_SHOW_PIP, _handle_show_pip, schema=SHOW_PIP_SCHEMA
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: S02000CameraCoordinator | None = hass.data.get(DOMAIN, {}).get(
        entry.entry_id
    )
    if coordinator is not None:
        await coordinator.async_stop_sse()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

"""DataUpdateCoordinator for Local S02000 Camera."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_HOST,
    CONF_HTTP_PORT,
    CONF_NAME,
    CONF_RTSP_PORT,
    DEFAULT_HTTP_PORT,
    DEFAULT_NAME,
    DEFAULT_PTZ_STEPS,
    DEFAULT_RTSP_PORT,
    DOMAIN,
    PAN_MAX_DEG,
    TILT_MAX_DEG,
)

_LOGGER = logging.getLogger(__name__)


class S02000CameraCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls /api/status and sends PTZ/IR commands to the camera."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.host: str = entry.data[CONF_HOST]
        self.name_str: str = entry.data.get(CONF_NAME, DEFAULT_NAME)
        self.http_port: int = entry.data.get(CONF_HTTP_PORT, DEFAULT_HTTP_PORT)
        self.rtsp_port: int = entry.data.get(CONF_RTSP_PORT, DEFAULT_RTSP_PORT)
        self.ptz_steps: int = DEFAULT_PTZ_STEPS
        self._session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.host}",
            update_interval=timedelta(seconds=3),
        )

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.http_port}"

    @property
    def rtsp_url(self) -> str:
        return f"rtsp://{self.host}:{self.rtsp_port}/"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.name_str,
            manufacturer="Ambiano / Local",
            model="NP-CSH-8645 (AK3918AV130)",
            configuration_url=f"{self.base_url}/",
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            async with asyncio.timeout(5):
                async with self._session.get(f"{self.base_url}/api/status") as resp:
                    resp.raise_for_status()
                    return await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Error communicating with camera {self.host}: {err}") from err

    async def async_set_ir_mode(self, mode: str) -> None:
        async with asyncio.timeout(5):
            async with self._session.post(f"{self.base_url}/api/ir?mode={mode}") as resp:
                resp.raise_for_status()
                self.async_set_updated_data(await resp.json(content_type=None))

    async def async_ptz_dir(self, direction: str, steps: int | None = None) -> None:
        step_val = steps if steps is not None else self.ptz_steps
        async with asyncio.timeout(5):
            async with self._session.post(
                f"{self.base_url}/api/ptz?dir={direction}&steps={step_val}"
            ) as resp:
                resp.raise_for_status()
                self.async_set_updated_data(await resp.json(content_type=None))

    async def async_set_pan_deg(self, deg: float) -> None:
        pan_range = int((self.data or {}).get("pan_range", 4096))
        target = int(round((deg / PAN_MAX_DEG) * pan_range))
        async with asyncio.timeout(5):
            async with self._session.post(f"{self.base_url}/api/ptz?pan_abs={target}") as resp:
                resp.raise_for_status()
                self.async_set_updated_data(await resp.json(content_type=None))

    async def async_set_tilt_deg(self, deg: float) -> None:
        tilt_range = int((self.data or {}).get("tilt_range", 4096))
        target = int(round((deg / TILT_MAX_DEG) * tilt_range))
        async with asyncio.timeout(5):
            async with self._session.post(f"{self.base_url}/api/ptz?tilt_abs={target}") as resp:
                resp.raise_for_status()
                self.async_set_updated_data(await resp.json(content_type=None))

    def pan_deg(self) -> float:
        data = self.data or {}
        pan = int(data.get("pan", 0))
        pan_range = max(1, int(data.get("pan_range", 4096)))
        return round((pan / pan_range) * PAN_MAX_DEG, 1)

    def tilt_deg(self) -> float:
        data = self.data or {}
        tilt = int(data.get("tilt", 0))
        tilt_range = max(1, int(data.get("tilt_range", 4096)))
        return round((tilt / tilt_range) * TILT_MAX_DEG, 1)

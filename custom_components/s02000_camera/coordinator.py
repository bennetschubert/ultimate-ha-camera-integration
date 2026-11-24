"""DataUpdateCoordinator for Local S02000 Camera."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import json
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
        self._sse_task: asyncio.Task[None] | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.host}",
            # Live state arrives via SSE (/api/events); 60s poll is only a safety fallback
            update_interval=timedelta(seconds=60),
        )

    def async_start_sse(self) -> None:
        """Start background Server-Sent Events listener for real-time local push."""
        if self._sse_task is None or self._sse_task.done():
            self._sse_task = self.entry.async_create_background_task(
                self.hass,
                self._async_sse_loop(),
                f"{DOMAIN}_{self.host}_sse",
            )

    async def async_stop_sse(self) -> None:
        """Cancel the SSE listener cleanly on unload."""
        if self._sse_task is not None:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
            self._sse_task = None

    async def _async_sse_loop(self) -> None:
        """Maintain a single persistent SSE stream to /api/events with auto-reconnect."""
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=5, sock_read=45)
        while True:
            try:
                async with self._session.get(
                    f"{self.base_url}/api/events",
                    headers={"Accept": "text/event-stream"},
                    timeout=timeout,
                ) as resp:
                    resp.raise_for_status()
                    _LOGGER.debug("Connected to camera SSE stream at %s", self.host)
                    async for raw_line in resp.content:
                        line = raw_line.decode("utf-8", errors="ignore").strip()
                        if not line or line.startswith(":"):
                            continue
                        if line.startswith("data:"):
                            payload = line[5:].strip()
                            try:
                                data = json.loads(payload)
                                if isinstance(data, dict):
                                    self.async_set_updated_data(data)
                            except ValueError:
                                pass
            except asyncio.CancelledError:
                raise
            except (aiohttp.ClientError, TimeoutError, OSError) as err:
                _LOGGER.debug(
                    "Camera SSE disconnected (%s), reconnecting in 3s: %s",
                    self.host,
                    err,
                )
            await asyncio.sleep(3)

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
        tilt_range = int((self.data or {}).get("tilt_range", 740))
        target = int(round((deg / TILT_MAX_DEG) * tilt_range))
        async with asyncio.timeout(5):
            async with self._session.post(f"{self.base_url}/api/ptz?tilt_abs={target}") as resp:
                resp.raise_for_status()
                self.async_set_updated_data(await resp.json(content_type=None))

    async def async_calibrate(self) -> None:
        async with asyncio.timeout(5):
            async with self._session.post(f"{self.base_url}/api/ptz?calibrate=1") as resp:
                resp.raise_for_status()
                self.async_set_updated_data(await resp.json(content_type=None))

    async def async_beep(self, freq: int = 880, ms: int = 400) -> None:
        async with asyncio.timeout(5):
            async with self._session.post(
                f"{self.base_url}/api/audio/beep?freq={freq}&ms={ms}"
            ) as resp:
                resp.raise_for_status()

    async def async_set_volume(self, level: float) -> None:
        pct = max(0, min(100, int(round(level * 100))))
        async with asyncio.timeout(5):
            async with self._session.post(
                f"{self.base_url}/api/audio/volume?level={pct}"
            ) as resp:
                resp.raise_for_status()
                self.async_set_updated_data(await resp.json(content_type=None))

    async def async_set_motion_sensitivity(self, sensitivity: int) -> None:
        val = max(1, min(100, int(sensitivity)))
        async with asyncio.timeout(5):
            async with self._session.post(
                f"{self.base_url}/api/motion?sensitivity={val}"
            ) as resp:
                resp.raise_for_status()
                self.async_set_updated_data(await resp.json(content_type=None))

    async def async_set_sound_sensitivity(self, sensitivity: int) -> None:
        val = max(1, min(100, int(sensitivity)))
        async with asyncio.timeout(5):
            async with self._session.post(
                f"{self.base_url}/api/audio/sound?sensitivity={val}"
            ) as resp:
                resp.raise_for_status()
                self.async_set_updated_data(await resp.json(content_type=None))

    async def async_set_mic_gain(self, level: int) -> None:
        val = max(0, min(100, int(level)))
        async with asyncio.timeout(5):
            async with self._session.post(
                f"{self.base_url}/api/audio/mic_gain?level={val}"
            ) as resp:
                resp.raise_for_status()
                self.async_set_updated_data(await resp.json(content_type=None))

    async def async_play_audio_url(self, media_url: str) -> None:
        """Transcode any audio/TTS URL to 8kHz 16-bit mono PCM via ffmpeg and play on camera."""
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            media_url,
            "-ar",
            "8000",
            "-ac",
            "1",
            "-f",
            "s16le",
            "pipe:1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        pcm_data, stderr = await asyncio.wait_for(proc.communicate(), timeout=20)
        if proc.returncode != 0 or not pcm_data:
            raise RuntimeError(f"ffmpeg failed ({proc.returncode}): {stderr.decode(errors='replace')}")

        # Camera HTTP endpoint accepts up to 256 KB (~16s of 8kHz mono PCM) per request; chunk if longer
        chunk_size = 240000
        for off in range(0, len(pcm_data), chunk_size):
            chunk = pcm_data[off : off + chunk_size]
            async with asyncio.timeout(25):
                async with self._session.post(
                    f"{self.base_url}/api/audio/play",
                    data=chunk,
                    headers={"Content-Type": "application/octet-stream"},
                ) as resp:
                    resp.raise_for_status()

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

"""Config flow for Local S02000 Camera."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_HOST,
    CONF_HTTP_PORT,
    CONF_NAME,
    CONF_RTSP_PORT,
    DEFAULT_HTTP_PORT,
    DEFAULT_NAME,
    DEFAULT_RTSP_PORT,
    DOMAIN,
)


class S02000CameraConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Local S02000 Camera."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            http_port = user_input[CONF_HTTP_PORT]
            await self.async_set_unique_id(f"{host}:{http_port}")
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            try:
                async with asyncio.timeout(5):
                    async with session.get(f"http://{host}:{http_port}/api/status") as resp:
                        resp.raise_for_status()
                        await resp.json(content_type=None)
            except (aiohttp.ClientError, TimeoutError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_HOST: host,
                        CONF_HTTP_PORT: http_port,
                        CONF_RTSP_PORT: user_input[CONF_RTSP_PORT],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_HOST, default="192.168.178.73"): str,
                vol.Required(CONF_HTTP_PORT, default=DEFAULT_HTTP_PORT): int,
                vol.Required(CONF_RTSP_PORT, default=DEFAULT_RTSP_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

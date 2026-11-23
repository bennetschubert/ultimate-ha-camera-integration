"""Constants for the Local S02000 Camera integration."""

from homeassistant.const import Platform

DOMAIN = "s02000_camera"

CONF_HOST = "host"
CONF_NAME = "name"
CONF_HTTP_PORT = "http_port"
CONF_RTSP_PORT = "rtsp_port"

DEFAULT_NAME = "Flur Camera"
DEFAULT_HTTP_PORT = 80
DEFAULT_RTSP_PORT = 554
DEFAULT_PTZ_STEPS = 300

PAN_MAX_DEG = 350.0
TILT_MAX_DEG = 65.0

PLATFORMS: list[Platform] = [
    Platform.CAMERA,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
]

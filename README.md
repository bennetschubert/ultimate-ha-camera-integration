# Local S02000 Camera (AK3918AV130)

100% local, cloud-free Home Assistant custom integration for Ambiano `NP-CSH-8645` (`S02000` / `JS02000`, Anyka `AK3918AV130`) cameras running the local `ak_rtsp` + HTTP API firmware.

## Features (Single Unified HA Device)
- **Camera (`camera.*`)** — 1080p H.264 RTSP stream (`rtsp://<host>:554/`)
- **IR Mode (`select.*`)** — `auto` / `day` / `night`
- **IR State (`sensor.*`)** — live `day` / `night` state
- **Pan & Tilt Angles (`number.*`)** — live position in degrees + sliders for absolute positioning
- **PTZ Controls (`button.*` + `number.*`)** — Pan Left/Right, Tilt Up/Down, and configurable step size

## Installation via HACS
1. Open **HACS** in Home Assistant.
2. Click the **⋮** menu (top right) → **Custom repositories**.
3. Paste this repository's GitHub URL, select category **Integration**, and click **Add**.
4. Search for **Local S02000 Camera** in HACS → **Download** → **Restart Home Assistant**.
5. Go to **Settings → Devices & Services → + Add Integration → Local S02000 Camera** and enter your camera's IP address.

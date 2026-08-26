# FRIDAY — God's Eye View integration

FRIDAY now has an optional integration boundary for the supplied **God's Eye View** project.

## What is integrated

The Python worker does not import the browser/Cesium application directly. Instead, FRIDAY exposes a stable capability registry and MCP interface:

- `gods_eye_view_manifest` — capability/configuration discovery.
- `gods_eye_view_health` — non-fatal endpoint health check.
- `friday://gods-eye-view` — MCP resource containing the feature manifest.
- `FRIDAY_GODS_EYE_VIEW_URL` — endpoint configuration.

The supplied archive is treated as the source feature package. Its SHA-256 is pinned in `friday_agent/gods_eye_view.py` so future replacements can be detected explicitly.

## Capabilities registered

- Photorealistic 3D globe
- Live aircraft and military contacts
- Live vessel tracking
- Satellites and space missions
- Earthquakes and active fires
- Traffic and CCTV context
- Radio and environmental layers
- Voice camera control
- Map annotations and measurements
- Cockpit and sensor views

## Deployment model

God's Eye View is deliberately optional. FRIDAY starts normally when `FRIDAY_GODS_EYE_VIEW_URL` is empty, and the health check reports the feature as unconfigured rather than failing the worker.

Deploy the God's Eye View web application separately, then set:

`FRIDAY_GODS_EYE_VIEW_URL=https://<your-gev-host>`

The full supplied archive is intentionally not copied wholesale into the Python worker image: it is a browser/Cesium application with large binary assets and its own Node/Vite runtime. Keeping it as an optional web module prevents the LiveKit worker image from becoming unnecessarily large or coupling Python startup to browser-only dependencies.

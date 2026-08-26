from __future__ import annotations

import os
from typing import Any

from friday_agent.mcp_tools import ToolResult, fetch_url


GODS_EYE_VIEW_URL = os.getenv("FRIDAY_GODS_EYE_VIEW_URL", "").strip().rstrip("/")
GODS_EYE_VIEW_NAME = "God's Eye View"
GODS_EYE_VIEW_SOURCE_SHA256 = "506fe6510be5ee2ee8d9772072bf1c30fc9e95c2df32baca37b4068f482741d7"

# Capability map derived from the supplied God's Eye View package. Keep this
# registry capability-oriented so the FRIDAY agent can reason about the module
# without importing its browser-only Cesium runtime into the Python worker.
CAPABILITIES: tuple[str, ...] = (
    "photorealistic_3d_globe",
    "live_aircraft_and_military_contacts",
    "live_vessel_tracking",
    "satellites_and_space_missions",
    "earthquakes_and_active_fires",
    "traffic_and_cctv_context",
    "radio_and_environmental_layers",
    "voice_camera_control",
    "map_annotations_and_measurements",
    "cockpit_and_sensor_views",
)


def feature_manifest() -> dict[str, Any]:
    """Return the stable FRIDAY integration manifest for God's Eye View."""
    return {
        "name": GODS_EYE_VIEW_NAME,
        "enabled": bool(GODS_EYE_VIEW_URL),
        "url": GODS_EYE_VIEW_URL or None,
        "capabilities": list(CAPABILITIES),
        "source_sha256": GODS_EYE_VIEW_SOURCE_SHA256,
        "integration": "optional-browser-module",
    }


async def health_check(timeout_seconds: float = 5.0) -> ToolResult:
    """Check the configured God's Eye View endpoint without failing FRIDAY startup."""
    if not GODS_EYE_VIEW_URL:
        return ToolResult(
            ok=True,
            content="God's Eye View is not configured; FRIDAY will continue without it.",
            metadata={"configured": False, "feature": GODS_EYE_VIEW_NAME},
        )

    result = await fetch_url(GODS_EYE_VIEW_URL, timeout_seconds)
    return ToolResult(
        ok=result.ok,
        content=("God's Eye View endpoint is reachable." if result.ok else result.content),
        metadata={**result.metadata, "configured": True, "feature": GODS_EYE_VIEW_NAME},
    )

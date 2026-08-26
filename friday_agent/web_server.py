"""Web server providing real-time dashboard and metrics for FRIDAY UI."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from friday_agent.config import config
from friday_agent.observability import metrics, telemetry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("friday_agent.web_server")


class ConnectionManager:
    """Manage WebSocket connections for real-time dashboard updates."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Register new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected. Total connections: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister closed WebSocket connection."""
        self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected. Total connections: %d", len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.warning("Failed to send WebSocket message: %s", exc)
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Handle startup and shutdown events."""
    logger.info("Starting FRIDAY Web Server (port 8001)")
    # Start metrics collection task
    metrics_task = asyncio.create_task(_metrics_broadcast_loop())
    yield
    logger.info("Shutting down FRIDAY Web Server")
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="FRIDAY AI Agent",
    description="Real-time dashboard for FRIDAY personal assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
async def get_status() -> dict[str, Any]:
    """Get current FRIDAY system status."""
    return {
        "identity": config.identity,
        "metrics": metrics.get_current_metrics(),
        "memory": telemetry.get_memory_stats(),
    }


@app.get("/api/metrics")
async def get_metrics() -> dict[str, Any]:
    """Get detailed metrics snapshot."""
    return metrics.get_detailed_metrics()


@app.get("/api/events")
async def get_recent_events(limit: int = 50) -> list[dict[str, Any]]:
    """Get recent system events."""
    return telemetry.get_recent_events(limit)


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time metrics streaming."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive heartbeat
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
        manager.disconnect(websocket)


async def _metrics_broadcast_loop() -> None:
    """Continuously broadcast metrics to connected clients."""
    while True:
        try:
            await asyncio.sleep(0.5)  # Update every 500ms
            current_metrics = metrics.get_current_metrics()
            await manager.broadcast(
                {
                    "type": "metrics_update",
                    "data": current_metrics,
                    "timestamp": current_metrics.get("timestamp"),
                }
            )
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Error in metrics broadcast loop: %s", exc)


@app.get("/")
async def serve_index() -> FileResponse:
    """Serve the web UI index."""
    return FileResponse("web/dist/index.html")


try:
    app.mount("/", StaticFiles(directory="web/dist", html=True), name="static")
except RuntimeError:
    logger.warning("Web UI dist directory not found; static files not mounted")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

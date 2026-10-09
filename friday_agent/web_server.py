"""HTTP and WebSocket server for the FRIDAY dashboard."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from friday_agent.config import config
from friday_agent.observability import metrics, telemetry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("friday_agent.web_server")
WEB_DIST = Path(__file__).resolve().parents[1] / "web" / "dist"


class ConnectionManager:
    """Manage WebSocket clients without allowing stale sockets to break broadcasts."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        metrics.update_connections(len(self.active_connections))
        logger.info("WebSocket client connected. Total connections: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            metrics.update_connections(len(self.active_connections))
            logger.info("WebSocket client disconnected. Total connections: %d", len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        connections = tuple(self.active_connections)
        if not connections:
            return

        async def send(connection: WebSocket) -> bool:
            try:
                await asyncio.wait_for(connection.send_json(message), timeout=1.0)
                return True
            except Exception as exc:
                logger.debug("Dropping unresponsive WebSocket client: %s", exc)
                return False

        results = await asyncio.gather(*(send(connection) for connection in connections))
        for connection, sent in zip(connections, results):
            if not sent:
                self.disconnect(connection)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start and stop the lightweight telemetry broadcast task."""
    logger.info("Starting FRIDAY Web Server (port 8001)")
    metrics_task = asyncio.create_task(_metrics_broadcast_loop())
    try:
        yield
    finally:
        logger.info("Shutting down FRIDAY Web Server")
        metrics_task.cancel()
        try:
            await metrics_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="FRIDAY AI Agent",
    description="Realtime dashboard API for FRIDAY",
    version="1.1.0",
    lifespan=lifespan,
)

# Same-origin deployment needs no CORS. For split-origin deployments, explicitly
# list trusted origins in FRIDAY_CORS_ORIGINS (comma-separated).
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRIDAY_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)


@app.get("/healthz", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return a lightweight liveness signal without exposing runtime details."""
    return {"status": "ok"}


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
async def get_recent_events(limit: int = Query(default=50, ge=1, le=100)) -> list[dict[str, Any]]:
    """Get a bounded page of recent system events."""
    return telemetry.get_recent_events(limit)


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket) -> None:
    """Keep a dashboard socket alive and respond to client heartbeats."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        logger.exception("WebSocket error")
        manager.disconnect(websocket)


async def _metrics_broadcast_loop() -> None:
    """Broadcast telemetry without letting a slow client stall all other clients."""
    while True:
        try:
            await asyncio.sleep(1.0)
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
        except Exception:
            logger.exception("Error in metrics broadcast loop")


@app.get("/")
async def serve_index() -> FileResponse:
    """Serve the compiled dashboard, with an actionable error before the first build."""
    index = WEB_DIST / "index.html"
    if not index.is_file():
        raise HTTPException(
            status_code=503,
            detail="FRIDAY dashboard is not built. Run 'cd web && npm install && npm run build'.",
        )
    return FileResponse(index)


if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="static")
else:
    logger.info("Dashboard build not present; API-only mode enabled until web/dist is built")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

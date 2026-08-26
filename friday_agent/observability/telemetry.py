"""Telemetry and event tracking for FRIDAY observability."""

from __future__ import annotations

import json
import logging
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("friday_agent.observability.telemetry")

# Maximum events to keep in memory
MAX_EVENTS = 1000


@dataclass
class TelemetryEvent:
    """A single telemetry event."""

    timestamp: str
    event_type: str  # agent_state, api_call, tool_execution, error, memory_update
    severity: str  # info, warning, error, critical
    message: str
    metadata: dict[str, Any]


class TelemetryCollector:
    """Collect and manage system events."""

    def __init__(self) -> None:
        self.events: deque[TelemetryEvent] = deque(maxlen=MAX_EVENTS)
        self.memory_state: dict[str, Any] = {}

    def record_event(
        self,
        event_type: str,
        message: str,
        severity: str = "info",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a telemetry event."""
        event = TelemetryEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            severity=severity,
            message=message,
            metadata=metadata or {},
        )
        self.events.append(event)

        # Log based on severity
        if severity == "critical":
            logger.critical(message)
        elif severity == "error":
            logger.error(message)
        elif severity == "warning":
            logger.warning(message)
        else:
            logger.info(message)

    def update_memory(self, key: str, value: Any) -> None:
        """Update memory state tracking."""
        self.memory_state[key] = value

    def get_memory_stats(self) -> dict[str, Any]:
        """Get memory state summary."""
        return {
            "items": len(self.memory_state),
            "keys": list(self.memory_state.keys()),
            "state": self.memory_state.copy(),
        }

    def get_recent_events(self, limit: int = 50, event_type: str | None = None) -> list[dict[str, Any]]:
        """Get recent events, optionally filtered by type."""
        events_list = list(self.events)

        if event_type:
            events_list = [e for e in events_list if e.event_type == event_type]

        # Return most recent events first
        return [asdict(e) for e in reversed(events_list[-limit:])]

    def clear_events(self) -> None:
        """Clear all events."""
        self.events.clear()
        logger.info("Telemetry events cleared")


# Global collector instance
_collector = TelemetryCollector()


def record_agent_state_change(state: str, metadata: dict[str, Any] | None = None) -> None:
    """Record agent state change event."""
    _collector.record_event(
        event_type="agent_state",
        message=f"Agent state changed to {state}",
        severity="info",
        metadata=metadata or {},
    )


def record_api_call(
    api_name: str,
    duration_ms: float,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Record API call event."""
    severity = "warning" if not success else "info"
    message = f"API call: {api_name} - {duration_ms:.1f}ms"
    if error:
        message += f" - Error: {error}"

    _collector.record_event(
        event_type="api_call",
        message=message,
        severity=severity,
        metadata={
            "api_name": api_name,
            "duration_ms": duration_ms,
            "success": success,
            "error": error,
        },
    )


def record_tool_execution(tool_name: str, success: bool = True, error: str | None = None) -> None:
    """Record tool execution event."""
    severity = "warning" if not success else "info"
    message = f"Tool execution: {tool_name}"
    if error:
        message += f" - Error: {error}"

    _collector.record_event(
        event_type="tool_execution",
        message=message,
        severity=severity,
        metadata={
            "tool_name": tool_name,
            "success": success,
            "error": error,
        },
    )


def record_error(error_message: str, error_type: str = "unknown", severity: str = "error") -> None:
    """Record system error event."""
    _collector.record_event(
        event_type="error",
        message=error_message,
        severity=severity,
        metadata={"error_type": error_type},
    )


def update_memory_state(key: str, value: Any) -> None:
    """Update tracked memory state."""
    _collector.update_memory(key, value)


def get_memory_stats() -> dict[str, Any]:
    """Get memory statistics."""
    return _collector.get_memory_stats()


def get_recent_events(limit: int = 50, event_type: str | None = None) -> list[dict[str, Any]]:
    """Get recent telemetry events."""
    return _collector.get_recent_events(limit, event_type)


def get_all_events() -> list[dict[str, Any]]:
    """Get all recorded events."""
    return [asdict(e) for e in _collector.events]

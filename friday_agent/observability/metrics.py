"""Real-time metrics collection for FRIDAY observability."""

from __future__ import annotations

import logging
import platform
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("friday_agent.observability.metrics")


@dataclass
class SystemMetrics:
    """Snapshot of system health metrics."""

    timestamp: str
    identity: str
    state: str  # active, idle, processing, error
    uptime_seconds: float
    memory_usage_percent: float
    active_connections: int
    api_calls_total: int
    api_calls_failed: int
    avg_response_time_ms: float
    tool_execution_count: int
    tool_execution_failures: int


class MetricsCollector:
    """Collect and expose real-time metrics."""

    def __init__(self) -> None:
        self.start_time = time.time()
        self.state = "idle"
        self.active_connections = 0
        self.api_calls_total = 0
        self.api_calls_failed = 0
        self.response_times: list[float] = []
        self.tool_executions = 0
        self.tool_failures = 0
        self.last_activity = time.time()

    def set_state(self, state: str) -> None:
        """Update agent state."""
        self.state = state
        self.last_activity = time.time()
        logger.debug("Agent state changed to: %s", state)

    def record_api_call(self, duration_ms: float, success: bool = True) -> None:
        """Record an API call and its duration."""
        self.api_calls_total += 1
        if not success:
            self.api_calls_failed += 1
        self.response_times.append(duration_ms)
        # Keep only last 100 response times for average calculation
        if len(self.response_times) > 100:
            self.response_times.pop(0)
        self.last_activity = time.time()

    def record_tool_execution(self, success: bool = True) -> None:
        """Record tool execution."""
        self.tool_executions += 1
        if not success:
            self.tool_failures += 1
        self.last_activity = time.time()

    def update_connections(self, count: int) -> None:
        """Update active connection count."""
        self.active_connections = count

    def get_metrics(self) -> SystemMetrics:
        """Get current metrics snapshot."""
        uptime = time.time() - self.start_time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0

        # Simple memory estimation based on Python process
        try:
            import psutil

            process = psutil.Process()
            memory_percent = process.memory_percent()
        except (ImportError, Exception):
            memory_percent = 0.0

        return SystemMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            identity="friday-ai-agent",
            state=self.state,
            uptime_seconds=uptime,
            memory_usage_percent=memory_percent,
            active_connections=self.active_connections,
            api_calls_total=self.api_calls_total,
            api_calls_failed=self.api_calls_failed,
            avg_response_time_ms=avg_response_time,
            tool_execution_count=self.tool_executions,
            tool_execution_failures=self.tool_failures,
        )


# Global collector instance
_collector = MetricsCollector()


def set_state(state: str) -> None:
    """Set agent state (active, idle, processing, error)."""
    _collector.set_state(state)


def record_api_call(duration_ms: float, success: bool = True) -> None:
    """Record an API call."""
    _collector.record_api_call(duration_ms, success)


def record_tool_execution(success: bool = True) -> None:
    """Record a tool execution."""
    _collector.record_tool_execution(success)


def update_connections(count: int) -> None:
    """Update active connection count."""
    _collector.update_connections(count)


def get_current_metrics() -> dict[str, Any]:
    """Get current metrics as dictionary."""
    metrics = _collector.get_metrics()
    return asdict(metrics)


def get_detailed_metrics() -> dict[str, Any]:
    """Get detailed metrics with additional diagnostics."""
    metrics = _collector.get_metrics()
    metrics_dict = asdict(metrics)

    # Add system info
    metrics_dict["system"] = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
    }

    # Add health score (0-100)
    health_score = _calculate_health_score(metrics)
    metrics_dict["health_score"] = health_score

    return metrics_dict


def _calculate_health_score(metrics: SystemMetrics) -> int:
    """Calculate overall system health score (0-100)."""
    score = 100

    # Penalize for failures
    if metrics.api_calls_total > 0:
        failure_rate = metrics.api_calls_failed / metrics.api_calls_total
        score -= int(failure_rate * 30)

    if metrics.tool_execution_count > 0:
        tool_failure_rate = metrics.tool_execution_failures / metrics.tool_execution_count
        score -= int(tool_failure_rate * 20)

    # Penalize for high memory usage
    if metrics.memory_usage_percent > 80:
        score -= 15
    elif metrics.memory_usage_percent > 60:
        score -= 5

    # Penalize for slow responses
    if metrics.avg_response_time_ms > 1000:
        score -= 10
    elif metrics.avg_response_time_ms > 500:
        score -= 5

    # Penalize for error state
    if metrics.state == "error":
        score -= 25

    return max(0, min(100, score))

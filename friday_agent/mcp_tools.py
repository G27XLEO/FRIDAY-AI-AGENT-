from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import os
import platform
import shlex
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("friday_agent.mcp_tools")

WORKSPACE_ROOT = Path(os.getenv("FRIDAY_WORKSPACE_ROOT", Path.cwd())).resolve()
MEMORY_PATH = Path(os.getenv("FRIDAY_MEMORY_PATH", WORKSPACE_ROOT / ".run" / "memory.json")).resolve()
MAX_TEXT_CHARS = int(os.getenv("FRIDAY_MAX_TEXT_CHARS", "12000"))
MAX_WRITE_BYTES = int(os.getenv("FRIDAY_MAX_WRITE_BYTES", "1000000"))
HTTP_MAX_CONNECTIONS = int(os.getenv("FRIDAY_HTTP_MAX_CONNECTIONS", "32"))
HTTP_MAX_KEEPALIVE = int(os.getenv("FRIDAY_HTTP_MAX_KEEPALIVE", "16"))
HTTP_TIMEOUT = float(os.getenv("FRIDAY_HTTP_TIMEOUT", "8"))
ALLOWED_URL_SCHEMES = {"http", "https"}

DEFAULT_ALLOWED_COMMANDS = {
    "cat", "head", "tail", "python", "python3", "pwd", "rg", "sed", "git",
}

_http_client: httpx.AsyncClient | None = None
_http_lock = asyncio.Lock()


async def _http() -> httpx.AsyncClient:
    """Reuse one pooled async client so MCP URL calls avoid TCP/TLS setup per request."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        async with _http_lock:
            if _http_client is None or _http_client.is_closed:
                _http_client = httpx.AsyncClient(
                    timeout=HTTP_TIMEOUT,
                    follow_redirects=True,
                    limits=httpx.Limits(
                        max_connections=HTTP_MAX_CONNECTIONS,
                        max_keepalive_connections=HTTP_MAX_KEEPALIVE,
                    ),
                    headers={"User-Agent": "FRIDAY-MCP/1.0"},
                )
    return _http_client


async def close_http() -> None:
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def _allowed_commands() -> set[str]:
    configured = os.getenv("FRIDAY_ALLOWED_COMMANDS", "")
    commands = {command for chunk in configured.split(",") for command in chunk.split() if command}
    return commands or DEFAULT_ALLOWED_COMMANDS


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    content: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clip(text: str, max_chars: int = MAX_TEXT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n...[clipped {len(text) - max_chars} chars]"


def _resolve_workspace_path(path: str) -> Path:
    candidate = (WORKSPACE_ROOT / path).resolve()
    if candidate != WORKSPACE_ROOT and WORKSPACE_ROOT not in candidate.parents:
        raise ValueError(f"Path escapes workspace: {path}")
    return candidate


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_URL_SCHEMES or not parsed.netloc:
        raise ValueError("Only absolute http:// and https:// URLs are allowed")


def _load_memory() -> dict[str, Any]:
    if not MEMORY_PATH.exists():
        return {}
    try:
        return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("Memory file at %s is unreadable; starting empty.", MEMORY_PATH)
        return {}


def _save_memory(memory: dict[str, Any]) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = MEMORY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(memory, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(MEMORY_PATH)


def system_status() -> dict[str, Any]:
    return {
        "ok": True,
        "utc": dt.datetime.now(dt.UTC).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "workspace_root": str(WORKSPACE_ROOT),
        "memory_path": str(MEMORY_PATH),
        "mcp": {"transport": "streamable-http", "server": "friday-custom-mcp"},
    }


async def fetch_url(url: str, timeout_seconds: float = HTTP_TIMEOUT) -> ToolResult:
    try:
        _validate_url(url)
        client = await _http()
        response = await client.get(url, timeout=timeout_seconds)
        response.raise_for_status()
        return ToolResult(True, _clip(response.text), {
            "url": str(response.url),
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type", ""),
        })
    except ValueError as exc:
        return ToolResult(False, str(exc), {"url": url})
    except httpx.TimeoutException:
        return ToolResult(False, f"Request timed out after {timeout_seconds}s", {"url": url})
    except httpx.HTTPStatusError as exc:
        return ToolResult(False, f"HTTP {exc.response.status_code}", {
            "url": url, "status_code": exc.response.status_code,
        })
    except httpx.RequestError as exc:
        return ToolResult(False, f"Request failed: {exc}", {"url": url})


async def run_shell(command: str, timeout_seconds: float = 30.0) -> ToolResult:
    parts = shlex.split(command)
    if not parts:
        return ToolResult(False, "No command supplied", {"command": command})
    allowed = _allowed_commands()
    if parts[0] not in allowed:
        return ToolResult(False, f"Command '{parts[0]}' is not allow-listed.", {
            "command": command, "allowed": sorted(allowed),
        })
    process = await asyncio.create_subprocess_exec(
        *parts, cwd=WORKSPACE_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout_seconds)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return ToolResult(False, f"Command timed out after {timeout_seconds} seconds", {"command": command})
    return ToolResult(process.returncode == 0, _clip(stdout.decode(errors="replace")), {
        "command": command, "returncode": process.returncode,
    })


def read_workspace_file(path: str) -> ToolResult:
    try:
        target = _resolve_workspace_path(path)
        if not target.exists():
            return ToolResult(False, f"File not found: {path}", {"path": str(target)})
        if target.is_dir():
            return ToolResult(False, f"Path is a directory: {path}", {"path": str(target)})
        return ToolResult(True, _clip(target.read_text(encoding="utf-8")), {"path": str(target)})
    except (ValueError, UnicodeDecodeError, OSError) as exc:
        return ToolResult(False, f"Failed to read {path}: {exc}", {"path": path})


def write_workspace_file(path: str, content: str, overwrite: bool = False) -> ToolResult:
    try:
        target = _resolve_workspace_path(path)
        encoded_len = len(content.encode("utf-8"))
        if encoded_len > MAX_WRITE_BYTES:
            return ToolResult(False, f"Content exceeds {MAX_WRITE_BYTES} bytes", {"path": str(target)})
        if target.exists() and not overwrite:
            return ToolResult(False, "File already exists; pass overwrite=true", {"path": str(target)})
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return ToolResult(True, f"Wrote {len(content)} characters", {"path": str(target)})
    except (ValueError, OSError) as exc:
        return ToolResult(False, f"Failed to write {path}: {exc}", {"path": path})


def list_workspace_files(path: str = ".", max_entries: int = 200) -> ToolResult:
    try:
        target = _resolve_workspace_path(path)
        if not target.exists() or not target.is_dir():
            return ToolResult(False, f"Directory not found: {path}", {"path": str(target)})
        entries = []
        for entry in sorted(target.iterdir()):
            entries.append(f"{'d' if entry.is_dir() else 'f'} {entry.relative_to(WORKSPACE_ROOT)}")
            if len(entries) >= max_entries:
                entries.append(f"...[truncated at {max_entries}]")
                break
        return ToolResult(True, "\n".join(entries) if entries else "(empty)", {"path": str(target)})
    except (ValueError, OSError) as exc:
        return ToolResult(False, f"Failed to list {path}: {exc}", {"path": path})


def remember(key: str, value: Any) -> ToolResult:
    memory = _load_memory()
    memory[key] = {"value": value, "updated_at": dt.datetime.now(dt.UTC).isoformat()}
    _save_memory(memory)
    return ToolResult(True, f"Remembered '{key}'", {"key": key})


def recall(key: str | None = None) -> ToolResult:
    memory = _load_memory()
    return ToolResult(True, json.dumps(memory.get(key, {}) if key else memory, indent=2, sort_keys=True), {"key": key})


def plan_task(goal: str, constraints: list[str] | None = None) -> ToolResult:
    steps = [
        "Confirm objective and success criteria",
        "Inspect context and available tools",
        "Execute the highest-impact action first",
        "Validate the result with a runnable check",
        "Summarize outcome, risks, and next steps",
    ]
    return ToolResult(True, json.dumps({"goal": goal, "constraints": constraints or [], "steps": steps}, indent=2), {})

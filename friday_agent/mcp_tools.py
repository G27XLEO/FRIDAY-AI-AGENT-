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


logger = logging.getLogger("friday_agent.mcp_tools")

WORKSPACE_ROOT = Path(os.getenv("FRIDAY_WORKSPACE_ROOT", Path.cwd())).resolve()
MEMORY_PATH = Path(os.getenv("FRIDAY_MEMORY_PATH", WORKSPACE_ROOT / ".run" / "memory.json")).resolve()
MAX_TEXT_CHARS = int(os.getenv("FRIDAY_MAX_TEXT_CHARS", "12000"))
MAX_WRITE_BYTES = int(os.getenv("FRIDAY_MAX_WRITE_BYTES", "1000000"))
DEFAULT_ALLOWED_COMMANDS = {
    "cat",
    "head",
    "tail",
    "python",
    "python3",
    "pwd",
    "rg",
    "sed",
    "git",
}


def _allowed_commands() -> set[str]:
    """Return shell command allow-list from comma or whitespace separated env values."""
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


def _load_memory() -> dict[str, Any]:
    if not MEMORY_PATH.exists():
        return {}
    try:
        return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Memory file at %s is corrupt; starting from empty memory.", MEMORY_PATH)
        return {}


def _save_memory(memory: dict[str, Any]) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_PATH.write_text(json.dumps(memory, indent=2, sort_keys=True), encoding="utf-8")


def system_status() -> dict[str, Any]:
    """Return local runtime status for realtime orchestration."""
    return {
        "utc": dt.datetime.now(dt.UTC).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "workspace_root": str(WORKSPACE_ROOT),
        "memory_path": str(MEMORY_PATH),
    }


async def fetch_url(url: str, timeout_seconds: float = 10.0) -> ToolResult:
    """Fetch a public URL and return clipped text for live context."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return ToolResult(
                ok=True,
                content=_clip(response.text),
                metadata={"url": str(response.url), "status_code": response.status_code},
            )
    except httpx.TimeoutException:
        return ToolResult(False, f"Request to {url} timed out after {timeout_seconds}s", {"url": url})
    except httpx.HTTPStatusError as exc:
        return ToolResult(
            False,
            f"Request to {url} failed with status {exc.response.status_code}",
            {"url": url, "status_code": exc.response.status_code},
        )
    except httpx.RequestError as exc:
        return ToolResult(False, f"Request to {url} failed: {exc}", {"url": url})


async def run_shell(command: str, timeout_seconds: float = 30.0) -> ToolResult:
    """Run an allow-listed command in the workspace and return bounded output."""
    parts = shlex.split(command)
    if not parts:
        return ToolResult(False, "No command supplied", {"command": command})
    allowed = _allowed_commands()
    if parts[0] not in allowed:
        return ToolResult(
            False,
            f"Command '{parts[0]}' is not allow-listed. Set FRIDAY_ALLOWED_COMMANDS to override.",
            {"command": command, "allowed": sorted(allowed)},
        )

    process = await asyncio.create_subprocess_exec(
        *parts,
        cwd=WORKSPACE_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout_seconds)
    except asyncio.TimeoutError:
        process.kill()
        return ToolResult(False, f"Command timed out after {timeout_seconds} seconds", {"command": command})

    return ToolResult(
        ok=process.returncode == 0,
        content=_clip(stdout.decode(errors="replace")),
        metadata={"command": command, "returncode": process.returncode},
    )


def read_workspace_file(path: str) -> ToolResult:
    """Read a UTF-8 workspace file without allowing path traversal."""
    try:
        target = _resolve_workspace_path(path)
    except ValueError as exc:
        return ToolResult(False, str(exc), {"path": path})

    if not target.exists():
        return ToolResult(False, f"File not found: {path}", {"path": str(target)})
    if target.is_dir():
        return ToolResult(False, f"Path is a directory, not a file: {path}", {"path": str(target)})

    try:
        return ToolResult(True, _clip(target.read_text(encoding="utf-8")), {"path": str(target)})
    except UnicodeDecodeError:
        return ToolResult(False, f"File is not valid UTF-8 text: {path}", {"path": str(target)})
    except OSError as exc:
        return ToolResult(False, f"Failed to read {path}: {exc}", {"path": str(target)})


def write_workspace_file(path: str, content: str, overwrite: bool = False) -> ToolResult:
    """Write a UTF-8 workspace file, creating parents, with overwrite protection."""
    try:
        target = _resolve_workspace_path(path)
    except ValueError as exc:
        return ToolResult(False, str(exc), {"path": path})

    encoded_len = len(content.encode("utf-8"))
    if encoded_len > MAX_WRITE_BYTES:
        return ToolResult(
            False,
            f"Content is {encoded_len} bytes, exceeding the {MAX_WRITE_BYTES}-byte write limit",
            {"path": str(target)},
        )
    if target.exists() and not overwrite:
        return ToolResult(False, "File already exists; pass overwrite=true to replace it", {"path": str(target)})

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        return ToolResult(False, f"Failed to write {path}: {exc}", {"path": str(target)})

    return ToolResult(True, f"Wrote {len(content)} characters", {"path": str(target)})


def list_workspace_files(path: str = ".", max_entries: int = 200) -> ToolResult:
    """List files and directories under a workspace-relative path."""
    try:
        target = _resolve_workspace_path(path)
    except ValueError as exc:
        return ToolResult(False, str(exc), {"path": path})

    if not target.exists():
        return ToolResult(False, f"Path not found: {path}", {"path": str(target)})
    if not target.is_dir():
        return ToolResult(False, f"Path is not a directory: {path}", {"path": str(target)})

    entries = []
    for entry in sorted(target.iterdir()):
        entries.append(f"{'d' if entry.is_dir() else 'f'} {entry.relative_to(WORKSPACE_ROOT)}")
        if len(entries) >= max_entries:
            entries.append(f"...[truncated at {max_entries} entries]")
            break

    return ToolResult(True, "\n".join(entries) if entries else "(empty)", {"path": str(target)})


def remember(key: str, value: Any) -> ToolResult:
    """Persist a small JSON-serializable memory item."""
    memory = _load_memory()
    memory[key] = {"value": value, "updated_at": dt.datetime.now(dt.UTC).isoformat()}
    _save_memory(memory)
    return ToolResult(True, f"Remembered '{key}'", {"key": key})


def recall(key: str | None = None) -> ToolResult:
    """Recall one memory item or all stored memory."""
    memory = _load_memory()
    payload = memory.get(key, {}) if key else memory
    return ToolResult(True, json.dumps(payload, indent=2, sort_keys=True), {"key": key})


def plan_task(goal: str, constraints: list[str] | None = None) -> ToolResult:
    """Create a compact execution plan for a user goal."""
    constraints = constraints or []
    steps = [
        "Confirm objective and success criteria",
        "Inspect available context and tools",
        "Execute the highest-impact action first",
        "Validate result with a runnable check",
        "Summarize outcome, risks, and next steps",
    ]
    return ToolResult(True, json.dumps({"goal": goal, "constraints": constraints, "steps": steps}, indent=2), {})

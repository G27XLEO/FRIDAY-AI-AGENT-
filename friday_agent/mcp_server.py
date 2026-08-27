from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from friday_agent import mcp_tools

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("friday_agent.mcp_server")

mcp = FastMCP(
    "friday-custom-mcp",
    instructions=(
        "Custom FRIDAY MCP server for realtime agent orchestration. "
        "Use these tools to inspect runtime state, read/write trusted workspace files, "
        "fetch user-approved public URLs, execute allow-listed local commands, remember facts, "
        "and produce compact plans."
    ),
)


@mcp.resource("friday://status")
def status_resource() -> dict[str, Any]:
    """Expose current FRIDAY server status as a resource."""
    return mcp_tools.system_status()


@mcp.prompt()
def friday_operator_prompt(mission: str) -> str:
    """Generate the standard operator prompt for a mission."""
    return (
        "You are FRIDAY, the operator's realtime mission-control AI. "
        "Answer with calm precision, state assumptions, use tools when useful, "
        f"and complete this mission: {mission}"
    )


@mcp.tool()
def system_status() -> dict[str, Any]:
    """Return local runtime status for orchestration decisions."""
    return mcp_tools.system_status()


@mcp.tool()
async def fetch_url(url: str, timeout_seconds: float = 10.0) -> dict[str, Any]:
    """Fetch a public URL and return bounded text content."""
    return (await mcp_tools.fetch_url(url, timeout_seconds)).to_dict()


@mcp.tool()
async def run_shell(command: str, timeout_seconds: float = 30.0) -> dict[str, Any]:
    """Run an allow-listed command in the workspace and return bounded output."""
    return (await mcp_tools.run_shell(command, timeout_seconds)).to_dict()


@mcp.tool()
def read_workspace_file(path: str) -> dict[str, Any]:
    """Read a UTF-8 file under the configured workspace root."""
    return mcp_tools.read_workspace_file(path).to_dict()


@mcp.tool()
def write_workspace_file(path: str, content: str, overwrite: bool = False) -> dict[str, Any]:
    """Write a UTF-8 file under the configured workspace root."""
    return mcp_tools.write_workspace_file(path, content, overwrite).to_dict()


@mcp.tool()
def list_workspace_files(path: str = ".", max_entries: int = 200) -> dict[str, Any]:
    """List files and directories under a workspace-relative path."""
    return mcp_tools.list_workspace_files(path, max_entries).to_dict()


@mcp.tool()
def remember(key: str, value: Any) -> dict[str, Any]:
    """Persist a JSON-serializable memory item for later recall."""
    return mcp_tools.remember(key, value).to_dict()


@mcp.tool()
def recall(key: str | None = None) -> dict[str, Any]:
    """Recall one memory item or all memory."""
    return mcp_tools.recall(key).to_dict()


@mcp.tool()
def plan_task(goal: str, constraints: list[str] | None = None) -> dict[str, Any]:
    """Create a compact execution plan for a user goal."""
    return mcp_tools.plan_task(goal, constraints).to_dict()


if __name__ == "__main__":
    logger.info("Starting FRIDAY MCP server (workspace root: %s)", mcp_tools.WORKSPACE_ROOT)
    mcp.run(transport="streamable-http")

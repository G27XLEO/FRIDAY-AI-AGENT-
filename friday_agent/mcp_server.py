from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from friday_agent import mcp_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("friday_agent.mcp_server")

mcp = FastMCP(
    "friday-custom-mcp",
    instructions=(
        "FRIDAY capability server. Use tools for runtime status, trusted workspace "
        "operations, public URL retrieval, allow-listed commands, memory, planning, "
        "and live information feeds."
    ),
)


@mcp.resource("friday://status")
def status_resource() -> dict[str, Any]:
    return mcp_tools.system_status()


@mcp.prompt()
def friday_operator_prompt(mission: str) -> str:
    return (
        "You are FRIDAY, the operator's realtime mission-control AI. "
        "Address the operator as boss. Be concise, precise, proactive, and calm. "
        f"Mission: {mission}"
    )


@mcp.tool()
def system_status() -> dict[str, Any]:
    return mcp_tools.system_status()


@mcp.tool()
async def fetch_url(url: str, timeout_seconds: float = 10.0) -> dict[str, Any]:
    return (await mcp_tools.fetch_url(url, timeout_seconds)).to_dict()


@mcp.tool()
async def get_world_news() -> dict[str, Any]:
    return (await mcp_tools.get_world_news()).to_dict()


@mcp.tool()
async def get_world_finance_news() -> dict[str, Any]:
    return (await mcp_tools.get_world_finance_news()).to_dict()


@mcp.tool()
async def run_shell(command: str, timeout_seconds: float = 30.0) -> dict[str, Any]:
    return (await mcp_tools.run_shell(command, timeout_seconds)).to_dict()


@mcp.tool()
def read_workspace_file(path: str) -> dict[str, Any]:
    return mcp_tools.read_workspace_file(path).to_dict()


@mcp.tool()
def write_workspace_file(
    path: str, content: str, overwrite: bool = False
) -> dict[str, Any]:
    return mcp_tools.write_workspace_file(path, content, overwrite).to_dict()


@mcp.tool()
def list_workspace_files(path: str = ".", max_entries: int = 200) -> dict[str, Any]:
    return mcp_tools.list_workspace_files(path, max_entries).to_dict()


@mcp.tool()
def remember(key: str, value: Any) -> dict[str, Any]:
    return mcp_tools.remember(key, value).to_dict()


@mcp.tool()
def recall(key: str | None = None) -> dict[str, Any]:
    return mcp_tools.recall(key).to_dict()


@mcp.tool()
def plan_task(goal: str, constraints: list[str] | None = None) -> dict[str, Any]:
    return mcp_tools.plan_task(goal, constraints).to_dict()


if __name__ == "__main__":
    logger.info("Starting FRIDAY MCP at http://127.0.0.1:8000/mcp")
    mcp.run(transport="streamable-http")

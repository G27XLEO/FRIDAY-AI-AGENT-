from __future__ import annotations

import json
import logging
from typing import Any

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli, mcp
from livekit.plugins import elevenlabs, groq, silero, turn_detector

from friday_agent.config import config
from friday_agent.nlp import build_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("friday_agent.livekit_agent")


async def _mcp_result_resolver(ctx: mcp.MCPToolResultContext) -> str:
    """Keep MCP output compact so voice turns stay fast and context stays bounded."""
    try:
        if len(ctx.result.content) == 1:
            item = ctx.result.content[0]
            text = item.model_dump_json() if hasattr(item, "model_dump_json") else str(item)
        else:
            items = [
                item.model_dump() if hasattr(item, "model_dump") else str(item)
                for item in ctx.result.content
            ]
            text = json.dumps(items, ensure_ascii=False)
    except Exception:
        text = str(ctx.result.content)

    if len(text) > config.max_tool_result_chars:
        return text[: config.max_tool_result_chars] + "\n... [FRIDAY result truncated]"
    return text


def build_mcp_toolset() -> mcp.MCPToolset | None:
    """Build the optional FRIDAY MCP toolset from environment configuration."""
    if not config.mcp_url:
        logger.info("FRIDAY MCP is disabled: FRIDAY_MCP_URL is not configured")
        return None

    headers: dict[str, str] = {}
    if config.mcp_auth_token:
        headers["Authorization"] = f"Bearer {config.mcp_auth_token}"

    return mcp.MCPToolset(
        id="friday-mcp",
        mcp_server=mcp.MCPServerHTTP(
            config.mcp_url,
            headers=headers or None,
            transport_type="streamable_http",
            client_session_timeout_seconds=config.mcp_timeout_seconds,
            tool_result_resolver=_mcp_result_resolver,
        ),
    )


class FridayAgent(Agent):
    def __init__(self) -> None:
        tools: list[Any] = []
        mcp_toolset = build_mcp_toolset()
        if mcp_toolset is not None:
            tools.append(mcp_toolset)

        super().__init__(
            instructions=config.instructions,
            tools=tools,
        )

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        """Inject fast deterministic NLP context before the LLM reasons about a turn."""
        text = ""
        for content in getattr(new_message, "content", []):
            if isinstance(content, str):
                text += content + " "
        text = text.strip()

        if text:
            turn_ctx.add_message(role="system", content=build_context(text))

        await super().on_user_turn_completed(turn_ctx, new_message)


async def entrypoint(ctx: JobContext) -> None:
    """Run FRIDAY as a realtime Groq + ElevenLabs voice agent with MCP tools."""
    if not config.elevenlabs_voice_id:
        logger.warning(
            "No ElevenLabs voice configured (ELEVENLABS_VOICE_LINK/ELEVENLABS_VOICE_ID unset); "
            "falling back to the plugin default voice."
        )

    await ctx.connect()
    logger.info("Connected to room '%s' as identity '%s'", ctx.room.name, config.identity)

    session = AgentSession(
        stt=groq.STT(model=config.groq_stt_model),
        llm=groq.LLM(model=config.groq_llm_model),
        tts=elevenlabs.TTS(voice_id=config.elevenlabs_voice_id or None),
        vad=silero.VAD.load(),
        turn_detection=turn_detector.EOUModel(),
        max_tool_steps=config.max_tool_steps,
    )

    try:
        await session.start(agent=FridayAgent(), room=ctx.room)
        await session.generate_reply(
            instructions=(
                "Greet the operator briefly. State that FRIDAY realtime systems are online "
                "and that software tools are ready when configured. Do not list capabilities unless asked."
            )
        )
    except Exception:
        logger.exception("FRIDAY session failed to start in room '%s'", ctx.room.name)
        raise


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name=config.identity))

"""Realtime FRIDAY voice worker with bounded, observable mission tools."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import PurePosixPath

from livekit.agents import Agent, AgentSession, JobContext, JobProcess, RunContext, WorkerOptions, cli, function_tool, inference
from livekit.plugins import elevenlabs, groq, silero

from friday_agent.config import config
from friday_agent.doctor import require_voice_configuration
from friday_agent import mcp_tools
from friday_agent.mission_control import MissionControl
from friday_agent.nlp import analyze

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("friday_agent.livekit_agent")


def permitted_document(path: str) -> bool:
    """Expose only clearly public project text to the voice model."""
    if not isinstance(path, str) or not path or "\\" in path:
        return False
    parts = PurePosixPath(path).parts
    if ".." in parts or any(part.startswith(".") for part in parts):
        return False
    return path == "README.md" or (
        len(parts) >= 2
        and parts[0] in ("docs", "tests", "friday_agent")
        and parts[-1].endswith((".md", ".py", ".txt"))
    )


class FridayAgent(Agent):
    def __init__(self) -> None:
        self.missions = MissionControl()
        super().__init__(instructions=(
            config.instructions
            + "\nMISSION RULES: For complex tasks define an outcome, measurable success "
            "criteria and no more than eight steps. Use your mission tools to track "
            "progress. Distinguish reported results from independently verified "
            "results. Never claim a tool ran without receiving tool output. "
            "Never claim a reported step is verified. Ask the operator before "
            "destructive, paid, external, or irreversible actions; these actions "
            "are not accessible from this voice worker. If work cannot be "
            "completed with available tools, say what is blocked."
        ))

    @function_tool()
    async def runtime_status(self, context: RunContext) -> str:
        """Get the local public runtime status, without credentials."""
        info = mcp_tools.system_status()
        return json.dumps({key: info[key] for key in ("utc", "platform", "python")})

    @function_tool()
    async def read_project_document(self, context: RunContext, path: str) -> str:
        """Read public README, docs, tests or source text for reasoning.

        Args:
            path: Project-relative public text path, for example README.md.
        """
        if not permitted_document(path):
            return json.dumps({"error": "Document path not allowed"})
        return json.dumps(mcp_tools.read_workspace_file(path).to_dict())

    @function_tool()
    async def create_mission(
        self, context: RunContext, goal: str, steps_json: str, success_criteria: str
    ) -> str:
        """Start a bounded plan for an operator goal.

        Args:
            goal: User's objective.
            steps_json: JSON array with 1 to 8 short ordered steps.
            success_criteria: Concrete, observable acceptance criteria.
        """
        try:
            steps = json.loads(steps_json)
            return json.dumps(self.missions.create(goal, steps, success_criteria))
        except (ValueError, TypeError) as exc:
            return json.dumps({"error": str(exc)})

    @function_tool()
    async def mission_status(self, context: RunContext, mission_id: str) -> str:
        """Read the true stored status of a mission.

        Args:
            mission_id: ID provided by create_mission.
        """
        try:
            return json.dumps(self.missions.status(mission_id))
        except ValueError as exc:
            return json.dumps({"error": str(exc)})

    @function_tool()
    async def report_mission_step(
        self, context: RunContext, mission_id: str, step_number: int,
        evidence: str, passed: bool
    ) -> str:
        """Record observed progress. Reports are not independent verification.

        Args:
            mission_id: ID provided by create_mission.
            step_number: One-based active step index.
            evidence: What was actually observed in a tool response.
            passed: Whether the active step appeared to succeed.
        """
        try:
            return json.dumps(self.missions.report(mission_id, step_number, evidence, passed))
        except ValueError as exc:
            return json.dumps({"error": str(exc)})

    @function_tool()
    async def verify_document_step(
        self, context: RunContext, mission_id: str, step_number: int,
        path: str, expected_text: str
    ) -> str:
        """Verify a reported step by checking a non-secret project file.

        Args:
            mission_id: ID provided by create_mission.
            step_number: One-based reported step index.
            path: Public project document to check.
            expected_text: Nonempty text that must appear in that document.
        """
        if not permitted_document(path):
            return json.dumps({"error": "Document path not allowed"})
        try:
            return json.dumps(self.missions.verify_file(mission_id, step_number, path, expected_text))
        except ValueError as exc:
            return json.dumps({"error": str(exc)})

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        """Inject compact, untrusted NLP hints without changing operator text."""
        text = " ".join(
            content for content in getattr(new_message, "content", [])
            if isinstance(content, str)
        ).strip()
        if text:
            signals = analyze(text[:1200])
            turn_ctx.add_message(
                role="assistant",
                content=(f"Non-authoritative intent signal: {signals.intent}; "
                         f"urgency: {signals.urgency}."),
            )
        await super().on_user_turn_completed(turn_ctx, new_message)


def prewarm(proc: JobProcess) -> None:
    """Load VAD once per worker process instead of during the first user turn."""
    proc.userdata["vad"] = silero.VAD.load()


def create_session(vad) -> AgentSession:
    """Use direct provider keys and local turn detection (no inference gateway)."""
    # LiveKit's plugin otherwise reads ELEVEN_API_KEY, while FRIDAY documents
    # ELEVENLABS_API_KEY. Pass the repository's public configuration explicitly.
    tts_options = {"model": config.elevenlabs_model, "api_key": os.environ["ELEVENLABS_API_KEY"]}
    # Passing None is not the plugin default: omit voice_id when not selected.
    if config.elevenlabs_voice_id:
        tts_options["voice_id"] = config.elevenlabs_voice_id
    return AgentSession(
        stt=groq.STT(model=config.groq_stt_model),
        llm=groq.LLM(model=config.groq_llm_model),
        tts=elevenlabs.TTS(**tts_options),
        vad=vad,
        turn_handling={"turn_detection": inference.TurnDetector(version="v1-mini")},
    )


async def close_session(session: AgentSession) -> None:
    """Close provider clients even when the session failed before start()."""
    try:
        await session.aclose()
    finally:
        await asyncio.gather(*(provider.aclose() for provider in (
            session.stt, session.llm, session.tts
        ) if provider is not None))


async def entrypoint(ctx: JobContext) -> None:
    """Connect to LiveKit and serve a voice session."""
    if not config.elevenlabs_voice_id:
        logger.warning("No ElevenLabs voice selected; using plugin default.")
    await ctx.connect()
    logger.info("Connected to LiveKit room '%s'", ctx.room.name)
    session = create_session(ctx.proc.userdata["vad"])

    async def shutdown() -> None:
        await close_session(session)

    ctx.add_shutdown_callback(shutdown)
    try:
        await session.start(agent=FridayAgent(), room=ctx.room)
        await session.generate_reply(
            instructions="Greet the operator briefly. Explain that planning and "
            "read-only evidence checks are available, without claiming untested capabilities."
        )
    except Exception:
        logger.exception("FRIDAY voice session failed to start")
        raise


if __name__ == "__main__":
    # Downloads and CLI help must work before credentials are configured.
    if len(sys.argv) > 1 and sys.argv[1] in {"start", "dev", "connect", "console"} and not any(
        flag in sys.argv for flag in ("--help", "-h")
    ):
        try:
            require_voice_configuration(console=sys.argv[1] == "console")
        except ValueError as exc:
            raise SystemExit(str(exc)) from None
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name=config.identity))

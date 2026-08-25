from __future__ import annotations

import logging

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import elevenlabs, groq, silero, turn_detector

from friday_agent.config import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("friday_agent.livekit_agent")


class FridayAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=config.instructions)


async def entrypoint(ctx: JobContext) -> None:
    """Join a LiveKit room and run FRIDAY as a Groq + ElevenLabs voice participant."""
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
    )

    try:
        await session.start(agent=FridayAgent(), room=ctx.room)
        await session.generate_reply(
            instructions="Greet the operator briefly and report that realtime FRIDAY systems are online."
        )
    except Exception:
        logger.exception("FRIDAY session failed to start in room '%s'", ctx.room.name)
        raise


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name=config.identity))

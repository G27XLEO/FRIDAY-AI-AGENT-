from __future__ import annotations

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import elevenlabs, groq, openai, silero, turn_detector

from friday_agent.config import config


class FridayAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=config.instructions)


def _llm():
    """Create the LLM, using OmniRoute when enabled and configured."""
    if config.use_omniroute:
        return openai.LLM(
            model=config.omniroute_model,
            base_url=config.omniroute_base_url,
            api_key=config.omniroute_api_key or "sk-omniroute",
        )

    return groq.LLM(model=config.groq_llm_model)


async def entrypoint(ctx: JobContext) -> None:
    """Join a LiveKit room and run FRIDAY with OmniRoute + Groq STT + ElevenLabs TTS."""
    await ctx.connect()

    session = AgentSession(
        stt=groq.STT(model=config.groq_stt_model),
        llm=_llm(),
        tts=elevenlabs.TTS(voice_id=config.elevenlabs_voice_id or None),
        vad=silero.VAD.load(),
        turn_detection=turn_detector.EOUModel(),
    )

    await session.start(agent=FridayAgent(), room=ctx.room)
    await session.generate_reply(
        instructions="Greet the operator briefly and report that realtime FRIDAY systems are online."
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name=config.identity))

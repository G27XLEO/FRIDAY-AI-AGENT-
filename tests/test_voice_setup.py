"""No network or paid calls: exercise configuration and real SDK construction."""
from __future__ import annotations

from dataclasses import replace
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from friday_agent.config import FridayConfig
from friday_agent.doctor import configuration_errors, require_voice_configuration


class VoiceConfigurationTests(unittest.TestCase):
    def test_service_modules_import_with_installed_dependencies(self):
        import friday_agent.mcp_server
        import friday_agent.web_server

    def setUp(self):
        self.env = {
            "LIVEKIT_URL": "wss://test.livekit.cloud",
            "LIVEKIT_API_KEY": "test-key", "LIVEKIT_API_SECRET": "test-secret",
            "GROQ_API_KEY": "test-groq", "ELEVENLABS_API_KEY": "test-eleven",
        }

    def test_complete_configuration_and_default_voice(self):
        self.assertEqual(configuration_errors(self.env), [])

    def test_example_is_rejected_without_leaking_values(self):
        from dotenv import dotenv_values
        template = dotenv_values(Path(__file__).resolve().parents[1] / ".env.example")
        errors = configuration_errors(template)
        for name in self.env:
            self.assertTrue(any(name in error for error in errors), name)
        self.env["GROQ_API_KEY"] = ""
        with patch.dict(os.environ, self.env, clear=True):
            with self.assertRaises(ValueError) as caught:
                require_voice_configuration()
        self.assertIn("GROQ_API_KEY", str(caught.exception))
        self.assertNotIn("test-secret", str(caught.exception))

    def test_bad_livekit_urls(self):
        for url in ("https://test.livekit.cloud", "wss://", "wss://your-project.livekit.cloud",
                    "wss://host:invalid", "wss://host:0", "wss://user:secret@host", "wss://[invalid"):
            with self.subTest(url=url):
                self.assertTrue(configuration_errors({**self.env, "LIVEKIT_URL": url}))

    def test_console_needs_providers_but_not_livekit_cloud(self):
        env = {key: value for key, value in self.env.items() if not key.startswith("LIVEKIT_")}
        self.assertEqual(configuration_errors(env, console=True), [])
        self.assertTrue(configuration_errors(env))
        del env["ELEVENLABS_API_KEY"]
        self.assertTrue(configuration_errors(env, console=True))

    def test_invalid_voice_and_empty_models_rejected(self):
        for value in ("your_voice_id", "https://example.com/unrecognized", "bad voice", "https://[bad"):
            self.assertTrue(configuration_errors({**self.env, "ELEVENLABS_VOICE_ID": value}))
        self.assertTrue(configuration_errors({**self.env, "GROQ_LLM_MODEL": " "}))

    def test_settings_read_current_environment_and_empty_link_falls_back(self):
        with patch.dict(os.environ, {"FRIDAY_IDENTITY": "new-agent", "ELEVENLABS_VOICE_LINK": " ",
                                     "ELEVENLABS_VOICE_ID": "abc123"}):
            settings = FridayConfig()
        self.assertEqual(settings.identity, "new-agent")
        self.assertEqual(settings.elevenlabs_voice_id, "abc123")

    def test_dotenv_loads_only_checkout_file_and_preserves_environment(self):
        # A separate temporary checkout avoids touching the operator's .env.
        import sys
        source = Path(__file__).resolve().parents[1] / "friday_agent/config.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "friday_agent"
            package.mkdir()
            (package / "config.py").write_text(source.read_text())
            (root / ".env").write_text("FRIDAY_IDENTITY=from-file\nGROQ_LLM_MODEL=file-model\n")
            spec = importlib.util.spec_from_file_location("isolated_friday_config", package / "config.py")
            module = importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules, {spec.name: module}), patch.dict(os.environ, {"GROQ_LLM_MODEL": "deployed-model"}, clear=True):
                spec.loader.exec_module(module)
                self.assertEqual(module.config.identity, "from-file")
                self.assertEqual(module.config.groq_llm_model, "deployed-model")


class VoiceSDKTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_provider_construction_with_documented_keys_and_default_voice(self):
        from friday_agent import livekit_agent as worker
        from livekit.plugins import groq, elevenlabs, silero
        settings = replace(FridayConfig(), elevenlabs_voice="")
        # Explicitly omit ELEVEN_API_KEY: this catches the original plugin-key mismatch.
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-groq", "ELEVENLABS_API_KEY": "test-eleven"}, clear=True), patch.object(worker, "config", settings), patch.object(groq.LLM, "_prewarm_impl", new_callable=AsyncMock):
            session = worker.create_session(silero.VAD.load())
            try:
                self.assertIsInstance(session.stt, groq.STT)
                self.assertIsInstance(session.llm, groq.LLM)
                self.assertIsInstance(session.tts, elevenlabs.TTS)
                # The real TTS constructor accepts None; guard the resulting invalid voice.
                self.assertTrue(session.tts._opts.voice_id)
            finally:
                await worker.close_session(session)

    async def test_custom_voice_model_and_key_are_forwarded(self):
        from friday_agent import livekit_agent as worker
        settings = replace(FridayConfig(), elevenlabs_voice="chosenVoice", elevenlabs_model="eleven_multilingual_v2")
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-eleven"}), patch.object(worker, "config", settings), \
             patch.object(worker.groq, "STT"), patch.object(worker.groq, "LLM"), \
             patch.object(worker.elevenlabs, "TTS") as tts, patch.object(worker, "AgentSession"):
            worker.create_session(object())
        tts.assert_called_once_with(voice_id="chosenVoice", model="eleven_multilingual_v2", api_key="test-eleven")

    async def test_entrypoint_registers_cleanup_and_starts_session_before_greeting(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from friday_agent import livekit_agent as worker
        session = SimpleNamespace(start=AsyncMock(), generate_reply=AsyncMock(), aclose=AsyncMock())
        ctx = SimpleNamespace(connect=AsyncMock(), room=SimpleNamespace(name="test"),
                              proc=SimpleNamespace(userdata={"vad": object()}), add_shutdown_callback=Mock())
        calls = Mock()
        calls.attach_mock(session.start, "start")
        calls.attach_mock(session.generate_reply, "reply")
        with patch.object(worker, "create_session", return_value=session), patch.object(worker, "FridayAgent"):
            await worker.entrypoint(ctx)
        ctx.add_shutdown_callback.assert_called_once()
        with patch.object(worker, "close_session", new_callable=AsyncMock) as close:
            await ctx.add_shutdown_callback.call_args.args[0]()
        close.assert_awaited_once_with(session)
        self.assertEqual([call[0] for call in calls.mock_calls], ["start", "reply"])

    async def test_provider_clients_close_even_if_session_cleanup_fails(self):
        from types import SimpleNamespace
        from friday_agent.livekit_agent import close_session
        providers = [SimpleNamespace(aclose=AsyncMock()) for _ in range(3)]
        session = SimpleNamespace(aclose=AsyncMock(side_effect=RuntimeError("failed start")),
                                  stt=providers[0], llm=providers[1], tts=providers[2])
        with self.assertRaises(RuntimeError):
            await close_session(session)
        for provider in providers:
            provider.aclose.assert_awaited_once()

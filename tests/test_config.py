
import unittest

from friday_agent.config import _elevenlabs_voice_id


class ConfigTests(unittest.TestCase):
    def test_elevenlabs_voice_link_query_parses_voice_id(self):
        self.assertEqual(
            _elevenlabs_voice_id("https://elevenlabs.io/app/voice-library?voiceId=abc123"),
            "abc123",
        )

    def test_elevenlabs_raw_voice_id_passes_through(self):
        self.assertEqual(_elevenlabs_voice_id("abc123"), "abc123")

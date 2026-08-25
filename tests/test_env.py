import os
import unittest


class EnvironmentValidationTests(unittest.TestCase):
    """Validate required runtime environment variables without exposing secrets."""

    REQUIRED = (
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "GROQ_API_KEY",
        "ELEVENLABS_API_KEY",
    )

    def test_required_environment_variables_are_present(self):
        missing = [name for name in self.REQUIRED if not os.getenv(name)]
        self.assertEqual(
            missing,
            [],
            "Missing required environment variables: " + ", ".join(missing),
        )

    def test_livekit_url_is_configured(self):
        value = os.getenv("LIVEKIT_URL", "").strip()
        self.assertTrue(value, "LIVEKIT_URL must be set")
        self.assertTrue(
            value.startswith(("ws://", "wss://")),
            "LIVEKIT_URL must start with ws:// or wss://",
        )

    def test_secret_values_are_not_placeholder_values(self):
        placeholders = {"", "changeme", "your-api-key", "your-api-secret", "replace-me"}
        for name in self.REQUIRED[1:]:
            value = os.getenv(name, "").strip().lower()
            self.assertNotIn(
                value,
                placeholders,
                f"{name} is still using a placeholder value",
            )


if __name__ == "__main__":
    unittest.main()

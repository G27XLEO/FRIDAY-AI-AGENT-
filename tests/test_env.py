import os
import unittest


class EnvironmentValidationTests(unittest.TestCase):
    """Validate runtime environment variables when explicitly enabled."""

    REQUIRED = (
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "GROQ_API_KEY",
        "ELEVENLABS_API_KEY",
    )

    @classmethod
    def setUpClass(cls) -> None:
        if os.getenv("FRIDAY_VALIDATE_RUNTIME_ENV") != "1":
            raise unittest.SkipTest(
                "Runtime secret validation is enabled only for protected main-branch CI."
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
        placeholders = {
            "",
            "changeme",
            "your-api-key",
            "your-api-secret",
            "replace-me",
            "your_livekit_api_key_here",
            "your_livekit_api_secret_here",
            "your_groq_api_key_here",
            "your_elevenlabs_api_key_here",
        }
        for name in self.REQUIRED[1:]:
            value = os.getenv(name, "").strip().lower()
            self.assertNotIn(
                value,
                placeholders,
                f"{name} is still using a placeholder value",
            )


if __name__ == "__main__":
    unittest.main()

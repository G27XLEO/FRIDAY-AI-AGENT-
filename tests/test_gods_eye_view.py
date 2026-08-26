import os
import unittest
from unittest.mock import AsyncMock, patch

from friday_agent import gods_eye_view


class GodsEyeViewTests(unittest.IsolatedAsyncioTestCase):
    def test_manifest_is_stable_and_keyless_by_default(self):
        with patch.dict(os.environ, {}, clear=False):
            manifest = gods_eye_view.feature_manifest()
        self.assertEqual(manifest["name"], "God's Eye View")
        self.assertIn("photorealistic_3d_globe", manifest["capabilities"])
        self.assertIn("live_aircraft_and_military_contacts", manifest["capabilities"])
        self.assertEqual(len(manifest["source_sha256"]), 64)

    async def test_health_check_is_non_fatal_when_not_configured(self):
        with patch.object(gods_eye_view, "GODS_EYE_VIEW_URL", ""):
            result = await gods_eye_view.health_check()
        self.assertTrue(result.ok)
        self.assertFalse(result.metadata["configured"])

    async def test_health_check_uses_configured_endpoint(self):
        fake = gods_eye_view.ToolResult(True, "ok", {"status_code": 200})
        with patch.object(gods_eye_view, "GODS_EYE_VIEW_URL", "http://gev.test"), patch(
            "friday_agent.gods_eye_view.fetch_url", new=AsyncMock(return_value=fake)
        ) as fetch:
            result = await gods_eye_view.health_check(2.0)
        self.assertTrue(result.ok)
        fetch.assert_awaited_once_with("http://gev.test", 2.0)
        self.assertTrue(result.metadata["configured"])


if __name__ == "__main__":
    unittest.main()

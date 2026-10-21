from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path

from friday_agent.mission_control import MissionControl


class MissionControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = MissionControl()
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root_before = os.environ.get("FRIDAY_WORKSPACE_ROOT")
        os.environ["FRIDAY_WORKSPACE_ROOT"] = self.tempdir.name
        import friday_agent.mcp_tools as mcp_tools
        self.tools = importlib.reload(mcp_tools)
        self.addCleanup(self._restore_workspace)

    def _restore_workspace(self) -> None:
        if self.root_before is None:
            os.environ.pop("FRIDAY_WORKSPACE_ROOT", None)
        else:
            os.environ["FRIDAY_WORKSPACE_ROOT"] = self.root_before
        importlib.reload(self.tools)

    def mission(self) -> dict:
        return self.controller.create(
            "Document release", ["Inspect README", "Check documentation"],
            "Both documents contain the agreed launch marker"
        )

    def test_missions_start_with_one_active_step(self) -> None:
        mission = self.mission()
        self.assertEqual(mission["status"], "in_progress")
        self.assertEqual([s["status"] for s in mission["steps"]], ["active", "pending"])

    def test_unverified_reports_do_not_claim_success(self) -> None:
        mission = self.mission()
        output = self.controller.report(mission["id"], 1, "Model says done", True)
        self.assertEqual(output["steps"][0]["status"], "reported")
        self.assertEqual(output["status"], "in_progress")
        output = self.controller.report(mission["id"], 2, "Model says done", True)
        self.assertEqual(output["status"], "awaiting_verification")

    def test_immutable_verification_requires_file_contents(self) -> None:
        mission = self.mission()
        self.controller.report(mission["id"], 1, "README edited", True)
        self.assertTrue(self.tools.write_workspace_file("README.md", "release marker").ok)
        with self.assertRaisesRegex(ValueError, "verification failed"):
            self.controller.verify_file(mission["id"], 1, "README.md", "wrong marker")
        verified = self.controller.verify_file(mission["id"], 1, "README.md", "release marker")
        self.assertEqual(verified["steps"][0]["status"], "verified")
        self.assertNotEqual(verified["status"], "verified")

    def test_all_steps_must_be_verified_for_verified_mission(self) -> None:
        mission = self.mission()
        self.tools.write_workspace_file("README.md", "launch marker")
        self.tools.write_workspace_file("docs/launch.md", "launch marker")
        self.controller.report(mission["id"], 1, "README updated", True)
        self.controller.verify_file(mission["id"], 1, "README.md", "launch marker")
        self.controller.report(mission["id"], 2, "docs updated", True)
        result = self.controller.verify_file(mission["id"], 2, "docs/launch.md", "launch marker")
        self.assertEqual(result["status"], "verified")

    def test_failed_step_blocks_execution_and_can_be_retried(self) -> None:
        mission = self.mission()
        blocked = self.controller.report(mission["id"], 1, "Required file is absent", False)
        self.assertEqual(blocked["status"], "blocked")
        with self.assertRaisesRegex(ValueError, "active or blocked"):
            self.controller.report(mission["id"], 2, "skipped", True)
        result = self.controller.report(mission["id"], 1, "File now exists", True)
        self.assertEqual(result["steps"][1]["status"], "active")

    def test_input_limits_and_capacity(self) -> None:
        with self.assertRaises(ValueError):
            self.controller.create(" ", ["test"], "pass")
        with self.assertRaises(ValueError):
            self.controller.create("goal", ["x"] * 9, "pass")
        with self.assertRaises(ValueError):
            self.controller.create("goal", [], "pass")
        for _ in range(5):
            self.mission()
        with self.assertRaises(ValueError):
            self.mission()

    def test_invalid_ids_steps_and_missing_verification(self) -> None:
        mission = self.mission()
        with self.assertRaises(ValueError):
            self.controller.status("wrong")
        with self.assertRaises(ValueError):
            self.controller.report(mission["id"], 0, "no", True)
        with self.assertRaises(ValueError):
            self.controller.report(mission["id"], 1, "no", "yes")
        with self.assertRaises(ValueError):
            self.controller.verify_file(mission["id"], 1, "README.md", "ok")


if __name__ == "__main__":
    unittest.main()

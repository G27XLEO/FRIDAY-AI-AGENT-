from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path


class McpToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        os.environ["FRIDAY_WORKSPACE_ROOT"] = self.tempdir.name
        os.environ["FRIDAY_MEMORY_PATH"] = str(Path(self.tempdir.name) / "memory.json")

        import importlib
        import friday_agent.mcp_tools as mcp_tools

        self.mcp_tools = importlib.reload(mcp_tools)

    def test_workspace_file_round_trip(self) -> None:
        write_result = self.mcp_tools.write_workspace_file("notes/mission.txt", "online")
        self.assertTrue(write_result.ok)

        read_result = self.mcp_tools.read_workspace_file("notes/mission.txt")
        self.assertTrue(read_result.ok)
        self.assertEqual(read_result.content, "online")

    def test_workspace_path_traversal_is_blocked(self) -> None:
        with self.assertRaises(ValueError):
            self.mcp_tools.read_workspace_file("../outside.txt")

    def test_memory_round_trip(self) -> None:
        self.assertTrue(self.mcp_tools.remember("operator", {"name": "boss"}).ok)
        recall_result = self.mcp_tools.recall("operator")
        self.assertTrue(recall_result.ok)
        self.assertIn("boss", recall_result.content)

    def test_plan_task_contains_goal(self) -> None:
        result = self.mcp_tools.plan_task("build my own mcp server")
        self.assertTrue(result.ok)
        self.assertIn("build my own mcp server", result.content)


class AllowedCommandsTest(unittest.TestCase):
    def test_allowed_commands_accepts_comma_separated_values(self):
        import friday_agent.mcp_tools as mcp_tools

        original = os.environ.get("FRIDAY_ALLOWED_COMMANDS")
        try:
            os.environ["FRIDAY_ALLOWED_COMMANDS"] = "echo, python git"
            self.assertEqual(mcp_tools._allowed_commands(), {"echo", "python", "git"})
        finally:
            if original is None:
                os.environ.pop("FRIDAY_ALLOWED_COMMANDS", None)
            else:
                os.environ["FRIDAY_ALLOWED_COMMANDS"] = original


if __name__ == "__main__":
    unittest.main()

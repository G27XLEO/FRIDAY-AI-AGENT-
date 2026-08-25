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
        result = self.mcp_tools.read_workspace_file("../outside.txt")
        self.assertFalse(result.ok)
        self.assertIn("escapes workspace", result.content)

    def test_memory_round_trip(self) -> None:
        self.assertTrue(self.mcp_tools.remember("operator", {"name": "boss"}).ok)
        recall_result = self.mcp_tools.recall("operator")
        self.assertTrue(recall_result.ok)
        self.assertIn("boss", recall_result.content)

    def test_plan_task_contains_goal(self) -> None:
        result = self.mcp_tools.plan_task("build my own mcp server")
        self.assertTrue(result.ok)
        self.assertIn("build my own mcp server", result.content)

    def test_read_missing_file_returns_error_result(self) -> None:
        result = self.mcp_tools.read_workspace_file("does/not/exist.txt")
        self.assertFalse(result.ok)
        self.assertIn("not found", result.content.lower())

    def test_write_without_overwrite_then_overwrite(self) -> None:
        first = self.mcp_tools.write_workspace_file("notes/a.txt", "one")
        self.assertTrue(first.ok)

        blocked = self.mcp_tools.write_workspace_file("notes/a.txt", "two")
        self.assertFalse(blocked.ok)

        forced = self.mcp_tools.write_workspace_file("notes/a.txt", "two", overwrite=True)
        self.assertTrue(forced.ok)
        self.assertEqual(self.mcp_tools.read_workspace_file("notes/a.txt").content, "two")

    def test_write_over_size_limit_is_rejected(self) -> None:
        os.environ["FRIDAY_MAX_WRITE_BYTES"] = "10"
        try:
            import importlib

            reloaded = importlib.reload(self.mcp_tools)
            result = reloaded.write_workspace_file("notes/big.txt", "x" * 100)
            self.assertFalse(result.ok)
            self.assertIn("exceeding", result.content)
        finally:
            os.environ.pop("FRIDAY_MAX_WRITE_BYTES", None)

    def test_list_workspace_files(self) -> None:
        self.mcp_tools.write_workspace_file("notes/a.txt", "one")
        self.mcp_tools.write_workspace_file("notes/b.txt", "two")

        result = self.mcp_tools.list_workspace_files("notes")
        self.assertTrue(result.ok)
        self.assertIn("a.txt", result.content)
        self.assertIn("b.txt", result.content)

    def test_list_workspace_files_missing_path(self) -> None:
        result = self.mcp_tools.list_workspace_files("nope")
        self.assertFalse(result.ok)

    def test_corrupt_memory_file_recovers_gracefully(self) -> None:
        self.mcp_tools.MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.mcp_tools.MEMORY_PATH.write_text("{not valid json", encoding="utf-8")

        result = self.mcp_tools.recall()
        self.assertTrue(result.ok)
        self.assertEqual(result.content.strip(), "{}")


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

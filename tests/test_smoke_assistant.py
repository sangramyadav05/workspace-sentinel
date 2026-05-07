import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from core.dashboard import show_status
from core.paths import MEMORY_FILE, PROJECT_ROOT
from core.state import SystemState
from core.workspace_guard import WORKSPACE_ROOT, WorkspaceViolation, resolve_safe_path
from memory.short_term import ShortTermMemory


class WorkspaceGuardTests(unittest.TestCase):
    def test_rejects_parent_traversal_to_sibling_directory(self):
        with self.assertRaises(WorkspaceViolation):
            resolve_safe_path("..\\workspace_backup\\poc.txt")

    def test_allows_workspace_relative_file(self):
        path = resolve_safe_path("hello.txt")
        self.assertEqual(path, (WORKSPACE_ROOT / "hello.txt").resolve())


class DashboardTests(unittest.TestCase):
    def test_status_output_is_ascii_safe(self):
        state = SystemState()
        short_memory = ShortTermMemory()
        output = io.StringIO()

        with redirect_stdout(output):
            show_status(
                state=state,
                last_activity=0,
                session_timeout=600,
                last_command_time=0,
                min_interval=2,
                short_memory=short_memory,
                long_memory_path=MEMORY_FILE,
                workspace_root=WORKSPACE_ROOT,
            )

        rendered = output.getvalue()
        rendered.encode("cp1252")
        self.assertIn("[OK] Human approval required", rendered)


class MainEntryTests(unittest.TestCase):
    def test_main_starts_without_api_key_for_non_ai_commands(self):
        env = os.environ.copy()
        env["OPENROUTER_API_KEY"] = ""

        result = subprocess.run(
            [sys.executable, "main.py"],
            input="EXIT\n",
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=env,
            timeout=10,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Workspace Sentinel (DISABLED)", result.stdout)
        self.assertIn("Exiting system.", result.stdout)

    def test_main_uses_project_paths_when_started_from_parent_directory(self):
        env = os.environ.copy()
        env["OPENROUTER_API_KEY"] = ""

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main.py")],
            input="ENABLE\nstatus\nEXIT\n",
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT.parent,
            env=env,
            timeout=10,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Workspace Sentinel (DISABLED)", result.stdout)
        self.assertIn("Files present   : 1", result.stdout)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch

from core.command_processor import (
    CommandContext,
    expire_session_if_needed,
    process_command,
)
from core.config import ConfigurationError
from core.state import SystemState
from memory.short_term import ShortTermMemory


class PermissionStub:
    def __init__(self, *responses):
        self._responses = list(responses)
        self.prompts = []

    def request(self, action_description: str) -> bool:
        self.prompts.append(action_description)
        return self._responses.pop(0)


class LongTermMemoryStub:
    def __init__(self):
        self.saved_entries = []

    def save(self, title: str, content: str) -> None:
        self.saved_entries.append({
            "title": title,
            "content": content,
        })


def build_context(
    *,
    permissions=None,
    long_memory=None,
    min_interval=2,
    session_timeout=600,
):
    return CommandContext(
        state=SystemState(),
        short_memory=ShortTermMemory(),
        long_memory=long_memory or LongTermMemoryStub(),
        permissions=permissions or PermissionStub(),
        min_interval=min_interval,
        session_timeout=session_timeout,
    )


class CommandProcessorTests(unittest.TestCase):
    def test_enable_command_updates_state(self):
        context = build_context()
        output = []
        logs = []

        keep_running = process_command(
            "ENABLE",
            context,
            now=100,
            output=output.append,
            logger=logs.append,
        )

        self.assertTrue(keep_running)
        self.assertTrue(context.state.is_enabled())
        self.assertIn("System ENABLED", output)
        self.assertIn("System enabled by user", logs)

    def test_status_command_renders_through_output_writer(self):
        context = build_context()
        context.state.enable()
        output = []

        process_command(
            "status",
            context,
            now=100,
            output=output.append,
            logger=lambda _: None,
        )

        self.assertEqual(context.last_command_time, 100)
        self.assertTrue(any("SYSTEM STATUS" in line for line in output))
        self.assertIn("  [OK] Workspace sandbox enforced", output)

    def test_read_command_requires_filename(self):
        context = build_context()
        context.state.enable()
        output = []

        process_command(
            "read",
            context,
            now=100,
            output=output.append,
            logger=lambda _: None,
        )

        self.assertIn("[ERROR] No filename provided.", output)

    def test_read_command_denial_skips_file_access(self):
        context = build_context(permissions=PermissionStub(False))
        context.state.enable()
        output = []

        with patch("core.command_processor.read_text_file") as reader:
            process_command(
                "read hello.txt",
                context,
                now=100,
                output=output.append,
                logger=lambda _: None,
            )

        reader.assert_not_called()
        self.assertIn("[DENIED] File read denied.", output)

    def test_write_command_collects_content_and_writes(self):
        context = build_context(permissions=PermissionStub(True))
        context.state.enable()
        output = []
        lines = iter(["alpha", "beta", "EOF"])

        with patch("core.command_processor.write_text_file") as writer:
            process_command(
                "write demo.txt",
                context,
                now=100,
                output=output.append,
                line_reader=lambda: next(lines),
                logger=lambda _: None,
            )

        writer.assert_called_once_with("demo.txt", "alpha\nbeta")
        self.assertIn("[OK] File written successfully.", output)

    def test_ai_command_can_save_memory_without_network(self):
        long_memory = LongTermMemoryStub()
        context = build_context(
            permissions=PermissionStub(True, True),
            long_memory=long_memory,
        )
        context.state.enable()
        output = []

        def fake_loader():
            def fake_interpret(user_input: str) -> str:
                self.assertIn("<user_input>", user_input)
                return "safe reply"

            return fake_interpret

        process_command(
            "Summarize the workspace",
            context,
            now=100,
            output=output.append,
            interpreter_loader=fake_loader,
            logger=lambda _: None,
        )

        self.assertEqual(context.short_memory.count(), 2)
        self.assertEqual(len(long_memory.saved_entries), 1)
        self.assertIn("safe reply", long_memory.saved_entries[0]["content"])
        self.assertIn("[OK] Memory saved.", output)
        self.assertIn("external AI service", context.permissions.prompts[0])
        self.assertIn("long-term memory", context.permissions.prompts[1])

    def test_ai_command_reports_missing_configuration(self):
        context = build_context(permissions=PermissionStub(True))
        context.state.enable()
        output = []

        def failing_loader():
            raise ConfigurationError("OPENROUTER_API_KEY is not set.")

        process_command(
            "Explain this",
            context,
            now=100,
            output=output.append,
            interpreter_loader=failing_loader,
            logger=lambda _: None,
        )

        self.assertIn("[ERROR] OPENROUTER_API_KEY is not set.", output)
        self.assertEqual(context.short_memory.count(), 0)

    def test_ai_command_requires_outbound_approval(self):
        context = build_context(permissions=PermissionStub(False))
        context.state.enable()
        output = []

        with patch("core.command_processor.load_interpreter") as loader:
            process_command(
                "Explain this",
                context,
                now=100,
                output=output.append,
                logger=lambda _: None,
            )

        loader.assert_not_called()
        self.assertIn("[DENIED] AI request cancelled.", output)
        self.assertEqual(context.short_memory.count(), 0)

    def test_ai_command_blocks_memory_save_for_sensitive_data(self):
        long_memory = LongTermMemoryStub()
        context = build_context(
            permissions=PermissionStub(True),
            long_memory=long_memory,
        )
        context.state.enable()
        output = []
        logs = []

        def fake_loader():
            return lambda _: "Here is a token: sk-testtoken1234567890abcdef"

        process_command(
            "Summarize the workspace",
            context,
            now=100,
            output=output.append,
            interpreter_loader=fake_loader,
            logger=logs.append,
        )

        self.assertEqual(len(context.permissions.prompts), 1)
        self.assertEqual(len(long_memory.saved_entries), 0)
        self.assertIn("[DENIED] Memory save blocked because sensitive data was detected.", output)
        self.assertIn("Memory save blocked due to sensitive data", logs)

    def test_user_command_logging_redacts_sensitive_data(self):
        context = build_context(permissions=PermissionStub(False))
        context.state.enable()
        logs = []

        process_command(
            "OPENROUTER_API_KEY=sk-testtoken1234567890abcdef",
            context,
            now=100,
            output=lambda _: None,
            logger=logs.append,
        )

        self.assertIn("OPENROUTER_API_KEY=[REDACTED]", logs[0])
        self.assertNotIn("sk-testtoken1234567890abcdef", logs[0])

    def test_rate_limit_blocks_follow_up_command(self):
        context = build_context()
        context.state.enable()
        context.last_command_time = 99
        output = []

        process_command(
            "status",
            context,
            now=100,
            output=output.append,
            logger=lambda _: None,
        )

        self.assertEqual(output, ["[WAIT] Please wait before sending another command."])

    def test_session_timeout_disables_enabled_state(self):
        context = build_context(session_timeout=10)
        context.state.enable()
        context.last_activity = 0
        output = []
        logs = []

        expire_session_if_needed(
            context,
            now=20,
            output=output.append,
            logger=logs.append,
        )

        self.assertFalse(context.state.is_enabled())
        self.assertIn("[LOCK] Session expired. System DISABLED.", output)
        self.assertIn("Session timeout - system disabled", logs)


if __name__ == "__main__":
    unittest.main()

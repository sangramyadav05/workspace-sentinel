import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from core.audit import log
from core.config import ConfigurationError
from core.dashboard import show_status
from core.file_reader import FileReadError, read_text_file
from core.file_writer import FileWriteError, write_text_file
from core.paths import MEMORY_FILE
from core.permissions import PermissionGate
from core.sanitizer import sanitize_user_input
from core.secret_filter import contains_sensitive_data, redact_sensitive_data
from core.state import SystemState
from core.workspace_guard import WORKSPACE_ROOT
from memory.long_term import LongTermMemory
from memory.short_term import ShortTermMemory


OutputWriter = Callable[[str], None]
InputReader = Callable[[], str]
Interpreter = Callable[[str], str]
InterpreterLoader = Callable[[], Interpreter]
Logger = Callable[[str], None]

DEFAULT_LONG_MEMORY_PATH = MEMORY_FILE


@dataclass
class CommandContext:
    state: SystemState
    short_memory: ShortTermMemory
    long_memory: LongTermMemory
    permissions: PermissionGate
    min_interval: int
    session_timeout: int
    long_memory_path: Path = DEFAULT_LONG_MEMORY_PATH
    workspace_root: Path = WORKSPACE_ROOT
    last_command_time: float = 0.0
    last_activity: float = field(default_factory=time.time)



def load_interpreter() -> Interpreter:
    from agent.interpreter import interpret

    return interpret



def expire_session_if_needed(
    context: CommandContext,
    *,
    now: float,
    output: OutputWriter = print,
    logger: Logger = log,
) -> None:
    if context.state.is_enabled() and (now - context.last_activity > context.session_timeout):
        context.state.disable()
        output("[LOCK] Session expired. System DISABLED.")
        logger("Session timeout - system disabled")



def process_command(
    cmd: str,
    context: CommandContext,
    *,
    now: float,
    output: OutputWriter = print,
    line_reader: InputReader = input,
    interpreter_loader: InterpreterLoader = load_interpreter,
    logger: Logger = log,
) -> bool:
    cmd = cmd.strip()
    if not cmd:
        return True

    context.last_activity = now
    upper_cmd = cmd.upper()

    if upper_cmd == "EXIT":
        logger("System exited by user")
        output("Exiting system.")
        return False

    if upper_cmd == "ENABLE":
        context.state.enable()
        logger("System enabled by user")
        output("System ENABLED")
        return True

    if not context.state.is_enabled():
        output("System is DISABLED. Type ENABLE to continue.")
        return True

    if now - context.last_command_time < context.min_interval:
        output("[WAIT] Please wait before sending another command.")
        return True

    context.last_command_time = now
    logger(f"User command received: {redact_sensitive_data(cmd)}")

    try:
        lower_cmd = cmd.lower()
        verb, _, remainder = cmd.partition(" ")

        if lower_cmd == "status":
            _handle_status_command(context, output=output)
            return True

        if verb.lower() == "read":
            _handle_read_command(
                remainder.strip(),
                context,
                output=output,
                logger=logger,
            )
            return True

        if verb.lower() == "write":
            _handle_write_command(
                remainder.strip(),
                context,
                output=output,
                line_reader=line_reader,
                logger=logger,
            )
            return True

        _handle_ai_command(
            cmd,
            context,
            output=output,
            interpreter_loader=interpreter_loader,
            logger=logger,
        )
    except Exception as exc:
        logger(f"ERROR: {str(exc)}")
        output("[ERROR] System error occurred. Action aborted safely.")

    return True



def _handle_status_command(
    context: CommandContext,
    *,
    output: OutputWriter,
) -> None:
    show_status(
        state=context.state,
        last_activity=context.last_activity,
        session_timeout=context.session_timeout,
        last_command_time=context.last_command_time,
        min_interval=context.min_interval,
        short_memory=context.short_memory,
        long_memory_path=context.long_memory_path,
        workspace_root=context.workspace_root,
        output=output,
    )



def _handle_read_command(
    filename: str,
    context: CommandContext,
    *,
    output: OutputWriter,
    logger: Logger,
) -> None:
    if not filename:
        output("[ERROR] No filename provided.")
        return

    approve = context.permissions.request(
        f"Do you want to read the file '{filename}' from workspace?"
    )

    if not approve:
        output("[DENIED] File read denied.")
        return

    try:
        content = read_text_file(filename)
        output("\n--- FILE CONTENT START ---")
        output(content)
        output("--- FILE CONTENT END ---\n")
        logger(f"File read: {filename}")
    except FileReadError as exc:
        output(f"[ERROR] File read error: {exc}")
        logger(f"File read error: {exc}")



def _handle_write_command(
    filename: str,
    context: CommandContext,
    *,
    output: OutputWriter,
    line_reader: InputReader,
    logger: Logger,
) -> None:
    if not filename:
        output("[ERROR] No filename provided.")
        return

    output("Enter file content. Finish with a single line containing EOF:")
    lines = []

    while True:
        line = line_reader()
        if line == "EOF":
            break
        lines.append(line)

    content = "\n".join(lines)

    output("\n=== PROPOSED FILE CONTENT ===")
    output(content)
    output("=== END OF CONTENT ===\n")

    approve = context.permissions.request(
        f"Allow writing this content to '{filename}'?"
    )

    if not approve:
        output("[DENIED] File write cancelled.")
        return

    try:
        write_text_file(filename, content)
        output("[OK] File written successfully.")
        logger(f"File written: {filename}")
    except FileWriteError as exc:
        output(f"[ERROR] File write error: {exc}")
        logger(f"File write error: {exc}")



def _handle_ai_command(
    cmd: str,
    context: CommandContext,
    *,
    output: OutputWriter,
    interpreter_loader: InterpreterLoader,
    logger: Logger,
) -> None:
    wrapped_cmd, suspicious = sanitize_user_input(cmd)

    if suspicious:
        output("[WARN] Input flagged as suspicious.")
        logger("Suspicious input detected")

    approve = context.permissions.request(
        "Do you want to send this prompt to the external AI service?"
    )

    if not approve:
        output("[DENIED] AI request cancelled.")
        logger("AI request denied")
        return

    try:
        interpret = interpreter_loader()
        reply = interpret(wrapped_cmd)
    except ConfigurationError as exc:
        logger(f"Configuration error: {str(exc)}")
        output(f"[ERROR] {exc}")
        return

    output("\nAI (READ-ONLY):")
    output(reply)
    output("")

    context.short_memory.add("user", cmd)
    context.short_memory.add("assistant", reply)

    memory_entry = f"USER: {cmd}\nAI: {reply}"
    if contains_sensitive_data(memory_entry):
        output("[DENIED] Memory save blocked because sensitive data was detected.")
        logger("Memory save blocked due to sensitive data")
        return

    save = context.permissions.request(
        "Do you want to save this interaction to long-term memory?"
    )

    if save:
        context.long_memory.save(
            title="User Command",
            content=memory_entry,
        )
        output("[OK] Memory saved.")
        logger("Memory saved")
    else:
        output("[DENIED] Memory NOT saved.")
        logger("Memory save denied")

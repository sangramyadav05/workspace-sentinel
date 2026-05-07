import time
from core.command_processor import (
    CommandContext,
    expire_session_if_needed,
    process_command,
)
from core.permissions import PermissionGate
from interface.cli import get_user_command
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from core.state import SystemState


# ----------------------------
# SYSTEM CONFIGURATION
# ----------------------------

MIN_INTERVAL = 2
SESSION_TIMEOUT = 600

INITIAL_LAST_COMMAND_TIME = 0.0


def build_context() -> CommandContext:
    return CommandContext(
        state=SystemState(),
        short_memory=ShortTermMemory(),
        long_memory=LongTermMemory(),
        permissions=PermissionGate(),
        min_interval=MIN_INTERVAL,
        session_timeout=SESSION_TIMEOUT,
        last_command_time=INITIAL_LAST_COMMAND_TIME,
        last_activity=time.time(),
    )


def print_banner(output=print) -> None:
    output("Workspace Sentinel (DISABLED)")
    output("Commands: ENABLE | EXIT | status | read <file> | write <file>")
    output("-" * 40)


def run_cli(
    *,
    context: CommandContext | None = None,
    command_reader=get_user_command,
    line_reader=input,
    output=print,
    time_source=time.time,
) -> int:
    context = context or build_context()
    print_banner(output=output)

    while True:
        now = time_source()
        expire_session_if_needed(context, now=now, output=output)
        cmd = command_reader().strip()

        if not process_command(
            cmd,
            context,
            now=now,
            output=output,
            line_reader=line_reader,
        ):
            return 0


def main() -> int:
    return run_cli()


if __name__ == "__main__":
    raise SystemExit(main())

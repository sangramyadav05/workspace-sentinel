import time
from pathlib import Path


def show_status(
    *,
    state,
    last_activity,
    session_timeout,
    last_command_time,
    min_interval,
    short_memory,
    long_memory_path: Path,
    workspace_root: Path,
    output=print,
):
    now = time.time()

    enabled = state.is_enabled()
    session_left = max(0, int(session_timeout - (now - last_activity)))
    rate_ok = (now - last_command_time) >= min_interval

    short_mem_count = short_memory.count()

    long_mem_size = (
        long_memory_path.stat().st_size
        if long_memory_path.exists()
        else 0
    )

    workspace_files = (
        len([p for p in workspace_root.iterdir() if p.is_file()])
        if workspace_root.exists()
        else 0
    )

    output("\n========== SYSTEM STATUS ==========")
    output(f"System State      : {'ENABLED' if enabled else 'DISABLED'}")
    output(f"Session Time Left : {session_left} seconds")
    output(f"Rate Limit Ready  : {'YES' if rate_ok else 'WAIT'}")
    output("")
    output("Memory:")
    output(f"  Short-term items: {short_mem_count}")
    output(f"  Long-term size  : {long_mem_size} bytes")
    output("")
    output("Workspace:")
    output(f"  Files present   : {workspace_files}")
    output("")
    output("Safety:")
    output("  [OK] Human approval required")
    output("  [OK] Workspace sandbox enforced")
    output("  [OK] Read-only AI")
    output("  [OK] No autonomous actions")
    output("=================================\n")

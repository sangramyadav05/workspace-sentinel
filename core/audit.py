from datetime import UTC, datetime

from core.secret_filter import redact_sensitive_data



def log(event: str):
    """
    Append an audit log entry with UTC timestamp.
    This file is append-only by design.
    """

    timestamp = datetime.now(UTC).isoformat()
    entry = f"[{timestamp}] {redact_sensitive_data(event)}\n"

    with open("audit.log", "a", encoding="utf-8") as f:
        f.write(entry)

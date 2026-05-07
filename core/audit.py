from datetime import datetime


def log(event: str):
    """
    Append an audit log entry with UTC timestamp.
    This file is append-only by design.
    """

    timestamp = datetime.utcnow().isoformat()
    entry = f"[{timestamp}] {event}\n"

    with open("audit.log", "a", encoding="utf-8") as f:
        f.write(entry)

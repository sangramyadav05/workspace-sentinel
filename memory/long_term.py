import json
from pathlib import Path
from datetime import UTC, datetime

from core.paths import MEMORY_FILE
from core.secret_filter import contains_sensitive_data

MAX_MEMORY_CHARS = 5000


class LongTermMemoryError(RuntimeError):
    """Raised when persistent memory cannot be read or written safely."""


class LongTermMemory:
    """
    Persistent memory storage.
    Writes ONLY with explicit user approval.
    """

    def __init__(self, path: Path = MEMORY_FILE):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

        if not self._path.exists():
            self._write_entries([])

    def save(self, title: str, content: str):
        """
        Save a memory entry.
        This method must ONLY be called after user approval.
        """
        if len(content) > MAX_MEMORY_CHARS:
            raise LongTermMemoryError("Memory entry exceeds safe size limit")

        if contains_sensitive_data(f"{title}\n{content}"):
            raise LongTermMemoryError(
                "Memory entry contains sensitive data and cannot be stored"
            )

        data = self._read_entries()

        data.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "title": title,
            "content": content
        })

        self._write_entries(data)

    def load_all(self):
        """
        Load all saved memory entries.
        """
        return self._read_entries()

    def _read_entries(self):
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise LongTermMemoryError(
                f"Long-term memory file is corrupted: {self._path}"
            ) from exc

    def _write_entries(self, entries) -> None:
        self._path.write_text(
            json.dumps(entries, indent=2),
            encoding="utf-8",
        )

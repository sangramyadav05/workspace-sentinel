import unittest
from contextlib import suppress
from pathlib import Path
from uuid import uuid4

from memory.long_term import (
    MAX_MEMORY_CHARS,
    LongTermMemory,
    LongTermMemoryError,
)


def make_test_memory_path() -> Path:
    return Path("workspace") / "test_artifacts" / f"{uuid4().hex}.json"


class LongTermMemoryTests(unittest.TestCase):
    def test_custom_path_round_trips_entries(self):
        memory_path = make_test_memory_path()

        try:
            memory = LongTermMemory(memory_path)

            memory.save("Example", "Remember this")
            entries = memory.load_all()

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["title"], "Example")
            self.assertEqual(entries[0]["content"], "Remember this")
        finally:
            with suppress(OSError):
                memory_path.parent.rmdir()

    def test_rejects_oversized_entries(self):
        memory_path = make_test_memory_path()

        try:
            memory = LongTermMemory(memory_path)

            with self.assertRaises(LongTermMemoryError):
                memory.save("Too big", "x" * (MAX_MEMORY_CHARS + 1))
        finally:
            with suppress(OSError):
                memory_path.parent.rmdir()


if __name__ == "__main__":
    unittest.main()

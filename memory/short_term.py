class ShortTermMemory:
    """
    Temporary in-memory storage.
    Cleared automatically when the program exits.
    """

    def __init__(self):
        self._buffer = []

    def add(self, role: str, content: str):
        self._buffer.append({
            "role": role,
            "content": content
        })

    def get_all(self):
        return list(self._buffer)

    def clear(self):
        self._buffer.clear()

    def count(self) -> int:
        return len(self._buffer)
    

class SystemState:
    """
    Tracks whether the system is enabled or disabled.
    Default state is DISABLED for safety.
    """

    def __init__(self):
        self._enabled = False

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

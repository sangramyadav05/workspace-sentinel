class PermissionGate:
    """
    Central authority for approving sensitive actions.
    NOTHING passes without explicit user consent.
    """

    def request(self, action_description: str) -> bool:
        print("\n=== PERMISSION REQUIRED ===")
        print(action_description)
        choice = input("Approve? (YES / NO): ").strip().upper()

        return choice == "YES"

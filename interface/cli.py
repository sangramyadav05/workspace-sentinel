def get_user_command() -> str:
    """
    Reads a command from the user via CLI.
    This is the ONLY place raw user input enters the system.
    """
    return input("> ").strip()

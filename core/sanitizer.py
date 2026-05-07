import re
from typing import Tuple


# High-risk instruction override patterns (case-insensitive)
INSTRUCTION_OVERRIDE_PATTERNS = [
    r"ignore\s+.*instructions",
    r"disregard\s+.*rules",
    r"override\s+.*system",
    r"bypass\s+.*safety",
    r"act\s+as\s+.*system",
    r"you\s+are\s+now\s+.*",
]


def detect_prompt_injection(text: str) -> bool:
    """
    Detects whether the input attempts instruction override.
    This is classification, NOT sanitization.
    """

    lowered = text.lower()

    for pattern in INSTRUCTION_OVERRIDE_PATTERNS:
        if re.search(pattern, lowered):
            return True

    return False


def wrap_user_input(text: str) -> str:
    """
    Structurally delimit user input so the LLM knows
    exactly what is user data and nothing else.
    """

    return f"<user_input>\n{text.strip()}\n</user_input>"


def sanitize_user_input(text: str) -> Tuple[str, bool]:
    """
    Returns:
        (wrapped_input, is_suspicious)

    We do NOT modify user intent.
    We only classify risk and enforce structure.
    """

    suspicious = detect_prompt_injection(text)
    wrapped = wrap_user_input(text)

    return wrapped, suspicious

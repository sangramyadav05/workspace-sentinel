import re


ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b([a-z0-9_]*api[_-]?key|[a-z0-9_]*access[_-]?token|[a-z0-9_]*auth[_-]?token|[a-z0-9_]*refresh[_-]?token|[a-z0-9_]*client[_-]?secret|[a-z0-9_]*password|[a-z0-9_]*passwd|[a-z0-9_]*secret)\b(\s*[:=]\s*)([^\s,;]+)"
)
BEARER_PATTERN = re.compile(r"(?i)\b(bearer)\s+([a-z0-9._\-]{8,})")
TOKEN_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]



def contains_sensitive_data(text: str) -> bool:
    if not text:
        return False

    if ASSIGNMENT_PATTERN.search(text) or BEARER_PATTERN.search(text):
        return True

    return any(pattern.search(text) for pattern in TOKEN_PATTERNS)



def redact_sensitive_data(text: str) -> str:
    if not text:
        return text

    redacted = ASSIGNMENT_PATTERN.sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", text)
    redacted = BEARER_PATTERN.sub(lambda match: f"{match.group(1)} [REDACTED]", redacted)

    for pattern in TOKEN_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)

    return redacted

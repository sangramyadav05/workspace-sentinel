from core.workspace_guard import resolve_safe_path, WorkspaceViolation


MAX_FILE_SIZE = 50_000  # 50 KB safety limit


class FileReadError(Exception):
    pass


def read_text_file(relative_path: str) -> str:
    """
    Safely reads a text file from the workspace only.
    """

    try:
        safe_path = resolve_safe_path(relative_path)
    except WorkspaceViolation as e:
        raise FileReadError(str(e))

    if not safe_path.exists():
        raise FileReadError("File does not exist")

    if not safe_path.is_file():
        raise FileReadError("Path is not a file")

    size = safe_path.stat().st_size
    if size > MAX_FILE_SIZE:
        raise FileReadError("File too large to read safely")

    try:
        return safe_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise FileReadError("File is not valid UTF-8 text")

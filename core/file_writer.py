from core.workspace_guard import resolve_safe_path, WorkspaceViolation


MAX_WRITE_SIZE = 50_000  # 50 KB safety limit


class FileWriteError(Exception):
    pass


def write_text_file(
    relative_path: str,
    content: str,
    *,
    overwrite: bool = False
) -> None:
    """
    Safely writes a UTF-8 text file to the workspace only.

    Default behavior is CREATE-ONLY.
    Overwrite requires explicit opt-in.
    """

    if not isinstance(content, str):
        raise FileWriteError("Content must be a string")

    if len(content.encode("utf-8")) > MAX_WRITE_SIZE:
        raise FileWriteError("Content too large to write safely")

    try:
        safe_path = resolve_safe_path(relative_path)
    except WorkspaceViolation as e:
        raise FileWriteError(str(e))

    if safe_path.exists() and not overwrite:
        raise FileWriteError("File already exists (overwrite not allowed)")

    if safe_path.exists() and not safe_path.is_file():
        raise FileWriteError("Target path is not a file")

    try:
        safe_path.write_text(content, encoding="utf-8")
    except Exception as e:
        raise FileWriteError(f"Write failed: {e}")

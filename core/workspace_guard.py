from pathlib import Path


# Absolute, resolved path to workspace
WORKSPACE_ROOT = Path("workspace").resolve()


class WorkspaceViolation(Exception):
    """Raised when an attempt is made to access files outside workspace."""
    pass


def resolve_safe_path(relative_path: str) -> Path:
    """
    Resolves a user-provided path safely inside the workspace.
    Blocks absolute paths, path traversal, and existing symlink hops.
    """
    user_path = Path(relative_path)

    if user_path.is_absolute():
        raise WorkspaceViolation("Access denied: absolute paths are not allowed")

    current = WORKSPACE_ROOT
    for part in user_path.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise WorkspaceViolation(
                f"Access denied: '{relative_path}' uses a symlink"
            )

    candidate = (WORKSPACE_ROOT / user_path).resolve()

    try:
        candidate.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise WorkspaceViolation(
            f"Access denied: '{relative_path}' is outside workspace"
        ) from exc

    return candidate

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"
MEMORY_DATA_DIR = PROJECT_ROOT / "memory" / "data"
MEMORY_FILE = MEMORY_DATA_DIR / "user_memory.json"
AUDIT_LOG_FILE = PROJECT_ROOT / "audit.log"
ENV_FILE = PROJECT_ROOT / ".env"

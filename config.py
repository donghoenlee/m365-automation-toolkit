import os

from dotenv import load_dotenv

load_dotenv()


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


USE_MOCK_GRAPH = _bool_env("USE_MOCK_GRAPH", True)

GRAPH_TENANT_ID = os.getenv("GRAPH_TENANT_ID", "")
GRAPH_CLIENT_ID = os.getenv("GRAPH_CLIENT_ID", "")
GRAPH_CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET", "")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")

MOCK_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "mock_db.json")
INACTIVE_DAYS_THRESHOLD = int(os.getenv("INACTIVE_DAYS_THRESHOLD", "90"))

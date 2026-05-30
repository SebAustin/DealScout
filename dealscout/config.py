"""Environment and runtime configuration."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "cache.db"

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
BRIGHT_DATA_TOKEN = os.getenv("BRIGHT_DATA_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

MCP_SSE_URL = (
    f"https://mcp.brightdata.com/sse?token={BRIGHT_DATA_TOKEN}"
    if BRIGHT_DATA_TOKEN
    else ""
)

"""Configuration for the WayTum agent service."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent
REPO = BACKEND.parent

# Load env files in priority order — last loaded wins on conflict.
load_dotenv(REPO / ".env")
load_dotenv(BACKEND / ".env")

AGENT_HOST: str = os.getenv("AGENT_HOST", "0.0.0.0")
AGENT_PORT: int = int(os.getenv("AGENT_PORT", "8000"))

MCP_URL: str = os.getenv("MCP_URL", "http://localhost:8001/mcp")

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL: str = os.getenv(
    "ANTHROPIC_MODEL", "claude-3-5-haiku-latest"
)
ANTHROPIC_MAX_TOKENS: int = int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096"))
MAX_TOOL_ROUNDS: int = int(os.getenv("AGENT_MAX_TOOL_ROUNDS", "8"))

DEMO_TUM_USERNAME: str = os.getenv("DEMO_TUM_USERNAME", "ge47lbg").strip()

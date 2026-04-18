"""Shared configuration for the combined backend host."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent

# Prefer the new backend-level env file, but still load the old MCP env file so
# existing local secrets keep working during the transition.
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "mcp" / ".env")

BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))

INTERNAL_MCP_PORT: int = int(os.getenv("INTERNAL_MCP_PORT", "8001"))
INTERNAL_AGENT_PORT: int = int(os.getenv("INTERNAL_AGENT_PORT", "8002"))
INSPECTOR_CLIENT_PORT: int = int(os.getenv("INSPECTOR_CLIENT_PORT", "6274"))
INSPECTOR_PROXY_PORT: int = int(os.getenv("INSPECTOR_PROXY_PORT", "6277"))

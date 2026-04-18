"""Shared configuration for the combined backend host."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent

# Load env files in priority order — last loaded wins on conflict.
load_dotenv(REPO / ".env")
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "mcp" / ".env")

BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))

INTERNAL_MCP_PORT: int = int(os.getenv("INTERNAL_MCP_PORT", "8001"))
INTERNAL_AGENT_PORT: int = int(os.getenv("INTERNAL_AGENT_PORT", "8002"))
INSPECTOR_CLIENT_PORT: int = int(os.getenv("INSPECTOR_CLIENT_PORT", "6274"))
INSPECTOR_PROXY_PORT: int = int(os.getenv("INSPECTOR_PROXY_PORT", "6277"))

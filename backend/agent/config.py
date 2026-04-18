"""Configuration for the isolated agent service."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "mcp" / ".env")

AGENT_HOST: str = os.getenv("AGENT_HOST", "0.0.0.0")
AGENT_PORT: int = int(os.getenv("AGENT_PORT", "8002"))

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

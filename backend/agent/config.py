"""Configuration for the Bedrock-backed Campus Co-Pilot agent service."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent
REPO = BACKEND.parent

# Load env files in priority order — last loaded wins on conflict.
load_dotenv(REPO / ".env")
load_dotenv(BACKEND / ".env")
load_dotenv(BACKEND / "mcp" / ".env")

AGENT_HOST: str = os.getenv("AGENT_HOST", "0.0.0.0")
AGENT_PORT: int = int(os.getenv("AGENT_PORT", "8002"))

MCP_URL: str = os.getenv("MCP_URL", "http://localhost:8000/mcp")

AWS_REGION: str = os.getenv("AWS_REGION", "eu-north-1")
BEDROCK_MODEL: str = os.getenv(
    "BEDROCK_MODEL", "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
)
BEDROCK_MAX_TOKENS: int = int(os.getenv("BEDROCK_MAX_TOKENS", "4096"))
ANTHROPIC_VERSION: str = "bedrock-2023-05-31"
MAX_TOOL_ROUNDS: int = int(os.getenv("AGENT_MAX_TOOL_ROUNDS", "8"))

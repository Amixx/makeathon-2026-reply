"""Configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT.parent
REPO = BACKEND.parent

# Load env files in priority order — last loaded wins on conflict.
load_dotenv(REPO / ".env")
load_dotenv(BACKEND / ".env")
load_dotenv(ROOT / ".env")

# ── TUM environment ──────────────────────────────────────────────────────────
TUM_ENV: str = os.getenv("TUM_ENV", "demo")
TUM_BASE_URL: str = (
    "https://demo.campus.tum.de" if TUM_ENV == "demo" else "https://campus.tum.de"
)
TUM_ONLINE_PATH: str = "/DSYSTEM" if TUM_ENV == "demo" else "/tumonline"
DEMO_TUM_USERNAME: str = os.getenv("DEMO_TUM_USERNAME", "ge47lbg").strip()

# ── Encryption ───────────────────────────────────────────────────────────────
FERNET_KEY: str = os.getenv("FERNET_KEY", "")

# ── Session store ────────────────────────────────────────────────────────────
SESSION_STORE_PATH: Path = Path(
    os.getenv("SESSION_STORE_PATH", "./data/sessions")
)

# ── Server ───────────────────────────────────────────────────────────────────
MCP_HOST: str = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT: int = int(os.getenv("MCP_PORT", "8001"))
INTERNAL_MCP_PORT: int = int(os.getenv("INTERNAL_MCP_PORT", "8001"))
INSPECTOR_CLIENT_PORT: int = int(os.getenv("INSPECTOR_CLIENT_PORT", "6274"))
INSPECTOR_PROXY_PORT: int = int(os.getenv("INSPECTOR_PROXY_PORT", "6277"))

# ── External APIs ────────────────────────────────────────────────────────────
EAT_API_BASE: str = "https://tum-dev.github.io/eat-api/en"
NAT_API_BASE: str = "https://api.srv.nat.tum.de/api/v1"
NAVIGATUM_API_BASE: str = "https://nav.tum.de/api"

# ── Rate limiting ────────────────────────────────────────────────────────────
MAX_CONCURRENT_REQUESTS: int = 5
MIN_REQUEST_DELAY: float = 0.5  # seconds between requests to same domain

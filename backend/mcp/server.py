"""WayTum MCP Server — MCP app entry point."""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from config import FERNET_KEY, MCP_HOST, MCP_PORT, SESSION_STORE_PATH

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("waytum")
if not FERNET_KEY:
    logger.warning("FERNET_KEY is not set; auth session persistence will fail")
logger.info("Session store path: %s", SESSION_STORE_PATH)

# ── MCP server ───────────────────────────────────────────────────────────────
mcp = FastMCP(
    "WayTum",
    instructions="TUM campus systems exposed as agent-callable tools",
    host=MCP_HOST,
    port=MCP_PORT,
)

# ── Register all modules ─────────────────────────────────────────────────────
from modules import tumonline, moodle, mensa, navigatum, mvv, matrix, collab, zhs, career, linkedin, professors  # noqa: E402
from modules import auth_tools  # noqa: E402

for mod in [auth_tools, mensa, tumonline, navigatum, mvv, moodle, matrix, collab, zhs, career, linkedin, professors]:
    mod.register(mcp)

logger.info("All modules registered")

def build_app():
    return mcp.streamable_http_app()


app = build_app()


# ── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn  # noqa: E402
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)

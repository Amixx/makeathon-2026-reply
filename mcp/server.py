"""Campus Co-Pilot MCP Server — entry point."""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from config import MCP_HOST, MCP_PORT

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("campus-copilot")

# ── MCP server ───────────────────────────────────────────────────────────────
mcp = FastMCP(
    "Campus Co-Pilot",
    instructions="TUM campus systems exposed as agent-callable tools",
    host=MCP_HOST,
    port=MCP_PORT,
)

# ── Register all modules ─────────────────────────────────────────────────────
from modules import tumonline, moodle, mensa, navigatum, mvv, matrix, collab, zhs  # noqa: E402
from modules import auth_tools  # noqa: E402

for mod in [auth_tools, mensa, tumonline, navigatum, mvv, moodle, matrix, collab, zhs]:
    mod.register(mcp)

logger.info("All modules registered")

# ── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="streamable-http")

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
from modules import tumonline, moodle, mensa, navigatum, mvv, matrix, collab, zhs, career  # noqa: E402
from modules import auth_tools  # noqa: E402

for mod in [auth_tools, mensa, tumonline, navigatum, mvv, moodle, matrix, collab, zhs, career]:
    mod.register(mcp)

logger.info("All modules registered")

# ── Landing page → MCP Inspector ─────────────────────────────────────────────
from starlette.responses import HTMLResponse  # noqa: E402
from starlette.routing import Route  # noqa: E402


def _landing(request):
    server_url = f"{request.url.scheme}://{request.url.netloc}/mcp"
    inspector_url = f"https://inspector.tools.modelcontextprotocol.io/?serverUrl={server_url}&transportType=streamableHttp"
    return HTMLResponse(
        f'<html><head><meta http-equiv="refresh" content="0;url={inspector_url}"></head>'
        f'<body>Redirecting to <a href="{inspector_url}">MCP Inspector</a>…</body></html>'
    )


# ── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = mcp.streamable_http_app()
    app.routes.insert(0, Route("/", _landing))

    import uvicorn  # noqa: E402
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)

"""Public HTTP gateway exposing Inspector at /, MCP at /mcp, agent at /agent, and frontend at /app."""

import html
import os
from pathlib import Path

import httpx
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, RedirectResponse, Response, StreamingResponse
from starlette.routing import Route

from config import INSPECTOR_CLIENT_PORT, INSPECTOR_PROXY_PORT, INTERNAL_AGENT_PORT, INTERNAL_MCP_PORT

FRONTEND_DIST = Path("/app/frontend-dist")
PROTOTYPE_DIR = Path("/app/prototype")
MCP_DOCS_TEMPLATE = Path(__file__).resolve().parent / "mcp" / "docs_template.html"

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


async def _close_upstream(upstream: httpx.Response, client: httpx.AsyncClient) -> None:
    await upstream.aclose()
    await client.aclose()


def _target_url(request: Request, target_base: str) -> str:
    query = f"?{request.url.query}" if request.url.query else ""
    return f"{target_base}{request.url.path}{query}"


def _public_base_url(request: Request) -> str:
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", request.url.netloc))
    return f"{scheme}://{host}"


def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "").lower()
    return "text/html" in accept or "application/xhtml+xml" in accept


async def _serve_mcp_docs(request: Request) -> Response:
    html_text = MCP_DOCS_TEMPLATE.read_text()
    mcp_url = html.escape(f"{_public_base_url(request)}/mcp")
    demo_username = html.escape(os.getenv("DEMO_TUM_USERNAME", "ge47lbg").strip() or "ge47lbg")
    html_text = html_text.replace("__MCP_URL__", mcp_url)
    html_text = html_text.replace("__DEMO_USERNAME__", demo_username)
    return HTMLResponse(html_text)


async def _serve_mcp_entry(request: Request) -> Response:
    mcp_url = html.escape(f"{_public_base_url(request)}/mcp")
    docs_url = html.escape(f"{_public_base_url(request)}/mcp/docs")
    return HTMLResponse(
        f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>WayTum MCP</title>
    <style>
      :root {{
        --bg: #fbfaf7;
        --card: #ffffff;
        --ink: #141925;
        --muted: #5c6171;
        --line: #e6e4dd;
        --accent: #3d78b5;
        --mono: "JetBrains Mono", "SF Mono", Menlo, monospace;
        --sans: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 24px;
        background: linear-gradient(180deg, #f4f3ee 0%, var(--bg) 220px);
        color: var(--ink);
        font-family: var(--sans);
      }}
      .card {{
        width: min(680px, 100%);
        padding: 28px;
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 20px;
        box-shadow: 0 16px 50px rgba(20, 25, 37, 0.05);
      }}
      .eyebrow {{
        font: 700 11px/1 var(--mono);
        letter-spacing: 1.8px;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: 12px;
      }}
      h1 {{
        margin: 0 0 10px;
        font-size: clamp(30px, 6vw, 42px);
        line-height: 1.05;
        letter-spacing: -0.8px;
      }}
      p {{
        margin: 0;
        color: var(--muted);
        line-height: 1.55;
      }}
      .actions {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 18px;
      }}
      a {{
        display: inline-flex;
        align-items: center;
        padding: 10px 13px;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: #fff;
        color: var(--ink);
        text-decoration: none;
        font: 700 12px/1 var(--mono);
      }}
      a:hover {{
        border-color: var(--accent);
        color: var(--accent);
      }}
      code {{
        display: block;
        margin-top: 16px;
        padding: 12px 14px;
        background: #f7f8fb;
        border: 1px solid var(--line);
        border-radius: 14px;
        font: 12px/1.5 var(--mono);
        overflow-wrap: anywhere;
        color: var(--ink);
      }}
    </style>
  </head>
  <body>
    <main class="card">
      <div class="eyebrow">WayTum MCP</div>
      <h1>This endpoint is for MCP clients.</h1>
      <p>
        If you opened <code style="display:inline;padding:0;background:none;border:none;margin:0;">/mcp</code> in a browser, you probably want the docs instead.
        MCP tools should connect to the raw endpoint below over Streamable HTTP.
      </p>
      <div class="actions">
        <a href="{docs_url}">Open docs</a>
      </div>
      <code>{mcp_url}</code>
    </main>
  </body>
</html>"""
    )


async def _proxy_request(request: Request, target_base: str) -> Response:
    body = await request.body()
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
    }
    client = httpx.AsyncClient(
        follow_redirects=False,
        timeout=httpx.Timeout(connect=10.0, read=None, write=60.0, pool=60.0),
    )
    upstream = await client.send(
        client.build_request(
            request.method,
            _target_url(request, target_base),
            headers=headers,
            content=body,
        ),
        stream=True,
    )
    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }
    return StreamingResponse(
        upstream.aiter_raw(),
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
        background=BackgroundTask(_close_upstream, upstream, client),
    )


async def root_redirect(request: Request) -> Response:
    return RedirectResponse(url="/app/", status_code=307)


async def _serve_frontend(request: Request) -> Response:
    """Serve SPA from /app — try the exact file, fall back to index.html."""
    # Strip the /app prefix to get the file path within the dist dir
    rel = request.url.path.removeprefix("/app").lstrip("/")
    candidate = FRONTEND_DIST / rel if rel else None
    if candidate and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(FRONTEND_DIST / "index.html")


async def _serve_prototype(request: Request) -> Response:
    """Serve the static HTML prototype from /prototype."""
    path = request.url.path
    if path == "/prototype":
        return RedirectResponse(url="/prototype/", status_code=308)
    rel = path.removeprefix("/prototype").lstrip("/")
    candidate = PROTOTYPE_DIR / rel if rel else PROTOTYPE_DIR / "index.html"
    if candidate.is_file():
        return FileResponse(candidate)
    return Response(status_code=404)


async def catch_all(request: Request) -> Response:
    path = request.url.path
    if path == "/" and "transport" not in request.query_params:
        return await root_redirect(request)
    if path in {"/mcp", "/mcp/"} and request.method in {"GET", "HEAD"} and _wants_html(request):
        return await _serve_mcp_entry(request)
    if path in {"/mcp/docs", "/mcp/docs/"}:
        return await _serve_mcp_docs(request)
    if path.startswith("/prototype"):
        return await _serve_prototype(request)
    if path.startswith("/app"):
        return await _serve_frontend(request)
    if path.startswith("/agent"):
        return await _proxy_request(request, f"http://127.0.0.1:{INTERNAL_AGENT_PORT}")
    if path.startswith("/mcp"):
        if "url" in request.query_params or "transportType" in request.query_params:
            return await _proxy_request(request, f"http://127.0.0.1:{INSPECTOR_PROXY_PORT}")
        return await _proxy_request(request, f"http://127.0.0.1:{INTERNAL_MCP_PORT}")
    if (
        path.startswith("/message")
        or path.startswith("/sse")
        or path.startswith("/config")
        or path.startswith("/health")
        or path.startswith("/fetch")
        or path.startswith("/sandbox")
        or path.startswith("/register")
        or path.startswith("/authorize")
        or path.startswith("/token")
        or path.startswith("/.well-known")
    ):
        return await _proxy_request(request, f"http://127.0.0.1:{INSPECTOR_PROXY_PORT}")
    return await _proxy_request(request, f"http://127.0.0.1:{INSPECTOR_CLIENT_PORT}")


app = Starlette(
    debug=False,
    routes=[Route("/{path:path}", catch_all, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])],
)

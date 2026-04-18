"""Public HTTP gateway exposing Inspector at / and MCP at /mcp."""

from urllib.parse import urlencode

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route

from config import (
    INSPECTOR_CLIENT_PORT,
    INSPECTOR_PROXY_PORT,
    INTERNAL_MCP_PORT,
)

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


async def startup() -> None:
    app.state.client = httpx.AsyncClient(follow_redirects=False, timeout=60.0)


async def shutdown() -> None:
    await app.state.client.aclose()


def _public_base_url(request: Request) -> str:
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", request.url.netloc))
    return f"{scheme}://{host}"


def _target_url(request: Request, target_base: str) -> str:
    query = f"?{request.url.query}" if request.url.query else ""
    return f"{target_base}{request.url.path}{query}"


async def _proxy_request(request: Request, target_base: str) -> Response:
    body = await request.body()
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
    }
    upstream = await app.state.client.request(
        request.method,
        _target_url(request, target_base),
        headers=headers,
        content=body,
    )
    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )


async def root_redirect(request: Request) -> Response:
    public_base = _public_base_url(request)
    params = dict(request.query_params)
    params["transport"] = "streamable-http"
    params["serverUrl"] = f"{public_base}/mcp"
    params["MCP_PROXY_FULL_ADDRESS"] = public_base
    return RedirectResponse(url=f"/?{urlencode(params)}", status_code=307)


async def catch_all(request: Request) -> Response:
    path = request.url.path
    if path == "/" and "transport" not in request.query_params:
        return await root_redirect(request)
    if path.startswith("/mcp"):
        return await _proxy_request(request, f"http://127.0.0.1:{INTERNAL_MCP_PORT}")
    if path.startswith("/message") or path.startswith("/sse"):
        return await _proxy_request(request, f"http://127.0.0.1:{INSPECTOR_PROXY_PORT}")
    return await _proxy_request(request, f"http://127.0.0.1:{INSPECTOR_CLIENT_PORT}")


app = Starlette(
    debug=False,
    routes=[Route("/{path:path}", catch_all, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])],
)
app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)

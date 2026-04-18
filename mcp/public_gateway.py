"""Public HTTP gateway exposing Inspector at / and MCP at /mcp."""

from urllib.parse import urlencode

import httpx
from starlette.background import BackgroundTask
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response, StreamingResponse
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


async def _close_upstream(upstream: httpx.Response, client: httpx.AsyncClient) -> None:
    await upstream.aclose()
    await client.aclose()


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
        # The Inspector proxy also uses /mcp, but with query params such as
        # url=... and transportType=.... Route those requests to the Inspector
        # proxy while keeping plain /mcp traffic pointed at the real MCP server.
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
    ):
        return await _proxy_request(request, f"http://127.0.0.1:{INSPECTOR_PROXY_PORT}")
    return await _proxy_request(request, f"http://127.0.0.1:{INSPECTOR_CLIENT_PORT}")


app = Starlette(
    debug=False,
    routes=[Route("/{path:path}", catch_all, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])],
)

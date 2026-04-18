"""Confluence/Collab Wiki tools — REST API via httpx (PAT auth per call)."""

import logging

import httpx
from mcp.server.fastmcp import FastMCP

import mock

logger = logging.getLogger(__name__)

COLLAB_BASE = "https://collab.dvb.bayern"


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def collab_search(query: str, token: str, limit: int = 10) -> dict:
        """Search the TUM Collab Wiki (Confluence) using CQL.
        Requires a Personal Access Token for authentication."""
        if mock.is_demo_mode():
            m = await mock.get_mock("collab", "collab_search", query=query)
            if m is not None:
                return m
        cql = f'text ~ "{query}"'
        url = f"{COLLAB_BASE}/rest/api/content/search"
        params = {"cql": cql, "limit": limit}
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        logger.info("Collab search: cql=%s limit=%d", cql, limit)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 401:
                return {"error": "Authentication failed — check your Personal Access Token."}
            resp.raise_for_status()
            data = resp.json()
            results = [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "type": r["type"],
                    "space": r.get("space", {}).get("key"),
                    "url": f"{COLLAB_BASE}{r.get('_links', {}).get('webui', '')}",
                }
                for r in data.get("results", [])
            ]
            return {"total": data.get("totalSize", len(results)), "results": results}

    @mcp.tool()
    async def collab_get_page(page_id: str, token: str) -> dict:
        """Get a specific Collab Wiki page by ID with its rendered content.
        Requires a Personal Access Token for authentication."""
        if mock.is_demo_mode():
            m = await mock.get_mock("collab", "collab_get_page", page_id=page_id)
            if m is not None:
                return m
        url = f"{COLLAB_BASE}/rest/api/content/{page_id}"
        params = {"expand": "body.view,version,space"}
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        logger.info("Collab get page: %s", page_id)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 401:
                return {"error": "Authentication failed — check your Personal Access Token."}
            if resp.status_code == 404:
                return {"error": f"Page '{page_id}' not found."}
            resp.raise_for_status()
            data = resp.json()
            return {
                "id": data["id"],
                "title": data["title"],
                "type": data["type"],
                "space": data.get("space", {}).get("key"),
                "version": data.get("version", {}).get("number"),
                "body_html": data.get("body", {}).get("view", {}).get("value", ""),
                "url": f"{COLLAB_BASE}{data.get('_links', {}).get('webui', '')}",
            }

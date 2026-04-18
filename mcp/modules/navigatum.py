"""Navigatum tools — campus navigation and room search (public API, no auth)."""

import logging

import httpx
from mcp.server.fastmcp import FastMCP

from config import NAVIGATUM_API_BASE

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def navigatum_search(query: str, limit: int = 10) -> dict:
        """Search TUM campus locations, buildings, and rooms via Navigatum.
        Returns matching locations with coordinates and details."""
        url = f"{NAVIGATUM_API_BASE}/search"
        params = {"q": query, "limit_all": limit}
        logger.info("Navigatum search: %s", params)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    @mcp.tool()
    async def navigatum_get_room(room_id: str) -> dict:
        """Get detailed info about a specific room/location by its Navigatum ID."""
        url = f"{NAVIGATUM_API_BASE}/locations/{room_id}"
        logger.info("Navigatum get room: %s", room_id)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                return {"error": f"Room '{room_id}' not found"}
            resp.raise_for_status()
            return resp.json()

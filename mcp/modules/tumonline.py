"""TUMonline tools — TUM NAT API (public endpoints, no auth needed)."""

import logging

import httpx
from mcp.server.fastmcp import FastMCP

from config import NAT_API_BASE

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def tumonline_search_courses(query: str, limit: int = 10) -> dict:
        """Search TUMonline course catalog. Returns matching courses."""
        url = f"{NAT_API_BASE}/course-catalog/search"
        params = {"q": query, "limit": limit}
        logger.info("Searching courses: %s", params)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return {"error": f"NAT API returned {resp.status_code}", "detail": resp.text[:500]}
            return resp.json()

    @mcp.tool()
    async def tumonline_search_rooms(query: str, limit: int = 10) -> dict:
        """Search for rooms in TUMonline."""
        url = f"{NAT_API_BASE}/rooms"
        params = {"q": query, "limit": limit}
        logger.info("Searching rooms: %s", params)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return {"error": f"NAT API returned {resp.status_code}", "detail": resp.text[:500]}
            return resp.json()

    @mcp.tool()
    async def tumonline_get_semester_info() -> dict:
        """Get information about the current and upcoming semesters."""
        url = f"{NAT_API_BASE}/semesters"
        logger.info("Fetching semester info")
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return {"error": f"NAT API returned {resp.status_code}", "detail": resp.text[:500]}
            return resp.json()

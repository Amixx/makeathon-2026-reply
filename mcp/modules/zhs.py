"""ZHS sports booking tools — browser-automated (requires TUM SSO auth)."""

import logging

from mcp.server.fastmcp import FastMCP

import auth
from config import TUM_ENV

logger = logging.getLogger(__name__)

ZHS_BASE = "https://www.zhs-muenchen.de"


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def zhs_list_courses(category: str = "") -> dict:
        """List available ZHS sports courses. Optionally filter by category.
        NOTE: Partially implemented — scrapes the public course listing."""
        import httpx

        url = f"{ZHS_BASE}/sportarten"
        logger.info("Fetching ZHS courses from %s", url)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        # Basic extraction — returns raw for now
        return {"message": "ZHS course listing fetched. Full parsing in progress.", "url": url}

    @mcp.tool()
    async def zhs_book_slot(user_id: str, course_id: str, slot_id: str, confirm: bool = False) -> dict:
        """Book a ZHS sports slot. Requires prior tum_login.
        Set confirm=True to actually book. Uses demo environment by default.
        NOTE: Stub — implementation in progress."""
        if TUM_ENV == "prod" and not confirm:
            return {"error": "Production booking requires confirm=True flag."}
        ctx = await auth.get_context(user_id)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        await ctx.close()
        return {"error": "Not yet implemented. Booking logic in progress."}

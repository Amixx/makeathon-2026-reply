"""Mensa menu tools — TUM-Dev Eat API (no auth needed)."""

import logging
from datetime import date

import httpx
from mcp.server.fastmcp import FastMCP

from config import EAT_API_BASE

logger = logging.getLogger(__name__)

# Popular canteen IDs
CANTEEN_IDS = {
    "mensa-garching": "Mensa Garching",
    "mensa-arcisstr": "Mensa Arcisstraße",
    "mensa-leopoldstr": "Mensa Leopoldstraße",
    "mensa-lothstr": "Mensa Lothstraße",
    "mensa-pasing": "Mensa Pasing",
    "mensa-weihenstephan": "Mensa Weihenstephan",
    "stucafe-garching": "StuCafé Garching",
    "stucafe-karlstr": "StuCafé Karlstraße",
    "mediziner-mensa": "Mediziner Mensa",
}


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def mensa_list_canteens() -> dict:
        """List available TUM canteens and their IDs."""
        return {"canteens": CANTEEN_IDS}

    @mcp.tool()
    async def mensa_get_menu(
        canteen_id: str = "mensa-garching",
        year: int | None = None,
        week: int | None = None,
    ) -> dict:
        """Get the menu for a TUM canteen for a given week.
        Defaults to current week at Mensa Garching.
        Use mensa_list_canteens to get valid canteen_id values."""
        today = date.today()
        y = year or today.year
        w = week or today.isocalendar()[1]
        url = f"{EAT_API_BASE}/{canteen_id}/{y}/{w:02d}.json"
        logger.info("Fetching menu: %s", url)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                return {"error": f"No menu found for {canteen_id} week {w}/{y}"}
            resp.raise_for_status()
            return resp.json()

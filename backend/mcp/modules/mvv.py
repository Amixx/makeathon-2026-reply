"""Public transport tools — MVG/MVV departures and routing."""

import logging

from mcp.server.fastmcp import FastMCP

import mock

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def mvv_get_departures(station: str, limit: int = 10) -> dict:
        """Get upcoming departures from an MVG station (e.g. 'Garching-Forschungszentrum').
        Returns next departures with line, destination, and time."""
        if mock.is_demo_mode():
            m = await mock.get_mock("mvv", "mvv_get_departures", station=station)
            if m is not None:
                return m
        from mvg import MvgApi

        try:
            station_id = MvgApi.station(station)
            if not station_id:
                return {"error": f"Station '{station}' not found"}
            api = MvgApi(station_id["id"])
            departures = api.departures()
            return {"station": station_id["name"], "departures": departures[:limit]}
        except Exception as e:
            logger.exception("MVV departures failed")
            return {"error": str(e)}

    @mcp.tool()
    async def mvv_search_station(query: str) -> dict:
        """Search for MVG/MVV stations by name."""
        if mock.is_demo_mode():
            m = await mock.get_mock("mvv", "mvv_search_station", query=query)
            if m is not None:
                return m
        from mvg import MvgApi

        try:
            result = MvgApi.station(query)
            if not result:
                return {"error": f"No station found for '{query}'"}
            return {"station": result}
        except Exception as e:
            logger.exception("MVV station search failed")
            return {"error": str(e)}

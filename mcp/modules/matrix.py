"""Matrix chat tools — stub for TUM Matrix integration."""

import logging

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def matrix_send_message(room_id: str, message: str) -> dict:
        """Send a message to a TUM Matrix room.
        NOTE: Stub — requires matrix-nio setup and access token."""
        return {"error": "Not yet implemented. Requires Matrix access token configuration."}

    @mcp.tool()
    async def matrix_list_rooms() -> dict:
        """List joined Matrix rooms.
        NOTE: Stub — requires matrix-nio setup and access token."""
        return {"error": "Not yet implemented. Requires Matrix access token configuration."}

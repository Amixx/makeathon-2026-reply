"""Confluence/Collab Wiki tools — stub for atlassian-python-api integration."""

import logging

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def collab_search(query: str) -> dict:
        """Search the TUM Collab Wiki (Confluence).
        NOTE: Stub — requires Personal Access Token configuration."""
        return {"error": "Not yet implemented. Requires Confluence PAT."}

    @mcp.tool()
    async def collab_get_page(page_id: str) -> dict:
        """Get a specific Collab Wiki page by ID.
        NOTE: Stub — requires Personal Access Token configuration."""
        return {"error": "Not yet implemented. Requires Confluence PAT."}

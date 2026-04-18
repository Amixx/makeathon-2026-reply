"""LinkedIn people search — demo-only stub.

Real LinkedIn access requires partner API credentials or a paid lookup
service. For the hackathon demo this module returns curated mock contacts
so the agent can reason about "who to reach out to" realistically.

Contract matches the other MCP modules: register(mcp) exports @mcp.tool()
functions that honor demo mode via mock.get_mock(...).
"""

import logging

from mcp.server.fastmcp import FastMCP

import mock

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def linkedin_search_people(
        query: str,
        limit: int = 5,
        open_to_chat_only: bool = False,
    ) -> dict:
        """Search LinkedIn for people relevant to a career direction.

        Use this to find alumni, lab members, or industry professionals the
        student could reach out to for a 20-minute coffee/informational chat.

        query: free-text describing the target (e.g. "TUM Bio-CS alumni in
               computational neuroscience", "BrainLab AG ML engineer",
               "Gjorgjieva lab PhD").
        limit: max results.
        open_to_chat_only: if True, only return contacts marked as open
                           to student outreach.
        """
        if mock.is_demo_mode():
            m = mock.get_mock("linkedin", "linkedin_search_people", query=query)
            if m is not None:
                if open_to_chat_only and isinstance(m, dict) and "people" in m:
                    filtered = [p for p in m["people"] if p.get("open_to_chat")]
                    return {"count": len(filtered[:limit]), "people": filtered[:limit]}
                if isinstance(m, dict) and "people" in m:
                    return {"count": len(m["people"][:limit]), "people": m["people"][:limit]}
                return m
        return {
            "error": (
                "linkedin_search_people requires demo mode or a configured "
                "LinkedIn lookup provider. Enable demo mode with set_demo_mode."
            )
        }

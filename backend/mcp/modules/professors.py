"""TUM professor / Fachbereich lookup tools — mock data backed."""

import logging

from mcp.server.fastmcp import FastMCP

import mock

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def professors_list_fachbereiche() -> dict:
        """List all TUM Fachbereiche (research departments / subject areas).
        Useful for discovering which fields of study and research groups exist at TUM."""
        m = await mock.get_mock("professors", "fachbereiche")
        if m is not None:
            return {"fachbereiche": m}
        return {"error": "No data available."}

    @mcp.tool()
    async def professors_search(query: str) -> dict:
        """Search for TUM professors by name, Fachbereich, or research area.
        Returns matching professors with their department and research focus.
        The query is matched case-insensitively against professor names,
        Fachbereich names, and Bereich (research area) descriptions."""
        m = await mock.get_mock("professors", "profs")
        if m is None:
            return {"error": "No data available."}

        q = query.lower()
        results = []
        for fachbereich, profs in m.items():
            for prof in profs:
                if (
                    q in prof["name"].lower()
                    or q in prof["bereich"].lower()
                    or q in fachbereich.lower()
                ):
                    results.append(
                        {
                            "name": prof["name"],
                            "fachbereich": fachbereich,
                            "bereich": prof["bereich"],
                        }
                    )
        return {"total": len(results), "results": results}

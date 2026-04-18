"""MCP tools for TUM SSO authentication + demo-mode toggle."""

import logging

from mcp.server.fastmcp import FastMCP

import auth
import mock

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def set_demo_mode(enabled: bool) -> dict:
        """Toggle demo mode on/off. When enabled, tools return curated mock
        data instead of hitting real APIs. Use this during live demos to
        guarantee polished responses. Call with enabled=False to switch
        back to real data."""
        mock.set_demo_mode(enabled)
        return {
            "demo_mode": enabled,
            "message": f"Demo mode {'enabled — tools will return mock data' if enabled else 'disabled — tools will use real APIs'}",
        }

    @mcp.tool()
    async def get_demo_mode() -> dict:
        """Check whether demo mode is currently active."""
        return {"demo_mode": mock.is_demo_mode()}

    @mcp.tool()
    async def tum_login(username: str, password: str) -> dict:
        """Log in to TUM systems via SSO. Credentials are used once and never stored.
        Returns {"success": true/false, "message": "..."}."""
        logger.info("tum_login called for username=%s (password redacted)", username)
        ok, message = await auth.login(username, password)
        if ok:
            return {"success": True, "message": message}
        return {"success": False, "message": message}

    @mcp.tool()
    async def tum_session_status(username: str) -> dict:
        """Check if the stored TUM session for a user is still valid.
        Returns {"valid": true/false}."""
        valid = await auth.is_session_valid(username)
        return {"valid": valid}

    @mcp.tool()
    async def tum_logout(username: str) -> dict:
        """Delete stored TUM session for a user."""
        await auth.logout(username)
        return {"success": True, "message": "Session deleted."}

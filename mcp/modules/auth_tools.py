"""MCP tools for TUM SSO authentication."""

import logging

from mcp.server.fastmcp import FastMCP

import auth

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def tum_login(username: str, password: str) -> dict:
        """Log in to TUM systems via SSO. Credentials are used once and never stored.
        Returns {"success": true/false, "message": "..."}."""
        logger.info("tum_login called for username=%s (password redacted)", username)
        ok = await auth.login(username, password)
        if ok:
            return {"success": True, "message": "Logged in successfully. Session saved."}
        return {"success": False, "message": "Login failed. Check credentials and try again."}

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

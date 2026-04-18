"""MCP tools for TUM SSO authentication."""

import logging

from mcp.server.fastmcp import FastMCP

import auth

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def tum_login(user_id: str, username: str, password: str) -> dict:
        """Log in to TUM systems via SSO. Credentials are used once and never stored.
        Returns {"success": true/false, "message": "..."}."""
        logger.info("tum_login called for user_id=%s (password redacted)", user_id)
        ok = await auth.login(user_id, username, password)
        if ok:
            return {"success": True, "message": "Logged in successfully. Session saved."}
        return {"success": False, "message": "Login failed. Check credentials and try again."}

    @mcp.tool()
    async def tum_session_status(user_id: str) -> dict:
        """Check if the stored TUM session for a user is still valid.
        Returns {"valid": true/false}."""
        valid = await auth.is_session_valid(user_id)
        return {"valid": valid}

    @mcp.tool()
    async def tum_logout(user_id: str) -> dict:
        """Delete stored TUM session for a user."""
        await auth.logout(user_id)
        return {"success": True, "message": "Session deleted."}

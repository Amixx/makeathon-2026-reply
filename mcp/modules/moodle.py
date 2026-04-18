"""Moodle tools — browser-automated access (requires TUM SSO auth)."""

import logging

from mcp.server.fastmcp import FastMCP

import auth

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def moodle_list_courses(username: str) -> dict:
        """List the user's enrolled Moodle courses. Requires prior tum_login.
        NOTE: Stub — implementation in progress."""
        ctx = await auth.get_context(username)
        if ctx is None:
            return {"error": "No active session. Call tum_login first."}
        try:
            page = await ctx.new_page()
            await page.goto("https://www.moodle.tum.de/my/", wait_until="networkidle", timeout=30_000)
            # Extract course list from DOM
            courses = await page.eval_on_selector_all(
                ".course-listitem, .coursebox",
                "els => els.map(e => ({name: e.querySelector('.coursename, .course-title')?.textContent?.trim(), url: e.querySelector('a')?.href}))"
            )
            return {"courses": courses}
        except Exception as e:
            logger.exception("Moodle list_courses failed")
            return {"error": str(e)}
        finally:
            await ctx.close()

    @mcp.tool()
    async def moodle_list_assignments(username: str) -> dict:
        """List upcoming Moodle assignments. Requires prior tum_login.
        NOTE: Stub — implementation in progress."""
        return {"error": "Not yet implemented. Coming soon."}

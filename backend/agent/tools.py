"""Tool implementations + Anthropic Messages API tool declarations.

Loads tools from:
  1. Local tools defined here (load_courses)
  2. Remote MCP server tools (fetched at startup)
"""

import asyncio
import concurrent.futures
import json
import logging
from pathlib import Path

import yaml

from config import MCP_URL
from render import render_prompt

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent / "data"
_PROFILE_PATH = _DATA_DIR / "user_profile.yaml"


# ── Local tools ──────────────────────────────────────────────────────────────

def load_courses() -> str:
    """Student's enrolled courses (from the local demo profile)."""
    profile = yaml.safe_load(_PROFILE_PATH.read_text())
    return render_prompt(
        "courses.j2",
        semester=profile.get("semester", ""),
        enrolled=profile.get("enrolled", []),
        available=profile.get("available", []),
    )


# ── MCP tool bridge ─────────────────────────────────────────────────────────

def _call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call an MCP tool via the MCP client library (sync wrapper)."""
    async def _do():
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(MCP_URL) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                parts = []
                for block in result.content:
                    if hasattr(block, "text"):
                        parts.append(block.text)
                    else:
                        parts.append(str(block))
                return "\n".join(parts)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        return pool.submit(lambda: asyncio.run(_do())).result(timeout=60)


def _fetch_mcp_tools() -> tuple[dict, list]:
    """Fetch tool list from MCP server, return (tools_dict, tool_decls)."""
    tools: dict = {}
    decls: list = []

    async def _do():
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(MCP_URL) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return result.tools

    try:
        mcp_tools = asyncio.run(asyncio.wait_for(_do(), timeout=10))
    except Exception as e:
        logger.warning("Could not connect to MCP server at %s: %s", MCP_URL, e)
        return tools, decls

    for t in mcp_tools:
        name = t.name

        def make_wrapper(tool_name):
            def wrapper(**kwargs):
                return _call_mcp_tool(tool_name, kwargs)
            return wrapper

        tools[name] = make_wrapper(name)
        decls.append({
            "name": name,
            "description": t.description or "",
            "input_schema": t.inputSchema if t.inputSchema else {"type": "object", "properties": {}},
        })

    logger.info("Loaded %d MCP tools: %s", len(tools), list(tools.keys()))
    return tools, decls


# ── Build combined tool registry ─────────────────────────────────────────────

_LOAD_COURSES_DECL = {
    "name": "load_courses",
    "description": (
        "Load the student's enrolled courses this semester and a list "
        "of courses they are eligible to take next. Returns Markdown. "
        "Call this whenever the user asks about their studies, picking "
        "courses, or career planning that depends on coursework."
    ),
    "input_schema": {"type": "object", "properties": {}},
}

# Baseline chat toolkit — just local tools.
TOOLS: dict = {"load_courses": load_courses}
TOOL_DECLS: list = [_LOAD_COURSES_DECL]

# Plan subagent toolkit — local + everything from the MCP server.
_mcp_tools, _mcp_decls = _fetch_mcp_tools()
PLAN_TOOLS: dict = {"load_courses": load_courses, **_mcp_tools}
PLAN_TOOL_DECLS: list = [_LOAD_COURSES_DECL, *_mcp_decls]

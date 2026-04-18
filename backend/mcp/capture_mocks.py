#!/usr/bin/env python3
"""Capture real tool responses and save them as mock JSON files.

Calls every MCP tool with sample arguments, saves the response to
data/mock/{module}/{tool_name}.json. Skips tools that already have
a mock file (won't overwrite).

Usage:
    python capture_mocks.py              # capture all
    python capture_mocks.py --force      # overwrite existing mocks
    python capture_mocks.py --only mensa # only capture one module
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)
logger = logging.getLogger("capture_mocks")

MOCK_DIR = Path(__file__).parent / "data" / "mock"

# ── Tool definitions: (module, tool_name, kwargs) ────────────────────────────
# Tools requiring auth or that are destructive are marked with skip=True.
# Add new tools here as you implement them.

TOOLS: list[dict] = [
    # ── mensa ──
    {"module": "mensa", "tool": "mensa_list_canteens", "kwargs": {}},
    {"module": "mensa", "tool": "mensa_get_menu", "kwargs": {"canteen_id": "mensa-garching"}},

    # ── career ──
    {"module": "career", "tool": "career_list_jobs", "kwargs": {"keyword": "", "limit": 10}},
    {"module": "career", "tool": "career_list_events", "kwargs": {"keyword": "", "limit": 10}},
    # career_get_job needs a real URL from career_list_jobs — handled in post-capture

    # ── tumonline (public) ──
    {"module": "tumonline", "tool": "tumonline_search_courses", "kwargs": {"query": "machine learning", "limit": 5}},
    {"module": "tumonline", "tool": "tumonline_search_rooms", "kwargs": {"query": "MI", "limit": 5}},
    {"module": "tumonline", "tool": "tumonline_get_semester_info", "kwargs": {}},
    {"module": "tumonline", "tool": "tumonline_get_course", "kwargs": {"course_id": 950877768}},
    {"module": "tumonline", "tool": "tumonline_get_module", "kwargs": {"module_code": "IN2346"}},
    {"module": "tumonline", "tool": "tumonline_search_programs", "kwargs": {"query": "Informatics", "limit": 5}},
    {"module": "tumonline", "tool": "tumonline_list_module_catalogs", "kwargs": {"query": "Informatics"}},
    # tumonline_list_program_modules needs a real catalog_tag — handled in post-capture

    # ── tumonline (auth-required) ──
    {"module": "tumonline", "tool": "tumonline_my_courses", "skip": True, "reason": "requires tum_login"},
    {"module": "tumonline", "tool": "tumonline_register_course", "skip": True, "reason": "destructive + requires auth"},
    {"module": "tumonline", "tool": "tumonline_register_exam", "skip": True, "reason": "destructive + requires auth"},

    # ── navigatum ──
    {"module": "navigatum", "tool": "navigatum_search", "kwargs": {"query": "Garching Forschungszentrum", "limit": 5}},
    {"module": "navigatum", "tool": "navigatum_get_room", "kwargs": {"room_id": "5602.EG.001"}},

    # ── mvv ──
    {"module": "mvv", "tool": "mvv_get_departures", "kwargs": {"station": "Garching-Forschungszentrum", "limit": 5}},
    {"module": "mvv", "tool": "mvv_search_station", "kwargs": {"query": "Garching"}},

    # ── moodle (auth-required) ──
    {"module": "moodle", "tool": "moodle_list_courses", "skip": True, "reason": "requires tum_login"},
    {"module": "moodle", "tool": "moodle_list_assignments", "skip": True, "reason": "requires tum_login"},
    {"module": "moodle", "tool": "moodle_list_grades", "skip": True, "reason": "requires tum_login"},

    # ── zhs ──
    {"module": "zhs", "tool": "zhs_list_sports", "kwargs": {"category": ""}},
    {"module": "zhs", "tool": "zhs_list_slots", "skip": True, "reason": "needs sport_url from zhs_list_sports"},
    {"module": "zhs", "tool": "zhs_book_slot", "skip": True, "reason": "destructive + requires auth"},

    # ── matrix (stubs) ──
    {"module": "matrix", "tool": "matrix_list_rooms", "kwargs": {}},
    {"module": "matrix", "tool": "matrix_send_message", "skip": True, "reason": "destructive stub"},

    # ── collab (stubs) ──
    {"module": "collab", "tool": "collab_search", "kwargs": {"query": "TUM"}},
    {"module": "collab", "tool": "collab_get_page", "skip": True, "reason": "needs page_id"},
]


async def capture_one(tool_entry: dict, mcp_tools: dict, force: bool) -> str:
    """Capture a single tool. Returns status string."""
    module = tool_entry["module"]
    name = tool_entry["tool"]
    tag = f"{module}/{name}"

    if tool_entry.get("skip"):
        return f"⏭  {tag}: skipped ({tool_entry.get('reason', 'no reason')})"

    out_path = MOCK_DIR / module / f"{name}.json"
    if out_path.exists() and not force:
        return f"⏩ {tag}: already exists, skipping"

    if name not in mcp_tools:
        return f"❌ {tag}: tool not registered in MCP"

    tool = mcp_tools[name]
    kwargs = tool_entry.get("kwargs", {})

    try:
        result = await tool.run(kwargs)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n")
        return f"✅ {tag}: captured ({out_path.stat().st_size} bytes)"
    except Exception as e:
        return f"❌ {tag}: {e}"


async def main(force: bool, only: str | None):
    # Ensure demo mode is OFF so we get real data
    import mock as mock_mod
    mock_mod.set_demo_mode(False)

    # Import server to get all tools registered
    import server  # noqa: F401
    mcp_tools = server.mcp._tool_manager._tools

    logger.info("Registered tools: %s", ", ".join(sorted(mcp_tools.keys())))

    entries = TOOLS
    if only:
        entries = [t for t in entries if t["module"] == only]
        if not entries:
            logger.error("No tools found for module '%s'", only)
            sys.exit(1)

    results = []
    for entry in entries:
        status = await capture_one(entry, mcp_tools, force)
        results.append(status)
        print(status)

    print(f"\nDone: {len(results)} tools processed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture real MCP tool responses as mock data")
    parser.add_argument("--force", action="store_true", help="Overwrite existing mock files")
    parser.add_argument("--only", type=str, help="Only capture tools from this module")
    args = parser.parse_args()
    asyncio.run(main(force=args.force, only=args.only))

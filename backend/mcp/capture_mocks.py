#!/usr/bin/env python3
"""Capture real tool responses and save them as mock JSON files.

Calls every MCP tool with sample arguments, saves the response to
data/mock/{module}/{tool_name}.json. Skips tools that already have
a mock file (won't overwrite).

Logs in with TUM_USERNAME / TUM_PASSWORD from .env to capture
auth-required tools too. Destructive tools are always skipped.

Usage:
    python capture_mocks.py              # capture all
    python capture_mocks.py --force      # overwrite existing mocks
    python capture_mocks.py --only mensa # only capture one module
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)
logger = logging.getLogger("capture_mocks")

MOCK_DIR = Path(__file__).parent / "data" / "mock"
USERNAME = os.getenv("TUM_USERNAME", "")
PASSWORD = os.getenv("TUM_PASSWORD", "")


MAX_LIST_ITEMS = 20
MAX_STR_CHARS = 4000


def _truncate(obj, depth: int = 0):
    """Recursively truncate lists to MAX_LIST_ITEMS and long strings to MAX_STR_CHARS."""
    if isinstance(obj, list):
        truncated = [_truncate(item, depth + 1) for item in obj[:MAX_LIST_ITEMS]]
        if len(obj) > MAX_LIST_ITEMS:
            truncated.append({"_truncated": f"{len(obj) - MAX_LIST_ITEMS} more items omitted"})
        return truncated
    if isinstance(obj, dict):
        return {k: _truncate(v, depth + 1) for k, v in obj.items()}
    if isinstance(obj, str) and len(obj) > MAX_STR_CHARS:
        return obj[:MAX_STR_CHARS] + f"… [{len(obj) - MAX_STR_CHARS} chars truncated]"
    return obj


def build_tools_list(username: str) -> list[dict]:
    """Build the list of tools to capture. Uses username for auth tools."""
    return [
        # ── mensa ──
        {"module": "mensa", "tool": "mensa_list_canteens", "kwargs": {}},
        {"module": "mensa", "tool": "mensa_get_menu", "kwargs": {"canteen_id": "mensa-garching"}},

        # ── career ──
        {"module": "career", "tool": "career_list_jobs", "kwargs": {"keyword": "", "limit": 10}},
        {"module": "career", "tool": "career_list_events", "kwargs": {"keyword": "", "limit": 10}},
        {"module": "career", "tool": "career_get_job", "skip": True, "reason": "needs real job URL from career_list_jobs"},
        {"module": "career", "tool": "career_audit_cv", "kwargs": {"cv_text": "Max Mustermann\nmax.mustermann@tum.de\nB.Sc. Informatics, TUM\nExperience: Software Engineer Intern at Siemens 2025\nSkills: Python, Java, Machine Learning\nGitHub: github.com/maxmuster"}},
        {"module": "career", "tool": "career_github_audit", "kwargs": {"username": "torvalds"}},
        {"module": "career", "tool": "career_skills_from_courses", "kwargs": {"courses": [{"title": "Introduction to Machine Learning"}, {"title": "Database Systems"}, {"title": "Computer Networks"}]}},

        # ── tumonline (public) ──
        {"module": "tumonline", "tool": "tumonline_search_courses", "kwargs": {"query": "machine learning", "limit": 5}},
        {"module": "tumonline", "tool": "tumonline_search_rooms", "kwargs": {"query": "MI", "limit": 5}},
        {"module": "tumonline", "tool": "tumonline_get_semester_info", "kwargs": {}},
        {"module": "tumonline", "tool": "tumonline_get_course", "kwargs": {"course_id": 950877768}},
        {"module": "tumonline", "tool": "tumonline_get_module", "kwargs": {"module_code": "IN2346"}},
        {"module": "tumonline", "tool": "tumonline_search_programs", "kwargs": {"query": "Informatics", "limit": 5}},
        {"module": "tumonline", "tool": "tumonline_list_module_catalogs", "kwargs": {"query": "Informatics"}},
        {"module": "tumonline", "tool": "tumonline_get_room_schedule", "kwargs": {"room_code": "5606.EG.011"}},

        # ── tumonline (auth-required, read-only) ──
        {"module": "tumonline", "tool": "tumonline_my_courses", "kwargs": {"username": username}, "auth": True},
        {"module": "tumonline", "tool": "tumonline_my_exams", "kwargs": {"username": username}, "auth": True},

        # ── tumonline (destructive — always skip) ──
        {"module": "tumonline", "tool": "tumonline_register_course", "skip": True, "reason": "destructive"},
        {"module": "tumonline", "tool": "tumonline_register_exam", "skip": True, "reason": "destructive"},

        # ── navigatum ──
        {"module": "navigatum", "tool": "navigatum_search", "kwargs": {"query": "Garching Forschungszentrum", "limit": 5}},
        {"module": "navigatum", "tool": "navigatum_get_room", "kwargs": {"room_id": "5602.EG.001"}},

        # ── mvv ──
        {"module": "mvv", "tool": "mvv_get_departures", "kwargs": {"station": "Garching-Forschungszentrum", "limit": 5}},
        {"module": "mvv", "tool": "mvv_search_station", "kwargs": {"query": "Garching"}},

        # ── moodle (auth-required, read-only) ──
        {"module": "moodle", "tool": "moodle_list_courses", "kwargs": {"username": username}, "auth": True},
        {"module": "moodle", "tool": "moodle_list_assignments", "kwargs": {"username": username}, "auth": True},
        {"module": "moodle", "tool": "moodle_list_grades", "kwargs": {"username": username}, "auth": True},
        {"module": "moodle", "tool": "moodle_get_course_content", "skip": True, "reason": "needs course_url from moodle_list_courses"},
        {"module": "moodle", "tool": "moodle_fetch_resource_text", "skip": True, "reason": "needs resource_url from moodle_get_course_content"},

        # ── zhs ──
        {"module": "zhs", "tool": "zhs_list_sports", "kwargs": {"category": ""}},
        {"module": "zhs", "tool": "zhs_list_slots", "skip": True, "reason": "needs sport_url from zhs_list_sports"},
        {"module": "zhs", "tool": "zhs_book_slot", "skip": True, "reason": "destructive"},

        # ── matrix (stubs) ──
        {"module": "matrix", "tool": "matrix_list_rooms", "kwargs": {}},
        {"module": "matrix", "tool": "matrix_send_message", "skip": True, "reason": "destructive stub"},

        # ── collab (stubs) ──
        {"module": "collab", "tool": "collab_search", "kwargs": {"query": "TUM"}},
        {"module": "collab", "tool": "collab_get_page", "skip": True, "reason": "needs page_id"},
    ]


async def capture_one(tool_entry: dict, mcp_tools: dict, force: bool) -> tuple[str, bool]:
    """Capture a single tool. Returns (status_string, success)."""
    module = tool_entry["module"]
    name = tool_entry["tool"]
    tag = f"{module}/{name}"

    if tool_entry.get("skip"):
        return f"⏭  {tag}: skipped ({tool_entry.get('reason', '')})", True

    out_path = MOCK_DIR / module / f"{name}.json"
    if out_path.exists() and not force:
        return f"⏩ {tag}: mock exists, skipping", True

    if name not in mcp_tools:
        return f"❌ {tag}: tool not registered in MCP", False

    tool = mcp_tools[name]
    kwargs = tool_entry.get("kwargs", {})

    try:
        result = await tool.run(kwargs)
        # Check for error responses — save them anyway so there's a mock file,
        # but warn. Not counted as failure (stubs legitimately return errors).
        if isinstance(result, dict) and "error" in result:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n")
            return f"⚠️  {tag}: tool returned error (saved anyway): {result['error'][:100]}", True
        result = _truncate(result)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n")
        size = out_path.stat().st_size
        return f"✅ {tag}: captured ({size} bytes)", True
    except Exception as e:
        return f"❌ {tag}: {e}", False


async def login_if_needed(mcp_tools: dict) -> bool:
    """Log in via tum_login tool if credentials are available."""
    if not USERNAME or not PASSWORD:
        logger.warning("TUM_USERNAME / TUM_PASSWORD not in .env — auth tools will be skipped")
        return False

    logger.info("Logging in as %s ...", USERNAME)
    login_tool = mcp_tools.get("tum_login")
    if not login_tool:
        logger.error("tum_login tool not found")
        return False

    result = await login_tool.run({"username": USERNAME, "password": PASSWORD})
    if isinstance(result, dict) and result.get("success"):
        logger.info("✅ Login successful")
        return True
    else:
        msg = result.get("message", result) if isinstance(result, dict) else result
        logger.error("❌ Login failed: %s", msg)
        return False


async def main(force: bool, only: str | None):
    # Ensure demo mode is OFF so we get real data
    import mock as mock_mod
    mock_mod.set_demo_mode(False)

    # Import server to get all tools registered
    import server  # noqa: F401
    mcp_tools = server.mcp._tool_manager._tools

    logger.info("Registered tools: %s", ", ".join(sorted(mcp_tools.keys())))

    # Log in for auth-required tools
    logged_in = await login_if_needed(mcp_tools)

    entries = build_tools_list(USERNAME)
    if only:
        entries = [t for t in entries if t["module"] == only]
        if not entries:
            logger.error("No tools found for module '%s'", only)
            sys.exit(1)

    # Skip auth-required tools if login failed
    if not logged_in:
        for e in entries:
            if e.get("auth") and not e.get("skip"):
                e["skip"] = True
                e["reason"] = "login failed — skipping auth tool"

    # Split into parallel groups: public tools can run concurrently,
    # auth tools run concurrently in a separate batch (shared session)
    public = [e for e in entries if not e.get("auth")]
    authed = [e for e in entries if e.get("auth") and not e.get("skip")]
    skipped = [e for e in entries if e.get("skip")]

    results = []
    failed = 0

    # Run skipped first (instant)
    for e in skipped:
        status, _ = await capture_one(e, mcp_tools, force)
        results.append(status)
        print(status)

    # Run public tools in parallel
    if public:
        logger.info("Capturing %d public tools in parallel...", len(public))
        batch = await asyncio.gather(
            *(capture_one(e, mcp_tools, force) for e in public),
            return_exceptions=True,
        )
        for item in batch:
            if isinstance(item, Exception):
                status, ok = f"❌ exception: {item}", False
            else:
                status, ok = item
            if not ok:
                failed += 1
            results.append(status)
            print(status)

    # Run auth tools in parallel
    if authed:
        logger.info("Capturing %d auth tools in parallel...", len(authed))
        batch = await asyncio.gather(
            *(capture_one(e, mcp_tools, force) for e in authed),
            return_exceptions=True,
        )
        for item in batch:
            if isinstance(item, Exception):
                status, ok = f"❌ exception: {item}", False
            else:
                status, ok = item
            if not ok:
                failed += 1
            results.append(status)
            print(status)

    print(f"\nDone: {len(results)} tools, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture real MCP tool responses as mock data")
    parser.add_argument("--force", action="store_true", help="Overwrite existing mock files")
    parser.add_argument("--only", type=str, help="Only capture tools from this module")
    args = parser.parse_args()
    asyncio.run(main(force=args.force, only=args.only))

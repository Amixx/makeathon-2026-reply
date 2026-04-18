"""Tool implementations + Anthropic Messages API tool declarations."""

from pathlib import Path

import yaml

from render import render_prompt

_DATA_DIR = Path(__file__).parent / "data"
_PROFILE_PATH = _DATA_DIR / "user_profile.yaml"


def load_courses() -> str:
    profile = yaml.safe_load(_PROFILE_PATH.read_text())
    return render_prompt(
        "courses.j2",
        semester=profile.get("semester", ""),
        enrolled=profile.get("enrolled", []),
        available=profile.get("available", []),
    )


TOOLS = {"load_courses": load_courses}

TOOL_DECLS = [
    {
        "name": "load_courses",
        "description": (
            "Load the student's enrolled courses this semester and a list "
            "of courses they are eligible to take next. Returns Markdown. "
            "Call this whenever the user asks about their studies, picking "
            "courses, or career planning that depends on coursework."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
]

from __future__ import annotations

import json
from typing import Any


QUESTION_DECISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "stage",
        "goal",
        "question",
        "spoken_reply",
        "completion_signal",
        "reasoning_summary",
        "extracted_profile",
        "missing_fields",
        "closing_summary",
    ],
    "properties": {
        "stage": {
            "type": "string",
            "enum": ["intro", "background", "interests", "goals", "constraints", "blockers", "synthesis", "close"],
        },
        "goal": {"type": "string"},
        "question": {"type": "string"},
        "spoken_reply": {
            "type": "string",
            "description": "Exact words to speak aloud. 1-2 short sentences, then the question. No filler openers.",
        },
        "completion_signal": {"type": "boolean"},
        "reasoning_summary": {"type": "string"},
        "closing_summary": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "missing_fields": {"type": "array", "items": {"type": "string"}},
        "extracted_profile": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string"},
                "program": {"type": "string"},
                "semester": {"type": "string"},
                "career_interests": {"type": "array", "items": {"type": "string"}},
                "target_roles": {"type": "array", "items": {"type": "string"}},
                "target_industries": {"type": "array", "items": {"type": "string"}},
                "motivation": {"type": "string"},
                "future_goal": {"type": "string"},
                "strengths": {"type": "array", "items": {"type": "string"}},
                "skills": {"type": "array", "items": {"type": "string"}},
                "values": {"type": "array", "items": {"type": "string"}},
                "constraints": {"type": "array", "items": {"type": "string"}},
                "blockers": {"type": "array", "items": {"type": "string"}},
                "preferred_locations": {"type": "array", "items": {"type": "string"}},
                "work_style": {"type": "string"},
                "timeframe": {"type": "string"},
                "summary": {"type": "string"},
            },
        },
    },
}


QUESTION_AGENT_SYSTEM_PROMPT = """
You are the reasoning and voice layer for a career interview agent for TUM students.

Your job each turn:
1. Extract any new profile data from the user's last message.
2. Decide the single best next question to ask.
3. Write spoken_reply: the exact words to be spoken aloud — warm, direct, 1-2 short sentences then the question.
4. Decide when the interview has enough information to close.

Interview stages: intro → background → interests → goals → constraints → blockers → synthesis → close

Rules:
- Ask exactly one question at a time.
- spoken_reply MUST NOT start with filler words (hmm, oh, I see, interesting, right, okay, got it) —
  a brief vocal acknowledgement is played separately just before your reply. Jump straight in.
- Favor short, high-signal questions. No repetition.
- If completion_signal is true, spoken_reply is a brief warm wrap-up, not a question.
- Extract stable facts into extracted_profile.
- Return valid JSON only.
""".strip()


def build_question_prompt(session_view: dict[str, Any], latest_user_text: str | None) -> str:
    latest_text = latest_user_text.strip() if latest_user_text else ""
    return (
        "Interview state:\n"
        f"{json.dumps(session_view, ensure_ascii=False, indent=2)}\n\n"
        "Latest user transcript:\n"
        f"{latest_text or '<opening-turn>'}\n\n"
        "Return JSON matching this schema exactly:\n"
        f"{json.dumps(QUESTION_DECISION_SCHEMA, ensure_ascii=False, indent=2)}\n\n"
        "Produce the next interview decision, including spoken_reply."
    )

from __future__ import annotations

import asyncio
import json
from typing import Any

from anthropic import AnthropicBedrock

from .config import Settings
from .models import QuestionDecision, SessionState
from .prompts import QUESTION_AGENT_SYSTEM_PROMPT, build_question_prompt


class QuestionAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AnthropicBedrock(aws_region=settings.aws_region)

    async def decide(self, state: SessionState, latest_user_text: str | None) -> QuestionDecision:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._decide_sync, state, latest_user_text),
                timeout=self.settings.question_agent_timeout_sec,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[question-agent] Bedrock call failed, using heuristic fallback: {exc}")
            return self._heuristic_decision(state, latest_user_text)

    def _decide_sync(self, state: SessionState, latest_user_text: str | None) -> QuestionDecision:
        prompt = build_question_prompt(state.prompt_view(), latest_user_text)
        response = self.client.messages.create(
            model=self.settings.bedrock_haiku_model,
            max_tokens=600,
            system=QUESTION_AGENT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "\n".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text" and getattr(block, "text", None)
        )
        structured = _extract_json_object(text)
        if not structured:
            raise RuntimeError("Question agent response was not valid JSON.")
        return QuestionDecision.from_dict(structured)

    def _heuristic_decision(self, state: SessionState, latest_user_text: str | None) -> QuestionDecision:
        next_by_stage = {
            "intro":       ("background",  "understand context",          "What are you studying right now, and which part do you enjoy most?"),
            "background":  ("interests",   "identify interests",           "Which kinds of problems or industries pull your attention most?"),
            "interests":   ("goals",        "understand future direction",  "If the next year or two go well, what kind of role would you love to land?"),
            "goals":       ("constraints",  "understand constraints",       "What constraints do you need to work around — time, money, location, visa?"),
            "constraints": ("blockers",     "surface blockers",             "What has been the hardest part about moving in that direction so far?"),
            "blockers":    ("synthesis",    "prepare synthesis",            "What would make the biggest difference for you in the next three months?"),
            "synthesis":   ("close",        "wrap up",                      "I have enough to work with. Let me summarize and we can stop here."),
            "close":       ("close",        "finish",                       "Thanks — that gives me a solid picture of where you want to go."),
        }
        current = state.stage if state.stage in next_by_stage else "intro"
        next_stage, goal, question = next_by_stage[current]
        completion = next_stage == "close" and bool(latest_user_text)
        spoken = question if completion else f"Thanks for sharing that. {question}"
        return QuestionDecision(
            stage=next_stage,
            goal=goal,
            question=question,
            spoken_reply=spoken,
            completion_signal=completion,
            reasoning_summary="Heuristic fallback.",
            extracted_profile={},
            missing_fields=[],
            closing_summary="",
        )


def _extract_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return {}
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}

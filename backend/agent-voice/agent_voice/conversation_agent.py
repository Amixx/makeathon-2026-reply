from __future__ import annotations

import asyncio
from typing import Any

from anthropic import Anthropic

from .config import Settings
from .models import QuestionDecision, SessionState
from .prompts import CONVERSATION_AGENT_SYSTEM_PROMPT, build_conversation_payload


class ConversationAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    async def respond(
        self,
        state: SessionState,
        decision: QuestionDecision,
        latest_user_text: str | None,
    ) -> str:
        return await asyncio.to_thread(
            self._respond_sync,
            state.prompt_view(),
            decision.to_dict(),
            latest_user_text,
        )

    def _respond_sync(
        self,
        session_view: dict[str, Any],
        decision: dict[str, Any],
        latest_user_text: str | None,
    ) -> str:
        payload = build_conversation_payload(session_view, decision, latest_user_text)
        response = self.client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=self.settings.conversation_max_tokens,
            system=CONVERSATION_AGENT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": payload}],
        )
        text_parts = [
            block.text.strip()
            for block in response.content
            if getattr(block, "type", None) == "text" and getattr(block, "text", None)
        ]
        text = " ".join(part for part in text_parts if part).strip()
        if not text:
            raise RuntimeError("Conversation agent returned no text.")
        return text

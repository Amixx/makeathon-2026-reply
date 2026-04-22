from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anthropic

from .config import Settings, load_settings
from .elevenlabs_client import ElevenLabsClient
from .models import QuestionDecision, SessionState, TranscriptResult
from .prompts import QUESTION_AGENT_SYSTEM_PROMPT, build_question_prompt
from .storage import SessionStore


@dataclass(frozen=True)
class VoiceMemoSummary:
    session_id: str
    transcript: TranscriptResult
    decision: QuestionDecision
    log_path: Path


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


def _decide_sync(
    settings: Settings,
    state: SessionState,
    latest_user_text: str | None,
) -> QuestionDecision:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    prompt = build_question_prompt(state.prompt_view(), latest_user_text)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=600,
        system=QUESTION_AGENT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "\n".join(
        block.text.strip()
        for block in response.content
        if getattr(block, "type", None) == "text" and getattr(block, "text", None)
    ).strip()
    structured = _extract_json_object(text)
    if not structured:
        raise RuntimeError("Voice memo summarizer did not return valid JSON.")
    return QuestionDecision.from_dict(structured)


async def summarize_voice_memo(
    audio_bytes: bytes,
    *,
    filename: str = "memo.webm",
    content_type: str = "audio/webm",
    initial_context: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> VoiceMemoSummary:
    settings = load_settings()
    store = SessionStore(settings.logs_dir)
    state = SessionState.create(initial_context=initial_context, session_id=session_id)

    voice_client = ElevenLabsClient(settings)
    transcript = await voice_client.transcribe(
        audio_bytes,
        filename=filename,
        content_type=content_type,
    )
    state.add_user_turn(transcript)

    decision = await asyncio.to_thread(
        _decide_sync,
        settings,
        state,
        transcript.text,
    )
    state.apply_decision(decision)

    summary_text = decision.closing_summary or decision.spoken_reply or decision.question
    if summary_text:
        state.add_assistant_event(
            summary_text,
            stage=decision.stage,
            meta={"goal": decision.goal, "kind": "voice-memo-summary"},
        )

    log_path = store.save(state)
    return VoiceMemoSummary(
        session_id=state.session_id,
        transcript=transcript,
        decision=decision,
        log_path=log_path,
    )

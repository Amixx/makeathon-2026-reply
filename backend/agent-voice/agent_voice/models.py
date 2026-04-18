from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


STAGES = (
    "intro",
    "background",
    "interests",
    "goals",
    "constraints",
    "blockers",
    "synthesis",
    "close",
)

LIST_PROFILE_FIELDS = {
    "career_interests",
    "target_roles",
    "target_industries",
    "strengths",
    "skills",
    "values",
    "constraints",
    "blockers",
    "preferred_locations",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dedupe_list(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def merge_profile(profile: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(profile)
    for key, value in patch.items():
        if value in (None, "", []):
            continue
        if key in LIST_PROFILE_FIELDS:
            existing = merged.get(key) or []
            merged[key] = _dedupe_list([*existing, *value])
            continue
        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue
        merged[key] = value
    return merged


@dataclass
class TurnEntry:
    role: str
    text: str
    timestamp: str = field(default_factory=utc_now)
    stage: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class QuestionDecision:
    stage: str
    goal: str
    question: str
    completion_signal: bool
    reasoning_summary: str
    extracted_profile: dict[str, Any] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    closing_summary: str = ""
    spoken_reply: str = ""
    confidence: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuestionDecision":
        return cls(
            stage=str(data.get("stage") or "intro"),
            goal=str(data.get("goal") or "").strip(),
            question=str(data.get("question") or "").strip(),
            spoken_reply=str(data.get("spoken_reply") or "").strip(),
            completion_signal=bool(data.get("completion_signal")),
            reasoning_summary=str(data.get("reasoning_summary") or "").strip(),
            extracted_profile=data.get("extracted_profile") or {},
            missing_fields=[
                str(item).strip() for item in (data.get("missing_fields") or []) if str(item).strip()
            ],
            closing_summary=str(data.get("closing_summary") or "").strip(),
            confidence=float(data["confidence"]) if data.get("confidence") is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TranscriptResult:
    text: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    session_id: str
    created_at: str
    updated_at: str
    stage: str = "intro"
    completed: bool = False
    initial_context: dict[str, Any] = field(default_factory=dict)
    profile: dict[str, Any] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    reasoning_notes: list[str] = field(default_factory=list)
    turns: list[TurnEntry] = field(default_factory=list)

    @classmethod
    def create(cls, initial_context: dict[str, Any] | None = None, session_id: str | None = None) -> "SessionState":
        now = utc_now()
        return cls(
            session_id=session_id or datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:6],
            created_at=now,
            updated_at=now,
            initial_context=initial_context or {},
            profile=(initial_context or {}).copy(),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionState":
        return cls(
            session_id=str(data["session_id"]),
            created_at=str(data["created_at"]),
            updated_at=str(data.get("updated_at") or data["created_at"]),
            stage=str(data.get("stage") or "intro"),
            completed=bool(data.get("completed")),
            initial_context=data.get("initial_context") or {},
            profile=data.get("profile") or {},
            missing_fields=[
                str(item).strip() for item in (data.get("missing_fields") or []) if str(item).strip()
            ],
            reasoning_notes=[
                str(item).strip() for item in (data.get("reasoning_notes") or []) if str(item).strip()
            ],
            turns=[
                TurnEntry(
                    role=str(turn["role"]),
                    text=str(turn["text"]),
                    timestamp=str(turn.get("timestamp") or utc_now()),
                    stage=turn.get("stage"),
                    meta=turn.get("meta") or {},
                )
                for turn in (data.get("turns") or [])
            ],
        )

    def touch(self) -> None:
        self.updated_at = utc_now()

    def add_user_turn(self, transcript: TranscriptResult) -> None:
        self.turns.append(
            TurnEntry(
                role="user",
                text=transcript.text,
                stage=self.stage,
                meta=transcript.meta,
            )
        )
        self.touch()

    def add_assistant_turn(self, text: str, decision: QuestionDecision) -> None:
        meta = {"goal": decision.goal}
        if decision.closing_summary:
            meta["closing_summary"] = decision.closing_summary
        self.turns.append(
            TurnEntry(
                role="assistant",
                text=text,
                stage=decision.stage,
                meta=meta,
            )
        )
        self.touch()

    def add_assistant_event(
        self,
        text: str,
        *,
        stage: str = "intro",
        meta: dict[str, Any] | None = None,
    ) -> None:
        self.turns.append(
            TurnEntry(
                role="assistant",
                text=text,
                stage=stage,
                meta=meta or {},
            )
        )
        self.touch()

    def apply_decision(self, decision: QuestionDecision) -> None:
        self.stage = decision.stage if decision.stage in STAGES else self.stage
        self.completed = decision.completion_signal
        self.profile = merge_profile(self.profile, decision.extracted_profile)
        self.missing_fields = _dedupe_list(decision.missing_fields)
        if decision.reasoning_summary:
            self.reasoning_notes = _dedupe_list([*self.reasoning_notes, decision.reasoning_summary])
        self.touch()

    def prompt_view(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "stage": self.stage,
            "completed": self.completed,
            "initial_context": self.initial_context,
            "profile": self.profile,
            "missing_fields": self.missing_fields,
            "recent_turns": [asdict(turn) for turn in self.turns[-8:]],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "stage": self.stage,
            "completed": self.completed,
            "initial_context": self.initial_context,
            "profile": self.profile,
            "missing_fields": self.missing_fields,
            "reasoning_notes": self.reasoning_notes,
            "turns": [asdict(turn) for turn in self.turns],
        }

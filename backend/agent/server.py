"""FastAPI agent service — streams Bedrock Anthropic Messages with tool rounds.

Routes are mounted under /agent/* so this service can sit behind public_gateway.py
which forwards /agent/* paths verbatim to the internal agent port.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from secrets import token_hex
from typing import Any, Dict, Iterator, List, Literal, Optional

import io

import boto3
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import (
    AGENT_HOST,
    AGENT_PORT,
    ANTHROPIC_VERSION,
    AWS_REGION,
    BEDROCK_MAX_TOKENS,
    BEDROCK_MODEL,
    DEMO_TUM_USERNAME,
    MAX_TOOL_ROUNDS,
)
from render import render_prompt
from tools import PLAN_TOOL_DECLS, PLAN_TOOLS, TOOL_DECLS, TOOLS, _call_mcp_tool

app = FastAPI(title="WayTum Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)

_UPLOADS_DIR = Path(__file__).parent / "data" / "uploads"
_VOICE_AGENT_ROOT = Path(__file__).resolve().parent.parent / "agent-voice"

# In-memory profile — no YAML persistence needed for a demo.
_profile: dict = {"commitment": "steady"}


class IncomingMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[IncomingMessage]
    system: Optional[str] = None


class DiscoverRequest(BaseModel):
    program: Optional[str] = None
    interest: Optional[str] = None
    category: Optional[Literal["course", "event", "person", "scholarship"]] = None


class PlanItem(BaseModel):
    id: Optional[str] = None
    title: str
    why: Optional[str] = ""
    type: Optional[Literal["course", "event", "person", "scholarship"]] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class PlanRequest(BaseModel):
    item: PlanItem
    program: Optional[str] = None
    interest: Optional[str] = None


def _ndjson(event: dict) -> bytes:
    return (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")


def _default_system_prompt() -> str:
    return render_prompt("system.j2", date=date.today().isoformat())


def _stream_one_turn(
    messages: list, system_prompt: str, tool_decls: list
) -> Iterator[dict]:
    """Single Bedrock call; yields {type, ...} events plus a final summary dict.

    Yields:
      - {"type": "text", "delta": str}       — streaming text
      - {"type": "_done", ...}               — internal terminator with content_blocks/tool_uses/stop_reason
    """

    body = {
        "anthropic_version": ANTHROPIC_VERSION,
        "max_tokens": BEDROCK_MAX_TOKENS,
        "system": system_prompt,
        "tools": tool_decls,
        "messages": messages,
    }
    response = _bedrock.invoke_model_with_response_stream(
        modelId=BEDROCK_MODEL,
        body=json.dumps(body),
    )

    content_blocks: list[dict] = []
    current: dict | None = None
    tool_uses: list[dict] = []
    stop_reason: str | None = None

    for event in response["body"]:
        if "chunk" not in event:
            continue
        chunk = json.loads(event["chunk"]["bytes"])
        ct = chunk.get("type")

        if ct == "content_block_start":
            cb = chunk["content_block"]
            if cb["type"] == "text":
                current = {"type": "text", "text": ""}
            elif cb["type"] == "tool_use":
                current = {"type": "tool_use", "id": cb["id"], "name": cb["name"], "_json": ""}
            else:
                current = {"type": cb["type"]}
        elif ct == "content_block_delta":
            d = chunk["delta"]
            dt = d.get("type")
            if dt == "text_delta" and current and current["type"] == "text":
                t = d.get("text", "")
                current["text"] += t
                if t:
                    yield {"type": "text", "delta": t}
            elif dt == "input_json_delta" and current and current["type"] == "tool_use":
                current["_json"] += d.get("partial_json", "")
        elif ct == "content_block_stop":
            if current:
                if current["type"] == "tool_use":
                    raw = current.pop("_json", "")
                    current["input"] = json.loads(raw) if raw else {}
                    tool_uses.append(current)
                content_blocks.append(current)
                current = None
        elif ct == "message_delta":
            stop_reason = chunk.get("delta", {}).get("stop_reason") or stop_reason

    yield {
        "type": "_done",
        "content_blocks": content_blocks,
        "tool_uses": tool_uses,
        "stop_reason": stop_reason,
    }


def _run_agent(
    messages: list,
    system_prompt: str,
    tool_decls: list,
    tools: dict,
) -> Iterator[bytes]:
    """Drive the tool-use loop. Yields NDJSON-encoded bytes for the HTTP stream."""

    for _ in range(MAX_TOOL_ROUNDS):
        summary: dict | None = None
        for event in _stream_one_turn(messages, system_prompt, tool_decls):
            if event["type"] == "_done":
                summary = event
            else:
                yield _ndjson(event)

        assert summary is not None
        messages.append({"role": "assistant", "content": summary["content_blocks"]})

        if summary["stop_reason"] != "tool_use" or not summary["tool_uses"]:
            return

        tool_results = []
        for tu in summary["tool_uses"]:
            yield _ndjson(
                {"type": "tool_start", "id": tu["id"], "name": tu["name"], "input": tu["input"]}
            )
            try:
                result = tools[tu["name"]](**tu["input"])
                content = str(result)
                is_error = False
            except Exception as exc:  # noqa: BLE001
                content = f"{type(exc).__name__}: {exc}"
                is_error = True
            yield _ndjson(
                {"type": "tool_result", "id": tu["id"], "content": content, "isError": is_error}
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": content,
                    **({"is_error": True} if is_error else {}),
                }
            )

        messages.append({"role": "user", "content": tool_results})


@app.get("/agent/health")
def health() -> dict:
    return {"ok": True, "model": BEDROCK_MODEL, "region": AWS_REGION}


class ProfileRequest(BaseModel):
    userId: Optional[str] = None
    name: Optional[str] = None
    program: Optional[str] = None
    interest: Optional[str] = None
    semester: Optional[str] = None
    vision: Optional[str] = None
    blockers: Optional[str] = None
    githubUrl: Optional[str] = None
    linkedinUrl: Optional[str] = None
    cvFileName: Optional[str] = None
    cvUploaded: Optional[bool] = None
    interests: Optional[List[str]] = None
    tumSsoId: Optional[str] = None
    tumSsoConnected: Optional[bool] = None
    commitment: Optional[Literal["whisper", "steady", "push"]] = None
    isDemo: Optional[bool] = None


class ExtractInterestsRequest(BaseModel):
    text: str


class TumConnectRequest(BaseModel):
    tumSsoId: str
    password: str


class TumSessionStatusRequest(BaseModel):
    tumSsoId: str


_PROFILE_FIELD_MAP = {
    "userId": "user_id",
    "name": "name",
    "program": "program",
    "interest": "interest",
    "semester": "semester",
    "vision": "vision",
    "blockers": "blockers",
    "githubUrl": "github_url",
    "linkedinUrl": "linkedin_url",
    "cvFileName": "cv_file_name",
    "cvUploaded": "cv_uploaded",
    "interests": "interests",
    "tumSsoId": "tum_sso_id",
    "tumSsoConnected": "tum_sso_connected",
    "commitment": "commitment",
    "isDemo": "is_demo",
}


def _profile_to_api(data: Mapping[str, Any]) -> dict:
    return {
        "userId": data.get("user_id"),
        "name": data.get("name"),
        "program": data.get("program"),
        "interest": data.get("interest"),
        "semester": data.get("semester"),
        "vision": data.get("vision"),
        "blockers": data.get("blockers"),
        "githubUrl": data.get("github_url"),
        "linkedinUrl": data.get("linkedin_url"),
        "cvFileName": data.get("cv_file_name"),
        "cvUploaded": bool(data.get("cv_uploaded")),
        "interests": data.get("interests") or [],
        "tumSsoId": data.get("tum_sso_id"),
        "tumSsoConnected": bool(data.get("tum_sso_connected")),
        "commitment": data.get("commitment"),
        "isDemo": bool(data.get("is_demo")),
    }


def _merge_profile_patch(current: dict, patch: Mapping[str, Any]) -> dict:
    for api_key, value in patch.items():
        storage_key = _PROFILE_FIELD_MAP.get(api_key)
        if storage_key is None:
            continue
        if storage_key == "interests":
            current[storage_key] = [
                str(item).strip()
                for item in (value or [])
                if str(item).strip()
            ]
            if current[storage_key] and not current.get("interest"):
                current["interest"] = current[storage_key][0]
            continue
        current[storage_key] = value
    return current


def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name.strip()).strip(".-")
    return cleaned or "upload.bin"


def _load_profile() -> dict:
    return _profile.copy()


def _save_profile(data: dict) -> None:
    global _profile
    _profile = data


def _coerce_string_list(*values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, list):
            items = value
        elif value in (None, ""):
            items = []
        else:
            items = [value]
        for item in items:
            text = str(item).strip()
            if not text:
                continue
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(text)
    return result


def _voice_fields_from_profile(extracted: Mapping[str, Any], transcript_text: str) -> dict[str, Any]:
    interests = _coerce_string_list(
        extracted.get("career_interests"),
        extracted.get("target_industries"),
        extracted.get("target_roles"),
    )
    blockers = _coerce_string_list(extracted.get("blockers"), extracted.get("constraints"))
    vision = (
        str(extracted.get("future_goal") or "").strip()
        or str(extracted.get("summary") or "").strip()
        or str(extracted.get("motivation") or "").strip()
        or transcript_text.strip()
    )
    return {
        "vision": vision,
        "interests": interests,
        "interest": interests[0] if interests else None,
        "blockers": ", ".join(blockers),
        "program": str(extracted.get("program") or "").strip() or None,
        "semester": str(extracted.get("semester") or "").strip() or None,
        "summary": str(extracted.get("summary") or "").strip() or None,
    }


def _discover_prompt_context(profile: Mapping[str, Any], req: DiscoverRequest) -> dict:
    interests = profile.get("interests") or []
    program = (req.program or profile.get("program") or "").strip()
    interest = (req.interest or profile.get("interest") or "").strip()
    if not interest and interests:
        interest = str(interests[0]).strip()

    return {
        "program": program,
        "interest": interest,
        "vision": (profile.get("vision") or "").strip(),
        "blockers": (profile.get("blockers") or "").strip(),
        "semester": (profile.get("semester") or "").strip(),
        "interests": [str(item).strip() for item in interests if str(item).strip()],
        "commitment": (profile.get("commitment") or "").strip(),
        "tum_sso_connected": bool(profile.get("tum_sso_connected")),
        "github_url": (profile.get("github_url") or "").strip(),
        "linkedin_url": (profile.get("linkedin_url") or "").strip(),
        "cv_uploaded": bool(profile.get("cv_uploaded")),
        "cv_text": (profile.get("cv_text") or "").strip(),
        "category": (req.category or "").strip(),
    }


@app.get("/agent/profile")
def get_profile() -> dict:
    """Return the current user profile."""
    return _profile_to_api(_load_profile())


@app.post("/agent/profile")
def post_profile(req: ProfileRequest) -> dict:
    """Merge supplied fields into the profile. Unspecified fields are kept as-is."""
    current = _load_profile()
    updates = req.model_dump(exclude_none=True)
    current = _merge_profile_patch(current, updates)
    _save_profile(current)
    return _profile_to_api(current)


@app.post("/agent/profile/clear")
def clear_profile() -> dict:
    """Reset the server-side profile to a blank slate."""
    _save_profile({"commitment": "steady"})
    return _profile_to_api(_load_profile())


@app.post("/agent/profile/demo-reset")
def reset_demo_profile() -> dict:
    demo = {
        "user_id": DEMO_TUM_USERNAME,
        "tum_sso_id": DEMO_TUM_USERNAME,
        "tum_sso_connected": True,
        "commitment": "steady",
        "is_demo": True,
        "vision": (
            "I want to work on Mars robotics, ideally on the systems that "
            "actually move, navigate, and make decisions on the surface. "
            "By 2029 I'd love to be part of a team at ESA or a deep-tech "
            "startup building autonomous rovers."
        ),
        "blockers": (
            "Between coursework and everything else I never seem to have "
            "enough time, I second-guess whether I'm actually good enough "
            "for the labs I want, and the sheer amount of programs, "
            "scholarships, and internships out there leaves me frozen."
        ),
        "interests": ["Robotics", "Autonomous Systems", "Space Tech", "Embedded ML"],
        "interest": "Robotics",
        "github_url": "https://github.com/mars-rover-dev",
        "linkedin_url": "https://linkedin.com/in/anna-schmidt-tum",
    }
    _save_profile(demo)
    return {
        "profile": _profile_to_api(demo),
    }



@app.post("/agent/onboarding/tum-connect")
def connect_tum_account(req: TumConnectRequest) -> dict:
    tum_id = req.tumSsoId.strip().lower()
    password = req.password.strip()
    if not tum_id or not password:
        raise HTTPException(status_code=400, detail="TUM ID and password are required.")

    current = _load_profile()

    # Try real login via MCP
    try:
        result = _call_mcp_tool("tum_login", {"username": tum_id, "password": password})
        import json as _json
        login_result = _json.loads(result) if isinstance(result, str) else result
        if not login_result.get("success", False):
            raise HTTPException(
                status_code=401,
                detail=login_result.get("message", "TUM login failed."),
            )
        is_demo = login_result.get("demo_mode", False)
    except HTTPException:
        raise
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("MCP tum_login unavailable: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="TUM login service is currently unavailable. Please try again.",
        )

    current["tum_sso_id"] = tum_id
    current["tum_sso_connected"] = True
    current["user_id"] = tum_id
    current["is_demo"] = is_demo

    # Enrich profile with data from TUM systems
    try:
        # Fetch student info (name, program, semester)
        studies_raw = _call_mcp_tool("tumonline_my_studies", {"username": tum_id})
        studies_data = json.loads(studies_raw) if isinstance(studies_raw, str) else studies_raw
        if isinstance(studies_data, dict) and not studies_data.get("error"):
            if studies_data.get("name"):
                current["name"] = studies_data["name"]
            studies = studies_data.get("studies", [])
            if studies:
                primary = studies[0]
                if primary.get("program"):
                    current["program"] = primary["program"]
                sem = primary.get("semester")
                if sem is not None:
                    label = primary.get("semester_label") or f"Semester {sem}"
                    current["semester"] = label
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Could not fetch studies after login: %s", exc)

    try:
        # Fetch enrolled courses
        courses_raw = _call_mcp_tool("tumonline_my_courses", {"username": tum_id})
        courses_data = json.loads(courses_raw) if isinstance(courses_raw, str) else courses_raw
        if isinstance(courses_data, dict) and not courses_data.get("error"):
            enrolled = []
            for c in courses_data.get("courses", []):
                enrolled.append({
                    "id": c.get("course_number", ""),
                    "name": c.get("title", ""),
                    "ects": c.get("ects", 0),
                })
            if enrolled:
                current["enrolled"] = enrolled
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Could not fetch courses after login: %s", exc)

    _save_profile(current)
    return _profile_to_api(current)


@app.post("/agent/onboarding/tum-status")
def get_tum_session_status(req: TumSessionStatusRequest) -> dict:
    tum_id = req.tumSsoId.strip().lower()
    if not tum_id:
        raise HTTPException(status_code=400, detail="TUM ID is required.")

    current = _load_profile()

    if current.get("is_demo") and current.get("tum_sso_id") == tum_id:
        valid = bool(current.get("tum_sso_connected"))
        return {"valid": valid}

    try:
        result = _call_mcp_tool("tum_session_status", {"username": tum_id})
        import json as _json
        status_result = _json.loads(result) if isinstance(result, str) else result
        valid = bool(status_result.get("valid"))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("MCP tum_session_status unavailable: %s", exc)
        valid = bool(current.get("tum_sso_connected") and current.get("tum_sso_id") == tum_id)

    current["tum_sso_id"] = tum_id
    current["tum_sso_connected"] = valid
    current["user_id"] = current.get("user_id") or tum_id
    _save_profile(current)
    return {"valid": valid}


@app.post("/agent/onboarding/cv")
async def upload_cv(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".doc", ".docx"}:
        raise HTTPException(status_code=400, detail="Only PDF, DOC, and DOCX files are accepted.")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds the 10 MB demo limit.")

    _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    target_name = f"{token_hex(4)}-{_sanitize_filename(file.filename)}"
    target = _UPLOADS_DIR / target_name
    target.write_bytes(raw)

    cv_text = ""
    if suffix == ".pdf":
        try:
            import pypdf  # noqa: PLC0415
            reader = pypdf.PdfReader(io.BytesIO(raw))
            cv_text = "\n".join(
                page.extract_text() or "" for page in reader.pages
            ).strip()
            # Cap at 4 000 chars so it fits comfortably as context tokens
            if len(cv_text) > 4000:
                cv_text = cv_text[:4000] + "…"
        except Exception:  # noqa: BLE001
            cv_text = ""

    current = _load_profile()
    current["cv_file_name"] = file.filename
    current["cv_uploaded"] = True
    current["cv_storage_path"] = str(target.relative_to(Path(__file__).parent))
    if cv_text:
        current["cv_text"] = cv_text
    _save_profile(current)
    return _profile_to_api(current)


_ALLOWED_AUDIO_SUFFIXES = {".webm", ".wav", ".mp4", ".m4a", ".ogg", ".mp3", ".mpeg"}


async def _read_audio_upload(audio: UploadFile) -> tuple[bytes, str, str]:
    if not audio.filename:
        raise HTTPException(status_code=400, detail="Missing audio file name.")
    suffix = Path(audio.filename).suffix.lower()
    content_type = (audio.content_type or "").strip().lower()
    if suffix not in _ALLOWED_AUDIO_SUFFIXES and not content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Unsupported audio format.")
    raw = await audio.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded audio is empty.")
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio exceeds the 20 MB demo limit.")
    return raw, audio.filename, content_type


def _ensure_voice_agent_on_path() -> None:
    if str(_VOICE_AGENT_ROOT) not in sys.path:
        sys.path.insert(0, str(_VOICE_AGENT_ROOT))


async def _transcribe_audio_bytes(raw: bytes, filename: str, content_type: str) -> str:
    _ensure_voice_agent_on_path()
    try:
        from agent_voice.config import load_settings  # noqa: PLC0415
        from agent_voice.elevenlabs_client import ElevenLabsClient  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Voice agent import failed: {exc}") from exc
    client = ElevenLabsClient(load_settings())
    try:
        transcript = await client.transcribe(
            raw,
            filename=filename,
            content_type=content_type or "application/octet-stream",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Voice transcription failed: {exc}") from exc
    return transcript.text.strip()


_BLOCKERS_SYSTEM_PROMPT = (
    "You analyze a short voice memo from a TUM student describing what's "
    "weighing on them right now as they think about their career.\n"
    "Surface the emotional and practical obstacles they mentioned — NOT "
    "their career goals, job titles, or industries.\n"
    "Stay close to their own words. Do not invent new blockers.\n"
    "If nothing blocker-like is in the transcript, return empty values.\n"
    "Return valid JSON only."
)


def _extract_blockers_with_bedrock(transcript: str) -> dict[str, Any]:
    user_prompt = (
        "Voice memo transcript:\n"
        f"{transcript}\n\n"
        "Return JSON with exactly these fields:\n"
        "  blockers_text: 1-3 short sentences naming what actually feels heavy, "
        "in the speaker's voice. No job titles, industries, or career goals.\n"
        "  tags: up to 6 short uppercase tags. Prefer from this set when they "
        "apply: TIME, MONEY, CONFIDENCE, INFO OVERLOAD, AVOIDANCE, BURNOUT, "
        "COMPARISON, FAMILY, HEALTH, LANGUAGE, VISA, ISOLATION, UNCERTAINTY, "
        "IMPOSTER. You may add up to 2 short custom tags if nothing fits.\n"
        "  summary: one-line neutral paraphrase of the heaviest thing.\n"
    )
    body = {
        "anthropic_version": ANTHROPIC_VERSION,
        "max_tokens": 400,
        "system": _BLOCKERS_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    response = _bedrock.invoke_model(modelId=BEDROCK_MODEL, body=json.dumps(body))
    payload = json.loads(response["body"].read())
    text = "\n".join(
        block.get("text", "").strip()
        for block in payload.get("content", [])
        if block.get("type") == "text" and block.get("text")
    ).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return {"blockers_text": "", "tags": [], "summary": ""}
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {"blockers_text": "", "tags": [], "summary": ""}
    if not isinstance(parsed, dict):
        return {"blockers_text": "", "tags": [], "summary": ""}
    return {
        "blockers_text": str(parsed.get("blockers_text") or "").strip(),
        "tags": _coerce_string_list(parsed.get("tags")),
        "summary": str(parsed.get("summary") or "").strip(),
    }


@app.post("/agent/voice/transcribe")
async def voice_transcribe(audio: UploadFile = File(...)) -> dict:
    raw, filename, content_type = await _read_audio_upload(audio)

    _ensure_voice_agent_on_path()
    try:
        from agent_voice.summarizer import summarize_voice_memo  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Voice agent import failed: {exc}") from exc

    current = _load_profile()
    initial_context = {
        "name": current.get("name"),
        "program": current.get("program"),
        "semester": current.get("semester"),
        "future_goal": current.get("vision"),
        "career_interests": current.get("interests") or [],
        "blockers": _coerce_string_list(current.get("blockers")),
    }

    try:
        memo = await summarize_voice_memo(
            raw,
            filename=filename,
            content_type=content_type or "application/octet-stream",
            initial_context=initial_context,
            aws_region=AWS_REGION,
            model_id=BEDROCK_MODEL,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Voice memo processing failed: {exc}") from exc

    transcript_text = memo.transcript.text.strip()
    if not transcript_text:
        raise HTTPException(status_code=422, detail="Could not transcribe any speech from the recording.")

    extracted_profile = memo.decision.extracted_profile or {}
    voice_fields = _voice_fields_from_profile(extracted_profile, transcript_text)

    current = _merge_profile_patch(
        current,
        {
            key: value
            for key, value in {
                "vision": voice_fields["vision"],
                "blockers": voice_fields["blockers"],
                "interests": voice_fields["interests"],
                "interest": voice_fields["interest"],
                "program": voice_fields["program"],
                "semester": voice_fields["semester"],
            }.items()
            if value not in (None, "", [])
        },
    )
    current["voice_memo_transcript"] = transcript_text
    current["voice_memo_session_id"] = memo.session_id
    current["voice_memo_log_path"] = str(memo.log_path)
    if voice_fields["summary"]:
        current["voice_memo_summary"] = voice_fields["summary"]
    _save_profile(current)

    return {
        "text": transcript_text,
        "fields": {
            "vision": voice_fields["vision"],
            "interests": voice_fields["interests"],
            "interest": voice_fields["interest"],
            "blockers": voice_fields["blockers"],
            "program": voice_fields["program"],
            "semester": voice_fields["semester"],
        },
        "summary": voice_fields["summary"],
        "profile": _profile_to_api(current),
        "sessionId": memo.session_id,
        "logPath": str(memo.log_path),
    }


@app.post("/agent/voice/transcribe-blockers")
async def voice_transcribe_blockers(audio: UploadFile = File(...)) -> dict:
    raw, filename, content_type = await _read_audio_upload(audio)
    transcript_text = await _transcribe_audio_bytes(raw, filename, content_type)
    if not transcript_text:
        raise HTTPException(status_code=422, detail="Could not transcribe any speech from the recording.")

    try:
        extracted = _extract_blockers_with_bedrock(transcript_text)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Blocker extraction failed: {exc}") from exc

    blockers_text = extracted["blockers_text"] or transcript_text
    tags = extracted["tags"]
    summary = extracted["summary"] or None

    current = _load_profile()
    current = _merge_profile_patch(current, {"blockers": blockers_text})
    current["voice_memo_transcript"] = transcript_text
    if summary:
        current["voice_memo_summary"] = summary
    _save_profile(current)

    return {
        "text": transcript_text,
        "fields": {"blockers": blockers_text, "tags": tags},
        "summary": summary,
        "profile": _profile_to_api(current),
    }


@app.post("/agent/extract-interests")
def extract_interests(req: ExtractInterestsRequest) -> dict:
    text = req.text.strip()
    if len(text) < 15:
        return {"interests": []}
    try:
        body = {
            "anthropic_version": ANTHROPIC_VERSION,
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": f"Extract 3-6 short keyword tags (1-3 words each) that capture the main career interests and themes from this text. Return ONLY a JSON array of strings, nothing else.\n\nText: {text}",
                }
            ],
        }
        response = _bedrock.invoke_model(
            modelId=BEDROCK_MODEL,
            body=json.dumps(body),
        )
        result = json.loads(response["body"].read())
        raw = result.get("content", [{}])[0].get("text", "[]")
        start = raw.find("[")
        end = raw.rfind("]")
        if start >= 0 and end > start:
            interests = json.loads(raw[start : end + 1])
            if isinstance(interests, list):
                return {"interests": [str(i).strip() for i in interests[:6] if str(i).strip()]}
        return {"interests": []}
    except Exception:
        import logging
        logging.getLogger(__name__).warning("extract-interests failed", exc_info=True)
        return {"interests": []}


def _extract_items(text: str) -> list:
    """Extract JSON array of items from LLM text output."""
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        arr = json.loads(text[start:end + 1])
        return arr if isinstance(arr, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def _build_summary(items: list) -> str:
    """Build a short markdown summary from parsed items."""
    if not items:
        return "No opportunities found."
    lines = []
    for item in items[:4]:
        title = item.get("title", "")
        why = item.get("why", "")
        if title:
            lines.append(f"- **{title}**" + (f" — {why}" if why else ""))
    return "\n".join(lines)



@app.post("/agent/discover")
def discover(req: DiscoverRequest) -> StreamingResponse:
    """Main-agent orchestrator: brainstorm actionable items (JSON array).

    Streams the JSON directly — no tool rounds, for speed. The items are the
    seed set that the /agent/plan subagent will deep-research per-item.
    """
    profile = _load_profile()
    prompt_context = _discover_prompt_context(profile, req)

    user_prompt = render_prompt("discover.j2", **prompt_context)
    system_prompt = render_prompt("system_discover.j2", date=date.today().isoformat(), category=prompt_context["category"])
    messages = [{"role": "user", "content": user_prompt}]

    # Use tools when scoped to a category for richer results
    use_tools = bool(req.category)
    tool_decls = PLAN_TOOL_DECLS if use_tools else []
    tools = PLAN_TOOLS if use_tools else {}

    def generate():
        try:
            full_text = ""
            for chunk in _run_agent(messages, system_prompt, tool_decls=tool_decls, tools=tools):
                # Peek at text deltas to accumulate full_text
                try:
                    ev = json.loads(chunk.decode("utf-8"))
                    if ev.get("type") == "text":
                        full_text += ev.get("delta", "")
                except Exception:
                    pass
                yield chunk
            # Parse items from accumulated text
            items = _extract_items(full_text)
            summary = _build_summary(items)
            yield _ndjson({"type": "done", "items": items, "summary": summary})
        except Exception as exc:  # noqa: BLE001
            yield _ndjson({"type": "error", "message": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@app.post("/agent/plan")
def plan(req: PlanRequest) -> StreamingResponse:
    """Plan subagent: take ONE actionable item and deep-research it with MCP tools.

    Runs the full tool-use loop over TUMonline / career / navigatum / LinkedIn
    / Moodle. Returns a step-by-step plan + a ready-to-send email + key facts.
    """
    profile = _load_profile()
    prompt_context = _discover_prompt_context(profile, DiscoverRequest(program=req.program, interest=req.interest))

    user_prompt = render_prompt(
        "plan.j2",
        program=prompt_context["program"],
        interest=prompt_context["interest"],
        semester=prompt_context["semester"],
        username=profile.get("user_id", ""),
        vision=prompt_context["vision"],
        blockers=prompt_context["blockers"],
        interests=prompt_context["interests"],
        commitment=prompt_context["commitment"],
        tum_sso_connected=prompt_context["tum_sso_connected"],
        github_url=prompt_context["github_url"],
        linkedin_url=prompt_context["linkedin_url"],
        cv_uploaded=prompt_context["cv_uploaded"],
        cv_text=prompt_context["cv_text"],
        item=req.item.model_dump(),
    )
    system_prompt = render_prompt("system_plan.j2", date=date.today().isoformat())
    messages = [{"role": "user", "content": user_prompt}]

    def generate():
        try:
            yield from _run_agent(
                messages, system_prompt, tool_decls=PLAN_TOOL_DECLS, tools=PLAN_TOOLS
            )
            yield _ndjson({"type": "done"})
        except Exception as exc:  # noqa: BLE001
            yield _ndjson({"type": "error", "message": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@app.post("/agent/chat")
def chat(req: ChatRequest) -> StreamingResponse:
    system_prompt = (req.system or "").strip() or _default_system_prompt()
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    def generate():
        try:
            yield from _run_agent(messages, system_prompt, TOOL_DECLS, TOOLS)
            yield _ndjson({"type": "done"})
        except Exception as exc:  # noqa: BLE001
            yield _ndjson({"type": "error", "message": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host=AGENT_HOST, port=AGENT_PORT, reload=True)

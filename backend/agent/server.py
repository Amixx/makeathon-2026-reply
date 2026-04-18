"""FastAPI agent service — streams Bedrock Anthropic Messages with tool rounds.

Routes are mounted under /agent/* so this service can sit behind public_gateway.py
which forwards /agent/* paths verbatim to the internal agent port.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from secrets import token_hex
from typing import Any, Dict, Iterator, List, Literal, Optional

import io

import boto3
import yaml
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
    MAX_TOOL_ROUNDS,
)
from render import render_prompt
from tools import PLAN_TOOL_DECLS, PLAN_TOOLS, TOOL_DECLS, TOOLS

app = FastAPI(title="WayTum Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)

_PROFILE_PATH = Path(__file__).parent / "data" / "user_profile.yaml"
_DEMO_PROFILE_PATH = Path(__file__).parent / "data" / "user_profile_demo.yaml"
_UPLOADS_DIR = Path(__file__).parent / "data" / "uploads"


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


class TumConnectRequest(BaseModel):
    tumSsoId: str
    password: str


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
    if not _PROFILE_PATH.exists():
        return {}
    return yaml.safe_load(_PROFILE_PATH.read_text()) or {}


def _load_demo_profile() -> dict:
    if not _DEMO_PROFILE_PATH.exists():
        return {}
    return yaml.safe_load(_DEMO_PROFILE_PATH.read_text()) or {}



def _save_profile(data: dict) -> None:
    _PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PROFILE_PATH.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False))


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
    """Return the current user profile from user_profile.yaml."""
    return _profile_to_api(_load_profile())


@app.post("/agent/profile")
def post_profile(req: ProfileRequest) -> dict:
    """Merge supplied fields into user_profile.yaml. Unspecified fields are kept as-is."""
    current = _load_profile()
    updates = req.model_dump(exclude_none=True)
    current = _merge_profile_patch(current, updates)
    _save_profile(current)
    return _profile_to_api(current)


@app.post("/agent/profile/demo-reset")
def reset_demo_profile() -> dict:
    demo = _load_demo_profile()
    _save_profile(demo)
    return {
        "profile": _profile_to_api(demo),
        "tumPassword": "demo-password",
    }



@app.post("/agent/onboarding/tum-connect")
def connect_tum_account(req: TumConnectRequest) -> dict:
    tum_id = req.tumSsoId.strip().lower()
    password = req.password.strip()
    if not tum_id or not password:
        raise HTTPException(status_code=400, detail="TUM ID and password are required.")

    current = _load_profile()
    demo = _load_demo_profile()
    current["tum_sso_id"] = tum_id
    current["tum_sso_connected"] = True
    current["user_id"] = current.get("user_id") or tum_id
    for key in ("name", "program", "interest", "semester", "interests"):
        if not current.get(key) and demo.get(key):
            current[key] = demo[key]
    _save_profile(current)
    return _profile_to_api(current)


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


@app.post("/agent/voice/transcribe")
async def voice_transcribe(audio: UploadFile = File(...)) -> dict:
    """
    # TODO: Real implementation needed — two jobs:
    #   (a) Transcribe the audio blob via Bedrock Transcription or ElevenLabs STT.
    #       audio.content_type will be audio/webm, audio/wav, or audio/mp4.
    #       Read bytes: raw = await audio.read()
    #   (b) Extract structured fields from the transcript via a small Bedrock
    #       structured-output call:
    #         prompt = f"Extract JSON {{vision, interests: [], blockers}} from:\n{text}"
    #       Return {"text": transcript, "fields": {"vision": ..., "interests": [...], "blockers": ...}}
    # STUB: returns empty result so the frontend can fall back to manual input.
    """
    return {"text": "", "fields": {}}


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

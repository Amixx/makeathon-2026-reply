"""FastAPI agent service — streams Bedrock Anthropic Messages with tool rounds.

Routes are mounted under /agent/* so this service can sit behind public_gateway.py
which forwards /agent/* paths verbatim to the internal agent port.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Iterator, List, Optional

import boto3
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

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

app = FastAPI(title="Campus Co-Pilot Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)

_PROFILE_PATH = Path(__file__).parent / "data" / "user_profile.yaml"


class IncomingMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[IncomingMessage]
    system: Optional[str] = None


class DiscoverRequest(BaseModel):
    program: Optional[str] = None
    interest: Optional[str] = None


class PlanItem(BaseModel):
    id: Optional[str] = None
    title: str
    why: Optional[str] = ""


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


def _load_profile() -> dict:
    return yaml.safe_load(_PROFILE_PATH.read_text()) or {}


@app.post("/agent/discover")
def discover(req: DiscoverRequest) -> StreamingResponse:
    """Main-agent orchestrator: brainstorm actionable items (JSON array).

    Streams the JSON directly — no tool rounds, for speed. The items are the
    seed set that the /agent/plan subagent will deep-research per-item.
    """
    profile = _load_profile()
    program = (req.program or profile.get("program") or "").strip()
    interest = (req.interest or profile.get("interest") or "").strip()

    user_prompt = render_prompt("discover.j2", program=program, interest=interest)
    system_prompt = render_prompt("system_discover.j2", date=date.today().isoformat())
    messages = [{"role": "user", "content": user_prompt}]

    def generate():
        try:
            # No tools — pure brainstorm. Single-turn.
            yield from _run_agent(messages, system_prompt, tool_decls=[], tools={})
            yield _ndjson({"type": "done"})
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
    program = (req.program or profile.get("program") or "").strip()
    interest = (req.interest or profile.get("interest") or "").strip()
    semester = profile.get("semester", "")
    username = profile.get("user_id", "")

    user_prompt = render_prompt(
        "plan.j2",
        program=program,
        interest=interest,
        semester=semester,
        username=username,
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

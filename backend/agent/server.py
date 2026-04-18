"""Minimal FastAPI scaffold for the future Campus Co-Pilot agent."""

import json
from typing import Literal

import uvicorn
from anthropic import AsyncAnthropic
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import AGENT_HOST, AGENT_PORT, ANTHROPIC_API_KEY, ANTHROPIC_MODEL

app = FastAPI(title="Campus Co-Pilot Agent", version="0.1.0")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class StreamRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    system: str | None = None
    model: str | None = None
    max_tokens: int = Field(default=1024, ge=1, le=4096)
    temperature: float = Field(default=0.2, ge=0, le=1)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _client() -> AsyncAnthropic:
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY is not configured")
    return AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


@app.get("/agent")
async def agent_info() -> dict:
    return {
        "name": "Campus Co-Pilot Agent API",
        "status": "ready",
        "stream_endpoint": "/agent/stream",
        "model_default": ANTHROPIC_MODEL,
    }


@app.get("/agent/health")
async def agent_health() -> dict:
    return {
        "ok": True,
        "anthropic_configured": bool(ANTHROPIC_API_KEY),
        "default_model": ANTHROPIC_MODEL,
    }


@app.post("/agent/stream")
async def agent_stream(payload: StreamRequest, request: Request) -> StreamingResponse:
    client = _client()

    async def event_stream():
        yield _sse("start", {"model": payload.model or ANTHROPIC_MODEL})
        try:
            request_kwargs = {
                "model": payload.model or ANTHROPIC_MODEL,
                "max_tokens": payload.max_tokens,
                "temperature": payload.temperature,
                "messages": [message.model_dump() for message in payload.messages],
            }
            if payload.system:
                request_kwargs["system"] = payload.system

            disconnected = False
            async with client.messages.stream(**request_kwargs) as stream:
                async for text in stream.text_stream:
                    if await request.is_disconnected():
                        disconnected = True
                        break
                    yield _sse("token", {"text": text})

                if disconnected:
                    return

                final_message = await stream.get_final_message()
                yield _sse(
                    "done",
                    {
                        "stop_reason": final_message.stop_reason,
                        "usage": final_message.usage.model_dump(),
                    },
                )
        except Exception as exc:
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host=AGENT_HOST, port=AGENT_PORT)

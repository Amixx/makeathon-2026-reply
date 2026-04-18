from __future__ import annotations

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import load_settings
from .elevenlabs_client import ElevenLabsClient
from .summarizer import ProfileSummarizer


app = FastAPI(title="WayTum Voice Intake")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_settings = load_settings()
_elevenlabs = ElevenLabsClient(_settings)
_summarizer = ProfileSummarizer(_settings)


class ProcessAudioResponse(BaseModel):
    transcript: str
    profile: dict


@app.post("/process-audio", response_model=ProcessAudioResponse)
async def process_audio(audio: UploadFile = File(...)) -> ProcessAudioResponse:
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    filename = audio.filename or "recording.webm"
    transcript_result = await _elevenlabs.transcribe(audio_bytes, filename=filename)

    if not transcript_result.text:
        raise HTTPException(status_code=422, detail="Could not transcribe audio")

    profile = _summarizer.extract_profile(transcript_result.text)

    return ProcessAudioResponse(transcript=transcript_result.text, profile=profile)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def main() -> None:
    uvicorn.run("agent_voice.main:app", host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    main()

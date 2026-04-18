# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "sounddevice",
#   "numpy",
#   "httpx",
#   "anthropic[bedrock]",
#   "python-dotenv",
# ]
# ///
"""
Live keyword extraction while you speak.
2s chunks → parallel ElevenLabs STT + parallel LLM calls → tags accumulate live.
Press ENTER to stop.
"""

import io
import json
import os
import queue
import threading
import wave
from pathlib import Path

import httpx
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv

_here = Path(__file__).resolve().parent
for _p in (_here / ".env", _here.parent / ".env", _here.parent.parent / ".env"):
    load_dotenv(_p, override=False)
os.environ.pop("ANTHROPIC_API_KEY", None)

from anthropic import AnthropicBedrock  # noqa: E402

ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")
BEDROCK_MODEL = os.getenv("BEDROCK_HAIKU_MODEL", "eu.anthropic.claude-haiku-4-5-20251001-v1:0")
SAMPLE_RATE = 16000
CHUNK_SECONDS = 1


def to_wav(audio: np.ndarray) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()


def transcribe_chunk(wav_bytes: bytes) -> str:
    with httpx.Client(timeout=30) as client:
        r = client.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            data={
                "model_id": "scribe_v2",
                "language_code": "en",
                "diarize": "false",
                "tag_audio_events": "false",
                "timestamps_granularity": "none",
                "file_format": "other",
                "no_verbatim": "true",
            },
            files={"file": ("chunk.wav", wav_bytes, "audio/wav")},
        )
        r.raise_for_status()
        return r.json().get("text", "").strip()


def summarize(transcript: str, keywords: list[str]) -> str:
    client = AnthropicBedrock(aws_region=AWS_REGION)
    msg = client.messages.create(
        model=BEDROCK_MODEL,
        max_tokens=512,
        system="""\
Summarize what this person said about themselves. Be dense — no filler, no repetition.
Use this compact format:

BACKGROUND: <1 sentence>
GOALS: <1 sentence>
INTERESTS: <comma list>
BLOCKERS: <1 sentence or "none mentioned">
KEY FACTS: <bullet list, max 6, only surprising or specific details>

Preserve all concrete details (names, places, numbers, technologies). Drop vague filler.""",
        messages=[{
            "role": "user",
            "content": f"Topics detected: {', '.join(keywords)}\n\nFull transcript:\n{transcript}"
        }],
    )
    return msg.content[0].text.strip()


def extract_keywords(transcript: str) -> list[str]:
    client = AnthropicBedrock(aws_region=AWS_REGION)
    msg = client.messages.create(
        model=BEDROCK_MODEL,
        max_tokens=256,
        system="""\
Extract big-picture life/career topics from what someone is saying about themselves.
Return ONLY a JSON array of short keyword strings (1-3 words each).
Examples: ["Neuroscience", "Machine Learning", "Mars", "Computer Science", "TUM", "startup"]
Only significant topics — no filler words. Max 15 keywords.""",
        messages=[{"role": "user", "content": f"Transcript so far:\n\n{transcript}"}],
    )
    raw = msg.content[0].text.strip()
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return [str(k).strip() for k in result if str(k).strip()]
    except json.JSONDecodeError:
        start, end = raw.find("["), raw.rfind("]") + 1
        if start != -1:
            return json.loads(raw[start:end])
    return []


def merge_keywords(existing: dict[str, str], incoming: list[str]) -> dict[str, str]:
    result = dict(existing)
    for kw in incoming:
        key = kw.lower().strip()
        if key and key not in result:
            result[key] = kw
    return result


def print_keywords(kw_map: dict[str, str]) -> None:
    if not kw_map:
        return
    tags = "  ".join(f"[{v}]" for v in kw_map.values())
    print(f"\r\033[K🏷  {tags}", end="", flush=True)


def main() -> None:
    stop_event = threading.Event()
    audio_queue: queue.Queue[np.ndarray | None] = queue.Queue()

    full_transcript = ""
    transcript_lock = threading.Lock()

    kw_map: dict[str, str] = {}
    kw_lock = threading.Lock()

    def recorder() -> None:
        chunk_frames = CHUNK_SECONDS * SAMPLE_RATE
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
            while not stop_event.is_set():
                data, _ = stream.read(chunk_frames)
                audio_queue.put(data.copy())
        audio_queue.put(None)

    def run_llm(transcript: str) -> None:
        try:
            new_kw = extract_keywords(transcript)
        except Exception as e:
            print(f"\n[llm error] {e}", flush=True)
            return
        if not new_kw:
            return
        with kw_lock:
            merged = merge_keywords(kw_map, new_kw)
            if merged != kw_map:
                kw_map.clear()
                kw_map.update(merged)
                print_keywords(kw_map)

    def processor() -> None:
        nonlocal full_transcript
        while True:
            chunk = audio_queue.get()
            if chunk is None:
                break
            if np.abs(chunk).mean() < 50:
                continue

            wav = to_wav(chunk)
            try:
                text = transcribe_chunk(wav)
            except Exception as e:
                print(f"\n[transcribe error] {e}", flush=True)
                continue

            if not text:
                continue

            with transcript_lock:
                full_transcript = (full_transcript + " " + text).strip()
                snapshot = full_transcript

            # fire LLM in parallel — no lock, all calls run concurrently
            threading.Thread(target=run_llm, args=(snapshot,), daemon=True).start()

    print("🎙  Speak freely — topics appear live. Press ENTER to stop.\n")

    threading.Thread(target=recorder, daemon=True).start()
    proc = threading.Thread(target=processor)
    proc.start()

    input()
    stop_event.set()
    proc.join(timeout=10)

    with transcript_lock:
        final_transcript = full_transcript
    with kw_lock:
        final_keywords = list(kw_map.values())

    print(f"\n\n🏷  Topics: {final_keywords}\n")
    print("⏳ Summarizing...", flush=True)
    try:
        summary = summarize(final_transcript, final_keywords)
        print(f"\n📋 Summary:\n{summary}\n")
    except Exception as e:
        print(f"[summary error] {e}")
    print(f"\n📝 Transcript:\n{final_transcript}")


if __name__ == "__main__":
    main()

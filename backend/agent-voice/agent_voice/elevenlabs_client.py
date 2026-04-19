from __future__ import annotations

import asyncio
import queue as _queue

import httpx

from .config import Settings
from .models import TranscriptResult


class ElevenLabsClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = "https://api.elevenlabs.io/v1"

    def _headers(self) -> dict[str, str]:
        if not self.settings.elevenlabs_api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is required for voice mode.")
        return {"xi-api-key": self.settings.elevenlabs_api_key}

    def _tts_json(self, text: str) -> dict:
        return {
            "text": text,
            "model_id": self.settings.elevenlabs_tts_model,
            "language_code": self.settings.language,
            "voice_settings": {"speed": self.settings.elevenlabs_tts_speed},
        }

    def _tts_params(self) -> dict:
        sr = self.settings.elevenlabs_tts_sample_rate
        return {
            "output_format": f"pcm_{sr}",
            "optimize_streaming_latency": self.settings.elevenlabs_tts_latency,
        }

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "turn.wav",
        content_type: str = "audio/wav",
    ) -> TranscriptResult:
        files = {"file": (filename, audio_bytes, content_type or "application/octet-stream")}
        data = {
            "model_id": self.settings.elevenlabs_stt_model,
            "language_code": self.settings.language,
            "diarize": "false",
            "tag_audio_events": "false",
            "timestamps_granularity": "none",
            "file_format": "other",
            "no_verbatim": "true",
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/speech-to-text",
                headers=self._headers(),
                data=data,
                files=files,
            )
            response.raise_for_status()
            payload = response.json()
        return TranscriptResult(
            text=str(payload.get("text") or "").strip(),
            meta={
                "language_code": payload.get("language_code"),
                "transcription_id": payload.get("transcription_id"),
            },
        )

    async def synthesize_pcm(self, text: str) -> bytes:
        """Fetch all PCM bytes at once (used for cache population)."""
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech/{self.settings.elevenlabs_voice_id}/stream",
                headers=self._headers() | {"Content-Type": "application/json"},
                params=self._tts_params(),
                json=self._tts_json(text),
            )
            response.raise_for_status()
            return response.content

    async def play_streaming(self, text: str) -> None:
        """Stream PCM audio from ElevenLabs and play via sounddevice with minimal latency."""
        import sounddevice as sd  # local import — only needed in voice mode

        sr = self.settings.elevenlabs_tts_sample_rate
        buf: _queue.SimpleQueue[bytes | None] = _queue.SimpleQueue()

        async def fetch() -> None:
            try:
                async with httpx.AsyncClient(timeout=90.0) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/text-to-speech/{self.settings.elevenlabs_voice_id}/stream",
                        headers=self._headers() | {"Content-Type": "application/json"},
                        params=self._tts_params(),
                        json=self._tts_json(text),
                    ) as response:
                        response.raise_for_status()
                        async for chunk in response.aiter_bytes(4096):
                            buf.put(chunk)
            finally:
                buf.put(None)  # always unblock the player thread

        def play() -> None:
            leftover = b""
            with sd.RawOutputStream(samplerate=sr, channels=1, dtype="int16") as stream:
                while True:
                    chunk = buf.get()
                    if chunk is None:
                        if leftover:
                            stream.write(leftover + b"\x00")  # pad to even bytes
                        break
                    data = leftover + chunk
                    if len(data) % 2:  # keep odd byte for next chunk
                        leftover = data[-1:]
                        data = data[:-1]
                    else:
                        leftover = b""
                    if data:
                        stream.write(data)

        await asyncio.gather(fetch(), asyncio.to_thread(play))

from __future__ import annotations

import asyncio
import hashlib
import random
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .elevenlabs_client import ElevenLabsClient

from .regex_responses import GENERIC_FILLERS, REGEX_RESPONSES


class ResponseCache:
    """
    Matches user transcripts to pre-written responses via regex, then serves
    the audio from disk cache (generating via ElevenLabs on first use).
    Cache hits are ~1ms, so filler audio starts playing almost instantly.
    """

    def __init__(self, cache_dir: Path, voice_client: "ElevenLabsClient") -> None:
        self.cache_dir = cache_dir
        self.voice_client = voice_client
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def match_text(self, transcript: str) -> str:
        """Return the first matching response text, or a random generic filler."""
        for pattern, response in REGEX_RESPONSES:
            if re.search(pattern, transcript, re.IGNORECASE):
                return response
        return random.choice(GENERIC_FILLERS)

    def _cache_path(self, text: str) -> Path:
        s = self.voice_client.settings
        key = hashlib.md5(
            f"{text}|{s.elevenlabs_voice_id}|{s.elevenlabs_tts_model}|"
            f"{s.elevenlabs_tts_speed}|{s.elevenlabs_tts_sample_rate}".encode()
        ).hexdigest()
        return self.cache_dir / f"{key}.pcm"

    async def get_audio(self, text: str) -> bytes:
        """Return PCM bytes from cache, generating via ElevenLabs if not yet cached."""
        path = self._cache_path(text)
        if path.exists():
            return path.read_bytes()
        pcm = await self.voice_client.synthesize_pcm(text)
        path.write_bytes(pcm)
        return pcm

    async def pre_warm(self) -> None:
        """Generate and cache all response audio files (run once before a demo)."""
        all_texts = [resp for _, resp in REGEX_RESPONSES] + GENERIC_FILLERS
        uncached = [t for t in all_texts if not self._cache_path(t).exists()]
        if not uncached:
            print(f"[cache] All {len(all_texts)} responses already cached.")
            return
        print(f"[cache] Pre-warming {len(uncached)}/{len(all_texts)} responses...")
        results = await asyncio.gather(
            *[self.get_audio(t) for t in uncached], return_exceptions=True
        )
        failed = sum(1 for r in results if isinstance(r, Exception))
        print(f"[cache] Done. {len(uncached) - failed} generated, {failed} failed.")

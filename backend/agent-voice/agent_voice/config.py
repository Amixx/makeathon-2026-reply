from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = BACKEND_ROOT.parent

for env_path in (
    REPO_ROOT / ".env",
    BACKEND_ROOT / ".env",
    PACKAGE_ROOT / ".env",
    PACKAGE_ROOT / ".env.local",
):
    load_dotenv(env_path, override=False)


@dataclass(frozen=True)
class Settings:
    package_root: Path = PACKAGE_ROOT
    logs_dir: Path = PACKAGE_ROOT / "logs"
    cache_dir: Path = PACKAGE_ROOT / "cache"
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    bedrock_haiku_model: str = os.getenv(
        "BEDROCK_HAIKU_MODEL", "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    )
    conversation_max_tokens: int = int(os.getenv("CONVERSATION_MAX_TOKENS", "300"))
    question_agent_timeout_sec: float = float(os.getenv("QUESTION_AGENT_TIMEOUT_SEC", "30"))
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_stt_model: str = os.getenv("ELEVENLABS_STT_MODEL", "scribe_v2")
    elevenlabs_tts_model: str = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_flash_v2_5")
    elevenlabs_tts_latency: int = int(os.getenv("ELEVENLABS_TTS_LATENCY", "4"))
    elevenlabs_tts_speed: float = float(os.getenv("ELEVENLABS_TTS_SPEED", "1.2"))
    elevenlabs_tts_sample_rate: int = int(os.getenv("ELEVENLABS_TTS_SAMPLE_RATE", "22050"))
    vad_rms_threshold: int = int(os.getenv("VAD_RMS_THRESHOLD", "500"))
    vad_silence_duration: float = float(os.getenv("VAD_SILENCE_DURATION", "1.2"))
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
    language: str = os.getenv("VOICE_AGENT_LANGUAGE", "en")
    max_turns: int = int(os.getenv("VOICE_AGENT_MAX_TURNS", "10"))
    recording_sample_rate: int = int(os.getenv("VOICE_AGENT_RECORDING_SAMPLE_RATE", "16000"))


def load_settings() -> Settings:
    settings = Settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    return settings

# Agent Voice

Local voice-first interview loop for the WayTum career coach.

## What it does

- records a turn from the local microphone
- transcribes it with ElevenLabs STT
- runs a structured `question-agent` on Anthropic Haiku
- runs a lightweight `conversation-agent` on Anthropic Haiku to phrase the spoken reply
- synthesizes the reply with ElevenLabs TTS
- saves the evolving interview state to `logs/<session-id>.yaml`

## Quickstart

```bash
cd backend/agent-voice
uv sync
cp .env.example .env
uv run agent-voice --initial-context data/initial_context.example.yaml
```

If local audio is not available, use:

```bash
uv run agent-voice --text-only
```

## Required environment

- `ANTHROPIC_API_KEY`
- `ELEVENLABS_API_KEY`

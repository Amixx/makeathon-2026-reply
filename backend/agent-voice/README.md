# Agent Voice

Local voice-first interview loop for the WayTum career coach.

## What it does

- records a turn from the local microphone
- transcribes it with ElevenLabs STT
- runs a structured `question-agent` on Anthropic's Agent SDK over Bedrock Haiku
- runs a lightweight `conversation-agent` on Bedrock Haiku to phrase the spoken reply
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

- `ELEVENLABS_API_KEY`
- Bedrock credentials via standard AWS auth or `AWS_BEARER_TOKEN_BEDROCK`

## Notes

- The question agent uses the Anthropic Agent SDK with Bedrock enabled through `CLAUDE_CODE_USE_BEDROCK=1`.
- The current implementation is intentionally local and terminal-first. It does not modify the existing `/agent` backend service.

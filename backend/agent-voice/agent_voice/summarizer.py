from __future__ import annotations

import json

from anthropic import AnthropicBedrock

from .config import Settings


SYSTEM_PROMPT = """\
You extract structured profile data from a student's spoken monologue about themselves.
Return ONLY valid JSON matching the schema — no markdown, no explanation.

Schema:
{
  "vision": "string | null — their career goal or dream",
  "blockers": "string | null — what's holding them back",
  "program": "string | null — their degree/study program",
  "interest": "string | null — primary interest area",
  "semester": "string | null — current semester (e.g. '3rd')",
  "githubUrl": "string | null",
  "linkedinUrl": "string | null",
  "interests": ["array of interest strings"],
  "commitment": "whisper | steady | push | null — how hard they want to push their career right now"
}

commitment levels:
- whisper: exploring, low urgency
- steady: actively working toward goals
- push: highly motivated, wants aggressive support

Leave fields null if not mentioned. Never hallucinate details."""


class ProfileSummarizer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AnthropicBedrock(aws_region=settings.aws_region)
    def extract_profile(self, transcript: str) -> dict:
        message = self.client.messages.create(
            model=self.settings.bedrock_haiku_model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Student monologue:\n\n{transcript}",
                }
            ],
        )
        raw = message.content[0].text.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
            return {}

# CLAUDE.md

Context for Claude Code working in this repo.

## Project

TUM.ai Makeathon 2026 submission — Reply track, "Campus Co-Pilot Suite".
We are building a **career guide / coach agent** for TUM students. See
[docs/TASK.md](docs/TASK.md) for the full challenge brief and
[README.md](README.md) for the one-paragraph pitch.

## Hackathon mode

- Optimize for a working demo by the pitch deadline, not for production polish.
- Prefer end-to-end vertical slices over horizontal completeness. One flow that
  works beats five flows that half-work.
- Hardcode / stub external systems we can't reach live (TUMonline auth, etc.) —
  but make the stub swappable so the demo story is honest.
- Don't add auth, tests, CI, or abstractions unless a judging criterion demands it.
- For AI stuff, use Gemini since we have credits for it, the api key will be provided.

## Judging criteria to keep in mind

From [docs/TASK.md](docs/TASK.md):

1. Innovation & agent-architecture ambition
2. Integration depth + autonomy (agent *acts*, not just retrieves)
3. Real-world impact
4. UI/UX
5. Pitch quality

When making trade-offs, favor **autonomous action** and **integration depth** over
extra features — those are the differentiators for this track.

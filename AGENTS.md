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

## Architecture

```
mcp/                    # Campus Co-Pilot MCP Server (Python)
├── server.py           # FastMCP entry point, registers all module tools
├── auth.py             # Playwright TUM SSO login, storageState management
├── session_store.py    # Fernet-encrypted session persistence on disk
├── config.py           # Env vars, API base URLs, constants
├── modules/            # One file per TUM system, each exports register(mcp)
│   ├── auth_tools.py   # tum_login, tum_session_status, tum_logout
│   ├── mensa.py        # ✅ mensa_get_menu, mensa_list_canteens (Eat API)
│   ├── tumonline.py    # ✅ course/room search, semester info (NAT API)
│   ├── navigatum.py    # ✅ campus location search (Navigatum API)
│   ├── mvv.py          # ✅ departures, station search (mvg package)
│   ├── moodle.py       # 🔧 list_courses (Playwright, needs auth)
│   ├── zhs.py          # 🔧 sports booking (Playwright, needs auth)
│   ├── matrix.py       # 📌 stub
│   └── collab.py       # 📌 stub
├── Dockerfile          # Playwright base image, ready for Fly.io
└── fly.toml            # Fly.io config with volume for session store
```

## Module contract

- Every module exports `register(mcp: FastMCP)` — tools use `@mcp.tool()`.
- Auth-requiring tools call `auth.get_context(user_id)` for a Playwright context.
- API-only tools use httpx directly, no auth.
- No LLM calls inside the MCP — it's tools only.

## Key env vars

- `TUM_ENV=demo|prod` — controls target (demo.campus.tum.de vs campus.tum.de)
- `FERNET_KEY` — encrypts session blobs
- `GOOGLE_API_KEY` — for the agent layer (not used in MCP itself)

## Running locally

```bash
cd mcp
python -m venv .venv && source .venv/bin/activate
pip install "mcp[cli]" httpx playwright pydantic cryptography python-dotenv uvicorn mvg
playwright install chromium
cp .env.example .env  # fill in FERNET_KEY
python server.py      # → http://0.0.0.0:8000/mcp
```

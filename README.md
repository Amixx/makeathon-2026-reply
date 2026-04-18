# WayTum

TUM.ai Makeathon 2026 — Reply track ("WayTum").

An autonomous agent that acts as a **career guide / coach** for TUM students: audits
professional hygiene (CV, email, online presence), cross-references your transcript
against real job/workshop requirements, and scouts opportunities from the TUM
ecosystem plus external sources. It bridges disconnected systems and takes concrete
actions on the student's behalf.

## Architecture

```
Frontend / clients  ──HTTP/SSE──▶  Agent API (/agent)
                               └─▶  MCP API (/mcp)
                                      └─▶  TUM APIs / Playwright
```

The backend now hosts two isolated services behind one public origin:

- `/mcp` — the MCP server exposing **20 tools** across 9 TUM systems
- `/agent` — a Bedrock-backed FastAPI agent (`/agent/chat` streams NDJSON, `/agent/health` for probes)

The MCP server exposes **20 tools** across 9 TUM systems as a single
[Model Context Protocol](https://modelcontextprotocol.io) endpoint. The agent
orchestrator calls tools over Streamable HTTP — no LLM logic lives in the MCP.

### Tools by module

| Module | Status | Tools |
|--------|--------|-------|
| **Auth** | ✅ | `tum_login`, `tum_session_status`, `tum_logout` |
| **Mensa** | ✅ | `mensa_get_menu`, `mensa_list_canteens` |
| **TUMonline** | ✅ | `tumonline_search_courses`, `tumonline_search_rooms`, `tumonline_get_semester_info` |
| **Navigatum** | ✅ | `navigatum_search`, `navigatum_get_room` |
| **MVV** | ✅ | `mvv_get_departures`, `mvv_search_station` |
| **Moodle** | 🔧 | `moodle_list_courses`, `moodle_list_assignments` |
| **ZHS** | 🔧 | `zhs_list_courses`, `zhs_book_slot` |
| **Matrix** | 📌 | `matrix_send_message`, `matrix_list_rooms` |
| **Collab** | 📌 | `collab_search`, `collab_get_page` |

✅ = working, 🔧 = needs auth testing, 📌 = stub

## Prerequisites

- Python 3.11+
- Node.js 20+ and npm (for the frontend)
- [uv](https://docs.astral.sh/uv/) (only for the optional voice agent)
- [Fly CLI](https://fly.io/docs/flyctl/install/) — `brew install flyctl` (macOS) or `curl -L https://fly.io/install.sh | sh`
  - Run `fly auth login` to authenticate (only needed for deploys)

## Run everything locally

Boots the MCP server, agent backend, and Vite frontend in one shell. Ctrl-C
stops all three.

```bash
./dev.sh
```

Once it settles:

- Chat UI    → http://localhost:5173/makeathon-2026-reply/chat
- Agent API  → http://127.0.0.1:8000/agent/chat  (health at `/agent/health`)
- MCP server → http://127.0.0.1:8001/mcp

`dev.sh` creates [backend/.venv](backend/) on first run, installs Python + npm
deps, and warns if no `.env` / `AWS_BEARER_TOKEN_BEDROCK` is set (Bedrock calls
fail without it). Overrides: `AGENT_PORT`, `MCP_PORT`, `PYTHON`.

### Configure the backend

```bash
cp backend/.env.example backend/.env
# Set AWS_BEARER_TOKEN_BEDROCK and AWS_REGION at minimum.
# `make setup` auto-generates FERNET_KEY; otherwise:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Run the pieces individually

<details><summary>Backend (MCP + agent behind one gateway)</summary>

```bash
cd backend
make setup   # venv, deps, playwright, .env with auto-generated FERNET_KEY
make run     # → http://0.0.0.0:8000 with /mcp and /agent behind one origin
```

Manual equivalent:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python launch_public.py
```

</details>

<details><summary>MCP server only</summary>

```bash
cd backend && source .venv/bin/activate
cd mcp && MCP_HOST=127.0.0.1 MCP_PORT=8001 python server.py
# → http://127.0.0.1:8001/mcp
```

</details>

<details><summary>Agent backend only (needs MCP already running)</summary>

```bash
cd backend && source .venv/bin/activate
cd agent && AGENT_PORT=8000 MCP_URL=http://127.0.0.1:8001/mcp python server.py
# → http://127.0.0.1:8000/agent/chat
```

</details>

<details><summary>Frontend only</summary>

```bash
cd frontend
npm install        # first run only
npm run dev        # → http://localhost:5173/makeathon-2026-reply/
```

Expects the agent at `http://127.0.0.1:8000` — start the backend first.

</details>

<details><summary>Voice agent (optional, terminal-only loop)</summary>

Separate project under [backend/agent-voice/](backend/agent-voice/), not part of
`dev.sh`. Uses `uv` + ElevenLabs + Bedrock Haiku.

```bash
cd backend/agent-voice
uv sync
cp .env.example .env      # ELEVENLABS_API_KEY + Bedrock creds
uv run agent-voice --initial-context data/initial_context.example.yaml
# or without a mic:
uv run agent-voice --text-only
```

See [backend/agent-voice/README.md](backend/agent-voice/README.md).

</details>

### Test with MCP Inspector

```bash
make inspect   # or: npx -y @modelcontextprotocol/inspector
```

1. Open the link printed in the terminal (includes auth token)
2. Set **Transport Type** → **Streamable HTTP**
3. Set **URL** → `http://localhost:8000/mcp`
4. Click **Connect**
5. Go to **Tools** tab → **List Tools** → select a tool → fill args → **Run Tool**

### Test flows you can try now

**Flow 1 — Mensa menu (no auth, instant):**
- `mensa_list_canteens` → copy a canteen ID
- `mensa_get_menu` with `canteen_id=mensa-garching` → live menu data

**Flow 2 — Campus search (no auth):**
- `navigatum_search` with `query=MW` → find Mechanical Engineering building
- `navigatum_get_room` with the ID from the result

**Flow 3 — Course search (no auth):**
- `tumonline_search_courses` with `query=Machine Learning`
- `tumonline_get_semester_info` → current semester dates

**Flow 4 — Public transport (no auth):**
- `mvv_search_station` with `query=Garching Forschungszentrum`
- `mvv_get_departures` with the station ID from the result

**Flow 5 — Full auth flow (needs TUM credentials):**
1. `tum_login` — `username=YOUR_TUM_ID`, `password=YOUR_PASSWORD`
2. `tum_session_status` — `username=YOUR_TUM_ID` → should return `{"valid": true}`
3. `moodle_list_courses` — `username=YOUR_TUM_ID` → your enrolled courses
4. `tum_logout` — `username=YOUR_TUM_ID` → clears the session

**Credentials never hit disk** — only the encrypted browser storageState is persisted.

## Deploy (Fly.io)

Pushes to `main` auto-deploy via the GitHub Actions workflow in
[`/.github/workflows/fly-deploy.yml`](.github/workflows/fly-deploy.yml), but only
when files under `backend/` changed.

### First-time setup

```bash
cd backend
fly volumes create session_data --size 1 --region ams
fly secrets set \
  FERNET_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
  GOOGLE_API_KEY="your-key" \
  AWS_BEARER_TOKEN_BEDROCK="your-bedrock-bearer-token" \
  AWS_REGION="eu-north-1"
```

Add a repository secret named `FLY_API_TOKEN` in GitHub so the workflow can run
`flyctl deploy` on pushes to `main`.

The frontend deploy is already scoped the same way: the GitHub Pages workflow only
runs when files under `frontend/` changed.

Fly also needs `FERNET_KEY` set as an app secret, otherwise `tum_login` can
complete the browser flow but still fail when persisting the encrypted session.
The deployed app should use `SESSION_STORE_PATH=/data/sessions` so sessions live
on the mounted Fly volume instead of ephemeral container storage.

### Manual deploy

```bash
cd backend
fly deploy
```

### Useful commands

```bash
fly status              # app & machine status
fly logs                # tail logs
fly ssh console         # shell into the VM
fly secrets list        # check which secrets are set
```

## Key design decisions

- **One MCP, no LLM inside** — orchestration lives in the agent layer
- **Fernet-encrypted sessions** — one key per deployment (hackathon; production wants per-user KDF)
- **`TUM_ENV=demo` by default** — destructive actions hit demo.campus.tum.de, never production
- **Prod demo account shortcut** — on `TUM_ENV=prod`, the `ge47lbg` TUM login stays on curated mock data while other usernames hit the real TUM systems
- **Rate limiting** — semaphore + per-domain delay to respect TUM ToS
- **Module contract** — `register(mcp)` per file, `@mcp.tool()` decorator, pydantic I/O

## Stack

- Python 3.11+, [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Playwright (browser automation for SSO + scraping)
- httpx (async HTTP for REST APIs)
- Fernet/cryptography (session encryption)
- Fly.io (deployment with persistent volumes)

## Structure

```
docs/           # Challenge brief
explorations/   # API discovery notes (endpoints, auth, response shapes)
backend/        # Shared host, MCP service, and isolated agent service
```

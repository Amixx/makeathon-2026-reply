# Campus Co-Pilot

TUM.ai Makeathon 2026 — Reply track ("Campus Co-Pilot Suite").

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
- [Fly CLI](https://fly.io/docs/flyctl/install/) — `brew install flyctl` (macOS) or `curl -L https://fly.io/install.sh | sh`
  - Run `fly auth login` to authenticate

## Quick start

```bash
cd backend
make setup   # venv, deps, playwright, .env with auto-generated FERNET_KEY
make run     # → http://0.0.0.0:8000 with /mcp and /agent
```

<details><summary>Manual setup (without make)</summary>

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print('FERNET_KEY=' + Fernet.generate_key().decode())"
# Paste the FERNET_KEY value into .env
python launch_public.py
```

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

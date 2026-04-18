# Campus Co-Pilot

TUM.ai Makeathon 2026 — Reply track ("Campus Co-Pilot Suite").

An autonomous agent that acts as a **career guide / coach** for TUM students: audits
professional hygiene (CV, email, online presence), cross-references your transcript
against real job/workshop requirements, and scouts opportunities from the TUM
ecosystem plus external sources. It bridges disconnected systems and takes concrete
actions on the student's behalf.

## Architecture

```
Agent / UI layer  ──HTTP/SSE──▶  MCP Server  ──▶  TUM APIs / Playwright
                                 (this repo)
```

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
cd mcp
python -m venv .venv && source .venv/bin/activate
pip install "mcp[cli]" httpx playwright pydantic cryptography python-dotenv uvicorn mvg
playwright install chromium

# Generate a Fernet key and create .env
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print('FERNET_KEY=' + Fernet.generate_key().decode())"
# Paste the output into .env

python server.py
# → Server at http://0.0.0.0:8000/mcp
```

### Test with MCP Inspector

```bash
npx -y @modelcontextprotocol/inspector
# Connect to http://localhost:8000/mcp
```

## Auth flow (manual test)

1. Start the server locally
2. Call `tum_login` with your TUM credentials via MCP Inspector or agent
3. Playwright opens headless Chromium → TUM Shibboleth SSO → captures session
4. Session encrypted with Fernet, stored on disk
5. Subsequent tools (`moodle_list_courses`, `zhs_book_slot`, etc.) load the session
6. Call `tum_session_status` to verify, `tum_logout` to clear

**Credentials never hit disk** — only the encrypted browser storageState is persisted.

## Deploy (Fly.io)

```bash
cd mcp
fly launch          # creates app
fly volumes create data --size 1 --region fra
fly secrets set FERNET_KEY=<key> GOOGLE_API_KEY=<key>
fly deploy
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
docs/          # Challenge brief
mcp/           # MCP server (see AGENTS.md for full tree)
```

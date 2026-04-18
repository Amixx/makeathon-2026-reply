#!/usr/bin/env bash
# WayTum — boot the Python agent backend + the Vite frontend together.
# Usage: ./dev.sh   (Ctrl-C stops both)

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$REPO/backend"
AGENT="$BACKEND/agent"
MCP="$BACKEND/mcp"
FRONTEND="$REPO/frontend"
VENV="$BACKEND/.venv"
PY="${PYTHON:-python3}"

AGENT_PORT="${AGENT_PORT:-8000}"
MCP_PORT="${MCP_PORT:-8001}"

c_b=$'\033[1m'; c_g=$'\033[32m'; c_y=$'\033[33m'; c_r=$'\033[31m'
c_c=$'\033[36m'; c_m=$'\033[35m'; c_n=$'\033[0m'

step() { printf "%s==>%s %s\n" "$c_b$c_g" "$c_n" "$*"; }
warn() { printf "%swarn:%s %s\n" "$c_b$c_y" "$c_n" "$*"; }
err()  { printf "%serr:%s %s\n"  "$c_b$c_r" "$c_n" "$*" >&2; }

command -v "$PY"  >/dev/null 2>&1 || { err "$PY not found in PATH"; exit 1; }
command -v npm    >/dev/null 2>&1 || { err "npm not found in PATH"; exit 1; }

# ── one-time setup ──────────────────────────────────────────────────────────
if [[ ! -d "$VENV" ]]; then
  step "Creating Python venv (one-time) at backend/.venv"
  "$PY" -m venv "$VENV"
fi

step "Syncing Python deps"
"$VENV/bin/pip" install -q -r "$BACKEND/requirements.txt"

if [[ ! -d "$FRONTEND/node_modules" ]]; then
  step "Installing frontend deps (one-time)"
  (cd "$FRONTEND" && npm install)
fi

if [[ ! -f "$REPO/.env" ]] && [[ ! -f "$BACKEND/.env" ]] && [[ -z "${AWS_BEARER_TOKEN_BEDROCK:-}" ]]; then
  warn "No .env files and no AWS_BEARER_TOKEN_BEDROCK in shell."
  warn "  The backend will start but Bedrock calls will fail. Fix:"
  warn "    cp backend/.env.example backend/.env  &&  edit backend/.env"
fi

# ── lifecycle ───────────────────────────────────────────────────────────────
cleanup() {
  printf "\n%s==>%s Stopping...\n" "$c_b$c_y" "$c_n"
  kill 0 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ── start all three ─────────────────────────────────────────────────────────
step "MCP      → http://127.0.0.1:${MCP_PORT}/mcp"
(
  cd "$MCP" && MCP_HOST=127.0.0.1 MCP_PORT="$MCP_PORT" "$VENV/bin/python" server.py 2>&1
) | awk -v p="${c_y}[mcp]  ${c_n}" '{ printf "%s %s\n", p, $0; fflush() }' &

step "Waiting for MCP on :${MCP_PORT}…"
for _ in $(seq 1 60); do
  if "$VENV/bin/python" -c "import socket,sys; s=socket.socket(); s.settimeout(0.5); sys.exit(s.connect_ex(('127.0.0.1', ${MCP_PORT})))" 2>/dev/null; then
    break
  fi
  sleep 0.5
done

step "Backend  → http://127.0.0.1:${AGENT_PORT}  (agent at /agent/chat)"
(
  cd "$AGENT" && AGENT_PORT="$AGENT_PORT" MCP_URL="http://127.0.0.1:${MCP_PORT}/mcp" "$VENV/bin/python" server.py 2>&1
) | awk -v p="${c_c}[agent]${c_n}" '{ printf "%s %s\n", p, $0; fflush() }' &

step "Frontend → http://localhost:5173/makeathon-2026-reply/"
(
  cd "$FRONTEND" && npm run dev --silent 2>&1
) | awk -v p="${c_m}[web]  ${c_n}" '{ printf "%s %s\n", p, $0; fflush() }' &

sleep 1
cat <<EOF

${c_b}${c_g}WayTum is up${c_n}
  Chat UI : ${c_b}http://localhost:5173/makeathon-2026-reply/chat${c_n}
  Health  : http://127.0.0.1:${AGENT_PORT}/agent/health
  MCP     : http://127.0.0.1:${MCP_PORT}/mcp
  Ctrl-C  : stop everything

EOF

wait

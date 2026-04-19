#!/usr/bin/env bash
# WayTum — start the combined backend host + Vite frontend together.
# Usage: ./dev.sh   (Ctrl-C stops everything)

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$REPO/backend"
FRONTEND="$REPO/frontend"
VENV="$BACKEND/.venv"
PY="${PYTHON:-python3}"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
PUBLIC_ORIGIN="${PUBLIC_ORIGIN:-http://${BACKEND_HOST}:${BACKEND_PORT}}"
VITE_AGENT_URL="${VITE_AGENT_URL:-}"
VITE_PROXY_TARGET="${VITE_PROXY_TARGET:-http://${BACKEND_HOST}:${BACKEND_PORT}}"

c_b=$'\033[1m'; c_g=$'\033[32m'; c_y=$'\033[33m'; c_r=$'\033[31m'
c_c=$'\033[36m'; c_m=$'\033[35m'; c_n=$'\033[0m'

step() { printf "%s==>%s %s\n" "$c_b$c_g" "$c_n" "$*"; }
warn() { printf "%swarn:%s %s\n" "$c_b$c_y" "$c_n" "$*"; }
err()  { printf "%serr:%s %s\n"  "$c_b$c_r" "$c_n" "$*" >&2; }

command -v "$PY" >/dev/null 2>&1 || { err "$PY not found in PATH"; exit 1; }
command -v npm >/dev/null 2>&1 || { err "npm not found in PATH"; exit 1; }

if [[ ! -d "$VENV" ]]; then
  step "Creating Python venv at backend/.venv"
  "$PY" -m venv "$VENV"
fi

step "Syncing Python deps"
"$VENV/bin/pip" install -q -r "$BACKEND/requirements.txt"

if [[ ! -d "$FRONTEND/node_modules" ]]; then
  step "Installing frontend deps"
  (cd "$FRONTEND" && npm install)
fi

if [[ ! -f "$REPO/.env" ]] && [[ ! -f "$BACKEND/.env" ]] && [[ -z "${AWS_BEARER_TOKEN_BEDROCK:-}" ]]; then
  warn "No .env files and no AWS_BEARER_TOKEN_BEDROCK in shell."
  warn "The stack will start, but Bedrock-backed routes will fail until env is configured."
fi

cleanup() {
  printf "\n%s==>%s Stopping...\n" "$c_b$c_y" "$c_n"
  kill 0 2>/dev/null || true
}
trap cleanup EXIT INT TERM

step "Backend   → http://${BACKEND_HOST}:${BACKEND_PORT}"
(
  cd "$BACKEND" && \
    BACKEND_HOST="$BACKEND_HOST" \
    BACKEND_PORT="$BACKEND_PORT" \
    PUBLIC_ORIGIN="$PUBLIC_ORIGIN" \
    "$VENV/bin/python" launch_public.py 2>&1
) | awk -v p="${c_c}[backend]${c_n}" '{ printf "%s %s\n", p, $0; fflush() }' &

step "Waiting for backend on :${BACKEND_PORT}…"
for _ in $(seq 1 120); do
  if "$VENV/bin/python" -c "import socket,sys; s=socket.socket(); s.settimeout(0.5); sys.exit(s.connect_ex(('${BACKEND_HOST}', ${BACKEND_PORT})))" 2>/dev/null; then
    break
  fi
  sleep 0.5
done

step "Frontend  → http://${FRONTEND_HOST}:${FRONTEND_PORT}/"
(
  cd "$FRONTEND" && \
    VITE_AGENT_URL="$VITE_AGENT_URL" \
    VITE_PROXY_TARGET="$VITE_PROXY_TARGET" \
    npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" 2>&1
) | awk -v p="${c_m}[frontend]${c_n}" '{ printf "%s %s\n", p, $0; fflush() }' &

sleep 1
cat <<EOF

${c_b}${c_g}WayTum is up${c_n}
  Frontend dev : ${c_b}http://${FRONTEND_HOST}:${FRONTEND_PORT}/${c_n}
  Backend      : ${c_b}http://${BACKEND_HOST}:${BACKEND_PORT}${c_n}
  Agent health : http://${BACKEND_HOST}:${BACKEND_PORT}/agent/health
  MCP docs     : http://${BACKEND_HOST}:${BACKEND_PORT}/mcp/docs
  Built app    : http://${BACKEND_HOST}:${BACKEND_PORT}/app/
  Ctrl-C       : stop everything

EOF

wait

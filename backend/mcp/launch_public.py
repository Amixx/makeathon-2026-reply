"""Run MCP + MCP Inspector + public gateway in one Fly machine."""

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import uvicorn

from config import (
    INSPECTOR_CLIENT_PORT,
    INSPECTOR_PROXY_PORT,
    INTERNAL_MCP_PORT,
    MCP_HOST,
    MCP_PORT,
)

ROOT = Path(__file__).resolve().parent
CHILD_PROCESSES: list[subprocess.Popen] = []


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _start_process(args: list[str], env: dict[str, str]) -> subprocess.Popen:
    process = subprocess.Popen(args, cwd=ROOT, env=env)
    CHILD_PROCESSES.append(process)
    return process


def _wait_for_port(port: int, timeout: float = 60.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for localhost:{port}")


def _stop_children(*_args: object) -> None:
    for process in reversed(CHILD_PROCESSES):
        if process.poll() is None:
            process.terminate()
    for process in reversed(CHILD_PROCESSES):
        if process.poll() is None:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


def main() -> None:
    env = os.environ.copy()
    inspector_command = (
        ["mcp-inspector"]
        if shutil.which("mcp-inspector")
        else ["npx", "-y", "@modelcontextprotocol/inspector"]
    )
    public_origin = env.get("PUBLIC_ORIGIN", "https://makeathon-2026-reply.fly.dev")
    allowed_origins = _dedupe(
        [
            public_origin,
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:6274",
            "http://127.0.0.1:6274",
        ]
    )

    mcp_env = env | {
        "MCP_HOST": "127.0.0.1",
        "MCP_PORT": str(INTERNAL_MCP_PORT),
    }
    inspector_env = env | {
        "HOST": "127.0.0.1",
        "CLIENT_PORT": str(INSPECTOR_CLIENT_PORT),
        "SERVER_PORT": str(INSPECTOR_PROXY_PORT),
        "MCP_AUTO_OPEN_ENABLED": "false",
        # The user explicitly wants the inspector public for the demo.
        "DANGEROUSLY_OMIT_AUTH": "true",
        "ALLOWED_ORIGINS": ",".join(allowed_origins),
    }

    _start_process([sys.executable, "server.py"], mcp_env)
    _start_process(inspector_command, inspector_env)

    _wait_for_port(INTERNAL_MCP_PORT)
    _wait_for_port(INSPECTOR_CLIENT_PORT)
    _wait_for_port(INSPECTOR_PROXY_PORT)

    signal.signal(signal.SIGTERM, _stop_children)
    signal.signal(signal.SIGINT, _stop_children)

    try:
        uvicorn.run("public_gateway:app", host=MCP_HOST, port=MCP_PORT)
    finally:
        _stop_children()


if __name__ == "__main__":
    main()

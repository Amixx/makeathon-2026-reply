"""Encrypted on-disk storage for Playwright storageState blobs."""

import json
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from config import FERNET_KEY, SESSION_STORE_PATH


def _fernet() -> Fernet:
    if not FERNET_KEY:
        raise RuntimeError("FERNET_KEY is not set – cannot encrypt session data")
    return Fernet(FERNET_KEY.encode())


def _path_for(user_id: str) -> Path:
    safe = user_id.replace("/", "_").replace("..", "_")
    return SESSION_STORE_PATH / f"{safe}.enc"


def save(user_id: str, state: dict) -> None:
    SESSION_STORE_PATH.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(state).encode()
    encrypted = _fernet().encrypt(blob)
    _path_for(user_id).write_bytes(encrypted)


def load(user_id: str) -> dict | None:
    path = _path_for(user_id)
    if not path.exists():
        return None
    try:
        decrypted = _fernet().decrypt(path.read_bytes())
        return json.loads(decrypted)
    except (InvalidToken, json.JSONDecodeError):
        return None


def delete(user_id: str) -> None:
    path = _path_for(user_id)
    if path.exists():
        path.unlink()

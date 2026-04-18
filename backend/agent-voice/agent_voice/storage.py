from __future__ import annotations

from pathlib import Path

import yaml

from .models import SessionState


class SessionStore:
    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, session_id: str) -> Path:
        return self.logs_dir / f"{session_id}.yaml"

    def save(self, state: SessionState) -> Path:
        path = self.path_for(state.session_id)
        path.write_text(
            yaml.safe_dump(state.to_dict(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return path

    def load(self, session_id: str) -> SessionState:
        path = self.path_for(session_id)
        return SessionState.from_dict(yaml.safe_load(path.read_text(encoding="utf-8")) or {})

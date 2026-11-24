"""Save and reopen a session (.msession = JSON)."""

from __future__ import annotations

import json
from pathlib import Path

from ..core.serialize import session_from_dict, session_to_dict
from ..core.types import Session

SUFFIX = ".msession"


def save_session(session: Session, path: str | Path) -> Path:
    path = Path(path)
    if path.suffix != SUFFIX:
        path = path.with_suffix(SUFFIX)
    path.write_text(json.dumps(session_to_dict(session), indent=2), encoding="utf-8")
    return path


def load_session(path: str | Path) -> Session:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not open '{path.name}': {exc}") from exc
    return session_from_dict(data)

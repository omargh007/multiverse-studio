"""Save and reopen a session (.msession = JSON). Owner: C."""

from __future__ import annotations

from pathlib import Path

from ..core.types import Session


def save_session(session: Session, path: str | Path) -> Path:
    raise NotImplementedError  # TODO(C)


def load_session(path: str | Path) -> Session:
    raise NotImplementedError  # TODO(C)

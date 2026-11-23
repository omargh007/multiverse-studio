"""Export the full session as a JSON report, with environment capture. Owner: C.

Includes: plan, blind-mode hash, seed, every universe's result, verdict,
cherry-pick result, and environment (Python version, OS, package versions,
``pip freeze``-style list) so others can rebuild the exact environment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.types import Session


def environment_info() -> dict[str, Any]:
    """Python version, platform and versions of the main dependencies."""
    raise NotImplementedError  # TODO(C)


def session_to_dict(session: Session) -> dict[str, Any]:
    raise NotImplementedError  # TODO(C)


def export_json(session: Session, path: str | Path) -> Path:
    raise NotImplementedError  # TODO(C)

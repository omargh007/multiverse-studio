"""Export the full session as a JSON report, with environment capture.

Includes: plan, blind-mode hash (and whether it still verifies), seed, every
universe's result, verdict, cherry-pick result, decision importance,
auto-written text, and the environment (Python, OS, package versions) so
others can rebuild the exact setup.
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from .. import __version__
from ..core import api
from ..core.serialize import session_to_dict
from ..core.types import Session

PACKAGES = ("multiverse-studio", "numpy", "pandas", "statsmodels", "matplotlib", "customtkinter")


def environment_info() -> dict[str, Any]:
    """Python version, platform and versions of the main dependencies."""
    versions: dict[str, str | None] = {}
    for name in PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "packages": versions,
    }


def report_dict(session: Session) -> dict[str, Any]:
    report: dict[str, Any] = {
        "report": "multiverse-studio-report",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "app_version": __version__,
        "environment": environment_info(),
        "session": session_to_dict(session),
    }
    if session.blind is not None:
        report["plan_verified"] = api.verify_plan(session, session.blind)
    if session.results:
        report["decision_importance"] = api.decision_importance(session.results, session.decisions)
    if session.verdict is not None:
        report["methods_text"] = api.methods_paragraph(session)
        report["results_text"] = api.results_paragraph(session)
    return report


def export_json(session: Session, path: str | Path) -> Path:
    path = Path(path)
    path.write_text(json.dumps(report_dict(session), indent=2), encoding="utf-8")
    return path

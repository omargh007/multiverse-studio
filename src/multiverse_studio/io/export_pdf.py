"""PDF report via Matplotlib's PdfPages (no extra dependency). Owner: C.

Pages: summary + verdict, specification curve, decision importance,
guardrail table, cherry-pick result, methods/results paragraphs, plan hash.
"""

from __future__ import annotations

from pathlib import Path

from ..core.types import Session


def export_pdf(session: Session, path: str | Path) -> Path:
    raise NotImplementedError  # TODO(C)

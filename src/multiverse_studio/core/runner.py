"""Run every universe, with progress reporting and cancellation. Owner: A (Core).

The runner is GUI-agnostic: the GUI runs it in a worker thread and passes a
``progress`` callback that only puts messages on a queue (never touches Tk).
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator, Sequence

import pandas as pd

from .models import fit_one
from .types import Decision, ModelFamily, Spec, SpecResult

ProgressFn = Callable[[int, int], None]
"""Called as progress(done, total) after each step."""


class Cancelled(Exception):
    """Raised by long tasks (e.g. the permutation test) when the user cancels."""


def iter_multiverse(
    df: pd.DataFrame,
    y: str,
    x: str,
    family: ModelFamily,
    decisions: Sequence[Decision],
    specs: Sequence[Spec],
    *,
    alpha: float = 0.05,
    progress: ProgressFn | None = None,
    cancel: threading.Event | None = None,
) -> Iterator[SpecResult]:
    """Yield results one by one (lets the GUI draw the curve progressively).

    Stops early, without error, when ``cancel`` is set.
    """
    total = len(specs)
    for i, spec in enumerate(specs, start=1):
        if cancel is not None and cancel.is_set():
            return
        result = fit_one(df, y, x, family, decisions, spec, alpha=alpha)
        if progress is not None:
            progress(i, total)
        yield result


def run_multiverse(
    df: pd.DataFrame,
    y: str,
    x: str,
    family: ModelFamily,
    decisions: Sequence[Decision],
    specs: Sequence[Spec],
    *,
    alpha: float = 0.05,
    progress: ProgressFn | None = None,
    cancel: threading.Event | None = None,
) -> list[SpecResult]:
    """Same arguments as :func:`iter_multiverse`; returns a list."""
    return list(
        iter_multiverse(
            df, y, x, family, decisions, specs, alpha=alpha, progress=progress, cancel=cancel
        )
    )

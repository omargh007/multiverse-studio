"""Run the multiverse off the UI thread so the app never freezes.

Pattern (required by the brief: long computations run in a worker thread):
  * ``RunJob.start()`` runs :func:`run_task` in a daemon thread. The task reports
    through ``emit((kind, payload))``, which only puts the message on a
    ``queue.Queue``.
  * The UI polls with ``RunJob.drain()`` on a timer (a Streamlit fragment with
    ``run_every``) and applies the messages on its own thread.
  * ``RunJob.cancel()`` sets a ``threading.Event`` that the core runner checks.

Final messages are always one of ("done", None), ("cancelled", None) or
("error", message). This module has no Streamlit import.
"""

from __future__ import annotations

import logging
import queue
import threading
import traceback
from collections.abc import Callable, Sequence
from typing import Any

import pandas as pd

from ..core import api
from ..core.runner import Cancelled
from ..core.types import ControlAssessment, Decision

log = logging.getLogger(__name__)

Message = tuple[str, Any]
Emit = Callable[[Message], None]


def run_task(
    emit: Emit,
    cancel: threading.Event,
    df: pd.DataFrame,
    params: dict[str, Any],
    decisions: Sequence[Decision],
    assessments: Sequence[ControlAssessment],
) -> None:
    """Build the specs, run every universe, mark validity, run the luck check, summarise."""
    specs = api.build_specs(
        decisions, max_specs=params["max_specs"], sample_if_over=True, seed=params["seed"]
    )
    emit(("specs", specs))
    emit(("stage", "run"))
    results = []
    for r in api.iter_multiverse(
        df,
        params["y"],
        params["x"],
        params["family"],
        decisions,
        specs,
        alpha=params["alpha"],
        cancel=cancel,
    ):
        results.append(r)
        emit(("result", r))
    if cancel.is_set():
        raise Cancelled()
    results = api.mark_validity(results, decisions, assessments)
    emit(("validated", results))
    perm_p = None
    if params["n_permutations"] and any(r.ok and r.valid for r in results):
        emit(("stage", "perm"))
        perm_p = api.permutation_test(
            df,
            params["y"],
            params["x"],
            params["family"],
            decisions,
            specs,
            results,
            n_permutations=params["n_permutations"],
            alpha=params["alpha"],
            seed=params["seed"],
            progress=lambda i, n: emit(("perm", (i, n))),
            cancel=cancel,
        )
    emit(("stage", "verdict"))
    emit(("verdict", api.summarize(results, alpha=params["alpha"], permutation_p=perm_p)))


class RunJob:
    """One background run. Create a new job for every run."""

    def __init__(
        self,
        df: pd.DataFrame,
        params: dict[str, Any],
        decisions: Sequence[Decision],
        assessments: Sequence[ControlAssessment],
        task: Callable[..., None] = run_task,
    ) -> None:
        self.queue: queue.Queue[Message] = queue.Queue()
        self.cancel_event = threading.Event()
        self._args = (df, params, list(decisions), list(assessments))
        self._task = task
        self.thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def start(self) -> None:
        if self.thread is not None:
            raise RuntimeError("This job has already been started.")

        def run() -> None:
            try:
                self._task(self.queue.put, self.cancel_event, *self._args)
                self.queue.put(
                    ("cancelled", None) if self.cancel_event.is_set() else ("done", None)
                )
            except Cancelled:
                self.queue.put(("cancelled", None))
            except Exception as exc:  # report every failure to the UI
                log.error("Background run failed:\n%s", traceback.format_exc())
                self.queue.put(("error", str(exc) or type(exc).__name__))

        self.thread = threading.Thread(target=run, name="multiverse-run", daemon=True)
        self.thread.start()

    def cancel(self) -> None:
        self.cancel_event.set()

    def drain(self, limit: int = 100_000) -> list[Message]:
        """Every message waiting in the queue (non-blocking)."""
        out: list[Message] = []
        for _ in range(limit):
            try:
                out.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return out

    def wait(self, timeout: float | None = None) -> None:
        """Block until the thread ends (used by tests and scripts)."""
        if self.thread is not None:
            self.thread.join(timeout)

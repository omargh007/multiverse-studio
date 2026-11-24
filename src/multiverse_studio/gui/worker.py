"""Run long tasks off the Tk main thread so the window never freezes.

Pattern (required by the brief):
  * ``Worker.start(task, on_message, ...)`` runs ``task(emit, cancel, ...)`` in a
    daemon thread. The task reports through ``emit((kind, payload))``, which only
    puts the message on a ``queue.Queue``.
  * The worker polls the queue with ``widget.after(50, ...)`` and calls
    ``on_message(kind, payload)`` on the main thread. Tk widgets are never
    touched from the worker thread.
  * ``Worker.cancel()`` sets a ``threading.Event`` that the core runner checks.

Final messages are always one of: ("done", None), ("cancelled", None) or
("error", message).
"""

from __future__ import annotations

import logging
import queue
import threading
import traceback
from collections.abc import Callable
from typing import Any

from ..core.runner import Cancelled

log = logging.getLogger(__name__)

Message = tuple[str, Any]
POLL_MS = 50
MAX_PER_POLL = 400


class Worker:
    def __init__(self, widget) -> None:
        self.widget = widget
        self.queue: queue.Queue[Message] = queue.Queue()
        self.cancel_event = threading.Event()
        self.thread: threading.Thread | None = None
        self._on_message: Callable[[str, Any], None] | None = None

    @property
    def running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def start(self, task: Callable[..., None], on_message: Callable[[str, Any], None], *args):
        if self.running:
            raise RuntimeError("A task is already running.")
        self.cancel_event.clear()
        self._on_message = on_message

        def run() -> None:
            try:
                task(self.queue.put, self.cancel_event, *args)
                self.queue.put(
                    ("cancelled", None) if self.cancel_event.is_set() else ("done", None)
                )
            except Cancelled:
                self.queue.put(("cancelled", None))
            except Exception as exc:  # report every failure to the UI
                log.error("Background task failed:\n%s", traceback.format_exc())
                self.queue.put(("error", str(exc) or type(exc).__name__))

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        self.widget.after(POLL_MS, self._poll)

    def cancel(self) -> None:
        self.cancel_event.set()

    def _poll(self) -> None:
        for _ in range(MAX_PER_POLL):
            try:
                kind, payload = self.queue.get_nowait()
            except queue.Empty:
                break
            if self._on_message is not None:
                self._on_message(kind, payload)
        if self.running or not self.queue.empty():
            self.widget.after(POLL_MS, self._poll)

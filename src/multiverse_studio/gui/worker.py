"""Run long tasks off the Tk main thread. Owner: B (GUI).

Pattern (required by the brief - the window must never freeze):
  * ``Worker.start(fn, *args)`` runs ``fn`` in a ``threading.Thread(daemon=True)``.
  * The task reports via a ``queue.Queue`` (progress, partial results, done, error).
  * The page polls the queue with ``widget.after(50, poll)`` and updates widgets
    ONLY from the main thread. Tk widgets are never touched from the worker.
  * ``Worker.cancel()`` sets a ``threading.Event`` passed to the core runner.
"""

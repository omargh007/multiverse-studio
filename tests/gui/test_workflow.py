"""End-to-end GUI smoke test: example data -> question -> choices -> guardrails -> run -> results.

Skipped automatically where no display is available (e.g. headless Linux CI).
"""

from __future__ import annotations

import time
import tkinter

import pytest

from multiverse_studio.core.types import GuardrailAnswers


@pytest.fixture
def app():
    try:
        from multiverse_studio.gui.app import App

        application = App()
    except tkinter.TclError as exc:  # no display
        pytest.skip(f"No display available: {exc}")
    application.withdraw()
    yield application
    application.destroy()


def _pump(app, seconds=0.2):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.update()


def test_full_workflow(app):
    assert app.current == 0 and not app.reachable(1)
    app.page("data").load_example("mediated")
    app.next()
    q = app.page("question")
    q.y_menu.set("grade")
    q.x_menu.set("sleep_hours")
    q.on_change()
    assert app.session.family == "linear"
    app.next()
    assert app.current == 2 and app.suggested
    app.next()
    app.session.guardrails["tiredness"] = GuardrailAnswers(False, True, False)
    app.page("guardrails").on_show()
    app.next()
    run = app.page("run")
    run.perm_menu.set("Skip")
    run.on_option()
    app.next()  # lock plan and run (blind mode is on by default)
    assert app.session.blind is not None
    deadline = time.monotonic() + 120
    while (run.worker.running or app.session.verdict is None) and time.monotonic() < deadline:
        _pump(app, 0.1)
    assert app.session.verdict is not None
    assert app.session.verdict.n_valid < len(app.session.results)  # guardrails excluded some
    app.next()
    res = app.page("results")
    res.cherry_entry.insert(0, "99")
    res.check_cherry()
    assert app.session.cherry_pick.flagged
    app.next()
    assert app.current == 6


def test_invalidation_records_changed_plan(app):
    app.page("data").load_example("real_effect")
    s = app.session
    s.y, s.x, s.family = "grade", "sleep_hours", "linear"
    from multiverse_studio.core import api

    s.blind = api.lock_plan(s)
    s.results = [object()]  # pretend results were shown
    app.invalidate_plan("choices")
    assert s.blind is None and s.results == []
    assert "was changed" in s.notes

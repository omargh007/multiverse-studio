"""Theme tokens, launcher arguments, charts and the background job."""

from __future__ import annotations

import threading

from multiverse_studio.core import api
from multiverse_studio.core.runner import Cancelled
from multiverse_studio.gui import charts
from multiverse_studio.gui.jobs import RunJob
from multiverse_studio.gui.launch import streamlit_args
from multiverse_studio.gui.theme import COLORS, css, streamlit_theme_flags, tokens


def test_tokens_and_css():
    light, dark = tokens(False), tokens(True)
    assert light["button"] == dark["button"] == "#256abf"
    assert set(light) == set(COLORS)
    sheet = css(dark=True, scale=1.3)
    assert "zoom: 1.3" in sheet and dark["panel"] in sheet and "color-scheme: dark" in sheet


def test_launch_is_local_and_themed():
    args = streamlit_args(["--server.port", "8600"])
    assert args[0] == "run" and args[1].endswith("app.py")
    assert "--server.address=localhost" in args
    assert "--browser.gatherUsageStats=false" in args
    assert args[-2:] == ["--server.port", "8600"]
    flags = streamlit_theme_flags()
    assert "--theme.light.primaryColor=#256abf" in flags
    assert "--theme.dark.backgroundColor=#0b1220" in flags
    assert all(f.startswith("--theme.") for f in flags)


def test_curve_frame_and_specs():
    from multiverse_studio.core.types import GuardrailAnswers

    df = api.simulate("collider", n=200, seed=3)
    dec = api.suggest_decisions(api.profile_data(df), "grade", "sleep_hours", df)
    specs = api.build_specs(dec, max_specs=60, seed=3)
    res = api.run_multiverse(df, "grade", "sleep_hours", "linear", dec, specs)
    res = api.mark_validity(
        res, dec, api.assess_controls({"scholarship": GuardrailAnswers(False, True, True)})
    )
    frame = charts.curve_frame(res, dec, 0.05)
    assert list(frame["rank"]) == list(range(1, len(frame) + 1))
    assert frame["estimate"].is_monotonic_increasing
    assert set(frame["fair"]) == {"Fair", "Left out"}
    only_fair = charts.curve_frame(res, dec, 0.05, show_invalid=False)
    assert set(only_fair["fair"]) == {"Fair"}

    spec = charts.to_spec(charts.spec_curve_chart(res, dec, reported_estimate=1.0, dark=True))
    assert "pick" in str(spec) and spec["$schema"].startswith("https://vega.github.io")
    panel = charts.choices_chart(res, dec)
    assert panel is not None
    rows = {d["row"] for d in charts.to_spec(panel)["datasets"].popitem()[1]}
    labels = [charts.row_label(d, o.label) for d in dec if len(d.options) > 1 for o in d.options]
    assert rows <= set(labels) and len(labels) == len(set(labels))  # names never collide
    live = charts.to_spec(charts.live_curve_chart(res[:10], alpha=0.05, dark=False))
    assert "pick" not in str(live)
    assert charts.choices_chart([], dec) is None


def test_job_reports_every_outcome():
    def ok(emit, cancel, *args):
        emit(("hello", 1))

    job = RunJob(None, {}, [], [], task=ok)
    job.start()
    job.wait(5)
    assert job.drain() == [("hello", 1), ("done", None)] and not job.running

    def stops(emit, cancel, *args):
        raise Cancelled()

    job = RunJob(None, {}, [], [], task=stops)
    job.start()
    job.wait(5)
    assert job.drain() == [("cancelled", None)]

    started = threading.Event()

    def waits(emit, cancel, *args):
        started.set()
        cancel.wait(5)

    job = RunJob(None, {}, [], [], task=waits)
    job.start()
    started.wait(5)
    job.cancel()
    job.wait(5)
    assert job.drain()[-1] == ("cancelled", None)
    try:
        job.start()
    except RuntimeError:
        pass
    else:  # pragma: no cover
        raise AssertionError("a job can only start once")

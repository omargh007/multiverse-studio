from __future__ import annotations

import threading

import pytest

from multiverse_studio.core import api
from multiverse_studio.core.inference import summarize
from multiverse_studio.core.runner import Cancelled, iter_multiverse
from tests.conftest import make_result


def test_progress_and_results(real_run):
    df, decisions, specs, results = real_run
    seen = []
    out = list(
        iter_multiverse(
            df,
            "grade",
            "sleep_hours",
            "linear",
            decisions,
            specs[:5],
            progress=lambda d, t: seen.append((d, t)),
        )
    )
    assert len(out) == 5 and seen[-1] == (5, 5)
    assert len(results) == len(specs) and all(r.ok for r in results)


def test_cancel_stops_early(real_run):
    df, decisions, specs, _ = real_run
    cancel = threading.Event()
    out = []
    for r in iter_multiverse(df, "grade", "sleep_hours", "linear", decisions, specs, cancel=cancel):
        out.append(r)
        if len(out) == 3:
            cancel.set()
    assert len(out) == 3


def test_real_effect_is_consistent_and_close_to_truth(real_run):
    _, _, _, results = real_run
    v = summarize(results)
    assert v.label == "consistent"
    assert v.median_estimate == pytest.approx(3.0, abs=0.6)
    assert v.share_significant > 0.9


def test_label_rules_d2():
    pos = [make_result(i, 1.0, 0.01) for i in range(10)]
    assert summarize(pos, permutation_p=0.01).label == "consistent"
    assert summarize(pos, permutation_p=0.2).label == "fragile"
    mixed = [make_result(i, 1.0, 0.01) for i in range(8)] + [
        make_result(9, -1, 0.01),
        make_result(10, -1, 0.3),
    ]
    assert summarize(mixed, permutation_p=0.01).label == "mixed"
    weak = [make_result(i, 0.5, 0.4) for i in range(10)]
    assert summarize(weak).label == "fragile"
    assert "not run" in summarize(weak).explanation


def test_summary_ignores_invalid_and_failed():
    rs = [
        make_result(0, 1.0, 0.01),
        make_result(1, -5, 0.01, valid=False),
        make_result(2, 0, 0, error="x"),
    ]
    v = summarize(rs)
    assert (v.n_specs, v.n_ok, v.n_valid) == (3, 2, 1)
    with pytest.raises(ValueError, match="None of the analyses"):
        summarize([make_result(0, 0, 0, error="x")])


def test_permutation_detects_real_effect_and_is_seeded(real_run):
    df, decisions, specs, results = real_run
    few = specs[:6]
    obs = [r for r in results if r.spec_id in {s.id for s in few}]
    kw = dict(n_permutations=19, seed=3)
    p1 = api.permutation_test(df, "grade", "sleep_hours", "linear", decisions, few, obs, **kw)
    p2 = api.permutation_test(df, "grade", "sleep_hours", "linear", decisions, few, obs, **kw)
    assert p1 == p2 == pytest.approx(1 / 20)


def test_permutation_no_effect_is_not_significant():
    df = api.simulate("no_effect", n=200, seed=2)
    decisions = []
    specs = api.build_specs(decisions)
    obs = api.run_multiverse(df.dropna(), "grade", "sleep_hours", "linear", decisions, specs)
    p = api.permutation_test(
        df.dropna(),
        "grade",
        "sleep_hours",
        "linear",
        decisions,
        specs,
        obs,
        n_permutations=30,
        seed=1,
    )
    assert p > 0.05


def test_permutation_cancel_and_bad_n(real_run):
    df, decisions, specs, results = real_run
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(Cancelled):
        api.permutation_test(
            df,
            "grade",
            "sleep_hours",
            "linear",
            decisions,
            specs[:2],
            results,
            n_permutations=5,
            cancel=cancel,
        )
    with pytest.raises(ValueError):
        api.permutation_test(
            df, "grade", "sleep_hours", "linear", decisions, specs, results, n_permutations=0
        )

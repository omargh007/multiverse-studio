from __future__ import annotations

import pytest

from multiverse_studio.core import api
from multiverse_studio.core.types import GuardrailAnswers, Session
from tests.conftest import make_result


def test_blind_view_shuffles_y_only_and_is_seeded(real_df):
    a = api.blind_view(real_df, "grade", seed=5)
    b = api.blind_view(real_df, "grade", seed=5)
    assert a["grade"].tolist() == b["grade"].tolist()
    assert sorted(a["grade"].dropna()) == sorted(real_df["grade"].dropna())
    assert a["grade"].tolist() != real_df["grade"].tolist()
    assert a["sleep_hours"].equals(real_df["sleep_hours"])


def _session(tmp_path, real_run):
    df, decisions, _, _ = real_run
    f = tmp_path / "data.csv"
    df.to_csv(f, index=False)
    return Session(
        data_path=str(f),
        y="grade",
        x="sleep_hours",
        family="linear",
        decisions=list(decisions),
        guardrails={"study_hours": GuardrailAnswers(True, False, False)},
    )


def test_lock_and_verify_plan(tmp_path, real_run):
    s = _session(tmp_path, real_run)
    lock = api.lock_plan(s)
    assert len(lock.sha256) == 64 and lock.locked_at.endswith("+00:00")
    assert lock.plan["data_sha256"] and api.verify_plan(s, lock)
    s.alpha = 0.10  # tamper with the plan
    assert not api.verify_plan(s, lock)


def test_editing_the_data_breaks_the_lock(tmp_path, real_run):
    s = _session(tmp_path, real_run)
    lock = api.lock_plan(s)
    with open(s.data_path, "a", encoding="utf-8") as f:
        f.write("1,2,3,no,1,1,1\n")
    assert not api.verify_plan(s, lock)


def test_results_do_not_change_the_plan_hash(tmp_path, real_run):
    s = _session(tmp_path, real_run)
    h = api.plan_hash(s)
    s.results = list(real_run[3])
    assert api.plan_hash(s) == h


def test_cherry_pick():
    rs = [make_result(i, float(i), 0.01) for i in range(1, 21)]  # 1..20
    hi = api.cherry_pick_check(rs, 25.0)
    assert hi.flagged and hi.share_weaker == 1.0 and "stronger than all" in hi.explanation
    mid = api.cherry_pick_check(rs, 10.5)
    assert not mid.flagged and mid.share_weaker == pytest.approx(0.5)
    neg = api.cherry_pick_check([make_result(i, -float(i), 0.01) for i in range(1, 21)], -19.5)
    assert neg.flagged
    with pytest.raises(ValueError):
        api.cherry_pick_check([make_result(0, 1, 0.1, valid=False)], 1.0)


def test_importance_finds_the_decision_that_matters():
    rs = []
    for i, (a, b) in enumerate([(a, b) for a in "xy" for b in "pq"] * 3):
        est = (5.0 if a == "y" else 0.0) + (0.1 if b == "q" else 0.0)
        rs.append(make_result(i, est, 0.01, choices={"A": a, "B": b}))
    from multiverse_studio.core.types import Decision, DecisionKind, Option

    decs = [
        Decision("A", DecisionKind.CONTROLS, "A", (Option("x", "x"), Option("y", "y"))),
        Decision("B", DecisionKind.OUTLIERS, "B", (Option("p", "p"), Option("q", "q"))),
    ]
    imp = api.decision_importance(rs, decs)
    assert list(imp) == ["A", "B"] and imp["A"] > 0.99
    assert api.decision_importance([], decs) == {"A": 0.0, "B": 0.0}
    flat = [make_result(i, 1.0, 0.01, choices={"A": "x", "B": "p"}) for i in range(3)]
    assert api.decision_importance(flat, decs)["A"] == 0.0

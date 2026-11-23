from __future__ import annotations

import pandas as pd
import pytest

from multiverse_studio.core.choices import suggest_decisions
from multiverse_studio.core.profiling import profile_data
from multiverse_studio.core.types import DecisionKind


def test_suggestions_for_simulated_students(real_df):
    decisions = suggest_decisions(profile_data(real_df), "grade", "sleep_hours", real_df)
    kinds = {d.kind for d in decisions}
    assert {DecisionKind.OUTLIERS, DecisionKind.CONTROLS, DecisionKind.MISSING} <= kinds
    controls = next(d for d in decisions if d.kind is DecisionKind.CONTROLS)
    assert controls.options[0].params["columns"] == []
    assert controls.options[1].params["columns"] == ["study_hours"]
    assert all(d.explanation for d in decisions)


def test_subset_levels_need_30_rows():
    df = pd.DataFrame(
        {"y": range(100), "x": [i % 7 + 0.5 for i in range(100)], "g": ["a"] * 80 + ["b"] * 20}
    )
    decisions = suggest_decisions(profile_data(df), "y", "x", df)
    subset = next(d for d in decisions if d.kind is DecisionKind.SUBSET)
    assert [o.id for o in subset.options] == ["all", "g=a"]


def test_skewed_positive_x_gets_log_option():
    xs = [1.0] * 50 + [2.0] * 20 + [5.0] * 5 + [40.0, 60.0, 90.0]
    df = pd.DataFrame({"y": [v * 0.5 + i % 3 for i, v in enumerate(xs)], "x": xs})
    decisions = suggest_decisions(profile_data(df), "y", "x", df)
    assert any(d.id == "transform_x" for d in decisions)


def test_no_decisions_for_clean_two_column_data():
    df = pd.DataFrame({"y": [1.0, 2.1, 2.9, 4.2, 5.1], "x": [1.1, 2.0, 3.2, 3.9, 5.0]})
    assert suggest_decisions(profile_data(df), "y", "x", df) == []


@pytest.mark.parametrize(
    "y,x,msg", [("y", "y", "different"), ("y", "nope", "not in the data"), ("y", "t", "must be")]
)
def test_invalid_questions(y, x, msg):
    df = pd.DataFrame({"y": [1.0, 2.0, 3.0], "t": ["a", "b", "c"]})
    with pytest.raises(ValueError, match=msg):
        suggest_decisions(profile_data(df), y, x, df)

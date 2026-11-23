from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from multiverse_studio.core.profiling import detect_kind, profile_data, suggest_family
from multiverse_studio.core.types import ColumnKind


@pytest.mark.parametrize(
    "values,kind",
    [
        ([1.5, 2.25, 3.1, 4.0, 5.2], ColumnKind.NUMERIC),
        ([0, 1, 0, 1, None], ColumnKind.BINARY),
        (["yes", "no", "yes"], ColumnKind.BINARY),
        ([True, False, True], ColumnKind.BINARY),
        ([0, 1, 2, 5, 3, 0], ColumnKind.COUNT),
        ([-1, 2, 3, 4], ColumnKind.NUMERIC),
        (["a", "b", "c", "a"], ColumnKind.CATEGORICAL),
        (list(range(200)), ColumnKind.NUMERIC),
    ],
)
def test_detect_kind(values, kind):
    assert detect_kind(pd.Series(values)) is kind


def test_text_and_datetime():
    assert detect_kind(pd.Series([f"id{i}" for i in range(100)])) is ColumnKind.TEXT
    assert detect_kind(pd.Series(pd.date_range("2026-01-01", periods=5))) is ColumnKind.DATETIME


def test_profile_counts_missing_skew_and_outliers():
    rng = np.random.default_rng(0)
    vals = np.append(rng.normal(0, 1, 200), [25.0])
    df = pd.DataFrame({"v": vals, "g": ["a", "b"] * 100 + [None]})
    p = profile_data(df)
    v = p.column("v")
    assert p.n_rows == 201
    assert v.kind is ColumnKind.NUMERIC and v.n_outliers_3sd >= 1 and v.skewness > 1
    assert p.column("g").n_missing == 1


def test_constant_column_has_no_skew():
    p = profile_data(pd.DataFrame({"c": [1.5] * 10}))
    assert p.column("c").skewness is None


@pytest.mark.parametrize(
    "values,family",
    [([1.2, 3.4, 5.6, 7.1], "linear"), ([0, 1, 1, 0], "logistic"), ([0, 1, 4, 2, 3], "poisson")],
)
def test_suggest_family(values, family):
    assert suggest_family(profile_data(pd.DataFrame({"y": values})), "y") == family


def test_suggest_family_rejects_categories():
    with pytest.raises(ValueError, match="outcome must be"):
        suggest_family(profile_data(pd.DataFrame({"y": ["a", "b", "c"]})), "y")

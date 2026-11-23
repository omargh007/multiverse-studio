from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from multiverse_studio.core.models import fit_one, prepare_data
from multiverse_studio.core.types import Decision, DecisionKind, Option, Spec


def _data(n=200, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n)
    z = rng.normal(0, 1, n)
    y = 2.0 * x + 1.0 * z + rng.normal(0, 1, n)
    return pd.DataFrame({"y": y, "x": x, "z": z, "g": np.where(rng.random(n) < 0.5, "a", "b")})


CONTROLS = Decision(
    "controls",
    DecisionKind.CONTROLS,
    "c",
    (Option("none", "none", {"columns": []}), Option("z", "z", {"columns": ["z"]})),
)


def test_ols_matches_statsmodels_directly():
    df = _data()
    r = fit_one(df, "y", "x", "linear", [CONTROLS], Spec(0, {"controls": "z"}))
    ref = sm.OLS(df["y"], sm.add_constant(df[["x", "z"]])).fit()
    assert r.ok and r.n_obs == 200
    assert r.estimate == pytest.approx(ref.params["x"])
    assert r.p_value == pytest.approx(ref.pvalues["x"])
    assert r.ci_low < r.estimate < r.ci_high


def test_logistic_and_poisson():
    rng = np.random.default_rng(1)
    x = rng.normal(0, 1, 400)
    yb = (rng.random(400) < 1 / (1 + np.exp(-1.5 * x))).astype(int)
    yc = rng.poisson(np.exp(0.5 + 0.4 * x))
    df = pd.DataFrame({"x": x, "yb": yb, "yc": yc})
    rb = fit_one(df, "yb", "x", "logistic", [], Spec(0, {}))
    rc = fit_one(df, "yc", "x", "poisson", [], Spec(0, {}))
    assert rb.estimate == pytest.approx(1.5, abs=0.4)
    assert rc.estimate == pytest.approx(0.4, abs=0.1)


def test_binary_text_outcome_and_categorical_control():
    df = _data()
    df["passed"] = np.where(df["y"] > 0, "yes", "no")
    df["city"] = np.tile(["x", "y", "z", "w"], 50)
    dec = Decision(
        "controls", DecisionKind.CONTROLS, "c", (Option("c", "city", {"columns": ["city"]}),)
    )
    r = fit_one(df, "passed", "x", "logistic", [dec], Spec(0, {"controls": "c"}))
    assert r.ok and r.estimate > 0


def test_processing_order_subset_missing_outliers_transform():
    df = pd.DataFrame(
        {
            "y": [1.0, 2.0, 3.0, 4.0, 100.0, 5.0, None, 6.0] * 5,
            "x": [1.0, 2.0, None, 4.0, 5.0, 6.0, 7.0, 8.0] * 5,
            "g": ["a"] * 20 + ["b"] * 20,
        }
    )
    decisions = [
        Decision("s", DecisionKind.SUBSET, "s", (Option("a", "a", {"column": "g", "value": "a"}),)),
        Decision("m", DecisionKind.MISSING, "m", (Option("mean", "mean", {"method": "mean"}),)),
        Decision(
            "o",
            DecisionKind.OUTLIERS,
            "o",
            (Option("iqr", "iqr", {"rule": "iqr", "k": 1.5, "columns": ["y"]}),),
        ),
        Decision(
            "t", DecisionKind.TRANSFORM, "t", (Option("log", "log", {"column": "x", "fn": "log"}),)
        ),
    ]
    data, controls = prepare_data(
        df, "y", "x", decisions, Spec(0, {"s": "a", "m": "mean", "o": "iqr", "t": "log"})
    )
    assert controls == []
    assert len(data) < 20  # subset to 20 rows, y missing dropped, outlier y=100 dropped
    assert data["y"].max() < 100
    assert data["x"].min() >= 0  # log of values >= 1


def test_errors_are_returned_not_raised():
    df = _data(n=8)
    r = fit_one(df, "y", "x", "linear", [], Spec(0, {}))
    assert not r.ok and "too few" in r.error
    df2 = _data()
    df2["x"] = 1.0
    assert "only one value" in fit_one(df2, "y", "x", "linear", [], Spec(0, {})).error
    bad_log = Decision(
        "t", DecisionKind.TRANSFORM, "t", (Option("log", "log", {"column": "x", "fn": "log"}),)
    )
    r3 = fit_one(_data(), "y", "x", "linear", [bad_log], Spec(0, {"t": "log"}))
    assert "log" in r3.error
    missing_col = Decision(
        "c", DecisionKind.CONTROLS, "c", (Option("q", "q", {"columns": ["nope"]}),)
    )
    assert (
        "not found"
        in fit_one(_data(), "y", "x", "linear", [missing_col], Spec(0, {"c": "q"})).error
    )

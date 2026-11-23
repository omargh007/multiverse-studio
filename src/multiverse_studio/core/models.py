"""Apply one universe's choices to the data and fit the model. Owner: A (Core).

Processing order inside a universe is fixed (docs/decisions.md, D-4):
subset -> missing values -> outliers -> transforms -> fit.
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .types import Decision, DecisionKind, ModelFamily, Option, Spec, SpecResult

MIN_ROWS = 10


class DataPrepError(ValueError):
    """A universe cannot be analysed (plain-language message)."""


def _picked(decisions: Sequence[Decision], spec: Spec) -> list[tuple[Decision, Option]]:
    return [(d, d.option(spec.choices[d.id])) for d in decisions if d.id in spec.choices]


def _as_numeric(series: pd.Series) -> pd.Series:
    """Numbers stay numbers; two-valued labels (yes/no) become 0/1 (sorted order)."""
    if pd.api.types.is_bool_dtype(series):
        return series.astype(float)
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    levels = sorted(series.dropna().astype(str).unique())
    if len(levels) == 2:
        return series.map(lambda v: np.nan if pd.isna(v) else float(str(v) == levels[1]))
    raise DataPrepError(f"'{series.name}' is not numeric and has {len(levels)} levels.")


def prepare_data(
    df: pd.DataFrame, y: str, x: str, decisions: Sequence[Decision], spec: Spec
) -> tuple[pd.DataFrame, list[str]]:
    """Apply subset -> missing -> outliers -> transforms and return (data, controls)."""
    picked = _picked(decisions, spec)
    controls: list[str] = []
    for d, o in picked:
        if d.kind is DecisionKind.CONTROLS:
            controls = list(o.params.get("columns", []))
    used = list(dict.fromkeys([y, x, *controls]))
    missing_cols = [c for c in used if c not in df.columns]
    if missing_cols:
        raise DataPrepError(f"Column(s) not found: {', '.join(missing_cols)}.")
    data = df.loc[:, list(dict.fromkeys([*used, *df.columns]))]

    # 1. subset
    for d, o in picked:
        if d.kind is DecisionKind.SUBSET and o.params.get("column") is not None:
            col = o.params["column"]
            data = data[data[col].astype(str) == str(o.params["value"])]
    data = data.loc[:, used].copy()

    # 2. missing values
    method = "drop"
    for d, o in picked:
        if d.kind is DecisionKind.MISSING:
            method = o.params.get("method", "drop")
    if method == "mean":
        for col in [x, *controls]:
            if pd.api.types.is_numeric_dtype(data[col]):
                data[col] = data[col].fillna(data[col].mean())
    data = data.dropna(subset=used)

    # 3. outliers (thresholds computed on the subset, D-4)
    for d, o in picked:
        if d.kind is not DecisionKind.OUTLIERS or o.params.get("rule", "none") == "none":
            continue
        keep = pd.Series(True, index=data.index)
        k = float(o.params.get("k", 3.0))
        for col in o.params.get("columns", []):
            if col not in data or not pd.api.types.is_numeric_dtype(data[col]):
                continue
            v = data[col].astype(float)
            if o.params["rule"] == "sd":
                sd = v.std(ddof=1)
                if sd > 0:
                    keep &= ((v - v.mean()) / sd).abs() <= k
            elif o.params["rule"] == "iqr":
                q1, q3 = v.quantile(0.25), v.quantile(0.75)
                iqr = q3 - q1
                keep &= (v >= q1 - k * iqr) & (v <= q3 + k * iqr)
        data = data[keep]

    # 4. transforms
    for d, o in picked:
        if d.kind is not DecisionKind.TRANSFORM:
            continue
        col, fn = o.params.get("column"), o.params.get("fn", "raw")
        if fn == "log":
            if (data[col] <= 0).any():
                raise DataPrepError(f"Can't take the log of {col}: it has zero or negative values.")
            data[col] = np.log(data[col].astype(float))
        elif fn == "z":
            sd = data[col].std(ddof=1)
            data[col] = (data[col] - data[col].mean()) / sd if sd > 0 else 0.0

    return data, controls


def _design(
    data: pd.DataFrame, y: str, x: str, controls: list[str]
) -> tuple[pd.Series, pd.DataFrame]:
    endog = _as_numeric(data[y])
    cols: dict[str, pd.Series] = {x: _as_numeric(data[x])}
    exog = pd.DataFrame(cols, index=data.index)
    for c in controls:
        s = data[c]
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
            exog[c] = s.astype(float)
        elif s.dropna().nunique() == 2:
            exog[c] = _as_numeric(s)
        else:
            dummies = pd.get_dummies(s.astype(str), prefix=c, drop_first=True, dtype=float)
            exog = pd.concat([exog, dummies], axis=1)
    exog = sm.add_constant(exog, has_constant="add")
    return endog, exog


def _error(spec: Spec, n: int, msg: str) -> SpecResult:
    return SpecResult(spec.id, dict(spec.choices), None, None, None, None, None, n, error=msg)


def fit_one(
    df: pd.DataFrame,
    y: str,
    x: str,
    family: ModelFamily,
    decisions: Sequence[Decision],
    spec: Spec,
    alpha: float = 0.05,
) -> SpecResult:
    """Fit one universe with statsmodels and return the coefficient of X.

    linear -> OLS, logistic -> Logit, poisson -> Poisson GLM. Categorical
    controls are dummy-coded. Never raises for data problems: returns a
    SpecResult with ``error`` set instead.
    """
    try:
        data, controls = prepare_data(df, y, x, decisions, spec)
        n = len(data)
        endog, exog = _design(data, y, x, controls)
    except DataPrepError as exc:
        return _error(spec, 0, str(exc))

    if n < max(MIN_ROWS, exog.shape[1] + 2):
        return _error(spec, n, f"Only {n} rows left after these choices - too few to fit.")
    if exog[x].nunique() < 2:
        return _error(spec, n, f"'{x}' has only one value in these rows.")
    if family == "logistic" and endog.nunique() < 2:
        return _error(spec, n, f"'{y}' has only one value in these rows.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if family == "linear":
                res = sm.OLS(endog, exog).fit()
            elif family == "logistic":
                res = sm.Logit(endog, exog).fit(disp=0, maxiter=200)
            elif family == "poisson":
                res = sm.GLM(endog, exog, family=sm.families.Poisson()).fit()
            else:
                return _error(spec, n, f"Unknown model family '{family}'.")
        est = float(res.params[x])
        se = float(res.bse[x])
        p = float(res.pvalues[x])
        lo, hi = (float(v) for v in res.conf_int(alpha=alpha).loc[x])
    except Exception as exc:  # statsmodels raises many types (separation, singular matrix...)
        return _error(spec, n, f"The model could not be fitted: {exc}")

    if not all(np.isfinite(v) for v in (est, se, p)):
        return _error(spec, n, "The model did not converge (non-finite estimate).")
    return SpecResult(spec.id, dict(spec.choices), est, se, p, lo, hi, n)

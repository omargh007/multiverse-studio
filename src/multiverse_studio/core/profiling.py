"""Detect column types and pick the regression family. Owner: A (Core)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .types import ColumnInfo, ColumnKind, DataProfile, ModelFamily

MAX_COUNT_LEVELS = 50
MAX_CATEGORY_LEVELS = 20


def detect_kind(series: pd.Series) -> ColumnKind:
    """Classify one column.

    Rules (in order):
      1. datetime dtype -> DATETIME
      2. exactly 2 distinct non-missing values (or boolean) -> BINARY
      3. numeric, all values whole numbers >= 0, 3..50 distinct values -> COUNT
      4. numeric -> NUMERIC
      5. non-numeric with <= 20 distinct values (or <= 5% of rows) -> CATEGORICAL
      6. otherwise -> TEXT
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return ColumnKind.DATETIME
    values = series.dropna()
    n_unique = values.nunique()
    if pd.api.types.is_bool_dtype(series) or n_unique == 2:
        return ColumnKind.BINARY
    if pd.api.types.is_numeric_dtype(series):
        arr = values.to_numpy(dtype=float)
        whole = arr.size > 0 and bool(np.all(arr >= 0) and np.all(np.mod(arr, 1) == 0))
        if whole and 3 <= n_unique <= MAX_COUNT_LEVELS:
            return ColumnKind.COUNT
        return ColumnKind.NUMERIC
    if n_unique <= MAX_CATEGORY_LEVELS or n_unique <= 0.05 * max(len(values), 1):
        return ColumnKind.CATEGORICAL
    return ColumnKind.TEXT


def _profile_column(name: str, series: pd.Series) -> ColumnInfo:
    kind = detect_kind(series)
    values = series.dropna()
    skew: float | None = None
    n_out = 0
    if kind in (ColumnKind.NUMERIC, ColumnKind.COUNT) and len(values) > 2:
        arr = values.to_numpy(dtype=float)
        sd = arr.std(ddof=1)
        if sd > 0:
            skew = float(pd.Series(arr).skew())
            n_out = int(np.sum(np.abs((arr - arr.mean()) / sd) > 3))
    return ColumnInfo(
        name=str(name),
        kind=kind,
        n_missing=int(series.isna().sum()),
        n_unique=int(values.nunique()),
        skewness=skew,
        n_outliers_3sd=n_out,
    )


def profile_data(df: pd.DataFrame) -> DataProfile:
    """Kind, missing count, unique count, skewness and 3-SD outlier count for every column."""
    return DataProfile(
        n_rows=len(df),
        columns=tuple(_profile_column(str(c), df[c]) for c in df.columns),
    )


def suggest_family(profile: DataProfile, y: str) -> ModelFamily:
    """BINARY -> "logistic", COUNT -> "poisson", NUMERIC -> "linear".

    Raises ValueError with a plain-language message for other outcome types.
    """
    kind = profile.column(y).kind
    if kind is ColumnKind.BINARY:
        return "logistic"
    if kind is ColumnKind.COUNT:
        return "poisson"
    if kind is ColumnKind.NUMERIC:
        return "linear"
    raise ValueError(
        f"'{y}' holds {kind.value} values. The outcome must be a number, "
        "a yes/no column or a count."
    )

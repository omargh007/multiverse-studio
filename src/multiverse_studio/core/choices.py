"""Suggest defensible analytic choices from the data. Owner: A (Core).

Suggestions are rule-based (no AI), so they are explainable and testable.
The GUI shows them as ticked options; the user has the final say and can
untick options or remove whole decisions.
"""

from __future__ import annotations

import pandas as pd

from .types import ColumnKind, DataProfile, Decision, DecisionKind, Option

MAX_CONTROLS = 4
MAX_SUBSET_DECISIONS = 2
MIN_SUBSET_ROWS = 30
SKEW_THRESHOLD = 1.0

PREDICTOR_KINDS = (ColumnKind.NUMERIC, ColumnKind.COUNT, ColumnKind.BINARY)
CONTROL_KINDS = (ColumnKind.NUMERIC, ColumnKind.COUNT, ColumnKind.BINARY, ColumnKind.CATEGORICAL)
CONTINUOUS = (ColumnKind.NUMERIC, ColumnKind.COUNT)


def validate_question(profile: DataProfile, y: str, x: str) -> None:
    """Raise ValueError (plain language) if X -> Y is not a question we can model."""
    if y == x:
        raise ValueError("The outcome and the factor must be different columns.")
    for col in (y, x):
        if col not in profile.names:
            raise ValueError(f"Column '{col}' is not in the data.")
    if profile.column(x).kind not in PREDICTOR_KINDS:
        raise ValueError(
            f"'{x}' must be a number or a yes/no column to be used as the factor "
            f"(it looks like {profile.column(x).kind.value})."
        )


def _outliers(profile: DataProfile, y: str, x: str) -> Decision | None:
    cols = [
        c
        for c in (x, y)
        if profile.column(c).kind in CONTINUOUS and profile.column(c).n_outliers_3sd > 0
    ]
    if not cols:
        return None
    names = " and ".join(cols)
    return Decision(
        id="outliers",
        kind=DecisionKind.OUTLIERS,
        label="Extreme values",
        explanation=f"A few unusual values in {names} can pull the result up or down.",
        options=(
            Option("none", "Keep all", {"rule": "none"}),
            Option("sd3", "Drop beyond 3 SD", {"rule": "sd", "k": 3.0, "columns": cols}),
            Option("iqr", "Drop beyond 1.5 IQR", {"rule": "iqr", "k": 1.5, "columns": cols}),
        ),
    )


def _controls(profile: DataProfile, y: str, x: str) -> tuple[Decision | None, list[str]]:
    candidates = [
        c.name
        for c in profile.columns
        if c.name not in (x, y)
        and c.kind in CONTROL_KINDS
        and not (c.kind is ColumnKind.CATEGORICAL and c.n_unique > 10)
    ][:MAX_CONTROLS]
    if not candidates:
        return None, []
    options = [Option("none", "Nothing", {"columns": []})]
    for i in range(1, len(candidates) + 1):
        cols = candidates[:i]
        options.append(Option(f"c{i}", " + ".join(cols), {"columns": cols}))
    decision = Decision(
        id="controls",
        kind=DecisionKind.CONTROLS,
        label="Things to keep equal",
        explanation=(
            "Compare cases that are alike in these ways, so another factor doesn't fake the effect."
        ),
        options=tuple(options),
    )
    return decision, candidates


def _subsets(profile: DataProfile, y: str, x: str, df: pd.DataFrame | None) -> list[Decision]:
    out: list[Decision] = []
    for col in profile.columns:
        if len(out) >= MAX_SUBSET_DECISIONS:
            break
        if col.name in (x, y) or col.kind not in (ColumnKind.CATEGORICAL, ColumnKind.BINARY):
            continue
        if not 2 <= col.n_unique <= 6:
            continue
        if df is not None:
            counts = df[col.name].dropna().astype(str).value_counts()
            levels = [str(v) for v, n in counts.items() if n >= MIN_SUBSET_ROWS]
            levels.sort()
        else:
            levels = []
        if not levels:
            continue
        options = [Option("all", "Everyone", {"column": None})]
        options += [
            Option(f"{col.name}={v}", f"Only {col.name} = {v}", {"column": col.name, "value": v})
            for v in levels
        ]
        out.append(
            Decision(
                id=f"subset_{col.name}",
                kind=DecisionKind.SUBSET,
                label=f"Who to include ({col.name})",
                explanation=f"Does the result hold for everyone, or only some {col.name} groups?",
                options=tuple(options),
            )
        )
    return out


def _transforms(
    profile: DataProfile, y: str, x: str, df: pd.DataFrame | None, linear: bool
) -> list[Decision]:
    out: list[Decision] = []
    targets = [("x", x)] + ([("y", y)] if linear else [])
    for role, col in targets:
        info = profile.column(col)
        if info.kind not in CONTINUOUS or info.skewness is None:
            continue
        if abs(info.skewness) <= SKEW_THRESHOLD:
            continue
        if df is None or not bool((df[col].dropna() > 0).all()):
            continue
        out.append(
            Decision(
                id=f"transform_{role}",
                kind=DecisionKind.TRANSFORM,
                label=f"How to measure {col}",
                explanation=f"{col} is skewed; a log scale is a common, defensible alternative.",
                options=(
                    Option("raw", "As is", {"column": col, "fn": "raw"}),
                    Option("log", "Log scale", {"column": col, "fn": "log"}),
                ),
            )
        )
    return out


def _missing(profile: DataProfile, used: list[str]) -> Decision | None:
    missing_cols = [c for c in used if profile.column(c).n_missing > 0]
    if not missing_cols:
        return None
    total = sum(profile.column(c).n_missing for c in missing_cols)
    return Decision(
        id="missing",
        kind=DecisionKind.MISSING,
        label="Missing answers",
        explanation=f"{total} values are missing in {', '.join(missing_cols)}.",
        options=(
            Option("drop", "Leave those rows out", {"method": "drop"}),
            Option("mean", "Fill numbers with the average", {"method": "mean"}),
        ),
    )


def suggest_decisions(
    profile: DataProfile, y: str, x: str, df: pd.DataFrame | None = None
) -> list[Decision]:
    """Return suggested decisions for an X -> Y question.

    Rules:
      * OUTLIERS ("outliers"): if X or Y (numeric) has values beyond 3 SD:
        keep all / drop beyond 3 SD / drop beyond 1.5 IQR.
      * CONTROLS ("controls"): up to 4 other numeric/binary/categorical columns
        (categorical with <= 10 levels), as nested sets: nothing, +c1, +c1+c2, ...
      * SUBSET ("subset_<col>"): up to 2 categorical/binary columns with 2-6
        levels; options "everyone" plus each level with >= 30 rows (needs ``df``).
      * TRANSFORM ("transform_x"/"transform_y"): if |skewness| > 1 and all
        values > 0 (needs ``df``): as is / log. Y only for linear models.
      * MISSING ("missing"): if X, Y or a candidate control has missing values:
        leave rows out / fill numbers with the average.

    Raises ValueError (plain language) when X -> Y cannot be modelled.
    """
    validate_question(profile, y, x)
    y_kind = profile.column(y).kind
    linear = y_kind is ColumnKind.NUMERIC

    decisions: list[Decision] = []
    outliers = _outliers(profile, y, x)
    if outliers:
        decisions.append(outliers)
    controls, candidates = _controls(profile, y, x)
    if controls:
        decisions.append(controls)
    decisions += _subsets(profile, y, x, df)
    decisions += _transforms(profile, y, x, df, linear)
    missing = _missing(profile, [y, x, *candidates])
    if missing:
        decisions.append(missing)
    return decisions

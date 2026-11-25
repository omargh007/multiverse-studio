"""Interactive charts for the Streamlit interface (Altair / Vega-Lite).

Same encoding as the Matplotlib figures in ``plots/`` (which the PDF export
uses): estimates sorted from smallest to largest, 95% intervals, colour for
significance, and hollow markers for analyses the fair-comparison questions
left out, so colour never carries meaning alone. Colours come from
``plots.palette``. No Streamlit import.
"""

from __future__ import annotations

from collections.abc import Sequence

import altair as alt
import pandas as pd

from ..core.types import Decision, SpecResult
from ..plots.palette import palette
from ..plots.spec_curve import categorize, short
from .theme import FONT_STACK

CATEGORY_NAMES = {
    "same": "Significant, same direction",
    "opp": "Significant, opposite direction",
    "ns": "Not significant",
}
SELECTION = "pick"


def curve_frame(
    results: Sequence[SpecResult],
    decisions: Sequence[Decision],
    alpha: float,
    show_invalid: bool = True,
) -> pd.DataFrame:
    """One row per fitted analysis, sorted by estimate, with its rank and labels."""
    shown = sorted(
        (r for r in results if r.ok and (show_invalid or r.valid)), key=lambda r: r.estimate
    )
    cats, _ = categorize(shown, alpha)
    rows = []
    for rank, (r, cat) in enumerate(zip(shown, cats, strict=True), start=1):
        rows.append(
            {
                "rank": rank,
                "spec_id": r.spec_id,
                "estimate": r.estimate,
                "ci_low": r.ci_low if r.ci_low is not None else r.estimate,
                "ci_high": r.ci_high if r.ci_high is not None else r.estimate,
                "p": r.p_value,
                "category": CATEGORY_NAMES[cat],
                "fair": "Fair" if r.valid else "Left out",
                "choices": " · ".join(
                    d.option(r.choices[d.id]).label
                    for d in decisions
                    if d.id in r.choices and len(d.options) > 1
                )
                or "Standard analysis",
            }
        )
    return pd.DataFrame(rows)


def _colors(dark: bool) -> alt.Scale:
    pal = palette(dark)
    return alt.Scale(
        domain=list(CATEGORY_NAMES.values()),
        range=[pal.sig_same, pal.sig_opposite, pal.not_significant],
    )


def _config(chart: alt.TopLevelMixin, dark: bool) -> alt.TopLevelMixin:
    pal = palette(dark)
    return (
        chart.configure(background="transparent", font=FONT_STACK)
        .configure_view(stroke=None)
        .configure_axis(
            labelColor=pal.text_secondary,
            titleColor=pal.text_secondary,
            gridColor=pal.grid,
            domainColor=pal.axis,
            tickColor=pal.axis,
            labelFontSize=12,
            titleFontSize=12,
            titleFontWeight="normal",
        )
    )


AXIS_GUTTER = 230
"""Fixed width of the y-axis area, so the curve and the choices panel line up."""


def _x(n: int) -> alt.X:
    return alt.X(
        "rank:Q", title=None, axis=None, scale=alt.Scale(domain=[0.5, n + 0.5], nice=False)
    )


def spec_curve_chart(
    results: Sequence[SpecResult],
    decisions: Sequence[Decision],
    *,
    alpha: float = 0.05,
    show_invalid: bool = True,
    reported_estimate: float | None = None,
    dark: bool = False,
    y_label: str = "Effect",
    interactive: bool = True,
    height: int = 260,
    gutter: int | None = AXIS_GUTTER,
) -> alt.TopLevelMixin:
    """The specification curve: sorted estimates, 95% intervals, significance colour.

    With ``interactive=True`` a click selects one analysis (selection name
    ``"pick"``, field ``spec_id``); the app shows its details.
    """
    pal = palette(dark)
    df = curve_frame(results, decisions, alpha, show_invalid)
    if df.empty:
        df = pd.DataFrame(
            columns=["rank", "spec_id", "estimate", "ci_low", "ci_high", "p", "category", "fair"]
        )
    n = max(len(df), 1)
    x = _x(n)
    yaxis = (
        alt.Axis(
            minExtent=gutter,
            maxExtent=gutter,
            title=y_label or None,
            titleAngle=0,
            titleAlign="right",
            titleAnchor="end",
            titleBaseline="bottom",
            titleY=-10,
            titleX=-8,
            titleFontWeight="bold",
        )
        if gutter
        else alt.Axis(title=None)
    )
    color = alt.Color("category:N", scale=_colors(dark), legend=None)
    tooltip = [
        alt.Tooltip("estimate:Q", title=y_label or "Effect", format="+.3g"),
        alt.Tooltip("ci_low:Q", title="95% low", format="+.3g"),
        alt.Tooltip("ci_high:Q", title="95% high", format="+.3g"),
        alt.Tooltip("p:Q", title="p", format=".3f"),
        alt.Tooltip("category:N", title="Result"),
        alt.Tooltip("fair:N", title="Comparison"),
        alt.Tooltip("choices:N", title="Choices"),
    ]
    base = alt.Chart(df)
    pick = alt.selection_point(name=SELECTION, fields=["spec_id"], on="click", empty=False)
    size = 46 if n <= 300 else 26
    y = alt.Y("estimate:Q", axis=yaxis)

    zero = (
        alt.Chart(pd.DataFrame({"y": [0.0]}))
        .mark_rule(color=pal.axis, strokeWidth=1)
        .encode(y=alt.Y("y:Q", axis=yaxis))
    )
    ci = base.mark_rule(strokeWidth=1, opacity=0.45).encode(
        x=x, y=alt.Y("ci_low:Q", axis=yaxis), y2="ci_high:Q", color=color
    )
    enc = {"x": x, "y": y, "color": color, "tooltip": tooltip}
    layers = [zero, ci]
    if (df["fair"] == "Left out").any():
        layers.append(
            base.transform_filter(alt.datum.fair == "Left out")
            .mark_point(size=size, filled=False, strokeWidth=1.4, opacity=1)
            .encode(**enc)
        )
    fair_dots = (
        base.transform_filter(alt.datum.fair == "Fair")
        .mark_circle(size=size, opacity=1)
        .encode(**enc)
    )
    if interactive:
        fair_dots = fair_dots.add_params(pick)
    layers.append(fair_dots)
    if interactive:
        layers.append(
            base.mark_point(size=size * 4, filled=False, strokeWidth=2, color=pal.text_primary)
            .encode(x=x, y=y)
            .transform_filter(pick)
        )
    if reported_estimate is not None:
        layers.append(
            alt.Chart(pd.DataFrame({"y": [reported_estimate]}))
            .mark_rule(color=pal.reported_line, strokeDash=[5, 4], strokeWidth=1.5)
            .encode(y=alt.Y("y:Q", axis=yaxis))
        )
    return _config(alt.layer(*layers).properties(height=height), dark)


PREFIX = {
    "outliers": "Extremes",
    "controls": "Kept equal",
    "transform": "Measured as",
    "missing": "Missing",
}


SHORTER = {
    "Fill numbers with the average": "fill with average",
    "Leave those rows out": "drop those rows",
    "Drop beyond ": "drop beyond ",
    "Keep all": "keep all",
}


def row_label(d: Decision, option: str) -> str:
    """Short, unambiguous row name for the choices panel, e.g. "Kept equal: study_hours"."""
    if d.kind.value == "subset":
        col = next((o.params.get("column") for o in d.options if o.params.get("column")), None)
        prefix = f"Group {col}" if col else "Who"
        option = option.replace("Only ", "").replace(f"{col} = ", "= ") if col else option
    elif d.kind.value == "controls":
        # control sets grow one variable at a time, so name the newest one
        cols = next((o.params.get("columns", []) for o in d.options if o.label == option), [])
        if len(cols) > 2:
            return f"Kept equal: {len(cols)} (+ {short(cols[-1], 14)})"
        prefix = "Kept equal"
    else:
        prefix = PREFIX.get(d.kind.value, short(d.label, 14))
    for long, brief in SHORTER.items():
        option = option.replace(long, brief)
    return f"{prefix}: {short(option, 26)}"


def choices_chart(
    results: Sequence[SpecResult],
    decisions: Sequence[Decision],
    *,
    alpha: float = 0.05,
    show_invalid: bool = True,
    dark: bool = False,
    gutter: int = AXIS_GUTTER,
) -> alt.TopLevelMixin | None:
    """The panel under the curve: one row per option, a mark where it was used."""
    df = curve_frame(results, decisions, alpha, show_invalid)
    multi = [d for d in decisions if len(d.options) > 1]
    if df.empty or not multi:
        return None
    order = [row_label(d, o.label) for d in multi for o in d.options]
    lookup = {r.spec_id: r for r in results}
    rows = []
    for rec in df.itertuples():
        r = lookup[rec.spec_id]
        for d in multi:
            if d.id in r.choices:
                o = d.option(r.choices[d.id])
                rows.append(
                    {
                        "rank": rec.rank,
                        "row": row_label(d, o.label),
                        "category": rec.category,
                        "fair": rec.fair,
                    }
                )
    panel = (
        alt.Chart(pd.DataFrame(rows))
        .mark_tick(size=11)
        .encode(
            x=_x(len(df)),
            y=alt.Y(
                "row:N",
                sort=order,
                title=None,
                axis=alt.Axis(
                    labelLimit=gutter - 12, minExtent=gutter, maxExtent=gutter, grid=False
                ),
            ),
            color=alt.Color("category:N", scale=_colors(dark), legend=None),
            opacity=alt.condition(alt.datum.fair == "Fair", alt.value(1.0), alt.value(0.45)),
            # second encoding besides opacity: left-out analyses are drawn as thin ticks
            strokeWidth=alt.condition(alt.datum.fair == "Fair", alt.value(2.2), alt.value(0.9)),
        )
        .properties(height=17 * len(order))
    )
    return _config(panel, dark)


def to_spec(chart: alt.TopLevelMixin) -> dict:
    """Vega-Lite spec without Altair's (slow) schema validation."""
    return chart.to_dict(validate=False)


def live_curve_chart(
    results: Sequence[SpecResult], *, alpha: float, dark: bool
) -> alt.TopLevelMixin:
    """Small, non-interactive curve drawn while the run is in progress."""
    return spec_curve_chart(
        results, [], alpha=alpha, dark=dark, interactive=False, height=170, y_label="", gutter=None
    )

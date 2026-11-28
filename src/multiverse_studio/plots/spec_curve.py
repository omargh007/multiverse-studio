"""Specification curve figure (two panels). Pure Matplotlib, so it can be tested.

Top panel: estimates sorted ascending with 95% CI whiskers. Colour encodes
significant-same-direction / significant-opposite / not significant (from
``plots.palette``). Left-out universes (guardrails) are hollow markers, a second
encoding besides colour. An optional dashed line marks a reported estimate
(cherry-pick check).

Bottom panel: one row per decision option, with a mark where that option was
used. It is coloured like the dot above it, so you can see which choices
produce which results.

The figure stores the left-to-right spec order in ``fig.ms_spec_order`` so the
GUI can map a click to a universe.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from matplotlib.figure import Figure

from ..core.types import Decision, DecisionKind, Option, SpecResult
from .palette import (
    CI_LINE_WIDTH,
    FONT_FAMILY,
    GRID_LINE_WIDTH,
    MARKER_SIZE_PT,
    palette,
)


def categorize(results: Sequence[SpecResult], alpha: float) -> tuple[list[str], float]:
    """Category per result ("same" / "opp" / "ns") and the dominant direction."""
    valid = [r.estimate for r in results if r.ok and r.valid]
    base = valid or [r.estimate for r in results if r.ok] or [0.0]
    direction = 1.0 if float(np.median(base)) >= 0 else -1.0
    cats = []
    for r in results:
        if not r.ok or r.p_value is None or r.p_value >= alpha:
            cats.append("ns")
        elif np.sign(r.estimate) == direction:
            cats.append("same")
        else:
            cats.append("opp")
    return cats, direction


MAX_LABEL = 30


def short(label: str, limit: int = MAX_LABEL) -> str:
    """Trim long option labels so they never get clipped at the left edge."""
    return label if len(label) <= limit else label[: limit - 1].rstrip(" +,") + "…"


def _option_label(d: Decision, option: Option) -> str:
    """Control sets grow one variable at a time, so long ones name the newest one."""
    cols = option.params.get("columns", [])
    if d.kind is DecisionKind.CONTROLS and len(cols) > 1 and len(option.label) > MAX_LABEL:
        return f"{len(cols)} variables, adds {cols[-1]}"
    return option.label


def _style_axis(ax, pal) -> None:
    ax.set_facecolor(pal.surface)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(pal.axis)
    ax.tick_params(colors=pal.text_secondary, labelsize=9, length=0)


def spec_curve_figure(
    results: Sequence[SpecResult],
    decisions: Sequence[Decision],
    *,
    alpha: float = 0.05,
    show_invalid: bool = True,
    reported_estimate: float | None = None,
    dark: bool = False,
    indicators: bool = True,
    y_label: str = "Effect",
    figsize: tuple[float, float] = (9.0, 5.6),
) -> Figure:
    pal = palette(dark)
    fig = Figure(figsize=figsize, dpi=100, facecolor=pal.surface)
    fig.ms_spec_order = []  # type: ignore[attr-defined]

    shown = [r for r in results if r.ok and (show_invalid or r.valid)]
    shown.sort(key=lambda r: r.estimate)
    cats, _ = categorize(shown, alpha)
    colors = {"same": pal.sig_same, "opp": pal.sig_opposite, "ns": pal.not_significant}

    rows: list[tuple[str, str | None, str]] = []  # (label, option_id, decision_id)
    if indicators:
        for d in decisions:
            if len(d.options) < 2:
                continue
            rows.append((d.label, None, d.id))
            rows += [(_option_label(d, o), o.id, d.id) for o in d.options]

    if indicators and rows:
        gs = fig.add_gridspec(
            2,
            1,
            height_ratios=[2.2, max(0.9, 0.16 * len(rows))],
            hspace=0.06,
            left=0.24,
            right=0.98,
            top=0.96,
            bottom=0.04,
        )
        ax = fig.add_subplot(gs[0])
        ax_ind = fig.add_subplot(gs[1], sharex=ax)
    else:
        fig.subplots_adjust(left=0.1 if not indicators else 0.24, right=0.98, top=0.94, bottom=0.12)
        ax = fig.add_subplot(111)
        ax_ind = None
    _style_axis(ax, pal)

    if not shown:
        ax.text(
            0.5,
            0.5,
            "No results yet",
            transform=ax.transAxes,
            ha="center",
            va="center",
            color=pal.text_secondary,
            fontsize=11,
            family=FONT_FAMILY,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        if ax_ind is not None:
            ax_ind.set_visible(False)
        return fig

    x = np.arange(len(shown))
    est = np.array([r.estimate for r in shown])
    lo = np.array([r.ci_low if r.ci_low is not None else r.estimate for r in shown])
    hi = np.array([r.ci_high if r.ci_high is not None else r.estimate for r in shown])
    col = [colors[c] for c in cats]
    valid = np.array([r.valid for r in shown])

    ax.grid(axis="y", color=pal.grid, linewidth=GRID_LINE_WIDTH)
    ax.set_axisbelow(True)
    ax.axhline(0, color=pal.axis, linewidth=1.2, zorder=1)
    ax.vlines(x, lo, hi, colors=col, linewidth=CI_LINE_WIDTH, alpha=0.45, zorder=2)
    if valid.any():
        ax.scatter(
            x[valid],
            est[valid],
            s=MARKER_SIZE_PT**2,
            c=[c for c, v in zip(col, valid, strict=False) if v],
            edgecolors=pal.surface,
            linewidths=1.0,
            zorder=3,
        )
    if (~valid).any():
        ax.scatter(
            x[~valid],
            est[~valid],
            s=MARKER_SIZE_PT**2,
            facecolors=pal.surface,
            edgecolors=[c for c, v in zip(col, valid, strict=False) if not v],
            linewidths=1.4,
            zorder=3,
        )
    if reported_estimate is not None:
        ax.axhline(
            reported_estimate,
            color=pal.reported_line,
            linestyle=(0, (5, 4)),
            linewidth=1.1,
            zorder=4,
        )
        ax.text(
            0.005,
            reported_estimate,
            f"  Reported: {reported_estimate:+.3g}",
            transform=ax.get_yaxis_transform(),
            va="bottom",
            ha="left",
            fontsize=9,
            color=pal.text_primary,
            family=FONT_FAMILY,
            fontweight="bold",
        )
    ax.set_ylabel(y_label, color=pal.text_secondary, fontsize=9, family=FONT_FAMILY)
    ax.set_xlim(-0.8, len(shown) - 0.2)
    plt_hide = ax_ind is not None
    ax.tick_params(axis="x", labelbottom=not plt_hide)
    if not plt_hide:
        ax.set_xlabel("Analyses, sorted by effect", color=pal.text_secondary, fontsize=9)

    if ax_ind is not None:
        _style_axis(ax_ind, pal)
        ax_ind.spines["bottom"].set_visible(False)
        n = len(rows)
        ylabels, yticks = [], []
        for i, (label, opt_id, dec_id) in enumerate(rows):
            yy = n - 1 - i
            yticks.append(yy)
            ylabels.append(short(label) if opt_id is not None else short(label.upper()))
            if opt_id is None:
                continue
            ax_ind.axhline(yy, color=pal.grid, linewidth=0.5, zorder=1)
            used = np.array([r.choices.get(dec_id) == opt_id for r in shown])
            if used.any():
                ax_ind.scatter(
                    x[used],
                    np.full(used.sum(), yy),
                    marker="|",
                    s=55,
                    linewidths=2.2,
                    c=[c for c, u in zip(col, used, strict=False) if u],
                    alpha=[1.0 if v else 0.45 for v, u in zip(valid, used, strict=False) if u],
                    zorder=2,
                )
        ax_ind.set_yticks(yticks)
        ax_ind.set_yticklabels(ylabels, fontsize=8.5, family=FONT_FAMILY)
        for tick, (_, opt_id, _) in zip(ax_ind.get_yticklabels(), rows, strict=False):
            if opt_id is None:
                tick.set_fontweight("bold")
                tick.set_color(pal.text_primary)
        ax_ind.set_ylim(-0.7, n - 0.3)
        ax_ind.set_xticks([])
    fig.ms_spec_order = [r.spec_id for r in shown]  # type: ignore[attr-defined]
    return fig

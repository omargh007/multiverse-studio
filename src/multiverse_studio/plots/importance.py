"""Horizontal bar chart: which decision moves the estimate most."""

from __future__ import annotations

from collections.abc import Mapping

from matplotlib.figure import Figure

from .palette import FONT_FAMILY, palette


def importance_figure(
    importance: Mapping[str, float],
    labels: Mapping[str, str],
    *,
    dark: bool = False,
    figsize: tuple[float, float] = (5.0, 2.6),
) -> Figure:
    """Single series, so no legend: the title names it. Values are labelled directly."""
    pal = palette(dark)
    fig = Figure(figsize=figsize, dpi=100, facecolor=pal.surface)
    ax = fig.add_subplot(111)
    ax.set_facecolor(pal.surface)
    items = list(importance.items())[::-1]  # largest at top
    if not items:
        ax.text(
            0.5,
            0.5,
            "No choices to compare",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color=pal.text_secondary,
        )
        ax.axis("off")
        return fig
    names = [labels.get(k, k) for k, _ in items]
    vals = [v * 100 for _, v in items]
    y = range(len(items))
    ax.barh(y, [100] * len(vals), color=pal.grid, height=0.55, zorder=1)
    ax.barh(y, vals, color=pal.bar, height=0.55, zorder=2)
    for yy, v in zip(y, vals, strict=False):
        ax.text(
            101,
            yy,
            f"{v:.0f}%",
            va="center",
            ha="left",
            fontsize=9,
            color=pal.text_primary,
            family=FONT_FAMILY,
            fontweight="bold",
        )
    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=9, family=FONT_FAMILY, color=pal.text_secondary)
    ax.set_xlim(0, 114)
    ax.set_xticks([])
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    longest = max(len(n) for n in names)
    fig.subplots_adjust(left=min(0.55, 0.05 + 0.017 * longest), right=0.98, top=0.96, bottom=0.04)
    return fig

"""Chart colours. Validated with the dataviz six-check validator (2026-11-23).

Results:
  * light, surface #ffffff: blue/orange, all pairs: CVD dE 24.7, normal-vision dE 33.6,
    contrast >= 3:1. PASS.
  * dark, surface #1e293b: CVD dE 26.8, normal-vision dE 31.8, contrast >= 3:1. PASS.
  * The "not significant" grey is a deliberate neutral, not a series hue. Its contrast
    is 3.47:1 in light mode and 3.99:1 in dark mode.

Identity is never carried by colour alone:
  * significance is also given in the legend and tooltip text;
  * invalid universes (guardrails) use a hollow marker as a second encoding.

Lives in ``plots`` (not ``gui``) so the PDF exporter can use it without Tk.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChartPalette:
    surface: str
    text_primary: str
    text_secondary: str
    grid: str
    axis: str
    sig_same: str
    """Significant, in the median's direction (categorical slot 1, blue)."""
    sig_opposite: str
    """Significant, opposite direction (categorical slot 2, orange)."""
    not_significant: str
    """Neutral grey."""
    reported_line: str
    """Cherry-pick check: the reported estimate (dashed line in ink colour)."""
    bar: str
    """Single-series bars (decision importance)."""


LIGHT = ChartPalette(
    surface="#ffffff",
    text_primary="#0f172a",
    text_secondary="#475569",
    grid="#e2e8f0",
    axis="#cbd5e1",
    sig_same="#2a78d6",
    sig_opposite="#eb6834",
    not_significant="#8a8a84",
    reported_line="#0f172a",
    bar="#2a78d6",
)

DARK = ChartPalette(
    surface="#1e293b",
    text_primary="#f1f5f9",
    text_secondary="#cbd5e1",
    grid="#334155",
    axis="#475569",
    sig_same="#3987e5",
    sig_opposite="#d95926",
    not_significant="#7d8696",
    reported_line="#f1f5f9",
    bar="#3987e5",
)


def palette(dark: bool = False) -> ChartPalette:
    return DARK if dark else LIGHT


# Mark specs (dataviz: thin marks, markers >= 8 px, 2 px lines, recessive grid).
MARKER_SIZE_PT = 6.0  # ~8 px at 100 dpi
LINE_WIDTH = 1.5  # ~2 px
CI_LINE_WIDTH = 1.0
GRID_LINE_WIDTH = 0.6

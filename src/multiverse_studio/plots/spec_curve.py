"""Specification curve figure (two panels). Owner: B (GUI) - pure Matplotlib, testable.

Top panel: estimates sorted ascending with CI whiskers; colour by
significant-same-direction / significant-opposite / not significant
(colours from ``multiverse_studio.plots.palette``). Invalid universes
(guardrails) drawn hollow or hidden depending on ``show_invalid``.
Optional horizontal line at a reported estimate (cherry-pick check).
Bottom panel: one row per decision option, a tick where that option was used.
"""

from __future__ import annotations

from collections.abc import Sequence

from matplotlib.figure import Figure

from ..core.types import Decision, SpecResult


def spec_curve_figure(
    results: Sequence[SpecResult],
    decisions: Sequence[Decision],
    *,
    alpha: float = 0.05,
    show_invalid: bool = True,
    reported_estimate: float | None = None,
    dark: bool = False,
) -> Figure:
    raise NotImplementedError  # TODO(B)

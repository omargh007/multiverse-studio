"""Horizontal bar chart: which decision moves the estimate most. Owner: B."""

from __future__ import annotations

from collections.abc import Mapping

from matplotlib.figure import Figure


def importance_figure(
    importance: Mapping[str, float], labels: Mapping[str, str], *, dark: bool = False
) -> Figure:
    raise NotImplementedError  # TODO(B)

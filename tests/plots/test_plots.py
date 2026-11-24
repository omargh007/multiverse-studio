from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import pytest  # noqa: E402

from multiverse_studio.core import api  # noqa: E402
from multiverse_studio.core.types import GuardrailAnswers  # noqa: E402
from multiverse_studio.plots.importance import importance_figure  # noqa: E402
from multiverse_studio.plots.spec_curve import categorize, spec_curve_figure  # noqa: E402
from tests.conftest import make_result  # noqa: E402


@pytest.mark.parametrize("dark", [False, True])
def test_spec_curve_renders_with_invalid_and_reported(real_run, dark):
    _, decisions, _, results = real_run
    results = api.mark_validity(
        results, decisions, api.assess_controls({"tiredness": GuardrailAnswers(False, True, False)})
    )
    fig = spec_curve_figure(results, decisions, reported_estimate=5.0, dark=dark)
    fig.canvas.draw()
    assert len(fig.axes) == 2
    assert len(fig.ms_spec_order) == len(results)
    hidden = spec_curve_figure(results, decisions, show_invalid=False)
    assert len(hidden.ms_spec_order) == sum(r.valid for r in results)


def test_spec_curve_without_indicators_and_empty():
    fig = spec_curve_figure([make_result(0, 1.0, 0.01)], [], indicators=False)
    fig.canvas.draw()
    assert len(fig.axes) == 1
    empty = spec_curve_figure([], [])
    empty.canvas.draw()
    assert empty.ms_spec_order == []


def test_categorize():
    rs = [make_result(0, 1, 0.01), make_result(1, -1, 0.01), make_result(2, 1, 0.5)]
    cats, direction = categorize(rs, 0.05)
    assert cats == ["same", "opp", "ns"] and direction == 1.0


def test_importance_figure():
    fig = importance_figure({"controls": 0.6, "outliers": 0.1}, {"controls": "Controls"})
    fig.canvas.draw()
    empty = importance_figure({}, {})
    empty.canvas.draw()

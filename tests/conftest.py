"""Shared fixtures."""

from __future__ import annotations

import pytest

from multiverse_studio.core.types import Decision, DecisionKind, Option


@pytest.fixture
def three_decisions() -> list[Decision]:
    """2 x 3 x 2 = 12 universes."""
    return [
        Decision(
            id="outliers",
            kind=DecisionKind.OUTLIERS,
            label="Outliers",
            options=(Option("none", "Keep all"), Option("sd3", "Drop beyond 3 SD")),
        ),
        Decision(
            id="controls",
            kind=DecisionKind.CONTROLS,
            label="Controls",
            options=(
                Option("none", "None", {"columns": []}),
                Option("study", "Study hours", {"columns": ["study_hours"]}),
                Option("study_job", "Study + job", {"columns": ["study_hours", "has_job"]}),
            ),
        ),
        Decision(
            id="subset",
            kind=DecisionKind.SUBSET,
            label="Who",
            options=(Option("all", "Everyone"), Option("y1", "First-years only")),
        ),
    ]


@pytest.fixture(scope="session")
def real_df():
    from multiverse_studio.core.simulate import simulate

    return simulate("real_effect", n=300, seed=1)


@pytest.fixture(scope="session")
def real_run(real_df):
    """(df, decisions, specs, results) for the real-effect scenario."""
    from multiverse_studio.core import api

    profile = api.profile_data(real_df)
    decisions = api.suggest_decisions(profile, "grade", "sleep_hours", real_df)
    specs = api.build_specs(decisions, seed=1)
    results = api.run_multiverse(real_df, "grade", "sleep_hours", "linear", decisions, specs)
    return real_df, decisions, specs, results


def make_result(spec_id, est, p, choices=None, valid=True, error=None):
    from multiverse_studio.core.types import SpecResult

    if error:
        return SpecResult(spec_id, choices or {}, None, None, None, None, None, 0, error=error)
    return SpecResult(spec_id, choices or {}, est, 0.1, p, est - 0.2, est + 0.2, 100, valid=valid)

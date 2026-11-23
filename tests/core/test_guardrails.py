from __future__ import annotations

import pytest

from multiverse_studio.core import api
from multiverse_studio.core.guardrails import assess_control
from multiverse_studio.core.types import CausalRole
from multiverse_studio.core.types import GuardrailAnswers as G

T, F, N = True, False, None


@pytest.mark.parametrize(
    "before,by_x,by_y,role,keep",
    [
        (N, T, T, CausalRole.COLLIDER, False),
        (N, T, F, CausalRole.MEDIATOR, False),
        (N, T, N, CausalRole.MEDIATOR, False),
        (N, F, T, CausalRole.OUTCOME_PROXY, False),
        (N, N, T, CausalRole.OUTCOME_PROXY, False),
        (T, F, F, CausalRole.CONFOUNDER, True),
        (F, F, F, CausalRole.NEUTRAL, True),
        (N, F, F, CausalRole.NEUTRAL, True),
        (T, N, F, CausalRole.UNKNOWN, True),
        (N, N, N, CausalRole.UNKNOWN, True),
    ],
)
def test_rule_table(before, by_x, by_y, role, keep):
    a = assess_control("v", G(before, by_x, by_y))
    assert (a.role, a.keep) == (role, keep)
    assert "v" in a.reason


def test_mediated_scenario_guardrails_recover_total_effect():
    df = api.simulate("mediated", n=400, seed=4)
    decisions = api.suggest_decisions(api.profile_data(df), "grade", "sleep_hours", df)
    assert "tiredness" in api.variables_to_assess(decisions)
    specs = api.build_specs(decisions)
    results = api.run_multiverse(df, "grade", "sleep_hours", "linear", decisions, specs)
    guarded = api.mark_validity(
        results, decisions, api.assess_controls({"tiredness": G(False, True, False)})
    )
    before, after = api.summarize(results), api.summarize(guarded)
    assert after.n_valid < before.n_valid
    truth = df.attrs["true_effect"]
    assert abs(after.median_estimate - truth) < abs(before.median_estimate - truth)


def test_collider_subset_is_also_invalid():
    df = api.simulate("collider", n=300, seed=1)
    decisions = api.suggest_decisions(api.profile_data(df), "grade", "sleep_hours", df)
    specs = api.build_specs(decisions)
    results = api.run_multiverse(df, "grade", "sleep_hours", "linear", decisions, specs)
    guarded = api.mark_validity(
        results, decisions, api.assess_controls({"scholarship": G(False, True, True)})
    )
    for r in guarded:
        uses = "scholarship" in api.conditioned_on(r, decisions)
        assert r.valid is (not uses)
    assert api.summarize(guarded).label == "fragile"  # true effect is zero

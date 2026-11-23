from __future__ import annotations

import pytest

from multiverse_studio.core.specs import build_specs, count_specs, iter_all_choices
from multiverse_studio.core.types import Decision, DecisionKind


def test_count_specs(three_decisions):
    assert count_specs(three_decisions) == 12
    assert count_specs([]) == 1


def test_full_grid_is_every_combination_once(three_decisions):
    specs = build_specs(three_decisions)
    assert [s.id for s in specs] == list(range(12))
    got = sorted(tuple(sorted(s.choices.items())) for s in specs)
    want = sorted(tuple(sorted(c.items())) for c in iter_all_choices(three_decisions))
    assert got == want


def test_choice_order_follows_decision_order(three_decisions):
    spec = build_specs(three_decisions)[0]
    assert list(spec.choices) == ["outliers", "controls", "subset"]


def test_no_decisions_gives_one_baseline_universe():
    specs = build_specs([])
    assert len(specs) == 1 and specs[0].choices == {}


def test_sampling_is_seeded_and_sized(three_decisions):
    a = build_specs(three_decisions, max_specs=5, seed=7)
    b = build_specs(three_decisions, max_specs=5, seed=7)
    c = build_specs(three_decisions, max_specs=5, seed=8)
    assert len(a) == 5
    assert [s.choices for s in a] == [s.choices for s in b]
    assert [s.choices for s in a] != [s.choices for s in c]


def test_over_limit_without_sampling_raises(three_decisions):
    with pytest.raises(ValueError, match="more than the limit"):
        build_specs(three_decisions, max_specs=5, sample_if_over=False)


def test_under_limit_is_not_sampled(three_decisions):
    assert len(build_specs(three_decisions, max_specs=100)) == 12


def test_duplicate_ids_rejected(three_decisions):
    with pytest.raises(ValueError, match="unique"):
        build_specs([three_decisions[0], three_decisions[0]])


def test_empty_options_rejected():
    bad = Decision(id="x", kind=DecisionKind.OUTLIERS, label="x", options=())
    with pytest.raises(ValueError, match="no options"):
        build_specs([bad])

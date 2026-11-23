from __future__ import annotations

import json

import pytest

from multiverse_studio.core import api
from multiverse_studio.core.types import GuardrailAnswers, Session


@pytest.mark.parametrize("scenario", list(api.SCENARIOS))
def test_simulator_is_seeded_and_documented(scenario):
    a = api.simulate(scenario, n=100, seed=9)
    b = api.simulate(scenario, n=100, seed=9)
    assert a.equals(b)
    assert a.attrs["scenario"] == scenario and "true_effect" in a.attrs
    assert a["sleep_hours"].isna().sum() >= 1
    assert ("scholarship" in a.columns) is (scenario == "collider")


def test_simulator_validation():
    with pytest.raises(ValueError):
        api.simulate("nope", n=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        api.simulate("no_effect", n=10)


def _full_session(real_run, tmp_path):
    df, decisions, specs, results = real_run
    f = tmp_path / "d.csv"
    df.to_csv(f, index=False)
    s = Session(
        data_path=str(f),
        y="grade",
        x="sleep_hours",
        family="linear",
        decisions=list(decisions),
        specs=list(specs),
        n_permutations=0,
        guardrails={"tiredness": GuardrailAnswers(False, True, False)},
    )
    s.profile = api.profile_data(df)
    s.assessments = api.assess_controls(s.guardrails)
    s.results = api.mark_validity(results, decisions, s.assessments)
    s.verdict = api.summarize(s.results)
    s.cherry_pick = api.cherry_pick_check(s.results, 9.0)
    s.blind = api.lock_plan(s)
    return s


def test_narrative(real_run, tmp_path):
    s = _full_session(real_run, tmp_path)
    m = api.methods_paragraph(s)
    r = api.results_paragraph(s)
    assert (
        "sleep_hours" in m and "Simonsohn" in m and "tiredness (mediator)" in m and "SHA-256" in m
    )
    assert "median estimate" in r and "extreme tail" in r
    with pytest.raises(ValueError):
        api.results_paragraph(Session(y="a", x="b"))
    with pytest.raises(ValueError):
        api.methods_paragraph(Session())


def test_session_roundtrip_through_json(real_run, tmp_path):
    s = _full_session(real_run, tmp_path)
    text = json.dumps(api.session_to_dict(s))
    back = api.session_from_dict(json.loads(text))
    assert back.decisions == s.decisions
    assert back.results == s.results
    assert back.verdict == s.verdict
    assert back.blind == s.blind and api.verify_plan(back, back.blind)
    assert back.assessments == s.assessments and back.profile == s.profile
    with pytest.raises(ValueError):
        api.session_from_dict({"format": "other"})

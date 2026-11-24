from __future__ import annotations

import json

import pytest

from multiverse_studio.core import api
from multiverse_studio.core.types import Session
from multiverse_studio.io.export_json import environment_info, export_json
from multiverse_studio.io.session_store import load_session, save_session


def _session(tmp_path):
    df = api.simulate("real_effect", n=120, seed=3)
    data = tmp_path / "d.csv"
    df.to_csv(data, index=False)
    decisions = api.suggest_decisions(api.profile_data(df), "grade", "sleep_hours", df)[:2]
    s = Session(
        data_path=str(data),
        y="grade",
        x="sleep_hours",
        family="linear",
        decisions=decisions,
        n_permutations=0,
    )
    s.blind = api.lock_plan(s)
    s.specs = api.build_specs(decisions)
    s.results = api.run_multiverse(df, "grade", "sleep_hours", "linear", decisions, s.specs)
    s.verdict = api.summarize(s.results)
    return s


def test_save_and_load_roundtrip(tmp_path):
    s = _session(tmp_path)
    path = save_session(s, tmp_path / "analysis")
    assert path.suffix == ".msession"
    back = load_session(path)
    assert back.results == s.results and back.verdict == s.verdict


def test_load_errors(tmp_path):
    bad = tmp_path / "bad.msession"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Could not open"):
        load_session(bad)


def test_json_report(tmp_path):
    s = _session(tmp_path)
    path = export_json(s, tmp_path / "report.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["plan_verified"] is True
    assert data["environment"]["packages"]["statsmodels"]
    assert "median estimate" in data["results_text"]
    assert set(data["decision_importance"]) == {d.id for d in s.decisions}


def test_environment_info():
    info = environment_info()
    assert info["python"] and "numpy" in info["packages"]

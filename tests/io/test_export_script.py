from __future__ import annotations

import subprocess
import sys

import pytest

from multiverse_studio.core import api
from multiverse_studio.core.types import GuardrailAnswers, Session
from multiverse_studio.io.export_script import export_script, render_script


def test_exported_script_runs_and_reproduces_verdict(tmp_path):
    df = api.simulate("real_effect", n=200, seed=2)
    data = tmp_path / "students.csv"
    df.to_csv(data, index=False)
    decisions = api.suggest_decisions(api.profile_data(df), "grade", "sleep_hours", df)[:2]
    s = Session(
        data_path=str(data),
        y="grade",
        x="sleep_hours",
        family="linear",
        decisions=decisions,
        n_permutations=0,
        guardrails={"study_hours": GuardrailAnswers(True, False, False)},
    )
    s.blind = api.lock_plan(s)
    script = export_script(s, tmp_path / "reproduce.py")
    compile(script.read_text(encoding="utf-8"), str(script), "exec")

    out = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    specs = api.build_specs(decisions, max_specs=s.max_specs, seed=s.seed)
    verdict = api.summarize(
        api.run_multiverse(df, "grade", "sleep_hours", "linear", decisions, specs)
    )
    assert f"Verdict: {verdict.label}" in out.stdout
    assert "sha256" in script.read_text(encoding="utf-8")


def test_render_requires_question():
    with pytest.raises(ValueError):
        render_script(Session())

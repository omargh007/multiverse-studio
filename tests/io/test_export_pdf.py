from __future__ import annotations

import pytest
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.text import Text

from multiverse_studio.core import api
from multiverse_studio.core.types import GuardrailAnswers, Session
from multiverse_studio.io.export_pdf import export_pdf, render_pdf


def _session(scenario="collider", rename=None, blind=True):
    df = api.simulate(scenario, n=200, seed=1).rename(columns=rename or {})
    y, x = ((rename or {}).get(c, c) for c in ("grade", "sleep_hours"))
    profile = api.profile_data(df)
    decisions = api.suggest_decisions(profile, y, x, df)
    s = Session(
        data_path="/home/someone/private/d.csv",
        profile=profile,
        y=y,
        x=x,
        family="linear",
        decisions=decisions,
        n_permutations=0,
    )
    if blind:
        s.blind = api.lock_plan(s)
    s.specs = api.build_specs(decisions)
    results = api.run_multiverse(df, y, x, "linear", decisions, s.specs)
    s.results = api.mark_validity(results, decisions, s.assessments)
    s.verdict = api.summarize(s.results)
    return s


@pytest.fixture
def pages(monkeypatch):
    """The text on every PDF page, in order (each line also checked to sit on the page)."""
    seen: list[str] = []
    original = PdfPages.savefig

    def spy(self, figure=None, **kwargs):
        assert all(t.get_position()[1] > 0 for t in figure.texts)
        seen.append("\n".join(t.get_text() for t in figure.findobj(Text)))
        original(self, figure, **kwargs)

    monkeypatch.setattr(PdfPages, "savefig", spy)
    return seen


def _flat(pages):
    """All page text with the line wrapping removed."""
    return " ".join(" ".join(pages).split())


def test_full_report(tmp_path, pages):
    s = _session()
    s.guardrails = {"scholarship": GuardrailAnswers(False, True, True)}
    s.assessments = api.assess_controls(s.guardrails)
    s.results = api.mark_validity(s.results, s.decisions, s.assessments)
    s.verdict = api.summarize(s.results, permutation_p=0.01)
    s.n_permutations = 100
    s.blind = api.lock_plan(s)  # the lock covers the answers and run options set above
    s.cherry_pick = api.cherry_pick_check(s.results, 99.0)
    s.reported_estimate = 99.0

    path = export_pdf(s, tmp_path / "report.pdf")

    assert path.read_bytes().startswith(b"%PDF")
    assert len(pages) >= 4
    text = _flat(pages)
    for expected in (
        "Does sleep_hours affect grade?",
        "Typical effect (median)",
        "Unlikely (p = 0.01)",
        "Every analysis, sorted by effect size",
        "Reported result",
        "Which choice matters most?",
        "scholarship: Unfair: left out",
        "Could grade cause it: Yes",
        "may be cherry-picked",
        "Methods",
        s.blind.sha256,
        "The plan matches its fingerprint.",
    ):
        assert expected in text
    assert "private" not in text  # only the file name, never the folder


def test_empty_states_and_changed_plan(pages):
    s = _session(blind=False)
    s.notes = "Plan changed after results were seen.\n" * 150  # forces extra pages
    render_pdf(s)
    text = _flat(pages)
    assert "No locked plan" in text and "No reported result was entered." in text
    assert "Not checked" in text and "Not answered: kept" in text
    assert "The plan was changed after results were seen" in text
    assert len(pages) >= 6


def test_tampered_plan_is_reported(pages):
    s = _session()
    s.seed += 1
    render_pdf(s)
    assert "The plan no longer matches its fingerprint." in _flat(pages)


def test_dollar_signs_in_column_names():
    s = _session(rename={"grade": "pay $ (net $)", "sleep_hours": "cost $_{x$"})
    assert render_pdf(s).startswith(b"%PDF")


def test_needs_a_finished_run():
    with pytest.raises(ValueError, match="Run the analysis first"):
        render_pdf(Session())

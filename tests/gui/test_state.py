"""The workbench controller: the whole GUI workflow without a browser."""

from __future__ import annotations

import json

import pytest

from multiverse_studio.gui.state import RunProgress, Workbench


@pytest.fixture
def wb(tmp_path) -> Workbench:
    return Workbench(data_dir=tmp_path)


def plan_collider(wb: Workbench, answer: bool = True) -> None:
    """Collider example, question asked, choices kept, scholarship flagged."""
    wb.load_example("collider")
    wb.set_question("grade", "sleep_hours")
    assert wb.confirm_choices()
    if answer:
        wb.set_answer("scholarship", 0, "No")
        wb.set_answer("scholarship", 1, "Yes")
        wb.set_answer("scholarship", 2, "Yes")
    assert wb.confirm_fairness()
    wb.set_run_options(0, 0.05, 1)  # no luck check: keeps the test fast


def run_to_end(wb: Workbench) -> None:
    wb.start_run()
    assert wb.job is not None
    wb.job.wait(120)
    assert wb.poll()


def test_blocks_unlock_in_order(wb):
    assert [wb.block_state(b) for b in ("data", "question", "choices", "fairness")] == [
        "current",
        "locked",
        "locked",
        "locked",
    ]
    wb.load_example("real_effect")
    assert wb.block_state("data") == "done" and wb.block_state("question") == "current"
    assert wb.notice and wb.notice[0] == "info" and "truth" in wb.notice[2]
    assert "grade" in wb.outcome_columns() and "sleep_hours" in wb.factor_columns()
    wb.set_question("grade", "sleep_hours")
    assert wb.session.family == "linear" and wb.block_state("choices") == "current"
    assert wb.open_block == "choices" and wb.suggested
    wb.open("fairness")  # locked blocks can't be opened
    assert wb.open_block == "choices"
    assert wb.confirm_choices() and wb.block_state("fairness") == "current"
    assert wb.confirm_fairness() and wb.ready_to_run()
    assert wb.open_block is None


def test_bad_question_reports_error(wb):
    wb.load_example("real_effect")
    err = wb.set_question("grade", "grade")
    assert err and wb.session.family is None and wb.block_state("choices") == "locked"
    assert wb.set_question("grade", "grade") == err  # unchanged pair: same answer


def test_full_run_with_guardrails(wb):
    plan_collider(wb)
    assert wb.blind_mode and wb.session.blind is None
    fair, total = wb.fair_count()
    assert 0 < fair < total
    assert wb.estimate_seconds() > 0
    run_to_end(wb)
    s = wb.session
    assert s.blind is not None and wb.plan_matches() is True
    assert s.verdict is not None and s.verdict.n_valid == fair
    assert len(s.results) == total and wb.progress.stage == "finished"
    assert wb.job is None and not wb.running
    assert wb.progress.done == total and wb.progress.current
    # importance, detail, cherry-pick
    imp = wb.importance()
    assert imp and all(0 <= share <= 1 for _, share in imp)
    r = s.results[0]
    assert wb.result_by_id(r.spec_id) is r and wb.result_by_id(-1) is None
    compile(wb.single_code(r), "<analysis>", "exec")
    wb.check_cherry(99.0)
    assert s.cherry_pick is not None and s.cherry_pick.flagged
    wb.check_cherry(None)
    assert s.cherry_pick is None and s.reported_estimate is None


def test_exports_and_reopen(wb, tmp_path):
    plan_collider(wb)
    run_to_end(wb)
    script = wb.script_text()
    compile(script, "reproduce.py", "exec")
    assert "sha256" in script
    report = json.loads(wb.report_text())
    assert report["plan_verified"] is True and report["results_text"]
    assert report["session"]["verdict"]["label"] == wb.session.verdict.label
    saved = wb.session_text().encode("utf-8")
    other = Workbench(data_dir=tmp_path)
    assert other.load_session_file("plan.msession", saved)
    assert other.session.verdict is not None and other.ready_to_run()
    assert other.blind_mode and other.plan_matches() is True
    assert other.progress.stage == "finished"


def test_reopen_failures(wb):
    assert not wb.load_session_file("x.msession", b"not json")
    assert wb.notice[0] == "critical"
    missing = json.dumps({"format": "multiverse-studio-session", "data_path": "/nope.csv"})
    assert not wb.load_session_file("x.msession", missing.encode())


def test_upload(wb, tmp_path):
    assert not wb.load_upload("notes.pdf", b"%PDF")
    assert wb.notice[0] == "critical" and wb.df is None
    assert not wb.load_upload("empty.csv", b"")
    assert wb.notice[0] == "critical"
    assert wb.load_upload("../study.csv", b"a,b\n1,2\n3,4\n5,7\n")
    assert wb.data_name == "study.csv" and (tmp_path / "study.csv").exists()
    assert wb.df.shape == (3, 2) and wb.revision == 1


def test_changing_the_plan_after_results_is_recorded(wb):
    plan_collider(wb)
    run_to_end(wb)
    lock = wb.session.blind.sha256
    d = wb.suggested[0]
    wb.set_ticked(d.id, [d.options[0].id])
    s = wb.session
    assert s.blind is None and s.results == [] and s.verdict is None
    assert lock[:16] in s.notes and "was changed" in s.notes
    assert not wb.choices_confirmed and wb.block_state("choices") == "current"
    assert wb.n_total() < 270 and "×" in wb.formula()


def test_empty_choice_blocks_confirm(wb):
    wb.load_example("real_effect")
    wb.set_question("grade", "sleep_hours")
    d = wb.suggested[0]
    wb.set_ticked(d.id, [])
    assert wb.empty_choices() == [d.label] and not wb.confirm_choices()


def test_answers_and_limits(wb):
    plan_collider(wb, answer=False)
    assert wb.answer_word("scholarship", 0) is None and wb.assessment("scholarship") is None
    wb.set_answer("scholarship", 1, None)  # clearing an unanswered row does nothing
    assert "scholarship" not in wb.session.guardrails and wb.fairness_confirmed
    wb.set_answer("scholarship", 1, "Yes")
    assert wb.answer_word("scholarship", 1) == "Yes" and not wb.fairness_confirmed
    assert wb.assessment("scholarship").keep is False
    wb.set_limit(250)
    assert wb.session.max_specs == 250 and wb.fair_count()[1] == 250
    wb.set_blind(False)
    assert not wb.blind_mode


def test_cancel_and_errors(wb, monkeypatch):
    plan_collider(wb)
    wb.set_run_options(500, 0.05, 1)  # long luck check, so there is time to cancel
    wb.start_run()
    wb.cancel()
    assert wb.job is None and wb.session.verdict is None
    assert wb.notice and wb.notice[1].startswith("Cancelled")

    from multiverse_studio.gui import state as state_mod

    class Boom(state_mod.RunJob):
        def __init__(self, *a, **k):
            def task(emit, cancel, *args):
                raise RuntimeError("no luck")

            super().__init__(*a, task=task, **k)

    monkeypatch.setattr(state_mod, "RunJob", Boom)
    wb.start_run()
    wb.job.wait(10)
    assert wb.poll() and wb.notice == ("critical", "The analysis stopped.", "no luck")
    assert wb.progress == RunProgress()


def test_start_over_keeps_seed(wb):
    plan_collider(wb)
    wb.start_over()
    assert wb.df is None and wb.session.seed == 1 and wb.revision == 2

"""The workbench controller: every state change the interface can make.

The Streamlit script (``app.py``) only draws what this object holds and calls
its methods. Keeping the logic here, with no Streamlit import, means the whole
workflow is tested with plain pytest (``tests/gui/test_state.py``), and the GUI
still only reaches the analysis through ``core.api``.

One ``Workbench`` lives in each browser session (``st.session_state``).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

import pandas as pd

from ..core import api
from ..core.choices import PREDICTOR_KINDS
from ..core.serialize import session_from_dict, session_to_dict
from ..core.specs import count_specs
from ..core.types import (
    ColumnKind,
    ControlAssessment,
    Decision,
    GuardrailAnswers,
    Session,
    SpecResult,
)
from ..io.export_json import report_dict
from ..io.export_pdf import render_pdf
from ..io.export_script import render_script
from ..io.loaders import SUPPORTED, DataLoadError, load_table
from .jobs import RunJob

DEFAULT_PERMUTATIONS = 100  # keeps a typical run under a minute
DATA_DIR = Path.home() / "Multiverse Studio"
"""Uploaded files and generated examples are copied here, so the exported script
and the plan fingerprint can point at a real file on this computer."""

EXAMPLES: list[tuple[str, str, str]] = [
    ("real_effect", "Real effect", "Sleep truly raises grades by 3 points per hour."),
    ("no_effect", "No effect", "Sleep has no effect at all."),
    ("confounded", "Hidden common cause", "Study time drives both sleep and grades."),
    ("mediated", "Mediator trap", "Keeping tiredness equal hides the real effect."),
    ("collider", "Collider trap", "Looking only at scholarship students fakes an effect."),
]
OUTCOME_KINDS = (ColumnKind.NUMERIC, ColumnKind.BINARY, ColumnKind.COUNT)
MODEL_WORDS = {
    "linear": "is a number, so we'll use linear regression.",
    "logistic": "is a yes / no answer, so we'll use logistic regression.",
    "poisson": "is a count, so we'll use Poisson regression.",
}
MODEL_NAMES = {
    "linear": "Linear regression",
    "logistic": "Logistic regression",
    "poisson": "Poisson regression",
}
PERMUTATION_CHOICES = {"Skip": 0, "100 shuffles": 100, "200 shuffles": 200, "500 shuffles": 500}
ALPHAS = (0.05, 0.01, 0.10)
LIMITS = (250, 500, 1000, 2000)
SECONDS_PER_FIT = 0.005
ANSWER_WORDS = ("Yes", "No", "Not sure")
TO_BOOL = {"Yes": True, "No": False, "Not sure": None}
FROM_BOOL = {True: "Yes", False: "No", None: "Not sure"}

BlockId = Literal["data", "question", "choices", "fairness"]
BLOCK_ORDER: tuple[BlockId, ...] = ("data", "question", "choices", "fairness")
Notice = tuple[str, str, str]  # (kind, lead, text)


@dataclass
class RunProgress:
    """What the evidence pane shows while a run is going."""

    total: int = 0
    done: int = 0
    stage: str = "idle"  # idle | lock | run | perm | verdict | finished
    perm_done: int = 0
    perm_total: int = 0
    current: str = ""
    started: float = 0.0
    elapsed: float = 0.0
    live: list[SpecResult] = field(default_factory=list)
    live_spec: dict | None = None
    """Cached chart of the live results; rebuilt only when enough new results arrive."""
    live_spec_n: int = 0


@dataclass
class Workbench:
    df: pd.DataFrame | None = None
    data_name: str = ""
    example: str | None = None
    session: Session = field(default_factory=lambda: Session(n_permutations=DEFAULT_PERMUTATIONS))
    suggested: list[Decision] = field(default_factory=list)
    ticked: dict[str, dict[str, bool]] = field(default_factory=dict)
    blind_mode: bool = True
    choices_confirmed: bool = False
    fairness_confirmed: bool = False
    open_block: BlockId | None = "data"
    revision: int = 0
    run_id: int = 0
    """Bumped on every run, so result widgets (cherry-pick input) start fresh."""
    """Bumped when new data loads, so every plan widget starts fresh."""
    notice: Notice | None = None
    job: RunJob | None = None
    progress: RunProgress = field(default_factory=RunProgress)
    data_dir: Path = DATA_DIR

    # ================================================================ data
    def set_data(self, df: pd.DataFrame, name: str, path: str | None) -> None:
        self.cancel()
        self.df, self.data_name = df, name
        self.session = Session(
            data_path=path,
            profile=api.profile_data(df),
            seed=self.session.seed,
            n_permutations=DEFAULT_PERMUTATIONS,
        )
        self.suggested, self.ticked = [], {}
        self.choices_confirmed = self.fairness_confirmed = False
        self.progress = RunProgress()
        self.open_block = "question"
        self.revision += 1

    def load_example(self, scenario: str) -> None:
        df = api.simulate(scenario, n=300, seed=self.session.seed)  # type: ignore[arg-type]
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / f"example_{scenario}.csv"
        df.to_csv(path, index=False)
        self.set_data(df, path.name, str(path))
        self.example = scenario
        truth = df.attrs.get("description", "")
        self.notice = (
            "info",
            f"Loaded {path.name}: {len(df):,} rows, {df.shape[1]} columns.",
            f"The truth in this example: {truth}",
        )

    def load_upload(self, name: str, data: bytes) -> bool:
        """Load an uploaded file. Returns False (and sets a notice) when it fails."""
        safe = Path(name).name
        if Path(safe).suffix.lower() not in SUPPORTED:
            self.notice = (
                "critical",
                "That file could not be loaded.",
                f"'{safe}' is not a supported file. Please use CSV or Excel (.xlsx).",
            )
            return False
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / safe
        path.write_bytes(data)
        try:
            df = load_table(path)
        except DataLoadError as exc:
            self.notice = ("critical", "That file could not be loaded.", str(exc))
            return False
        self.set_data(df, safe, str(path))
        self.example = None
        self.notice = (
            "good",
            f"Loaded {safe}: {len(df):,} rows, {df.shape[1]} columns.",
            f"A copy is kept in {self.data_dir} so the exported script can find it.",
        )
        return True

    def load_session_file(self, name: str, data: bytes) -> bool:
        """Reopen a saved analysis (.msession). The data file must still exist."""
        try:
            s = session_from_dict(json.loads(data.decode("utf-8")))
            if not s.data_path or not Path(s.data_path).exists():
                raise ValueError(
                    "The data file used by this analysis was not found at "
                    f"{s.data_path or 'its saved location'}."
                )
            df = load_table(s.data_path)
        except Exception as exc:
            self.notice = ("critical", f"'{Path(name).name}' could not be opened.", str(exc))
            return False
        self.set_data(df, Path(s.data_path).name, s.data_path)
        self.session = s
        self.suggested = list(s.decisions)
        self.ticked = {d.id: {o.id: True for o in d.options} for d in s.decisions}
        self.choices_confirmed = self.fairness_confirmed = True
        self.blind_mode = s.blind is not None
        self.open_block = None
        if s.verdict is not None:
            self.progress = RunProgress(total=len(s.results), done=len(s.results), stage="finished")
        self.notice = ("good", f"Reopened {Path(name).name}.", "")
        return True

    # ============================================================ question
    def outcome_columns(self) -> list[str]:
        p = self.session.profile
        return [c.name for c in p.columns if c.kind in OUTCOME_KINDS] if p else []

    def factor_columns(self) -> list[str]:
        p = self.session.profile
        return [c.name for c in p.columns if c.kind in PREDICTOR_KINDS] if p else []

    def set_question(self, y: str | None, x: str | None) -> str | None:
        """Set Y and X. Returns an error message when the pair can't be analysed."""
        s = self.session
        if (y, x) == (s.y, s.x):
            return self.question_error()
        self.invalidate_plan("question")
        s.y, s.x, s.family = y, x, None
        if y and x:
            try:
                api.validate_question(s.profile, y, x)
                s.family = api.suggest_family(s.profile, y)
            except ValueError:
                pass
            if s.family is not None:
                self.ensure_suggestions()
                self.open_block = "choices"
        return self.question_error()

    def question_error(self) -> str | None:
        s = self.session
        if not (s.y and s.x) or s.family is not None:
            return None
        try:
            api.validate_question(s.profile, s.y, s.x)
        except ValueError as exc:
            return str(exc)
        return "This combination can't be analysed."

    def set_blind(self, on: bool) -> None:
        if on != self.blind_mode:
            self.blind_mode = on
            self.invalidate_plan("run")

    # ============================================================= choices
    def ensure_suggestions(self) -> None:
        s = self.session
        if not self.suggested and s.family is not None:
            self.suggested = api.suggest_decisions(s.profile, s.y, s.x, self.df)
            self.ticked = {d.id: {o.id: True for o in d.options} for d in self.suggested}

    def set_ticked(self, decision_id: str, option_ids: list[str]) -> None:
        d = next(d for d in self.suggested if d.id == decision_id)
        new = {o.id: o.id in option_ids for o in d.options}
        if new != self.ticked.get(decision_id):
            self.ticked[decision_id] = new
            self.invalidate_plan("choices")
            self.choices_confirmed = False

    def selected_decisions(self) -> list[Decision]:
        """Suggested decisions, keeping only ticked options (at least one each)."""
        out = []
        for d in self.suggested:
            keep = tuple(o for o in d.options if self.ticked.get(d.id, {}).get(o.id, True))
            if keep:
                out.append(replace(d, options=keep))
        return out

    def empty_choices(self) -> list[str]:
        return [d.label for d in self.suggested if not any(self.ticked.get(d.id, {}).values())]

    def n_total(self) -> int:
        return count_specs(self.selected_decisions())

    def formula(self) -> str:
        sizes = [len(d.options) for d in self.selected_decisions() if len(d.options) > 1]
        return " × ".join(map(str, sizes))

    def set_limit(self, limit: int) -> None:
        if limit != self.session.max_specs:
            self.session.max_specs = limit
            self.session.sample_if_over = True
            self.invalidate_plan("run")

    def confirm_choices(self) -> bool:
        if self.empty_choices():
            return False
        self.session.decisions = self.selected_decisions()
        self.choices_confirmed = True
        self.open_block = None if self.fairness_confirmed else "fairness"
        return True

    # ============================================================ fairness
    def variables(self) -> list[str]:
        return api.variables_to_assess(self.session.decisions)

    def set_answer(self, var: str, index: int, word: str | None) -> None:
        old = self.session.guardrails.get(var)
        if old is None and not word:
            return
        vals = (
            [old.happens_before_x, old.could_be_caused_by_x, old.could_be_caused_by_y]
            if old
            else [None, None, None]
        )
        vals[index] = TO_BOOL.get(word) if word else None
        new = GuardrailAnswers(*vals)
        if old != new:
            self.session.guardrails[var] = new
            self.invalidate_plan("fairness")

    def answer_word(self, var: str, index: int) -> str | None:
        a = self.session.guardrails.get(var)
        if a is None:
            return None
        return FROM_BOOL[
            (a.happens_before_x, a.could_be_caused_by_x, a.could_be_caused_by_y)[index]
        ]

    def assessment(self, var: str) -> ControlAssessment | None:
        a = self.session.guardrails.get(var)
        return api.assess_control(var, a) if a else None

    def assessments(self) -> list[ControlAssessment]:
        vs = set(self.variables())
        return api.assess_controls({v: a for v, a in self.session.guardrails.items() if v in vs})

    def fair_count(self) -> tuple[int, int]:
        """(fair analyses, analyses that will run) for the current plan."""
        s = self.session
        specs = api.build_specs(s.decisions, max_specs=s.max_specs, seed=s.seed)
        bad = {a.variable for a in self.assessments() if not a.keep}
        fair = sum(
            not (api.conditioned_on(sp, s.decisions) & bad)  # type: ignore[arg-type]
            for sp in specs
        )
        return fair, len(specs)

    def confirm_fairness(self) -> bool:
        if self.fair_count()[0] == 0:
            return False
        self.session.assessments = self.assessments()
        self.fairness_confirmed = True
        self.open_block = None
        return True

    # ======================================================= plan & blocks
    def block_state(self, block: BlockId) -> Literal["done", "current", "locked"]:
        done = {
            "data": self.df is not None,
            "question": self.session.family is not None,
            "choices": self.choices_confirmed,
            "fairness": self.fairness_confirmed,
        }
        if done[block]:
            return "done"
        first_open = next((b for b in BLOCK_ORDER if not done[b]), None)
        return "current" if block == first_open else "locked"

    def ready_to_run(self) -> bool:
        return all(self.block_state(b) == "done" for b in BLOCK_ORDER)

    def open(self, block: BlockId | None) -> None:
        if block is None or self.block_state(block) != "locked":
            self.open_block = block

    def invalidate_plan(self, from_step: str) -> None:
        """A plan input changed: drop everything downstream of ``from_step``.

        If the plan had been locked and results were shown, the old lock is recorded
        in the session notes, so changing the plan after seeing results stays visible.
        """
        self.cancel()
        s = self.session
        if s.blind is not None and s.results:
            s.notes += (
                f"Plan sha256 {s.blind.sha256[:16]}... (locked {s.blind.locked_at}) was changed "
                f"at '{from_step}' after results had been shown.\n"
            )
        s.blind = None
        s.specs, s.results, s.verdict, s.cherry_pick = [], [], None, None
        self.progress = RunProgress()
        if from_step == "question":
            self.suggested, self.ticked = [], {}
            s.decisions = []
            self.choices_confirmed = False
        if from_step in ("question", "choices"):
            self.fairness_confirmed = False
        if from_step == "fairness":
            self.fairness_confirmed = False

    def set_run_options(self, n_permutations: int, alpha: float, seed: int) -> None:
        s = self.session
        if (n_permutations, alpha, seed) != (s.n_permutations, s.alpha, s.seed):
            self.invalidate_plan("run")
            s.n_permutations, s.alpha, s.seed = n_permutations, alpha, seed

    def estimate_seconds(self) -> float:
        n = min(self.n_total(), self.session.max_specs)
        return n * SECONDS_PER_FIT * (1 + self.session.n_permutations)

    # ================================================================= run
    @property
    def running(self) -> bool:
        return self.job is not None and self.job.running

    def start_run(self) -> None:
        if not self.ready_to_run() or self.running or self.df is None:
            return
        s = self.session
        s.specs, s.results, s.verdict, s.cherry_pick = [], [], None, None
        if self.blind_mode and (s.blind is None or not api.verify_plan(s, s.blind)):
            s.blind = api.lock_plan(s)
        params = {
            "max_specs": s.max_specs,
            "seed": s.seed,
            "y": s.y,
            "x": s.x,
            "family": s.family,
            "alpha": s.alpha,
            "n_permutations": s.n_permutations,
        }
        self.progress = RunProgress(stage="run", started=time.monotonic())
        self.run_id += 1
        self.notice = None
        self.job = RunJob(self.df, params, s.decisions, s.assessments)
        self.job.start()

    def cancel(self) -> None:
        if self.running:
            self.job.cancel()  # type: ignore[union-attr]
            self.job.wait(10)  # type: ignore[union-attr]
            self.poll()

    def poll(self) -> bool:
        """Apply the job's queued messages. Returns True when the run just ended."""
        if self.job is None:
            return False
        ended = False
        s, p = self.session, self.progress
        for kind, payload in self.job.drain():
            if kind == "specs":
                s.specs = payload
                p.total = len(payload)
            elif kind == "result":
                p.live.append(payload)
                p.done = len(p.live)
                p.current = " · ".join(self.choice_labels(payload))
            elif kind == "validated":
                s.results = payload
            elif kind == "stage":
                p.stage = payload
            elif kind == "perm":
                p.perm_done, p.perm_total = payload
            elif kind == "verdict":
                s.verdict = payload
            elif kind == "done":
                p.stage, ended = "finished", True
            elif kind == "cancelled":
                s.specs, s.results, s.verdict = [], [], None
                self.progress = RunProgress()
                self.notice = (
                    "warning",
                    "Cancelled. Nothing was saved.",
                    "Your locked plan is kept, so you can run it again.",
                )
                ended = True
            elif kind == "error":
                s.results, s.verdict = [], None
                self.progress = RunProgress()
                self.notice = ("critical", "The analysis stopped.", str(payload))
                ended = True
        if self.progress.started:
            self.progress.elapsed = time.monotonic() - self.progress.started
        if ended:
            self.job = None
        return ended

    def choice_labels(self, r: SpecResult) -> list[str]:
        out = []
        for d in self.session.decisions:
            if d.id in r.choices and len(d.options) > 1:
                out.append(d.option(r.choices[d.id]).label)
        return out or ["standard analysis"]

    # ============================================================= results
    def check_cherry(self, value: float | None) -> None:
        s = self.session
        if value is None or not s.results:
            s.reported_estimate, s.cherry_pick = None, None
            return
        if value != s.reported_estimate or s.cherry_pick is None:
            s.reported_estimate = float(value)
            s.cherry_pick = api.cherry_pick_check(s.results, s.reported_estimate)

    def importance(self) -> list[tuple[str, float]]:
        """(decision label, share of variation) for decisions with 2+ options, largest first."""
        s = self.session
        imp = api.decision_importance(s.results, s.decisions)
        multi = {d.id: d for d in s.decisions if len(d.options) > 1}
        return [(multi[k].label, v) for k, v in imp.items() if k in multi]

    def result_by_id(self, spec_id: int) -> SpecResult | None:
        return next((r for r in self.session.results if r.spec_id == spec_id), None)

    def single_code(self, r: SpecResult) -> str:
        from ..core.serialize import decision_to_dict

        s = self.session
        decs = [decision_to_dict(d) for d in s.decisions]
        return (
            "from multiverse_studio.core import api\n"
            "from multiverse_studio.core.serialize import decision_from_dict\n"
            "from multiverse_studio.core.types import Spec\n"
            "from multiverse_studio.io.loaders import load_table\n\n"
            f"df = load_table({s.data_path!r})\n"
            f"decisions = [decision_from_dict(d) for d in {decs!r}]\n"
            f"result = api.fit_one(df, {s.y!r}, {s.x!r}, {s.family!r}, decisions, "
            f"Spec({r.spec_id}, {r.choices!r}), alpha={s.alpha})\n"
            "print(result)\n"
        )

    # ============================================================== export
    def file_stem(self) -> str:
        return f"{self.session.x}_vs_{self.session.y}".replace(" ", "_")

    def script_text(self) -> str:
        return render_script(self.session, f"{self.file_stem()}.py")

    def report_text(self) -> str:
        return json.dumps(report_dict(self.session), indent=2)

    def session_text(self) -> str:
        return json.dumps(session_to_dict(self.session), indent=2)

    def pdf_bytes(self) -> bytes:
        return render_pdf(self.session)

    def plan_matches(self) -> bool | None:
        s = self.session
        return None if s.blind is None else api.verify_plan(s, s.blind)

    def start_over(self) -> None:
        self.cancel()
        seed, revision = self.session.seed, self.revision
        self.__init__(data_dir=self.data_dir)  # type: ignore[misc]
        self.session.seed, self.revision = seed, revision + 1

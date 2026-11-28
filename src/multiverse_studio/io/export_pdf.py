"""PDF report via Matplotlib's PdfPages (no extra dependency). Owner: C.

Pages: summary + verdict, specification curve, decision importance, then flowing
text pages with the fairness answers, cherry-pick check, methods/results
paragraphs and the plan fingerprint.
"""

from __future__ import annotations

import textwrap
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.textpath import text_to_path

from .. import __version__
from ..core import api
from ..core.narrative import MODEL_NAMES
from ..core.types import Session
from ..plots.importance import importance_figure
from ..plots.palette import FONT_FAMILY, palette
from ..plots.spec_curve import short, spec_curve_figure
from .export_json import environment_info
from .wording import ROLE_WORDS, UNIT_WORDS, VERDICT_WORDS

PORTRAIT = (8.27, 11.69)  # A4, inches
LANDSCAPE = (11.69, 8.27)
MARGIN = 0.85
PAL = palette(dark=False)
ANSWERS = {True: "Yes", False: "No", None: "Not sure"}


def _wrap(paragraph: str, font: FontProperties) -> list[str]:
    """Split into lines that fit between the margins, using this font's real width."""
    if not paragraph.strip():
        return [""]
    points, _, _ = text_to_path.get_text_width_height_descent(paragraph, font, ismath=False)
    available = (PORTRAIT[0] - 2 * MARGIN) * 72
    # 0.95 leaves slack for lines with wider letters than the paragraph's average
    return textwrap.wrap(paragraph, max(10, int(0.95 * available * len(paragraph) / points)))


class _TextPages:
    """Writes wrapped paragraphs down A4 pages, starting a new page when one is full."""

    def __init__(self, pdf: PdfPages) -> None:
        self.pdf = pdf
        self.fig: Figure | None = None
        self.y = 0.0  # inches from the bottom of the page

    def _room(self, inches: float) -> None:
        if self.fig is not None and self.y - inches >= MARGIN:
            return
        self.close()
        self.fig = Figure(figsize=PORTRAIT, facecolor=PAL.surface)
        self.y = PORTRAIT[1] - MARGIN

    def write(
        self,
        text: str,
        *,
        size: float = 10,
        bold: bool = False,
        muted: bool = False,
        mono: bool = False,
        gap: float = 0.1,
    ) -> None:
        font = FontProperties(
            family="monospace" if mono else FONT_FAMILY,
            size=size,
            weight="bold" if bold else "normal",
        )
        line_height = size * 1.45 / 72
        for paragraph in text.split("\n"):
            for line in _wrap(paragraph, font):
                self._room(line_height)
                self.fig.text(
                    MARGIN / PORTRAIT[0],
                    self.y / PORTRAIT[1],
                    line,
                    va="top",
                    fontproperties=font,
                    color=PAL.text_secondary if muted else PAL.text_primary,
                    parse_math=False,  # a "$" in a column name is just a dollar sign
                )
                self.y -= line_height
        self.y -= gap

    def heading(self, text: str, size: float = 14) -> None:
        self._room(1.1)  # keep a heading on the same page as the start of its section
        if self.y < PORTRAIT[1] - MARGIN:
            self.y -= 0.15
        self.write(text, size=size, bold=True)

    def fact(self, name: str, value: str, meaning: str) -> None:
        self._room(0.7)
        self.write(f"{name}: {value}", size=11, bold=True, gap=0)
        self.write(meaning, muted=True, gap=0.14)

    def close(self) -> None:
        if self.fig is not None:
            self.pdf.savefig(self.fig)
            self.fig = None


def _summary(page: _TextPages, s: Session) -> None:
    v = s.verdict
    word = VERDICT_WORDS[v.label][1]
    unit = UNIT_WORDS[s.family].format(x=s.x, y=s.y)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    page.write("Multiverse Studio report", muted=True)
    page.write(f"Does {s.x} affect {s.y}?", size=20, bold=True)
    data = Path(s.data_path).name if s.data_path else "not recorded"
    rows = f" ({s.profile.n_rows:,} rows)" if s.profile else ""
    page.write(
        f"Data: {data}{rows}. Model: {MODEL_NAMES[s.family]}. Created {now}.", muted=True, gap=0.3
    )
    page.write(f"Verdict: {word}", size=15, bold=True)
    page.write(v.explanation, size=11, gap=0.3)

    page.fact(
        "Typical effect (median)",
        f"{v.median_estimate:+.3g}",
        f"The middle result of the fair analyses, measured as {unit}.",
    )
    page.fact(
        "Point the same way",
        f"{round(v.share_same_sign * v.n_valid):,} of {v.n_valid:,} ({v.share_same_sign:.0%})",
        "Fair analyses whose effect has the same sign as the typical effect.",
    )
    page.fact(
        "Significant in that direction",
        f"{round(v.share_significant * v.n_valid):,} of {v.n_valid:,} ({v.share_significant:.0%})",
        f"Fair analyses with p below {v.alpha:g} in the direction of the typical effect.",
    )
    if v.permutation_p is None:
        page.fact(
            "Could it be luck? (permutation test)",
            "Not checked",
            "The test was skipped, so the verdict relies on the share of significant analyses.",
        )
    else:
        digits = 2 if s.n_permutations <= 100 else 3
        likely = "Unlikely" if v.permutation_p < 0.05 else "Possible"
        page.fact(
            "Could it be luck? (permutation test)",
            f"{likely} (p = {v.permutation_p:.{digits}f})",
            f"How often shuffling {s.x} at random ({s.n_permutations} times) gave a pattern "
            "at least this strong.",
        )
    page.fact(
        "Could not be fitted",
        f"{v.n_specs - v.n_ok:,} of {v.n_specs:,}",
        "Combinations with too little data, or where the model failed.",
    )
    page.fact(
        "Left out as unfair",
        f"{v.n_ok - v.n_valid:,}",
        "Analyses that keep equal or group by a variable that would distort the effect. "
        "They are not counted above.",
    )
    if s.notes.strip():
        page.heading("The plan was changed after results were seen", size=12)
        page.write(s.notes.strip())


def _title(fig: Figure, x: float, y: float, text: str) -> None:
    fig.text(x, y, text, fontsize=14, fontweight="bold", family=FONT_FAMILY, color=PAL.text_primary)


def _caption(fig: Figure, x: float, y: float, text: str) -> None:
    fig.text(x, y, text, fontsize=9, family=FONT_FAMILY, color=PAL.text_secondary)


def _curve_page(s: Session) -> Figure:
    fig = spec_curve_figure(
        s.results,
        s.decisions,
        alpha=s.alpha,
        reported_estimate=s.reported_estimate,
        y_label=f"Effect on {short(s.y)}",
        figsize=LANDSCAPE,
    )
    gridspec = fig.axes[0].get_gridspec()
    gridspec.update(top=0.82, bottom=0.05)  # room for the title and legend
    for ax in fig.axes:  # update() only moves pyplot figures by itself
        ax.set_position(ax.get_subplotspec().get_position(fig))
    _title(fig, 0.04, 0.95, "Every analysis, sorted by effect size")
    _caption(
        fig,
        0.04,
        0.915,
        "Specification curve. Top: the effect each analysis found, with its 95% interval. "
        "Bottom: the choices it used.",
    )

    def mark(label: str, color: str, hollow: bool = False) -> Line2D:
        face = PAL.surface if hollow else color
        return Line2D(
            [], [], linestyle="none", marker="o", label=label, color=color, markerfacecolor=face
        )

    handles = [
        mark("Significant, same direction", PAL.sig_same),
        mark("Significant, opposite", PAL.sig_opposite),
        mark("Not significant", PAL.not_significant),
        mark("Left out (unfair comparison)", PAL.not_significant, hollow=True),
    ]
    if s.reported_estimate is not None:
        handles.append(
            Line2D([], [], linestyle="--", color=PAL.reported_line, label="Reported result")
        )
    fig.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(0.03, 0.9),
        ncols=len(handles),
        frameon=False,
        prop={"family": FONT_FAMILY, "size": 8.5},
    )
    return fig


def _importance_page(s: Session) -> Figure:
    labels = {d.id: short(d.label, 36) for d in s.decisions if len(d.options) > 1}
    scores = api.decision_importance(s.results, s.decisions)
    scores = {k: v for k, v in scores.items() if k in labels}
    fig = importance_figure(scores, labels, figsize=PORTRAIT)
    if scores:
        top = 0.8
        fig.subplots_adjust(
            left=0.36, right=0.9, top=top, bottom=top - min(0.6, 0.06 * len(scores))
        )
    _title(fig, 0.1, 0.92, "Which choice matters most?")
    _caption(
        fig, 0.1, 0.895, "How much of the difference between analyses each choice explains (η²)."
    )
    if scores:
        first, share = next(iter(scores.items()))
        sentence = (
            f"{labels[first]} changes the answer most ({share:.0%} of the variation)."
            if share >= 0.05
            else "No single choice changes the answer much."
        )
        fig.text(0.1, 0.86, sentence, fontsize=10, family=FONT_FAMILY, color=PAL.text_primary)
    return fig


def _details(page: _TextPages, s: Session) -> None:
    page.heading("Fair comparisons")
    variables = api.variables_to_assess(s.decisions)
    if not variables:
        page.write(
            "The plan keeps nothing equal and has no subgroups, so there was nothing to ask."
        )
    assessed = {a.variable: a for a in s.assessments}
    for var in variables:
        a = assessed.get(var)
        word = ROLE_WORDS[a.role.value] if a else "Not answered: kept"
        page.write(f"{var}: {word}", size=11, bold=True, gap=0)
        if answers := s.guardrails.get(var):
            page.write(
                f"Happens before {s.x}: {ANSWERS[answers.happens_before_x]}. "
                f"Could {s.x} cause it: {ANSWERS[answers.could_be_caused_by_x]}. "
                f"Could {s.y} cause it: {ANSWERS[answers.could_be_caused_by_y]}.",
                muted=True,
                gap=0,
            )
        page.write(a.reason if a else "No answers were given for this variable.", gap=0.16)

    page.heading("Cherry-pick check")
    if c := s.cherry_pick:
        page.write(c.explanation)
        page.write(
            f"Percentile among fair analyses: {c.percentile:.0f}. That is the share of fair "
            f"analyses with an effect at or below {c.reported_estimate:+.3g}."
        )
    else:
        page.write("No reported result was entered.")

    page.heading("Methods")
    page.write(api.methods_paragraph(s))
    page.heading("Results")
    page.write(api.results_paragraph(s))

    page.heading("Plan fingerprint")
    if s.blind is None:
        page.write(
            "No locked plan. Blind mode was off, so there is no fingerprint to check the plan "
            "against."
        )
    else:
        matches = api.verify_plan(s, s.blind)
        page.write(
            "The plan matches its fingerprint."
            if matches
            else "The plan no longer matches its fingerprint."
        )
        page.write(f"Locked at {s.blind.locked_at}. SHA-256 of the plan:", gap=0)
        page.write(s.blind.sha256, size=9, mono=True)

    env = environment_info()
    versions = ", ".join(
        f"{name} {number}"
        for name, number in env["packages"].items()
        if number and name != "multiverse-studio"
    )
    page.heading("How to repeat it")
    page.write(
        f"Seed {s.seed}. Multiverse Studio {__version__}, Python {env['python']}, {versions}. "
        "The Python script saved from the app re-runs the analyses and the verdict."
    )


def render_pdf(session: Session) -> bytes:
    """The whole report as PDF bytes. Raises ValueError before a run has finished."""
    if session.verdict is None or not session.results:
        raise ValueError("Run the analysis first.")
    buffer = BytesIO()
    with PdfPages(buffer, metadata={"Title": "Multiverse Studio report"}) as pdf:
        page = _TextPages(pdf)
        _summary(page, session)
        page.close()
        for fig in (_curve_page(session), _importance_page(session)):
            for text in fig.findobj(Text):
                text.set_parse_math(False)
            pdf.savefig(fig)
        _details(page, session)
        page.close()
    return buffer.getvalue()


def export_pdf(session: Session, path: str | Path) -> Path:
    path = Path(path)
    path.write_bytes(render_pdf(session))
    return path

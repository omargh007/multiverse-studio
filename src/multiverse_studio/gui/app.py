"""Multiverse Studio: the Streamlit workbench (plan beside evidence).

Start it with ``multiverse-studio`` or ``python -m multiverse_studio`` (see
``launch.py``); it opens in the browser at http://localhost:8501 and runs only on
this computer.

Layout: a top bar, the plan on the left (data, question, choices, fair
comparisons, then Run) and the evidence on the right (progress while running,
then the verdict, the specification curve, what matters most, the cherry-pick
check, ready-to-use text and the exports).

This file only draws. Every change goes through ``Workbench`` (``state.py``),
and the analysis itself through ``core.api``. Imports are absolute because
Streamlit runs this file as a script.
"""

from __future__ import annotations

import html
from urllib.parse import quote

import pandas as pd
import streamlit as st

from multiverse_studio import __version__
from multiverse_studio.core.types import CausalRole, ColumnKind
from multiverse_studio.gui import charts
from multiverse_studio.gui.state import (
    ALPHAS,
    ANSWER_WORDS,
    EXAMPLES,
    LIMITS,
    MODEL_NAMES,
    MODEL_WORDS,
    PERMUTATION_CHOICES,
    Workbench,
)
from multiverse_studio.gui.theme import BLOCKS, TEXT_SIZES, css, tokens
from multiverse_studio.plots.palette import palette

# ------------------------------------------------------------------- icons (inline SVG)
_SVG = (
    '<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>'
)
ICON_PATHS = {
    "good": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.8 2.8L16.5 9"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "warning": '<path d="M12 3.5l9.5 17h-19z"/><path d="M12 10v4.5M12 17.5h.01"/>',
    "critical": '<circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "unlock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7.5-2"/>',
    "wait": '<circle cx="12" cy="12" r="8"/>',
    "busy": '<path d="M12 3a9 9 0 1 0 9 9"/>',
    "skip": '<path d="M7 12h10"/>',
}


def icon(name: str, size: int = 16, color: str | None = None) -> str:
    """An icon as an <img> data URI (Streamlit strips inline <svg> from HTML)."""
    t = st.session_state.get("_tokens") or tokens(False)
    svg = (
        _SVG.format(s=size, p=ICON_PATHS[name])
        .replace('stroke="currentColor"', f'stroke="{color or t["text_secondary"]}"')
        .replace(' aria-hidden="true"', ' xmlns="http://www.w3.org/2000/svg"')
    )
    return (
        f'<img src="data:image/svg+xml;utf8,{quote(svg)}" width="{size}" height="{size}" '
        'alt="" style="display:inline-block;vertical-align:middle;flex:none">'
    )


SOFT = {
    "good": "good_soft",
    "warning": "warning_soft",
    "critical": "critical_soft",
    "info": "accent_soft",
}
INK = {"good": "good", "warning": "warning", "critical": "critical", "info": "accent"}
VERDICT_WORDS = {
    "consistent": ("good", "Consistent", "it holds up across reasonable analyses"),
    "mixed": ("warning", "Depends on choices", "the answer changes with the analysis"),
    "fragile": ("critical", "Fragile", "it does not hold up across reasonable analyses"),
}
ROLE_CHIP = {
    CausalRole.CONFOUNDER: ("good", "Fair to keep equal"),
    CausalRole.NEUTRAL: ("good", "Fair to keep equal"),
    CausalRole.UNKNOWN: ("warning", "Kept, but flagged"),
    CausalRole.MEDIATOR: ("critical", "Unfair: left out"),
    CausalRole.COLLIDER: ("critical", "Unfair: left out"),
    CausalRole.OUTCOME_PROXY: ("critical", "Unfair: left out"),
}
KIND_NAMES = {
    ColumnKind.NUMERIC: "Number",
    ColumnKind.BINARY: "Yes / no",
    ColumnKind.COUNT: "Count",
    ColumnKind.CATEGORICAL: "Category",
    ColumnKind.TEXT: "Text (not used)",
    ColumnKind.DATETIME: "Date (not used)",
}
TECH = {
    "outliers": "outliers",
    "controls": "control variables",
    "subset": "subsets",
    "transform": "transforms",
    "missing": "missing data",
}
POLL_SECONDS = 0.75
LOCKED_EDIT_WARNING = (
    "Changing anything here clears the results and records, in every export, that the "
    "locked plan was changed after the results were seen."
)
UNIT_WORDS = {
    "linear": "points of {y} for each one-unit increase in {x}",
    "logistic": "change in the log-odds of {y} for each one-unit increase in {x}",
    "poisson": "change in the log count of {y} for each one-unit increase in {x}",
}


# ----------------------------------------------------------------------- helpers
def esc(text: object) -> str:
    return html.escape(str(text))


def callout(kind: str, lead: str, text: str = "", *, raw: bool = False) -> None:
    """Tinted box with an icon and a bold lead sentence (never a side stripe)."""
    t = st.session_state["_tokens"]
    body = text if raw else esc(text)
    st.html(
        f'<div class="ms-callout" role="{"alert" if kind == "critical" else "status"}" '
        f'style="background:{t[SOFT[kind]]}">'
        f"<span>{icon(kind, 18, t[INK[kind]])}</span>"
        f'<div><b class="lead">{esc(lead)}</b>'
        f"{f'<span class=body>{body}</span>' if body else ''}</div></div>"
    )


def chip(text: str, kind: str = "") -> str:
    return f'<span class="ms-chip {kind}">{text}</span>'


def fmt_time(seconds: float) -> str:
    if seconds < 60:
        return f"{max(1, round(seconds))} second{'s' if round(seconds) > 1 else ''}"
    m = round(seconds / 60)
    return f"{m} minute{'s' if m != 1 else ''}"


def workbench() -> Workbench:
    if "wb" not in st.session_state:
        st.session_state["wb"] = Workbench()
    return st.session_state["wb"]


def is_dark() -> bool:
    try:
        return st.context.theme.type == "dark"
    except Exception:  # older Streamlit or a test runner
        return False


# ======================================================================= top bar
def top_bar(wb: Workbench) -> None:
    s = wb.session
    t = st.session_state["_tokens"]
    with st.container(key="topbar", horizontal=True, vertical_alignment="center", gap="medium"):
        logo = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">'
            f'<rect width="28" height="28" rx="7" fill="{t["accent_soft"]}"/>'
            f'<circle cx="8" cy="19" r="2.3" fill="{t["accent"]}"/><circle cx="13" cy="15" r="2.3" fill="{t["accent"]}"/>'
            f'<circle cx="18" cy="12" r="2.3" fill="{t["accent"]}"/><circle cx="22" cy="7.5" r="2.3" fill="{t["button"]}"/></svg>'
        )
        st.html(
            '<div class="ms-head">'
            f'<img src="data:image/svg+xml;utf8,{quote(logo)}" width="28" height="28" alt="">'
            f'<div><div style="font-size:16px;font-weight:700;color:{t["text"]};line-height:1.2">Multiverse Studio</div>'
            f'<div class="ms-muted" style="font-size:12px">Does your finding hold up? · offline · v{esc(__version__)}</div></div></div>',
            width="content",
        )
        with st.container(key="topbar-spacer", width="stretch"):
            st.space("stretch")
        if s.blind is not None:
            lock = chip(
                f'{icon("lock", 13, t["good"])}Plan locked <span class="ms-mono">{s.blind.sha256[:4]}…{s.blind.sha256[-4:]}</span>',
                "good",
            )
        elif wb.blind_mode:
            lock = chip(f"{icon('unlock', 13)}Blind mode on · not locked yet")
        else:
            lock = chip(f"{icon('unlock', 13, t['warning'])}Blind mode off")
        st.html(
            f'<div style="display:flex;gap:8px;flex-wrap:wrap">{chip(f"Repeat-exactly number <span class=ms-mono>{s.seed}</span>")}{lock}</div>',
            width="content",
        )
        with st.popover("Display", icon=":material/text_fields:"):
            st.segmented_control(
                "Text size",
                list(TEXT_SIZES),
                key="text_size",
                help="Larger text for classroom projectors and low vision.",
            )
            st.caption("Light or dark: open the ⋮ menu at the top right, then Settings.")


# ========================================================================== plan
def plan_pane(wb: Workbench) -> None:
    with st.container(key="plan", gap="small"):
        st.html(
            '<div style="font-size:19px;font-weight:700">What will be run</div>'
            '<div class="ms-muted" style="margin-top:2px">Everything that decides the result, '
            "written down before any result is shown.</div>"
        )
        if wb.notice:
            kind, lead, text = wb.notice
            callout(kind, lead, text)
        for i, (bid, title, tech) in enumerate(BLOCKS, start=1):
            st.divider()
            block(wb, i, bid, title, tech)
        st.divider()
        run_section(wb)


def block(wb: Workbench, n: int, bid: str, title: str, tech: str) -> None:
    state = wb.block_state(bid)  # type: ignore[arg-type]
    is_open = (wb.open_block == bid or state == "current") and state != "locked"
    t = st.session_state["_tokens"]
    badge = icon("check", 13, t["good"]) if state == "done" else str(n)
    cls = "done" if state == "done" else ("current" if state == "current" or is_open else "")
    with st.container(horizontal=True, vertical_alignment="center", gap="small", wrap=False):
        st.html(
            f'<div class="ms-head"><span class="ms-num {cls}">{badge}</span>'
            f'<span class="ms-block-title">{esc(title)} <span class="ms-tech">{esc(tech)}</span></span></div>',
            width="stretch",
        )
        if state == "done" and not is_open:
            st.button(
                "Edit",
                key=f"edit_{bid}",
                type="tertiary",
                on_click=wb.open,
                args=(bid,),
                help=LOCKED_EDIT_WARNING
                if wb.session.blind is not None and wb.session.results
                else f"Change {title.lower()}",
            )
        elif is_open and state == "done" and bid in ("data", "question"):
            st.button("Done", key=f"close_{bid}", type="tertiary", on_click=wb.open, args=(None,))
    if is_open and state == "done" and wb.session.blind is not None and wb.session.results:
        callout("warning", "This plan is locked.", LOCKED_EDIT_WARNING)
    if is_open:
        {
            "data": data_editor,
            "question": question_editor,
            "choices": choices_editor,
            "fairness": fairness_editor,
        }[bid](wb)
    elif state == "done":
        st.html(f'<div class="ms-summary" style="padding-left:32px">{summary(wb, bid)}</div>')
    else:
        prev = BLOCKS[n - 2][1].lower()
        st.html(
            f'<div class="ms-muted" style="padding-left:32px">Available after {esc(prev)}.</div>'
        )


def summary(wb: Workbench, bid: str) -> str:
    s = wb.session
    if bid == "data":
        rows = len(wb.df) if wb.df is not None else 0
        cols = wb.df.shape[1] if wb.df is not None else 0
        extra = " · example with a known answer" if wb.example else ""
        return f"{esc(wb.data_name)} · {rows:,} rows · {cols} columns{extra}"
    if bid == "question":
        return f"Does <b>{esc(s.x)}</b> affect <b>{esc(s.y)}</b>? {esc(MODEL_NAMES[s.family])}."
    if bid == "choices":
        n = len(s.decisions)
        total = wb.n_total()
        sample = f", a sample of {s.max_specs:,}" if total > s.max_specs else ""
        return f"{n} choice{'s' if n != 1 else ''} → {total:,} analyses{sample}"
    bad = [a for a in s.assessments if not a.keep]
    fair, run_n = wb.fair_count()
    if not wb.variables():
        return "Nothing to check: every analysis is fair."
    if bad:
        names = ", ".join(
            f"<b>{esc(a.variable)}</b> ({esc(a.role.value.replace('_', ' '))})" for a in bad
        )
        return f"{names} left out. {fair:,} of {run_n:,} analyses are fair."
    return f"All kept. {fair:,} of {run_n:,} analyses are fair."


# ---------------------------------------------------------------- data editor
def data_editor(wb: Workbench) -> None:
    rev = wb.revision
    up = st.file_uploader(
        "Load your table (CSV or Excel)",
        type=["csv", "tsv", "txt", "xlsx", "xls"],
        key=f"upload_{rev}",
        help="One row per person or case, one column per measurement. The first row must "
        "hold the column names. Your data never leaves this computer.",
    )
    if up is not None:
        if wb.load_upload(up.name, up.getvalue()):
            st.rerun()
    ex = st.radio(
        "Or try an example with a known answer",
        [k for k, _, _ in EXAMPLES],
        format_func=lambda k: next(n for kk, n, _ in EXAMPLES if kk == k),
        captions=[d for _, _, d in EXAMPLES],
        index=None,
        key=f"example_{rev}",
        help="Each example is generated with a true effect you know in advance, so you can "
        "watch whether the method finds it.",
    )
    if st.button("Use this example", disabled=ex is None, key=f"use_example_{rev}"):
        wb.load_example(ex)
        st.rerun()
    with st.expander("Reopen a saved analysis"):
        saved = st.file_uploader(
            "Analysis file (.msession)",
            type=["msession"],
            key=f"session_{rev}",
            help="Saved from Save & share. The data file it used must still be on this computer.",
        )
        if saved is not None and wb.load_session_file(saved.name, saved.getvalue()):
            st.rerun()


# ------------------------------------------------------------ question editor
def question_editor(wb: Workbench) -> None:
    s, rev = wb.session, wb.revision
    ys, xs = wb.outcome_columns(), wb.factor_columns()
    ky, kx = f"q_y_{rev}", f"q_x_{rev}"

    def changed() -> None:
        wb.set_question(st.session_state.get(ky), st.session_state.get(kx))
        wb.notice = None

    y = st.selectbox(
        "What do you want to explain?  ·  outcome, Y",
        ys,
        index=ys.index(s.y) if s.y in ys else None,
        placeholder="Choose a column",
        key=ky,
        on_change=changed,
    )
    x_options = [c for c in xs if c != y]
    st.selectbox(
        "What might affect it?  ·  factor, X",
        x_options,
        index=x_options.index(s.x) if s.x in x_options else None,
        placeholder="Choose a column",
        key=kx,
        on_change=changed,
    )
    err = wb.question_error()
    if err:
        callout("critical", "Pick different columns.", err)
    elif s.family:
        callout("info", f"Question: does {s.x} affect {s.y}?", f"{s.y} {MODEL_WORDS[s.family]}")
    kb = f"blind_{rev}"
    st.toggle(
        "Blind mode  ·  pre-registration (recommended)",
        value=wb.blind_mode,
        key=kb,
        on_change=lambda: wb.set_blind(bool(st.session_state[kb])),
    )
    st.caption(
        "You lock your analysis plan before any result is shown. The lock is a digital "
        "fingerprint saved in every export, so anyone can verify the plan wasn't changed after "
        "seeing the results."
    )


# ------------------------------------------------------------- choices editor
def choices_editor(wb: Workbench) -> None:
    rev = wb.revision
    wb.ensure_suggestions()
    st.caption(
        "Tick every option a careful researcher could defend. We run every combination and check "
        "whether the answer stays the same. Suggestions come from your data; you decide."
    )
    if not wb.suggested:
        callout(
            "info",
            "No obvious choices to vary in this data.",
            "We found no extreme values, missing answers, other columns to keep equal, or groups "
            "to compare. You can still run the single standard analysis.",
        )
    for d in wb.suggested:
        st.html(
            f'<div style="margin-top:6px"><span class="ms-block-title" style="font-size:14.5px">{esc(d.label)}</span> '
            f'<span class="ms-tech">{esc(TECH.get(d.kind.value, d.kind.value))}</span>'
            f'<div class="ms-muted" style="margin-top:2px">{esc(d.explanation)}</div></div>'
        )
        kp = f"pills_{rev}_{d.id}"
        picked = st.pills(
            d.label,
            [o.id for o in d.options],
            format_func=lambda oid, d=d: d.option(oid).label,
            selection_mode="multi",
            default=[o.id for o in d.options if wb.ticked.get(d.id, {}).get(o.id, True)],
            key=kp,
            label_visibility="collapsed",
            on_change=lambda d=d, kp=kp: wb.set_ticked(d.id, list(st.session_state[kp] or [])),
        )
        if not picked:
            st.html(
                f'<div style="color:{st.session_state["_tokens"]["critical"]};font-size:13px">Tick at least one option.</div>'
            )
    total = wb.n_total()
    formula = wb.formula()
    st.html(
        f'<div style="display:flex;align-items:baseline;gap:10px;margin-top:8px">'
        f'<span style="font-size:22px;font-weight:700" class="tabular">{total:,}</span>'
        f'<span class="ms-secondary">{"analysis" if total == 1 else "analyses"}</span>'
        f"{chip(f'<span class=ms-mono>{esc(formula)}</span>') if formula else ''}</div>"
    )
    kl = f"limit_{rev}"
    limit = st.selectbox(
        "Most analyses to run",
        LIMITS,
        index=LIMITS.index(wb.session.max_specs) if wb.session.max_specs in LIMITS else 2,
        format_func=lambda v: f"{v:,}",
        key=kl,
        help="Above this, we run a random sample. The same repeat-exactly number always gives "
        "the same sample.",
        on_change=lambda: wb.set_limit(int(st.session_state[kl])),
    )
    if total > limit:
        callout(
            "warning",
            f"That's {total:,} analyses, more than the limit of {limit:,}.",
            f"We'll run a random sample of {limit:,}. Untick some options to run them all.",
        )
    empty = wb.empty_choices()
    st.button(
        "Use these choices",
        type="primary",
        key=f"confirm_choices_{rev}",
        on_click=wb.confirm_choices,
        disabled=bool(empty),
        help=f"Tick at least one option in: {', '.join(empty)}." if empty else None,
    )


# ------------------------------------------------------------ fairness editor
def fairness_editor(wb: Workbench) -> None:
    s, rev = wb.session, wb.revision
    t = st.session_state["_tokens"]
    st.caption(
        "Some things are not fair to keep equal, because doing so hides or fakes the effect. "
        "Answer three quick questions for each. Not sure? Say so: we keep it and flag it."
    )
    variables = wb.variables()
    if not variables:
        callout(
            "info",
            "Nothing to check here.",
            "Your plan doesn't keep anything equal or look at sub-groups, so every analysis is fair.",
        )
    questions = [f"Happens before {s.x}?", f"Could {s.x} cause it?", f"Could {s.y} cause it?"]
    for var in variables:
        a = wb.assessment(var)
        kind, word = ROLE_CHIP[a.role] if a else ("warning", "Not answered: kept")
        st.html(
            f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:10px">'
            f'<span class="ms-mono" style="font-size:14px;color:{t["text"]}">{esc(var)}</span>'
            f'<span class="ms-chip" style="background:{t[SOFT[kind]]};color:{t[INK[kind]]}">'
            f"{icon(kind, 13, t[INK[kind]])}{esc(word)}</span></div>"
        )
        for j, q in enumerate(questions):
            kg = f"g_{rev}_{var}_{j}"
            with st.container(horizontal=True, vertical_alignment="center", gap="small"):
                st.html(
                    f'<div class="ms-secondary" style="font-size:14px">{esc(q)}</div>',
                    width="stretch",
                )
                st.segmented_control(
                    q,
                    ANSWER_WORDS,
                    default=wb.answer_word(var, j),
                    key=kg,
                    width="content",
                    label_visibility="collapsed",
                    on_change=lambda var=var, j=j, kg=kg: wb.set_answer(
                        var, j, st.session_state[kg]
                    ),
                )
        a = wb.assessment(var)
        st.html(
            f'<div class="ms-muted">{esc(a.reason if a else "Unanswered items are kept in every analysis.")}</div>'
        )
    with st.expander("Why this matters"):
        st.html(
            f"""<div style="display:grid;gap:12px;font-size:14px;line-height:1.45">
<div><span class="ms-chip good">{icon("good", 13, t["good"])}Common cause: keep equal</span>
<div class="ms-mono" style="margin:4px 0">study time → sleep, and study time → grade</div>
<div class="ms-secondary">It affects both, so it can fake an effect. Keeping it equal makes the comparison fair.</div></div>
<div><span class="ms-chip" style="background:{t["critical_soft"]};color:{t["critical"]}">{icon("critical", 13, t["critical"])}Mediator: don't keep equal</span>
<div class="ms-mono" style="margin:4px 0">sleep → tiredness → grade</div>
<div class="ms-secondary">It's the path the effect travels along. Blocking it hides part of the effect.</div></div>
<div><span class="ms-chip" style="background:{t["critical_soft"]};color:{t["critical"]}">{icon("critical", 13, t["critical"])}Collider: don't keep equal</span>
<div class="ms-mono" style="margin:4px 0">sleep → scholarship ← grade</div>
<div class="ms-secondary">Caused by both. Keeping it equal, or looking at one group of it, creates a fake link.</div></div>
<div class="ms-muted">Based on Cinelli, Forney &amp; Pearl (2022).</div></div>"""
        )
    fair, run_n = wb.fair_count()
    if fair:
        callout(
            "info",
            f"{fair:,} of {run_n:,} analyses are fair.",
            "The verdict uses only these. The others stay visible as hollow dots on the chart."
            if fair < run_n
            else "Every analysis in your plan is fair.",
        )
    else:
        callout(
            "critical",
            f"0 of {run_n:,} analyses are fair.",
            "Nothing would be left to judge. Change some answers or choices.",
        )
    st.button(
        "Use these answers",
        type="primary",
        key=f"confirm_fair_{rev}",
        on_click=wb.confirm_fairness,
        disabled=fair == 0,
        help="You can skip questions: unanswered items are kept.",
    )


# ------------------------------------------------------------------ run section
def run_section(wb: Workbench) -> None:
    s, rev = wb.session, wb.revision
    with st.expander(
        f"Run settings · luck check {s.n_permutations or 'off'}"
        f"{' shuffles' if s.n_permutations else ''} · α {s.alpha:.2f}"
    ):
        perm_labels = list(PERMUTATION_CHOICES)
        kp, ka, ks = f"perm_{rev}", f"alpha_{rev}", f"seed_{rev}"

        def options_changed() -> None:
            wb.set_run_options(
                PERMUTATION_CHOICES[st.session_state[kp]],
                float(st.session_state[ka]),
                int(st.session_state[ks] if st.session_state[ks] is not None else s.seed),
            )

        st.selectbox(
            "Luck check  ·  permutation test",
            perm_labels,
            index=list(PERMUTATION_CHOICES.values()).index(s.n_permutations)
            if s.n_permutations in PERMUTATION_CHOICES.values()
            else 1,
            key=kp,
            help="Shuffles the factor to see how often chance alone gives a pattern this strong.",
            on_change=options_changed,
        )
        st.selectbox(
            "Significance level  ·  alpha",
            ALPHAS,
            index=ALPHAS.index(s.alpha) if s.alpha in ALPHAS else 0,
            format_func=lambda v: f"{v:.2f}",
            key=ka,
            on_change=options_changed,
        )
        st.number_input(
            "Repeat-exactly number  ·  random seed",
            value=int(s.seed),
            step=1,
            format="%d",
            key=ks,
            help="Used by every random step (sampling, luck check). The same number always "
            "gives the same result.",
            on_change=options_changed,
        )
    if s.blind is not None:
        h = s.blind.sha256
        callout(
            "good",
            f"Plan locked {s.blind.locked_at.replace('T', ' ').replace('+00:00', ' UTC')[:20]} UTC",
            f'This fingerprint is saved in every export:<br><span class="ms-mono">'
            f"{' '.join(h[i : i + 8] for i in range(0, 64, 8))}</span>",
            raw=True,
        )
    total = min(wb.n_total(), s.max_specs) if wb.suggested or s.decisions else 1
    verb = "Lock plan and run" if wb.blind_mode else "Run"
    label = f"{verb} {total:,} {'analysis' if total == 1 else 'analyses'}"
    if s.verdict is not None:
        label = "Run again"
    st.button(
        label,
        type="secondary" if s.verdict is not None else "primary",
        width="stretch",
        disabled=not wb.ready_to_run() or wb.running,
        on_click=wb.start_run,
        key="run",
    )
    if wb.running:
        st.caption("Running in the background. You can keep reading the results area.")
    elif not wb.ready_to_run():
        st.caption("Finish the plan above to run it.")
    else:
        st.caption(
            f"Estimated time: about {fmt_time(wb.estimate_seconds())}."
            + (" Locking saves a fingerprint of your plan." if wb.blind_mode else "")
        )


# ====================================================================== evidence
def evidence_pane(wb: Workbench) -> None:
    s = wb.session
    if wb.running or wb.job is not None:
        progress_view(wb)
    elif s.verdict is not None:
        results_view(wb)
    elif wb.df is not None:
        data_overview(wb)
    else:
        welcome()


def welcome() -> None:
    st.html(
        """<div class="ms-empty" style="padding:8px 4px 0">
<h2>Does your finding hold up?</h2>
<p>A result can depend on small choices: which extreme values to drop, what to keep equal,
who to include. Multiverse Studio runs every reasonable combination of those choices and shows
whether the answer stays the same.</p>
<p>Start on the left: load a CSV or Excel file, or try an example with a known answer.
Your data never leaves this computer.</p></div>"""
    )
    with st.container(key="card-welcome"):
        st.html(
            """<div style="font-weight:700;margin-bottom:6px">What you will see here</div>
<ul class="ms-secondary" style="margin:0;padding-left:18px;line-height:1.7">
<li><b>A verdict</b> in one plain sentence, with the numbers behind it.</li>
<li><b>Every analysis, sorted</b> by the effect it found (the specification curve). Click a dot to see its choices.</li>
<li><b>Which choice matters most</b>, and a <b>cherry-pick check</b> for a reported number.</li>
<li><b>A reproducible script</b>, a full report and a locked plan anyone can verify.</li></ul>"""
        )


def data_overview(wb: Workbench) -> None:
    s = wb.session
    st.html(
        f'<div class="ms-empty"><h2>{esc(wb.data_name)}</h2>'
        f"<p>{len(wb.df):,} rows and {wb.df.shape[1]} columns. Here is what each column looks like. "
        "Results appear here after you run the plan"
        f"{' and lock it' if wb.blind_mode else ''}.</p></div>"
    )
    rows = []
    for info in s.profile.columns:
        notes = []
        if info.n_outliers_3sd:
            notes.append(
                f"{info.n_outliers_3sd} extreme value{'s' if info.n_outliers_3sd > 1 else ''}"
            )
        if info.skewness is not None and abs(info.skewness) > 1:
            notes.append("skewed")
        if info.kind is ColumnKind.CATEGORICAL:
            notes.append(f"{info.n_unique} groups")
        rows.append(
            {
                "Column": info.name,
                "Looks like": KIND_NAMES[info.kind],
                "Missing": str(info.n_missing) if info.n_missing else "–",
                "Notes": ", ".join(notes),
            }
        )
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
        **({"height": 460} if len(rows) > 12 else {}),
    )
    if wb.blind_mode:
        callout(
            "info",
            "Blind mode is on.",
            "No result is shown until you lock the plan. Then nobody, not even you, can change "
            "the analysis after peeking.",
        )


@st.fragment(run_every=POLL_SECONDS)
def progress_view(wb: Workbench) -> None:
    """Redrawn on a timer while the background run is going."""
    if wb.job is None or wb.poll():
        st.rerun(scope="app")
    p, s = wb.progress, wb.session
    t = st.session_state["_tokens"]
    with st.container(key="card-progress"):
        if p.stage == "perm":
            head = "Luck check"
            value = p.perm_done / max(p.perm_total, 1)
            text = f"{p.perm_done} of {p.perm_total} shuffles"
            detail = "Shuffling the data to see how often chance alone gives a pattern this strong."
        else:
            head = "Running every analysis"
            value = p.done / max(p.total, 1)
            text = f"{p.done:,} of {p.total:,} analyses"
            detail = f"Analysis: {p.current}" if p.current else "Preparing the analyses…"
        st.html(f'<div style="font-size:19px;font-weight:700">{head}</div>')
        st.progress(min(value, 1.0), text=text)
        st.caption(detail)
        if p.live:
            step = max(10, p.total // 12)
            if (
                p.live_spec is None
                or len(p.live) - p.live_spec_n >= step
                or (len(p.live) == p.total and p.live_spec_n != p.total)
            ):
                p.live_spec = charts.to_spec(
                    charts.live_curve_chart(p.live, alpha=s.alpha, dark=is_dark())
                )
                p.live_spec_n = len(p.live)
            st.vega_lite_chart(p.live_spec, width="stretch", theme=None)
        order = ["lock", "run", "perm", "verdict"]
        now = order.index(p.stage) if p.stage in order else 1
        names = {
            "lock": "Lock the plan",
            "run": "Run every analysis",
            "perm": "Luck check",
            "verdict": "Verdict",
        }
        items = []
        for i, key in enumerate(order):
            if key == "lock" and s.blind is None:
                ico, state = "skip", "skipped"
            elif key == "perm" and not s.n_permutations:
                ico, state = "skip", "skipped"
            elif i < now or key == "lock":
                ico, state = "check", "done"
            elif i == now:
                ico, state = "busy", "working"
            else:
                ico, state = "wait", "waiting"
            ink = {"check": t["good"], "busy": t["accent"]}.get(ico, t["text_muted"])
            items.append(
                f'<li>{icon(ico, 15, ink)}{names[key]}<span class="state">{state}</span></li>'
            )
        st.html(f'<ul class="ms-steps">{"".join(items)}</ul>')
        st.button("Cancel", on_click=wb.cancel, key="cancel")


def results_view(wb: Workbench) -> None:
    s, v = wb.session, wb.session.verdict
    t = st.session_state["_tokens"]
    dark = is_dark()
    kind, word, gloss = VERDICT_WORDS[v.label]
    direction = "positive" if v.median_estimate >= 0 else "negative"
    same = round(v.share_same_sign * v.n_valid)
    if v.permutation_p is None:
        luck = "Not checked"
    else:
        digits = 2 if s.n_permutations <= 100 else 3
        luck = f"{'Unlikely' if v.permutation_p < 0.05 else 'Possible'} (p = {v.permutation_p:.{digits}f})"
    n_sig = round(v.share_significant * v.n_valid)
    unit = UNIT_WORDS[s.family].format(x=s.x, y=s.y)
    chance = (
        ""
        if v.permutation_p is None
        else " A pattern this strong is unlikely to come from chance alone."
        if v.permutation_p < 0.05
        else " Chance alone could produce a pattern like this."
    )
    explain = (
        f"The typical analysis finds {v.median_estimate:+.3g} ({esc(unit)}). "
        f"{same:,} of {v.n_valid:,} point the same way, and {n_sig:,} "
        f"{'is' if n_sig == 1 else 'are'} significant.{chance}"
    )
    st.html(
        f'<div class="ms-callout" role="status" style="background:{t[SOFT[kind]]};padding:16px 18px;display:block">'
        f'<div style="display:flex;align-items:center;gap:8px;color:{t[INK[kind]]};font-weight:700;font-size:16px">'
        f'{icon(kind, 18, t[INK[kind]])}{word}<span style="font-weight:400;font-size:14px;color:{t["text_secondary"]}">· {gloss}</span></div>'
        f'<div style="display:flex;gap:16px;align-items:baseline;margin-top:10px;flex-wrap:wrap">'
        f'<span class="ms-verdict-share">{v.share_significant:.0%}</span>'
        f'<span style="font-size:15px;max-width:62ch">of the {v.n_valid:,} fair analyses find a '
        f"significant {direction} effect of <b>{esc(s.x)}</b> on <b>{esc(s.y)}</b>.</span></div>"
        f'<p style="margin:8px 0 0;max-width:72ch;color:{t["text"]};font-size:14.5px;line-height:1.5">{explain}</p>'
        f'<dl class="ms-facts">'
        f"<div><dt>Typical effect · median</dt><dd>{v.median_estimate:+.3g}</dd></div>"
        f"<div><dt>Point the same way</dt><dd>{same:,} of {v.n_valid:,} ({v.share_same_sign:.0%})</dd></div>"
        f"<div><dt>Could it be luck? · permutation test</dt><dd>{luck}</dd></div>"
        f"<div><dt>Could not be fitted</dt><dd>{v.n_specs - v.n_ok:,}</dd></div></dl></div>"
    )
    bad = [a for a in s.assessments if not a.keep]
    left_out = v.n_ok - v.n_valid
    if bad and left_out:
        names = ", ".join(f"{a.variable} ({a.role.value.replace('_', ' ')})" for a in bad)
        callout(
            "warning",
            f"{left_out:,} analyses left out as unfair.",
            f"They kept {names} equal or grouped by it, which would distort the effect. They're "
            "still shown as hollow dots on the chart.",
        )
    if s.notes.strip():
        callout("warning", "The plan was changed after results were seen.", s.notes.strip())

    # ---------------------------------------------------------------- curve
    pal = palette(dark)
    with st.container(key="card-curve"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html(
                '<div><div style="font-size:17px;font-weight:700">Every analysis, sorted by effect size '
                '<span class="ms-tech">specification curve</span></div>'
                '<div class="ms-muted" style="margin-top:2px">Top: the effect each analysis found '
                f"({esc(UNIT_WORDS[s.family].format(x=s.x, y=s.y))}), with its 95% interval. "
                "Bottom: the choices it used. Click a dot, or type its position below, to see that "
                "analysis.</div></div>",
                width="stretch",
            )
            show_invalid = st.toggle("Show left-out", value=True, key="show_invalid")
        st.html(
            '<div class="ms-legend">'
            f'<span><i class="ms-dot" style="background:{pal.sig_same}"></i>Significant, same direction</span>'
            f'<span><i class="ms-dot" style="background:{pal.sig_opposite}"></i>Significant, opposite</span>'
            f'<span><i class="ms-dot" style="background:{pal.not_significant}"></i>Not significant</span>'
            f'<span><i class="ms-dot" style="border:1.5px solid {pal.not_significant};box-sizing:border-box"></i>'
            "Left out (unfair comparison)</span>"
            + (
                f'<span><i style="width:16px;border-top:2px dashed {pal.reported_line};display:inline-block"></i>'
                "Reported result</span>"
                if s.reported_estimate is not None
                else ""
            )
            + "</div>"
        )
        top, panel = curve_specs(wb, show_invalid, is_dark())
        event = st.vega_lite_chart(
            top,
            width="stretch",
            theme=None,
            on_select="rerun",
            selection_mode=charts.SELECTION,
            key="curve",
        )
        if panel is not None:
            st.vega_lite_chart(panel, width="stretch", theme=None, key="curve_choices")
        picked = (event or {}).get("selection", {}).get(charts.SELECTION) if event else None
        order = charts.curve_frame(s.results, s.decisions, s.alpha, show_invalid)[
            "spec_id"
        ].tolist()
        position = st.number_input(
            "Inspect an analysis by its position on the curve (1 = leftmost)",
            min_value=1,
            max_value=max(len(order), 1),
            value=None,
            step=1,
            placeholder=f"1 to {len(order)}",
            key=f"position_{wb.run_id}_{show_invalid}",
        )
        spec_id = None
        if picked:
            spec_id = int(picked[0]["spec_id"])
        elif position is not None and order:
            spec_id = int(order[int(position) - 1])
        r = wb.result_by_id(spec_id) if spec_id is not None else None
        if r is not None:
            analysis_detail(wb, r)

    # ---------------------------------------------- importance | cherry-pick
    left, right = st.columns(2, gap="medium")
    with left, st.container(key="card-importance"):
        st.html(
            '<div style="font-size:17px;font-weight:700">Which choice matters most?</div>'
            '<div class="ms-muted" style="margin:2px 0 8px">How much each choice moves the effect '
            "(share of the variation it explains, η²).</div>"
        )
        imp = wb.importance()
        if imp:
            bars = "".join(
                f'<div class="ms-bar"><span>{esc(label)}</span><span class="track">'
                f'<span class="fill" style="display:block;width:{max(share, 0.004) * 100:.1f}%"></span></span>'
                f'<span class="val">{share:.0%}</span></div>'
                for label, share in imp
            )
            top_label, top_share = imp[0]
            sentence = (
                f"{top_label} changes the answer most ({top_share:.0%} of the variation)."
                if top_share >= 0.05
                else "No single choice changes the answer much."
            )
            st.html(
                f'{bars}<div class="ms-secondary" style="margin-top:10px;font-size:14px">{esc(sentence)}</div>'
            )
        else:
            st.caption("Your plan has no choices with more than one option.")
    with right, st.container(key="card-cherry"):
        st.html(
            '<div style="font-size:17px;font-weight:700">Cherry-pick check</div>'
            '<div class="ms-muted" style="margin:2px 0 8px">Is a reported result typical, or one of the '
            "best-looking versions?</div>"
        )
        st.number_input(
            "Reported effect",
            value=s.reported_estimate,
            placeholder="e.g. 5.8",
            format="%.4g",
            step=None,
            key=f"reported_{wb.run_id}",
            help="Type a number from a paper, a report or your own first analysis.",
            on_change=lambda: wb.check_cherry(st.session_state[f"reported_{wb.run_id}"]),
        )
        cp = s.cherry_pick
        if cp is not None:
            callout(
                "critical" if cp.flagged else "good",
                "Possibly cherry-picked." if cp.flagged else "Within the typical range.",
                cp.explanation,
            )
            st.caption(f"Percentile among fair analyses: {cp.percentile:.0f}")

    # ---------------------------------------------------- ready-to-use text
    from multiverse_studio.core import api

    with st.container(key="card-text"):
        st.html(
            '<div style="font-size:17px;font-weight:700">Ready-to-use text</div>'
            '<div class="ms-muted" style="margin:2px 0 8px">Written from your results. Use the copy '
            "button on each block to paste it into your report or thesis.</div>"
        )
        tab_m, tab_r = st.tabs(["Methods", "Results"])
        with tab_m:
            st.code(api.methods_paragraph(s), language=None, wrap_lines=True)
        with tab_r:
            st.code(api.results_paragraph(s), language=None, wrap_lines=True)

    save_and_share(wb)


def curve_specs(wb: Workbench, show_invalid: bool, dark: bool) -> tuple[dict, dict | None]:
    """Specs for the curve and the choices panel, cached until the results or view change."""
    s = wb.session
    cache_key = (wb.run_id, len(s.results), show_invalid, s.reported_estimate, dark)
    cached = st.session_state.get("_curve")
    if cached and cached[0] == cache_key:
        return cached[1]
    top = charts.to_spec(
        charts.spec_curve_chart(
            s.results,
            s.decisions,
            alpha=s.alpha,
            show_invalid=show_invalid,
            reported_estimate=s.reported_estimate,
            dark=dark,
            y_label=f"Effect on {s.y}",
        )
    )
    panel = charts.choices_chart(
        s.results, s.decisions, alpha=s.alpha, show_invalid=show_invalid, dark=dark
    )
    specs = (top, charts.to_spec(panel) if panel is not None else None)
    st.session_state["_curve"] = (cache_key, specs)
    return specs


def analysis_detail(wb: Workbench, r) -> None:
    s = wb.session
    lines = [
        f"<b>{esc(d.label)}</b>: {esc(d.option(r.choices[d.id]).label)}"
        for d in s.decisions
        if d.id in r.choices
    ]
    t = st.session_state["_tokens"]
    st.html(
        f'<div style="background:{t["subtle"]};border-radius:10px;padding:12px 14px;font-size:14px;line-height:1.5">'
        f'<div style="font-weight:700">Analysis #{r.spec_id + 1}'
        f"{'' if r.valid else ' · left out: unfair comparison'}</div>"
        f'<div class="ms-secondary">{" · ".join(lines) or "Standard analysis"}</div>'
        f'<div class="tabular" style="margin-top:4px">Effect {r.estimate:+.4g} · 95% interval '
        f"[{r.ci_low:+.4g}, {r.ci_high:+.4g}] · p = {r.p_value:.4f} · n = {r.n_obs:,}</div></div>"
    )
    with st.expander("Code for this analysis"):
        st.code(wb.single_code(r), language="python")


def save_and_share(wb: Workbench) -> None:
    s = wb.session
    stem = wb.file_stem()
    with st.container(key="card-save"):
        st.html(
            '<div style="font-size:17px;font-weight:700">Save &amp; share</div>'
            '<div class="ms-muted" style="margin:2px 0 10px">Everything someone needs to check or repeat '
            "this analysis.</div>"
        )
        items = [
            (
                "Reproducible Python script",
                "Anyone with Python can re-run it and get exactly the same numbers.",
                wb.script_text,
                f"{stem}.py",
                "text/x-python",
                "primary",
            ),
            (
                "Full report (JSON)",
                "Every analysis, the verdict, the locked plan and your software versions.",
                wb.report_text,
                f"{stem}.json",
                "application/json",
                "secondary",
            ),
            (
                "Analysis file",
                "Reopen this analysis later in Multiverse Studio.",
                wb.session_text,
                f"{stem}.msession",
                "application/json",
                "secondary",
            ),
        ]
        for title, desc, make, name, mime, kind in items:
            with st.container(horizontal=True, vertical_alignment="center"):
                st.html(
                    f'<div><b>{esc(title)}</b><div class="ms-muted">{esc(desc)}</div></div>',
                    width="stretch",
                )
                st.download_button(
                    f"Save .{name.rsplit('.', 1)[1]}",
                    data=make,
                    file_name=name,
                    mime=mime,
                    type=kind,
                    key=f"dl_{name}",
                    on_click="ignore",
                )
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html(
                '<div><b>PDF report</b><div class="ms-muted">Not available yet. Use the script or the '
                "JSON report for now.</div></div>",
                width="stretch",
            )
            st.button(
                "Save .pdf",
                disabled=True,
                key="dl_pdf",
                help="PDF export is planned for the next version.",
            )
        st.divider()
        ok = wb.plan_matches()
        if ok is None:
            callout(
                "warning",
                "No locked plan.",
                "Blind mode was off, so there's no fingerprint to verify. Turn it on in Your question "
                "for a verifiable plan.",
            )
        else:
            callout(
                "good" if ok else "critical",
                "The plan matches its fingerprint."
                if ok
                else "The plan no longer matches its fingerprint.",
                f"Locked {esc(s.blind.locked_at.replace('T', ' ').replace('+00:00', ' UTC'))}.<br>"
                f'<span class="ms-mono">{esc(s.blind.sha256)}</span>',
                raw=True,
            )
        st.button(
            "Start a new analysis",
            type="tertiary",
            on_click=wb.start_over,
            key="start_over",
            help="Clears the data and the plan. Your results stay until you do this.",
        )


# ========================================================================= main
def main() -> None:
    st.set_page_config(
        page_title="Multiverse Studio",
        page_icon=":material/scatter_plot:",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            "About": "Multiverse Studio: does your finding survive every reasonable way of "
            "analysing it? Free, offline and open source (MIT).",
        },
    )
    if "text_size" not in st.session_state:
        st.session_state["text_size"] = "100%"
    wb = workbench()
    if wb.job is not None and not wb.running:
        wb.poll()
    dark = is_dark()
    st.session_state["_tokens"] = tokens(dark)
    scale = TEXT_SIZES.get(st.session_state.get("text_size") or "100%", 1.0)
    st.html(f"<style>{css(dark, scale)}</style>")
    top_bar(wb)
    plan_col, evidence_col = st.columns([0.36, 0.64], gap="large")
    with plan_col:
        plan_pane(wb)
    with evidence_col:
        evidence_pane(wb)


if __name__ == "__main__":
    main()

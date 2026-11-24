"""Step 4: causal guardrails, three plain questions per variable."""

from __future__ import annotations

import customtkinter as ctk

from ...core import api
from ...core.guardrails import conditioned_on
from ...core.types import CausalRole, GuardrailAnswers
from ..theme import SPACE, c, font, mono
from ..widgets.common import Badge, Callout, PageHeader, Section, divider, label
from .base import Page

CHOICES = ["Yes", "No", "Not sure"]
TO_BOOL = {"Yes": True, "No": False, "Not sure": None, "": None}
FROM_BOOL = {True: "Yes", False: "No", None: "Not sure"}
ROLE_BADGE = {
    CausalRole.CONFOUNDER: ("good", "Fair to keep equal"),
    CausalRole.NEUTRAL: ("good", "Fair to keep equal"),
    CausalRole.UNKNOWN: ("warning", "Kept, but flagged"),
    CausalRole.MEDIATOR: ("critical", "Unfair: left out"),
    CausalRole.COLLIDER: ("critical", "Unfair: left out"),
    CausalRole.OUTCOME_PROXY: ("critical", "Unfair: left out"),
}


class GuardrailsPage(Page):
    step_id = "guardrails"

    def build(self) -> None:
        self.place(
            PageHeader(
                self,
                "Fair comparisons",
                "Some things are not fair to keep equal, because doing so hides or fakes the effect. "
                "Answer three quick questions for each. Not sure? Say so: we keep it and flag it.",
            ),
            0,
        )
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.grid_columnconfigure(0, weight=1)
        self.table = Section(cols)
        self.table.grid(row=0, column=0, sticky="nsew", padx=(0, SPACE["lg"]))
        self.explain = Section(cols, "Why this matters")
        self.explain.grid(row=0, column=1, sticky="nsew")
        self._explainer(self.explain.body)
        self.place(cols, 1)
        self.summary = ctk.CTkFrame(self, fg_color="transparent")
        self.summary.grid_columnconfigure(0, weight=1)
        self.place(self.summary, 2)
        self.segs: dict[str, list[ctk.CTkSegmentedButton]] = {}
        self.badges: dict[str, Badge] = {}
        self.reasons: dict[str, ctk.CTkLabel] = {}

    def _explainer(self, body) -> None:
        items = [
            (
                "good",
                "Common cause: keep equal",
                "study time → sleep, and study time → grade",
                "It affects both, so it can fake an effect. Keeping it equal makes the comparison fair.",
            ),
            (
                "critical",
                "Mediator: don't keep equal",
                "sleep → tiredness → grade",
                "It's the path the effect travels along. Blocking it hides part of the effect.",
            ),
            (
                "critical",
                "Collider: don't keep equal",
                "sleep → scholarship ← grade",
                "Caused by both. Keeping it equal, or looking at one group of it, creates a fake link.",
            ),
        ]
        for i, (kind, title, path, text) in enumerate(items):
            Badge(body, kind, title).grid(
                row=3 * i, column=0, sticky="w", pady=(0 if i == 0 else SPACE["lg"], 4)
            )
            ctk.CTkLabel(body, text=path, font=mono(11), text_color=c("text"), anchor="w").grid(
                row=3 * i + 1, column=0, sticky="w"
            )
            label(body, text, "small", "text_secondary", wrap=250).grid(
                row=3 * i + 2, column=0, sticky="w"
            )
        label(body, "Based on Cinelli, Forney & Pearl (2022).", "caption", "text_muted").grid(
            row=9, column=0, sticky="w", pady=(SPACE["lg"], 0)
        )

    # ------------------------------------------------------------------ show
    def on_show(self) -> None:
        s = self.app.session
        self.variables = api.variables_to_assess(s.decisions)
        body = self.table.body
        for w in body.winfo_children():
            w.destroy()
        self.segs, self.badges, self.reasons = {}, {}, {}
        if not self.variables:
            Callout(
                body,
                "info",
                "Nothing to check here.",
                "Your plan doesn't keep anything equal or look at sub-groups, so every analysis is fair.",
            ).grid(row=0, column=0, sticky="ew")
            self.render_summary()
            return
        questions = [f"Happens before {s.x}?", f"Could {s.x} cause it?", f"Could {s.y} cause it?"]
        for col in range(3):
            body.grid_columnconfigure(col, weight=1, uniform="q")
        r = 0
        for i, var in enumerate(self.variables):
            if i:
                divider(body).grid(row=r, column=0, columnspan=3, sticky="ew", pady=SPACE["lg"])
                r += 1
            head = ctk.CTkFrame(body, fg_color="transparent")
            head.grid(row=r, column=0, columnspan=3, sticky="ew")
            head.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                head, text=var, font=mono(14), text_color=c("text"), anchor="w", height=1
            ).grid(row=0, column=0, sticky="w")
            self.badges[var] = Badge(head, "warning", "Not answered yet")
            self.badges[var].grid(row=0, column=1, sticky="e")
            r += 1
            ans = s.guardrails.get(var)
            vals = (
                [ans.happens_before_x, ans.could_be_caused_by_x, ans.could_be_caused_by_y]
                if ans
                else [None, None, None]
            )
            self.segs[var] = []
            for j, q in enumerate(questions):
                cell = ctk.CTkFrame(body, fg_color="transparent")
                cell.grid(row=r, column=j, sticky="w", pady=(SPACE["sm"], 0), padx=(0, SPACE["md"]))
                label(cell, q, "small", "text_secondary", wrap=210).pack(anchor="w", pady=(0, 4))
                seg = ctk.CTkSegmentedButton(
                    cell,
                    values=CHOICES,
                    command=lambda _v, v=var: self.on_answer(v),
                    font=font("small"),
                    height=30,
                    selected_color=c("button"),
                    selected_hover_color=c("button_hover"),
                    unselected_color=c("card"),
                    unselected_hover_color=c("subtle"),
                    fg_color=c("border"),
                    text_color=c("text"),
                )
                seg.set(FROM_BOOL[vals[j]] if ans else "")
                seg.pack(anchor="w")
                self.segs[var].append(seg)
            r += 1
            self.reasons[var] = label(body, "", "small", "text_secondary", wrap=640)
            self.reasons[var].grid(row=r, column=0, columnspan=3, sticky="w", pady=(SPACE["sm"], 0))
            r += 1
            self.update_row(var)
        self.render_summary()

    # --------------------------------------------------------------- actions
    def on_answer(self, var: str) -> None:
        self.app.session.guardrails[var] = GuardrailAnswers(
            *(TO_BOOL[seg.get()] for seg in self.segs[var])
        )
        if self.app.guardrails_confirmed:
            self.app.invalidate_plan("guardrails")
        self.update_row(var)
        self.render_summary()

    def update_row(self, var: str) -> None:
        ans = self.app.session.guardrails.get(var)
        if ans is None:
            self.badges[var].set("warning", "Not answered: kept")
            self.reasons[var].configure(text="Unanswered items are kept in every analysis.")
            return
        a = api.assess_control(var, ans)
        kind, text = ROLE_BADGE[a.role]
        self.badges[var].set(kind, text)
        self.reasons[var].configure(text=a.reason)

    def assessments(self):
        s = self.app.session
        return api.assess_controls({v: a for v, a in s.guardrails.items() if v in self.variables})

    def render_summary(self) -> None:
        for w in self.summary.winfo_children():
            w.destroy()
        s = self.app.session
        specs = api.build_specs(s.decisions, max_specs=s.max_specs, seed=s.seed)
        bad = {a.variable for a in self.assessments() if not a.keep}
        fair = sum(not (conditioned_on(sp, s.decisions) & bad) for sp in specs)  # type: ignore[arg-type]
        lead = f"{fair:,} of {len(specs):,} analyses are fair."
        text = (
            "The verdict uses only these. The others stay visible as hollow dots on the results chart."
            if fair < len(specs)
            else "Every analysis in your plan is fair."
        )
        Callout(
            self.summary,
            "info" if fair else "critical",
            lead,
            text if fair else "Nothing would be left to judge. Change some answers or choices.",
        ).grid(row=0, column=0, sticky="ew")
        self.fair_count = fair
        self.refresh_footer()

    def footer(self) -> tuple[str, bool, str]:
        ok = getattr(self, "fair_count", 1) > 0
        return "Next: Run →", ok, "You can skip questions: unanswered items are kept."

    def on_next(self) -> bool:
        self.app.session.assessments = self.assessments()
        self.app.guardrails_confirmed = True
        return True

"""Step 3: tick the defensible options for each analysis choice."""

from __future__ import annotations

import customtkinter as ctk

from ...core import api
from ...core.specs import count_specs
from ...core.types import DecisionKind
from ..theme import SPACE, c, font, mono
from ..widgets.common import Callout, PageHeader, Section, Tag, divider, label
from .base import Page

TECH = {
    DecisionKind.OUTLIERS: "outliers",
    DecisionKind.CONTROLS: "control variables",
    DecisionKind.SUBSET: "subsets",
    DecisionKind.TRANSFORM: "transforms",
    DecisionKind.MISSING: "missing data",
}
LIMITS = ["250", "500", "1000", "2000"]
OPTIONS_PER_ROW = 3


class ChoicesPage(Page):
    step_id = "choices"

    def build(self) -> None:
        self.header = PageHeader(
            self,
            "Analysis choices",
            "Tick every option a careful researcher could defend. We run every combination and "
            "check whether the answer stays the same. Suggestions come from your data; you decide.",
        )
        right = self.header.right
        self.count = ctk.CTkLabel(
            right, text="", font=font("display"), text_color=c("text"), anchor="e"
        )
        self.count.pack(anchor="e")
        self.count_caption = label(right, "analyses", "small", "text_muted")
        self.count_caption.pack(anchor="e")
        self.formula = ctk.CTkLabel(
            right,
            text="",
            font=mono(11),
            text_color=c("text_muted"),
            fg_color=c("subtle"),
            corner_radius=999,
            height=22,
        )
        self.formula.pack(anchor="e", pady=(4, 0))
        self.place(self.header, 0)

        self.list = Section(self)
        self.place(self.list, 1)

        limit = Section(self)
        lb = limit.body
        lb.grid_columnconfigure(0, weight=1)
        left = ctk.CTkFrame(lb, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        label(left, "Most analyses to run", "body_bold").pack(anchor="w")
        label(
            left,
            "Above this, we run a random sample. The same repeat-exactly number always "
            "gives the same sample.",
            "small",
            "text_muted",
            wrap=520,
        ).pack(anchor="w")
        self.limit_menu = ctk.CTkOptionMenu(
            lb,
            values=LIMITS,
            command=lambda _v: self.update_count(),
            width=120,
            font=font("body"),
            fg_color=c("subtle"),
            button_color=c("border"),
            button_hover_color=c("text_muted"),
            text_color=c("text"),
            dropdown_fg_color=c("card"),
            dropdown_text_color=c("text"),
            dropdown_hover_color=c("subtle"),
        )
        self.limit_menu.grid(row=0, column=1, sticky="e")
        self.place(limit, 2)

        self.warn = ctk.CTkFrame(self, fg_color="transparent")
        self.warn.grid_columnconfigure(0, weight=1)
        self.vars: dict[str, dict[str, ctk.BooleanVar]] = {}
        self.row_errors: dict[str, ctk.CTkLabel] = {}

    # ------------------------------------------------------------------ show
    def on_show(self) -> None:
        app, s = self.app, self.app.session
        if not app.suggested:
            app.suggested = api.suggest_decisions(s.profile, s.y, s.x, app.df)
            app.ticked = {d.id: {o.id: True for o in d.options} for d in app.suggested}
        self.limit_menu.set(str(s.max_specs) if str(s.max_specs) in LIMITS else "1000")
        self.render_list()
        self.update_count()

    def render_list(self) -> None:
        body = self.list.body
        for w in body.winfo_children():
            w.destroy()
        self.vars, self.row_errors = {}, {}
        if not self.app.suggested:
            Callout(
                body,
                "info",
                "No obvious choices to vary in this data.",
                "We found no extreme values, missing answers, other columns to keep equal, or "
                "groups to compare. You can still run the single standard analysis.",
            ).grid(row=0, column=0, sticky="ew")
            return
        r = 0
        for i, d in enumerate(self.app.suggested):
            if i:
                divider(body).grid(row=r, column=0, sticky="ew", pady=(SPACE["md"], SPACE["lg"]))
                r += 1
            head = ctk.CTkFrame(body, fg_color="transparent")
            head.grid(row=r, column=0, sticky="ew")
            label(head, d.label, "h2").pack(side="left")
            Tag(head, TECH[d.kind]).pack(side="left", padx=SPACE["sm"])
            r += 1
            label(body, d.explanation, "body", "text_secondary", wrap=700).grid(
                row=r, column=0, sticky="w", pady=(2, SPACE["sm"])
            )
            r += 1
            chips = ctk.CTkFrame(body, fg_color="transparent")
            chips.grid(row=r, column=0, sticky="w")
            r += 1
            self.vars[d.id] = {}
            for j, o in enumerate(d.options):
                var = ctk.BooleanVar(value=self.app.ticked.get(d.id, {}).get(o.id, True))
                self.vars[d.id][o.id] = var
                ctk.CTkCheckBox(
                    chips,
                    text=o.label,
                    variable=var,
                    command=lambda d=d.id: self.on_tick(d),
                    font=font("body"),
                    text_color=c("text"),
                    corner_radius=4,
                    border_width=2,
                    border_color=c("border"),
                    fg_color=c("button"),
                    hover_color=c("button_hover"),
                    checkmark_color=c("text_on_accent"),
                    checkbox_width=18,
                    checkbox_height=18,
                ).grid(
                    row=j // OPTIONS_PER_ROW,
                    column=j % OPTIONS_PER_ROW,
                    sticky="w",
                    padx=(0, SPACE["xl"]),
                    pady=4,
                )
            err = label(body, "Tick at least one option.", "small", "critical")
            err.grid(row=r, column=0, sticky="w")
            err.grid_remove()
            self.row_errors[d.id] = err
            r += 1

    # --------------------------------------------------------------- actions
    def on_tick(self, decision_id: str) -> None:
        self.app.ticked[decision_id] = {k: v.get() for k, v in self.vars[decision_id].items()}
        if self.app.choices_confirmed:
            self.app.invalidate_plan("choices")
        self.update_count()

    def selection_problems(self) -> list[str]:
        bad = []
        for d in self.app.suggested:
            on = any(self.app.ticked.get(d.id, {}).values())
            if d.id in self.row_errors:
                (self.row_errors[d.id].grid_remove if on else self.row_errors[d.id].grid)()
            if not on:
                bad.append(d.label)
        return bad

    def update_count(self) -> None:
        decisions = self.app.selected_decisions()
        n = count_specs(decisions)
        limit = int(self.limit_menu.get())
        self.app.session.max_specs = limit
        self.app.session.sample_if_over = True
        self.count.configure(text=f"{n:,}")
        self.count_caption.configure(text="analysis" if n == 1 else "analyses")
        sizes = [len(d.options) for d in decisions if len(d.options) > 1]
        self.formula.configure(text="  " + " × ".join(map(str, sizes)) + "  " if sizes else "")
        for w in self.warn.winfo_children():
            w.destroy()
        if n > limit:
            Callout(
                self.warn,
                "warning",
                f"That's {n:,} analyses, more than the limit of {limit:,}.",
                f"We'll run a random sample of {limit:,}. Untick some options to run them all.",
            ).grid(row=0, column=0, sticky="ew")
            self.place(self.warn, 3)
        else:
            self.warn.grid_forget()
        self.selection_problems()
        self.refresh_footer()

    def footer(self) -> tuple[str, bool, str]:
        if not hasattr(self, "row_errors"):
            return "Next: Fair comparisons →", False, ""
        bad = [
            d.label for d in self.app.suggested if not any(self.app.ticked.get(d.id, {}).values())
        ]
        if bad:
            return (
                "Next: Fair comparisons →",
                False,
                f"Tick at least one option in: {', '.join(bad)}.",
            )
        return "Next: Fair comparisons →", True, ""

    def on_next(self) -> bool:
        new = self.app.selected_decisions()
        if new != self.app.session.decisions:
            if self.app.choices_confirmed:
                self.app.invalidate_plan("choices")
            self.app.session.decisions = new
        self.app.choices_confirmed = True
        return True

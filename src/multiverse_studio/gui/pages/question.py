"""Step 2: pick the outcome (Y) and the factor (X), and choose blind mode."""

from __future__ import annotations

import customtkinter as ctk

from ...core import api
from ...core.choices import PREDICTOR_KINDS
from ...core.types import ColumnKind
from ..theme import RADIUS, SPACE, c, font
from ..widgets.common import Callout, PageHeader, Section, Tag, label
from .base import Page

MODEL_WORDS = {
    "linear": "is a number, so we'll use linear regression.",
    "logistic": "is a yes / no answer, so we'll use logistic regression.",
    "poisson": "is a count, so we'll use Poisson regression.",
}
OUTCOME_KINDS = (ColumnKind.NUMERIC, ColumnKind.BINARY, ColumnKind.COUNT)
PLACEHOLDER = "Choose a column"


class QuestionPage(Page):
    step_id = "question"

    def build(self) -> None:
        self.place(
            PageHeader(
                self,
                "Your question",
                "Does one thing affect another? Pick what you want to explain and what might affect it.",
            ),
            0,
        )
        sec = Section(self, "Does … affect … ?")
        body = sec.body
        body.grid_columnconfigure(1, weight=1)

        self.y_menu = self._row(body, 0, "What do you want to explain?", "outcome, Y")
        self.x_menu = self._row(body, 1, "What might affect it?", "factor, X")
        self.status = ctk.CTkFrame(body, fg_color="transparent")
        self.status.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(SPACE["md"], 0))
        self.status.grid_columnconfigure(0, weight=1)
        self.place(sec, 1)

        blind = Section(self)
        b = blind.body
        b.grid_columnconfigure(1, weight=1)
        self.blind_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            b,
            text="",
            variable=self.blind_var,
            command=self.on_blind,
            width=46,
            progress_color=c("button"),
            button_color=c("card"),
            button_hover_color=c("subtle"),
            fg_color=c("border"),
        ).grid(row=0, column=0, rowspan=2, sticky="n", padx=(0, SPACE["md"]), pady=2)
        head = ctk.CTkFrame(b, fg_color="transparent")
        head.grid(row=0, column=1, sticky="w")
        label(head, "Blind mode", "h2").pack(side="left")
        Tag(head, "pre-registration").pack(side="left", padx=SPACE["sm"])
        Tag(head, "recommended").pack(side="left")
        label(
            b,
            "You lock your analysis plan before any result is shown. The lock is a digital "
            "fingerprint saved in every export, so anyone can verify the plan wasn't changed after "
            "seeing the results.",
            "body",
            "text_secondary",
            wrap=640,
        ).grid(row=1, column=1, sticky="w", pady=(4, 0))
        self.place(blind, 2)

    def _row(self, body, row: int, text: str, tech: str) -> ctk.CTkOptionMenu:
        left = ctk.CTkFrame(body, fg_color="transparent")
        left.grid(row=row, column=0, sticky="w", pady=SPACE["sm"], padx=(0, SPACE["xl"]))
        label(left, text, "body_bold").pack(anchor="w")
        label(left, tech, "small", "text_muted").pack(anchor="w")
        menu = ctk.CTkOptionMenu(
            body,
            values=[PLACEHOLDER],
            command=lambda _v: self.on_change(),
            width=300,
            height=36,
            font=font("body"),
            dropdown_font=font("body"),
            corner_radius=RADIUS["input"],
            fg_color=c("subtle"),
            button_color=c("border"),
            button_hover_color=c("text_muted"),
            text_color=c("text"),
            dropdown_fg_color=c("card"),
            dropdown_hover_color=c("subtle"),
            dropdown_text_color=c("text"),
        )
        menu.grid(row=row, column=1, sticky="w", pady=SPACE["sm"])
        return menu

    # ------------------------------------------------------------------ show
    def on_show(self) -> None:
        profile = self.app.session.profile
        ys = [col.name for col in profile.columns if col.kind in OUTCOME_KINDS]
        xs = [col.name for col in profile.columns if col.kind in PREDICTOR_KINDS]
        self.y_menu.configure(values=ys or [PLACEHOLDER])
        self.x_menu.configure(values=xs or [PLACEHOLDER])
        s = self.app.session
        self.y_menu.set(s.y if s.y in ys else PLACEHOLDER)
        self.x_menu.set(s.x if s.x in xs else PLACEHOLDER)
        self.blind_var.set(self.app.blind_mode)
        self.render_status()

    def footer(self) -> tuple[str, bool, str]:
        ok = self.app.session.family is not None
        return "Next: Analysis choices →", ok, "" if ok else "Pick both columns to continue."

    # --------------------------------------------------------------- actions
    def on_change(self) -> None:
        s = self.app.session
        y, x = self.y_menu.get(), self.x_menu.get()
        y = None if y == PLACEHOLDER else y
        x = None if x == PLACEHOLDER else x
        if (y, x) != (s.y, s.x):
            self.app.invalidate_plan("question")
            s.y, s.x, s.family = y, x, None
            if y and x:
                try:
                    api.validate_question(s.profile, y, x)
                    s.family = api.suggest_family(s.profile, y)
                except ValueError as exc:
                    self.error = str(exc)
        self.render_status()
        self.refresh_footer()

    def on_blind(self) -> None:
        if self.app.blind_mode != self.blind_var.get():
            self.app.blind_mode = self.blind_var.get()
            self.app.invalidate_plan("run")

    def render_status(self) -> None:
        for w in self.status.winfo_children():
            w.destroy()
        s = self.app.session
        if not (s.y and s.x):
            return
        if s.family is None:
            msg = getattr(self, "error", "This combination can't be analysed.")
            Callout(self.status, "critical", "Pick different columns.", msg).grid(sticky="ew")
            return
        Callout(
            self.status,
            "info",
            f"Question: does {s.x} affect {s.y}?",
            f"{s.y} {MODEL_WORDS[s.family]}",
        ).grid(sticky="ew")

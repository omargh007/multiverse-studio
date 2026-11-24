"""Main window: sidebar wizard + scrollable page area + footer bar.

The app owns the single shared state (``self.session`` plus the loaded
DataFrame). Pages read and write it, and the core library does all analysis.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import replace
from pathlib import Path

import customtkinter as ctk
import pandas as pd

from ..core import api
from ..core.specs import count_specs
from ..core.types import Decision, Session
from .pages.base import Page
from .theme import DEFAULT_WINDOW, MIN_WINDOW, SPACE, STEPS, c
from .widgets.common import ghost_button, label, primary_button, set_enabled
from .widgets.sidebar import Sidebar

log = logging.getLogger(__name__)

DEFAULT_PERMUTATIONS = 100  # keeps a typical run under a minute
TEXT_SCALES = {"100%": 1.0, "115%": 1.15, "130%": 1.3}
STEP_IDS = [s[0] for s in STEPS]


class App(ctk.CTk):
    def __init__(self) -> None:
        ctk.set_appearance_mode("light")
        super().__init__(fg_color=c("bg"))
        self.title("Multiverse Studio")
        w, h = DEFAULT_WINDOW
        self.geometry(f"{w}x{h}")
        self.minsize(*MIN_WINDOW)

        # ---- shared state ----
        self.session = Session(n_permutations=DEFAULT_PERMUTATIONS)
        self.df: pd.DataFrame | None = None
        self.data_name = ""
        self.blind_mode = True
        self.suggested: list[Decision] = []
        self.ticked: dict[str, dict[str, bool]] = {}
        self.choices_confirmed = False
        self.guardrails_confirmed = False
        self.example_scenario: str | None = None
        self.current = 0

        # ---- layout ----
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = Sidebar(
            self, self.go, self.show_examples, self.set_theme, self.set_text_size
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        ctk.CTkFrame(self, width=1, fg_color=c("border"), corner_radius=0).grid(
            row=0, column=0, sticky="nse"
        )

        main = ctk.CTkFrame(self, fg_color=c("bg"), corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)
        self.scroll = ctk.CTkScrollableFrame(
            main,
            fg_color=c("bg"),
            corner_radius=0,
            scrollbar_button_color=c("border"),
            scrollbar_button_hover_color=c("text_muted"),
        )
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        footer = ctk.CTkFrame(main, fg_color=c("card"), corner_radius=0, height=64)
        footer.grid(row=1, column=0, sticky="ew")
        ctk.CTkFrame(footer, height=1, fg_color=c("border"), corner_radius=0).pack(fill="x")
        bar = ctk.CTkFrame(footer, fg_color="transparent")
        bar.pack(fill="x", padx=SPACE["2xl"], pady=SPACE["md"])
        bar.grid_columnconfigure(1, weight=1)
        self.back_btn = ghost_button(bar, "← Back", self.back, width=110)
        self.back_btn.grid(row=0, column=0)
        self.hint = label(bar, "", "small", "text_muted")
        self.hint.grid(row=0, column=1, sticky="w", padx=SPACE["lg"])
        self.next_btn = primary_button(bar, "Next", self.next, width=200)
        self.next_btn.grid(row=0, column=2)

        self.pages: dict[str, Page] = {}
        self._bind_keys()
        self.sidebar.set_seed(self.session.seed)
        self.go(0)

    # ------------------------------------------------------------------ pages
    def page(self, step_id: str) -> Page:
        if step_id not in self.pages:
            from .pages import PAGE_CLASSES

            self.pages[step_id] = PAGE_CLASSES[step_id](self.scroll, self)
        return self.pages[step_id]

    def go(self, index: int) -> None:
        if not self.reachable(index):
            return
        for p in self.pages.values():
            p.grid_forget()
        self.current = index
        page = self.page(STEP_IDS[index])
        page.grid(row=0, column=0, sticky="nsew", padx=SPACE["2xl"], pady=SPACE["xl"])
        page.on_show()
        self.scroll._parent_canvas.yview_moveto(0)
        self.refresh_chrome()

    def next(self) -> None:
        page = self.page(STEP_IDS[self.current])
        _, enabled, _ = page.footer()
        if enabled and page.on_next() and self.current < len(STEPS) - 1:
            self.go(self.current + 1)

    def back(self) -> None:
        if self.current > 0:
            self.go(self.current - 1)

    def show_examples(self) -> None:
        self.go(0)
        self.page("data").focus_examples()

    # --------------------------------------------------------------- progress
    def complete(self, index: int) -> bool:
        s = self.session
        return [
            self.df is not None,
            s.family is not None,
            self.choices_confirmed,
            self.guardrails_confirmed,
            s.verdict is not None,
            s.verdict is not None,
            False,
        ][index]

    def reachable(self, index: int) -> bool:
        return all(self.complete(i) for i in range(index))

    def step_subtitles(self) -> list[str]:
        s = self.session
        subs = [t[2] for t in STEPS]
        if self.df is not None:
            subs[0] = f"{self.data_name} · {len(self.df)} rows"
        if s.x and s.y and s.family:
            subs[1] = f"{s.x} → {s.y}"
        if self.choices_confirmed:
            n = len(s.decisions)
            subs[2] = f"{n} choice{'s' if n != 1 else ''} · {count_specs(s.decisions)} analyses"
        if self.guardrails_confirmed:
            bad = sum(not a.keep for a in s.assessments)
            subs[3] = f"{bad} unfair found" if bad else "All fair"
        if s.blind:
            subs[4] = "Plan locked"
        if s.verdict:
            subs[5] = s.verdict.label.capitalize()
        return subs

    def refresh_chrome(self) -> None:
        statuses = []
        for i in range(len(STEPS)):
            if i == self.current:
                statuses.append("active")
            elif self.complete(i):
                statuses.append("done")
            else:
                statuses.append("todo")
        enabled = [self.reachable(i) for i in range(len(STEPS))]
        self.sidebar.update_steps(statuses, self.step_subtitles(), enabled)
        page = self.page(STEP_IDS[self.current])
        text, ok, hint = page.footer()
        self.next_btn.configure(text=text)
        set_enabled(self.next_btn, ok)
        self.hint.configure(text=hint)
        self.back_btn.configure(state="normal" if self.current > 0 else "disabled")

    # -------------------------------------------------------------- state ops
    def set_data(self, df: pd.DataFrame, name: str, path: str | None) -> None:
        self.df = df
        self.data_name = name
        seed = self.session.seed
        self.session = Session(
            data_path=path,
            profile=api.profile_data(df),
            seed=seed,
            n_permutations=DEFAULT_PERMUTATIONS,
        )
        self.suggested, self.ticked = [], {}
        self.choices_confirmed = self.guardrails_confirmed = False
        self.refresh_chrome()

    def invalidate_plan(self, from_step: str) -> None:
        """A plan input changed: drop everything downstream of ``from_step``.

        If the plan had been locked, the old lock is recorded in the session
        notes, so changing the plan after seeing results is always visible.
        """
        s = self.session
        if s.blind is not None and s.results:
            s.notes += (
                f"Plan sha256 {s.blind.sha256[:16]}... (locked {s.blind.locked_at}) was changed "
                f"at step '{from_step}' after results had been shown.\n"
            )
        s.blind = None
        s.specs, s.results, s.verdict, s.cherry_pick = [], [], None, None
        order = STEP_IDS.index(from_step)
        if order <= STEP_IDS.index("question"):
            self.suggested, self.ticked = [], {}
            self.choices_confirmed = False
            s.decisions = []
        if order <= STEP_IDS.index("choices"):
            self.guardrails_confirmed = False
        self.refresh_chrome()

    def selected_decisions(self) -> list[Decision]:
        """Suggested decisions, keeping only ticked options (at least one each)."""
        out = []
        for d in self.suggested:
            keep = tuple(o for o in d.options if self.ticked.get(d.id, {}).get(o.id, True))
            if keep:
                out.append(replace(d, options=keep))
        return out

    def load_session(self, path: str) -> None:
        from ..io.loaders import load_table
        from ..io.session_store import load_session

        s = load_session(path)
        if not s.data_path or not Path(s.data_path).exists():
            raise ValueError("The data file used by this analysis was not found next to it.")
        df = load_table(s.data_path)
        self.set_data(df, Path(s.data_path).name, s.data_path)
        self.session = s
        self.suggested = list(s.decisions)
        self.ticked = {d.id: {o.id: True for o in d.options} for d in s.decisions}
        self.choices_confirmed = True
        self.guardrails_confirmed = True
        self.blind_mode = s.blind is not None
        self.sidebar.set_seed(s.seed)
        self.refresh_chrome()

    # --------------------------------------------------------------- settings
    def set_theme(self, value: str) -> None:
        ctk.set_appearance_mode(value.lower())
        self.sidebar.draw_logo()
        for p in self.pages.values():
            p.on_theme_change()

    def set_text_size(self, value: str) -> None:
        ctk.set_widget_scaling(TEXT_SCALES.get(value, 1.0))
        for p in self.pages.values():
            p.on_theme_change()

    def _bind_keys(self) -> None:
        for i in range(len(STEPS)):
            self.bind(f"<Control-Key-{i + 1}>", lambda _e, i=i: self.go(i))
        self.bind("<Control-Return>", lambda _e: self.next())
        self.bind("<Alt-Left>", lambda _e: self.back())


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if sys.platform == "win32":  # crisp text on high-DPI Windows screens
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:  # pragma: no cover
            pass
    app = App()
    app.mainloop()


__all__ = ["App", "run"]

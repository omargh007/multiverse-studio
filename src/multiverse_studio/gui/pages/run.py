"""Step 5: review the plan, lock it (blind mode), run everything in the background."""

from __future__ import annotations

import time

import customtkinter as ctk

from ...core import api
from ...core.runner import Cancelled
from ...core.specs import count_specs
from ...plots.spec_curve import spec_curve_figure
from ..theme import RADIUS, SPACE, c, font, mono
from ..widgets.common import (
    Callout,
    KeyValue,
    PageHeader,
    Section,
    ghost_button,
    label,
)
from ..widgets.plot import PlotFrame
from ..worker import Worker
from .base import Page

MODEL_NAMES = {
    "linear": "Linear regression",
    "logistic": "Logistic regression",
    "poisson": "Poisson regression",
}
PERMS = {"Skip": 0, "100 shuffles": 100, "200 shuffles": 200, "500 shuffles": 500}
ALPHAS = ["0.05", "0.01", "0.10"]
SECONDS_PER_FIT = 0.005
LIVE_REDRAW_S = 0.4


def run_task(emit, cancel, df, session, decisions, assessments):
    """Runs in the worker thread. Only uses ``emit``; never touches Tk."""
    specs = api.build_specs(
        decisions, max_specs=session["max_specs"], sample_if_over=True, seed=session["seed"]
    )
    emit(("specs", specs))
    emit(("stage", "run"))
    results = []
    for r in api.iter_multiverse(
        df,
        session["y"],
        session["x"],
        session["family"],
        decisions,
        specs,
        alpha=session["alpha"],
        cancel=cancel,
    ):
        results.append(r)
        emit(("result", r))
    if cancel.is_set():
        raise Cancelled()
    results = api.mark_validity(results, decisions, assessments)
    emit(("validated", results))
    perm_p = None
    if session["n_permutations"]:
        emit(("stage", "perm"))
        perm_p = api.permutation_test(
            df,
            session["y"],
            session["x"],
            session["family"],
            decisions,
            specs,
            results,
            n_permutations=session["n_permutations"],
            alpha=session["alpha"],
            seed=session["seed"],
            progress=lambda i, n: emit(("perm", (i, n))),
            cancel=cancel,
        )
    emit(("stage", "verdict"))
    emit(("verdict", api.summarize(results, alpha=session["alpha"], permutation_p=perm_p)))


class RunPage(Page):
    step_id = "run"

    def build(self) -> None:
        self.worker = Worker(self)
        self.header = PageHeader(self, "Run", "")
        self.place(self.header, 0)
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.grid_columnconfigure((0, 1), weight=1, uniform="run")
        self.plan = Section(
            cols,
            "1. Your plan",
            "Everything that decides the result, written down before any result is shown.",
        )
        self.plan.grid(row=0, column=0, sticky="nsew", padx=(0, SPACE["lg"]))
        self.progress_sec = Section(
            cols,
            "2. Progress",
            "The window stays usable while analyses run. You can cancel any time.",
        )
        self.progress_sec.grid(row=0, column=1, sticky="nsew")
        self.place(cols, 1)

        pb = self.plan.body
        self.blind_box = ctk.CTkFrame(pb, fg_color="transparent")
        self.blind_box.grid(row=0, column=0, sticky="ew")
        self.blind_box.grid_columnconfigure(0, weight=1)
        self.kv = KeyValue(pb)
        self.kv.grid(row=1, column=0, sticky="ew", pady=(SPACE["md"], 0))
        opts = ctk.CTkFrame(pb, fg_color="transparent")
        opts.grid(row=2, column=0, sticky="ew", pady=(SPACE["sm"], 0))
        opts.grid_columnconfigure(1, weight=1)
        self.perm_menu = self._option(
            opts, 0, "Luck check", "permutation test", list(PERMS), self.on_option
        )
        self.alpha_menu = self._option(
            opts, 1, "Significance level", "alpha", ALPHAS, self.on_option
        )
        label(opts, "Repeat-exactly number", "body", "text_secondary").grid(
            row=2, column=0, sticky="w", pady=6
        )
        self.seed_entry = ctk.CTkEntry(
            opts,
            width=140,
            font=mono(12),
            corner_radius=RADIUS["input"],
            border_color=c("border"),
            fg_color=c("card"),
            text_color=c("text"),
        )
        self.seed_entry.grid(row=2, column=1, sticky="e", pady=6)
        self.seed_entry.bind("<FocusOut>", lambda _e: self.on_option())
        self.estimate = label(pb, "", "small", "text_muted", wrap=420)
        self.estimate.grid(row=3, column=0, sticky="w", pady=(SPACE["sm"], 0))
        self.lock_box = ctk.CTkFrame(pb, fg_color="transparent")
        self.lock_box.grid(row=4, column=0, sticky="ew", pady=(SPACE["md"], 0))
        self.lock_box.grid_columnconfigure(0, weight=1)

        rb = self.progress_sec.body
        self.big = ctk.CTkLabel(
            rb, text="Not started", font=font("h1"), text_color=c("text"), anchor="w"
        )
        self.big.grid(row=0, column=0, sticky="w")
        self.bar = ctk.CTkProgressBar(
            rb, height=10, corner_radius=999, progress_color=c("button"), fg_color=c("subtle")
        )
        self.bar.set(0)
        self.bar.grid(row=1, column=0, sticky="ew", pady=(SPACE["sm"], 4))
        self.current = label(
            rb,
            "Your plan is ready. Press the button at the bottom right to start.",
            "small",
            "text_muted",
            wrap=440,
        )
        self.current.grid(row=2, column=0, sticky="w")
        self.live = PlotFrame(rb, height=150)
        self.live.grid(row=3, column=0, sticky="ew", pady=(SPACE["md"], 0))
        self.live.grid_remove()
        self.tasks = ctk.CTkFrame(rb, fg_color="transparent")
        self.tasks.grid(row=4, column=0, sticky="ew", pady=(SPACE["md"], 0))
        self.tasks.grid_columnconfigure(1, weight=1)
        self.task_rows = {}
        for i, (key, text) in enumerate(
            [
                ("lock", "Lock the plan"),
                ("run", "Run every analysis"),
                ("perm", "Luck check"),
                ("verdict", "Verdict"),
            ]
        ):
            icon = label(self.tasks, "○", "body", "text_muted")
            icon.grid(row=i, column=0, padx=(0, SPACE["sm"]), pady=3)
            label(self.tasks, text, "body").grid(row=i, column=1, sticky="w")
            st = label(self.tasks, "waiting", "small", "text_muted")
            st.grid(row=i, column=2, sticky="e")
            self.task_rows[key] = (icon, st)
        self.cancel_btn = ghost_button(rb, "Cancel", self.cancel, width=100)
        self.result_msg = ctk.CTkFrame(rb, fg_color="transparent")
        self.result_msg.grid_columnconfigure(0, weight=1)
        self.results_live = []
        self._last_draw = 0.0

    def _option(self, master, row, text, tech, values, command):
        left = ctk.CTkFrame(master, fg_color="transparent")
        left.grid(row=row, column=0, sticky="w", pady=6)
        label(left, text, "body", "text_secondary").pack(side="left")
        ctk.CTkLabel(
            left,
            text=tech,
            font=font("caption"),
            fg_color=c("subtle"),
            corner_radius=999,
            text_color=c("text_muted"),
            height=20,
        ).pack(side="left", padx=SPACE["sm"])
        menu = ctk.CTkOptionMenu(
            master,
            values=values,
            command=lambda _v: command(),
            width=140,
            font=font("body"),
            fg_color=c("subtle"),
            button_color=c("border"),
            button_hover_color=c("text_muted"),
            text_color=c("text"),
            dropdown_fg_color=c("card"),
            dropdown_text_color=c("text"),
            dropdown_hover_color=c("subtle"),
        )
        menu.grid(row=row, column=1, sticky="e", pady=6)
        return menu

    # ------------------------------------------------------------------ show
    def on_show(self) -> None:
        s = self.app.session
        blind = self.app.blind_mode
        self.header.subtitle.configure(
            text="Lock your plan first, then see the results. Nobody, not even you, can change the "
            "analysis after peeking."
            if blind
            else "Run every analysis in your plan."
        )
        if s.n_permutations not in PERMS.values():
            s.n_permutations = 100
        self.perm_menu.set(next(k for k, v in PERMS.items() if v == s.n_permutations))
        self.alpha_menu.set(f"{s.alpha:.2f}" if f"{s.alpha:.2f}" in ALPHAS else "0.05")
        self.seed_entry.delete(0, "end")
        self.seed_entry.insert(0, str(s.seed))
        self.render_plan()
        if s.verdict is not None and not self.worker.running:
            self.show_finished()

    def render_plan(self) -> None:
        s, app = self.app.session, self.app
        for w in self.blind_box.winfo_children():
            w.destroy()
        if app.blind_mode:
            Callout(
                self.blind_box,
                "info",
                "Blind mode is on.",
                "No result is shown until you lock this plan.",
            ).grid(sticky="ew")
        else:
            Callout(
                self.blind_box,
                "warning",
                "Blind mode is off.",
                "Results will show straight away. Turn it on in step 2 for a verifiable plan.",
            ).grid(sticky="ew")
        total = count_specs(s.decisions)
        run_n = min(total, s.max_specs)
        bad = [a for a in s.assessments if not a.keep]
        self.kv.clear()
        self.kv.add("Question", f"Does {s.x} affect {s.y}?")
        self.kv.add("Model", MODEL_NAMES[s.family])
        self.kv.add(
            "Choices",
            f"{len(s.decisions)} → {run_n:,} analyses"
            + (f" (sample of {total:,})" if total > run_n else ""),
        )
        self.kv.add(
            "Fair comparisons",
            ", ".join(a.variable for a in bad) + " left out" if bad else "All kept",
        )
        fit_s = run_n * SECONDS_PER_FIT * (1 + s.n_permutations)
        self.estimate.configure(text=f"Estimated time: about {self._fmt_time(fit_s)}.")
        self.render_lock()
        self.refresh_footer()

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        if seconds < 60:
            return f"{max(1, round(seconds))} seconds"
        return f"{round(seconds / 60)} minute{'s' if round(seconds / 60) != 1 else ''}"

    def render_lock(self) -> None:
        for w in self.lock_box.winfo_children():
            w.destroy()
        lock = self.app.session.blind
        if lock is None:
            return
        box = ctk.CTkFrame(self.lock_box, fg_color=c("good_soft"), corner_radius=10)
        box.grid(row=0, column=0, sticky="ew")
        label(
            box,
            f"Plan locked {lock.locked_at.replace('T', ' ').replace('+00:00', ' UTC')}",
            "body_bold",
            "good",
        ).pack(anchor="w", padx=SPACE["md"], pady=(SPACE["md"], 0))
        label(box, "This fingerprint is saved in every export:", "small", "text_secondary").pack(
            anchor="w", padx=SPACE["md"]
        )
        h = lock.sha256
        first = " ".join(h[i : i + 8] for i in range(0, 32, 8))
        second = " ".join(h[i : i + 8] for i in range(32, 64, 8))
        ctk.CTkLabel(
            box,
            text=f"{first}\n{second}",
            font=mono(11),
            text_color=c("text"),
            anchor="w",
            justify="left",
        ).pack(anchor="w", padx=SPACE["md"], pady=(2, SPACE["md"]))

    # --------------------------------------------------------------- options
    def on_option(self) -> None:
        s = self.app.session
        try:
            seed = int(self.seed_entry.get().strip())
        except ValueError:
            seed = s.seed
            self.seed_entry.delete(0, "end")
            self.seed_entry.insert(0, str(seed))
        new = (PERMS[self.perm_menu.get()], float(self.alpha_menu.get()), seed)
        if new != (s.n_permutations, s.alpha, s.seed):
            self.app.invalidate_plan("run")
            s.n_permutations, s.alpha, s.seed = new
            self.app.sidebar.set_seed(seed)
            self.reset_progress()
        self.render_plan()

    # ------------------------------------------------------------------- run
    def footer(self) -> tuple[str, bool, str]:
        s = self.app.session
        if self.worker.running:
            return "Running…", False, "You can keep using the app."
        if s.verdict is not None:
            return "See results →", True, "Done. Everything here is reproducible."
        if self.app.blind_mode:
            return "Lock plan and run", True, "Locking saves a fingerprint of your plan."
        return "Run analyses", True, ""

    def on_next(self) -> bool:
        if self.app.session.verdict is not None:
            return True
        self.start()
        return False

    def start(self) -> None:
        app, s = self.app, self.app.session
        self.reset_progress()
        if app.blind_mode:
            if s.blind is None or not api.verify_plan(s, s.blind):
                s.blind = api.lock_plan(s)
            self.set_task("lock", "done", "0.1 s")
        else:
            self.set_task("lock", "skip", "skipped")
        self.render_lock()
        self.results_live = []
        self.cancel_btn.grid(row=5, column=0, sticky="w", pady=(SPACE["md"], 0))
        params = {
            "max_specs": s.max_specs,
            "seed": s.seed,
            "y": s.y,
            "x": s.x,
            "family": s.family,
            "alpha": s.alpha,
            "n_permutations": s.n_permutations,
        }
        self.worker.start(
            run_task, self.on_message, app.df, params, list(s.decisions), list(s.assessments)
        )
        self.refresh_footer()

    def cancel(self) -> None:
        self.worker.cancel()
        self.current.configure(text="Cancelling…")

    def reset_progress(self) -> None:
        self.bar.set(0)
        self.big.configure(text="Not started")
        self.current.configure(
            text="Your plan is ready. Press the button at the bottom right to start."
        )
        for key in self.task_rows:
            self.set_task(key, "wait", "waiting")
        for w in self.result_msg.winfo_children():
            w.destroy()
        self.result_msg.grid_forget()
        self.live.grid_remove()

    def set_task(self, key: str, state: str, text: str) -> None:
        icon, st = self.task_rows[key]
        sym, color = {
            "wait": ("○", "text_muted"),
            "busy": ("◔", "accent"),
            "done": ("✓", "good"),
            "skip": ("–", "text_muted"),
            "fail": ("✕", "critical"),
        }[state]
        icon.configure(text=sym, text_color=c(color))
        st.configure(text=text)

    def on_message(self, kind: str, payload) -> None:
        s = self.app.session
        if kind == "specs":
            self.total = len(payload)
            s.specs = payload
            self.set_task("run", "busy", f"0 / {self.total}")
            self.set_task(
                "perm",
                "wait" if s.n_permutations else "skip",
                "waiting" if s.n_permutations else "skipped",
            )
        elif kind == "result":
            self.results_live.append(payload)
            n = len(self.results_live)
            self.bar.set(n / max(self.total, 1))
            self.big.configure(text=f"{n:,} of {self.total:,} analyses")
            self.current.configure(text="Analysis " + " · ".join(self._choice_labels(payload)))
            self.set_task("run", "busy", f"{n} / {self.total}")
            now = time.monotonic()
            if now - self._last_draw > LIVE_REDRAW_S or n == self.total:
                self._last_draw = now
                self.draw_live()
        elif kind == "validated":
            s.results = payload
            self.set_task("run", "done", f"{len(payload)} / {self.total}")
            self.draw_live()
        elif kind == "stage" and payload == "perm":
            self.set_task("perm", "busy", "starting")
            self.big.configure(text="Luck check")
            self.current.configure(
                text="Shuffling the data to see how often chance alone gives a pattern this strong."
            )
            self.bar.set(0)
        elif kind == "perm":
            i, n = payload
            self.bar.set(i / n)
            self.set_task("perm", "busy", f"{i} / {n}")
        elif kind == "stage" and payload == "verdict":
            if s.n_permutations:
                self.set_task("perm", "done", f"{s.n_permutations} shuffles")
            self.set_task("verdict", "busy", "working")
        elif kind == "verdict":
            s.verdict = payload
            self.set_task("verdict", "done", payload.label)
        elif kind == "done":
            self.cancel_btn.grid_forget()
            self.show_finished()
        elif kind == "cancelled":
            self.cancel_btn.grid_forget()
            s.specs, s.results, s.verdict = [], [], None
            self.reset_progress()
            self.message(
                "warning",
                "Cancelled. Nothing was saved.",
                "Your locked plan is kept, so you can run it again.",
            )
        elif kind == "error":
            self.cancel_btn.grid_forget()
            for key, (icon, _st) in self.task_rows.items():
                if icon.cget("text") == "◔":
                    self.set_task(key, "fail", "failed")
            self.message("critical", "The analysis stopped.", payload)
        self.app.refresh_chrome()

    def _choice_labels(self, r) -> list[str]:
        out = []
        for d in self.app.session.decisions:
            if d.id in r.choices and len(d.options) > 1:
                out.append(d.option(r.choices[d.id]).label)
        return out or ["standard analysis"]

    def draw_live(self) -> None:
        self.live.grid()
        dark = ctk.get_appearance_mode() == "Dark"
        results = self.app.session.results or self.results_live
        self.live.show(
            spec_curve_figure(
                results, [], indicators=False, dark=dark, y_label="", figsize=(5, 1.5)
            )
        )

    def show_finished(self) -> None:
        s = self.app.session
        if s.verdict is None:
            return
        self.bar.set(1)
        self.big.configure(text="Finished")
        self.current.configure(
            text=f"{len(s.results):,} analyses · {s.verdict.n_valid:,} fair · "
            f"verdict: {s.verdict.label}"
        )
        for key in ("run", "verdict"):
            self.set_task(key, "done", "done")
        if s.blind:
            self.set_task("lock", "done", "done")
        self.draw_live()

    def message(self, kind, lead, text) -> None:
        for w in self.result_msg.winfo_children():
            w.destroy()
        Callout(self.result_msg, kind, lead, text, wrap=420).grid(row=0, column=0, sticky="ew")
        self.result_msg.grid(
            row=6, column=0, sticky="ew", pady=(SPACE["md"], 0), in_=self.progress_sec.body
        )

    def on_theme_change(self) -> None:
        if self.results_live or self.app.session.results:
            self.draw_live()

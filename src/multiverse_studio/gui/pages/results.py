"""Step 6: verdict, cherry-pick check, specification curve, what matters, ready text."""

from __future__ import annotations

import customtkinter as ctk

from ...core import api
from ...core.serialize import decision_to_dict
from ...plots.importance import importance_figure
from ...plots.spec_curve import spec_curve_figure
from ..theme import RADIUS, SPACE, c, font, mono
from ..widgets.common import (
    Badge,
    Callout,
    PageHeader,
    Section,
    Tag,
    autowrap,
    copy_to_clipboard,
    ghost_button,
    label,
)
from ..widgets.plot import PlotFrame
from .base import Page

LABELS = {
    "consistent": ("good", "Consistent"),
    "mixed": ("warning", "Depends on choices"),
    "fragile": ("critical", "Fragile"),
}


class ResultsPage(Page):
    step_id = "results"

    def build(self) -> None:
        self.header = PageHeader(self, "Results", "")
        self.lock_chip = ctk.CTkLabel(
            self.header.right,
            text="",
            font=mono(11),
            corner_radius=999,
            fg_color=c("good_soft"),
            text_color=c("good"),
            height=26,
        )
        self.place(self.header, 0)
        self.empty = ctk.CTkFrame(self, fg_color="transparent")
        self.empty.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid_columnconfigure(0, weight=3, uniform="top")
        top.grid_columnconfigure(1, weight=2, uniform="top")
        self.verdict = Section(top, "Verdict")
        self.verdict.grid(row=0, column=0, sticky="nsew", padx=(0, SPACE["lg"]))
        self.cherry = Section(
            top,
            "Cherry-pick check",
            "Is a reported result typical, or one of the best-looking versions?",
        )
        self.cherry.grid(row=0, column=1, sticky="nsew")
        self.top = top
        self._build_cherry()

        self.curve = Section(
            self,
            "Every analysis, sorted by effect size",
            "Top: the effect each analysis found, with its 95% interval. Bottom: the "
            "choices it used. Click a dot to see that analysis.",
        )
        cb = self.curve.body
        legend = ctk.CTkFrame(cb, fg_color="transparent")
        legend.grid(row=0, column=0, sticky="ew", pady=(0, SPACE["sm"]))
        self.legend_items = []
        for key, text in (
            ("sig_same", "Significant, same direction"),
            ("sig_opp", "Significant, opposite"),
            ("ns", "Not significant"),
            ("hollow", "Left out (unfair comparison)"),
        ):
            dot = ctk.CTkLabel(legend, text="○" if key == "hollow" else "●", font=font("body"))
            dot.pack(side="left")
            label(legend, text, "small", "text_secondary").pack(side="left", padx=(4, SPACE["lg"]))
            self.legend_items.append((key, dot))
        self.show_invalid = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            legend,
            text="Show left-out",
            variable=self.show_invalid,
            command=self.draw_curve,
            font=font("small"),
            text_color=c("text_secondary"),
            progress_color=c("button"),
            fg_color=c("border"),
            button_color=c("card"),
            button_hover_color=c("subtle"),
            width=40,
        ).pack(side="right")
        self.curve_plot = PlotFrame(cb, height=520)
        self.curve_plot.grid(row=1, column=0, sticky="ew")
        self.detail = ctk.CTkFrame(cb, fg_color=c("subtle"), corner_radius=10)
        self.detail.grid_columnconfigure(0, weight=1)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid_columnconfigure((0, 1), weight=1, uniform="bot")
        self.importance = Section(
            bottom,
            "Which choice matters most?",
            "How much each choice moves the effect (share of the variation it explains).",
        )
        self.importance.grid(row=0, column=0, sticky="nsew", padx=(0, SPACE["lg"]))
        self.imp_plot = PlotFrame(self.importance.body, height=170)
        self.imp_plot.grid(row=0, column=0, sticky="ew")
        self.imp_text = label(self.importance.body, "", "body", "text_secondary", wrap=440)
        self.imp_text.grid(row=1, column=0, sticky="w", pady=(SPACE["sm"], 0))
        self.text = Section(
            bottom,
            "Ready-to-use text",
            "Written from your results. Paste it into your report or thesis.",
        )
        self.text.grid(row=0, column=1, sticky="nsew")
        self.textbox = ctk.CTkTextbox(
            self.text.body,
            height=210,
            wrap="word",
            font=font("body"),
            fg_color=c("subtle"),
            text_color=c("text"),
            corner_radius=10,
            border_width=0,
        )
        self.textbox.grid(row=0, column=0, sticky="ew")
        btns = ctk.CTkFrame(self.text.body, fg_color="transparent")
        btns.grid(row=1, column=0, sticky="w", pady=(SPACE["sm"], 0))
        ghost_button(btns, "Copy all", lambda: self.copy("all"), width=90).pack(side="left")
        ghost_button(btns, "Copy methods", lambda: self.copy("methods"), width=120).pack(
            side="left", padx=SPACE["sm"]
        )
        ghost_button(btns, "Copy results", lambda: self.copy("results"), width=110).pack(
            side="left"
        )
        self.copied = label(btns, "", "small", "good")
        self.copied.pack(side="left", padx=SPACE["md"])
        self.bottom = bottom

    def _build_cherry(self) -> None:
        b = self.cherry.body
        row = ctk.CTkFrame(b, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew")
        row.grid_columnconfigure(1, weight=1)
        label(row, "Reported effect", "body", "text_secondary").grid(
            row=0, column=0, padx=(0, SPACE["sm"])
        )
        self.cherry_entry = ctk.CTkEntry(
            row,
            placeholder_text="e.g. 5.8",
            font=mono(13),
            height=36,
            corner_radius=RADIUS["input"],
            border_color=c("border"),
            fg_color=c("card"),
            text_color=c("text"),
        )
        self.cherry_entry.grid(row=0, column=1, sticky="ew")
        self.cherry_entry.bind("<Return>", lambda _e: self.check_cherry())
        ghost_button(row, "Check", self.check_cherry, width=80).grid(
            row=0, column=2, padx=(SPACE["sm"], 0)
        )
        self.cherry_out = ctk.CTkFrame(b, fg_color="transparent")
        self.cherry_out.grid(row=1, column=0, sticky="ew", pady=(SPACE["md"], 0))
        self.cherry_out.grid_columnconfigure(0, weight=1)
        label(
            self.cherry_out,
            "Type a number from a paper, a report or your own first analysis.",
            "small",
            "text_muted",
            wrap=320,
        ).grid(sticky="w")

    # ------------------------------------------------------------------ show
    def on_show(self) -> None:
        s = self.app.session
        n_fair = s.verdict.n_valid if s.verdict else 0
        self.header.subtitle.configure(
            text=f"Does {s.x} affect {s.y}? · {len(s.results):,} analyses run · {n_fair:,} fair"
        )
        if s.blind:
            self.lock_chip.configure(
                text=f"  Plan locked · sha256 {s.blind.sha256[:8]}…{s.blind.sha256[-4:]}  "
            )
            self.lock_chip.pack(anchor="e")
        else:
            self.lock_chip.pack_forget()
        if s.verdict is None:
            self.show_empty()
            return
        self.empty.grid_forget()
        self.place(self.top, 1)
        self.place(self.curve, 2)
        self.place(self.bottom, 3)
        self.render_verdict()
        self.render_cherry()
        self.draw_all()
        self.render_text()

    def show_empty(self) -> None:
        for w in self.empty.winfo_children():
            w.destroy()
        s = self.app.session
        errors = [r.error for r in s.results if r.error][:3]
        if errors:
            Callout(
                self.empty,
                "critical",
                "None of the analyses could be used.",
                "Examples: " + " | ".join(errors),
            ).grid(sticky="ew")
        else:
            Callout(self.empty, "info", "No results yet.", "Run your plan in step 5.").grid(
                sticky="ew"
            )
        for w in (self.top, self.curve, self.bottom):
            w.grid_forget()
        self.place(self.empty, 1)

    def render_verdict(self) -> None:
        s, v = self.app.session, self.app.session.verdict
        b = self.verdict.body
        for w in b.winfo_children():
            w.destroy()
        b.grid_columnconfigure(0, weight=1)
        kind, text = LABELS[v.label]

        head = ctk.CTkFrame(b, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew")
        head.grid_columnconfigure(1, weight=1)
        Badge(head, kind, text).grid(row=0, column=0, columnspan=2, sticky="w")
        ctk.CTkLabel(
            head,
            text=f"{v.share_significant:.0%}",
            font=font("display"),
            text_color=c("text"),
            anchor="w",
            height=1,
        ).grid(row=1, column=0, sticky="w", pady=(SPACE["md"], 0), padx=(0, SPACE["md"]))
        word = "positive" if v.median_estimate >= 0 else "negative"
        autowrap(
            label(
                head,
                f"of the {v.n_valid:,} fair analyses find a significant {word} effect "
                f"of {s.x} on {s.y}.",
                "body",
                "text_secondary",
                wrap=380,
            ),
            pad=110,
        ).grid(row=1, column=1, sticky="w", pady=(SPACE["md"], 0))

        grid = ctk.CTkFrame(b, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="ew", pady=(SPACE["lg"], 0))
        grid.grid_columnconfigure((0, 1), weight=1, uniform="st")
        luck = (
            "Not checked"
            if v.permutation_p is None
            else f"{'Unlikely' if v.permutation_p < 0.05 else 'Possible'} (p = {v.permutation_p:.3f})"
        )
        same = round(v.share_same_sign * v.n_valid)
        stats = [
            ("Typical effect", "median", f"{v.median_estimate:+.3g}"),
            ("Point the same way", None, f"{same} of {v.n_valid} ({v.share_same_sign:.0%})"),
            ("Could it be luck?", "permutation test", luck),
            ("Could not be fitted", None, f"{v.n_specs - v.n_ok}"),
        ]
        for i, (k, tech, val) in enumerate(stats):
            cell = ctk.CTkFrame(
                grid,
                fg_color="transparent",
                border_width=1,
                border_color=c("border"),
                corner_radius=10,
            )
            cell.grid(
                row=i // 2,
                column=i % 2,
                sticky="nsew",
                padx=(0, SPACE["sm"] if i % 2 == 0 else 0),
                pady=(0, SPACE["sm"]),
            )
            key = ctk.CTkFrame(cell, fg_color="transparent")
            key.pack(anchor="w", padx=SPACE["md"], pady=(SPACE["sm"], 0))
            label(key, k, "small", "text_muted").pack(side="left")
            if tech:
                Tag(key, tech).pack(side="left", padx=(SPACE["xs"], 0))
            label(cell, val, "body_bold").pack(anchor="w", padx=SPACE["md"], pady=(2, SPACE["sm"]))

        bad = [a for a in s.assessments if not a.keep]
        left_out = v.n_ok - v.n_valid
        if bad and left_out:
            names = ", ".join(f"{a.variable} ({a.role.value})" for a in bad)
            Callout(
                b,
                "warning",
                f"{left_out:,} analyses left out as unfair.",
                f"They kept {names} equal or grouped by it, which would distort the effect. "
                "They're still shown as hollow dots on the chart.",
            ).grid(row=2, column=0, sticky="ew", pady=(SPACE["sm"], 0))

    def check_cherry(self) -> None:
        s = self.app.session
        raw = self.cherry_entry.get().strip().replace(",", ".")
        try:
            s.reported_estimate = float(raw)
        except ValueError:
            s.reported_estimate, s.cherry_pick = None, None
            self.render_cherry(error="Type a number, for example 5.8 or -0.3.")
            return
        s.cherry_pick = api.cherry_pick_check(s.results, s.reported_estimate)
        self.render_cherry()
        self.draw_curve()
        self.render_text()

    def render_cherry(self, error: str | None = None) -> None:
        out = self.cherry_out
        for w in out.winfo_children():
            w.destroy()
        cp = self.app.session.cherry_pick
        if error:
            Callout(out, "critical", error, wrap=300).grid(sticky="ew")
        elif cp is None:
            label(
                out,
                "Type a number from a paper, a report or your own first analysis.",
                "small",
                "text_muted",
                wrap=320,
            ).grid(sticky="w")
        else:
            kind = "critical" if cp.flagged else "good"
            lead = "Possibly cherry-picked." if cp.flagged else "Within the typical range."
            Callout(out, kind, lead, cp.explanation, wrap=300).grid(sticky="ew")
            label(
                out, f"Percentile among fair analyses: {cp.percentile:.0f}", "small", "text_muted"
            ).grid(sticky="w", pady=(SPACE["sm"], 0))

    # ----------------------------------------------------------------- plots
    def dark(self) -> bool:
        return ctk.get_appearance_mode() == "Dark"

    def draw_all(self) -> None:
        self.draw_curve()
        s = self.app.session
        imp = api.decision_importance(s.results, s.decisions)
        labels = {d.id: d.label for d in s.decisions}
        multi = {
            k: v
            for k, v in imp.items()
            if len(next(d for d in s.decisions if d.id == k).options) > 1
        }
        self.imp_plot.show(
            importance_figure(
                multi, labels, dark=self.dark(), figsize=(4.6, max(1.2, 0.42 * len(multi) + 0.3))
            )
        )
        if multi:
            top, share = next(iter(multi.items()))
            self.imp_text.configure(
                text=f"{labels[top]} changes the answer most ({share:.0%} of the variation)."
                if share >= 0.05
                else "No single choice changes the answer much."
            )
        else:
            self.imp_text.configure(text="Your plan has no choices with more than one option.")
        from ...plots.palette import palette

        pal = palette(self.dark())
        colors = {
            "sig_same": pal.sig_same,
            "sig_opp": pal.sig_opposite,
            "ns": pal.not_significant,
            "hollow": pal.not_significant,
        }
        for key, dot in self.legend_items:
            dot.configure(text_color=colors[key])

    def draw_curve(self) -> None:
        s = self.app.session
        fig = spec_curve_figure(
            s.results,
            s.decisions,
            alpha=s.alpha,
            show_invalid=self.show_invalid.get(),
            reported_estimate=s.reported_estimate,
            dark=self.dark(),
            y_label=f"Effect on {s.y}",
        )
        self._order = fig.ms_spec_order
        self.curve_plot.show(fig, on_click=self.on_click)

    def on_click(self, event) -> None:
        if event.xdata is None or not self._order:
            return
        idx = int(round(event.xdata))
        if 0 <= idx < len(self._order):
            spec_id = self._order[idx]
            r = next(r for r in self.app.session.results if r.spec_id == spec_id)
            self.show_detail(r)

    def show_detail(self, r) -> None:
        s = self.app.session
        d = self.detail
        for w in d.winfo_children():
            w.destroy()
        label(
            d,
            f"Analysis #{r.spec_id + 1}" + ("" if r.valid else "  (left out: unfair comparison)"),
            "body_bold",
        ).grid(row=0, column=0, sticky="w", padx=SPACE["md"], pady=(SPACE["md"], 4))
        lines = [
            f"{dec.label}: {dec.option(r.choices[dec.id]).label}"
            for dec in s.decisions
            if dec.id in r.choices
        ]
        label(
            d, "   ·   ".join(lines) or "Standard analysis", "small", "text_secondary", wrap=760
        ).grid(row=1, column=0, sticky="w", padx=SPACE["md"])
        label(
            d,
            f"Effect {r.estimate:+.4g}   95% interval [{r.ci_low:+.4g}, {r.ci_high:+.4g}]   "
            f"p = {r.p_value:.4f}   n = {r.n_obs}",
            "body",
        ).grid(row=2, column=0, sticky="w", padx=SPACE["md"], pady=4)
        code = self.single_code(r)
        ghost_button(d, "Copy code for this analysis", lambda: copy_to_clipboard(self, code)).grid(
            row=3, column=0, sticky="w", padx=SPACE["md"], pady=(0, SPACE["md"])
        )
        d.grid(row=2, column=0, sticky="ew", pady=(SPACE["md"], 0))

    def single_code(self, r) -> str:
        s = self.app.session
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

    # ------------------------------------------------------------------ text
    def render_text(self) -> None:
        s = self.app.session
        self._methods = api.methods_paragraph(s)
        self._results = api.results_paragraph(s)
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", self._methods + "\n\n" + self._results)
        self.textbox.configure(state="disabled")

    def copy(self, which: str) -> None:
        text = {
            "all": self._methods + "\n\n" + self._results,
            "methods": self._methods,
            "results": self._results,
        }[which]
        copy_to_clipboard(self, text)
        self.copied.configure(text="Copied")
        self.after(1800, lambda: self.copied.configure(text=""))

    def footer(self) -> tuple[str, bool, str]:
        return "Next: Save & share →", self.app.session.verdict is not None, ""

    def on_theme_change(self) -> None:
        if self.app.session.verdict is not None and self.winfo_ismapped():
            self.draw_all()

"""Step 1: load a CSV/Excel file, an example with a known answer, or a saved analysis."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...core import api
from ...core.types import ColumnKind
from ...io.loaders import DataLoadError, load_table
from ..theme import SPACE, c, font
from ..widgets.common import (
    Callout,
    PageHeader,
    Section,
    Tag,
    divider,
    ghost_button,
    label,
    primary_button,
)
from .base import Page

KIND_NAMES = {
    ColumnKind.NUMERIC: "Number",
    ColumnKind.BINARY: "Yes / no",
    ColumnKind.COUNT: "Count",
    ColumnKind.CATEGORICAL: "Category",
    ColumnKind.TEXT: "Text (not used)",
    ColumnKind.DATETIME: "Date (not used)",
}

EXAMPLES = [
    ("real_effect", "Real effect", "Sleep truly raises grades by 3 points per hour."),
    ("no_effect", "No effect", "Sleep has no effect at all."),
    ("confounded", "Hidden common cause", "Study time drives both sleep and grades."),
    ("mediated", "Mediator trap", "Keeping tiredness equal hides the real effect."),
    ("collider", "Collider trap", "Looking only at scholarship students fakes an effect."),
]
MAX_COLUMNS_SHOWN = 60
EXAMPLES_DIR = Path.home() / "Multiverse Studio examples"


class DataPage(Page):
    step_id = "data"

    def build(self) -> None:
        self.header = PageHeader(
            self,
            "Your data",
            "Load the table you want to check: one row per person or case, one column per "
            "measurement. Your data never leaves this computer.",
        )
        self.place(self.header, 0)

        self.message = ctk.CTkFrame(self, fg_color="transparent")
        self.message.grid_columnconfigure(0, weight=1)

        load = Section(
            self, "Load a file", "CSV or Excel (.xlsx). The first row must hold the column names."
        )
        btns = ctk.CTkFrame(load.body, fg_color="transparent")
        btns.grid(row=0, column=0, sticky="w")
        primary_button(btns, "Choose a file…", self.choose_file, width=170).pack(side="left")
        ghost_button(btns, "Open a saved analysis…", self.open_session).pack(
            side="left", padx=(SPACE["sm"], 0)
        )
        self.place(load, 2)

        self.summary = Section(self, "What we found in each column")
        self.columns_frame = self.summary.body

        self.examples = Section(
            self,
            "Or try an example with a known answer",
            "Each example is generated with a true effect you know in advance, so you can watch "
            "whether the method finds it. Useful for learning and teaching.",
        )
        grid = self.examples.body
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1, uniform="ex")
        for i, (key, name, desc) in enumerate(EXAMPLES):
            cell = ctk.CTkFrame(grid, fg_color=c("subtle"), corner_radius=10)
            cell.grid(
                row=i // 3,
                column=i % 3,
                sticky="nsew",
                padx=(0, SPACE["sm"]),
                pady=(0, SPACE["sm"]),
            )
            label(cell, name, "body_bold").pack(anchor="w", padx=SPACE["md"], pady=(SPACE["md"], 0))
            label(cell, desc, "small", "text_secondary", wrap=220).pack(
                anchor="w", padx=SPACE["md"]
            )
            ghost_button(
                cell, "Use this example", lambda k=key: self.load_example(k), height=30
            ).pack(anchor="w", padx=SPACE["md"], pady=SPACE["md"])
        self.place(self.examples, 4)

    # ------------------------------------------------------------------ show
    def on_show(self) -> None:
        if self.app.df is not None:
            self.render_summary()

    def focus_examples(self) -> None:
        self.after(50, lambda: self.app.scroll._parent_canvas.yview_moveto(1.0))

    def footer(self) -> tuple[str, bool, str]:
        if self.app.df is None:
            return "Next: Your question →", False, "Load a file or pick an example to continue."
        return "Next: Your question →", True, f"{self.app.data_name} is ready."

    # --------------------------------------------------------------- actions
    def show_message(self, kind: str, lead: str, text: str = "") -> None:
        for w in self.message.winfo_children():
            w.destroy()
        Callout(self.message, kind, lead, text).grid(row=0, column=0, sticky="ew")
        self.place(self.message, 1)

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose your data",
            filetypes=[("Data files", "*.csv *.tsv *.txt *.xlsx *.xls"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            df = load_table(path)
        except DataLoadError as exc:
            self.show_message("critical", "That file could not be loaded.", str(exc))
            return
        self.app.example_scenario = None
        self.app.set_data(df, Path(path).name, path)
        self.after_load()

    def load_example(self, scenario: str) -> None:
        df = api.simulate(scenario, n=300, seed=self.app.session.seed)
        EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        path = EXAMPLES_DIR / f"example_{scenario}.csv"
        df.to_csv(path, index=False)
        self.app.example_scenario = scenario
        self.app.set_data(df, path.name, str(path))
        self.after_load(example=df.attrs.get("description"))

    def open_session(self) -> None:
        path = filedialog.askopenfilename(
            title="Open a saved analysis", filetypes=[("Multiverse Studio", "*.msession")]
        )
        if not path:
            return
        try:
            self.app.load_session(path)
        except Exception as exc:
            self.show_message("critical", "That analysis could not be opened.", str(exc))
            return
        self.after_load()
        target = 5 if self.app.session.verdict else 4
        self.app.go(target)

    def after_load(self, example: str | None = None) -> None:
        df = self.app.df
        lead = f"Loaded {self.app.data_name}: {len(df):,} rows, {df.shape[1]} columns."
        if example:
            self.show_message("info", lead, f"The truth in this example: {example}")
        else:
            self.show_message("good", lead)
        self.render_summary()
        self.refresh_footer()

    def render_summary(self) -> None:
        profile = self.app.session.profile
        if profile is None:
            return
        body = self.columns_frame
        for w in body.winfo_children():
            w.destroy()
        for col, weight in enumerate((3, 2, 1, 4)):
            body.grid_columnconfigure(col, weight=weight, uniform="cols")
        for col, head in enumerate(("Column", "Looks like", "Missing", "Notes")):
            label(body, head, "small", "text_muted").grid(
                row=0, column=col, sticky="w", pady=(0, 6)
            )
        row = 1
        for info in profile.columns[:MAX_COLUMNS_SHOWN]:
            divider(body).grid(row=row, column=0, columnspan=4, sticky="ew")
            row += 1
            ctk.CTkLabel(
                body, text=info.name, font=("Cascadia Mono", 12), text_color=c("text"), anchor="w"
            ).grid(row=row, column=0, sticky="w", pady=6)
            usable = info.kind not in (ColumnKind.TEXT, ColumnKind.DATETIME)
            label(body, KIND_NAMES[info.kind], "body", "text" if usable else "text_muted").grid(
                row=row, column=1, sticky="w"
            )
            label(
                body, f"{info.n_missing}" if info.n_missing else "–", "body", "text_secondary"
            ).grid(row=row, column=2, sticky="w")
            notes = []
            if info.n_outliers_3sd:
                notes.append(
                    f"{info.n_outliers_3sd} extreme value{'s' if info.n_outliers_3sd > 1 else ''}"
                )
            if info.skewness is not None and abs(info.skewness) > 1:
                notes.append("skewed")
            if info.kind is ColumnKind.CATEGORICAL:
                notes.append(f"{info.n_unique} groups")
            label(body, ", ".join(notes), "small", "text_secondary").grid(
                row=row, column=3, sticky="w"
            )
            row += 1
        if len(profile.columns) > MAX_COLUMNS_SHOWN:
            hidden = len(profile.columns) - MAX_COLUMNS_SHOWN
            Tag(body, f"+ {hidden} more columns").grid(row=row, column=0, sticky="w", pady=(8, 0))
        self.place(self.summary, 3)
        _ = font  # keep import for type scale consistency

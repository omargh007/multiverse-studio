"""Step 7: save the script, the report, the PDF and the session; check the plan's integrity."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...core import api
from ...io.export_json import export_json
from ...io.export_script import export_script
from ...io.session_store import save_session
from ..theme import SPACE, c, mono
from ..widgets.common import (
    Callout,
    PageHeader,
    Section,
    divider,
    ghost_button,
    label,
    primary_button,
)
from .base import Page


def _export_pdf(session, path):
    from ...io.export_pdf import export_pdf

    return export_pdf(session, path)


ITEMS = [
    (
        "script",
        "Reproducible Python script",
        ".py",
        "Anyone with Python can re-run it and get exactly the same numbers.",
        export_script,
    ),
    (
        "json",
        "Full report (JSON)",
        ".json",
        "Every analysis, the verdict, the locked plan and your software versions.",
        export_json,
    ),
    (
        "pdf",
        "PDF report",
        ".pdf",
        "Charts, verdict and ready-to-use text for your supervisor or reviewers.",
        _export_pdf,
    ),
    (
        "session",
        "Analysis file",
        ".msession",
        "Reopen this analysis later in Multiverse Studio.",
        save_session,
    ),
]


def open_folder(path: Path) -> None:
    folder = str(path.parent)
    if sys.platform == "win32":
        os.startfile(folder)  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.run(["open", folder], check=False)
    else:
        subprocess.run(["xdg-open", folder], check=False)


class ExportPage(Page):
    step_id = "export"

    def build(self) -> None:
        self.place(
            PageHeader(
                self, "Save & share", "Everything someone needs to check or repeat this analysis."
            ),
            0,
        )
        self.items = Section(self)
        b = self.items.body
        b.grid_columnconfigure(0, weight=1)
        for i, (key, title, suffix, desc, _fn) in enumerate(ITEMS):
            if i:
                divider(b).grid(
                    row=2 * i - 1, column=0, columnspan=2, sticky="ew", pady=SPACE["md"]
                )
            left = ctk.CTkFrame(b, fg_color="transparent")
            left.grid(row=2 * i, column=0, sticky="w")
            label(left, title, "body_bold").pack(anchor="w")
            label(left, desc, "small", "text_secondary", wrap=560).pack(anchor="w")
            make = primary_button if key == "script" else ghost_button
            make(b, f"Save {suffix}", lambda k=key: self.save(k), width=130).grid(
                row=2 * i, column=1, sticky="e"
            )
        self.place(self.items, 1)
        self.feedback = ctk.CTkFrame(self, fg_color="transparent")
        self.feedback.grid_columnconfigure(0, weight=1)
        self.integrity = Section(
            self,
            "Plan integrity",
            "Proof that the analysis plan was fixed before the results were seen.",
        )
        self.place(self.integrity, 3)

    def on_show(self) -> None:
        b = self.integrity.body
        for w in b.winfo_children():
            w.destroy()
        s = self.app.session
        if s.blind is None:
            Callout(
                b,
                "warning",
                "No locked plan.",
                "Blind mode was off, so there's no fingerprint to verify. Turn it on in step 2 "
                "next time for a verifiable plan.",
            ).grid(sticky="ew")
        else:
            ok = api.verify_plan(s, s.blind)
            Callout(
                b,
                "good" if ok else "critical",
                "The plan matches its fingerprint."
                if ok
                else "The plan no longer matches its fingerprint.",
                f"Locked {s.blind.locked_at.replace('T', ' ').replace('+00:00', ' UTC')}.",
            ).grid(sticky="ew")
            ctk.CTkLabel(
                b, text=s.blind.sha256, font=mono(11), text_color=c("text_secondary"), anchor="w"
            ).grid(sticky="w", pady=(SPACE["sm"], 0))
        if s.notes.strip():
            Callout(
                b, "warning", "The plan was changed after results were seen.", s.notes.strip()
            ).grid(sticky="ew", pady=(SPACE["sm"], 0))

    def save(self, key: str) -> None:
        _, title, suffix, _desc, fn = next(i for i in ITEMS if i[0] == key)
        base = f"{self.app.session.x}_vs_{self.app.session.y}".replace(" ", "_")
        path = filedialog.asksaveasfilename(
            title=f"Save {title}",
            defaultextension=suffix,
            initialfile=base + suffix,
            filetypes=[(title, f"*{suffix}")],
        )
        if not path:
            return
        for w in self.feedback.winfo_children():
            w.destroy()
        try:
            saved = Path(fn(self.app.session, path))
        except NotImplementedError:
            Callout(
                self.feedback,
                "info",
                "PDF export is coming in the next version.",
                "Use the JSON report or the script for now.",
            ).grid(row=0, column=0, sticky="ew")
        except Exception as exc:
            Callout(
                self.feedback, "critical", f"Could not save the {title.lower()}.", str(exc)
            ).grid(row=0, column=0, sticky="ew")
        else:
            box = Callout(self.feedback, "good", f"Saved {saved.name}", str(saved.parent))
            box.grid(row=0, column=0, sticky="ew")
            ghost_button(box, "Open folder", lambda: open_folder(saved), width=110).grid(
                row=0, column=2, rowspan=2, padx=SPACE["md"]
            )
        self.place(self.feedback, 2)

    def footer(self) -> tuple[str, bool, str]:
        return "Start a new analysis", True, "Your results stay here until you start over."

    def on_next(self) -> bool:
        self.app.df = None
        from ...core.types import Session

        self.app.session = Session(seed=self.app.session.seed)
        self.app.suggested, self.app.ticked = [], {}
        self.app.choices_confirmed = self.app.guardrails_confirmed = False
        self.app.go(0)
        return False

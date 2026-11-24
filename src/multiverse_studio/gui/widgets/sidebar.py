"""Left sidebar: brand, the 7-step wizard, and global settings."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import customtkinter as ctk

from ..theme import RADIUS, SIDEBAR_WIDTH, SPACE, STEPS, c, font, mono
from .common import label

Status = Literal["done", "active", "todo", "locked"]


class StepRow(ctk.CTkFrame):
    def __init__(
        self, master, index: int, title: str, subtitle: str, on_click: Callable[[int], None]
    ):
        super().__init__(master, fg_color="transparent", corner_radius=RADIUS["button"], height=46)
        self.index = index
        self._on_click = on_click
        self._enabled = True
        self._status: Status = "todo"
        self.grid_columnconfigure(1, weight=1)
        self.badge = ctk.CTkLabel(
            self,
            text=str(index + 1),
            width=26,
            height=26,
            corner_radius=13,
            font=font("small"),
            border_width=1,
        )
        self.badge.grid(row=0, column=0, rowspan=2, padx=(SPACE["sm"], SPACE["md"]), pady=6)
        self.title = label(self, title, "body_bold")
        self.title.grid(row=0, column=1, sticky="sw", pady=(6, 0))
        self.subtitle = label(self, subtitle, "caption", "text_muted")
        self.subtitle.grid(row=1, column=1, sticky="nw", pady=(0, 6))
        for w in (self, self.badge, self.title, self.subtitle):
            w.bind("<Button-1>", self._click)
            w.bind("<Enter>", self._hover_on)
            w.bind("<Leave>", self._hover_off)

    def _click(self, _event=None) -> None:
        if self._enabled:
            self._on_click(self.index)

    def _hover_on(self, _event=None) -> None:
        if self._enabled and self._status != "active":
            self.configure(fg_color=c("subtle"))

    def _hover_off(self, _event=None) -> None:
        if self._status != "active":
            self.configure(fg_color="transparent")

    def set_state(self, status: Status, subtitle: str, enabled: bool) -> None:
        self._status = status
        self._enabled = enabled
        self.subtitle.configure(text=subtitle if len(subtitle) <= 28 else subtitle[:27] + "…")
        cursor = "hand2" if enabled else "arrow"
        for w in (self, self.badge, self.title, self.subtitle):
            w.configure(cursor=cursor)
        if status == "active":
            self.configure(fg_color=c("accent_soft"))
            self.badge.configure(
                text=str(self.index + 1),
                fg_color=c("button"),
                text_color=c("text_on_accent"),
                border_color=c("button"),
            )
            self.title.configure(text_color=c("text"))
        elif status == "done":
            self.configure(fg_color="transparent")
            self.badge.configure(
                text="✓", fg_color=c("good_soft"), text_color=c("good"), border_color=c("good_soft")
            )
            self.title.configure(text_color=c("text"))
        else:
            self.configure(fg_color="transparent")
            self.badge.configure(
                text=str(self.index + 1),
                fg_color="transparent",
                text_color=c("text_muted"),
                border_color=c("border"),
            )
            self.title.configure(text_color=c("text_secondary" if enabled else "text_muted"))


class Sidebar(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_step: Callable[[int], None],
        on_examples: Callable[[], None],
        on_theme: Callable[[str], None],
        on_text_size: Callable[[str], None],
    ):
        super().__init__(
            master, width=SIDEBAR_WIDTH, corner_radius=0, fg_color=c("sidebar"), border_width=0
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=SPACE["lg"], pady=(SPACE["lg"], SPACE["md"]))
        logo = ctk.CTkCanvas(brand, width=30, height=30, highlightthickness=0, bd=0)
        logo.grid(row=0, column=0, rowspan=2, padx=(0, SPACE["md"]))
        self._logo = logo
        label(brand, "Multiverse Studio", "body_bold").grid(row=0, column=1, sticky="w")
        label(brand, "offline · v0.1", "caption", "text_muted").grid(row=1, column=1, sticky="w")

        steps = ctk.CTkFrame(self, fg_color="transparent")
        steps.grid(row=1, column=0, sticky="ew", padx=SPACE["md"])
        steps.grid_columnconfigure(0, weight=1)
        self.rows = []
        for i, (_sid, title, sub) in enumerate(STEPS):
            row = StepRow(steps, i, title, sub, on_step)
            row.grid(row=i, column=0, sticky="ew", pady=1)
            self.rows.append(row)

        self.grid_rowconfigure(2, weight=1)
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew", padx=SPACE["lg"], pady=SPACE["lg"])
        bottom.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(
            bottom,
            text="Examples with a known answer",
            command=on_examples,
            font=font("small"),
            height=32,
            corner_radius=RADIUS["button"],
            fg_color="transparent",
            hover_color=c("subtle"),
            border_width=1,
            border_color=c("border"),
            text_color=c("text_secondary"),
        ).grid(row=0, column=0, sticky="ew", pady=(0, SPACE["md"]))

        label(bottom, "Appearance", "caption", "text_muted").grid(row=1, column=0, sticky="w")
        self.theme = ctk.CTkSegmentedButton(
            bottom,
            values=["Light", "Dark"],
            command=on_theme,
            font=font("small"),
            height=28,
            selected_color=c("card"),
            selected_hover_color=c("card"),
            unselected_color=c("subtle"),
            unselected_hover_color=c("border"),
            fg_color=c("subtle"),
            text_color=c("text"),
        )
        self.theme.set("Light")
        self.theme.grid(row=2, column=0, sticky="ew", pady=(2, SPACE["sm"]))
        label(bottom, "Text size (projector)", "caption", "text_muted").grid(
            row=3, column=0, sticky="w"
        )
        self.text_size = ctk.CTkSegmentedButton(
            bottom,
            values=["100%", "115%", "130%"],
            command=on_text_size,
            font=font("small"),
            height=28,
            selected_color=c("card"),
            selected_hover_color=c("card"),
            unselected_color=c("subtle"),
            unselected_hover_color=c("border"),
            fg_color=c("subtle"),
            text_color=c("text"),
        )
        self.text_size.set("100%")
        self.text_size.grid(row=4, column=0, sticky="ew", pady=(2, SPACE["sm"]))
        self.seed = ctk.CTkLabel(
            bottom, text="", font=mono(11), text_color=c("text_muted"), anchor="w"
        )
        self.seed.grid(row=5, column=0, sticky="w", pady=(SPACE["xs"], 0))
        self.draw_logo()

    def draw_logo(self) -> None:
        """Four rising dots: a tiny specification curve."""
        dark = ctk.get_appearance_mode() == "Dark"
        bg = c("accent_soft")[1 if dark else 0]
        dot = c("accent")[1 if dark else 0]
        cv = self._logo
        cv.delete("all")
        cv.configure(bg=c("sidebar")[1 if dark else 0])
        cv.create_rectangle(0, 0, 30, 30, fill=bg, outline=bg)
        for i, (x, y) in enumerate([(7, 21), (12, 17), (18, 13), (23, 8)]):
            cv.create_oval(x - 2.5, y - 2.5, x + 2.5, y + 2.5, fill=dot, outline=dot, tags=f"d{i}")

    def update_steps(self, statuses: list[Status], subtitles: list[str], enabled: list[bool]):
        for row, st, sub, en in zip(self.rows, statuses, subtitles, enabled, strict=True):
            row.set_state(st, sub, en)

    def set_seed(self, seed: int) -> None:
        self.seed.configure(text=f"Repeat-exactly number: {seed}")

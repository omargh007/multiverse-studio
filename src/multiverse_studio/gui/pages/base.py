"""Base class for wizard pages."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from ..theme import SPACE

if TYPE_CHECKING:
    from ..app import App


class Page(ctk.CTkFrame):
    """One wizard step.

    Subclasses implement ``build`` once and ``on_show`` every time the page
    appears. ``footer`` tells the app what the Next button says and whether it
    is enabled; ``on_next`` runs when it's pressed (return True to move on).
    """

    step_id = ""
    gap = SPACE["lg"]

    def __init__(self, master, app: App):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.build()

    # --- to override -------------------------------------------------------
    def build(self) -> None:  # pragma: no cover - GUI
        raise NotImplementedError

    def on_show(self) -> None:
        pass

    def footer(self) -> tuple[str, bool, str]:
        """(next label, next enabled, hint text)."""
        return "Next", True, ""

    def on_next(self) -> bool:
        return True

    def on_theme_change(self) -> None:
        pass

    # --- helpers ------------------------------------------------------------
    def place(self, widget, row: int, **kw) -> None:
        widget.grid(row=row, column=0, sticky="ew", pady=(0, self.gap), **kw)

    def refresh_footer(self) -> None:
        self.app.refresh_chrome()

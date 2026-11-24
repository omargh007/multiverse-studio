"""Embed a Matplotlib Figure in CustomTkinter via FigureCanvasTkAgg."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ..theme import c
from .common import ui_scale  # noqa: E402


class PlotFrame(ctk.CTkFrame):
    """Holds one figure at a fixed height; replace it with ``show(fig)``."""

    def __init__(self, master, height: int = 360, **kw):
        super().__init__(master, fg_color=c("card"), height=height, **kw)
        self._height = height
        self._mpl_canvas: FigureCanvasTkAgg | None = None
        self.figure: Figure | None = None
        self._click_cb: Callable | None = None

    def show(self, fig: Figure, on_click: Callable | None = None) -> None:
        fig.set_dpi(100 * ui_scale(self))
        if self._mpl_canvas is not None:
            self._mpl_canvas.get_tk_widget().destroy()
        self.figure = fig
        self._mpl_canvas = FigureCanvasTkAgg(fig, master=self)
        tk_widget = self._mpl_canvas.get_tk_widget()
        tk_widget.configure(height=int(self._height * ui_scale(self)), highlightthickness=0, bd=0)
        tk_widget.pack(fill="both", expand=True)
        if on_click is not None:
            self._mpl_canvas.mpl_connect("button_press_event", on_click)
            tk_widget.configure(cursor="hand2")
        self._mpl_canvas.draw_idle()

    def redraw(self) -> None:
        if self._mpl_canvas is not None:
            self._mpl_canvas.draw_idle()

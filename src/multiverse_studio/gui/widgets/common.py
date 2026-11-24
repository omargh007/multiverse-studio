"""Small reusable widgets. Every colour, font and size comes from ``gui.theme``."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import customtkinter as ctk

from ..theme import RADIUS, SPACE, c, font, mono

Kind = Literal["info", "good", "warning", "critical"]
ICONS = {"info": "i", "good": "✓", "warning": "!", "critical": "✕"}
SOFT = {
    "info": "accent_soft",
    "good": "good_soft",
    "warning": "warning_soft",
    "critical": "critical_soft",
}
STRONG = {"info": "accent", "good": "good", "warning": "warning", "critical": "critical"}


def ui_scale(widget) -> float:
    """CustomTkinter's widget scaling (display DPI x user text size), 1.0 if unknown."""
    try:
        from customtkinter.windows.widgets.scaling import ScalingTracker

        return float(ScalingTracker.get_widget_scaling(widget))
    except Exception:  # pragma: no cover - depends on CTk internals
        return 1.0


def autowrap(lbl: ctk.CTkLabel, pad: int = 0, minimum: int = 120) -> ctk.CTkLabel:
    """Wrap ``lbl`` to the width of its container, whatever the window size or DPI."""

    def on_resize(event) -> None:
        width = event.width / ui_scale(lbl) - pad
        lbl.configure(wraplength=max(minimum, int(width)))

    lbl.master.bind("<Configure>", on_resize, add="+")
    return lbl


def label(master, text: str = "", role: str = "body", color: str = "text", wrap: int = 0, **kw):
    """Left-aligned text label. ``wrap`` > 0 wraps at that many pixels."""
    kw.setdefault("height", 1)  # shrink to the text (CTk default is 28 px)
    return ctk.CTkLabel(
        master,
        text=text,
        font=font(role),
        text_color=c(color),
        anchor="w",
        justify="left",
        wraplength=wrap,
        **kw,
    )


def primary_button(master, text: str, command: Callable | None = None, **kw) -> ctk.CTkButton:
    opts = dict(
        font=font("body_bold"),
        height=36,
        corner_radius=RADIUS["button"],
        fg_color=c("button"),
        hover_color=c("button_hover"),
        text_color=c("text_on_accent"),
        text_color_disabled=c("text_muted"),
    )
    return ctk.CTkButton(master, text=text, command=command, **{**opts, **kw})


def ghost_button(master, text: str, command: Callable | None = None, **kw) -> ctk.CTkButton:
    opts = dict(
        font=font("body"),
        height=34,
        corner_radius=RADIUS["button"],
        fg_color="transparent",
        hover_color=c("subtle"),
        border_width=1,
        border_color=c("border"),
        text_color=c("text_secondary"),
        text_color_disabled=c("text_muted"),
    )
    return ctk.CTkButton(master, text=text, command=command, **{**opts, **kw})


def set_enabled(button: ctk.CTkButton, enabled: bool, primary: bool = True) -> None:
    """Disabled primary buttons turn neutral, so a disabled action never looks clickable."""
    if primary:
        button.configure(
            state="normal" if enabled else "disabled",
            fg_color=c("button") if enabled else c("subtle"),
        )
    else:
        button.configure(state="normal" if enabled else "disabled")


class Section(ctk.CTkFrame):
    """A bordered surface for one self-contained unit. Put content in ``.body``."""

    def __init__(self, master, title: str | None = None, subtitle: str | None = None, **kw):
        super().__init__(
            master,
            fg_color=c("card"),
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=c("border"),
            **kw,
        )
        self.grid_columnconfigure(0, weight=1)
        row = 0
        if title:
            self.title = label(self, title, "h2")
            self.title.grid(row=row, column=0, sticky="ew", padx=SPACE["xl"], pady=(SPACE["lg"], 0))
            row += 1
        if subtitle:
            self.subtitle = autowrap(label(self, subtitle, "small", "text_muted", wrap=640), pad=60)
            self.subtitle.grid(row=row, column=0, sticky="ew", padx=SPACE["xl"], pady=(2, 0))
            row += 1
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(
            row=row,
            column=0,
            sticky="nsew",
            padx=SPACE["xl"],
            pady=(SPACE["md"] if (title or subtitle) else SPACE["lg"], SPACE["lg"]),
        )
        self.body.grid_columnconfigure(0, weight=1)


class Callout(ctk.CTkFrame):
    """Tinted message: icon + bold lead + text. Never a coloured side stripe."""

    def __init__(self, master, kind: Kind, lead: str, text: str = "", wrap: int = 680, **kw):
        super().__init__(master, fg_color=c(SOFT[kind]), corner_radius=10, **kw)
        self.grid_columnconfigure(1, weight=1)
        icon = ctk.CTkLabel(
            self,
            text=ICONS[kind],
            width=22,
            height=22,
            corner_radius=11,
            fg_color=c(STRONG[kind]),
            text_color=c("card"),
            font=font("small"),
        )
        icon.grid(row=0, column=0, sticky="n", padx=(SPACE["md"], SPACE["sm"]), pady=SPACE["md"])
        self.lead = autowrap(label(self, lead, "body_bold", wrap=wrap), pad=70)
        self.lead.grid(row=0, column=1, sticky="ew", padx=(0, SPACE["md"]), pady=(SPACE["md"], 0))
        self.text = autowrap(label(self, text, "body", "text_secondary", wrap=wrap), pad=70)
        if text:
            self.text.grid(
                row=1, column=1, sticky="ew", padx=(0, SPACE["md"]), pady=(2, SPACE["md"])
            )
        else:
            self.lead.grid_configure(pady=SPACE["md"])

    def update_text(self, lead: str, text: str = "") -> None:
        self.lead.configure(text=lead)
        self.text.configure(text=text)


class Badge(ctk.CTkLabel):
    def __init__(self, master, kind: Kind, text: str, **kw):
        super().__init__(
            master,
            text=f"{ICONS[kind]}  {text}",
            font=font("small"),
            corner_radius=999,
            fg_color=c(SOFT[kind]),
            text_color=c(STRONG[kind]),
            height=26,
            **kw,
        )

    def set(self, kind: Kind, text: str) -> None:
        self.configure(
            text=f"{ICONS[kind]}  {text}", fg_color=c(SOFT[kind]), text_color=c(STRONG[kind])
        )


class Tag(ctk.CTkLabel):
    """Small grey pill for technical terms next to plain words."""

    def __init__(self, master, text: str, **kw):
        super().__init__(
            master,
            text=text,
            font=font("caption"),
            corner_radius=999,
            fg_color=c("subtle"),
            text_color=c("text_muted"),
            height=20,
            **kw,
        )


class PageHeader(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str = "", **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.grid_columnconfigure(0, weight=1)
        self.title = label(self, title, "h1")
        self.title.grid(row=0, column=0, sticky="w")
        self.subtitle = label(self, subtitle, "body", "text_secondary", wrap=720)
        self.subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.right = ctk.CTkFrame(self, fg_color="transparent", width=1, height=1)
        self.right.grid(row=0, column=1, rowspan=2, sticky="ne")


class KeyValue(ctk.CTkFrame):
    """Rows of 'plain key: value', separated by hairlines."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.grid_columnconfigure(1, weight=1)
        self._rows = 0

    def clear(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._rows = 0

    def add(self, key: str, value: str, tech: str | None = None, mono_value: bool = False):
        r = self._rows
        if r:
            ctk.CTkFrame(self, height=1, fg_color=c("border")).grid(
                row=2 * r - 1, column=0, columnspan=2, sticky="ew"
            )
        k = ctk.CTkFrame(self, fg_color="transparent")
        k.grid(row=2 * r, column=0, sticky="w", pady=SPACE["sm"])
        label(k, key, "body", "text_secondary").pack(side="left")
        if tech:
            Tag(k, tech).pack(side="left", padx=(SPACE["sm"], 0))
        v = ctk.CTkLabel(
            self,
            text=value,
            font=mono(12) if mono_value else font("body_bold"),
            text_color=c("text"),
            anchor="e",
            justify="right",
            wraplength=360,
        )
        v.grid(row=2 * r, column=1, sticky="e", pady=SPACE["sm"], padx=(SPACE["lg"], 0))
        self._rows += 1
        return v


def divider(master) -> ctk.CTkFrame:
    return ctk.CTkFrame(master, height=1, fg_color=c("border"))


def copy_to_clipboard(widget, text: str) -> None:
    widget.clipboard_clear()
    widget.clipboard_append(text)

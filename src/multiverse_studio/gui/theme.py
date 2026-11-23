"""Design tokens: the ONLY place where colours, fonts, spacing and radii are defined.

Style: "clean scientific". The UI uses slate neutrals and one blue accent, and the
accent is the same blue as the chart's "significant" colour, so the app and the
charts read as one system. Every widget takes its values from here; there are no
hard-coded hex values in the pages.

CustomTkinter accepts (light, dark) tuples for colours and switches them when
``ctk.set_appearance_mode`` changes. Use ``c("name")`` to get such a tuple.
"""

from __future__ import annotations

import sys

# --------------------------------------------------------------------------- colour
# name: (light, dark)
COLORS: dict[str, tuple[str, str]] = {
    # surfaces
    "bg": ("#f8fafc", "#0b1220"),  # window background
    "sidebar": ("#ffffff", "#0f172a"),
    "card": ("#ffffff", "#1e293b"),  # = chart surface (validated)
    "subtle": ("#f1f5f9", "#273449"),  # hover rows, inactive chips
    "border": ("#e2e8f0", "#334155"),
    # text
    "text": ("#0f172a", "#f1f5f9"),
    "text_secondary": ("#475569", "#cbd5e1"),
    "text_muted": ("#64748b", "#94a3b8"),  # >= 4.5:1 on card in both modes
    "text_on_accent": ("#ffffff", "#ffffff"),
    # accent (one blue - same hue as chart "significant")
    "accent": ("#2a78d6", "#5598e7"),  # focus rings, selected step bar, links
    "button": ("#256abf", "#256abf"),  # primary button fill: white text 5.39:1
    "button_hover": ("#1c5cab", "#2a78d6"),
    "accent_soft": ("#e8f1fc", "#1c3253"),  # selected step, info banners
    # status text/icons (always paired with an icon + label, never colour alone)
    # all >= 4.5:1 on the card surface in their mode (checked 2026-11-23)
    "good": ("#0b7a0b", "#22b322"),
    "warning": ("#8a5a00", "#fab219"),
    "critical": ("#d03b3b", "#e66767"),
    "good_soft": ("#e7f6e7", "#163a1f"),
    "warning_soft": ("#fdf3dc", "#3d3115"),
    "critical_soft": ("#fbe9e9", "#3f1f24"),
}


def c(name: str) -> tuple[str, str]:
    """(light, dark) colour pair for CustomTkinter widgets."""
    return COLORS[name]


# ---------------------------------------------------------------------- typography
if sys.platform == "win32":
    FONT_FAMILY = "Segoe UI"
    MONO_FAMILY = "Cascadia Mono"
elif sys.platform == "darwin":
    FONT_FAMILY = "Helvetica Neue"
    MONO_FAMILY = "Menlo"
else:
    FONT_FAMILY = "DejaVu Sans"
    MONO_FAMILY = "DejaVu Sans Mono"

# role: (size, weight)
TYPE_SCALE: dict[str, tuple[int, str]] = {
    "display": (26, "bold"),  # big verdict number, e.g. "92%"
    "h1": (20, "bold"),  # page title
    "h2": (16, "bold"),  # card title
    "body": (14, "normal"),
    "body_bold": (14, "bold"),
    "small": (12, "normal"),  # helper text, technical term under plain word
    "caption": (11, "normal"),
}


def font(role: str = "body") -> tuple[str, int, str]:
    """Font tuple usable directly as ``font=`` in CustomTkinter widgets."""
    size, weight = TYPE_SCALE[role]
    return (FONT_FAMILY, size, weight)


def mono(size: int = 12) -> tuple[str, int]:
    return (MONO_FAMILY, size)


# --------------------------------------------------------------- spacing and shape
SPACE = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "2xl": 32, "3xl": 48}
RADIUS = {"input": 6, "button": 8, "card": 12, "chip": 999}
BORDER_WIDTH = 1

SIDEBAR_WIDTH = 240
MIN_WINDOW = (1100, 720)
DEFAULT_WINDOW = (1280, 800)

# -------------------------------------------------------------------- wizard steps
STEPS: list[tuple[str, str, str]] = [
    # (id, plain title, technical subtitle)
    ("data", "Your data", "Load CSV / Excel"),
    ("question", "Your question", "Outcome (Y) and factor (X)"),
    ("choices", "Analysis choices", "Specifications"),
    ("guardrails", "Fair comparisons", "Causal guardrails"),
    ("run", "Run", "Blind mode + multiverse"),
    ("results", "Results", "Specification curve"),
    ("export", "Save & share", "Script, JSON, PDF"),
]

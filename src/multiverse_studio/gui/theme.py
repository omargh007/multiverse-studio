"""Design tokens: the ONLY place where colours, fonts, spacing and radii are defined.

Style: "calm scientific instrument" (see DESIGN.md). Slate neutrals and one blue
accent; the accent is the same blue as the chart's "significant" colour, so the
app and its evidence read as one system.

The tokens feed three things:
  * ``streamlit_theme_flags()``: Streamlit's own light and dark themes (passed by
    the launcher as ``--theme.light.*`` / ``--theme.dark.*`` options);
  * ``css()``: the small stylesheet for the parts Streamlit does not theme;
  * ``tokens()``: colours for the HTML snippets the app draws itself.

This module has no Streamlit import, so it can be tested and reused anywhere.
"""

from __future__ import annotations

# --------------------------------------------------------------------------- colour
# name: (light, dark)
COLORS: dict[str, tuple[str, str]] = {
    # surfaces
    "bg": ("#f8fafc", "#0b1220"),  # page background
    "panel": ("#ffffff", "#0f172a"),  # the plan column (second neutral)
    "card": ("#ffffff", "#1e293b"),  # content surfaces, chart surface (validated)
    "subtle": ("#f1f5f9", "#273449"),  # widget fill, chips, code blocks
    "border": ("#e2e8f0", "#334155"),
    # text
    "text": ("#0f172a", "#f1f5f9"),
    "text_secondary": ("#475569", "#cbd5e1"),
    "text_muted": ("#64748b", "#94a3b8"),  # >= 4.5:1 on card in both modes
    "text_on_accent": ("#ffffff", "#ffffff"),
    # accent (one blue - same hue as chart "significant")
    "accent": ("#2a78d6", "#5598e7"),  # focus rings, links, current block
    "button": ("#256abf", "#256abf"),  # primary button fill: white text 5.39:1
    "accent_soft": ("#e8f1fc", "#1c3253"),  # selected chips, info callouts
    # status (always paired with an icon and a word, never colour alone)
    "good": ("#0b7a0b", "#22b322"),
    "warning": ("#8a5a00", "#fab219"),
    "critical": ("#b42d2d", "#e66767"),  # 5.35:1 on critical_soft (light)
    "good_soft": ("#e7f6e7", "#163a1f"),
    "warning_soft": ("#fdf3dc", "#3d3115"),
    "critical_soft": ("#fbe9e9", "#3f1f24"),
}

FONT_STACK = '"Segoe UI", "Helvetica Neue", "DejaVu Sans", system-ui, sans-serif'
MONO_STACK = '"Cascadia Mono", Menlo, "DejaVu Sans Mono", monospace'

# role: (size in px, weight)
TYPE_SCALE: dict[str, tuple[int, int]] = {
    "display": (30, 700),  # the verdict share only, e.g. "0%"
    "h1": (22, 700),
    "h2": (17, 700),
    "body": (15, 400),
    "small": (13, 400),
    "caption": (12, 400),
}

SPACE = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "2xl": 32, "3xl": 48}
RADIUS = {"input": 6, "button": 8, "card": 12, "chip": 999}

TEXT_SIZES = {"100%": 1.0, "115%": 1.15, "130%": 1.3}
"""Projector / low-vision setting: scales the whole page."""


def tokens(dark: bool = False) -> dict[str, str]:
    """``{name: hex}`` for one mode."""
    i = 1 if dark else 0
    return {name: pair[i] for name, pair in COLORS.items()}


def streamlit_theme_flags() -> list[str]:
    """Command-line options that give Streamlit our light and dark themes.

    Both themes are defined, so the app menu offers a Light / Dark choice.
    """
    flags: list[str] = []
    for mode, dark in (("light", False), ("dark", True)):
        t = tokens(dark)
        values = {
            "primaryColor": t["button"],
            "backgroundColor": t["bg"],
            "secondaryBackgroundColor": t["subtle"],
            "textColor": t["text"],
            "borderColor": t["border"],
            "linkColor": t["accent"],
            "blueColor": t["accent"],
            "blueBackgroundColor": t["accent_soft"],
            "greenColor": t["good"],
            "greenTextColor": t["good"],
            "greenBackgroundColor": t["good_soft"],
            "orangeColor": t["warning"],
            "orangeTextColor": t["warning"],
            "orangeBackgroundColor": t["warning_soft"],
            "yellowColor": t["warning"],
            "yellowTextColor": t["warning"],
            "yellowBackgroundColor": t["warning_soft"],
            "redColor": t["critical"],
            "redTextColor": t["critical"],
            "redBackgroundColor": t["critical_soft"],
            "grayColor": t["text_muted"],
            "grayTextColor": t["text_secondary"],
            "grayBackgroundColor": t["subtle"],
            "codeBackgroundColor": t["subtle"],
            "font": FONT_STACK,
            "codeFont": MONO_STACK,
            "headingFontWeights": "700",
            "baseRadius": f"{RADIUS['input']}px",
            "buttonRadius": f"{RADIUS['button']}px",
            "showWidgetBorder": "true",
            "chartCategoricalColors": '["#2a78d6", "#eb6834", "#8a8a84"]'
            if not dark
            else '["#3987e5", "#d95926", "#7d8696"]',
        }
        flags += [f"--theme.{mode}.{key}={value}" for key, value in values.items()]
    flags.append(f"--theme.baseFontSize={TYPE_SCALE['body'][0]}")  # global only
    return flags


def css(dark: bool = False, scale: float = 1.0) -> str:
    """The stylesheet for what Streamlit's theme does not reach."""
    t = tokens(dark)
    return f"""
:root {{ color-scheme: {"dark" if dark else "light"}; }}
.stApp {{ zoom: {scale}; }}
::selection {{ background: {t["accent_soft"]}; color: {t["text"]}; }}
.stApp *:focus-visible {{ outline: 2px solid {t["accent"]}; outline-offset: 2px; }}
* {{ scrollbar-color: {t["border"]} transparent; }}
[data-testid="stHeader"] {{ background: transparent; height: 3rem; }}
[data-testid="stMainBlockContainer"] {{ padding: 0.5rem 2rem 3rem; max-width: 1600px; }}
[data-testid="stDecoration"] {{ display: none; }}
.stApp .tabular, .stApp table, .stApp code {{ font-variant-numeric: tabular-nums; }}
.st-key-plan {{
  background: {t["panel"]}; border: 1px solid {t["border"]};
  border-radius: {RADIUS["card"]}px; padding: 20px 22px 22px;
}}
.st-key-plan hr {{ margin: 4px 0; border-color: {t["border"]}; }}
.st-key-topbar {{ border-bottom: 1px solid {t["border"]}; padding: 2px 3.5rem 12px 0; margin-bottom: 4px; }}
[class*="st-key-card-"] {{
  background: {t["card"]}; border: 1px solid {t["border"]};
  border-radius: {RADIUS["card"]}px; padding: 16px 18px;
}}
.ms-callout {{ display: flex; gap: 10px; align-items: flex-start; border-radius: {RADIUS["card"]}px;
  padding: 12px 14px; font-size: 14px; line-height: 1.45; color: {t["text"]}; }}
.ms-callout svg {{ flex: none; margin-top: 2px; }}
.ms-callout b.lead {{ display: block; }}
.ms-callout .body {{ color: {t["text_secondary"]}; }}
.ms-mono {{ font-family: {MONO_STACK}; font-size: 12.5px; }}
.ms-callout .ms-mono {{ overflow-wrap: anywhere; }}
.st-key-card-curve {{ overflow-x: auto; }}
.st-key-card-curve [data-testid="stVegaLiteChart"] {{ min-width: 600px; }}
.ms-muted {{ color: {t["text_muted"]}; font-size: 13px; }}
.ms-secondary {{ color: {t["text_secondary"]}; }}
.ms-tech {{ color: {t["text_muted"]}; font-size: 12px; font-weight: 400; }}
.ms-chip {{ display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px;
  font-size: 12.5px; background: {t["subtle"]}; color: {t["text_secondary"]}; white-space: nowrap; }}
.ms-chip.good {{ background: {t["good_soft"]}; color: {t["good"]}; }}
.ms-block-title {{ font-size: 15px; font-weight: 700; color: {t["text"]}; line-height: 1.3; }}
.ms-summary {{ font-size: 14px; color: {t["text_secondary"]}; line-height: 1.45; }}
.ms-num {{ display: inline-flex; width: 22px; height: 22px; border-radius: 50%; align-items: center;
  justify-content: center; font-size: 12px; font-weight: 700; flex: none;
  border: 1px solid {t["border"]}; color: {t["text_muted"]}; background: {t["card"]}; }}
.ms-num.current {{ background: {t["button"]}; border-color: {t["button"]}; color: #fff; }}
.ms-num.done {{ background: {t["good_soft"]}; border-color: {t["good_soft"]}; color: {t["good"]}; }}
.ms-head {{ display: flex; gap: 10px; align-items: center; }}
.ms-verdict-share {{ font-size: {TYPE_SCALE["display"][0]}px; font-weight: 700; line-height: 1;
  color: {t["text"]}; font-variant-numeric: tabular-nums; }}
.ms-facts {{ display: flex; flex-wrap: wrap; gap: 8px 28px; margin-top: 12px; font-size: 14px; }}
.ms-facts dt {{ color: {t["text_secondary"]}; font-size: 12.5px; }}
.ms-facts dd {{ margin: 2px 0 0; font-weight: 700; color: {t["text"]}; font-variant-numeric: tabular-nums; }}
.ms-bar {{ display: grid; grid-template-columns: minmax(120px, 190px) 1fr 44px; gap: 10px;
  align-items: center; font-size: 14px; padding: 5px 0; }}
.ms-bar .track {{ height: 10px; border-radius: 3px; background: {t["subtle"]}; }}
.ms-bar .fill {{ height: 10px; border-radius: 3px; background: {t["accent"]}; }}
.ms-bar .val {{ text-align: right; color: {t["text_secondary"]}; font-variant-numeric: tabular-nums; }}
.ms-legend {{ display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 13px; color: {t["text_secondary"]}; }}
.ms-legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
.ms-dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; }}
.ms-steps {{ list-style: none; margin: 8px 0 0; padding: 0; font-size: 14px; }}
.ms-steps li {{ display: flex; align-items: center; gap: 8px; padding: 4px 0; color: {t["text"]}; }}
.ms-steps li .state {{ margin-left: auto; color: {t["text_muted"]}; font-size: 13px; }}
.ms-empty h2 {{ font-size: {TYPE_SCALE["h1"][0]}px; margin: 0 0 6px; }}
.st-key-card-text [data-testid="stCode"] pre, .st-key-card-text [data-testid="stCode"] code {{
  font-family: {FONT_STACK}; font-size: 15px; line-height: 1.6; white-space: pre-wrap; max-width: 72ch; }}
@media (max-width: 640px) {{
  .st-key-topbar-spacer, .st-key-topbar > div:has(.st-key-topbar-spacer) {{ display: none !important; }}
  .st-key-topbar {{ padding-right: 2.5rem; gap: 8px 12px !important; }}
}}
.ms-empty p {{ max-width: 68ch; color: {t["text_secondary"]}; line-height: 1.55; margin: 0 0 10px; }}
"""


# -------------------------------------------------------------------- plan blocks
BLOCKS: list[tuple[str, str, str]] = [
    # (id, plain title, technical subtitle)
    ("data", "Your data", "CSV / Excel"),
    ("question", "Your question", "outcome Y and factor X"),
    ("choices", "Analysis choices", "specifications"),
    ("fairness", "Fair comparisons", "causal guardrails"),
]

# Design

Source of truth for values: `src/multiverse_studio/gui/theme.py` (UI: Streamlit light/dark themes plus a small stylesheet) and `src/multiverse_studio/plots/palette.py` (charts, shared by the Altair curve and the Matplotlib figures). This file explains them.

## Visual theme
**Calm scientific instrument.** The UI uses cool slate neutrals plus one blue, the same blue that marks "significant" in the charts, so the app and its evidence read as one system. Light mode is the default: users work in daylight, and the classroom projector washes out dark UIs. Dark mode is fully supported.

Colour strategy: **Restrained**. The neutrals carry the surface. Blue appears only for the primary action, the current step, selection and "significant same direction". Status colours appear only with an icon and a label.

## Colour (light / dark)
| Role | Light | Dark | Use |
|---|---|---|---|
| bg | #f8fafc | #0b1220 | page |
| panel | #ffffff | #0f172a | the plan column (second neutral) |
| card | #ffffff | #1e293b | content surfaces, chart surface |
| subtle | #f1f5f9 | #273449 | hover rows, chips, code blocks |
| border | #e2e8f0 | #334155 | 1px dividers and control outlines |
| text / secondary / muted | #0f172a / #475569 / #64748b | #f1f5f9 / #cbd5e1 / #94a3b8 | all at least 4.5:1 on card |
| accent | #2a78d6 | #5598e7 | focus, current step, links |
| button | #256abf | #256abf | primary fill; white text 5.39:1 |
| good / warning / critical | #0b7a0b / #8a5a00 / #b42d2d | #22b322 / #fab219 / #e66767 | status text, always with icon and label |

Chart: significant same direction #2a78d6 / #3987e5, opposite #eb6834 / #d95926, not significant #8a8a84 / #7d8696. Validated: colour-blind ΔE ≥ 24, normal-vision ΔE ≥ 31, contrast ≥ 3:1. Left-out analyses use hollow markers.

## Typography
One family, the system UI font (Segoe UI on Windows, Helvetica Neue on macOS, DejaVu Sans on Linux), plus a mono font for hashes, seeds, variable names and code.

| Role | Size / weight |
|---|---|
| display | 30 bold (only the verdict share) |
| h1 | 22 bold (empty-state and data titles) |
| h2 | 17–19 bold (plan title, card titles) |
| body | 15 (Streamlit base size) |
| small | 13 (helper text, technical terms) |
| caption | 12 |

The **Display** setting scales the whole page by 1.0, 1.15 or 1.3 (CSS zoom).

## Spacing and shape
4px base: 4, 8, 12, 16, 24, 32, 48. Radii: input 6, button 8, section 12, chips fully rounded. Borders are 1px. No shadows inside the app, and no side-stripe accents. The current step is shown by a tinted background and a filled number.

## Layout
**Workbench: plan beside evidence.** A top bar (logo and name, repeat-exactly number, lock state, Display), then two columns: the plan (about 36%) and the evidence (about 64%). Below about 640 px the columns stack, plan first.

## Components
- **Plan column:** a white panel with 1px dividers. Four blocks (data, question, choices, fair comparisons) each with a number badge (done: green tick on a green tint; current: filled blue; locked: outlined grey), a plain title and a small technical subtitle. A finished block folds to a one-line summary with a tertiary **Edit** button. The run section ends the column: Run settings (expander), the lock callout with the fingerprint, and the one primary **Lock plan and run N analyses** button.
- **Option chips:** Streamlit pills, multi-select, one row per analysis choice.
- **Segmented control:** Yes / No / Not sure for each guardrail question, one question per row, label left.
- **Callouts:** tinted background plus an icon and a bold lead sentence. Never a coloured side stripe. Kinds: info (accent tint), good, warning, critical.
- **Verdict:** a tinted callout in the verdict's status colour, with icon + word + gloss, the share as the only display number, one plain sentence, and a row of four labelled facts.
- **Cards:** white, 1px border, 12 px radius, only for separate units of evidence (curve, importance, cherry-pick, text, Save & share). No nested cards.
- **Specification curve:** interactive Altair chart (hover tooltip, click a dot for its choices and code), with the choices panel underneath sharing the x scale and a fixed axis gutter.
- **Chips:** status and fact chips in the top bar, fully rounded.

States for every interactive element come from Streamlit's themed widgets: default, hover, focus (2 px accent ring, set in the stylesheet), active, disabled with a reason in the help text or caption, loading (progress bar), error (critical callout).

## Motion
Streamlit's own colour transitions only. The progress bar fills; the live curve adds dots as results arrive (redrawn every 0.75 s). No page transitions.

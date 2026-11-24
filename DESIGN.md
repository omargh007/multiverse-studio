# Design

Source of truth for values: `src/multiverse_studio/gui/theme.py` (UI) and `src/multiverse_studio/plots/palette.py` (charts). This file explains them.

## Visual theme
**Calm scientific instrument.** The UI uses cool slate neutrals plus one blue, the same blue that marks "significant" in the charts, so the app and its evidence read as one system. Light mode is the default: users work in daylight, and the classroom projector washes out dark UIs. Dark mode is fully supported.

Colour strategy: **Restrained**. The neutrals carry the surface. Blue appears only for the primary action, the current step, selection and "significant same direction". Status colours appear only with an icon and a label.

## Colour (light / dark)
| Role | Light | Dark | Use |
|---|---|---|---|
| bg | #f8fafc | #0b1220 | window |
| sidebar | #ffffff | #0f172a | navigation layer (second neutral) |
| card | #ffffff | #1e293b | content surfaces, chart surface |
| subtle | #f1f5f9 | #273449 | hover rows, chips, code blocks |
| border | #e2e8f0 | #334155 | 1px dividers and control outlines |
| text / secondary / muted | #0f172a / #475569 / #64748b | #f1f5f9 / #cbd5e1 / #94a3b8 | all at least 4.5:1 on card |
| accent | #2a78d6 | #5598e7 | focus, current step, links |
| button | #256abf | #256abf | primary fill; white text 5.39:1 |
| good / warning / critical | #0b7a0b / #8a5a00 / #d03b3b | #22b322 / #fab219 / #e66767 | status text, always with icon and label |

Chart: significant same direction #2a78d6 / #3987e5, opposite #eb6834 / #d95926, not significant #8a8a84 / #7d8696. Validated: colour-blind ΔE ≥ 24, normal-vision ΔE ≥ 31, contrast ≥ 3:1. Left-out analyses use hollow markers.

## Typography
One family, the system UI font (Segoe UI on Windows, Helvetica Neue on macOS, DejaVu Sans on Linux), plus a mono font for hashes, seeds and code.

| Role | Size / weight |
|---|---|
| display | 26 bold (only the verdict share) |
| h1 | 20 bold (page title) |
| h2 | 16 bold (section title) |
| body | 14 |
| small | 12 (helper text, technical terms) |
| caption | 11 |

A text-scale setting multiplies every size by 1.0, 1.15 or 1.3.

## Spacing and shape
4px base: 4, 8, 12, 16, 24, 32, 48. Radii: input 6, button 8, section 12, chips fully rounded. Borders are 1px. No shadows inside the app, and no side-stripe accents. The current step is shown by a tinted background and a filled number.

## Components
- **Sidebar wizard:** 7 steps, each with a number badge (done ✓, current, upcoming), a plain title and a small technical subtitle. Below it: Teaching mode, seed chip, theme toggle and text size.
- **Page header:** h1 title, one-line purpose, right-aligned context (count, lock status).
- **Sections:** a card is used only where content is a separate unit (verdict, cherry-pick, curve). Choices are listed as rows on one surface, not nested cards.
- **Option chips:** checkbox and label, tinted when selected, disabled with a reason ("needs ≥ 30").
- **Segmented control:** Yes / No / Not sure for the guardrail questions.
- **Callouts:** tinted background plus an icon and bold lead sentence. Never a coloured side stripe.
- **Footer bar:** Back (ghost) on the left, hint in the middle, primary Next on the right.

States for every interactive element: default, hover, focus (2px accent ring), active, disabled (with reason), loading, error.

## Motion
150–200 ms colour and opacity changes only. The progress bar fills; the live curve adds dots as results arrive. No page transitions.

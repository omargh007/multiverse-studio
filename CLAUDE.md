# CLAUDE.md: Multiverse Studio

Instructions for Claude (and humans) working in this repo. Read this first, then **[docs/STATUS.md](docs/STATUS.md)**, which says where the project is and what is left to do.

## What this project is
A university final project (Python for Data Science, Fall 2026, 3 students). The presentation to the instructor is due around **7 December 2026**. A SoftwareX submission is optional.

**Multiverse Studio** is an offline CustomTkinter desktop app for non-programmers. It runs every defensible combination of analysis choices (a multiverse / specification-curve analysis) and says whether an "X affects Y" finding is consistent or fragile.

The novel features:
- **Causal guardrails:** excludes bad controls and bad subsets.
- **Blind mode:** the plan is locked with a SHA-256 hash before results are shown.
- **Cherry-pick check.**

The full brief from the instructor is in the course document. The requirements that matter are summarised below.

## Hard rules
1. **No AI attribution anywhere.** No "Co-Authored-By: Claude", no "Generated with Claude", no mention of AI in commits, code comments or docs.
2. **Core never imports the GUI.** `core/`, `io/` and `plots/` must not import `tkinter`, `customtkinter` or `gui`. A test enforces this.
3. **The GUI only calls `multiverse_studio.core.api`.** Put analysis logic in `core/`, not in GUI callbacks.
4. **Long work runs off the main thread.** Use `gui/worker.py` (thread + queue + `after()` polling). Never touch Tk widgets from a worker thread.
5. **One seed.** Any random step uses `core.seed.rng_for(seed, purpose)`. See `docs/decisions.md`, D-3.
6. **Don't change the contract casually.** Changes to `core/types.py` or the signatures in `core/api.py` affect everyone. Explain the change and get the team to agree first.
7. **Keep scope locked:** linear, logistic and Poisson models only. No new statistical families unless the team agrees.
8. **Update `docs/STATUS.md`** when a task is finished or started, and `CHANGELOG.md` for user-visible changes.

## Before saying something is done
```bash
# from the repo root, with the virtual environment active
ruff format src tests
ruff check src tests
pytest --cov --cov-fail-under=70
```
- CI runs the same checks on Windows and Linux, Python 3.10 and 3.12.
- Coverage must stay at least 70%. It is currently about 97%.
- For GUI changes, also run the app (`python -m multiverse_studio`) and look at the screen you changed, in light **and** dark mode.

## Setup on a new laptop
```bash
git clone https://github.com/omargh007/multiverse-studio.git
cd multiverse-studio
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
pytest -q                         # everything should pass
python -m multiverse_studio       # opens the app
```
To try the app quickly, use the sidebar → **Examples with a known answer** → **Mediator trap**. Choose grade ← sleep_hours, then click through to the results.

## Map of the code
| Path | What |
|---|---|
| `src/multiverse_studio/core/` | analysis engine: `api.py` (public facade), `types.py` (the shared contract, `Session` = shared state), profiling, choices, specs, models (statsmodels), runner, inference (verdict + permutation test), guardrails, blind, cherry, importance, simulate, narrative, serialize |
| `src/multiverse_studio/io/` | load CSV/Excel, export script, JSON report, session save/load, PDF (**not built yet**) |
| `src/multiverse_studio/plots/` | Matplotlib figures (spec curve, importance) + validated chart palette |
| `src/multiverse_studio/gui/` | CustomTkinter app: `app.py` (window, navigation, state), `pages/` (one per wizard step), `widgets/`, `theme.py` (design tokens), `worker.py` |
| `tests/` | pytest: `core/`, `io/`, `plots/`, `gui/` (GUI test skips without a display) |
| `docs/architecture.md` | layers, workflow, threading |
| `docs/decisions.md` | verdict rule (D-2), seed (D-3), processing order (D-4), limits (D-5), guardrails (D-6), datasets (D-7) |
| `docs/planning/` | novelty search and feature plan |
| `PRODUCT.md`, `DESIGN.md` | who it's for, voice, design principles, colours, type, components |

## UI and design rules
- Use only the tokens in `gui/theme.py` (colours as `c("name")`, `font("role")`, `SPACE`, `RADIUS`). No hard-coded hex values in pages. Chart colours live in `plots/palette.py`.
- Wording comes first:
  - Plain words first, with the technical term small next to it (for example "Things to keep equal" with a `control variables` tag).
  - Every number gets a one-sentence explanation.
  - No em dashes, no emoji, no hype.
- Colour is never the only signal (icons, labels, hollow markers). Text must meet WCAG AA contrast in light and dark.
- No coloured side-stripe borders, no gradients, no glassmorphism, no nested cards.
- Every new screen needs its empty, loading, error and too-much-data states.
- Read `PRODUCT.md` and `DESIGN.md` before UI work.

## Grading reminders (from the brief)
Design and code quality 20, testing / CI / packaging 15, novelty 10, GUI usability 10, reproducibility 10, case studies 10, impact evidence 10, paper 10, demo 5.

The required evidence:
- 2 case studies on public, redistributable data
- a usability study (SUS plus time-on-task)
- a PyPI release
- a Zenodo DOI

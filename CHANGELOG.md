# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).


## [Unreleased]
### Changed
- **The interface is now a Streamlit app** served on localhost only, replacing the CustomTkinter desktop window (decision D-8). Start it the same way: `multiverse-studio` or `python -m multiverse_studio`; it opens in the browser.
- New layout, "plan beside evidence": the plan (data, question, choices, fair comparisons) sits in a left column and folds into one-line summaries; the evidence (progress, verdict, specification curve, what matters most, cherry-pick check, ready-to-use text, Save & share) sits on the right, so a changed choice and its effect are one glance apart.
- The specification curve is interactive (Altair): hover for details, click a dot to see that analysis and copy its code.
- Exports are browser downloads (script, JSON report, analysis file).
### Added
- `gui/state.py`: a `Workbench` controller with no Streamlit import, so the whole interface workflow is unit-tested; `tests/gui/test_app.py` drives the real page with Streamlit's `AppTest`.
### Removed
- CustomTkinter, the Tk worker and the seven wizard pages. Tcl/Tk is no longer needed.

## [Unreleased]
### Added
- Project skeleton: package layout, core API contract, CI on Windows and Linux (coverage gate 70%), MIT license, CITATION.cff.
- Core engine:
  - column profiling and model choice (linear, logistic, Poisson);
  - rule-based suggested choices (outliers, controls, subsets, transforms, missing values);
  - specification grid with a cap and seeded sampling;
  - runner with progress and cancel;
  - verdict (Simonsohn et al., 2020) with a permutation test;
  - decision importance.
- Causal guardrails: three plain questions per variable. Bad controls *and* subsets on bad variables are excluded.
- Blind mode: no result is shown until the plan is locked with a SHA-256 hash that includes a fingerprint of the data file (`blind_view` also offers an outcome-shuffled copy for previews).
- Cherry-pick check: where a reported estimate sits among the valid analyses.
- Teaching simulator with five scenarios that have a known true effect.
- Auto-written methods and results paragraphs.
- Session (de)serialisation, and export of a runnable reproduction script.
- Design tokens (light and dark) and a chart palette validated for colour-blind safety and contrast.
- Desktop GUI (CustomTkinter), a 7-step sidebar wizard:
  - load data, a saved analysis or an example with a known answer;
  - question and blind mode;
  - analysis choices with a live count and a limit;
  - fair comparisons (guardrail questions);
  - run in a background thread with a live preview, cancel and a luck check;
  - results: verdict, cherry-pick check, clickable specification curve, decision importance, ready-to-use text;
  - save and share: script, JSON report, analysis file, plan-integrity check.
- Light/dark mode, text-size setting for projectors, keyboard shortcuts.
- JSON report with environment capture; save and reopen analyses (.msession).
- Specification-curve and decision-importance figures (Matplotlib, embedded with FigureCanvasTkAgg).
- End-to-end GUI smoke test.

# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

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

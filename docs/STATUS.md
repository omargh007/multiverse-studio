# Project status

**Last updated:** 2026-11-24
**Presentation:** about 7 December 2026

Update this file when you finish a task: tick it off and move it to Done.

## Where we are
The software works end to end and is tested. CI is green on Windows and Linux with Python 3.10 and 3.12. Coverage is about 97% across 98 tests.

What is left is mostly **evidence and release work**: case studies, the usability study, the PDF export, the PyPI and Zenodo release, and the report and slides.

## Done
- [x] Repo, packaging (`pyproject.toml`), MIT license, CITATION.cff, CHANGELOG, CI on Windows and Linux with a 70% coverage gate
- [x] Core engine:
  - column profiling and model choice
  - suggested choices
  - specification grid with a cap and seeded sampling
  - runner with progress and cancel
  - verdict plus permutation test
  - decision importance
- [x] Novel features:
  - causal guardrails, covering controls and subsets
  - blind mode with a SHA-256 plan lock that includes a fingerprint of the data file
  - cherry-pick check
- [x] Teaching simulator with 5 scenarios that have a known true effect (used as the GUI examples and as ground-truth tests)
- [x] Exports: runnable reproduction script, JSON report with environment capture, save and reopen an analysis (`.msession`)
- [x] Auto-written methods and results paragraphs
- [x] Streamlit interface (plan beside evidence), light and dark mode, text size for projectors
- [x] Charts: specification curve (clickable) and decision importance, with a palette checked for colour-blind safety
- [x] Docs: architecture, decisions D-1 to D-7, PRODUCT.md, DESIGN.md, README with screenshots
- [x] Novelty search: SoftwareX, JOSS, PyPI, GitHub, jamovi/JASP (`docs/planning/novelty-search.md`)

## Changed since the last update
- [x] Interface rebuilt with Streamlit (plan beside evidence), approved by the instructor on 25 November 2026 (D-8). Tests: 113, coverage about 98%.

## To do (priority order)

| # | Task | Notes |
|---|---|---|
| 1 | **Case study 1: hurricane names** (Jung et al. 2014; Simonsohn et al. 2020) | Find the public data and check that its license allows redistribution. Reproduce the published curve with the app and save the script, JSON and screenshots in `examples/`. |
| 2 | **Case study 2: fertility and religiosity** (Durante et al. 2013; Steegen et al. 2016) | Same as task 1. If redistribution isn't allowed, download the data at runtime instead. |
| 3 | **Case study 3 (optional): collider trap simulation** | The simulator shows a false effect without guardrails (−1.66, 65% significant) and none with them (+0.19). This is a strong demo. See D-6. |
| 4 | **Usability study** | 5–10 people from outside CS. Use the SUS questionnaire and time the same task in Excel or SPSS against the app. Book participants early. Put the results in `docs/usability/`. |
| 5 | **PDF export** (`io/export_pdf.py`) | The button already exists and currently says "coming in the next version". Use Matplotlib `PdfPages`, with no new dependency. Pages: verdict, curve, importance, guardrails, cherry-pick, text, hash. Add tests in `tests/io/`. |
| 6 | **Release** | 1. Bump the version to 1.0.0. 2. Build and upload to TestPyPI, then PyPI. 3. Make a GitHub release. 4. Connect Zenodo to create the DOI, then add it to CITATION.cff and the README. |
| 7 | **Windows `.exe`** (optional) | Harder with Streamlit: PyInstaller needs Streamlit's static files and a small launcher script. Test it on a laptop that doesn't have Python. |
| 8 | **Report / paper** in SoftwareX structure | Put it in `paper/`. It needs: the code metadata table C1–C10, motivation, a description with the architecture figure, the comparison table (≥ 5 tools, see the novelty search), the case studies, impact (usability results) and limitations. |
| 9 | **Slides and demo script** | Demo with the Mediator and Collider examples, then a real case study. Rehearse it. |
| 10 | Final novelty re-check | Check again that Scatterize "Scatterverse" (GitHub njvack/scatterize issue #65) is still unreleased. |

## Known limitations (say these honestly in the report)
- English only.
- Linear, logistic and Poisson models only. No mixed or panel models.
- Data must be one row per case.
- Guardrails depend on the user's answers about causal order.
- Blind mode proves the plan was locked before results were shown, but a determined user could start a new session. Any re-lock after seeing results is recorded in the session notes and shown in the exports.
- The luck check (permutation test) is slow for very large multiverses. The GUI defaults to 100 shuffles.

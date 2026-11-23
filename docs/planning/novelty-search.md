# Novelty Search: Multiverse Studio

**Date:** 2026-11-22
**Question:** Is there already a free, offline, point-and-click desktop tool that lets non-programmers run a specification-curve or multiverse analysis on their own data, from start to finish?

**Short answer:** We found none. Every existing tool falls into one of three groups:

- **Code-only:** you need R, Python or Stata.
- **Visualization-only:** it displays results that were computed somewhere else.
- **Planning-only:** it documents the analysis but doesn't run it.

## What was searched
- Web search: specification curve / multiverse GUIs, Shiny apps, PyPI packages, jamovi/JASP modules, SoftwareX/JOSS papers.

**Still to do by hand:**
1. Search inside SoftwareX (ScienceDirect) and JOSS (joss.theoj.org) for "multiverse" and "specification curve".
2. Browse the jamovi library (Modules > jamovi library) and the JASP module list.

## Comparison of existing tools

| Tool | Type | Language | GUI for own data? | Runs the analysis? | Offline? | Session export to script? |
|---|---|---|---|---|---|---|
| **specr** (Masur & Scharkow) | R package | R | No | Yes | Yes | It already is code |
| **multiverse** (MUCollective) | R package | R | No | Yes | Yes | It already is code |
| **rdfanalysis** Shiny spec curve (Gassen) | R package + Shiny viewer | R | Viewer only; design defined in R code | Yes, via code | Local Shiny | No |
| **Boba** (Liu et al.) | DSL + CLI + web visualizer | Python/any | Visualizer only | Yes, via DSL scripts | Yes | Scripts |
| **specification_curve** (Turrell) | Python package | Python | No | Yes (OLS etc.) | Yes | It already is code |
| **RobustiPy** (Oxford DemSci, 2025) | Python package | Python | No | Yes (at scale, bootstraps) | Yes | It already is code |
| **multiversum** | Python package | Python | No | Yes (config file) | Yes | Config file |
| **multiverse-tools** dashboard | Plotly Dash viewer | Python | Viewer only, fed with existing results | No | Local | No |
| **SMART** (Short et al., RSOS 2025) | Shiny web app | R | Yes, but planning only | **No**, it only documents pipelines | No (hosted web) | Exports documentation |
| **Multiverse plots** (PLOS ONE 2026) | Plotting code | Stata/R | No | Plotting only | Yes | It already is code |
| JASP / jamovi | GUI stats suites | R backend | Yes | **No multiverse module found** | Yes | Partial |
| **Multiverse Studio (ours)** | Desktop app + core library | Python | **Yes** | **Yes** | **Yes** | **Yes (Python script + JSON)** |

## Deeper search (2026-11-22, after instructor approval)

**Searched:**
- SoftwareX on ScienceDirect
- JOSS (joss.theoj.org)
- The jamovi library (modules.yaml) and JASP
- GitHub
- Shiny apps

**SoftwareX:** no paper found on a multiverse or specification-curve tool.

**JOSS:**
- **splithalf** (Parsons 2021) has a multiverse function, but it is an R package that only covers split-half reliability of cognitive tasks.
- No general specification-curve tool found.

**jamovi / JASP:** no module found. The listed modules include GAMLj (robust SEs) and rdfamily (robustness checks for regression discontinuity designs only).

**New tools found:**

| Tool | What it is | Why it differs from ours |
|---|---|---|
| **metaMultiverse** (Plessen, R + Shiny) | Point-and-click multiverse **meta-analysis**. Input is study-level effect sizes. | Doesn't take raw individual-level data and doesn't run regressions with controls, outlier rules or subsets. Different problem. |
| **Scatterize "Scatterverse"** (njvack, browser web app) | **Proposed** spec-curve view: pick forks, fit every path. Issue #65 was opened 2026-11-05 and is still open. | **Not released** (no branches or PRs). Web app, OLS-focused. **Closest future competitor. Cite it and recheck before presenting.** |
| **Milliways** (research prototype, paper) | Multiverse visual analytics system. | Not publicly available as a tool. |
| **specurve** (GitHub, Python) | Spec-curve for DFA/MFDFA estimators. | Code-only, niche domain. |
| **mverse** (R) | Explorable multiverse in R. | Code-only. |

**What makes us different:** we are the only tool that combines all of these.
1. Native offline desktop app
2. Raw individual-level data
3. **Guided suggestions** of choices from column types
4. Linear, logistic and Poisson models
5. Plain-language robustness verdict plus "which choice matters most"
6. Export to a **reproducible Python script** and a JSON report

## Gap statement
Specification-curve and multiverse analyses are recommended across psychology, economics, sociology and medicine, and JASP's reporting guidelines advise reporting them. Every tool that runs these analyses requires code, though. The GUIs that exist only document the analysis (SMART) or display results that were computed elsewhere (Boba's visualizer, rdfanalysis Shiny, multiverse-tools).

## Draft novelty paragraph (for the paper)
> Multiverse and specification-curve analyses are increasingly recommended to show how robust a finding is to defensible analytic choices. Existing implementations, however, all require programming. These include the R packages specr and multiverse, the Python libraries specification_curve, RobustiPy and multiversum, and the Boba domain-specific language. The few graphical tools serve only part of the workflow. SMART guides researchers through defining and preregistering a multiverse but does not execute it. Boba's visualizer, the rdfanalysis Shiny app and the multiverse-tools dashboard display results that were already computed in code. metaMultiverse offers a point-and-click interface, but only for multiverse meta-analysis of study-level effect sizes, not for raw individual-level data. General point-and-click statistics suites such as JASP and jamovi offer no multiverse module. Multiverse Studio is, to our knowledge, the first free, offline desktop application covering the whole multiverse workflow without code. Users load their own data, specify analytic choices through forms, run all specifications in parallel and inspect the specification curve. Each session is exported as a standalone Python script and a JSON report, so a non-programmer's analysis can be fully reproduced by others.

## Risks this search revealed
- **RobustiPy** is the strongest Python competitor: published, GPL and scalable. Our pitch is "a GUI for non-programmers plus export", not "a better engine". We could even use RobustiPy or statsmodels as the backend and cite it.
- **SMART** covers the "guided definition" step. We should cite it, and could import or export SMART's documentation format as a feature.
- **Overclaiming "first"** is a risk until the manual searches of SoftwareX, JOSS and jamovi are done.

## Sources
- specr (CRAN): https://cran.r-project.org/web/packages/specr/index.html
- multiverse (R): https://www.github.com/MUCollective/multiverse
- rdfanalysis Shiny spec curve: https://rdrr.io/pkg/rdfanalysis/man/shiny_rdf_spec_curve.html ; https://r-bloggers.com/2019/12/from-one-regression-to-hundreds-within-seconds-a-shiny-specification-curve
- Boba: https://pypi.org/project/boba/0.1.5/ ; https://arxiv.org/pdf/2007.05551
- specification_curve: https://pypi.org/project/specification-curve ; https://aeturrell.github.io/specification_curve
- RobustiPy: https://arxiv.org/html/2506.19958v2 ; https://pypi.org/project/robustipy/ ; https://robustipy.github.io
- multiversum: https://pypi.org/project/multiversum/
- SMART: https://pmc.ncbi.nlm.nih.gov/articles/PMC12567067 ; https://www.apps.meta-rep.lmu.de/SMART-App
- Multiverse plots / visualizing multiverse: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12875576/
- JASP meta-analysis module (example of the JASP module model): https://arxiv.org/html/2509.09845v1

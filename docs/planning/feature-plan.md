# Multiverse Studio: Refined Idea and Feature Plan
**Date:** 2026-11-23

## Refined one-line pitch
> **Multiverse Studio is an offline, no-code workbench that tests whether a research finding survives every defensible analysis.**
> It is the first such tool to add **causal guardrails** (it filters out bad control variables), a **blind mode** (you lock the plan before seeing the outcome) and a **cherry-pick check** (it shows where a reported result sits among all valid analyses).

## Novelty check of the new features (searched 2026-11-23)
| Feature | Existing work | Our status |
|---|---|---|
| Causal guardrails (good and bad controls) | The theory comes from Cinelli, Forney & Pearl ("A Crash Course in Good and Bad Controls"). A paper (arXiv 2609.16618, Sep 2026) adds candidate causal graphs to multiverse robustness and states that existing multiverse software lacks a causal layer. It is a method paper built on Stata tools, with no GUI. | **Novel as a no-code tool.** Cite both. |
| Blind mode (lock the plan, hash it, then reveal) | Blind analysis and preregistration are discussed in the literature. SMART documents multiverse plans but does not run them. **No tool found** that combines blinding, a hashed plan and execution. | **Novel** |
| Cherry-pick check (percentile of a reported result) | No tool found. specr's docs suggest it would be a "custom step". | **Novel** |
| Decision importance (which choice matters most) | Boba highlights sensitive decisions, and global sensitivity analysis papers decompose variance. | **Not novel.** Include it as a standard feature and cite those. |
| Teaching simulator (synthetic data with a known truth) | The p-hacker Shiny app (Schönbrodt) teaches p-hacking. | **Extension.** Cite p-hacker. |

## Feature tiers

### Tier 1: Core (must work by Day 6)
1. Load CSV or Excel. Detect column types.
2. Pick Y and X. Auto-select the model: linear, logistic or Poisson.
3. Suggested choices, then the user ticks them. These cover outliers, controls, subsets, transforms and missing values.
4. Show the combination count before Run. Cap it, with an optional random sample of N specifications (uses the seed).
5. Run in a worker thread with a progress bar. Results stream in progressively.
6. Specification curve plus the choice panel, embedded with FigureCanvasTkAgg.
7. Verdict based on a **defined, cited rule** (Simonsohn et al. 2020):
   - the share of specifications with the same sign as the median
   - the share that are significant in that direction
   - an optional permutation test (uses the seed)
8. Export a Python script, a JSON report and an environment capture.

### Tier 2: Novel features (Days 5–10)
9. **Causal Guardrails.** For each candidate control, the user answers 2–3 plain questions:
   - "Does it happen before X?"
   - "Could X cause it?"
   - "Could Y cause it?"

   The rules then classify it as a confounder (keep), a mediator (bad: blocks the effect), a collider (bad) or neutral. The tool shows "all universes" against "causally valid universes" and recomputes the verdict on the valid set only.
10. **Blind Mode.** Y is shuffled or hidden while the user builds the multiverse.
    - "Lock plan" writes a preregistration file containing the plan, a timestamp and a SHA-256 hash.
    - Results are revealed only after locking.
    - The exported report includes the hash, so anyone can verify the plan wasn't changed after seeing the results.
11. **Cherry-Pick Check.** The user enters a reported estimate and p-value from a paper or a first analysis. The tool reports:
    - its percentile in the multiverse
    - "X% of valid analyses give a weaker result"
    - a flag if it sits in the extreme tail
12. **Decision Importance.** A bar chart of how much each choice shifts the estimate, using the variance of the estimate explained by each decision.

### Tier 3: Completeness and polish (Days 9–13, if time allows)
13. **Teaching Simulator.** Generates seeded synthetic datasets with a known truth: no effect, a real effect, or a confounded effect. This shows how forking paths create false positives. It doubles as ground-truth tests and as a classroom use case for the impact section.
14. **Auto-written Methods and Results paragraph.** Template-based, offline, APA-style text the user can paste into a thesis.
15. Click a dot on the curve to see that specification's full regression table and its exact code.
16. PDF report.
17. PyInstaller .exe.

## Who owns what
| Owner | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| A: Core | engine, models, verdict rule, permutation test, export | causal rule engine, cherry-pick stats, decision importance | simulator, auto-text |
| B: GUI | wizard, run screen, curve plot, verdict | guardrail question screen, blind-mode flow, cherry-pick input | click-to-inspect, PDF |
| C: Release & evidence | CI, PyPI, Zenodo, CITATION.cff, datasets | case studies (hurricanes, fertility) using the guardrails | usability study, report, slides, .exe |

## Scope rules
- Tier 1 must be complete and tested **before** Tier 2 starts.
- Models are limited to linear, logistic and Poisson.
- Causal guardrails use rule-based questions only. No free-form DAG drawing.
- Seed is used for the permutation test, bootstrap, specification sampling and the simulator.

## Sources
- Cinelli, Forney & Pearl, A Crash Course in Good and Bad Controls: https://ftp.cs.ucla.edu/pub/stat_ser/r493.pdf
- A Multiverse of Good and Bad Controls (arXiv 2609.16618): https://arxiv.org/pdf/2609.16618
- Simonsohn, Simmons & Nelson 2020, Specification curve analysis: https://link.springer.com/article/10.1038/s41562-020-0912-z
- SMART: https://pmc.ncbi.nlm.nih.gov/articles/PMC12567067
- Boba: https://arxiv.org/pdf/2007.05551
- Global sensitivity analysis for multiverse: appeared in the search results, but we haven't confirmed which paper it is. Find the exact citation before using it.
- p-hacker teaching app (Schönbrodt): verify the link before citing.

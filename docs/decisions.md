# Design Decisions

Short records of choices that affect results. Cite these in the report.

## D-1: Models
Linear (OLS), logistic (Logit) and Poisson (GLM) via statsmodels, picked from the outcome's column type. Mixed models, panel models and Bayesian models are out of scope for v1.

## D-2: Verdict rule
Computed over **valid, successfully fitted** universes. These definitions follow Simonsohn, Simmons & Nelson (2020).

- `median_estimate`: the median of the estimates.
- `share_same_sign`: the share of universes whose estimate has the same sign as the median.
- `share_significant`: the share of universes that are significant (p < α, default 0.05) **in the median's direction**.
- `permutation_p`: the share of permuted multiverses (X shuffled, default 500 times) whose count of significant same-direction universes is ≥ the observed count.

Label:
| Label | Rule |
|---|---|
| **consistent** | `permutation_p < 0.05` **and** `share_same_sign ≥ 0.90` |
| **fragile** | `permutation_p ≥ 0.05` |
| **mixed** | anything else |

If the permutation test was skipped, the label uses `share_significant ≥ 0.50` in place of the permutation condition, and the GUI says so. The app always shows the **numbers**. The label is only a summary.

## D-3: Random seed
There is one global seed (`Session.seed`). It only affects random steps: specification sampling, the permutation test, blind-mode shuffling and the simulator. Each step uses `rng_for(seed, purpose)`, so adding a new random step never changes existing results. Plain regressions are deterministic.

## D-4: Order of data processing in one universe
1. **Subset** (which rows)
2. **Missing values** (drop, or mean-impute predictors)
3. **Outliers** (computed on the subset, applied to X and Y)
4. **Transforms** (log or z-score)
5. **Fit**

Outlier thresholds are computed *after* subsetting, because a first-year-only analysis should use first-year statistics.

## D-5: Size limit
The default maximum is 1,000 universes. The GUI shows the count before Run. When the grid is larger, the user can either reduce choices or take a seeded random sample of 1,000 (D-3).

## D-6: Causal guardrails
Rule table in `core/guardrails.py`, following Cinelli, Forney & Pearl (2022). Mediators, colliders and outcome proxies are excluded from the valid set. "Not sure" answers are kept but flagged. Free-form causal-graph drawing is out of scope.

A universe is invalid if it **controls for** a bad variable **or restricts the data to one level of it** (a subset choice). Restricting to one level conditions on the variable just like adjusting for it, so subsetting on a collider creates selection bias. The GUI therefore asks the questions for every control and subset variable (`variables_to_assess`).

The simulator checks this end to end (seed 1, n = 300, collider scenario, true effect 0):

| | Median estimate | Share significant | Label |
|---|---|---|---|
| Without guardrails | −1.66 | 65% | mixed (a false effect) |
| With guardrails | +0.19 | 0% | fragile (correct) |

## D-7: Datasets for case studies (to confirm licenses)
- Hurricane names (Jung et al., 2014; re-analysed by Simonsohn et al., 2020)
- Fertility and religiosity (Durante et al., 2013; re-analysed by Steegen et al., 2016)

Check redistribution rights before adding the files to `examples/data/`. If redistribution isn't allowed, download the data at runtime instead.

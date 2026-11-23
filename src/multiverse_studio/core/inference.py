"""Robustness verdict and permutation test. Owner: A (Core).

Implements the descriptive and inferential steps of specification curve
analysis (Simonsohn, Simmons & Nelson, 2020, Nature Human Behaviour 4:1208).
The label rule is fixed in docs/decisions.md, D-2.
"""

from __future__ import annotations

import threading
from collections.abc import Sequence

import numpy as np
import pandas as pd

from .models import fit_one
from .runner import Cancelled, ProgressFn
from .seed import rng_for
from .types import Decision, ModelFamily, Spec, SpecResult, Verdict

SAME_SIGN_THRESHOLD = 0.90
PERMUTATION_ALPHA = 0.05
FALLBACK_SIGNIFICANT_SHARE = 0.50


def _usable(results: Sequence[SpecResult]) -> list[SpecResult]:
    return [r for r in results if r.ok and r.valid]


def _direction(estimates: np.ndarray) -> float:
    med = float(np.median(estimates))
    return 1.0 if med >= 0 else -1.0


def count_significant(results: Sequence[SpecResult], alpha: float) -> tuple[int, float]:
    """(number of usable universes significant in the median's direction, direction)."""
    usable = _usable(results)
    if not usable:
        return 0, 1.0
    est = np.array([r.estimate for r in usable], dtype=float)
    p = np.array([r.p_value for r in usable], dtype=float)
    direction = _direction(est)
    return int(np.sum((p < alpha) & (np.sign(est) == direction))), direction


def summarize(
    results: Sequence[SpecResult], alpha: float = 0.05, permutation_p: float | None = None
) -> Verdict:
    """Descriptive summary over valid, fitted universes plus the D-2 label."""
    usable = _usable(results)
    if not usable:
        raise ValueError(
            "None of the analyses could be used. Check the error column of the results "
            "(for example, too few rows after filtering)."
        )
    est = np.array([r.estimate for r in usable], dtype=float)
    p = np.array([r.p_value for r in usable], dtype=float)
    direction = _direction(est)
    n_valid = len(usable)
    same = float(np.mean(np.sign(est) == direction))
    sig = float(np.mean((p < alpha) & (np.sign(est) == direction)))
    median = float(np.median(est))

    if permutation_p is not None:
        passes = permutation_p < PERMUTATION_ALPHA
    else:
        passes = sig >= FALLBACK_SIGNIFICANT_SHARE
    if not passes:
        label = "fragile"
    elif same >= SAME_SIGN_THRESHOLD:
        label = "consistent"
    else:
        label = "mixed"

    word = "positive" if direction > 0 else "negative"
    n_sig = int(round(sig * n_valid))
    parts = [
        f"{n_sig} of {n_valid} analyses ({sig:.0%}) find a significant {word} effect "
        f"(median {median:+.3g}); {same:.0%} point in the same direction."
    ]
    if permutation_p is not None:
        luck = "unlikely" if permutation_p < PERMUTATION_ALPHA else "not unlikely"
        parts.append(
            f"A pattern this strong is {luck} to arise by chance (p = {permutation_p:.3f})."
        )
    else:
        parts.append("The luck check (permutation test) was not run.")
    parts.append(
        {
            "consistent": "The result is consistent across reasonable analyses.",
            "mixed": "The result depends on the analysis choices.",
            "fragile": "The result is fragile: it does not hold up across reasonable analyses.",
        }[label]
    )
    return Verdict(
        n_specs=len(results),
        n_ok=sum(r.ok for r in results),
        n_valid=n_valid,
        median_estimate=median,
        share_same_sign=same,
        share_significant=sig,
        alpha=alpha,
        permutation_p=permutation_p,
        label=label,
        explanation=" ".join(parts),
    )


def permutation_test(
    df: pd.DataFrame,
    y: str,
    x: str,
    family: ModelFamily,
    decisions: Sequence[Decision],
    specs: Sequence[Spec],
    observed: Sequence[SpecResult],
    *,
    n_permutations: int = 500,
    alpha: float = 0.05,
    seed: int = 0,
    progress: ProgressFn | None = None,
    cancel: threading.Event | None = None,
) -> float:
    """Shuffle X ``n_permutations`` times (breaking any true X -> Y link), rerun the
    usable universes, and return the share of shuffled multiverses whose count of
    significant same-direction universes is >= the observed count.

    Uses ``rng_for(seed, "permutation")``. Returns ``(1 + k) / (1 + n)`` in (0, 1].
    Raises :class:`Cancelled` if ``cancel`` is set.
    """
    if n_permutations < 1:
        raise ValueError("n_permutations must be at least 1.")
    usable_ids = {r.spec_id for r in _usable(observed)}
    run_specs = [s for s in specs if s.id in usable_ids]
    observed_count, _ = count_significant(observed, alpha)
    rng = rng_for(seed, "permutation")
    x_values = df[x].to_numpy()
    exceed = 0
    for i in range(1, n_permutations + 1):
        if cancel is not None and cancel.is_set():
            raise Cancelled("Permutation test cancelled.")
        shuffled = df.copy()
        shuffled[x] = rng.permutation(x_values)
        perm = [fit_one(shuffled, y, x, family, decisions, s, alpha=alpha) for s in run_specs]
        count, _ = count_significant(perm, alpha)
        exceed += count >= observed_count
        if progress is not None:
            progress(i, n_permutations)
    return (1 + exceed) / (1 + n_permutations)

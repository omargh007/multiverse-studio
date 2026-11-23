"""Which decision moves the result most? Owner: A (Core).

Method: for each decision, the share of variance in the estimates explained by
that decision alone (eta-squared from grouping estimates by the decision's
option). Simple, transparent and standard in the multiverse literature
(cf. Boba's sensitivity view). Not claimed as novel.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .types import Decision, SpecResult


def decision_importance(
    results: Sequence[SpecResult], decisions: Sequence[Decision]
) -> dict[str, float]:
    """Return {decision_id: eta_squared in [0, 1]}, sorted from most to least important.

    Uses valid, fitted universes. Decisions with a single option score 0.
    """
    usable = [r for r in results if r.ok and r.valid]
    if not usable:
        return {d.id: 0.0 for d in decisions}
    est = np.array([r.estimate for r in usable], dtype=float)
    grand = est.mean()
    ss_total = float(np.sum((est - grand) ** 2))
    scores: dict[str, float] = {}
    for d in decisions:
        if ss_total == 0:
            scores[d.id] = 0.0
            continue
        groups: dict[str, list[float]] = {}
        for r, e in zip(usable, est, strict=True):
            groups.setdefault(r.choices.get(d.id, ""), []).append(e)
        ss_between = sum(len(v) * (np.mean(v) - grand) ** 2 for v in groups.values())
        scores[d.id] = float(min(max(ss_between / ss_total, 0.0), 1.0))
    return dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True))

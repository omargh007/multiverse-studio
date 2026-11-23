"""Cherry-pick check: where does a reported result sit in the multiverse?

Owner: A (Core).  [NOVEL FEATURE]
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .types import CherryPickResult, SpecResult


def cherry_pick_check(
    results: Sequence[SpecResult], reported_estimate: float, tail: float = 0.05
) -> CherryPickResult:
    """Percentile of ``reported_estimate`` among valid universes.

    ``share_weaker`` counts universes with a smaller effect in the reported
    direction (for a negative reported effect, "smaller" means closer to zero
    or positive). ``flagged`` is True when share_weaker >= 1 - tail, i.e. the
    reported result is in the most favourable 5% of valid analyses.
    """
    est = np.array([r.estimate for r in results if r.ok and r.valid], dtype=float)
    if est.size == 0:
        raise ValueError("There are no valid analyses to compare the reported result with.")
    rep = float(reported_estimate)
    percentile = float(np.mean(est <= rep) * 100)
    share_weaker = float(np.mean(est < rep)) if rep >= 0 else float(np.mean(est > rep))
    flagged = share_weaker >= 1 - tail
    n = est.size
    text = (
        f"{share_weaker:.0%} of the {n} fair analyses give a weaker effect than the "
        f"reported {rep:+.3g}."
    )
    if share_weaker == 1.0:
        text = f"The reported {rep:+.3g} is stronger than all {n} fair analyses."
    if flagged:
        text += " It is one of the most favourable possible results and may be cherry-picked."
    else:
        text += " It is within the range that reasonable analyses produce."
    return CherryPickResult(
        reported_estimate=rep,
        percentile=percentile,
        share_weaker=share_weaker,
        flagged=flagged,
        explanation=text,
    )

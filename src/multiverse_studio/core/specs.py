"""Build the grid of universes (specifications) from a list of decisions."""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence

from .seed import rng_for
from .types import Decision, Spec


def count_specs(decisions: Sequence[Decision]) -> int:
    """Number of universes = product of the number of options of every decision.

    An empty decision list gives exactly one universe (the baseline analysis).
    """
    return math.prod(len(d.options) for d in decisions) if decisions else 1


def _choice_at(decisions: Sequence[Decision], index: int) -> dict[str, str]:
    """Decode a flat index into one option per decision (mixed-radix, last decision fastest)."""
    choices: dict[str, str] = {}
    for decision in reversed(decisions):
        n = len(decision.options)
        index, r = divmod(index, n)
        choices[decision.id] = decision.options[r].id
    return {d.id: choices[d.id] for d in decisions}


def build_specs(
    decisions: Sequence[Decision],
    *,
    max_specs: int | None = None,
    sample_if_over: bool = True,
    seed: int = 0,
) -> list[Spec]:
    """Enumerate every universe, or a seeded random sample when there are too many.

    Args:
        decisions: the forks to combine. Each must have at least one option.
        max_specs: upper limit on universes. ``None`` means no limit.
        sample_if_over: when the full grid exceeds ``max_specs``, draw a uniform
            random sample of ``max_specs`` universes (seeded). If False, raise.
        seed: the session's global seed.

    Returns:
        Specs with ids ``0..k-1`` in grid order (sampled specs keep grid order too,
        so results are stable and easy to compare).

    Raises:
        ValueError: if a decision has no options, ids are duplicated, or the grid
            exceeds ``max_specs`` while ``sample_if_over`` is False.
    """
    ids = [d.id for d in decisions]
    if len(ids) != len(set(ids)):
        raise ValueError("Decision ids must be unique.")
    for d in decisions:
        if not d.options:
            raise ValueError(f"Decision '{d.id}' has no options.")

    total = count_specs(decisions)

    if max_specs is not None and total > max_specs:
        if not sample_if_over:
            raise ValueError(
                f"The multiverse has {total} universes, more than the limit of {max_specs}. "
                "Remove some options or allow random sampling."
            )
        rng = rng_for(seed, "sampling")
        indices = sorted(rng.choice(total, size=max_specs, replace=False).tolist())
    else:
        indices = range(total)

    if not decisions:
        return [Spec(id=0, choices={})]

    return [Spec(id=i, choices=_choice_at(decisions, idx)) for i, idx in enumerate(indices)]


def iter_all_choices(decisions: Sequence[Decision]):
    """Yield every combination as a dict (convenience for small grids and tests)."""
    for combo in itertools.product(*(d.options for d in decisions)):
        yield {d.id: o.id for d, o in zip(decisions, combo, strict=True)}

"""One global seed for every random step (docs/decisions.md, D-3).

Plain regressions are deterministic, so the seed only matters for:
  * random sampling of universes when the multiverse is larger than ``max_specs``,
  * the permutation test (Simonsohn et al., 2020),
  * blind mode (shuffling the outcome while the plan is built),
  * the teaching simulator.

Each step gets its *own* child generator derived from the global seed and a
fixed purpose name, so adding a new random step never changes the results of
the existing ones.
"""

from __future__ import annotations

import hashlib

import numpy as np

PURPOSES = ("sampling", "permutation", "blind", "simulator")


def child_seed(seed: int, purpose: str) -> int:
    """Derive a stable 32-bit seed for one purpose from the global seed."""
    digest = hashlib.sha256(f"{seed}:{purpose}".encode()).digest()
    return int.from_bytes(digest[:4], "little")


def rng_for(seed: int, purpose: str) -> np.random.Generator:
    """Return a NumPy generator dedicated to ``purpose``.

    >>> a = rng_for(42, "sampling").integers(0, 100, 3)
    >>> b = rng_for(42, "sampling").integers(0, 100, 3)
    >>> bool((a == b).all())
    True
    """
    return np.random.default_rng(child_seed(seed, purpose))

from __future__ import annotations

from multiverse_studio.core.seed import child_seed, rng_for


def test_same_seed_same_numbers():
    assert (rng_for(1, "permutation").random(5) == rng_for(1, "permutation").random(5)).all()


def test_purposes_are_independent():
    assert child_seed(1, "sampling") != child_seed(1, "permutation")


def test_different_seeds_differ():
    assert child_seed(1, "sampling") != child_seed(2, "sampling")

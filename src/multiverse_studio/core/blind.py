"""Blind mode: build the plan without seeing real results. Owner: A (Core).  [NOVEL FEATURE]

Workflow:
  1. ``blind_view`` returns a copy of the data with Y shuffled (seeded), so
     profiling and choice building work, but any curve shown is meaningless.
  2. ``lock_plan`` serialises the plan (question, decisions, guardrails, seed,
     alpha, limits, and a fingerprint of the data file) to canonical JSON and
     stores its SHA-256 hash with a UTC timestamp.
  3. Real results are revealed only after locking. Exports include the hash;
     ``verify_plan`` lets anyone check the plan was not edited afterwards.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .seed import rng_for
from .serialize import answers_to_dict, decision_to_dict
from .types import BlindLock, Session


def blind_view(df: pd.DataFrame, y: str, seed: int) -> pd.DataFrame:
    """Copy of ``df`` with column ``y`` permuted using ``rng_for(seed, "blind")``."""
    out = df.copy()
    out[y] = rng_for(seed, "blind").permutation(out[y].to_numpy())
    return out


def file_sha256(path: str | Path) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def plan_dict(session: Session) -> dict[str, Any]:
    """Everything that defines the analysis, and nothing that depends on results."""
    return {
        "plan_version": 1,
        "data_file": Path(session.data_path).name if session.data_path else None,
        "data_sha256": file_sha256(session.data_path) if session.data_path else None,
        "y": session.y,
        "x": session.x,
        "family": session.family,
        "decisions": [decision_to_dict(d) for d in session.decisions],
        "guardrails": {k: answers_to_dict(v) for k, v in sorted(session.guardrails.items())},
        "seed": session.seed,
        "alpha": session.alpha,
        "max_specs": session.max_specs,
        "sample_if_over": session.sample_if_over,
        "n_permutations": session.n_permutations,
    }


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def plan_hash(session: Session) -> str:
    return hashlib.sha256(canonical_json(plan_dict(session)).encode("utf-8")).hexdigest()


def lock_plan(session: Session) -> BlindLock:
    """Canonical JSON (sorted keys, no whitespace) -> SHA-256, UTC ISO-8601 timestamp."""
    plan = plan_dict(session)
    digest = hashlib.sha256(canonical_json(plan).encode("utf-8")).hexdigest()
    locked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return BlindLock(plan=plan, sha256=digest, locked_at=locked_at)


def verify_plan(session: Session, lock: BlindLock) -> bool:
    """True when the session's current plan hashes to ``lock.sha256``."""
    return plan_hash(session) == lock.sha256

"""Public API of the core library - the ONLY module the GUI imports from core.

Typical script use (no GUI)::

    from multiverse_studio.core import api
    from multiverse_studio.io.loaders import load_table

    df = load_table("survey.csv")
    profile = api.profile_data(df)
    family = api.suggest_family(profile, "grade")
    decisions = api.suggest_decisions(profile, "grade", "sleep_hours", df)
    specs = api.build_specs(decisions, max_specs=1000, seed=42)
    results = api.run_multiverse(df, "grade", "sleep_hours", family, decisions, specs)
    verdict = api.summarize(results)

See docs/architecture.md for the full workflow and ownership.
"""

from __future__ import annotations

from .blind import blind_view, lock_plan, plan_dict, plan_hash, verify_plan
from .cherry import cherry_pick_check
from .choices import suggest_decisions, validate_question
from .guardrails import (
    assess_control,
    assess_controls,
    conditioned_on,
    controls_of,
    mark_validity,
    variables_to_assess,
)
from .importance import decision_importance
from .inference import count_significant, permutation_test, summarize
from .models import fit_one, prepare_data
from .narrative import methods_paragraph, results_paragraph
from .profiling import detect_kind, profile_data, suggest_family
from .runner import Cancelled, iter_multiverse, run_multiverse
from .seed import rng_for
from .serialize import session_from_dict, session_to_dict
from .simulate import SCENARIOS, simulate
from .specs import build_specs, count_specs

__all__ = [
    "SCENARIOS",
    "Cancelled",
    "assess_control",
    "assess_controls",
    "blind_view",
    "build_specs",
    "cherry_pick_check",
    "conditioned_on",
    "controls_of",
    "count_significant",
    "count_specs",
    "decision_importance",
    "detect_kind",
    "fit_one",
    "iter_multiverse",
    "lock_plan",
    "mark_validity",
    "methods_paragraph",
    "permutation_test",
    "plan_dict",
    "plan_hash",
    "prepare_data",
    "profile_data",
    "results_paragraph",
    "rng_for",
    "run_multiverse",
    "session_from_dict",
    "session_to_dict",
    "simulate",
    "suggest_decisions",
    "suggest_family",
    "summarize",
    "validate_question",
    "variables_to_assess",
    "verify_plan",
]

"""Teaching simulator: datasets with a known truth. Owner: A (Core).

Used three ways: (1) a classroom mode in the GUI, (2) ground-truth tests for
the engine, (3) the "teaching" use case in the report's impact section.
Extends the idea of Schönbrodt's p-hacker app to multiverse analysis.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from .seed import rng_for

Scenario = Literal["no_effect", "real_effect", "confounded", "mediated", "collider"]
SCENARIOS: dict[str, str] = {
    "no_effect": "Sleep has no effect on grades.",
    "real_effect": "Each extra hour of sleep raises the grade by 3 points.",
    "confounded": "Sleep has no direct effect; study time drives both sleep and grades.",
    "mediated": "Sleep raises grades partly by reducing tiredness (tiredness is a bad control).",
    "collider": "No effect, but sleep and grades both affect a scholarship (a bad control).",
}


def simulate(scenario: Scenario, n: int = 300, seed: int = 0) -> pd.DataFrame:
    """Generate a student dataset where the true sleep -> grade effect is known.

    Columns: sleep_hours, grade, study_hours, has_job ("yes"/"no"), tiredness (1-5),
    [scholarship (0/1), collider scenario only], year (1-4), coffee_cups.
    About 2% of sleep_hours is missing and a few grades are extreme, so the
    suggested choices are realistic.

    ``df.attrs["true_effect"]`` holds the true *total* effect of one extra hour
    of sleep on grade; ``df.attrs["scenario"]`` and ``df.attrs["description"]``
    describe the scenario.
    """
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'. Choose one of {list(SCENARIOS)}.")
    if n < 30:
        raise ValueError("Simulate at least 30 students.")
    rng = rng_for(seed, "simulator")

    study = np.clip(rng.normal(3.0, 1.0, n), 0, 8)
    job = rng.binomial(1, 0.3, n)
    year = rng.integers(1, 5, n)
    coffee = rng.poisson(1.5, n)
    noise_sleep = rng.normal(0, 0.9, n)
    noise_grade = rng.normal(0, 8.0, n)
    noise_tired = rng.normal(0, 0.6, n)

    sleep = 7.0 - 0.8 * job + noise_sleep
    tired = 3.0 + noise_tired
    true_effect = 0.0

    if scenario == "no_effect":
        grade = 55 + 5 * study - 3 * job + noise_grade
    elif scenario == "real_effect":
        true_effect = 3.0
        grade = 35 + 3.0 * sleep + 5 * study - 3 * job + noise_grade
    elif scenario == "confounded":
        sleep = 5.0 + 0.6 * study - 0.8 * job + noise_sleep
        grade = 55 + 6 * study - 3 * job + noise_grade
    elif scenario == "mediated":
        tired = 7.0 - 0.6 * sleep + noise_tired
        # direct 1.0 + indirect (-0.6 * -4.0 = 2.4) -> total 3.4
        true_effect = 3.4
        grade = 70 + 1.0 * sleep - 4.0 * tired + 5 * study - 3 * job + noise_grade
    else:  # collider
        grade = 55 + 5 * study - 3 * job + noise_grade

    latent = 0.8 * (sleep - sleep.mean()) + 0.15 * (grade - grade.mean()) + rng.normal(0, 0.5, n)
    scholarship = (latent > np.quantile(latent, 0.7)).astype(int)

    # Column order matters: the first candidate columns become the suggested
    # controls, so the scenario's "trap" variable is placed early.
    columns: dict[str, object] = {
        "sleep_hours": np.round(np.clip(sleep, 2, 12), 1),
        "grade": np.round(np.clip(grade, 0, 100), 1),
        "study_hours": np.round(study, 1),
        "has_job": np.where(job == 1, "yes", "no"),
        "tiredness": np.clip(np.round(tired), 1, 5).astype(int),
    }
    if scenario == "collider":
        columns["scholarship"] = scholarship
    columns["year"] = year
    columns["coffee_cups"] = coffee
    df = pd.DataFrame(columns)
    # realistic mess: a few extreme grades and ~2% missing sleep answers
    extreme = rng.choice(n, size=max(2, n // 100), replace=False)
    df.loc[extreme, "grade"] = np.where(df.loc[extreme, "grade"] > 50, 100.0, 5.0)
    missing = rng.choice(n, size=max(1, n // 50), replace=False)
    df.loc[missing, "sleep_hours"] = np.nan

    df.attrs["scenario"] = scenario
    df.attrs["description"] = SCENARIOS[scenario]
    df.attrs["true_effect"] = true_effect
    return df

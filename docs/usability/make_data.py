"""Write the two study datasets and the answer key (simulated data, safe to share).

Run from the repo root:  python docs/usability/make_data.py

Set A uses the "confounded" scenario: the sleep effect disappears once study hours
are kept equal. Set B uses "real_effect": it stays in all four analyses.

Seed rule, using the data only (never the app's verdict): take the first seed from 1
upward where
  1. the app suggests exactly the two choices of the task,
  2. removing values beyond 3 SD removes at least one student, and
  3. every p-value is below 0.001 or above 0.5, in the pattern the scenario implies,
     so that no answer depends on rounding or on a borderline result.
The rule favours clear-cut data. Say so when reporting the study.
"""

from __future__ import annotations

import json
from pathlib import Path

from multiverse_studio.core import api
from multiverse_studio.core.types import Decision, DecisionKind, Option, Spec

# set -> (scenario, which of ways 1 to 4 should show a clear effect)
SETS = {
    "A": ("confounded", (True, False, True, False)),
    "B": ("real_effect", (True, True, True, True)),
}
COLUMNS = ["grade", "sleep_hours", "study_hours"]  # X columns side by side, as Excel needs
ALPHA = 0.05
DECISIONS = [
    Decision(
        "outliers",
        DecisionKind.OUTLIERS,
        "Extreme values",
        (
            Option("none", "Keep all", {"rule": "none"}),
            Option(
                "sd3",
                "Drop beyond 3 SD",
                {"rule": "sd", "k": 3.0, "columns": ["sleep_hours", "grade"]},
            ),
        ),
    ),
    Decision(
        "controls",
        DecisionKind.CONTROLS,
        "Things to keep equal",
        (
            Option("none", "Nothing", {"columns": []}),
            Option("c1", "study_hours", {"columns": ["study_hours"]}),
        ),
    ),
]
# "Way" number on the task sheet -> (extreme values, study hours)
WAYS = {1: ("none", "none"), 2: ("none", "c1"), 3: ("sd3", "none"), 4: ("sd3", "c1")}


def dataset(scenario: str, seed: int):
    df = api.simulate(scenario, n=200, seed=seed)
    return df[COLUMNS].dropna().reset_index(drop=True)


def fit_ways(df) -> dict:
    return {
        way: api.fit_one(
            df,
            "grade",
            "sleep_hours",
            "linear",
            DECISIONS,
            Spec(way, {"outliers": outliers, "controls": controls}),
        )
        for way, (outliers, controls) in WAYS.items()
    }


def suitable(df, pattern: tuple[bool, ...]) -> bool:
    """The three conditions of the seed rule."""
    profile = api.profile_data(df)
    suggested = api.suggest_decisions(profile, "grade", "sleep_hours", df)
    if [d.id for d in suggested] != ["outliers", "controls"]:
        return False
    fits = fit_ways(df)
    if fits[3].n_obs == fits[1].n_obs:
        return False
    return all(
        r.p_value < 0.001 if clear else r.p_value > 0.5
        for r, clear in zip(fits.values(), pattern, strict=True)
    )


def first_seed(scenario: str, pattern: tuple[bool, ...]) -> int:
    for seed in range(1, 1000):
        if suitable(dataset(scenario, seed), pattern):
            return seed
    raise RuntimeError(f"No suitable seed for {scenario}.")


def answers(df) -> dict:
    fits = fit_ways(df)
    clear = {way: r.p_value < ALPHA for way, r in fits.items()}
    if clear[1] != clear[2] or clear[3] != clear[4]:
        changes = "study hours"
    elif clear[1] != clear[3] or clear[2] != clear[4]:
        changes = "extreme values"
    else:
        changes = "neither"
    return {
        "q1": round(fits[1].estimate, 2),
        "q2": round(fits[2].estimate, 2),
        "q3": sum(clear.values()),
        "q4": changes,
        "ways": {
            str(way): {
                "effect": round(r.estimate, 3),
                "p": float(f"{r.p_value:.3g}"),
                "rows": r.n_obs,
            }
            for way, r in fits.items()
        },
    }


def main(folder: Path = Path(__file__).parent / "data") -> None:
    folder.mkdir(parents=True, exist_ok=True)
    key = {}
    for name, (scenario, pattern) in SETS.items():
        seed = first_seed(scenario, pattern)
        df = dataset(scenario, seed)
        df.to_csv(folder / f"study_{name.lower()}.csv", index=False, lineterminator="\n")
        key[name] = {"scenario": scenario, "seed": seed, **answers(df)}
    (folder / "answer_key.json").write_text(
        json.dumps(key, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(key, indent=2))


if __name__ == "__main__":
    main()

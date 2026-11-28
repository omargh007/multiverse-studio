"""Check results.csv and write summary.md. Standard library only.

Run from the repo root:  python docs/usability/score.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean, median

HERE = Path(__file__).parent
TOOLS = ("app", "excel")
NAMES = {"app": "Multiverse Studio", "excel": "Excel"}
TIME_LIMIT = 900
TOLERANCE = 0.01  # answers are written with 2 decimals; allows rounding or cutting off
Q4_ANSWERS = ("extreme values", "study hours", "neither")


def sus(answers: list[int]) -> float:
    """System Usability Scale score (0 to 100) from ten answers of 1 to 5 (Brooke, 1996)."""
    if len(answers) != 10 or any(a not in range(1, 6) for a in answers):
        raise ValueError("SUS needs ten answers, each from 1 to 5.")
    # odd items are worded positively, even items negatively
    return 2.5 * sum(a - 1 if i % 2 == 0 else 5 - a for i, a in enumerate(answers))


def n_correct(row: dict, tool: str, key: dict) -> int:
    score = 0
    for q in ("q1", "q2", "q3", "q4"):
        given = (row[f"{tool}_{q}"] or "").strip().lower()
        if not given:
            continue
        if q == "q4":
            if given not in Q4_ANSWERS:
                raise ValueError(f"{tool}_q4 must be one of {', '.join(Q4_ANSWERS)}.")
            score += given == key[q]
            continue
        try:
            number = float(given.replace(",", "."))
        except ValueError:
            raise ValueError(f"{tool}_{q} must be a number, not '{given}'.") from None
        slack = TOLERANCE if q in ("q1", "q2") else 0
        score += abs(number - key[q]) <= slack + 1e-9
    return score


def read_row(row: dict, key: dict) -> dict:
    """One participant, checked and scored."""
    if row["first_tool"] not in TOOLS:
        raise ValueError("first_tool must be 'app' or 'excel'.")
    if {row["app_set"], row["excel_set"]} != {"A", "B"}:
        raise ValueError("app_set and excel_set must be A and B, one each.")
    ran = (row["app_analyses"] or "").strip()
    out = {"participant": row["participant"], "app_analyses": int(ran) if ran else None}
    for tool in TOOLS:
        done = row[f"{tool}_completed"].strip().lower()
        if done not in ("yes", "no"):
            raise ValueError(f"{tool}_completed must be 'yes' or 'no'.")
        seconds = int(row[f"{tool}_seconds"])
        if not 0 < seconds <= TIME_LIMIT:
            raise ValueError(f"{tool}_seconds must be between 1 and {TIME_LIMIT}.")
        out[tool] = {
            "seconds": seconds,
            "completed": done == "yes",
            "correct": n_correct(row, tool, key[row[f"{tool}_set"]]),
            "sus": sus([int(row[f"sus_{tool}_{i}"]) for i in range(1, 11)]),
            "set": row[f"{tool}_set"],
            "first": row["first_tool"] == tool,
        }
    return out


def _times(runs: list[dict]) -> str:
    if not runs:
        return "none"
    values = [r["seconds"] for r in runs]
    return f"{median(values):.0f} ({min(values)} to {max(values)})"


def summarize(people: list[dict]) -> str:
    n = len(people)
    lines = [
        "# Usability results",
        "",
        f"Participants: {n}. With a group this small these numbers describe these people only.",
        "",
        "| Measure | " + " | ".join(NAMES[t] for t in TOOLS) + " |",
        "|---|" + "---|" * len(TOOLS),
    ]

    def row(name, show):
        cells = [show([p[tool] for p in people]) for tool in TOOLS]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")

    row("Time in seconds, median (range)", _times)
    row(
        "Time when all 4 answers were correct",
        lambda rs: _times([r for r in rs if r["correct"] == 4]),
    )
    row("Finished within 15 minutes", lambda rs: f"{sum(r['completed'] for r in rs)} of {n}")
    row("Correct answers out of 4, mean", lambda rs: f"{mean(r['correct'] for r in rs):.1f}")
    row("All 4 answers correct", lambda rs: f"{sum(r['correct'] == 4 for r in rs)} of {n}")
    row(
        "SUS score 0 to 100, mean (range)",
        lambda rs: (
            f"{mean(r['sus'] for r in rs):.1f} "
            f"({min(r['sus'] for r in rs):g} to {max(r['sus'] for r in rs):g})"
        ),
    )

    both = [p for p in people if p["app"]["completed"] and p["excel"]["completed"]]
    lines.append("")
    if both:
        diff = median(p["excel"]["seconds"] - p["app"]["seconds"] for p in both)
        faster = sum(p["app"]["seconds"] < p["excel"]["seconds"] for p in both)
        lines.append(
            f"Faster with the app: {faster} of the {len(both)} who finished both tasks. "
            f"Median time of Excel minus app: {diff:+.0f} seconds."
        )
    else:
        lines.append("Nobody finished both tasks, so times can't be compared person by person.")
    ran = [p["app_analyses"] for p in people if p["app_analyses"] is not None]
    lines.append(
        f"Ran exactly the four analyses in the app: {ran.count(4)} of the {len(ran)} who ran any."
    )

    lines += [
        "",
        "## Check for dataset and order effects",
        "The rows for the first task compare different people who had not yet seen the task.",
        "",
        "| Group | Tool | People | Median seconds | Mean correct |",
        "|---|---|---|---|---|",
    ]
    groups = (
        ("Set A", lambda r: r["set"] == "A"),
        ("Set B", lambda r: r["set"] == "B"),
        ("First task", lambda r: r["first"]),
        ("Second task", lambda r: not r["first"]),
    )
    for label, wanted in groups:
        for tool in TOOLS:
            runs = [p[tool] for p in people if wanted(p[tool])]
            seconds = f"{median(r['seconds'] for r in runs):.0f}" if runs else "none"
            correct = f"{mean(r['correct'] for r in runs):.1f}" if runs else "none"
            lines.append(f"| {label} | {NAMES[tool]} | {len(runs)} | {seconds} | {correct} |")
    lines += ["", "Times of 900 seconds mean the limit was reached.", ""]
    return "\n".join(lines)


def main(results: Path = HERE / "results.csv") -> None:
    key = json.loads((HERE / "data" / "answer_key.json").read_text(encoding="utf-8"))
    with results.open(newline="", encoding="utf-8-sig") as f:  # -sig: Excel adds a BOM
        rows = [r for r in csv.DictReader(f) if (r["participant"] or "").strip()]
    if not rows:
        raise SystemExit(f"No participants in {results} yet.")
    people = []
    for r in rows:
        try:
            people.append(read_row(r, key))
        except (ValueError, KeyError) as exc:
            raise SystemExit(f"Row {r['participant']}: {exc}") from None
    codes = [p["participant"] for p in people]
    if len(set(codes)) != len(codes):
        raise SystemExit("Each participant code must appear once.")
    text = summarize(people)
    (results.parent / "summary.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()

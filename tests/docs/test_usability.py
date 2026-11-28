"""The usability study kit: scoring is right and the data matches the answer key."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

KIT = Path(__file__).resolve().parents[2] / "docs" / "usability"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"usability_{name}", KIT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


score = _load("score")
make_data = _load("make_data")
KEY = json.loads((KIT / "data" / "answer_key.json").read_text(encoding="utf-8"))


def test_committed_data_and_key_match_the_generator(tmp_path):
    make_data.main(tmp_path)
    for name in ("study_a.csv", "study_b.csv"):
        pd.testing.assert_frame_equal(
            pd.read_csv(tmp_path / name), pd.read_csv(KIT / "data" / name)
        )
    assert json.loads((tmp_path / "answer_key.json").read_text(encoding="utf-8")) == KEY


def test_the_two_sets_have_the_intended_answers():
    assert (KEY["A"]["q3"], KEY["A"]["q4"]) == (2, "study hours")
    assert (KEY["B"]["q3"], KEY["B"]["q4"]) == (4, "neither")
    # no p-value sits near the 0.05 line, so rounding can't change an answer
    for data in KEY.values():
        assert all(w["p"] < 0.001 or w["p"] > 0.5 for w in data["ways"].values())


def test_sus():
    assert score.sus([3] * 10) == 50
    assert score.sus([5, 1] * 5) == 100
    assert score.sus([1, 5] * 5) == 0
    with pytest.raises(ValueError):
        score.sus([3] * 9)
    with pytest.raises(ValueError):
        score.sus([6] + [3] * 9)


def _row(participant, app_set="A", app_seconds=200, excel_seconds=900, excel_completed="no"):
    excel_set = "B" if app_set == "A" else "A"
    row = {
        "participant": participant,
        "first_tool": "app",
        "app_set": app_set,
        "excel_set": excel_set,
        "app_analyses": "4",
        "app_seconds": str(app_seconds),
        "app_completed": "yes",
        "excel_seconds": str(excel_seconds),
        "excel_completed": excel_completed,
    }
    for q in ("q1", "q2", "q3", "q4"):
        row[f"app_{q}"] = str(KEY[app_set][q])
        row[f"excel_{q}"] = ""
    for i in range(1, 11):
        row[f"sus_app_{i}"] = "5" if i % 2 else "1"
        row[f"sus_excel_{i}"] = "3"
    return row


def test_scoring_a_participant():
    row = _row("P01")
    row["excel_q1"] = f"{KEY['B']['q1'] - 0.01:.2f}".replace(".", ",")  # comma decimals are fine
    row["excel_q2"] = str(KEY["B"]["q2"] + 0.2)  # too far off
    row["excel_q4"] = "Neither"
    person = score.read_row(row, KEY)
    app = person["app"]
    assert (app["seconds"], app["correct"], app["sus"], app["set"]) == (200, 4, 100, "A")
    assert app["first"] and not person["excel"]["first"]
    assert person["excel"]["correct"] == 2 and person["excel"]["sus"] == 50


@pytest.mark.parametrize(
    "field, value",
    [
        ("first_tool", "pen"),
        ("excel_set", "A"),
        ("app_completed", ""),
        ("app_seconds", "901"),
        ("app_q1", "about three"),
        ("sus_app_1", "0"),
        ("app_q4", "study hour"),
    ],
)
def test_bad_rows_are_rejected(field, value):
    row = _row("P01")
    row[field] = value
    with pytest.raises(ValueError):
        score.read_row(row, KEY)


def test_summary_file(tmp_path, capsys):
    rows = [
        _row("P01"),
        _row("P02", app_set="B", app_seconds=300, excel_seconds=800, excel_completed="yes"),
    ]
    results = tmp_path / "results.csv"
    with results.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    score.main(results)
    text = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "| Time in seconds, median (range) | 250 (200 to 300) | 850 (800 to 900) |" in text
    assert "| Finished within 15 minutes | 2 of 2 | 1 of 2 |" in text
    assert "| Time when all 4 answers were correct | 250 (200 to 300) | none |" in text
    assert "Ran exactly the four analyses in the app: 2 of the 2 who ran any." in text
    assert "| First task | Multiverse Studio | 2 | 250 | 4.0 |" in text
    assert "| First task | Excel | 0 | none | none |" in text
    assert "Faster with the app: 1 of the 1 who finished both tasks." in text
    assert "+500 seconds" in text

    results.write_text(results.read_text(encoding="utf-8-sig").replace("P02", "P01"), "utf-8")
    with pytest.raises(SystemExit, match="must appear once"):
        score.main(results)


def test_the_neighbouring_way_is_not_accepted():
    """An effect read from the wrong analysis must not count as correct."""
    for name, data in KEY.items():
        row = _row("P01", app_set=name)
        row["app_q1"] = f"{data['ways']['3']['effect']:.2f}"
        assert score.n_correct(row, "app", data) == 3


def test_template_has_every_column():
    header = (KIT / "results.csv").read_text(encoding="utf-8").splitlines()[0].split(",")
    assert set(_row("P01")) <= set(header)

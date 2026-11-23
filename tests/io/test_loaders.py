from __future__ import annotations

import pandas as pd
import pytest

from multiverse_studio.io.loaders import DataLoadError, load_table


def test_load_csv_semicolon(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text(" a ;b\n1;2\n3;4\n", encoding="utf-8")
    df = load_table(f)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2


def test_load_excel(tmp_path):
    f = tmp_path / "d.xlsx"
    pd.DataFrame({"x": [1, 2], "y": [3, 4]}).to_excel(f, index=False)
    assert load_table(f).shape == (2, 2)


def test_drops_empty_rows_and_columns(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text("a,b,c\n1,2,\n,,\n3,4,\n", encoding="utf-8")
    df = load_table(f)
    assert list(df.columns) == ["a", "b"] and len(df) == 2


@pytest.mark.parametrize(
    "name,content,msg",
    [
        ("d.json", "{}", "not a supported"),
        ("e.csv", "a,b\n", "no data rows"),
    ],
)
def test_bad_files(tmp_path, name, content, msg):
    f = tmp_path / name
    f.write_text(content, encoding="utf-8")
    with pytest.raises(DataLoadError, match=msg):
        load_table(f)


def test_missing_file(tmp_path):
    with pytest.raises(DataLoadError, match="not found"):
        load_table(tmp_path / "nope.csv")

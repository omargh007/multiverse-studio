"""Load tabular data from CSV or Excel."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SUPPORTED = {".csv", ".tsv", ".txt", ".xlsx", ".xls"}


class DataLoadError(ValueError):
    """Raised with a plain-language message the GUI can show as-is."""


def load_table(path: str | Path, sheet: str | int = 0) -> pd.DataFrame:
    """Read a CSV/TSV/Excel file into a DataFrame.

    * CSV delimiter is sniffed (comma, semicolon, tab).
    * Column names are stripped of surrounding whitespace.
    * Fully empty rows and columns are dropped.
    """
    path = Path(path)
    if not path.exists():
        raise DataLoadError(f"File not found: {path}")
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise DataLoadError(
            f"'{path.name}' is not a supported file. Please use CSV or Excel (.xlsx)."
        )
    try:
        if suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(path, sheet_name=sheet)
        else:
            df = pd.read_csv(path, sep=None, engine="python")
    except Exception as exc:  # pragma: no cover - message depends on pandas internals
        raise DataLoadError(f"Could not read '{path.name}': {exc}") from exc

    df = df.dropna(how="all").dropna(axis=1, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    if df.empty:
        raise DataLoadError(f"'{path.name}' has no data rows.")
    if len(set(df.columns)) != len(df.columns):
        raise DataLoadError(f"'{path.name}' has duplicate column names.")
    return df

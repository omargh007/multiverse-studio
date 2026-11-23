from __future__ import annotations

import pytest

from multiverse_studio.core.types import (
    ColumnInfo,
    ColumnKind,
    DataProfile,
    Session,
    SpecResult,
)


def test_profile_lookup():
    p = DataProfile(n_rows=3, columns=(ColumnInfo("a", ColumnKind.NUMERIC, 0, 3),))
    assert p.column("a").kind is ColumnKind.NUMERIC
    assert p.names == ["a"]
    with pytest.raises(KeyError):
        p.column("b")


def test_decision_option_lookup(three_decisions):
    assert three_decisions[1].option("study").params == {"columns": ["study_hours"]}
    with pytest.raises(KeyError):
        three_decisions[1].option("nope")


def test_spec_result_ok():
    good = SpecResult(0, {}, 0.5, 0.1, 0.01, 0.3, 0.7, 100)
    bad = SpecResult(1, {}, None, None, None, None, None, 5, error="Too few rows")
    assert good.ok and not bad.ok


def test_session_defaults_are_independent():
    a, b = Session(), Session()
    a.decisions.append("x")  # type: ignore[arg-type]
    assert b.decisions == []

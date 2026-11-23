"""Convert contract types to and from plain dicts (JSON-safe).

Used by blind mode (plan hashing), the exported Python script, session files
and the JSON report, so all of them agree on one representation.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .types import (
    BlindLock,
    CausalRole,
    CherryPickResult,
    ColumnInfo,
    ColumnKind,
    ControlAssessment,
    DataProfile,
    Decision,
    DecisionKind,
    GuardrailAnswers,
    Option,
    Session,
    Spec,
    SpecResult,
    Verdict,
)


def decision_to_dict(d: Decision) -> dict[str, Any]:
    return {
        "id": d.id,
        "kind": d.kind.value,
        "label": d.label,
        "explanation": d.explanation,
        "options": [{"id": o.id, "label": o.label, "params": dict(o.params)} for o in d.options],
    }


def decision_from_dict(data: dict[str, Any]) -> Decision:
    return Decision(
        id=data["id"],
        kind=DecisionKind(data["kind"]),
        label=data["label"],
        explanation=data.get("explanation", ""),
        options=tuple(
            Option(o["id"], o["label"], dict(o.get("params", {}))) for o in data["options"]
        ),
    )


def answers_to_dict(a: GuardrailAnswers) -> dict[str, bool | None]:
    return asdict(a)


def answers_from_dict(data: dict[str, Any]) -> GuardrailAnswers:
    return GuardrailAnswers(
        happens_before_x=data.get("happens_before_x"),
        could_be_caused_by_x=data.get("could_be_caused_by_x"),
        could_be_caused_by_y=data.get("could_be_caused_by_y"),
    )


def result_to_dict(r: SpecResult) -> dict[str, Any]:
    return asdict(r)


def result_from_dict(data: dict[str, Any]) -> SpecResult:
    return SpecResult(**data)


def profile_to_dict(p: DataProfile) -> dict[str, Any]:
    return {
        "n_rows": p.n_rows,
        "columns": [{**asdict(c), "kind": c.kind.value} for c in p.columns],
    }


def profile_from_dict(data: dict[str, Any]) -> DataProfile:
    cols = tuple(ColumnInfo(**{**c, "kind": ColumnKind(c["kind"])}) for c in data["columns"])
    return DataProfile(n_rows=data["n_rows"], columns=cols)


def session_to_dict(s: Session) -> dict[str, Any]:
    """Full session, including results. JSON-safe."""
    return {
        "format": "multiverse-studio-session",
        "version": 1,
        "data_path": s.data_path,
        "profile": profile_to_dict(s.profile) if s.profile else None,
        "y": s.y,
        "x": s.x,
        "family": s.family,
        "decisions": [decision_to_dict(d) for d in s.decisions],
        "guardrails": {k: answers_to_dict(v) for k, v in s.guardrails.items()},
        "assessments": [{**asdict(a), "role": a.role.value} for a in s.assessments],
        "seed": s.seed,
        "alpha": s.alpha,
        "max_specs": s.max_specs,
        "sample_if_over": s.sample_if_over,
        "n_permutations": s.n_permutations,
        "blind": asdict(s.blind) if s.blind else None,
        "specs": [asdict(sp) for sp in s.specs],
        "results": [result_to_dict(r) for r in s.results],
        "verdict": asdict(s.verdict) if s.verdict else None,
        "reported_estimate": s.reported_estimate,
        "cherry_pick": asdict(s.cherry_pick) if s.cherry_pick else None,
        "notes": s.notes,
    }


def session_from_dict(data: dict[str, Any]) -> Session:
    if data.get("format") != "multiverse-studio-session":
        raise ValueError("This file is not a Multiverse Studio session.")
    return Session(
        data_path=data.get("data_path"),
        profile=profile_from_dict(data["profile"]) if data.get("profile") else None,
        y=data.get("y"),
        x=data.get("x"),
        family=data.get("family"),
        decisions=[decision_from_dict(d) for d in data.get("decisions", [])],
        guardrails={k: answers_from_dict(v) for k, v in data.get("guardrails", {}).items()},
        assessments=[
            ControlAssessment(**{**a, "role": CausalRole(a["role"])})
            for a in data.get("assessments", [])
        ],
        seed=data.get("seed", Session.seed),
        alpha=data.get("alpha", Session.alpha),
        max_specs=data.get("max_specs", Session.max_specs),
        sample_if_over=data.get("sample_if_over", Session.sample_if_over),
        n_permutations=data.get("n_permutations", Session.n_permutations),
        blind=BlindLock(**data["blind"]) if data.get("blind") else None,
        specs=[Spec(**sp) for sp in data.get("specs", [])],
        results=[result_from_dict(r) for r in data.get("results", [])],
        verdict=Verdict(**data["verdict"]) if data.get("verdict") else None,
        reported_estimate=data.get("reported_estimate"),
        cherry_pick=CherryPickResult(**data["cherry_pick"]) if data.get("cherry_pick") else None,
        notes=data.get("notes", ""),
    )

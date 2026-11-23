"""Causal guardrails: flag bad controls. Owner: A (Core).  [NOVEL FEATURE]

Based on Cinelli, Forney & Pearl, "A Crash Course in Good and Bad Controls"
(Sociological Methods & Research, 2022). The user answers three plain questions
per candidate control (GuardrailAnswers); these rules map answers to a role:

  caused_by_x  caused_by_y  before_x  ->  role            keep?
  -----------  -----------  --------      -------------   -----
  True         True         any           COLLIDER        no
  True         False/None   any           MEDIATOR        no
  False/None   True         any           OUTCOME_PROXY   no
  False        False        True          CONFOUNDER      yes
  False        False        False/None    NEUTRAL         yes
  anything else (some None) ->            UNKNOWN         yes (flagged)

Universes whose control set contains a "keep=False" variable are marked
``valid=False``; the verdict uses valid universes only, and the GUI shows
"all universes" vs "causally valid universes".
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace

from .types import (
    CausalRole,
    ControlAssessment,
    Decision,
    DecisionKind,
    GuardrailAnswers,
    SpecResult,
)


def assess_control(variable: str, answers: GuardrailAnswers) -> ControlAssessment:
    """Apply the rule table above to one variable, with a plain-language reason."""
    by_x = answers.could_be_caused_by_x
    by_y = answers.could_be_caused_by_y
    before = answers.happens_before_x

    if by_x is True and by_y is True:
        return ControlAssessment(
            variable,
            CausalRole.COLLIDER,
            False,
            f"{variable} is caused by both the factor and the outcome (a collider). "
            "Keeping it equal creates a fake link.",
        )
    if by_x is True:
        return ControlAssessment(
            variable,
            CausalRole.MEDIATOR,
            False,
            f"{variable} is caused by the factor and lies on its path to the outcome "
            "(a mediator). Keeping it equal hides part of the real effect.",
        )
    if by_y is True:
        return ControlAssessment(
            variable,
            CausalRole.OUTCOME_PROXY,
            False,
            f"{variable} is caused by the outcome. Keeping it equal distorts the effect.",
        )
    if by_x is False and by_y is False:
        if before is True:
            return ControlAssessment(
                variable,
                CausalRole.CONFOUNDER,
                True,
                f"{variable} comes first and may affect both (a confounder). "
                "Keeping it equal makes the comparison fairer.",
            )
        return ControlAssessment(
            variable,
            CausalRole.NEUTRAL,
            True,
            f"{variable} is not caused by the factor or the outcome, so it is safe to keep equal.",
        )
    return ControlAssessment(
        variable,
        CausalRole.UNKNOWN,
        True,
        f"Not sure about {variable}: it is kept, but the result should be read with care.",
    )


def assess_controls(answers: Mapping[str, GuardrailAnswers]) -> list[ControlAssessment]:
    return [assess_control(v, a) for v, a in answers.items()]


def controls_of(result: SpecResult, decisions: Sequence[Decision]) -> list[str]:
    """Control variables used by one universe."""
    for d in decisions:
        if d.kind is DecisionKind.CONTROLS and d.id in result.choices:
            return list(d.option(result.choices[d.id]).params.get("columns", []))
    return []


def subsets_of(result: SpecResult, decisions: Sequence[Decision]) -> list[str]:
    """Columns that one universe restricts to a single level (subset choices)."""
    cols = []
    for d in decisions:
        if d.kind is DecisionKind.SUBSET and d.id in result.choices:
            col = d.option(result.choices[d.id]).params.get("column")
            if col is not None:
                cols.append(col)
    return cols


def conditioned_on(result: SpecResult, decisions: Sequence[Decision]) -> set[str]:
    """Everything a universe conditions on: its controls and its subset columns.

    Restricting the data to one level of a variable conditions on it just like
    controlling for it, so a bad control is also a bad subset (selection bias).
    """
    return set(controls_of(result, decisions)) | set(subsets_of(result, decisions))


def mark_validity(
    results: Sequence[SpecResult],
    decisions: Sequence[Decision],
    assessments: Sequence[ControlAssessment],
) -> list[SpecResult]:
    """Return copies of ``results`` with ``valid`` set according to the assessments.

    A universe is invalid when it controls for, or subsets on, a variable whose
    assessment says ``keep=False``.
    """
    bad = {a.variable for a in assessments if not a.keep}
    return [replace(r, valid=not (conditioned_on(r, decisions) & bad)) for r in results]


def variables_to_assess(decisions: Sequence[Decision]) -> list[str]:
    """Variables the GUI should ask the three guardrail questions about."""
    out: list[str] = []
    for d in decisions:
        if d.kind is DecisionKind.CONTROLS:
            for o in d.options:
                out += o.params.get("columns", [])
        elif d.kind is DecisionKind.SUBSET:
            out += [o.params["column"] for o in d.options if o.params.get("column")]
    return list(dict.fromkeys(out))

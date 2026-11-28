"""Plain-language wording shared by the app and the PDF report."""

from __future__ import annotations

VERDICT_WORDS = {
    # label: (callout kind, headline, one-line meaning)
    "consistent": ("good", "Consistent", "it holds up across reasonable analyses"),
    "mixed": ("warning", "Depends on choices", "the answer changes with the analysis"),
    "fragile": ("critical", "Fragile", "it does not hold up across reasonable analyses"),
}

UNIT_WORDS = {
    "linear": "points of {y} for each one-unit increase in {x}",
    "logistic": "change in the log-odds of {y} for each one-unit increase in {x}",
    "poisson": "change in the log count of {y} for each one-unit increase in {x}",
}

ROLE_WORDS = {
    "confounder": "Fair to keep equal",
    "neutral": "Fair to keep equal",
    "unknown": "Kept, but flagged",
    "mediator": "Unfair: left out",
    "collider": "Unfair: left out",
    "outcome_proxy": "Unfair: left out",
}

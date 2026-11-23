"""Auto-written Methods and Results paragraphs (offline templates, no AI). Owner: A (Core)."""

from __future__ import annotations

from .specs import count_specs
from .types import Session

MODEL_NAMES = {
    "linear": "linear regression (OLS)",
    "logistic": "logistic regression",
    "poisson": "Poisson regression",
}


def _join(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def methods_paragraph(session: Session) -> str:
    """Methods text: method, model, decisions, guardrails, inference, seed, blind lock."""
    if not (session.x and session.y):
        raise ValueError("Pick an outcome and a factor first.")
    n_specs = len(session.specs) or count_specs(session.decisions)
    forks = [f"{d.label.lower()} ({len(d.options)} options)" for d in session.decisions]
    text = [
        "We conducted a specification curve (multiverse) analysis (Simonsohn, Simmons & "
        f"Nelson, 2020) of the association between {session.x} and {session.y}, "
        f"using {MODEL_NAMES.get(session.family or '', 'regression')}."
    ]
    if forks:
        text.append(f"Specifications varied {_join(forks)}, giving {n_specs} specifications.")
    else:
        text.append("A single specification was estimated.")
    if total := count_specs(session.decisions):
        if session.specs and len(session.specs) < total:
            text.append(
                f"Because the full grid had {total} specifications, a random sample of "
                f"{len(session.specs)} was analysed."
            )
    bad = [a for a in session.assessments if not a.keep]
    if bad:
        roles = _join([f"{a.variable} ({a.role.value})" for a in bad])
        text.append(
            "Following the good- and bad-control criteria of Cinelli, Forney and Pearl (2022), "
            f"specifications adjusting for {roles} were excluded from inference."
        )
    text.append(
        f"Significance was assessed at alpha = {session.alpha:g}. "
        + (
            f"Joint inference used a permutation test with {session.n_permutations} "
            "permutations of the predictor."
            if session.n_permutations
            else ""
        )
    )
    text.append(f"All random steps used seed {session.seed}.")
    if session.blind:
        text.append(
            "The analysis plan was locked before results were viewed "
            f"(SHA-256 {session.blind.sha256[:12]}..., {session.blind.locked_at})."
        )
    text.append("Analyses were run with Multiverse Studio.")
    return " ".join(t.strip() for t in text if t.strip())


def results_paragraph(session: Session) -> str:
    """Results text from the verdict (and the cherry-pick check, when run)."""
    v = session.verdict
    if v is None:
        raise ValueError("Run the analysis first.")
    excluded = v.n_ok - v.n_valid
    text = [f"Of {v.n_specs} specifications, {v.n_ok} could be estimated"]
    text[0] += f" and {v.n_valid} were retained after excluding bad controls." if excluded else "."
    text.append(
        f"The median estimate was {v.median_estimate:+.3g}; {v.share_same_sign:.0%} of "
        f"specifications had the same sign and {v.share_significant:.0%} were significant "
        f"in that direction (p < {v.alpha:g})."
    )
    if v.permutation_p is not None:
        text.append(f"The permutation test gave p = {v.permutation_p:.3f}.")
    text.append(
        {
            "consistent": "The association was consistent across specifications.",
            "mixed": "The association depended on analytic choices.",
            "fragile": "The association was not robust across specifications.",
        }[v.label]
    )
    if session.cherry_pick is not None:
        c = session.cherry_pick
        text.append(
            f"A reported estimate of {c.reported_estimate:+.3g} exceeded "
            f"{c.share_weaker:.0%} of retained specifications"
            + ("; it lies in the extreme tail of the specification curve." if c.flagged else ".")
        )
    return " ".join(text)

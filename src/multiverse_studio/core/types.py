"""Shared data types for Multiverse Studio.

This module is the *contract* between the core library and the GUI. Every other
module exchanges these objects. Change them only after the whole team agrees
(see docs/architecture.md, "Changing the contract").

No GUI imports are allowed anywhere in ``multiverse_studio.core``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

ModelFamily = Literal["linear", "logistic", "poisson"]
"""Regression family. Chosen from the outcome column type (see profiling.suggest_family)."""


class ColumnKind(str, Enum):
    """What a column looks like, detected from its values."""

    NUMERIC = "numeric"  # continuous numbers (grades, income)
    BINARY = "binary"  # exactly two values (yes/no, 0/1)
    COUNT = "count"  # non-negative whole numbers (visits, errors)
    CATEGORICAL = "categorical"  # a few labels (gender, year, city)
    TEXT = "text"  # free text / IDs - never used in models
    DATETIME = "datetime"  # dates - never used in models (v1)


@dataclass(frozen=True)
class ColumnInfo:
    """Profile of one column."""

    name: str
    kind: ColumnKind
    n_missing: int
    n_unique: int
    skewness: float | None = None
    """Sample skewness for numeric columns, else ``None``. Used to suggest a log transform."""
    n_outliers_3sd: int = 0
    """Rows beyond 3 standard deviations (numeric only). Used to suggest outlier rules."""


@dataclass(frozen=True)
class DataProfile:
    """Profile of a whole table."""

    n_rows: int
    columns: tuple[ColumnInfo, ...]

    def column(self, name: str) -> ColumnInfo:
        for col in self.columns:
            if col.name == name:
                return col
        raise KeyError(name)

    @property
    def names(self) -> list[str]:
        return [c.name for c in self.columns]


class DecisionKind(str, Enum):
    """The families of analytic choices a multiverse can vary."""

    OUTLIERS = "outliers"  # which extreme rows to drop
    CONTROLS = "controls"  # which covariates to adjust for
    SUBSET = "subset"  # which rows (people) to include
    TRANSFORM = "transform"  # how to measure X or Y (raw / log / z-score)
    MISSING = "missing"  # how to handle missing values


@dataclass(frozen=True)
class Option:
    """One alternative for a decision, e.g. "remove beyond 3 SD".

    ``params`` holds machine-readable settings consumed by the runner, e.g.
    ``{"rule": "sd", "k": 3, "column": "coffee"}`` or ``{"columns": ["age"]}``.
    """

    id: str
    label: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Decision:
    """A fork in the analysis, with two or more options."""

    id: str
    kind: DecisionKind
    label: str
    options: tuple[Option, ...]
    explanation: str = ""
    """Plain-language 'why this matters', shown in the GUI."""

    def option(self, option_id: str) -> Option:
        for opt in self.options:
            if opt.id == option_id:
                return opt
        raise KeyError(option_id)


@dataclass(frozen=True)
class Spec:
    """One universe: a single option picked for every decision."""

    id: int
    choices: dict[str, str]
    """Mapping decision id -> option id."""


@dataclass(frozen=True)
class SpecResult:
    """The fitted result of one universe."""

    spec_id: int
    choices: dict[str, str]
    estimate: float | None
    std_error: float | None
    p_value: float | None
    ci_low: float | None
    ci_high: float | None
    n_obs: int
    error: str | None = None
    """Set when the model could not be fitted (too few rows, no variation...)."""
    valid: bool = True
    """False when causal guardrails flag this universe (bad control)."""

    @property
    def ok(self) -> bool:
        return self.error is None and self.estimate is not None


class CausalRole(str, Enum):
    """Role of a candidate control relative to X -> Y (Cinelli, Forney & Pearl)."""

    CONFOUNDER = "confounder"  # causes X and Y: good control, keep
    MEDIATOR = "mediator"  # caused by X, causes Y: bad control (blocks the effect)
    COLLIDER = "collider"  # caused by X and by Y: bad control (opens bias)
    OUTCOME_PROXY = "outcome_proxy"  # caused by Y only: bad control
    NEUTRAL = "neutral"  # precedes X, unrelated to it: harmless
    UNKNOWN = "unknown"  # user unsure: kept, but flagged


@dataclass(frozen=True)
class GuardrailAnswers:
    """The user's plain-language answers about one candidate control.

    Each answer is True / False / None (= "not sure").
    """

    happens_before_x: bool | None
    could_be_caused_by_x: bool | None
    could_be_caused_by_y: bool | None


@dataclass(frozen=True)
class ControlAssessment:
    variable: str
    role: CausalRole
    keep: bool
    reason: str


@dataclass(frozen=True)
class Verdict:
    """Robustness summary of a multiverse (see docs/decisions.md, D-2)."""

    n_specs: int
    n_ok: int
    n_valid: int
    median_estimate: float
    share_same_sign: float
    """Share of valid universes whose estimate has the same sign as the median."""
    share_significant: float
    """Share of valid universes significant (p < alpha) in the median's direction."""
    alpha: float
    permutation_p: float | None
    """p-value of Simonsohn et al. (2020) permutation test, or None if not run."""
    label: Literal["consistent", "mixed", "fragile"]
    explanation: str
    """Plain-language sentence for the GUI and the report."""


@dataclass(frozen=True)
class CherryPickResult:
    reported_estimate: float
    percentile: float
    """Percent of valid universes with an estimate <= the reported one (0-100)."""
    share_weaker: float
    """Share of valid universes with a smaller effect in the reported direction."""
    flagged: bool
    """True when the reported result sits in the extreme 5% tail."""
    explanation: str


@dataclass(frozen=True)
class BlindLock:
    """A locked analysis plan (blind mode)."""

    plan: dict[str, Any]
    sha256: str
    locked_at: str
    """ISO-8601 UTC timestamp."""


@dataclass
class Session:
    """The single shared state of one analysis (read and written by every GUI page).

    Everything needed to reproduce an analysis lives here, so saving a session,
    exporting a script and exporting a JSON report all start from this object.
    """

    data_path: str | None = None
    profile: DataProfile | None = None
    y: str | None = None
    x: str | None = None
    family: ModelFamily | None = None
    decisions: list[Decision] = field(default_factory=list)
    guardrails: dict[str, GuardrailAnswers] = field(default_factory=dict)
    assessments: list[ControlAssessment] = field(default_factory=list)
    seed: int = 20261207
    alpha: float = 0.05
    max_specs: int = 1000
    sample_if_over: bool = True
    n_permutations: int = 500
    blind: BlindLock | None = None
    specs: list[Spec] = field(default_factory=list)
    results: list[SpecResult] = field(default_factory=list)
    verdict: Verdict | None = None
    reported_estimate: float | None = None
    cherry_pick: CherryPickResult | None = None
    notes: str = ""

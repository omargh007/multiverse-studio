"""One module per wizard step: data, question, choices, guardrails, run, results, export."""

from __future__ import annotations

from .choices import ChoicesPage
from .data import DataPage
from .export import ExportPage
from .guardrails import GuardrailsPage
from .question import QuestionPage
from .results import ResultsPage
from .run import RunPage

PAGE_CLASSES = {
    "data": DataPage,
    "question": QuestionPage,
    "choices": ChoicesPage,
    "guardrails": GuardrailsPage,
    "run": RunPage,
    "results": ResultsPage,
    "export": ExportPage,
}

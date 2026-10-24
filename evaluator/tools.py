"""Compatibility layer for evaluator.tools.

Directs calls to the EvaluationEngine in evaluator.engine.
"""

from __future__ import annotations

from typing import Any
from evaluator.engine import EvaluationEngine
from evaluator.schema import (
    CRITERIA_IDS,
    CRITERIA_TITLES,
    CriterionEvaluation,
    EvaluatedItem,
    EvaluationFindings,
)

_engine = EvaluationEngine()


def evaluate_project_item(item: dict[str, Any], spec: dict[str, Any]) -> EvaluatedItem:
    """Evaluate a single project item using the 9-criteria engine."""
    return _engine._evaluate_project(item, spec)


def evaluate_paper_item(item: dict[str, Any], spec: dict[str, Any]) -> EvaluatedItem:
    """Evaluate a single paper item using the 9-criteria engine."""
    return _engine._evaluate_paper(item, spec)

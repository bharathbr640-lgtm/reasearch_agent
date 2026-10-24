"""Evaluator Agent (Agent 3) package.

Exports:
- execute_evaluation
- async_execute_evaluation
- EvaluationEngine
- EvaluationFindings
- EvaluatedItem
- CriterionEvaluation
- EvaluationVerdict
- BoundaryValidationError
- MalformedInputError
- MissingInputError
- CRITERIA_IDS
"""

from evaluator.boundary import (
    BoundaryValidationError,
    MalformedInputError,
    MissingInputError,
    load_session_inputs,
    resolve_and_validate_session_dir,
    validate_session_id,
)
from evaluator.engine import EvaluationEngine
from evaluator.run import async_execute_evaluation, execute_evaluation
from evaluator.schema import (
    CRITERIA_IDS,
    CriterionEvaluation,
    CrossFindingConflict,
    EvaluatedItem,
    EvaluationFindings,
    EvaluationVerdict,
)

__all__ = [
    "execute_evaluation",
    "async_execute_evaluation",
    "EvaluationEngine",
    "EvaluationFindings",
    "EvaluatedItem",
    "CriterionEvaluation",
    "CrossFindingConflict",
    "EvaluationVerdict",
    "BoundaryValidationError",
    "MalformedInputError",
    "MissingInputError",
    "CRITERIA_IDS",
    "load_session_inputs",
    "resolve_and_validate_session_dir",
    "validate_session_id",
]

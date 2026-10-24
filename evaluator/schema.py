"""Pydantic v2 data models for the Evaluation Agent (Agent 3).

Strictly enforces:
- 4 verdicts only: "verified", "partially verified", "not verified", "unknown"
- NO arbitrary numerical scores (no 0-10 float scores, no weighted rankings)
- Explicit applicability with applicability_reason
- Traceable evidence fields (requirement, supporting_evidence, source_identifier,
  source_location, explanation, missing_evidence, verification_status, limitations)
- Equal architectural verification for both projects and papers
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

# Authoritative list of 4 verdicts allowed across the evaluation system
EvaluationVerdict = Literal["verified", "partially verified", "not verified", "unknown"]

VALID_VERDICTS: set[str] = {"verified", "partially verified", "not verified", "unknown"}

# Authoritative list of the 9 criteria IDs
CRITERIA_IDS: list[str] = [
    "problem_relevance",
    "input_compatibility",
    "output_compatibility",
    "dataset_relevance",
    "method_relevance",
    "model_relevance",
    "experimental_evidence",
    "reproducibility",
    "research_gap",
]

CRITERIA_TITLES: dict[str, str] = {
    "problem_relevance": "Problem Relevance",
    "input_compatibility": "Input Compatibility",
    "output_compatibility": "Output Compatibility",
    "dataset_relevance": "Dataset Relevance",
    "method_relevance": "Method Relevance",
    "model_relevance": "Model Relevance",
    "experimental_evidence": "Experimental Evidence",
    "reproducibility": "Reproducibility",
    "research_gap": "Research Gap",
}


class CriterionEvaluation(BaseModel):
    """Evidence-backed evaluation for a single criterion."""

    criterion_id: str = Field(description="One of the 9 standard criteria identifiers")
    criterion_name: str = Field(default="", description="Human-readable title of criterion")
    verdict: EvaluationVerdict = Field(description="One of: verified, partially verified, not verified, unknown")
    applicable: bool = Field(default=True, description="False if this criterion does not apply to the item")
    applicability_reason: str | None = Field(
        default=None,
        description="Explicit explanation if criterion is not applicable",
    )
    requirement: str = Field(description="Requirement statement from research spec")
    supporting_evidence: str = Field(description="Traceable text/data evidence from source findings")
    source_identifier: str = Field(description="URL, DOI, or repository name")
    source_location: str = Field(
        default="",
        description="Quote, section heading, or file name where evidence was found",
    )
    explanation: str = Field(description="Reasoning connecting evidence to the verdict")
    missing_evidence: str | None = Field(
        default=None,
        description="What specific evidence is missing or unconfirmed",
    )
    verification_status: str = Field(
        default="claim_documented_only",
        description="Status: explicit_paper_statement, claim_documented_only, unsupported, contradictory, not_applicable",
    )
    limitations: str | None = Field(
        default=None,
        description="Known limitations affecting this criterion",
    )

    # Legacy / UI compatibility aliases (kept in sync automatically)
    criterion: str = ""
    evidence: str = ""
    judgment: str = ""

    @model_validator(mode="after")
    def sync_compatibility_fields(self) -> CriterionEvaluation:
        if not self.criterion_name and self.criterion_id in CRITERIA_TITLES:
            self.criterion_name = CRITERIA_TITLES[self.criterion_id]
        if not self.criterion:
            self.criterion = self.criterion_name or self.criterion_id
        if not self.evidence:
            self.evidence = self.supporting_evidence
        if not self.judgment:
            self.judgment = self.explanation
        return self


class EvaluatedItem(BaseModel):
    """Evaluated project codebase or academic research paper."""

    name: str = Field(description="Repository name or paper title")
    item_type: Literal["project", "paper"] = Field(description="Type of audited artifact")
    url: str = Field(description="Direct URL or DOI link")
    platform_or_venue: str = Field(default="", description="e.g. GitHub, Hugging Face, arXiv, CVPR")
    overall_verdict: EvaluationVerdict = Field(
        description="Overall verdict synthesized from 9 criteria results",
    )
    criteria_results: list[CriterionEvaluation] = Field(
        default_factory=list,
        description="Evaluations across all 9 criteria",
    )
    key_strengths: list[str] = Field(default_factory=list)
    known_limitations: list[str] = Field(default_factory=list)
    research_gaps: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Claims made without traceable supporting evidence",
    )
    contradictions_detected: list[str] = Field(
        default_factory=list,
        description="Contradictions identified within this item's claims",
    )


class CrossFindingConflict(BaseModel):
    """Contradiction or conflict identified between two different findings."""

    source_a: str = Field(description="Name or URL of first finding")
    source_b: str = Field(description="Name or URL of second finding")
    conflict_type: str = Field(description="e.g. dataset_size_conflict, performance_contradiction, feasibility_conflict")
    description: str = Field(description="Explanation of the contradiction")
    evidence_a: str = Field(description="Claim/evidence from source A")
    evidence_b: str = Field(description="Claim/evidence from source B")


class EvaluationFindings(BaseModel):
    """Final output schema for Agent 3 (Evaluator)."""

    session_id: str
    total_items_evaluated: int
    verdict_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Counts of verified, partially verified, not verified, unknown",
    )
    evaluated_projects: list[EvaluatedItem] = Field(default_factory=list)
    evaluated_papers: list[EvaluatedItem] = Field(default_factory=list)
    comparative_matrix: list[dict[str, Any]] = Field(default_factory=list)
    cross_finding_contradictions: list[CrossFindingConflict] = Field(default_factory=list)
    identified_research_gaps: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Errors encountered during input boundary loading",
    )

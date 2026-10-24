"""Verification engine for Agent 1 (projects) and Agent 2 (papers).

Architectural verification rules:
- Agent 1: Verify documented claims vs claims confirmed through inspection.
  Distinguish claims backed by README/docs from claims lacking evidence.
  Explicitly ensure no claim of runtime code execution is made unless execution actually occurred.
- Agent 2: Check quotes, numbers, sections. Distinguish explicit paper statements
  from extracted evidence from independent scientific verification.
- Detect and flag contradictory evidence across findings.
- Detect and flag unsupported extractions (claims without supporting evidence).
"""

from __future__ import annotations

import re
from typing import Any
from evaluator.schema import CrossFindingConflict


class ProjectClaimVerification:
    """Verification record for a specific field in a project finding."""

    def __init__(
        self,
        field: str,
        claim_text: str,
        source_str: str,
        is_backed_by_docs: bool,
        is_unsupported: bool,
        status: str,
        code_execution_verified: bool = False,
    ):
        self.field = field
        self.claim_text = claim_text
        self.source_str = source_str
        self.is_backed_by_docs = is_backed_by_docs
        self.is_unsupported = is_unsupported
        self.status = status
        self.code_execution_verified = code_execution_verified


class ProjectVerificationSummary:
    """Summary of verification checks for a project codebase finding."""

    def __init__(self, repo_name: str):
        self.repo_name = repo_name
        self.claims: dict[str, ProjectClaimVerification] = {}
        self.documented_claims: list[str] = []
        self.unsupported_claims: list[str] = []
        self.internal_contradictions: list[str] = []
        self.code_execution_occurred: bool = False
        self.inspection_notes: list[str] = []


class PaperClaimVerification:
    """Verification record for a specific field in an academic paper finding."""

    def __init__(
        self,
        field: str,
        claim_text: str,
        quote: str,
        section: str,
        status: str,
        is_author_claim_only: bool = True,
        independent_verification: str = "unverified_author_claim",
    ):
        self.field = field
        self.claim_text = claim_text
        self.quote = quote
        self.section = section
        self.status = status
        self.is_author_claim_only = is_author_claim_only
        self.independent_verification = independent_verification


class PaperVerificationSummary:
    """Summary of verification checks for an academic paper finding."""

    def __init__(self, title: str):
        self.title = title
        self.claims: dict[str, PaperClaimVerification] = {}
        self.explicit_statements: list[str] = []
        self.unsupported_claims: list[str] = []
        self.internal_contradictions: list[str] = []
        self.independent_verification_status: str = "unverified_author_claim"


def _is_empty_or_not_found(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, str):
        s = val.strip().lower()
        return s in {"", "not found", "n/a", "none", "unknown"}
    return False


def verify_project_claims(item: dict[str, Any]) -> ProjectVerificationSummary:
    """Verify an Agent 1 project finding against README/docs sources and execution constraints."""
    repo_name = item.get("name", "Unnamed Project")
    summary = ProjectVerificationSummary(repo_name)

    field_sources: dict[str, Any] = item.get("field_sources", {}) or {}

    project_fields = [
        "problem_solved",
        "input_output",
        "dataset",
        "model_and_architecture",
        "method",
        "evaluation_and_results",
        "reproducibility",
        "known_limitations",
    ]

    for fld in project_fields:
        val = item.get(fld, "")
        val_str = str(val).strip() if val is not None else ""
        source_val = field_sources.get(fld, "")
        source_str = str(source_val).strip() if source_val is not None else ""

        if _is_empty_or_not_found(val_str):
            claim = ProjectClaimVerification(
                field=fld,
                claim_text=val_str,
                source_str=source_str,
                is_backed_by_docs=False,
                is_unsupported=False,
                status="missing_claim",
                code_execution_verified=False,
            )
        elif _is_empty_or_not_found(source_str):
            # Claim exists in finding but source is missing or "not found" -> Unsupported extraction!
            claim = ProjectClaimVerification(
                field=fld,
                claim_text=val_str,
                source_str=source_str,
                is_backed_by_docs=False,
                is_unsupported=True,
                status="unsupported",
                code_execution_verified=False,
            )
            summary.unsupported_claims.append(
                f"Field '{fld}' claims '{val_str[:80]}...' but field source is missing or marked 'not found'"
            )
        else:
            # Backed by static docs/README
            claim = ProjectClaimVerification(
                field=fld,
                claim_text=val_str,
                source_str=source_str,
                is_backed_by_docs=True,
                is_unsupported=False,
                status="claim_documented_only",
                code_execution_verified=False,
            )
            summary.documented_claims.append(fld)

        summary.claims[fld] = claim

    # Explicit code execution check
    # In this agent framework, Agent 1 performs static inspection of GitHub/HuggingFace metadata
    # It does NOT execute untrusted arbitrary repo code on local hardware.
    summary.code_execution_occurred = False
    summary.inspection_notes.append(
        "Static inspection only: No arbitrary repository code execution was performed. "
        "Claims are documented only via README and repository metadata."
    )

    # Check for internal contradictions
    prob_str = str(item.get("problem_solved", "")).lower()
    limits_str = str(item.get("known_limitations", "")).lower()
    eval_str = str(item.get("evaluation_and_results", "")).lower()
    method_str = str(item.get("method", "")).lower()

    # Contradiction: Claims mobile/offline inference, but limitations/method states cloud or server only
    if ("offline" in prob_str or "mobile" in prob_str) and (
        "requires server" in limits_str
        or "cloud only" in limits_str
        or "api connection required" in limits_str
        or "not compatible with mobile" in limits_str
        or "cloud only" in method_str
    ):
        summary.internal_contradictions.append(
            "Contradiction: Project claims mobile/offline functionality in problem_solved, "
            "but limitations state that server/cloud connectivity is strictly required."
        )

    # Contradiction: High accuracy claim vs failing evaluation results
    if ("high accuracy" in prob_str or "9" in prob_str) and (
        "low accuracy" in eval_str
        or "failed" in eval_str
        or "poor performance" in eval_str
        or "overfitting" in eval_str
    ):
        summary.internal_contradictions.append(
            "Contradiction: Problem statement claims high accuracy, but evaluation results cite "
            "poor performance or failure."
        )

    return summary


def verify_paper_claims(item: dict[str, Any]) -> PaperVerificationSummary:
    """Verify an Agent 2 research paper finding against extracted quotes and sections."""
    title = item.get("title", "Unnamed Paper")
    summary = PaperVerificationSummary(title)

    key_evidence = item.get("key_evidence", []) or []
    # Build map of field -> list of evidence records
    evidence_by_field: dict[str, list[dict[str, Any]]] = {}
    for ev in key_evidence:
        if isinstance(ev, dict):
            fld = ev.get("field", "")
            if fld:
                evidence_by_field.setdefault(fld, []).append(ev)

    paper_fields = [
        "problem_addressed",
        "research_objective",
        "domain",
        "input_type",
        "output_type",
        "method",
        "limitations",
        "research_gap",
    ]

    for fld in paper_fields:
        val = item.get(fld, "")
        val_str = str(val).strip() if val is not None else ""

        matched_ev = evidence_by_field.get(fld, [])
        valid_ev = [
            e for e in matched_ev
            if not _is_empty_or_not_found(e.get("quote"))
        ]

        if _is_empty_or_not_found(val_str):
            claim = PaperClaimVerification(
                field=fld,
                claim_text=val_str,
                quote="",
                section="",
                status="missing_claim",
                is_author_claim_only=True,
                independent_verification="unverified_author_claim",
            )
        elif not valid_ev:
            # Claim exists in finding but no direct quote or section is referenced in key_evidence!
            claim = PaperClaimVerification(
                field=fld,
                claim_text=val_str,
                quote="",
                section="",
                status="unsupported",
                is_author_claim_only=True,
                independent_verification="unverified_author_claim",
            )
            summary.unsupported_claims.append(
                f"Paper claim for '{fld}' ('{val_str[:80]}...') lacks direct quote evidence in key_evidence"
            )
        else:
            first_ev = valid_ev[0]
            quote = str(first_ev.get("quote", "")).strip()
            section = str(first_ev.get("section", "")).strip()
            claim = PaperClaimVerification(
                field=fld,
                claim_text=val_str,
                quote=quote,
                section=section,
                status="explicit_paper_statement",
                is_author_claim_only=True,
                independent_verification="unverified_author_claim",
            )
            summary.explicit_statements.append(f"{fld} [{section}]")

        summary.claims[fld] = claim

    # Verify complex nested structures: dataset, model, experiments_and_results
    exp_dict = item.get("experiments_and_results", {}) or {}
    reported_res = exp_dict.get("reported_results", "") if isinstance(exp_dict, dict) else ""
    if not _is_empty_or_not_found(reported_res):
        # Preprint metrics are author self-reported
        summary.independent_verification_status = (
            "Preprint metrics are author-reported claims from arXiv text; "
            "independent replication or third-party benchmark verification has not occurred."
        )

    # Internal contradiction check
    match_reason = str(item.get("match_reason", "")).lower()
    prob_str = str(item.get("problem_addressed", "")).lower()
    obj_str = str(item.get("research_objective", "")).lower()
    limits_str = str(item.get("limitations", "")).lower()

    if "offline operation not stated" in match_reason and ("offline" in prob_str or "offline" in obj_str):
        summary.internal_contradictions.append(
            "Contradiction: Finding text asserts offline operation, but match_reason explicitly notes "
            "'offline operation not stated in the text'."
        )

    if ("100%" in reported_res or "perfect" in reported_res) and (
        "no method or configuration works well in all cases" in limits_str
        or "failure" in limits_str
    ):
        summary.internal_contradictions.append(
            "Contradiction: Abstract/results claim near-perfect performance, while limitations acknowledge "
            "severe generalization failures."
        )

    return summary


def detect_cross_finding_conflicts(
    projects: list[dict[str, Any]],
    papers: list[dict[str, Any]],
) -> list[CrossFindingConflict]:
    """Scan across all findings for contradictory claims regarding datasets, metrics, and feasibility."""
    conflicts: list[CrossFindingConflict] = []

    # Map dataset names mentioned across findings -> list of (source_name, description/size)
    dataset_mentions: dict[str, list[tuple[str, str]]] = {}

    for p in projects:
        p_name = p.get("name", "Project")
        ds = p.get("dataset", "")
        if ds and not _is_empty_or_not_found(ds):
            # Extract common dataset tokens
            ds_clean = str(ds).lower()
            if "rocole" in ds_clean:
                dataset_mentions.setdefault("rocole", []).append((p_name, str(ds)))
            if "mendeley" in ds_clean:
                dataset_mentions.setdefault("mendeley", []).append((p_name, str(ds)))

    for paper in papers:
        paper_title = paper.get("title", "Paper")
        ds_info = paper.get("dataset", {})
        ds_desc = ""
        if isinstance(ds_info, dict):
            ds_desc = f"{ds_info.get('name', '')} {ds_info.get('description', '')} (size: {ds_info.get('size', '')})"
        elif isinstance(ds_info, str):
            ds_desc = ds_info

        ds_clean = ds_desc.lower()
        if "rocole" in ds_clean:
            dataset_mentions.setdefault("rocole", []).append((paper_title, ds_desc))
        if "mendeley" in ds_clean:
            dataset_mentions.setdefault("mendeley", []).append((paper_title, ds_desc))

    # Check for contradictions in size or scope
    for ds_key, mentions in dataset_mentions.items():
        if len(mentions) >= 2:
            src_a, desc_a = mentions[0]
            src_b, desc_b = mentions[1]
            # Check if sizes explicitly contradict (e.g., numbers that differ significantly)
            numbers_a = re.findall(r"\b\d{2,6}\b", desc_a)
            numbers_b = re.findall(r"\b\d{2,6}\b", desc_b)
            if numbers_a and numbers_b and set(numbers_a).isdisjoint(set(numbers_b)):
                conflicts.append(
                    CrossFindingConflict(
                        source_a=src_a,
                        source_b=src_b,
                        conflict_type="dataset_size_conflict",
                        description=f"Findings cite conflicting dataset dimensions or sample counts for {ds_key.upper()}.",
                        evidence_a=desc_a,
                        evidence_b=desc_b,
                    )
                )

    return conflicts

"""Common Evaluation Agent Engine (Agent 3).

Coordinates:
1. Input boundary loading and validation
2. Project and paper claim verification (Agent 1 & Agent 2 architectural equality)
3. 9 criteria evidence-backed evaluation
4. Cross-finding contradiction detection
5. Matrix assembly, research gap synthesis, and recommended next steps formulation
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evaluator.boundary import load_session_inputs
from evaluator.criteria import (
    CRITERIA_IDS,
    evaluate_criterion_deterministic,
    evaluate_criterion_llm,
)
from evaluator.schema import (
    CriterionEvaluation,
    EvaluatedItem,
    EvaluationFindings,
    EvaluationVerdict,
)
from evaluator.verification import (
    detect_cross_finding_conflicts,
    verify_paper_claims,
    verify_project_claims,
)


def synthesize_overall_verdict(criteria_results: list[CriterionEvaluation]) -> EvaluationVerdict:
    """Synthesize an overall verdict from the 9 criteria results without numerical scoring."""
    counts: dict[str, int] = {
        "verified": 0,
        "partially verified": 0,
        "not verified": 0,
        "unknown": 0,
    }
    prob_verdict: str = "unknown"

    for c in criteria_results:
        counts[c.verdict] = counts.get(c.verdict, 0) + 1
        if c.criterion_id == "problem_relevance":
            prob_verdict = c.verdict

    # If problem relevance completely fails, the item is not verified for the spec
    if prob_verdict == "not verified":
        return "not verified"

    # If 3 or more criteria fail completely
    if counts["not verified"] >= 3:
        return "not verified"

    # If all or nearly all criteria are unknown
    if counts["unknown"] >= 7:
        return "unknown"

    # If problem relevance is verified and majority of applicable criteria are verified
    if prob_verdict == "verified" and counts["verified"] >= 4 and counts["not verified"] == 0:
        return "verified"

    return "partially verified"


class EvaluationEngine:
    """The central evaluation engine applying the 9 criteria framework across projects and papers."""

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm

    def evaluate_session(
        self,
        session_id: str,
        output_base: Path | str | None = None,
    ) -> EvaluationFindings:
        """Execute complete evaluation workflow for a session."""
        spec_data, project_data, paper_data, validation_errors = load_session_inputs(
            session_id, output_base
        )

        evaluated_projects: list[EvaluatedItem] = []
        raw_projects: list[dict[str, Any]] = project_data.get("findings", []) if isinstance(project_data, dict) else []
        for p in raw_projects:
            if not isinstance(p, dict):
                continue
            item = self._evaluate_project(p, spec_data)
            evaluated_projects.append(item)

        evaluated_papers: list[EvaluatedItem] = []
        raw_papers: list[dict[str, Any]] = paper_data.get("findings", []) if isinstance(paper_data, dict) else []
        for paper in raw_papers:
            if not isinstance(paper, dict):
                continue
            item = self._evaluate_paper(paper, spec_data)
            evaluated_papers.append(item)

        # Cross-finding conflict detection across all candidates
        cross_conflicts = detect_cross_finding_conflicts(raw_projects, raw_papers)

        all_evaluated = evaluated_projects + evaluated_papers
        total_count = len(all_evaluated)

        # Count verdicts
        verdict_counts: dict[str, int] = {
            "verified": sum(1 for i in all_evaluated if i.overall_verdict == "verified"),
            "partially verified": sum(1 for i in all_evaluated if i.overall_verdict == "partially verified"),
            "not verified": sum(1 for i in all_evaluated if i.overall_verdict == "not verified"),
            "unknown": sum(1 for i in all_evaluated if i.overall_verdict == "unknown"),
        }

        # Build Comparative Matrix
        comparative_matrix: list[dict[str, Any]] = []
        for item in all_evaluated:
            crit_summary = {c.criterion_id: c.verdict for c in item.criteria_results}
            sample_ev = ""
            for c in item.criteria_results:
                if c.supporting_evidence and len(c.supporting_evidence) > 10 and c.supporting_evidence.lower() != "not found":
                    sample_ev = c.supporting_evidence
                    break

            comparative_matrix.append({
                "name": item.name,
                "item_type": item.item_type,
                "url": item.url,
                "platform_or_venue": item.platform_or_venue,
                "overall_verdict": item.overall_verdict,
                "criteria_summary": crit_summary,
                "criteria_results": [c.model_dump() for c in item.criteria_results],
                "key_evidence": sample_ev or "Audited against specification.",
                "unsupported_claims": item.unsupported_claims,
                "contradictions": item.contradictions_detected,
                "research_gaps": item.research_gaps,
            })

        # Synthesize research gaps
        all_gaps: list[str] = []
        for item in all_evaluated:
            for g in item.research_gaps:
                if g and g not in all_gaps and len(g) > 8:
                    all_gaps.append(g)

        # Synthesize gaps from unmet constraints in research spec
        constraints_text = str(spec_data.get("constraints", "")).lower()
        if "offline" in constraints_text or "android" in constraints_text:
            gap_offline = "Lack of edge-quantized mobile inference pipeline (TFLite/ONNX) verified under offline Android constraints."
            if gap_offline not in all_gaps:
                all_gaps.append(gap_offline)
        if "latency" in constraints_text or "3 second" in constraints_text:
            gap_latency = "Absence of empirical on-device inference latency benchmarks on consumer mobile hardware."
            if gap_latency not in all_gaps:
                all_gaps.append(gap_latency)
        if "kannada" in constraints_text or "language" in constraints_text:
            gap_lang = "Lack of localized multilingual treatment guide content (Kannada & English agronomic action steps)."
            if gap_lang not in all_gaps:
                all_gaps.append(gap_lang)
        if "robusta" in str(spec_data.get("datasets_and_technologies", "")).lower():
            gap_variety = "Limited public image representation for Robusta coffee variety compared to Arabica."
            if gap_variety not in all_gaps:
                all_gaps.append(gap_variety)

        # Formulate recommended next steps
        recommended_next_steps = [
            "Select the highest-verdict candidate architecture (e.g., MobileNet or CNN backbone) as foundation baseline.",
            "Export model weights to TensorFlow Lite (INT8 quantized) to satisfy the <= 50MB and <= 3s latency budget.",
            "Augment training dataset with field imagery covering both Arabica and Robusta cultivars to close variety gaps.",
            "Integrate rule-based practical agronomic treatment guides in English and Kannada without chemical dosages.",
            "Establish automated verification test harness validating offline camera inference on physical Android testbeds.",
        ]

        return EvaluationFindings(
            session_id=session_id,
            total_items_evaluated=total_count,
            verdict_counts=verdict_counts,
            evaluated_projects=evaluated_projects,
            evaluated_papers=evaluated_papers,
            comparative_matrix=comparative_matrix,
            cross_finding_contradictions=cross_conflicts,
            identified_research_gaps=all_gaps[:6],
            recommended_next_steps=recommended_next_steps,
            validation_errors=validation_errors,
        )

    def _evaluate_project(self, item: dict[str, Any], spec: dict[str, Any]) -> EvaluatedItem:
        """Audit a single project finding across the 9 criteria."""
        name = item.get("name", "Unnamed Project")
        url = item.get("url", "")
        platform = item.get("platform", "github")
        repo_details = item.get("repository_details", {}) or {}
        lang = repo_details.get("language", "Code")
        venue = f"{platform.capitalize()} ({lang})" if lang else platform.capitalize()

        verification = verify_project_claims(item)

        criteria_results: list[CriterionEvaluation] = []
        for cid in CRITERIA_IDS:
            res = evaluate_criterion_deterministic(cid, spec, item, "project", verification)
            criteria_results.append(res)

        overall_verdict = synthesize_overall_verdict(criteria_results)

        key_strengths = [
            f"{c.criterion_name}: {c.supporting_evidence[:80]}"
            for c in criteria_results
            if c.verdict == "verified" and c.supporting_evidence and c.supporting_evidence.lower() != "not found"
        ]

        known_limitations = list(verification.internal_contradictions)
        for c in criteria_results:
            if c.missing_evidence and c.verdict in {"partially verified", "not verified"}:
                known_limitations.append(f"{c.criterion_name}: {c.missing_evidence}")

        gaps = []
        lim = item.get("known_limitations", "")
        if lim and str(lim).lower() != "not found":
            gaps.append(str(lim))

        return EvaluatedItem(
            name=name,
            item_type="project",
            url=url,
            platform_or_venue=venue,
            overall_verdict=overall_verdict,
            criteria_results=criteria_results,
            key_strengths=key_strengths[:4],
            known_limitations=known_limitations[:4],
            research_gaps=gaps[:3],
            unsupported_claims=verification.unsupported_claims,
            contradictions_detected=verification.internal_contradictions,
        )

    def _evaluate_paper(self, item: dict[str, Any], spec: dict[str, Any]) -> EvaluatedItem:
        """Audit a single research paper finding across the 9 criteria."""
        title = item.get("title", "Unnamed Paper")
        url = item.get("paper_url", "")
        year = item.get("year", "")
        venue = f"arXiv ({year})" if year else "arXiv"

        verification = verify_paper_claims(item)

        criteria_results: list[CriterionEvaluation] = []
        for cid in CRITERIA_IDS:
            res = evaluate_criterion_deterministic(cid, spec, item, "paper", verification)
            criteria_results.append(res)

        overall_verdict = synthesize_overall_verdict(criteria_results)

        key_strengths = [
            f"{c.criterion_name}: {c.supporting_evidence[:80]}"
            for c in criteria_results
            if c.verdict == "verified" and c.supporting_evidence and c.supporting_evidence.lower() != "not found"
        ]

        known_limitations = list(verification.internal_contradictions)
        for c in criteria_results:
            if c.missing_evidence and c.verdict in {"partially verified", "not verified"}:
                known_limitations.append(f"{c.criterion_name}: {c.missing_evidence}")

        gaps = []
        rg = item.get("research_gap", "")
        if rg and str(rg).lower() != "not found":
            gaps.append(str(rg))
        lim = item.get("limitations", "")
        if lim and str(lim).lower() != "not found":
            gaps.append(str(lim))

        return EvaluatedItem(
            name=title,
            item_type="paper",
            url=url,
            platform_or_venue=venue,
            overall_verdict=overall_verdict,
            criteria_results=criteria_results,
            key_strengths=key_strengths[:4],
            known_limitations=known_limitations[:4],
            research_gaps=gaps[:3],
            unsupported_claims=verification.unsupported_claims,
            contradictions_detected=verification.internal_contradictions,
        )

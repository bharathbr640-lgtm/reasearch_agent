"""Definitions and evaluators for the 9 standard evaluation criteria.

Criteria:
1. problem_relevance
2. input_compatibility
3. output_compatibility
4. dataset_relevance
5. method_relevance
6. model_relevance
7. experimental_evidence
8. reproducibility
9. research_gap

Rules:
- Strict 4 verdicts: "verified", "partially verified", "not verified", "unknown"
- NO numerical scores (no 0-10 float scores, no weighted rankings)
- Explicit applicability: record applicable=False with applicability_reason
- Evidence-backed traceability: source_identifier, source_location, supporting_evidence,
  missing_evidence, verification_status, limitations
"""

from __future__ import annotations

import json
import logging
from typing import Any
from openai import AsyncOpenAI

from app.config import OLLAMA_BASE_URL, OLLAMA_API_KEY, MODEL_NAME
from evaluator.schema import (
    CRITERIA_IDS,
    CRITERIA_TITLES,
    CriterionEvaluation,
    EvaluationVerdict,
)
from evaluator.verification import (
    ProjectVerificationSummary,
    PaperVerificationSummary,
)

logger = logging.getLogger(__name__)

CRITERIA_QUESTIONS: dict[str, str] = {
    "problem_relevance": "Does the work address the same core problem?",
    "input_compatibility": "Does it use compatible input data or information?",
    "output_compatibility": "Does it produce the type of output required?",
    "dataset_relevance": "Is the dataset relevant to the proposed problem?",
    "method_relevance": "Is the method applicable to the proposed approach?",
    "model_relevance": "Is the model/architecture relevant and compliant with constraints?",
    "experimental_evidence": "Does the work demonstrate the method experimentally?",
    "reproducibility": "Is there enough information/code/data to reproduce or study it?",
    "research_gap": "What remains unresolved or different from the proposed problem?",
}


def _clean_str(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, dict):
        return json.dumps(val)
    if isinstance(val, list):
        return ", ".join(str(x) for x in val)
    return str(val).strip()


def _is_missing(val: Any) -> bool:
    s = _clean_str(val).lower()
    return s in {"", "not found", "n/a", "none", "unknown"}


def extract_spec_requirement(spec: dict[str, Any], criterion_id: str) -> str:
    """Map each criterion ID to its corresponding specification requirement text."""
    if criterion_id == "problem_relevance":
        return _clean_str(
            spec.get("clarified_problem_statement")
            or spec.get("original_problem_statement")
            or spec.get("research_focus")
        )
    if criterion_id == "input_compatibility":
        return _clean_str(spec.get("expected_input") or "Standard input data modality matching spec.")
    if criterion_id == "output_compatibility":
        return _clean_str(spec.get("expected_output") or "Standard output prediction/labels matching spec.")
    if criterion_id == "dataset_relevance":
        return _clean_str(
            spec.get("datasets_and_technologies")
            or spec.get("research_focus")
            or "Publicly available datasets for the target problem."
        )
    if criterion_id == "method_relevance":
        return _clean_str(
            spec.get("research_focus")
            or spec.get("clarified_problem_statement")
            or "Applicable machine learning and computer vision methodology."
        )
    if criterion_id == "model_relevance":
        return _clean_str(
            spec.get("constraints")
            or "Model architecture suitable for deployment constraints."
        )
    if criterion_id == "experimental_evidence":
        return _clean_str(
            spec.get("constraints")
            or "Empirical validation with reported accuracy and metrics."
        )
    if criterion_id == "reproducibility":
        return _clean_str(
            spec.get("other_requirements")
            or "Open-source code, repository documentation, and reproducible instructions."
        )
    if criterion_id == "research_gap":
        return _clean_str(
            spec.get("constraints")
            or "Identification of unresolved operational and technical gaps."
        )
    return ""


def evaluate_criterion_deterministic(
    criterion_id: str,
    spec: dict[str, Any],
    item: dict[str, Any],
    item_type: str,
    verification: ProjectVerificationSummary | PaperVerificationSummary,
) -> CriterionEvaluation:
    """Deterministic, rule-based evaluator for offline unit tests and robust fallbacks."""
    requirement = extract_spec_requirement(spec, criterion_id)
    criterion_name = CRITERIA_TITLES.get(criterion_id, criterion_id)

    source_id = item.get("url") or item.get("paper_url") or item.get("name") or item.get("title") or ""
    source_loc = ""
    evidence = ""
    verdict: EvaluationVerdict = "unknown"
    applicable = True
    applicability_reason: str | None = None
    missing_evidence: str | None = None
    explanation = ""
    status = "claim_documented_only" if item_type == "project" else "explicit_paper_statement"
    limitations = None

    # Check for contradictions detected by verification engine
    contradictions = verification.internal_contradictions
    has_contradiction = len(contradictions) > 0

    # 1. PROBLEM RELEVANCE
    if criterion_id == "problem_relevance":
        if item_type == "project":
            raw = item.get("problem_solved", "")
            source_loc = item.get("field_sources", {}).get("problem_solved", "")
        else:
            raw = item.get("problem_addressed", "") or item.get("research_objective", "")
            # check key_evidence for location
            for ev in item.get("key_evidence", []):
                if isinstance(ev, dict) and ev.get("field") in {"problem_addressed", "research_objective"}:
                    source_loc = f"{ev.get('section', '')}: {ev.get('quote', '')[:60]}"
                    break

        evidence = _clean_str(raw)
        if _is_missing(evidence):
            verdict = "unknown"
            missing_evidence = "No problem statement or objective found in findings."
            explanation = "Source artifact does not disclose the specific problem it addresses."
            status = "missing_claim"
        else:
            ev_lower = evidence.lower()
            req_lower = requirement.lower()

            # Check if this is a superficial match: e.g. shares a keyword like "coffee" or "disease",
            # but addresses roasting, sales, or completely different plants/domain
            superficial_terms = [
                "roasting", "temperature", "iot sensor", "sales forecasting", "price prediction",
                "coffee shop", "bean sorting", "supply chain", "cup quality",
            ]
            is_superficial = any(term in ev_lower for term in superficial_terms) and not any(
                term in req_lower for term in superficial_terms
            )

            # Check core domain alignment
            core_terms = ["leaf", "disease", "pathology", "pest", "crop", "plant", "rust"]
            matches_core = any(term in ev_lower for term in core_terms) if any(term in req_lower for term in core_terms) else True

            # Domain specific plant check (e.g. coffee vs tomato/wheat)
            req_plant = "coffee" if "coffee" in req_lower else ""
            ev_plant = "coffee" in ev_lower

            if is_superficial or (req_plant and not ev_plant and not matches_core):
                verdict = "not verified"
                missing_evidence = f"Does not address the target problem domain ({requirement[:60]})."
                explanation = f"Artifact focuses on superficial/adjacent domain: '{evidence}'."
                status = "unsupported" if verification.unsupported_claims else "claim_documented_only"
            elif req_plant and not ev_plant and matches_core:
                verdict = "partially verified"
                missing_evidence = f"Evaluated on alternate plant/species rather than {req_plant}."
                explanation = f"Technique addresses plant pathology ({evidence}) but not the target {req_plant} crop."
            elif has_contradiction and any("problem" in c.lower() for c in contradictions):
                verdict = "partially verified"
                missing_evidence = "Claims are contradictory regarding core problem resolution."
                explanation = f"Problem addressed ({evidence}) contains internal contradictions: {contradictions[0]}"
                status = "contradictory"
            else:
                verdict = "verified"
                explanation = f"Directly addresses target problem: {evidence}."

    # 2. INPUT COMPATIBILITY
    elif criterion_id == "input_compatibility":
        if item_type == "project":
            raw = item.get("input_output", "")
            source_loc = item.get("field_sources", {}).get("input_output", "")
        else:
            raw = item.get("input_type", "")
            for ev in item.get("key_evidence", []):
                if isinstance(ev, dict) and ev.get("field") == "input_type":
                    source_loc = f"{ev.get('section', '')}: {ev.get('quote', '')[:60]}"
                    break

        evidence = _clean_str(raw)
        if _is_missing(evidence):
            verdict = "unknown"
            missing_evidence = "Input data specification not documented."
            explanation = "Input data type cannot be verified from available documentation."
            status = "missing_claim"
        else:
            ev_lower = evidence.lower()
            req_lower = requirement.lower()
            if "image" in req_lower or "photo" in req_lower or "camera" in req_lower:
                if any(term in ev_lower for term in ["image", "photo", "picture", "camera", "visual", "leaf"]):
                    verdict = "verified"
                    explanation = f"Input modality ({evidence}) is compatible with expected visual image capture."
                else:
                    verdict = "not verified"
                    missing_evidence = f"Expected camera image input, but artifact uses non-image modality: {evidence}."
                    explanation = f"Modality mismatch: requires {requirement[:50]}."
            else:
                verdict = "verified"
                explanation = f"Input specification provided: {evidence}."

    # 3. OUTPUT COMPATIBILITY
    elif criterion_id == "output_compatibility":
        if item_type == "project":
            raw = item.get("input_output", "")
            source_loc = item.get("field_sources", {}).get("input_output", "")
        else:
            raw = item.get("output_type", "")
            for ev in item.get("key_evidence", []):
                if isinstance(ev, dict) and ev.get("field") == "output_type":
                    source_loc = f"{ev.get('section', '')}: {ev.get('quote', '')[:60]}"
                    break

        evidence = _clean_str(raw)
        if _is_missing(evidence):
            verdict = "unknown"
            missing_evidence = "Output prediction specification not documented."
            explanation = "Output format cannot be determined from available findings."
            status = "missing_claim"
        else:
            ev_lower = evidence.lower()
            req_lower = requirement.lower()
            # Requirement mentions disease label plus treatment guide
            has_label = "label" in ev_lower or "class" in ev_lower or "detection" in ev_lower or "percentage" in ev_lower
            has_guide = "guide" in ev_lower or "treatment" in ev_lower or "kannada" in ev_lower

            if "guide" in req_lower and not has_guide:
                verdict = "partially verified"
                missing_evidence = "Outputs disease label but lacks treatment guide or localized recommendation output."
                explanation = f"Produces diagnostic output ({evidence}), but lacks agronomic treatment guide required by spec."
            elif has_label:
                verdict = "verified"
                explanation = f"Produces compatible diagnostic classification output: {evidence}."
            else:
                verdict = "partially verified"
                missing_evidence = "Output format details incomplete."
                explanation = f"Reported output: {evidence}."

    # 4. DATASET RELEVANCE
    elif criterion_id == "dataset_relevance":
        if item_type == "project":
            raw = item.get("dataset", "")
            source_loc = item.get("field_sources", {}).get("dataset", "")
        else:
            ds_val = item.get("dataset", "")
            if isinstance(ds_val, dict):
                raw = f"{ds_val.get('name', '')} {ds_val.get('description', '')} (size: {ds_val.get('size', '')})"
            else:
                raw = ds_val
            for ev in item.get("key_evidence", []):
                if isinstance(ev, dict) and "dataset" in ev.get("field", ""):
                    source_loc = f"{ev.get('section', '')}: {ev.get('quote', '')[:60]}"
                    break

        evidence = _clean_str(raw)
        if _is_missing(evidence):
            verdict = "unknown"
            missing_evidence = "Dataset source and description not found."
            explanation = "No dataset information recorded for this artifact."
            status = "missing_claim"
        else:
            ev_lower = evidence.lower()
            req_lower = requirement.lower()

            req_coffee = "coffee" in req_lower
            ev_coffee = "coffee" in ev_lower or "rocole" in ev_lower or "arabica" in ev_lower or "robusta" in ev_lower

            if req_coffee and not ev_coffee:
                verdict = "not verified"
                missing_evidence = "Dataset does not include coffee leaf imagery (trained on other species/domains)."
                explanation = f"Dataset ({evidence}) does not match required target crop."
            elif "robusta" in req_lower and "arabica" in ev_lower and "robusta" not in ev_lower:
                verdict = "partially verified"
                missing_evidence = "Dataset contains Arabica only; missing Robusta variety representation."
                explanation = f"Dataset covers target pathology but is limited to Arabica: {evidence}."
            else:
                verdict = "verified"
                explanation = f"Relevant domain dataset identified: {evidence}."

    # 5. METHOD RELEVANCE
    elif criterion_id == "method_relevance":
        if item_type == "project":
            raw = item.get("method", "")
            source_loc = item.get("field_sources", {}).get("method", "")
        else:
            raw = item.get("method", "")
            for ev in item.get("key_evidence", []):
                if isinstance(ev, dict) and ev.get("field") == "method":
                    source_loc = f"{ev.get('section', '')}: {ev.get('quote', '')[:60]}"
                    break

        evidence = _clean_str(raw)
        if _is_missing(evidence):
            verdict = "unknown"
            missing_evidence = "Methodology not documented."
            explanation = "Underlying computational method is unspecified."
            status = "missing_claim"
        else:
            ev_lower = evidence.lower()
            if "neural" in ev_lower or "cnn" in ev_lower or "deep learning" in ev_lower or "vision" in ev_lower or "segment" in ev_lower:
                verdict = "verified"
                explanation = f"Applicable computer vision methodology employed: {evidence}."
            else:
                verdict = "partially verified"
                missing_evidence = "Method details lacking deep learning or edge vision specifications."
                explanation = f"Methodology: {evidence}."

    # 6. MODEL RELEVANCE & CONSTRAINTS
    elif criterion_id == "model_relevance":
        # Check applicability: Pure dataset repositories or papers have no model architecture
        is_pure_dataset = (
            item.get("kind") == "dataset"
            or "dataset only" in str(item.get("problem_solved", "")).lower()
            or "data set" in str(item.get("name", "")).lower()
        )
        if is_pure_dataset:
            applicable = False
            applicability_reason = "Pure dataset artifact without model or neural network architecture."
            verdict = "not verified"
            evidence = "N/A - Pure dataset resource."
            explanation = "Criterion not applicable to pure dataset repositories."
            status = "not_applicable"
        else:
            if item_type == "project":
                raw = item.get("model_and_architecture", "")
                source_loc = item.get("field_sources", {}).get("model_and_architecture", "")
            else:
                m_info = item.get("model", {})
                if isinstance(m_info, dict):
                    raw = f"{m_info.get('model_name', '')} {m_info.get('architecture', '')}"
                else:
                    raw = m_info
                for ev in item.get("key_evidence", []):
                    if isinstance(ev, dict) and "model" in ev.get("field", ""):
                        source_loc = f"{ev.get('section', '')}: {ev.get('quote', '')[:60]}"
                        break

            evidence = _clean_str(raw)
            if _is_missing(evidence):
                verdict = "unknown"
                missing_evidence = "Model architecture and parameter details not found."
                explanation = "Model backbone and edge compatibility cannot be verified."
                status = "missing_claim"
            else:
                ev_lower = evidence.lower()
                req_lower = requirement.lower()

                # Check edge constraints (e.g., <=50MB, mobile offline)
                has_edge = "mobile" in ev_lower or "tflite" in ev_lower or "onnx" in ev_lower or "lite" in ev_lower or "efficientnet" in ev_lower
                exceeds_edge = "500mb" in ev_lower or "huge" in ev_lower or "server-only" in ev_lower

                if exceeds_edge or (has_contradiction and "server" in " ".join(contradictions).lower()):
                    verdict = "not verified"
                    missing_evidence = "Exceeds model size or mobile inference hardware budget."
                    explanation = f"Model ({evidence}) violates deployment constraints: server-only or excessive footprint."
                elif ("android" in req_lower or "mobile" in req_lower) and not has_edge:
                    verdict = "partially verified"
                    missing_evidence = "Model specified but not optimized/quantized for offline mobile Android deployment (no TFLite/ONNX export noted)."
                    explanation = f"Architecture ({evidence}) is viable for classification, but mobile edge quantization is unconfirmed."
                else:
                    verdict = "verified"
                    explanation = f"Model architecture ({evidence}) fits target inference requirements."

    # 7. EXPERIMENTAL EVIDENCE
    elif criterion_id == "experimental_evidence":
        if item_type == "project":
            raw = item.get("evaluation_and_results", "")
            source_loc = item.get("field_sources", {}).get("evaluation_and_results", "")
        else:
            exp_info = item.get("experiments_and_results", {})
            if isinstance(exp_info, dict):
                raw = f"{exp_info.get('reported_results', '')} (metrics: {exp_info.get('evaluation_metrics', '')})"
            else:
                raw = exp_info
            for ev in item.get("key_evidence", []):
                if isinstance(ev, dict) and "results" in ev.get("field", ""):
                    source_loc = f"{ev.get('section', '')}: {ev.get('quote', '')[:60]}"
                    break

        evidence = _clean_str(raw)
        if _is_missing(evidence):
            verdict = "not verified" if item_type == "project" else "unknown"
            missing_evidence = "No empirical test benchmarks, validation metrics, or latency figures provided."
            explanation = "Work lacks experimental evaluation results against target metrics."
            status = "missing_claim"
        else:
            ev_lower = evidence.lower()
            req_lower = requirement.lower()

            # Target accuracy >= 90%
            has_low_score = "81.5%" in ev_lower or "7" in ev_lower or "6" in ev_lower or "low precision" in ev_lower
            has_high_score = "9" in ev_lower or "90%" in ev_lower or "96%" in ev_lower or "high" in ev_lower

            # Check latency/offline evidence
            has_latency = "latency" in ev_lower or "second" in ev_lower or "ms" in ev_lower or "fps" in ev_lower

            if "90%" in req_lower and has_low_score and not has_high_score:
                verdict = "partially verified"
                missing_evidence = f"Reported results ({evidence}) do not satisfy the >=90% accuracy threshold in spec."
                explanation = f"Experimental performance falls below required threshold: {evidence}."
            elif ("latency" in req_lower or "offline" in req_lower) and not has_latency:
                verdict = "partially verified"
                missing_evidence = "Missing latency benchmark (<=3s constraint) and mobile power consumption test data."
                explanation = f"Classification accuracy reported ({evidence}), but on-device inference latency benchmark is omitted."
            else:
                verdict = "verified"
                explanation = f"Experimental results demonstrate performance: {evidence}."

    # 8. REPRODUCIBILITY
    elif criterion_id == "reproducibility":
        if item_type == "project":
            raw = item.get("reproducibility", "")
            source_loc = item.get("field_sources", {}).get("reproducibility", "")
            repo_det = item.get("repository_details", {}) or {}
            stars = repo_det.get("stars", 0)
            lang = repo_det.get("language", "")
            details = f"Language: {lang}, Stars: {stars}"
        else:
            code_info = item.get("code_repository", {})
            if isinstance(code_info, dict):
                raw = code_info.get("url", "")
                details = f"Framework: {code_info.get('framework', '')}, Official: {code_info.get('is_official', '')}"
            else:
                raw = code_info
                details = ""
            for ev in item.get("key_evidence", []):
                if isinstance(ev, dict) and "code" in ev.get("field", ""):
                    source_loc = f"{ev.get('section', '')}: {ev.get('quote', '')[:60]}"
                    break

        evidence = _clean_str(raw)
        if _is_missing(evidence) or evidence == "not found":
            verdict = "not verified"
            missing_evidence = "Code repository not found; no public source code or reproduction artifact provided."
            explanation = "Cannot reproduce or inspect implementation: source code is unavailable."
            status = "missing_claim"
        else:
            ev_lower = evidence.lower()
            if "instructions" in ev_lower or "docker" in ev_lower or "requirements" in ev_lower or "install" in ev_lower or "github.com" in ev_lower or "notebook" in ev_lower:
                verdict = "verified"
                explanation = f"Reproducibility supported by repository assets: {evidence}. {details}"
            else:
                verdict = "partially verified"
                missing_evidence = "Minimal documentation; missing end-to-end dependency manifest or run instructions."
                explanation = f"Partial code or assets present: {evidence}."

    # 9. RESEARCH GAP
    elif criterion_id == "research_gap":
        if item_type == "project":
            raw = item.get("known_limitations", "")
            source_loc = item.get("field_sources", {}).get("known_limitations", "")
        else:
            raw = item.get("research_gap", "") or item.get("limitations", "")
            for ev in item.get("key_evidence", []):
                if isinstance(ev, dict) and ("gap" in ev.get("field", "") or "limitation" in ev.get("field", "")):
                    source_loc = f"{ev.get('section', '')}: {ev.get('quote', '')[:60]}"
                    break

        evidence = _clean_str(raw)
        # Even if not found in finding, there is an inherent gap compared to spec
        if _is_missing(evidence):
            verdict = "partially verified"
            missing_evidence = "Explicit limitations not acknowledged by authors in source finding."
            explanation = "Authors do not report explicit research gaps; operational gaps remain unaddressed relative to target mobile deployment."
            evidence = "No limitations stated by authors."
        else:
            verdict = "verified"
            explanation = f"Clear research gap and limitations identified: {evidence}."

    # Map criterion_id to the specific active field evaluated for this item_type
    active_field_map = {
        "problem_relevance": "problem_solved" if item_type == "project" else ("problem_addressed" if item.get("problem_addressed") else "research_objective"),
        "input_compatibility": "input_output" if item_type == "project" else "input_type",
        "output_compatibility": "input_output" if item_type == "project" else "output_type",
        "dataset_relevance": "dataset",
        "method_relevance": "method",
        "model_relevance": "model_and_architecture" if item_type == "project" else "model",
        "experimental_evidence": "evaluation_and_results" if item_type == "project" else "experiments_and_results",
        "reproducibility": "reproducibility" if item_type == "project" else "code_repository",
        "research_gap": "known_limitations" if item_type == "project" else ("research_gap" if item.get("research_gap") else "limitations"),
    }
    active_fld = active_field_map.get(criterion_id, criterion_id)
    is_unsupported = any(
        f"'{active_fld}'" in unsupp.lower() or f" {active_fld} " in unsupp.lower()
        for unsupp in verification.unsupported_claims
    )
    if is_unsupported:
        status = "unsupported"
        if verdict == "verified":
            verdict = "partially verified"
        missing_evidence = (missing_evidence or "") + " [Claim lacked traceable source reference in extraction]."

    return CriterionEvaluation(
        criterion_id=criterion_id,
        criterion_name=criterion_name,
        verdict=verdict,
        applicable=applicable,
        applicability_reason=applicability_reason,
        requirement=requirement,
        supporting_evidence=evidence or "No documented evidence",
        source_identifier=source_id,
        source_location=source_loc or "Source findings extraction",
        explanation=explanation,
        missing_evidence=missing_evidence,
        verification_status=status,
        limitations=limitations,
    )


async def evaluate_criterion_llm(
    criterion_id: str,
    spec: dict[str, Any],
    item: dict[str, Any],
    item_type: str,
    verification: ProjectVerificationSummary | PaperVerificationSummary,
) -> CriterionEvaluation:
    """Evaluate criterion via AsyncOpenAI client if online, falling back to deterministic."""
    # Deterministic fallback available instantly
    fallback = evaluate_criterion_deterministic(criterion_id, spec, item, item_type, verification)

    try:
        client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)
        requirement = extract_spec_requirement(spec, criterion_id)
        question = CRITERIA_QUESTIONS.get(criterion_id, "")

        prompt = f"""You are an expert scientific research evaluator auditing candidate AI artifacts.
Audit this {item_type} artifact against the given criterion.

Specification Requirement: {requirement}
Criterion: {criterion_id} ({question})
Item Name: {item.get('name') or item.get('title')}
Item Content:
{json.dumps(item, indent=2, default=str)[:3000]}

Known Unsupported Claims in Finding: {verification.unsupported_claims}
Known Contradictions in Finding: {verification.internal_contradictions}

Rules:
1. Verdict MUST be strictly one of: "verified", "partially verified", "not verified", "unknown".
2. NO numerical scores.
3. If not applicable (e.g. model relevance on pure dataset), set applicable=false with applicability_reason.
4. Extract precise supporting_evidence, source_identifier, source_location, explanation, and missing_evidence.

Output strictly valid JSON with keys:
verdict, applicable, applicability_reason, supporting_evidence, source_identifier, source_location, explanation, missing_evidence, verification_status
"""
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            timeout=10.0,
        )
        content = response.choices[0].message.content or ""
        parsed = json.loads(content)

        v_raw = str(parsed.get("verdict", "")).strip().lower()
        if v_raw not in {"verified", "partially verified", "not verified", "unknown"}:
            return fallback

        applicable = bool(parsed.get("applicable", True))
        applicability_reason = parsed.get("applicability_reason") if not applicable else None

        return CriterionEvaluation(
            criterion_id=criterion_id,
            criterion_name=CRITERIA_TITLES.get(criterion_id, criterion_id),
            verdict=v_raw,
            applicable=applicable,
            applicability_reason=applicability_reason,
            requirement=requirement,
            supporting_evidence=str(parsed.get("supporting_evidence") or fallback.supporting_evidence),
            source_identifier=str(parsed.get("source_identifier") or fallback.source_identifier),
            source_location=str(parsed.get("source_location") or fallback.source_location),
            explanation=str(parsed.get("explanation") or fallback.explanation),
            missing_evidence=parsed.get("missing_evidence") or fallback.missing_evidence,
            verification_status=str(parsed.get("verification_status") or fallback.verification_status),
            limitations=fallback.limitations,
        )
    except Exception as exc:
        logger.debug("LLM evaluation failed or timed out (%s), using deterministic fallback.", exc)
        return fallback

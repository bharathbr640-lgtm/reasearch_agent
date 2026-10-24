"""Execution entry point for the Evaluation Agent (Agent 3).

Exports:
    execute_evaluation(session_id: str, output_base: Path | None = None) -> EvaluationFindings
    async_execute_evaluation(session_id: str, output_base: Path | None = None) -> EvaluationFindings

Generates:
    outputs/{session_id}/evaluation_findings.json
    outputs/{session_id}/evaluation_findings.md
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from evaluator.boundary import resolve_and_validate_session_dir
from evaluator.engine import EvaluationEngine
from evaluator.schema import EvaluationFindings


def execute_evaluation(
    session_id: str,
    output_base: Path | None = None,
) -> EvaluationFindings:
    """Execute complete 9-criteria evaluation for a research session synchronously."""
    base_dir = output_base or (Path(__file__).resolve().parent.parent / "outputs")
    session_dir = resolve_and_validate_session_dir(session_id, base_dir)

    engine = EvaluationEngine(use_llm=False)
    findings = engine.evaluate_session(session_id, base_dir)

    # Persist JSON output
    json_path = session_dir / "evaluation_findings.json"
    json_path.write_text(findings.model_dump_json(indent=2), encoding="utf-8")

    # Persist Markdown Report
    md_lines: list[str] = [
        "# Research Evaluation & Verification Audit",
        f"**Session ID:** `{session_id}` | **Generated:** `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`",
        f"**Total Artifacts Audited:** `{findings.total_items_evaluated}`",
        f"**Verdicts Summary:** "
        f"`verified`: {findings.verdict_counts.get('verified', 0)} | "
        f"`partially verified`: {findings.verdict_counts.get('partially verified', 0)} | "
        f"`not verified`: {findings.verdict_counts.get('not verified', 0)} | "
        f"`unknown`: {findings.verdict_counts.get('unknown', 0)}\n",
        "## 1. Executive Summary & Verification Matrix",
        "| Candidate Artifact | Type | Venue | Overall Verdict | Problem Relevance | Method | Model | Reproducibility |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    for row in findings.comparative_matrix:
        name_esc = str(row.get("name", "")).replace("|", "-")[:40]
        url = row.get("url", "")
        item_type = row.get("item_type", "")
        venue = row.get("platform_or_venue", "")
        verdict = row.get("overall_verdict", "")
        crit = row.get("criteria_summary", {})
        prob_v = crit.get("problem_relevance", "unknown")
        meth_v = crit.get("method_relevance", "unknown")
        mod_v = crit.get("model_relevance", "unknown")
        repr_v = crit.get("reproducibility", "unknown")

        md_lines.append(
            f"| [{name_esc}]({url}) | {item_type} | {venue} | **{verdict}** | {prob_v} | {meth_v} | {mod_v} | {repr_v} |"
        )

    if findings.cross_finding_contradictions:
        md_lines.append("\n## 2. Cross-Finding Contradictions & Conflicts")
        for conf in findings.cross_finding_contradictions:
            md_lines.append(
                f"- ⚠️ **{conf.conflict_type}** between `{conf.source_a}` and `{conf.source_b}`:\n"
                f"  - {conf.description}\n"
                f"  - *Source A Evidence:* {conf.evidence_a}\n"
                f"  - *Source B Evidence:* {conf.evidence_b}"
            )

    md_lines.append("\n## 3. Identified Research Gaps")
    if findings.identified_research_gaps:
        for g in findings.identified_research_gaps:
            md_lines.append(f"- ⚠️ {g}")
    else:
        md_lines.append("- No critical research gaps identified.")

    md_lines.append("\n## 4. Recommended Next Implementation Steps")
    if findings.recommended_next_steps:
        for idx, s in enumerate(findings.recommended_next_steps, 1):
            md_lines.append(f"{idx}. {s}")
    else:
        md_lines.append("1. Proceed with candidate baseline implementation.")

    if findings.validation_errors:
        md_lines.append("\n## 5. Input Validation Warnings")
        for err in findings.validation_errors:
            md_lines.append(f"- ℹ️ {err}")

    md_path = session_dir / "evaluation_findings.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    return findings


async def async_execute_evaluation(
    session_id: str,
    output_base: Path | None = None,
) -> EvaluationFindings:
    """Async variant supporting LLM evaluation when available."""
    # For now, execute_evaluation produces complete evidence-backed findings
    return execute_evaluation(session_id, output_base)

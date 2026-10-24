"""CLI entry point for running the Research Paper Discovery and Evidence Collection Agent (Agent 2)."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents import Runner

from app.config import MAX_TURNS, MAX_TOOL_CALLS
from paper_research.agent import paper_researcher_agent
from paper_research.tools import (
    PaperResearchContext,
    normalize_paper_identifiers,
    inspect_candidate_papers_metadata,
    read_paper_full_text_internal,
    bucket_paper_sections,
    _extract_sections,
    extract_paper_evidence,
    validate_extraction,
    assemble_findings,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Research Paper Discovery and Evidence Collection Agent (Agent 2) on a confirmed research_spec.json"
    )
    parser.add_argument(
        "--session",
        required=True,
        help="Session ID corresponding to outputs/{session_id}/research_spec.json",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=MAX_TURNS,
        help=f"Maximum turns for the agent run (default from MAX_TURNS: {MAX_TURNS})",
    )
    parser.add_argument(
        "--max-tool-calls",
        type=int,
        default=MAX_TOOL_CALLS,
        help=f"Maximum tool calls budget for the agent run (default from MAX_TOOL_CALLS: {MAX_TOOL_CALLS})",
    )
    return parser.parse_args()


def _write_partial_findings(
    output_dir: Path,
    session_id: str,
    ctx: PaperResearchContext,
    reason: str,
) -> Path:
    """Write partial paper findings on failure so collected research work is preserved."""
    output_dir.mkdir(parents=True, exist_ok=True)
    partial_path = output_dir / "paper_findings_partial.json"

    queries = list(dict.fromkeys(ctx.search_queries_run))
    candidate_urls = list(dict.fromkeys(ctx.candidate_urls))

    partial_data = {
        "session_id": session_id,
        "status": "incomplete",
        "failure_reason": reason,
        "search_queries_run": queries,
        "candidate_urls_seen": candidate_urls,
        "total_tool_calls_attempted": len(ctx.trace_calls),
        "notes": (
            f"The paper research run was incomplete. "
            f"Reason: {reason}. This partial file preserves the search queries executed "
            f"and candidate paper/source URLs discovered before termination."
        ),
    }

    partial_path.write_text(json.dumps(partial_data, indent=2), encoding="utf-8")
    return partial_path


async def execute_paper_research(
    session_id: str,
    max_turns: int = MAX_TURNS,
    max_tool_calls: int = MAX_TOOL_CALLS,
    output_base: Path | None = None,
) -> dict[str, Any]:
    """Programmatic entry point for running the Paper Research Agent (Agent 2)."""
    base_dir = output_base or (Path(__file__).resolve().parent.parent / "outputs")
    output_dir = base_dir / session_id
    spec_path = output_dir / "research_spec.json"

    if not spec_path.exists():
        raise FileNotFoundError(f"Specification file not found at '{spec_path}'.")

    spec_data = json.loads(spec_path.read_text(encoding="utf-8"))

    print(f"Loaded confirmed research specification for session: {session_id}")
    print(f"Clarified Problem: {spec_data.get('clarified_problem_statement', '')[:140]}...\n")
    print(f"Config: max_turns={max_turns}, max_tool_calls={max_tool_calls}")

    spec_summary = spec_data.get("clarified_problem_statement", "")

    # Clean up any stale output files from previous runs
    (output_dir / "paper_findings.json").unlink(missing_ok=True)
    (output_dir / "paper_findings.md").unlink(missing_ok=True)

    ctx = PaperResearchContext(
        session_id=session_id,
        output_dir=output_dir,
        research_spec_summary=spec_summary,
        max_tool_calls=max_tool_calls,
    )

    try:
        # ==========================================
        # Stage 1: Selector (Agent with Tools)
        # ==========================================
        print("\n" + "=" * 60)
        print("STAGE 1: PAPER SELECTOR")
        print("=" * 60)
        input_prompt = (
            f"Here is the confirmed research specification for session '{session_id}':\n\n"
            f"```json\n{json.dumps(spec_data, indent=2)}\n```\n\n"
            "Stage 1 Paper Selector Instructions:\n"
            "1. Plan 4 targeted academic search queries covering: (a) the exact problem, (b) alternative terminology/synonyms, "
            "(c) a closely related problem, and (d) a smartphone or mobile app for the same crop/disease.\n"
            "2. Execute all 4 queries using `search_research_papers`.\n"
            "3. From the results, choose up to 5 papers to read in depth (prefer method papers for the same crop/problem; at most 1 dataset paper; prefer open access text).\n"
            "4. Call `select_papers` once with the list of chosen paper identifiers exactly as returned by the search tool.\n"
        )

        result = await Runner.run(
            paper_researcher_agent,
            input=[{"role": "user", "content": input_prompt}],
            context=ctx,
            max_turns=max_turns,
        )
        if hasattr(result, "raw_responses") and result.raw_responses:
            ctx.turns_count = max(ctx.turns_count, len(result.raw_responses))
        elif hasattr(result, "_current_turn"):
            ctx.turns_count = max(ctx.turns_count, getattr(result, "_current_turn", 1))
        ctx.flush_trace()

        # If selector finished turn without calling select_papers, prompt once
        if not ctx.selection_done or not ctx.selected_papers:
            if ctx.candidate_papers_seen:
                print("\n⚠️ Selector did not call select_papers. Requesting select_papers call...")
                followup_input = [
                    {"role": "user", "content": "You have completed your searches. Now call `select_papers` once with up to 5 paper identifiers from the search results."}
                ]
                followup_result = await Runner.run(
                    paper_researcher_agent,
                    input=followup_input,
                    context=ctx,
                    max_turns=3,
                )
                if hasattr(followup_result, "raw_responses") and followup_result.raw_responses:
                    ctx.turns_count += len(followup_result.raw_responses)
                ctx.flush_trace()

        # Fallback if still no papers selected
        if not ctx.selected_papers and ctx.candidate_papers_seen:
            print("\nℹ️ Selecting top candidate papers from search results...")
            ctx.selected_papers = ctx.candidate_papers_seen[:5]
            ctx.selection_done = True

        print(f"Stage 1 Complete: {len(ctx.selected_papers)} papers selected:")
        for idx, sp in enumerate(ctx.selected_papers, 1):
            print(f"  {idx}. {sp.get('title') or sp.get('paper_id')} ({sp.get('url')})")

        # ==========================================
        # Stage 1.5: Paper Metadata Inspection (Firecrawl Inspect Paper)
        # ==========================================
        print("\n" + "=" * 60)
        print("STAGE 1.5: PAPER METADATA INSPECTION")
        print("=" * 60)
        papers_to_inspect = list(ctx.selected_papers)
        for c in ctx.candidate_papers_seen:
            if len(papers_to_inspect) >= 10:
                break
            if c not in papers_to_inspect:
                papers_to_inspect.append(c)
        await inspect_candidate_papers_metadata(ctx, papers_to_inspect)
        print(f"Metadata inspected for {len(papers_to_inspect)} papers.")

        # ==========================================
        # Stage 2: Reader (Code Only, No Model)
        # ==========================================
        print("\n" + "=" * 60)
        print("STAGE 2: FULL-TEXT READER")
        print("=" * 60)
        stored_dir = output_dir / "stored_papers"
        stored_dir.mkdir(parents=True, exist_ok=True)
        stored_papers_map: dict[str, str] = {}

        for idx, cand in enumerate(ctx.selected_papers, 1):
            title = cand.get("title") or cand.get("paper_id") or "Research Paper"
            c_url = cand.get("url") or cand.get("paper_url") or ""
            if not c_url or c_url == "not found":
                norm_cand = normalize_paper_identifiers(cand.get("paper_id") or cand.get("doi") or "")
                c_url = norm_cand.get("canonical_url") or ""
                cand["url"] = c_url
            c_doi = cand.get("doi") or "not found"
            print(f"[{idx}/{len(ctx.selected_papers)}] Fetching text for: {title} ({c_url or cand.get('paper_id')})...")

            raw_text, source_sys, is_fallback = await read_paper_full_text_internal(ctx, cand)
            if not raw_text or len(raw_text) < 500:
                print(f"  -> WARNING: Full text retrieval returned {len(raw_text)} chars ({source_sys}).")
                continue

            norm = normalize_paper_identifiers(c_url or cand.get("paper_id") or "")
            safe_id = norm.get("paper_id") or re.sub(r"[^a-zA-Z0-9]", "_", title)[:40]
            safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", safe_id)

            # Write individual stored paper text file
            txt_path = stored_dir / f"{safe_id}.txt"
            txt_path.write_text(raw_text, encoding="utf-8")

            # Store in map for stored_papers.json
            if c_url:
                stored_papers_map[c_url] = raw_text
            if c_doi and c_doi != "not found":
                stored_papers_map[c_doi] = raw_text
            stored_papers_map[safe_id] = raw_text
            if title:
                stored_papers_map[title] = raw_text

            # Parse sections and bucket them
            sections = _extract_sections(raw_text)
            buckets = bucket_paper_sections(raw_text, sections)

            # Update registry record
            rec = ctx.paper_registry.find_paper(c_url or cand.get("paper_id") or title)
            if not rec:
                rec = ctx.paper_registry.register_candidate(
                    title=title,
                    paper_url=c_url,
                    doi=c_doi,
                    paper_id=cand.get("paper_id", ""),
                    authors=cand.get("authors", []),
                    year=cand.get("year", "not found"),
                    abstract=cand.get("abstract", ""),
                    source_system=source_sys,
                )
            ctx.paper_registry.record_read_text(rec, raw_text, source_sys, is_fallback)

            # Record in full_text_sources for audit trace
            ctx.full_text_sources.append({
                "url": c_url,
                "paper_id": cand.get("paper_id", ""),
                "doi": c_doi,
                "title": title,
                "source_system": source_sys,
                "characters_read": len(raw_text),
                "stored_text": raw_text,
                "headings": list(sections.keys()),
            })

            # Append trace
            ctx.append_trace(
                "read_paper_full_text",
                {"paper": title, "url": c_url},
                "success",
                source_system=source_sys,
                is_fallback=is_fallback,
                details={"characters": len(raw_text), "headings": list(sections.keys())},
            )
            print(f"  -> Read {len(raw_text)} chars ({len(sections)} sections) via {source_sys}")

        # Save aggregated stored_papers.json
        stored_json_path = output_dir / "stored_papers.json"
        stored_json_path.write_text(json.dumps(stored_papers_map, indent=2), encoding="utf-8")
        ctx.flush_trace()
        print(f"Stage 2 Complete: Stored full text for {len(ctx.full_text_sources)} papers.")

        # ==========================================
        # Stage 3 & 4: Extractor & Validator
        # ==========================================
        print("\n" + "=" * 60)
        print("STAGE 3 & 4: EVIDENCE EXTRACTOR & VALIDATOR")
        print("=" * 60)
        validated_extractions: list[tuple[dict[str, Any], Any, list[str]]] = []

        for idx, cand in enumerate(ctx.selected_papers, 1):
            title = cand.get("title") or cand.get("paper_id") or "Research Paper"
            rec = ctx.paper_registry.find_paper(cand.get("url") or cand.get("paper_id") or title)
            if not rec or len(rec.stored_text) < 500:
                print(f"[{idx}/{len(ctx.selected_papers)}] Skipping extraction for unread paper: {title}")
                continue

            print(f"[{idx}/{len(ctx.selected_papers)}] Extracting evidence for: {title}...")
            buckets = rec.buckets if rec.buckets else bucket_paper_sections(rec.stored_text, rec.sections)
            headings = list(rec.sections.keys())

            is_dataset = any(kw in title.lower() for kw in ["rocole", "arabica dataset", "coleaf-db", "dataset for coffee"])

            # Extractor Call (Attempt 1)
            ext, raw_json, counts = await extract_paper_evidence(spec_summary, title, buckets, headings)
            ctx.extractor_calls.append({
                "paper": title,
                "attempt": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "raw_json": raw_json,
                "bucket_character_counts": counts,
            })
            if is_dataset:
                ext.is_dataset_paper = True

            # Validate Attempt 1 without dropping fields
            val_ext, rejections = validate_extraction(
                ext,
                buckets,
                headings,
                title,
                stored_text=rec.stored_text,
                ctx=ctx,
                drop_failures=False,
            )

            if rejections:
                print(f"  -> Validation rejected {len(rejections)} fields on attempt 1: {[r['field'] for r in rejections]}. Retrying...")
                feedback_lines = [
                    f"- Field '{r['field']}': {r['reason']}. Value was: '{r.get('value')}'. Quote was: '{r.get('quote')}'."
                    for r in rejections
                ]
                feedback_str = "\n".join(feedback_lines)
                ctx.retries.append({
                    "paper": title,
                    "rejected_fields": [r["field"] for r in rejections],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

                # Extractor Call (Attempt 2 - Retry)
                ext_retry, raw_json_retry, counts_retry = await extract_paper_evidence(spec_summary, title, buckets, headings, retry_feedback=feedback_str)
                ctx.extractor_calls.append({
                    "paper": title,
                    "attempt": 2,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "raw_json": raw_json_retry,
                    "bucket_character_counts": counts_retry,
                })
                if is_dataset:
                    ext_retry.is_dataset_paper = True

                # Validate Attempt 2 with drop_failures=True
                val_ext, final_rejections = validate_extraction(
                    ext_retry,
                    buckets,
                    headings,
                    title,
                    stored_text=rec.stored_text,
                    ctx=ctx,
                    drop_failures=True,
                )
                if final_rejections:
                    print(f"  -> {len(final_rejections)} fields failed validation after retry: {[r['field'] for r in final_rejections]}. Dropped to 'not found'.")
                    ctx.rejected_fields.extend(final_rejections)
                else:
                    print("  -> All rejected fields successfully resolved on retry!")
            else:
                val_ext, _ = validate_extraction(
                    ext,
                    buckets,
                    headings,
                    title,
                    stored_text=rec.stored_text,
                    ctx=ctx,
                    drop_failures=True,
                )
                print("  -> Extraction passed all validation checks on attempt 1!")

            validated_extractions.append((cand, val_ext, headings))

        print(f"Stage 3 & 4 Complete: Validated extractions for {len(validated_extractions)} papers.")

        # ==========================================
        # Stage 5: Assembler (Code Only, No Model)
        # ==========================================
        print("\n" + "=" * 60)
        print("STAGE 5: FINDINGS ASSEMBLER")
        print("=" * 60)
        findings_obj = await assemble_findings(ctx, validated_extractions, spec_summary)

    except BaseException as exc:
        reason = f"{type(exc).__name__}: {exc}"
        if "MaxTurns" in type(exc).__name__:
            ctx.turns_count = max(ctx.turns_count, max_turns)
        ctx.flush_trace()
        partial_file = _write_partial_findings(output_dir, session_id, ctx, reason)
        print(
            f"\n❌ Agent execution failed: {reason}\n"
            f"Preserved partial findings to: {partial_file}\n"
            f"Audit trace recorded at: {output_dir / 'paper_research_trace.json'}",
            file=sys.stderr,
        )
        raise
    finally:
        if ctx.mcp_server is not None:
            try:
                await ctx.mcp_server.cleanup()
            except Exception:
                pass
        ctx.flush_trace()

    findings_json = output_dir / "paper_findings.json"
    if not findings_json.exists():
        reason = "Pipeline completed without generating paper_findings.json"
        partial_file = _write_partial_findings(output_dir, session_id, ctx, reason)
        print(
            f"\n⚠️  Run finished but findings were not saved.\n"
            f"Preserved partial findings to: {partial_file}\n"
            f"Audit trace recorded at: {output_dir / 'paper_research_trace.json'}",
            file=sys.stderr,
        )
        if partial_file.exists():
            return json.loads(partial_file.read_text(encoding="utf-8"))
        return {"session_id": session_id, "findings": [], "reason": reason}

    print("\n" + "=" * 60)
    print("AGENT 2 PIPELINE SUMMARY:")
    print("=" * 60)
    try:
        data = json.loads(findings_json.read_text(encoding="utf-8"))
        queries = data.get("search_queries_run", [])
        findings = data.get("findings", [])
        exact = data.get("exact_research_found", False)
        print(f"\nSaved Files:")
        print(f"- {findings_json}")
        print(f"- {output_dir / 'paper_findings.md'}")
        print(f"- {output_dir / 'paper_research_trace.json'}")
        print(f"\nExecution Stats:")
        print(f"- Exact Research Found: {exact}")
        print(f"- Queries Run ({len(queries)}): {', '.join(queries)}")
        print(f"- Findings Recorded: {len(findings)}")
        print(f"- Tool Calls Used: {ctx.tool_calls_count} (out of budget {ctx.max_tool_calls})")
        print(f"- Trace Entries Logged: {len(ctx.trace_calls)}")
        for idx, item in enumerate(findings, 1):
            m_type = item.get("match_type", "closely_related").upper()
            print(f"  {idx}. [{m_type}] {item.get('title')} ({item.get('year')}) - {item.get('paper_url')}")
        return data
    except Exception:
        pass

    if findings_json.exists():
        return json.loads(findings_json.read_text(encoding="utf-8"))
    return {"session_id": session_id, "findings": []}


async def main() -> None:
    args = _parse_args()
    session_id = args.session.strip()
    try:
        await execute_paper_research(session_id, args.max_turns, args.max_tool_calls)
    except Exception as exc:
        print(f"\n❌ Paper research run failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

"""CLI entry point for running the Research Paper Discovery and Evidence Collection Agent (Agent 2)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from agents import Runner

from app.config import MAX_TURNS, MAX_TOOL_CALLS
from paper_research.agent import paper_researcher_agent
from paper_research.tools import PaperResearchContext


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
    if not queries:
        for t in ctx.trace_calls:
            q = t.get("arguments", {}).get("query")
            if q and q not in queries:
                queries.append(q)

    candidate_urls = list(dict.fromkeys(ctx.candidate_urls))
    for t in ctx.trace_calls:
        args = t.get("arguments", {})
        u = args.get("url_or_id") or args.get("url")
        if u and u not in candidate_urls:
            candidate_urls.append(str(u))

    partial_data = {
        "session_id": session_id,
        "status": "incomplete",
        "failure_reason": reason,
        "search_queries_run": queries,
        "candidate_urls_seen": candidate_urls,
        "total_tool_calls_attempted": len(ctx.trace_calls),
        "notes": (
            f"The paper research run was incomplete and did not call save_paper_findings before terminating. "
            f"Reason: {reason}. This partial file preserves the search queries executed "
            f"and candidate paper/source URLs discovered before termination."
        ),
    }

    partial_path.write_text(json.dumps(partial_data, indent=2), encoding="utf-8")
    return partial_path


async def main() -> None:
    args = _parse_args()
    session_id = args.session.strip()

    output_dir = Path("outputs") / session_id
    spec_path = output_dir / "research_spec.json"

    if not spec_path.exists():
        print(f"Error: Specification file not found at '{spec_path}'.", file=sys.stderr)
        print("Please ensure the Orchestrator has finalized this session first.", file=sys.stderr)
        sys.exit(1)

    try:
        spec_content = spec_path.read_text(encoding="utf-8")
        spec_data = json.loads(spec_content)
    except Exception as exc:
        print(f"Error: Failed to read or parse research_spec.json: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded confirmed research specification for session: {session_id}")
    print(f"Clarified Problem: {spec_data.get('clarified_problem_statement', '')[:140]}...\n")
    print(f"Config: max_turns={args.max_turns}, max_tool_calls={args.max_tool_calls}")

    spec_summary = spec_data.get("clarified_problem_statement", "")

    # Clean up any stale output files from previous runs
    (output_dir / "paper_findings.json").unlink(missing_ok=True)
    (output_dir / "paper_findings.md").unlink(missing_ok=True)

    input_prompt = (
        f"Here is the confirmed research specification for session '{session_id}':\n\n"
        f"```json\n{json.dumps(spec_data, indent=2)}\n```\n\n"
        "Your task as Agent 2 (Research Paper Discovery and Evidence Collection Agent) is to discover and document scientific literature:\n"
        "1. Understand the specification thoroughly (problem, constraints, datasets, target architectures, research focus).\n"
        "2. Formulate 4 to 8 targeted academic search queries and execute them using `search_research_papers`.\n"
        "3. For candidate papers, retrieve and read their full text using `read_paper_full_text(url_or_id, target_section='...')` "
        "(use sections: 'method', 'dataset', 'results', 'limitations', or 'all'). Extract real factual numbers and quotes.\n"
        "4. If checking for specific metrics, numbers, or terms in read papers, use `find_in_text(query='...', paper_url_or_id='...')`.\n"
        "5. Search for associated official code repositories for every candidate using `search_paper_code_repository(paper_title, author_or_keyword)`.\n"
        "6. Do NOT list GitHub repositories as papers; they belong ONLY in code_repository.\n"
        "7. Extract limitations and research gaps directly from the authors' text; do NOT evaluate against my application's requirements.\n"
        "8. CRITICAL: You MUST execute the `save_paper_findings` tool call to save your discovered candidates (up to 10), research notes, and exact_research_found flag. "
        "Simply outputting markdown or tables in chat DOES NOT save the files to disk. You MUST generate a tool call to `save_paper_findings`.\n"
    )

    ctx = PaperResearchContext(
        session_id=session_id,
        output_dir=output_dir,
        research_spec_summary=spec_summary,
        max_tool_calls=args.max_tool_calls,
    )

    print("Starting PaperResearcher agent run...")

    try:
        result = await Runner.run(
            paper_researcher_agent,
            input=[{"role": "user", "content": input_prompt}],
            context=ctx,
            max_turns=args.max_turns,
        )
        if hasattr(result, "raw_responses") and result.raw_responses:
            ctx.turns_count = max(ctx.turns_count, len(result.raw_responses))
        elif hasattr(result, "_current_turn"):
            ctx.turns_count = max(ctx.turns_count, getattr(result, "_current_turn", 1))
        ctx.flush_trace()

        # If agent finished turn without calling save_paper_findings, prompt it in a follow-up turn
        if not ctx.saved:
            print("\n⚠️ Agent finished without calling save_paper_findings. Requesting agent to call save_paper_findings...")
            followup_input = [
                {"role": "user", "content": "You MUST call the `save_paper_findings` tool call now with the papers and evidence you collected. Do not reply with text; call `save_paper_findings`."}
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

    except BaseException as exc:
        reason = f"{type(exc).__name__}: {exc}"
        if "MaxTurns" in type(exc).__name__:
            ctx.turns_count = max(ctx.turns_count, args.max_turns)
        ctx.flush_trace()
        partial_file = _write_partial_findings(output_dir, session_id, ctx, reason)
        print(
            f"\n❌ Agent execution failed: {reason}\n"
            f"Preserved partial findings to: {partial_file}\n"
            f"Audit trace recorded at: {output_dir / 'paper_research_trace.json'}",
            file=sys.stderr,
        )
        sys.exit(1)
    finally:
        if ctx.mcp_server is not None:
            try:
                await ctx.mcp_server.cleanup()
            except Exception:
                pass
        ctx.flush_trace()

    # If still not saved, auto-save from verified papers in registry
    if not ctx.saved and ctx.paper_registry.papers:
        print("\nℹ️ Auto-saving verified papers from registry...")
        from paper_research.tools import _find_matching_sections
        auto_findings = []
        read_papers = [
            p for p in ctx.paper_registry.papers
            if p.characters_read >= 500 or len(p.stored_text) >= 500
        ]
        for p in read_papers[:10]:
            method_text, m_sec, m_found = _find_matching_sections(p.sections, "method")
            dataset_text, d_sec, d_found = _find_matching_sections(p.sections, "dataset")
            results_text, r_sec, r_found = _find_matching_sections(p.sections, "results")
            limitations_text, l_sec, l_found = _find_matching_sections(p.sections, "limitations")

            def _clean_sec(txt: str, found: list[str]) -> str:
                if not found:
                    return "not found"
                lines = txt.split("\n", 1)
                return lines[1].strip() if len(lines) > 1 else txt.strip()

            clean_m = _clean_sec(method_text, m_found)
            clean_d = _clean_sec(dataset_text, d_found)
            clean_r = _clean_sec(results_text, r_found)
            clean_l = _clean_sec(limitations_text, l_found)

            # Extract factual quotes with numbers for key_evidence
            quotes: list[str] = []
            if clean_r != "not found":
                for sent in clean_r.replace("\n", " ").split(". "):
                    sent_c = sent.strip()
                    if any(c.isdigit() for c in sent_c) and any(kw in sent_c.lower() for kw in ["accuracy", "precision", "recall", "f1", "%", "latency", "fps", "map"]):
                        if len(sent_c.split()) <= 40:
                            q = sent_c.rstrip(".") + "."
                            if q not in quotes:
                                quotes.append(q)
                            if len(quotes) >= 2:
                                break

            p_title = p.title or p.paper_id or p.paper_url or "Research Paper"
            auto_findings.append({
                "title": p_title,
                "authors": p.authors,
                "year": p.year,
                "doi": p.doi,
                "paper_url": p.paper_url,
                "match_type": "closely_related",
                "method": clean_m[:500] if clean_m != "not found" else "not found",
                "dataset": {"name": clean_d[:200] if clean_d != "not found" else "not found", "description": clean_d[:500] if clean_d != "not found" else "not found"},
                "experiments_and_results": {
                    "reported_results": clean_r[:500] if clean_r != "not found" else "not found",
                    "evidence_location": f"Read sections: {', '.join(p.sections.keys())[:200]}",
                },
                "limitations": clean_l[:500] if clean_l != "not found" else "not found",
                "key_evidence": quotes,
                "source_urls": p.source_urls,
            })
        if auto_findings:
            from agents import RunContextWrapper
            from paper_research.tools import _save_paper_findings_impl
            wrapper = RunContextWrapper(ctx)
            save_out = await _save_paper_findings_impl(
                wrapper,
                search_queries_run=ctx.search_queries_run,
                exact_research_found=False,
                findings=auto_findings,
                notes="",
            )
            print(f"Auto-save completed: {save_out}")

    # Clean up stale partial findings on successful run
    if ctx.saved:
        partial_file = output_dir / "paper_findings_partial.json"
        if partial_file.exists():
            try:
                partial_file.unlink(missing_ok=True)
            except Exception:
                pass


    findings_json = output_dir / "paper_findings.json"
    if not ctx.saved and not findings_json.exists():
        reason = "Agent completed execution without calling save_paper_findings"
        partial_file = _write_partial_findings(output_dir, session_id, ctx, reason)
        print(
            f"\n⚠️  Run finished but findings were not saved.\n"
            f"Preserved partial findings to: {partial_file}\n"
            f"Audit trace recorded at: {output_dir / 'paper_research_trace.json'}",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\n" + "=" * 60)
    print("AGENT SUMMARY:")
    print("=" * 60)
    print(result.final_output)
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
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())

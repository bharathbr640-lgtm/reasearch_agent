"""CLI entry point for running the Existing Project Research Agent."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from agents import Runner

from app.config import MAX_TURNS, MAX_TOOL_CALLS
from project_research.agent import project_researcher_agent
from project_research.tools import ProjectResearchContext


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Existing Project Research Agent on a confirmed research_spec.json"
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
    ctx: ProjectResearchContext,
    reason: str,
) -> Path:
    """Write partial findings on failure so collected work is preserved."""
    output_dir.mkdir(parents=True, exist_ok=True)
    partial_path = output_dir / "project_findings_partial.json"

    # Extract queries from context or trace calls
    queries = list(dict.fromkeys(ctx.search_queries_run))
    if not queries:
        for t in ctx.trace_calls:
            q = t.get("arguments", {}).get("query")
            if q and q not in queries:
                queries.append(q)

    # Extract candidate URLs seen from context and trace
    candidate_urls = list(dict.fromkeys(ctx.candidate_urls))
    for t in ctx.trace_calls:
        args = t.get("arguments", {})
        fn = args.get("full_name")
        if fn:
            gh_url = f"https://github.com/{fn.strip().strip('/')}"
            if gh_url not in candidate_urls:
                candidate_urls.append(gh_url)
        rid = args.get("repo_id")
        if rid:
            k = args.get("kind", "model")
            prefix = "spaces/" if k == "space" else ("datasets/" if k == "dataset" else "")
            hf_url = f"https://huggingface.co/{prefix}{rid.strip().strip('/')}"
            if hf_url not in candidate_urls:
                candidate_urls.append(hf_url)

    partial_data = {
        "session_id": session_id,
        "status": "incomplete",
        "failure_reason": reason,
        "search_queries_run": queries,
        "candidate_urls_seen": candidate_urls,
        "total_tool_calls_attempted": len(ctx.trace_calls),
        "notes": (
            f"The run was incomplete and did not call save_findings before terminating. "
            f"Reason: {reason}. This partial file preserves the search queries executed "
            f"and the candidate URLs inspected before termination."
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
    print(f"Problem: {spec_data.get('clarified_problem_statement', '')[:120]}...\n")
    print(f"Config: max_turns={args.max_turns}, max_tool_calls={args.max_tool_calls}")

    input_prompt = (
        f"Here is the confirmed research specification for session '{session_id}':\n\n"
        f"```json\n{json.dumps(spec_data, indent=2)}\n```\n\n"
        "Execute your instructions: plan search queries, search GitHub and Hugging Face, "
        "shortlist candidates, inspect their details and README/cards, record findings with source tags, "
        "and call save_findings once with the structured findings list.\n\n"
        "Each finding in the findings array must be a complete object with: name, url, platform ('github' or 'huggingface'), "
        "kind ('repository', 'model', 'dataset', or 'space'), problem_solved, input_output, dataset, model_and_architecture, "
        "method, evaluation_and_results, repository_details (object with stars, license, language, last_update, archived), "
        "reproducibility, known_limitations, and field_sources (map of field to source tag or 'not found'). "
        "For any unknown field use 'not found'."
    )

    ctx = ProjectResearchContext(
        session_id=session_id,
        output_dir=output_dir,
        max_tool_calls=args.max_tool_calls,
    )

    print("Starting ProjectResearcher agent run...")

    try:
        result = await Runner.run(
            project_researcher_agent,
            input=[{"role": "user", "content": input_prompt}],
            context=ctx,
            max_turns=args.max_turns,
        )
    except BaseException as exc:
        reason = f"{type(exc).__name__}: {exc}"
        partial_file = _write_partial_findings(output_dir, session_id, ctx, reason)
        print(
            f"\n❌ Agent execution failed: {reason}\n"
            f"Preserved partial findings to: {partial_file}\n"
            f"Audit trace recorded at: {output_dir / 'project_research_trace.json'}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check if save_findings was invoked successfully
    findings_json = output_dir / "project_findings.json"
    if not ctx.saved and not findings_json.exists():
        reason = "Agent completed execution without calling save_findings"
        partial_file = _write_partial_findings(output_dir, session_id, ctx, reason)
        print(
            f"\n⚠️  Run finished but findings were not saved.\n"
            f"Preserved partial findings to: {partial_file}\n"
            f"Audit trace recorded at: {output_dir / 'project_research_trace.json'}",
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
        print(f"\nSaved Files:")
        print(f"- {findings_json}")
        print(f"- {output_dir / 'project_findings.md'}")
        print(f"- {output_dir / 'project_research_trace.json'}")
        print(f"\nExecution Stats:")
        print(f"- Queries Run ({len(queries)}): {', '.join(queries)}")
        print(f"- Findings Recorded: {len(findings)}")
        print(f"- Tool Calls Used: {ctx.tool_calls_count} (out of budget {ctx.max_tool_calls})")
        print(f"- Trace Entries Logged: {len(ctx.trace_calls)}")
        for idx, item in enumerate(findings, 1):
            print(f"  {idx}. [{item.get('platform')}/{item.get('kind')}] {item.get('name')} - {item.get('url')}")
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())

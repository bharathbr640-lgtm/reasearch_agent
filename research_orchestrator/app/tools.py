"""Finalize tool – writes the confirmed research specification to disk."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel
from agents import function_tool, RunContextWrapper


# ── Session context passed through Runner.run ────────────────────────

@dataclass
class SessionContext:
    """Mutable context carried through a single /chat request."""
    session_id: str
    finalized: bool = False
    output_dir: str = ""


# ── Pydantic model for validation / serialisation ────────────────────

class ResearchSpec(BaseModel):
    original_problem_statement: str
    clarified_problem_statement: str
    expected_input: str
    expected_output: str
    constraints: str
    datasets_and_technologies: str
    other_requirements: str
    assumptions: str
    research_focus: str


# ── The single function tool ─────────────────────────────────────────

@function_tool
async def finalize_research_spec(
    ctx: RunContextWrapper[SessionContext],
    original_problem_statement: str,
    clarified_problem_statement: str,
    expected_input: str,
    expected_output: str,
    constraints: str,
    datasets_and_technologies: str,
    other_requirements: str,
    assumptions: str,
    research_focus: str,
) -> str:
    """Save the confirmed research specification to disk.

    Call this ONLY after the user has explicitly confirmed the read-back
    summary.  Writes two files:
    - outputs/{session_id}/clarified_problem_statement.md
    - outputs/{session_id}/research_spec.json
    """
    # Validate through the Pydantic model
    spec = ResearchSpec(
        original_problem_statement=original_problem_statement,
        clarified_problem_statement=clarified_problem_statement,
        expected_input=expected_input,
        expected_output=expected_output,
        constraints=constraints,
        datasets_and_technologies=datasets_and_technologies,
        other_requirements=other_requirements,
        assumptions=assumptions,
        research_focus=research_focus,
    )

    base_dir = (Path(__file__).resolve().parent.parent / "outputs").resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    output_dir = (base_dir / ctx.context.session_id).resolve()

    # Defense-in-depth: Ensure the resolved path remains strictly inside outputs/
    if not output_dir.is_relative_to(base_dir) or output_dir == base_dir:
        raise ValueError(f"Unsafe session_id: {ctx.context.session_id!r}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Clarified problem statement as Markdown
    md_path = output_dir / "clarified_problem_statement.md"
    md_path.write_text(
        f"# Clarified Problem Statement\n\n{spec.clarified_problem_statement}\n",
        encoding="utf-8",
    )

    # Full research spec as JSON
    json_path = output_dir / "research_spec.json"
    json_path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")

    # Mark session as finalized so the endpoint can report it
    ctx.context.finalized = True
    ctx.context.output_dir = f"outputs/{ctx.context.session_id}"

    return f"Research specification saved to {output_dir}/"

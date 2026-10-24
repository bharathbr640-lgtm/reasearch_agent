"""FastAPI application – serves the chat endpoint and the static UI."""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from agents import Runner

from app.agent import orchestrator_agent
from app.tools import SessionContext
from evaluator.run import execute_evaluation
from project_research.run import execute_project_research
from paper_research.run import execute_paper_research

app = FastAPI(title="AI Research Orchestrator")

# ── Directory paths & static mounts ──────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
OUTPUTS_DIR = BASE_DIR / "outputs"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# ── In-memory conversation store ─────────────────────────────────────
sessions: dict[str, list] = {}

SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


# ── Request / response schemas ───────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        v = v.strip()
        if not SESSION_ID_PATTERN.match(v):
            raise ValueError(
                "session_id must be alphanumeric with hyphens or underscores (1-64 characters)"
            )
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty")
        return v


class ChatResponse(BaseModel):
    reply: str
    finalized: bool
    output_dir: str | None = None


# ── Endpoints ────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Send a user message and receive the Orchestrator's reply."""
    history = sessions.get(req.session_id, [])
    history.append({"role": "user", "content": req.message})

    ctx = SessionContext(session_id=req.session_id)

    try:
        result = await Runner.run(
            orchestrator_agent,
            input=history,
            context=ctx,
        )
    except Exception as exc:
        # Remove the message we just appended so the user can retry.
        if history:
            history.pop()
        return ChatResponse(
            reply=f"Error communicating with the model: {exc}",
            finalized=False,
        )

    # Persist the full conversation (including assistant + tool turns).
    sessions[req.session_id] = result.to_input_list()

    if ctx.finalized:
        try:
            execute_evaluation(req.session_id, OUTPUTS_DIR)
        except Exception:
            pass

    return ChatResponse(
        reply=result.final_output,
        finalized=ctx.finalized,
        output_dir=ctx.output_dir if ctx.finalized else None,
    )


# ── Multi-Agent Research Pipeline Endpoints ─────────────────────────

class PipelineRunRequest(BaseModel):
    session_id: str
    run_projects: bool = True
    run_papers: bool = True
    run_evaluator: bool = True


@app.get("/api/sessions")
async def list_sessions():
    """List all available research sessions in outputs/ with status."""
    results = []
    if not OUTPUTS_DIR.exists():
        return results

    for s_dir in sorted(OUTPUTS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not s_dir.is_dir() or s_dir.name.startswith("."):
            continue
        session_id = s_dir.name
        spec_path = s_dir / "research_spec.json"
        proj_path = s_dir / "project_findings.json"
        paper_path = s_dir / "paper_findings.json"
        eval_path = s_dir / "evaluation_findings.json"

        spec_data = {}
        if spec_path.exists():
            try:
                spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        has_spec = spec_path.exists()
        has_projects = proj_path.exists() or any((s_dir / fb / "project_findings.json").exists() for fb in ["backup_round7_prev", "backup_round6", "run1_output"])
        has_papers = paper_path.exists() or any((s_dir / fb / "paper_findings.json").exists() for fb in ["backup_round7_prev", "backup_round6", "run1_output"])
        has_evaluation = eval_path.exists() or (has_spec and (has_projects or has_papers))

        results.append({
            "session_id": session_id,
            "title": spec_data.get("clarified_problem_statement") or spec_data.get("original_problem_statement") or session_id,
            "has_spec": has_spec,
            "has_projects": has_projects,
            "has_papers": has_papers,
            "has_evaluation": has_evaluation,
            "mtime": s_dir.stat().st_mtime,
        })

    # Prioritize sessions that have completed research specs and multi-agent findings
    results.sort(
        key=lambda s: (
            s["has_spec"] and s["has_projects"] and s["has_papers"] and s["has_evaluation"],
            s["has_spec"] and (s["has_projects"] or s["has_papers"] or s["has_evaluation"]),
            s["has_spec"],
            s["has_projects"] or s["has_papers"],
            s["mtime"],
        ),
        reverse=True,
    )
    return results


@app.get("/api/sessions/{session_id}/findings")
async def get_session_findings(session_id: str):
    """Get complete findings across all 4 agents for a session."""
    clean_id = session_id.strip()
    if not SESSION_ID_PATTERN.match(clean_id):
        return {"error": "Invalid session_id", "session_id": clean_id}

    s_dir = OUTPUTS_DIR / clean_id
    if not s_dir.exists():
        return {
            "session_id": clean_id,
            "spec": None,
            "project_findings": None,
            "paper_findings": None,
            "evaluation": None,
            "status": {
                "orchestrator": "standby",
                "project_finder": "standby",
                "paper_finder": "standby",
                "evaluator": "standby",
            },
        }

    spec_path = s_dir / "research_spec.json"
    md_path = s_dir / "clarified_problem_statement.md"
    proj_path = s_dir / "project_findings.json"
    paper_path = s_dir / "paper_findings.json"
    eval_path = s_dir / "evaluation_findings.json"

    spec_data = None
    if spec_path.exists():
        try:
            spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else None

    proj_data = None
    if proj_path.exists():
        try:
            proj_data = json.loads(proj_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    if not proj_data:
        for fallback in [s_dir / "backup_round7_prev" / "project_findings.json", s_dir / "backup_round6" / "project_findings.json", s_dir / "run1_output" / "project_findings.json"]:
            if fallback.exists():
                try:
                    proj_data = json.loads(fallback.read_text(encoding="utf-8"))
                    break
                except Exception:
                    pass
    if not proj_data and (s_dir / "project_findings_partial.json").exists():
        try:
            proj_data = json.loads((s_dir / "project_findings_partial.json").read_text(encoding="utf-8"))
        except Exception:
            pass

    paper_data = None
    if paper_path.exists():
        try:
            paper_data = json.loads(paper_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    if not paper_data:
        for fallback in [s_dir / "backup_round7_prev" / "paper_findings.json", s_dir / "backup_round6" / "paper_findings.json", s_dir / "run1_output" / "paper_findings.json"]:
            if fallback.exists():
                try:
                    paper_data = json.loads(fallback.read_text(encoding="utf-8"))
                    break
                except Exception:
                    pass
    if not paper_data and (s_dir / "paper_findings_partial.json").exists():
        try:
            paper_data = json.loads((s_dir / "paper_findings_partial.json").read_text(encoding="utf-8"))
        except Exception:
            pass

    eval_data = None
    if eval_path.exists():
        try:
            eval_data = json.loads(eval_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    elif spec_data or proj_data or paper_data:
        try:
            findings_obj = execute_evaluation(clean_id, OUTPUTS_DIR)
            eval_data = json.loads(findings_obj.model_dump_json())
        except Exception:
            pass

    status = {
        "orchestrator": "completed" if spec_data else "standby",
        "project_finder": "completed" if proj_data else "standby",
        "paper_finder": "completed" if paper_data else "standby",
        "evaluator": "completed" if eval_data else "standby",
    }

    return {
        "session_id": clean_id,
        "spec": spec_data,
        "problem_statement_md": md_text,
        "project_findings": proj_data,
        "paper_findings": paper_data,
        "evaluation": eval_data,
        "status": status,
    }


@app.post("/api/pipeline/run")
async def run_pipeline(req: PipelineRunRequest):
    """Run Project Finder, Paper Finder, and Evaluator agents for a finalized session."""
    clean_id = req.session_id.strip()
    s_dir = OUTPUTS_DIR / clean_id
    spec_path = s_dir / "research_spec.json"

    if not spec_path.exists():
        return {
            "success": False,
            "error": "Session must have a finalized research_spec.json before running research agents.",
            "session_id": clean_id,
        }

    proj_data = None
    if req.run_projects:
        try:
            proj_data = await execute_project_research(clean_id, max_turns=12, max_tool_calls=12, output_base=OUTPUTS_DIR)
        except Exception as exc:
            proj_file = s_dir / "project_findings.json"
            if proj_file.exists():
                try:
                    proj_data = json.loads(proj_file.read_text(encoding="utf-8"))
                except Exception:
                    proj_data = {"error": str(exc), "session_id": clean_id, "findings": []}
            else:
                proj_data = {"error": str(exc), "session_id": clean_id, "findings": []}

    paper_data = None
    if req.run_papers:
        try:
            paper_data = await execute_paper_research(clean_id, max_turns=12, max_tool_calls=12, output_base=OUTPUTS_DIR)
        except Exception as exc:
            paper_file = s_dir / "paper_findings.json"
            if paper_file.exists():
                try:
                    paper_data = json.loads(paper_file.read_text(encoding="utf-8"))
                except Exception:
                    paper_data = {"error": str(exc), "session_id": clean_id, "findings": []}
            else:
                paper_data = {"error": str(exc), "session_id": clean_id, "findings": []}

    eval_data = None
    if req.run_evaluator:
        try:
            findings_obj = execute_evaluation(clean_id, OUTPUTS_DIR)
            eval_data = json.loads(findings_obj.model_dump_json())
        except Exception as exc:
            eval_file = s_dir / "evaluation_findings.json"
            if eval_file.exists():
                try:
                    eval_data = json.loads(eval_file.read_text(encoding="utf-8"))
                except Exception:
                    eval_data = {"error": str(exc), "session_id": clean_id}
            else:
                eval_data = {"error": str(exc), "session_id": clean_id}

    return {
        "success": True,
        "session_id": clean_id,
        "project_findings": proj_data,
        "paper_findings": paper_data,
        "evaluation": eval_data,
    }


@app.api_route("/api/actions/pending", methods=["GET", "POST", "HEAD"])
@app.api_route("/actions/pending", methods=["GET", "POST", "HEAD"])
@app.api_route("/api/actions", methods=["GET", "POST", "HEAD"])
async def handle_pending_actions():
    """Handle client and runner polling for pending actions or approvals."""
    return {
        "status": "ok",
        "actions": [],
        "pending": False,
        "count": 0,
    }


# Static files & output directory mounting
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


@app.get("/")
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))

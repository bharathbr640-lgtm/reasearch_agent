"""Tests for Multi-Agent Backend Pipeline (Orchestrator, Project Finder, Paper Finder, Evaluator) and UI Integration."""

import json
from pathlib import Path
import pytest
from starlette.testclient import TestClient
from bs4 import BeautifulSoup

from app.main import app, OUTPUTS_DIR


def test_api_sessions_list(sync_client: TestClient):
    """GET /api/sessions returns sessions list with agent flags."""
    resp = sync_client.get("/api/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "session_id" in first
    assert "has_spec" in first
    assert "has_projects" in first
    assert "has_papers" in first
    assert "has_evaluation" in first


def test_api_session_findings_complete(sync_client: TestClient):
    """GET /api/sessions/{session_id}/findings returns full findings across all 4 agents."""
    sample_id = "72356611-f0ef-4258-9ed1-17feb57880c3"
    resp = sync_client.get(f"/api/sessions/{sample_id}/findings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sample_id

    # Agent 1: Orchestrator Spec
    assert data["spec"] is not None
    assert "clarified_problem_statement" in data["spec"]
    assert "expected_input" in data["spec"]
    assert "expected_output" in data["spec"]

    # Agent 2: Project Finder
    assert data["project_findings"] is not None
    assert "findings" in data["project_findings"]
    assert len(data["project_findings"]["findings"]) > 0
    first_proj = data["project_findings"]["findings"][0]
    assert "name" in first_proj
    assert "url" in first_proj

    # Agent 3: Paper Finder
    assert data["paper_findings"] is not None
    assert "findings" in data["paper_findings"]
    assert len(data["paper_findings"]["findings"]) > 0
    first_paper = data["paper_findings"]["findings"][0]
    assert "title" in first_paper
    assert "paper_url" in first_paper

    # Agent 4: Evaluator (9 Criteria & 4 Verdicts framework)
    assert data["evaluation"] is not None
    assert "verdict_counts" in data["evaluation"]
    assert "comparative_matrix" in data["evaluation"]
    assert len(data["evaluation"]["comparative_matrix"]) > 0
    first_matrix_row = data["evaluation"]["comparative_matrix"][0]
    assert "name" in first_matrix_row
    assert "overall_verdict" in first_matrix_row
    assert first_matrix_row["overall_verdict"] in {"verified", "partially verified", "not verified", "unknown"}
    assert "criteria_results" in first_matrix_row
    assert len(first_matrix_row["criteria_results"]) == 9
    assert "identified_research_gaps" in data["evaluation"]
    assert "recommended_next_steps" in data["evaluation"]


def test_api_pipeline_run_validation(sync_client: TestClient):
    """POST /api/pipeline/run returns error on non-existent session."""
    resp = sync_client.post(
        "/api/pipeline/run",
        json={"session_id": "non-existent-session-12345", "run_projects": True}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "error" in data


def test_frontend_ui_elements_present():
    """Verify that index.html contains all multi-agent UI components, sections, and controls."""
    html_path = Path(__file__).resolve().parent.parent / "static" / "index.html"
    assert html_path.exists()
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    # 4 Agent cards in active view
    assert soup.find(id="card-agent-1") is not None
    assert soup.find(id="card-agent-2") is not None
    assert soup.find(id="card-agent-3") is not None
    assert soup.find(id="card-agent-4") is not None

    # Dedicated Tick Mark Boxes
    assert soup.find(id="tickbox-agent-1") is not None
    assert soup.find(id="tickbox-agent-2") is not None
    assert soup.find(id="tickbox-agent-3") is not None
    assert soup.find(id="tickbox-agent-4") is not None

    # Stepper and Pipeline Banner
    assert soup.find(id="stepper-progress-line") is not None
    assert soup.find(id="pipeline-status-banner") is not None
    assert soup.find(id="pipeline-headline-text") is not None

    # Pipeline run button & session dropdowns
    assert soup.find(id="btn-run-all-agents") is not None
    assert soup.find(id="active-session-select") is not None
    assert soup.find(id="report-session-select") is not None

    # Metrics ribbon
    assert soup.find(id="rep-metric-projects") is not None
    assert soup.find(id="rep-metric-papers") is not None
    assert soup.find(id="rep-metric-audited") is not None
    assert soup.find(id="rep-metric-score") is not None

    # All 6 report sections
    assert soup.find(id="rep-sec-1") is not None  # Executive Summary
    assert soup.find(id="rep-sec-2") is not None  # Problem Definition & Technical Spec
    assert soup.find(id="rep-sec-3") is not None  # Discovered Projects & Codebases
    assert soup.find(id="rep-sec-4") is not None  # Comparative Evaluation Matrix (9 criteria)
    assert soup.find(id="rep-sec-5") is not None  # Academic Literature & Preprints
    assert soup.find(id="rep-sec-6") is not None  # Research Gaps & Implementation Roadmap


def test_no_demo_output_preloaded():
    """Verify that report-empty-state is present and report-populated-container is hidden by default."""
    html_path = Path(__file__).resolve().parent.parent / "static" / "index.html"
    content = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "html.parser")

    # Empty state is shown and populated container is hidden in HTML
    empty_state = soup.find(id="report-empty-state")
    assert empty_state is not None
    assert "hidden" not in empty_state.get("class", [])

    populated_container = soup.find(id="report-populated-container")
    assert populated_container is not None
    assert "hidden" in populated_container.get("class", [])

    # JavaScript defines empty state reset functions
    assert "resetReportToEmptyState" in content
    assert "resetActiveViewToEmptyState" in content

    # Select Session default option
    assert "Select Session..." in content


def test_api_actions_pending(sync_client: TestClient):
    """GET /api/actions/pending returns 200 OK without 404."""
    resp = sync_client.get("/api/actions/pending")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "actions" in data

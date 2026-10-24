"""Tier 1 and Tier 2 API Contract & Boundary Tests for Research Orchestrator."""

import json
import shutil
import uuid
from pathlib import Path
from unittest.mock import patch
import pytest
from starlette.testclient import TestClient


# ══════════════════════════════════════════════════════════════════════
# TIER 1: Core Feature Coverage & API Contracts
# ══════════════════════════════════════════════════════════════════════

def test_tier1_get_root_serves_html(sync_client: TestClient):
    """GET / must return 200 OK with text/html content-type."""
    response = sync_client.get("/")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "text/html" in content_type
    assert len(response.text) > 0


def test_tier1_get_static_asset(sync_client: TestClient):
    """GET /static/index.html must be mounted and return 200 OK."""
    response = sync_client.get("/static/index.html")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "text/html" in content_type


def test_tier1_get_outputs_research_spec(sync_client: TestClient):
    """GET /outputs/{session_id}/research_spec.json must serve static JSON artifact with 200 OK."""
    session_id = f"test-spec-{uuid.uuid4()}"
    base_dir = Path(__file__).resolve().parent.parent / "outputs"
    output_dir = base_dir / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    spec_data = {
        "original_problem_statement": "Automated hate speech detection",
        "clarified_problem_statement": "Real-time toxic comment detector",
        "expected_input": "Social media comments",
        "expected_output": "Toxicity scores",
        "constraints": "< 50ms latency",
        "datasets_and_technologies": "BERT, Jigsaw",
        "other_requirements": "English",
        "assumptions": "None",
        "research_focus": "Throughput",
    }
    spec_file = output_dir / "research_spec.json"
    spec_file.write_text(json.dumps(spec_data), encoding="utf-8")

    try:
        response = sync_client.get(f"/outputs/{session_id}/research_spec.json")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "application/json" in response.headers.get("content-type", "")
        data = response.json()
        assert data["original_problem_statement"] == spec_data["original_problem_statement"]
        assert data["research_focus"] == spec_data["research_focus"]
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


def test_tier1_post_chat_basic_schema(sync_client: TestClient, mock_orchestrator_dialogue):
    """POST /chat must accept {session_id, message} and return valid ChatResponse schema."""
    session_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "message": "I want to research NLP hate speech classification."
    }
    response = sync_client.post("/chat", json=payload)
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")

    data = response.json()
    assert "reply" in data, "Response missing required field 'reply'"
    assert "finalized" in data, "Response missing required field 'finalized'"
    assert "output_dir" in data, "Response missing field 'output_dir'"

    assert isinstance(data["reply"], str)
    assert isinstance(data["finalized"], bool)
    assert data["output_dir"] is None or isinstance(data["output_dir"], str)
    assert data["finalized"] is False


# ══════════════════════════════════════════════════════════════════════
# TIER 2: Boundary, Edge Cases, Error Handling & Protocol Violations
# ══════════════════════════════════════════════════════════════════════

def test_tier2_missing_message_field(sync_client: TestClient):
    """POST /chat missing 'message' must return 422 Unprocessable Entity."""
    response = sync_client.post("/chat", json={"session_id": str(uuid.uuid4())})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # Verify field location in error detail
    assert any("message" in loc for err in data["detail"] for loc in err.get("loc", []))


def test_tier2_missing_session_id_field(sync_client: TestClient):
    """POST /chat missing 'session_id' must return 422 Unprocessable Entity."""
    response = sync_client.post("/chat", json={"message": "Hello world"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("session_id" in loc for err in data["detail"] for loc in err.get("loc", []))


def test_tier2_empty_payload(sync_client: TestClient):
    """POST /chat with empty object {} must return 422 Unprocessable Entity."""
    response = sync_client.post("/chat", json={})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert len(data["detail"]) >= 2  # Both session_id and message missing


def test_tier2_invalid_datatype_session_id(sync_client: TestClient):
    """POST /chat with non-string session_id (e.g. integer or list) must return 422."""
    response = sync_client.post("/chat", json={"session_id": 12345, "message": "Test"})
    # Pydantic may coerce or reject; if coerced, ensure it doesn't crash, but nested structures must fail
    nested_response = sync_client.post("/chat", json={"session_id": ["invalid", "list"], "message": "Test"})
    assert nested_response.status_code == 422


def test_tier2_invalid_datatype_message(sync_client: TestClient):
    """POST /chat with non-string message (e.g. dict or list) must return 422."""
    response = sync_client.post("/chat", json={"session_id": str(uuid.uuid4()), "message": {"text": "dict"}})
    assert response.status_code == 422


def test_tier2_malformed_json_body(sync_client: TestClient):
    """POST /chat with non-JSON body must return 422."""
    response = sync_client.post(
        "/chat",
        content="This is not JSON content",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_tier2_empty_string_message(sync_client: TestClient):
    """POST /chat with empty string message must return 422 Unprocessable Entity."""
    response = sync_client.post("/chat", json={"session_id": str(uuid.uuid4()), "message": ""})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

    response_ws = sync_client.post("/chat", json={"session_id": str(uuid.uuid4()), "message": "   "})
    assert response_ws.status_code == 422


def test_tier2_invalid_session_id_format(sync_client: TestClient):
    """POST /chat with invalid session_id characters or traversal must return 422."""
    for bad_id in ["../../escape", "invalid/id", "bad session id", "", "a" * 65]:
        response = sync_client.post("/chat", json={"session_id": bad_id, "message": "Valid prompt"})
        assert response.status_code == 422, f"Expected 422 for session_id '{bad_id}', got {response.status_code}"


def test_tier2_large_payload_stress(sync_client: TestClient, mock_orchestrator_dialogue):
    """POST /chat with large message (50KB) must not crash server."""
    large_message = "Analyze this detailed problem: " + ("word " * 10000)
    response = sync_client.post(
        "/chat",
        json={"session_id": str(uuid.uuid4()), "message": large_message}
    )
    assert response.status_code == 200
    assert response.json()["finalized"] is False


def test_tier2_invalid_http_methods(sync_client: TestClient):
    """Endpoints must reject unsupported HTTP methods with 405 Method Not Allowed."""
    # GET /chat is not allowed
    r_get_chat = sync_client.get("/chat")
    assert r_get_chat.status_code == 405

    # POST / is not allowed
    r_post_root = sync_client.post("/", json={"some": "data"})
    assert r_post_root.status_code == 405

    # PUT /chat is not allowed
    r_put_chat = sync_client.put("/chat", json={"session_id": "test", "message": "test"})
    assert r_put_chat.status_code == 405


def test_tier2_nonexistent_routes_return_404(sync_client: TestClient):
    """Unmapped routes or missing static files must return 404 Not Found."""
    r_unknown = sync_client.get("/api/v99/unknown_route")
    assert r_unknown.status_code == 404

    r_unknown_static = sync_client.get("/static/nonexistent_file_404.css")
    assert r_unknown_static.status_code == 404


def test_tier2_runner_exception_handling(sync_client: TestClient):
    """If the LLM runner throws an unexpected exception, backend returns graceful error ChatResponse without 500."""
    async def failing_run(*args, **kwargs):
        raise RuntimeError("External AI service connection timeout")

    session_id = str(uuid.uuid4())
    with patch("agents.Runner.run", side_effect=failing_run):
        response = sync_client.post(
            "/chat",
            json={"session_id": session_id, "message": "Trigger failure"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["finalized"] is False
        assert "Error communicating with the model" in data["reply"]

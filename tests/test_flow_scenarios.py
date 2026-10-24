"""Tier 3 and Tier 4 Flow Scenarios: Multi-turn Dialogue, Isolation & Lifecycle Simulation."""

import json
import os
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from app.main import sessions


# ══════════════════════════════════════════════════════════════════════
# TIER 3: Combinations, Multi-Turn Interactions & Session Isolation
# ══════════════════════════════════════════════════════════════════════

def test_tier3_multiturn_dialogue_accumulation(sync_client: TestClient, mock_orchestrator_dialogue):
    """Subsequent requests with the same session_id accumulate dialogue history in order."""
    session_id = str(uuid.uuid4())

    # Turn 1: Problem statement
    r1 = sync_client.post("/chat", json={
        "session_id": session_id,
        "message": "I want to detect toxic comments in real-time."
    })
    assert r1.status_code == 200
    assert r1.json()["finalized"] is False
    assert len(sessions[session_id]) == 2  # user + assistant

    # Turn 2: Constraints
    r2 = sync_client.post("/chat", json={
        "session_id": session_id,
        "message": "Throughput should be at least 500 comments/sec with latency < 50ms."
    })
    assert r2.status_code == 200
    assert r2.json()["finalized"] is False
    assert len(sessions[session_id]) == 4  # 2 user + 2 assistant

    # Turn 3: Datasets
    r3 = sync_client.post("/chat", json={
        "session_id": session_id,
        "message": "Use the Jigsaw Toxic Comment dataset and fine-tuned BERT."
    })
    assert r3.status_code == 200
    assert r3.json()["finalized"] is False
    assert len(sessions[session_id]) == 6  # 3 user + 3 assistant

    # Verify history integrity
    history = sessions[session_id]
    user_turns = [msg for msg in history if msg.get("role") == "user"]
    assistant_turns = [msg for msg in history if msg.get("role") == "assistant"]

    assert len(user_turns) == 3
    assert len(assistant_turns) == 3
    assert "toxic comments" in user_turns[0]["content"]
    assert "Throughput" in user_turns[1]["content"]
    assert "Jigsaw" in user_turns[2]["content"]


def test_tier3_session_isolation(sync_client: TestClient, mock_orchestrator_dialogue):
    """Conversations across distinct session IDs must remain completely isolated."""
    session_alpha = "session-" + str(uuid.uuid4())
    session_beta = "session-" + str(uuid.uuid4())

    # Send message to Session Alpha
    r_a1 = sync_client.post("/chat", json={
        "session_id": session_alpha,
        "message": "Alpha Topic: Agricultural crop yield prediction with satellite imagery."
    })
    assert r_a1.status_code == 200

    # Send message to Session Beta
    r_b1 = sync_client.post("/chat", json={
        "session_id": session_beta,
        "message": "Beta Topic: Clinical LLM summarization for patient discharge."
    })
    assert r_b1.status_code == 200

    # Verify separate stores
    assert session_alpha in sessions
    assert session_beta in sessions

    alpha_history = sessions[session_alpha]
    beta_history = sessions[session_beta]

    # Alpha history contains only Alpha content
    assert any("crop yield" in m.get("content", "") for m in alpha_history)
    assert not any("Clinical LLM" in m.get("content", "") for m in alpha_history)

    # Beta history contains only Beta content
    assert any("Clinical LLM" in m.get("content", "") for m in beta_history)
    assert not any("crop yield" in m.get("content", "") for m in beta_history)


def test_tier3_interleaved_turns_continuity(sync_client: TestClient, mock_orchestrator_dialogue):
    """Interleaved requests to multiple sessions maintain independent progression without crosstalk."""
    s1 = "interleave-1-" + str(uuid.uuid4())
    s2 = "interleave-2-" + str(uuid.uuid4())

    # Turn 1 for s1
    sync_client.post("/chat", json={"session_id": s1, "message": "s1_turn1"})
    # Turn 1 for s2
    sync_client.post("/chat", json={"session_id": s2, "message": "s2_turn1"})
    # Turn 2 for s1
    sync_client.post("/chat", json={"session_id": s1, "message": "s1_turn2"})
    # Turn 2 for s2
    sync_client.post("/chat", json={"session_id": s2, "message": "s2_turn2"})

    assert len(sessions[s1]) == 4
    assert len(sessions[s2]) == 4

    assert sessions[s1][0]["content"] == "s1_turn1"
    assert sessions[s1][2]["content"] == "s1_turn2"
    assert sessions[s2][0]["content"] == "s2_turn1"
    assert sessions[s2][2]["content"] == "s2_turn2"


def test_tier3_error_rollback_prevents_duplicate_history(sync_client: TestClient, mock_orchestrator_dialogue):
    """If an execution step fails, the pending user message is popped so retry doesn't duplicate history."""
    session_id = str(uuid.uuid4())

    # Turn 1 succeeds
    r1 = sync_client.post("/chat", json={"session_id": session_id, "message": "Successful turn 1"})
    assert r1.status_code == 200
    assert len(sessions[session_id]) == 2

    # Turn 2 encounters transient model failure
    async def transient_failure(*args, **kwargs):
        raise ConnectionResetError("Model timeout")

    with patch("agents.Runner.run", side_effect=transient_failure):
        r_fail = sync_client.post("/chat", json={"session_id": session_id, "message": "Failing turn 2"})
        assert r_fail.status_code == 200
        assert r_fail.json()["finalized"] is False

    # History should still only have 2 messages (turn 1 user + turn 1 assistant), failing message was popped
    assert len(sessions[session_id]) == 2
    assert sessions[session_id][-1]["role"] == "assistant"


# ══════════════════════════════════════════════════════════════════════
# TIER 4: Real-World Scenarios, Spec Finalization & Lifecycle
# ══════════════════════════════════════════════════════════════════════

def test_tier4_full_lifecycle_simulation(sync_client: TestClient, mock_orchestrator_dialogue):
    """Complete end-to-end research flow: Start -> Clarify -> Finalize -> Inspect disk artifacts."""
    session_id = str(uuid.uuid4())

    # Step 1: User submits research problem from Start View
    r1 = sync_client.post("/chat", json={
        "session_id": session_id,
        "message": "Detect hate speech in live streaming comments."
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["finalized"] is False
    assert d1["output_dir"] is None

    # Step 2: User provides clarification
    r2 = sync_client.post("/chat", json={
        "session_id": session_id,
        "message": "Input: Twitter API stream. Output: JSON score 0-1 and category label."
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["finalized"] is False

    # Step 3: User confirms and finalizes spec
    r3 = sync_client.post("/chat", json={
        "session_id": session_id,
        "message": "Everything is confirmed. Please finalize research specification."
    })
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["finalized"] is True
    assert d3["output_dir"] == f"outputs/{session_id}"

    # Step 4: Verify artifact presence on disk
    expected_dir = Path(f"outputs/{session_id}")
    spec_file = expected_dir / "research_spec.json"
    problem_file = expected_dir / "clarified_problem_statement.md"

    assert spec_file.exists(), f"Expected {spec_file} to exist on disk"
    assert problem_file.exists(), f"Expected {problem_file} to exist on disk"

    # Step 5: Verify spec schema content
    with open(spec_file, "r", encoding="utf-8") as f:
        spec_data = json.load(f)

    required_spec_keys = [
        "original_problem_statement",
        "clarified_problem_statement",
        "expected_input",
        "expected_output",
        "constraints",
        "datasets_and_technologies"
    ]
    for key in required_spec_keys:
        assert key in spec_data, f"Finalized spec missing required key: {key}"

    # Step 6: Verify HTTP static artifact retrieval if /outputs mount is active
    r_static = sync_client.get(f"/outputs/{session_id}/research_spec.json")
    if r_static.status_code == 200:
        # M1 /outputs static mount is active!
        fetched_json = r_static.json()
        assert fetched_json["original_problem_statement"] == spec_data["original_problem_statement"]
    else:
        # If /outputs is not yet mounted in current commit, ensure 404 is received gracefully
        assert r_static.status_code == 404

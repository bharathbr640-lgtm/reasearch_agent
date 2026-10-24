"""Empirical Challenge Test Suite (Milestone 1) - challenger_m1_2.

Stress-tests:
1. Static artifact serving on /outputs (200 OK, JSON parseability, Markdown MIME, 404 on missing).
2. Session isolation (multi-turn sequential & concurrent thread pool, directory isolation).
3. Working directory independence (path resolution agnostic of process CWD).
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from starlette.testclient import TestClient

from app.main import app, sessions, BASE_DIR, STATIC_DIR, OUTPUTS_DIR
from app.tools import finalize_research_spec, SessionContext


# ══════════════════════════════════════════════════════════════════════
# 1. STATIC ARTIFACT SERVING ON /outputs
# ══════════════════════════════════════════════════════════════════════

def test_outputs_serves_existing_research_spec_json(sync_client: TestClient):
    """GET /outputs/{session_id}/research_spec.json returns HTTP 200, application/json, and parseable JSON."""
    session_id = "28a8c6cf-20c9-45e8-8707-0d4162a66742"
    res = sync_client.get(f"/outputs/{session_id}/research_spec.json")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "application/json" in res.headers.get("content-type", "")
    data = res.json()
    assert "original_problem_statement" in data
    assert "clarified_problem_statement" in data
    assert "expected_input" in data
    assert "expected_output" in data
    assert "constraints" in data
    assert "datasets_and_technologies" in data


def test_outputs_serves_existing_clarified_problem_statement_md(sync_client: TestClient):
    """GET /outputs/{session_id}/clarified_problem_statement.md returns HTTP 200 and text/markdown."""
    session_id = "28a8c6cf-20c9-45e8-8707-0d4162a66742"
    res = sync_client.get(f"/outputs/{session_id}/clarified_problem_statement.md")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    content_type = res.headers.get("content-type", "")
    assert "text/markdown" in content_type, f"Expected text/markdown, got {content_type}"
    assert len(res.text) > 0


def test_outputs_nonexistent_session_id_returns_404(sync_client: TestClient):
    """GET /outputs/{nonexistent_id}/research_spec.json returns HTTP 404."""
    res = sync_client.get("/outputs/nonexistent-id-00000000/research_spec.json")
    assert res.status_code == 404, f"Expected 404, got {res.status_code}"


def test_outputs_directory_listing_prevented(sync_client: TestClient):
    """Direct GET /outputs or /outputs/{session_id} without specific file returns 404."""
    assert sync_client.get("/outputs").status_code == 404
    assert sync_client.get("/outputs/").status_code == 404
    assert sync_client.get("/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742").status_code == 404
    assert sync_client.get("/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/").status_code == 404


# ══════════════════════════════════════════════════════════════════════
# 2. SESSION ISOLATION: SEQUENTIAL & CONCURRENT
# ══════════════════════════════════════════════════════════════════════

def test_sequential_session_history_and_directory_isolation(sync_client: TestClient):
    """Multiple sequential sessions maintain strictly isolated in-memory histories and output folders."""
    sessions.clear()
    s_alpha = f"seq-alpha-{uuid.uuid4()}"
    s_beta = f"seq-beta-{uuid.uuid4()}"
    raw_finalize = finalize_research_spec.on_invoke_tool._get_wrapped_callable()

    async def mock_runner(agent, input, context):
        last_turn = input[-1]["content"]
        sid = context.session_id
        if "FINALIZE" in last_turn:
            class MockWrapper:
                def __init__(self, c):
                    self.context = c
            await raw_finalize(
                MockWrapper(context),
                original_problem_statement=f"Alpha Problem for {sid}",
                clarified_problem_statement=f"Alpha Clarified for {sid}",
                expected_input="Input",
                expected_output="Output",
                constraints="None",
                datasets_and_technologies="Tech",
                other_requirements="None",
                assumptions="None",
                research_focus=f"Focus_{sid}",
            )
            reply = f"Finalized {sid}"
        else:
            reply = f"Reply to {last_turn} for {sid}"

        mock_res = MagicMock()
        mock_res.final_output = reply
        new_in = list(input) + [{"role": "assistant", "content": reply}]
        mock_res.to_input_list.return_value = new_in
        return mock_res

    with patch("agents.Runner.run", side_effect=mock_runner):
        # Alpha turn 1
        sync_client.post("/chat", json={"session_id": s_alpha, "message": "Alpha topic: astronomy"})
        # Beta turn 1
        sync_client.post("/chat", json={"session_id": s_beta, "message": "Beta topic: robotics"})
        # Alpha turn 2
        sync_client.post("/chat", json={"session_id": s_alpha, "message": "FINALIZE Alpha"})
        # Beta turn 2
        sync_client.post("/chat", json={"session_id": s_beta, "message": "Beta turn 2: sensors"})

    # History isolation checks
    assert len(sessions[s_alpha]) == 4
    assert len(sessions[s_beta]) == 4
    assert all("robotics" not in m["content"] and "sensors" not in m["content"] for m in sessions[s_alpha])
    assert all("astronomy" not in m["content"] and "Alpha" not in m["content"] for m in sessions[s_beta])

    # Directory isolation checks
    alpha_dir = OUTPUTS_DIR / s_alpha
    beta_dir = OUTPUTS_DIR / s_beta
    try:
        assert alpha_dir.exists()
        assert (alpha_dir / "research_spec.json").exists()
        assert not beta_dir.exists()
    finally:
        shutil.rmtree(alpha_dir, ignore_errors=True)


def test_concurrent_session_stress_and_isolation(sync_client: TestClient):
    """Concurrent requests across 8 simultaneous worker threads maintain zero crosstalk and isolated artifacts."""
    sessions.clear()
    num_sessions = 8
    conc_sids = [f"conc-chal-{i}-{uuid.uuid4()}" for i in range(num_sessions)]
    raw_finalize = finalize_research_spec.on_invoke_tool._get_wrapped_callable()
    created_dirs: list[Path] = []

    async def mock_async_runner(agent, input, context):
        await asyncio.sleep(random.uniform(0.005, 0.02))  # simulate variable async latency
        last_turn = input[-1]["content"]
        sid = context.session_id
        if "FINALIZE" in last_turn:
            class MockWrapper:
                def __init__(self, c):
                    self.context = c
            await raw_finalize(
                MockWrapper(context),
                original_problem_statement=f"Prob {sid}",
                clarified_problem_statement=f"Clarified {sid}",
                expected_input="In",
                expected_output="Out",
                constraints="None",
                datasets_and_technologies="Tech",
                other_requirements="None",
                assumptions="None",
                research_focus=f"Focus_{sid}",
            )
            reply = f"Finalized {sid}"
        else:
            reply = f"Echo {last_turn} for {sid}"

        mock_res = MagicMock()
        mock_res.final_output = reply
        new_in = list(input) + [{"role": "assistant", "content": reply}]
        mock_res.to_input_list.return_value = new_in
        return mock_res

    def run_worker(sid: str):
        # Turn 1
        r1 = sync_client.post("/chat", json={"session_id": sid, "message": f"Prompt_{sid}"})
        assert r1.status_code == 200
        # Turn 2: Finalize
        r2 = sync_client.post("/chat", json={"session_id": sid, "message": f"FINALIZE {sid}"})
        assert r2.status_code == 200
        assert r2.json()["finalized"] is True
        return sid

    try:
        with patch("agents.Runner.run", side_effect=mock_async_runner):
            with ThreadPoolExecutor(max_workers=num_sessions) as executor:
                futures = [executor.submit(run_worker, sid) for sid in conc_sids]
                for f in as_completed(futures):
                    s = f.result()
                    created_dirs.append(OUTPUTS_DIR / s)

        # Verify zero cross-talk across all sessions
        for sid in conc_sids:
            history = sessions[sid]
            assert len(history) == 4
            for m in history:
                assert sid in m["content"]
                for other_sid in conc_sids:
                    if other_sid != sid:
                        assert other_sid not in m["content"]

            s_dir = OUTPUTS_DIR / sid
            assert s_dir.exists()
            spec = json.loads((s_dir / "research_spec.json").read_text(encoding="utf-8"))
            assert spec["research_focus"] == f"Focus_{sid}"

            # Verify HTTP static serving for this concurrent session
            r_get = sync_client.get(f"/outputs/{sid}/research_spec.json")
            assert r_get.status_code == 200
            assert r_get.headers.get("content-type") == "application/json"
    finally:
        for d in created_dirs:
            shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
# 3. WORKING DIRECTORY INDEPENDENCE
# ══════════════════════════════════════════════════════════════════════

def test_working_directory_paths_are_absolute():
    """Verify BASE_DIR, STATIC_DIR, and OUTPUTS_DIR are resolved to absolute paths."""
    expected_base = Path(__file__).resolve().parent.parent
    assert BASE_DIR == expected_base
    assert STATIC_DIR == expected_base / "static"
    assert OUTPUTS_DIR == expected_base / "outputs"
    assert STATIC_DIR.is_absolute()
    assert OUTPUTS_DIR.is_absolute()
    assert (STATIC_DIR / "index.html").exists()
    assert (OUTPUTS_DIR / "28a8c6cf-20c9-45e8-8707-0d4162a66742").exists()

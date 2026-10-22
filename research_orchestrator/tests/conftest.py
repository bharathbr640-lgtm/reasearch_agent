"""Shared fixtures and utilities for Research Orchestrator E2E test suites."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import patch

import httpx
import pytest
from starlette.testclient import TestClient

from app.main import app, sessions
from app.tools import SessionContext


class MockRunResult:
    """Mock result imitating agents.Runner.run return object."""

    def __init__(self, final_output: str, history: list):
        self.final_output = final_output
        self._history = list(history)

    def to_input_list(self) -> list:
        return self._history + [{"role": "assistant", "content": self.final_output}]


@pytest.fixture(autouse=True)
def clean_sessions() -> Generator[None, None, None]:
    """Ensure in-memory sessions dictionary is cleared before and after each test."""
    sessions.clear()
    yield
    sessions.clear()


@pytest.fixture
def sync_client() -> Generator[TestClient, None, None]:
    """Provide a synchronous Starlette TestClient."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an asynchronous httpx client bound to the FastAPI ASGI app."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def prototype_html_path() -> Path:
    """Return path to authoritative Stitch prototype screen HTML."""
    return Path(__file__).resolve().parent.parent.parent / "stitch_screen" / "screen_1940b14692274c4197c2b8086465105d.html"


@pytest.fixture
def static_html_path() -> Path:
    """Return path to current static index.html served by FastAPI."""
    return Path(__file__).resolve().parent.parent / "static" / "index.html"


@pytest.fixture
def mock_orchestrator_dialogue():
    """Mock agents.Runner.run to enable deterministic, offline multi-turn conversation and finalization."""
    created_output_dirs: list[str] = []

    async def fake_run(agent, input, context: SessionContext):
        last_turn = input[-1]["content"] if input else ""
        session_id = context.session_id

        # If user requests finalization / confirmation
        if "finalize" in last_turn.lower() or "confirm" in last_turn.lower() or "proceed" in last_turn.lower():
            context.finalized = True
            output_dir = f"outputs/{session_id}"
            context.output_dir = output_dir
            
            # Create output directory and mock artifacts on disk
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            created_output_dirs.append(output_dir)

            spec_content = {
                "original_problem_statement": "Automated hate speech detection",
                "clarified_problem_statement": "Real-time toxic comment detector with explainability",
                "expected_input": "Social media comment text",
                "expected_output": "JSON with toxicity score and rationale",
                "constraints": "Latency < 50ms, Single GPU",
                "datasets_and_technologies": "Jigsaw Toxic Comment, BERT",
                "other_requirements": "English only initially",
                "assumptions": "Standard text format",
                "research_focus": "Model throughput and explainability"
            }
            with open(out_path / "research_spec.json", "w", encoding="utf-8") as f:
                json.dump(spec_content, f, indent=2)

            with open(out_path / "clarified_problem_statement.md", "w", encoding="utf-8") as f:
                f.write("# Clarified Problem Statement\n\nReal-time toxic comment detector with explainability.")

            reply = f"Specification confirmed and finalized for session {session_id}."
        else:
            context.finalized = False
            reply = f"Thank you for the prompt. What are your specific constraints and dataset requirements for {session_id}?"

        return MockRunResult(final_output=reply, history=input)

    with patch("agents.Runner.run", side_effect=fake_run):
        yield

    # Cleanup any mock output directories created during test
    for d in created_output_dirs:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

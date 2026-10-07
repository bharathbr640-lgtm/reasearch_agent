"""Orchestrator agent definition."""

from __future__ import annotations

from pathlib import Path

from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, set_tracing_disabled

from app.config import OLLAMA_BASE_URL, OLLAMA_API_KEY, MODEL_NAME
from app.tools import finalize_research_spec, SessionContext

# Disable tracing so no OpenAI API key is required for telemetry.
set_tracing_disabled(True)

# OpenAI-compatible client pointed at Ollama.
_client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)

_model = OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=_client)

# Load the system prompt from the Markdown file.
_prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "orchestrator.md"
_instructions = _prompt_path.read_text(encoding="utf-8")

orchestrator_agent: Agent[SessionContext] = Agent(
    name="Orchestrator",
    instructions=_instructions,
    model=_model,
    tools=[finalize_research_spec],
)

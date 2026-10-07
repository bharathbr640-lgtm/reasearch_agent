"""Agent definition for the Existing Project Research Agent."""

from __future__ import annotations

from pathlib import Path

from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, set_tracing_disabled

from app.config import OLLAMA_BASE_URL, OLLAMA_API_KEY, MODEL_NAME
from project_research.tools import (
    ProjectResearchContext,
    github_search_repositories,
    github_get_repository,
    github_get_readme,
    hf_search,
    hf_get_details,
    save_findings,
)

set_tracing_disabled(True)

_client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)
_model = OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=_client)

_prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "project_research.md"
_instructions = _prompt_path.read_text(encoding="utf-8")

project_researcher_agent: Agent[ProjectResearchContext] = Agent(
    name="ProjectResearcher",
    instructions=_instructions,
    model=_model,
    tools=[
        github_search_repositories,
        github_get_repository,
        github_get_readme,
        hf_search,
        hf_get_details,
        save_findings,
    ],
)

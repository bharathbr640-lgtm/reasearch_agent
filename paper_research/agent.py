"""Agent definition for the Research Paper Discovery and Evidence Collection Agent (Agent 2)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, set_tracing_disabled
from agents.lifecycle import AgentHooksBase

from app.config import OLLAMA_BASE_URL, OLLAMA_API_KEY, MODEL_NAME
from paper_research.tools import (
    PaperResearchContext,
    search_research_papers,
    _search_research_papers,
    select_papers,
    _select_papers,
)

set_tracing_disabled(True)

_client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)
_model = OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=_client)

_prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "paper_research.md"
_instructions = _prompt_path.read_text(encoding="utf-8")


class PaperResearchHooks(AgentHooksBase[PaperResearchContext]):
    async def on_llm_start(
        self,
        context: Any,
        agent: Any,
        system_prompt: Any,
        input_items: Any,
    ) -> None:
        if hasattr(context, "context") and hasattr(context.context, "turns_count"):
            context.context.turns_count += 1


paper_researcher_agent: Agent[PaperResearchContext] = Agent(
    name="PaperResearcher",
    instructions=_instructions,
    model=_model,
    hooks=PaperResearchHooks(),
    tools=[
        search_research_papers,
        _search_research_papers,
        select_papers,
        _select_papers,
    ],
)


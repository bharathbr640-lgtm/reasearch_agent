# AI Research Agent

A multi-agent autonomous system that clarifies rough technical problem statements into structured research specifications, discovers prior art across GitHub and Hugging Face, evaluates scientific literature, and synthesizes findings into verified research reports. Built with the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) and [FastAPI](https://fastapi.tiangolo.com/).

## Setup

1. **Clone and enter the project:**
   ```bash
   cd reasearch_agent
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your values:
   | Variable | Description | Default |
   |---|---|---|
   | `OLLAMA_BASE_URL` | Ollama's OpenAI-compatible endpoint | `https://ollama.com/v1` |
   | `OLLAMA_API_KEY` | Your Ollama API key | _(required)_ |
   | `MODEL_NAME` | Model to use for the orchestrator | `gpt-oss:120b-cloud` |

   For a local Ollama instance, set `OLLAMA_BASE_URL=http://localhost:11434/v1` and `OLLAMA_API_KEY=ollama`.

## Running

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Usage

1. Type a rough problem statement or project idea.
2. The Orchestrator asks clarifying questions (up to ~8 rounds).
3. It presents a read-back summary for you to confirm or correct.
4. On confirmation, two files are saved:

## Output Format

Files are written to `outputs/{session_id}/`:

### `clarified_problem_statement.md`

A Markdown file with the final clarified problem statement.

### `research_spec.json`

A JSON file with the full research specification:

```json
{
  "original_problem_statement": "...",
  "clarified_problem_statement": "...",
  "expected_input": "...",
  "expected_output": "...",
  "constraints": "...",
  "datasets_and_technologies": "...",
  "other_requirements": "...",
  "assumptions": "...",
  "research_focus": "..."
}
```

This schema is designed to be consumed directly by downstream research agents (e.g., Existing Project Research Agent, Research Paper Agent) without any further clarification.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, /chat endpoint, session management
│   ├── agent.py          # Agent definition, model wiring
│   ├── config.py         # Environment variable loading
│   └── tools.py          # finalize_research_spec tool + Pydantic model
├── prompts/
│   ├── orchestrator.md   # System prompt (loaded at startup)
│   ├── paper_extractor.md
│   ├── paper_research.md
│   └── project_research.md # System prompt for Existing Project Research Agent
├── project_research/
│   ├── __init__.py
│   ├── agent.py          # ProjectResearcher agent definition
│   ├── run.py            # CLI entry point (--session <session_id>)
│   ├── schema.py         # Pydantic schemas for findings and repository details
│   └── tools.py          # GitHub & Hugging Face search/inspection tools
├── paper_research/
│   ├── __init__.py
│   ├── agent.py          # PaperResearcher agent definition
│   ├── run.py            # CLI entry point (--session <session_id>)
│   ├── schema.py         # Pydantic schemas for findings
│   └── tools.py          # Paper extraction and search tools
├── evaluator/
│   ├── __init__.py
│   ├── run.py            # 9-criteria evaluation runner
│   ├── engine.py
│   ├── criteria.py
│   ├── boundary.py
│   └── schema.py
├── static/
│   └── index.html        # Unified workspace SPA
├── tests/                # Automated pytest test suite
├── outputs/              # Generated specs and findings (gitignored)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Existing Project Research Agent

The Existing Project Research Agent (`project_research`) discovers existing implementations, models, datasets, and Spaces on GitHub and Hugging Face for a confirmed session.

### Running the Research Agent

Make sure the session is already clarified and has an existing `outputs/{session_id}/research_spec.json`.

```bash
python -m project_research.run --session <session_id>
```

Optional arguments:
- `--max-turns`: Maximum turns for the agent loop (default: `MAX_TURNS` in `.env` or `60`).
- `--max-tool-calls`: Tool-call budget across all tools (default: `MAX_TOOL_CALLS` in `.env` or `30`).

### Output Files

The research run generates files in `outputs/{session_id}/`:
- `project_findings.json`: JSON output containing up to 10 structured findings, platform/kind, repository details, known limitations, and field-level source tags.
- `project_findings.md`: Markdown report summarizing the findings and field sources.
- `project_research_trace.json`: Full audit trace recording every tool call, argument, and execution status (written in real time on every tool call).
- `project_findings_partial.json`: Generated if the run fails or terminates prematurely, preserving queries executed and candidate URLs inspected.

## Research Paper Research Agent (Agent 2)

The Research Paper Research Agent (`paper_research`) discovers scientific literature, extracts evidence from open-access full texts and PDFs, checks for associated code implementations, and clearly distinguishes exact research from closely related research.

### Running Agent 2

Make sure the session is already clarified and has an existing `outputs/{session_id}/research_spec.json`.

```bash
python -m paper_research.run --session <session_id>
```

Optional arguments:
- `--max-turns`: Maximum turns for the agent loop (default: `MAX_TURNS` in `.env` or `60`).
- `--max-tool-calls`: Tool-call budget across all tools (default: `MAX_TOOL_CALLS` in `.env` or `30`).

### Output Files

The paper research run generates files in `outputs/{session_id}/`:
- `paper_findings.json`: Structured JSON containing up to 10 paper candidates, match classification (`exact` vs `closely_related`), datasets, models, architectures, experimental metrics, verified evidence quotes, limitations, research gaps, and code repositories.
- `paper_findings.md`: Human-readable Markdown research report.
- `paper_research_trace.json`: Comprehensive audit trace recording all queries, API calls, and sources accessed.
- `paper_findings_partial.json`: Saved if the run terminates prematurely, preserving discovered candidate URLs and queries.

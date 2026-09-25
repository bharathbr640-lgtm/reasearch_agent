# Project Progress: AI Research Agent
*Developed by Mac OS*

## 🎯 Overview
The AI Research Agent is a specialized tool designed to validate project ideas. Unlike standard LLMs that answer immediately, this agent follows a rigorous professional research workflow: **Context Gathering $\rightarrow$ Problem Synthesis $\rightarrow$ Web Discovery $\rightarrow$ Content Extraction $\rightarrow$ Gap Analysis.**

## ✅ Completed Milestones

### 1. Core Architecture
- [x] Implemented a phased research pipeline: **Exa $\rightarrow$ Firecrawl $\rightarrow$ Ollama**.
- [x] Separated concerns into dedicated modules (`llm.py`, `researcher.py`, `agent_manager.py`).
- [x] Integrated **Ollama Cloud API** using the `gpt-oss:120b` model via the OpenAI SDK.

### 2. Tool Integration (SDK Transition)
- [x] Migrated from raw `requests` calls to official SDKs for increased stability.
- [x] **Exa AI**: Integrated neural search for high-precision URL discovery.
- [x] **Firecrawl**: Integrated v2 scraping to extract clean Markdown from the web.

### 3. Interface Development
- [x] **Guided Web UI**: Built a Streamlit application (`app.py`) that interviews the user to refine their project idea before researching.
- [x] **Standalone CLI**: Created `standalone_agent.py` for direct research queries and system diagnostics.

### 5. Subagent 1: Prior-Art Discovery Agent
- [x] Built `prior_art_agent.py` based on `skill.md` specification.
- [x] Implemented Plan-Mode interactive clarification loop (asking 1 focused question at a time across 6 dimensions).
- [x] Added plain-language problem statement synthesis and explicit confirmation gate.
- [x] Configured 4-MCP stack: Exa MCP, Firecrawl MCP, Hugging Face MCP (`mcp-remote https://huggingface.co/mcp`), Playwright MCP (`@playwright/mcp`).
- [x] Added visible headed Playwright verification of candidate web pages.
- [x] Implemented strict JSON export (`prior_art_findings.json`) for Subagent 2 handoff and Markdown report (`prior_art_report.md`).
### 6. Subagent 2: Academic Paper Finder Agent
- [x] Built `paper_finder_agent.py` based on `skill1.md` specification.
- [x] Implemented input contract consumption: ingests `prior_art_findings.json` (no clarification interview).
- [x] Implemented gap-seeded query generation combining domain keywords, identified gaps, and prior-art methods.
- [x] Integrated Firecrawl research tools: `firecrawl_research_search_papers`, `firecrawl_research_inspect_paper`, `firecrawl_research_related_papers`, and `firecrawl_research_read_paper`.
- [x] Integrated Exa academic preprint search (`search_academic_preprints`) as fallback.
- [x] Implemented gap-directness paper evaluation and narrowing to top 5 ranked papers.
- [x] Dual output generation: strict JSON contract (`paper_findings.json`) and curated reading list (`paper_reading_list.md`).
### 7. Interactive Multi-Mode Web UI (`app.py`)
- [x] Built interactive Streamlit dashboard supporting all three requested modes.
- [x] **Mode 1 (Subagent 1 Standalone)**: Plan-mode turn-by-turn chat, confirmation card, live search, prior-art report, and JSON contract inspector.
- [x] **Mode 2 (Subagent 2 Standalone)**: Input source flexibility (load existing, upload JSON, manual input), 2-pass paper discovery, and top 5 ranked paper cards with direct links.
- [x] **Mode 3 (Both Sub-Agents at Once)**: Unified end-to-end chained pipeline, executive research dossier, and complete artifact downloads.
- [x] Added configurable settings for Playwright browser mode (visible headed vs headless).

## 🛠️ Technical Stack
| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **LLM** | Ollama Cloud (`gpt-oss:120b`) | Reasoning, Plan-Mode Interview, Prior-Art & Paper Synthesis |
| **Semantic Discovery** | Exa MCP | Neural Web & Academic Preprint Discovery |
| **Broad & Dev Search** | Firecrawl MCP | Web Crawl & Developer Search (Subagent 1) |
| **Academic Research** | Firecrawl MCP Paper Tools | Paper Search, Abstract Inspection, Citation Graph (Subagent 2) |
| **Model & Space Hub** | Hugging Face MCP / HfApi | Structured Model, Space & Dataset Metadata (Subagent 1) |
| **Candidate Verifier**| Playwright MCP (headed) | Live Visible Browser Page Verification (Subagent 1) |
| **Orchestration** | Python 3.14 | 2-Stage Literature Discovery Pipeline |

## 📂 Project Structure
- `main.py`: Primary CLI orchestrator for the 2-Stage Literature Discovery Pipeline.
- `researcher.py`: Shared MCP tool integrations (Exa, Firecrawl Web & Papers, Hugging Face, Playwright).
- `utils.py`: Environment variable management (`.env`).
- `prior_art_agent.py`: Backward-compatible redirect to `subagent_1.agent`.
- `paper_finder_agent.py`: Backward-compatible redirect to `subagent_2.agent`.
- `subagent_1/`: Dedicated directory for Subagent 1 (Prior-Art Discovery):
  - `agent.py`: PriorArtDiscoveryAgent engine.
  - `run.py`: Standalone runner script (`python3 subagent_1/run.py`).
  - `SKILL.md`: Subagent 1 skill specification.
  - `prior_art_findings.json`: Contract output for Subagent 2.
  - `prior_art_report.md`: Human-readable research report.
- `subagent_2/`: Dedicated directory for Subagent 2 (Academic Paper Finder):
  - `agent.py`: PaperFinderAgent engine.
  - `run.py`: Standalone runner script (`python3 subagent_2/run.py`).
  - `SKILL.md`: Subagent 2 skill specification.
  - `paper_findings.json`: Contract output with top 5 ranked papers.
  - `paper_reading_list.md`: Curated academic reading list.
- `legacy/`: Archive of initial prototype scripts (`app.py`, `script.py`, `agent_manager.py`, etc.).

## 🚀 How to Run

### Running the 2-Stage Pipeline Interactively
```bash
python3 main.py
```

### Running Subagent 1 Only (Prior-Art Discovery)
```bash
python3 main.py --stage 1
```

### Running Subagent 2 Only (Academic Literature Discovery)
```bash
python3 main.py --stage 2
```

### Running Both Stages Automatically
```bash
python3 main.py --stage all
```

### Running the Interactive MCP Chatbot
```bash
python3 script.py
```

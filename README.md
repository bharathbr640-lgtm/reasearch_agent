# 🔬 AI Research Literature Discovery Pipeline

An autonomous two-stage AI research pipeline that validates technical project ideas by searching existing open-source implementations (**Subagent 1**) and identifying peer-reviewed academic literature (**Subagent 2**) to address innovation gaps.

---

## 🌟 Key Capabilities

1. **Subagent 1 (Prior-Art Discovery)**:
   - Interactive Plan-Mode clarification interview (1 focused question at a time across 6 core dimensions).
   - Multi-MCP discovery: Semantic search (**Exa**), broad web & GitHub search (**Firecrawl**), model/Space metadata (**Hugging Face**).
   - Live page verification in a visible browser (**Playwright**).
   - Emits structured JSON findings (`prior_art_findings.json`) and formatted markdown report (`prior_art_report.md`).

2. **Subagent 2 (Academic Paper Finder)**:
   - Ingests Subagent 1's findings without re-interviewing the user.
   - Generates queries targeted at identified innovation gaps.
   - Searches academic literature via **Firecrawl Paper Tools** (PubMed, arXiv, IEEE).
   - Explores citation graphs and inspects abstracts.
   - Emits top 5 ranked papers with concrete gap explanations (`paper_findings.json` & `paper_reading_list.md`).

3. **Multi-Mode Web UI**:
   - Run **Subagent 1 standalone**.
   - Run **Subagent 2 standalone**.
   - Run **Both sub-agents at once** in a continuous pipeline.

---

## 🚀 Quickstart: Web UI

Launch the interactive Streamlit dashboard:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`. Use the sidebar to switch between:
- 🚀 **Full Pipeline (Both Agents)**
- 🎯 **Subagent 1 (Prior-Art Standalone)**
- 📚 **Subagent 2 (Paper Finder Standalone)**

---

## 💻 CLI Usage

You can also run everything directly from your terminal:

### 1. Interactive 2-Stage Pipeline
```bash
python3 main.py
```

### 2. Run Subagent 1 Standalone
```bash
python3 main.py --stage 1
# Or directly:
python3 subagent_1/run.py
```

### 3. Run Subagent 2 Standalone
```bash
python3 main.py --stage 2
# Or directly:
python3 subagent_2/run.py
```

### 4. Run Both Stages Automatically
```bash
python3 main.py --stage all
```

---

## 📂 Project Structure

```
reasearch_agent/
├── app.py                            # Streamlit Web UI (All 3 Modes)
├── main.py                           # 2-Stage Pipeline CLI orchestrator
├── researcher.py                     # Shared MCP tool integrations (Exa, Firecrawl, HF, Playwright)
├── utils.py                          # Environment & config loader
│
├── subagent_1/                       # 📁 Subagent 1: Prior-Art Discovery
│   ├── agent.py                      # PriorArtDiscoveryAgent engine
│   ├── run.py                        # Standalone runner
│   ├── SKILL.md                      # Subagent 1 skill specification
│   ├── prior_art_findings.json       # Contract output
│   └── prior_art_report.md           # Formatted report
│
├── subagent_2/                       # 📁 Subagent 2: Academic Paper Finder
│   ├── agent.py                      # PaperFinderAgent engine
│   ├── run.py                        # Standalone runner
│   ├── SKILL.md                      # Subagent 2 skill specification
│   ├── paper_findings.json           # Top 5 ranked papers contract
│   └── paper_reading_list.md         # Curated reading list
│
└── legacy/                           # 📁 Archived initial prototypes
```

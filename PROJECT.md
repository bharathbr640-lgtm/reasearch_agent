# Project: AI Research Agent - Unified Workspace Replication

## Architecture
- **Presentation Layer**: Single-page application in `research_orchestrator/static/index.html` utilizing Tailwind CSS (via CDN with forms and container-queries plugins), Google Fonts (`Inter`, `Plus Jakarta Sans`, `JetBrains Mono`), and Material Symbols Outlined.
- **Client Controller & State Management**: Zero-reload client-side hash router (`#/dashboard`, `#/start`, `#/active`, `#/report`) managing 4 view containers (`#view-dashboard`, `#view-start`, `#view-active`, `#view-report`), localStorage-backed session registry, turn history, and real-time pipeline telemetry.
- **Backend Service**: Lightweight FastAPI service (`research_orchestrator/app/main.py`) serving static UI on `GET /` and `/static`, managing conversational agent execution via `POST /chat`, and persisting confirmed specs to `outputs/{session_id}/`.
- **Zero Heavy Dependencies Constraint**: Strict preservation of `research_orchestrator/requirements.txt` with no new backend frameworks, databases, or build toolchains added.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Backend Static Asset Mounting | Serve `static/index.html` on `GET /` and mount `/static` directory cleanly | M1 | explorer_survey_2 |
| 2 | Backend Spec Artifact Mounting | Mount `outputs/` static directory via existing FastAPI StaticFiles for direct client retrieval | M1 | explorer_survey_2 |
| 3 | Dependency Footprint Enforcement | Maintain exact `requirements.txt` without adding heavy dependencies | M1 | explorer_survey_2 |
| 4 | Persistent Left Dark Sidebar | Fixed sidebar (`w-64`, `#0f111a`) with branding, "New Research" CTA, navigation routes, agent telemetry, user profile | M2 | spec_miner_survey_1 |
| 5 | Floating Toast Notification System | Top-right transient toast banner (`#toast-notification`) for visual feedback | M2 | spec_miner_survey_1 |
| 6 | SPA Hash-based View Router | Zero-reload client router toggling 4 views with browser history/bookmark support (`#/dashboard`, `#/start`, `#/active`, `#/report`) | M2 | explorer_survey_3 |
| 7 | Dashboard Header & Status | "Workspace Active" pulsing pill, user greeting, search filter input, notification bell | M2 | spec_miner_survey_1 |
| 8 | Dashboard Hero Overview Card | Gradient banner highlighting AI-Powered Research with direct CTA to Report | M2 | spec_miner_survey_1 |
| 9 | Dashboard Quick Problem Input | Textarea with live character counter (`#dash-char-count`) and suggested domain chips | M2 | spec_miner_survey_1 |
| 10 | Dashboard 4-Stage Workflow Grid | Interactive 4-card overview of pipeline with step numbers and status badges | M2 | spec_miner_survey_1 |
| 11 | Dashboard Recent Research Rail | Sidebar list of recent research runs with colored status dots and links | M2 | spec_miner_survey_1 |
| 12 | Dashboard Metrics Snapshot | 2x2 grid displaying counts for Projects, Papers, Gaps, and Reports | M2 | spec_miner_survey_1 |
| 13 | Dashboard Quality Gauge | Circular radial SVG gauge and progress bar displaying 83% evidence coverage | M2 | spec_miner_survey_1 |
| 14 | Start View Header & Breadcrumbs | Breadcrumb navigation (`Dashboard / New Research Intake`) and Cancel button | M2 | spec_miner_survey_1 |
| 15 | Start View Intake Form | Textarea with live character counter (`#start-char-count`) and 4 context tag chips | M2 | spec_miner_survey_1 |
| 16 | Start View Benchmark Preset Cards | 4 recommended benchmark cards (Crop Yield, Clinical LLM, Edge Drone, Tick Anomaly) with 1-click autofill | M2 | spec_miner_survey_1 |
| 17 | Start View Autonomous Pipeline Guide | Explanatory side card detailing sequential multi-agent roles and execution timing | M2 | spec_miner_survey_1 |
| 18 | Active View Header & Session Badge | Header displaying session identifier (`#AG-9042`), active pulsing indicator, and subtitle | M2 | spec_miner_survey_1 |
| 19 | Active View Pipeline Progress Bar | Visual progress meter with percentage display and current stage label | M2 | spec_miner_survey_1 |
| 20 | Active View 4 Agent State Cards | Cards showing status for Orchestrator, Project Finder, Paper Finder, Evaluator | M2 | spec_miner_survey_1 |
| 21 | Active View Telemetry Log Console | Dark monospace terminal window streaming timestamped agent execution events | M2 | spec_miner_survey_1 |
| 22 | Report View Header & Confidence | Report identifier (`#REP-...`), `VERIFIED REPORT` badge, confidence score (8.7 / 10), return button | M2 | spec_miner_survey_1 |
| 23 | Report View 4-Metric Summary Ribbon | 4 metrics cards (Projects Analyzed, Papers Synthesized, Findings, Gaps Found) | M2 | spec_miner_survey_1 |
| 24 | Report View Sticky Table of Contents | Sticky sidebar navigation indexing 6 report sections with smooth scrolling | M2 | spec_miner_survey_1 |
| 25 | Report View Executive Summary Section | Section 01 with key metrics and highlighted core agent finding callout box | M2 | spec_miner_survey_1 |
| 26 | Report View Comparative Evaluation Matrix | Section 04 data table comparing architectures, modalities, R², code quality, and status | M2 | spec_miner_survey_1 |
| 27 | Report View Recommended Next Step Card | Section 06 dark gradient card with action buttons | M2 | spec_miner_survey_1 |
| 28 | Report View Sticky Floating Action Bar | Fixed bottom toolbar with generation timing, Share Report, and Export Full Spec buttons | M2 | spec_miner_survey_1 |
| 29 | Client Session ID Management | Generate UUID (`crypto.randomUUID()`) per session, persist active ID, and sync across views | M3 | explorer_survey_3 |
| 30 | Research Problem Dispatch to `/chat` | Form submission from Dashboard or Start view initiates session and dispatches `POST /chat` | M3 | spec_miner_survey_1 / explorer_survey_2 |
| 31 | Active View Interactive Dialogue Stream | 2-column layout in Active view providing chat message history, user clarification replies, and send button | M3 | explorer_survey_3 |
| 32 | In-Flight Loading & Typing Feedback | Disable buttons during requests, display typing indicator dots, and pulse progress bar | M3 | explorer_survey_3 |
| 33 | Robust Network Error Handling | Catch fetch exceptions, display inline alert message, restore user input, and show error toast | M3 | explorer_survey_3 |
| 34 | Active Session Pause/Resume Control | Toggle execution pause state, flip button label, and update telemetry | M3 | spec_miner_survey_1 |
| 35 | Recent Research Local Persistence | Save completed sessions to localStorage and render them dynamically in Dashboard recent list | M3 | explorer_survey_3 |
| 36 | Finalized State Transition | Detect `finalized: true`, update Agent 1 badge to DONE, advance progress to 100%, and enable Report view | M4 | spec_miner_survey_1 / explorer_survey_3 |
| 37 | Dynamic Report View Data Hydration | Populate Executive Summary, specifications, and metrics from finalized Orchestrator output | M4 | explorer_survey_3 |
| 38 | Report Spec Export Actions | Client-side export of research spec JSON and shareable link copying | M4 | explorer_survey_3 |
| 39 | E2E Testing Suite (Tiers 1-4) Pass | Full verification pass against all opaque-box and contract test cases | M4 | Project Pattern Dual Track |
| 40 | Adversarial Hardening (Tier 5) Pass | Adversarial coverage verification and edge case validation | M4 | Project Pattern Final Milestone |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Backend Foundation & Static Output Mounting | Verify `app/main.py` routes, mount `outputs/` via `StaticFiles`, verify zero dependency additions in `requirements.txt` | none | DONE |
| M2 | SPA Shell & High-Fidelity 4-View Layout | Implement unified workspace layout in `research_orchestrator/static/index.html` with Tailwind, fonts, icons, hash routing, and all 4 views | M1 | IN_PROGRESS |
| M3 | Interactive Client State, Dialogue & Backend Flow | Implement client store, wire `POST /chat`, interactive 2-column active session with dialogue and telemetry, error handling | M2 | PLANNED |
| M4 | Report Hydration, Export Actions & Final E2E Suite Pass | Wire `finalized: true` report hydration, spec export, pass 100% E2E test suite (Tiers 1-4), and Tier 5 adversarial hardening | M3 | PLANNED |

---

## Interface Contracts

### Client ↔ Backend (`POST /chat`)
- **URL**: `/chat`
- **Method**: `POST`
- **Request Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "session_id": "string (UUID)",
    "message": "string (user prompt or clarification response)"
  }
  ```
- **Response Headers**: `Content-Type: application/json`
- **Response Body**:
  ```json
  {
    "reply": "string (Orchestrator answer or clarified spec summary)",
    "finalized": "boolean (true if research spec is finalized, false if clarification needed)",
    "output_dir": "string | null (e.g. 'outputs/<session_id>' if finalized, otherwise null)"
  }
  ```
- **Error Responses**:
  - `422 Unprocessable Entity`: Schema mismatch (missing `session_id` or `message`).
  - `500 Internal Server Error`: Backend runtime or agent execution failure.

### Client ↔ Backend (`GET /` and `/static/*`)
- `GET /` -> Returns `static/index.html` with MIME type `text/html; charset=utf-8`.
- `GET /static/{filepath}` -> Serves static assets from `research_orchestrator/static/`.
- `GET /outputs/{session_id}/{filename}` -> Serves `research_spec.json` and `clarified_problem_statement.md`.

### Client Internal State Model
```typescript
interface AppState {
  activeView: 'dashboard' | 'start' | 'active' | 'report';
  sessionId: string | null;
  problemStatement: string;
  messages: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
  }>;
  pipeline: {
    progress: number; // 0 - 100
    currentStage: number; // 1 to 4
    stageLabel: string;
    isPaused: boolean;
    isFinalized: boolean;
    outputDir: string | null;
  };
  finalizedSpec: Record<string, any> | null;
  recentSessions: Array<{
    sessionId: string;
    title: string;
    timestamp: string;
    finalized: boolean;
  }>;
}
```

---

## Code Layout
- `research_orchestrator/app/main.py`: FastAPI server entrypoint and route declarations.
- `research_orchestrator/app/agent.py`: Orchestrator agent definitions and prompt configuration.
- `research_orchestrator/app/tools.py`: Research spec finalization tools and file generation.
- `research_orchestrator/app/config.py`: Configuration settings and environment variables.
- `research_orchestrator/static/index.html`: Unified workspace SPA containing HTML markup, Tailwind configuration, SVG icons, and client JavaScript.
- `research_orchestrator/outputs/`: Output directory where finalized research specs are saved per session.
- `research_orchestrator/tests/` (or `test_e2e.py`): E2E and API contract test suite.

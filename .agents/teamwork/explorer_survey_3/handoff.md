# Handoff Report: Frontend Integration & Architecture Survey

## 1. Observation

### 1.1 Existing Static Files Setup
- **File**: `/Users/bharathbr/reasearch_agent/research_orchestrator/static/index.html` (295 lines, 6,878 bytes).
  - Contains minimal plain CSS styling (lines 8–24 `:root` and `@media (prefers-color-scheme: dark)`).
  - DOM structure: Single `.container` (max-width: 720px) containing `<header>`, `<div id="chat">`, `<div id="notice">`, and `.input-area` with `#input` (textarea) and `#send` (button) (lines 201–219).
  - Client logic (lines 221–292):
    - Session ID created once on page load via `const sessionId = crypto.randomUUID();` (line 222).
    - Sends user input via `POST /chat` with payload `{"session_id": sessionId, "message": text}` (lines 251–255).
    - Upon response where `data.finalized === true`, displays static text banner in `#notice` pointing to output files:
      `data.output_dir + "/clarified_problem_statement.md"` and `data.output_dir + "/research_spec.json"` (lines 260–264).
    - No modular CSS or JS files exist in `research_orchestrator/static/` (confirmed by `list_dir`).

### 1.2 FastAPI Backend Static Mounting & Routes
- **File**: `/Users/bharathbr/reasearch_agent/research_orchestrator/app/main.py` (74 lines).
  - Route: `@app.get("/")` returns `FileResponse("static/index.html")` (lines 71–73).
  - Static Mount: `app.mount("/static", StaticFiles(directory="static"), name="static")` (line 68).
  - Chat Endpoint: `@app.post("/chat", response_model=ChatResponse)` (lines 35–64).
  - Schemas:
    - Request: `ChatRequest(session_id: str, message: str)` (lines 22–24).
    - Response: `ChatResponse(reply: str, finalized: bool, output_dir: str | None = None)` (lines 27–30).
  - In-memory conversation state: `sessions: dict[str, list] = {}` (line 17). Appends user message, runs `Runner.run(orchestrator_agent, input=history, context=ctx)`, and persists `result.to_input_list()` (lines 38–59).
  - Finalization triggers: `finalize_research_spec` tool (`app/tools.py`: lines 40–90) saves `outputs/{session_id}/clarified_problem_statement.md` and `outputs/{session_id}/research_spec.json`, setting `ctx.context.finalized = True` and `ctx.context.output_dir = "outputs/{session_id}"`.
  - Dependencies in `requirements.txt`: `openai-agents>=0.0.7`, `openai>=1.60.0`, `fastapi>=0.115.0`, `uvicorn>=0.34.0`, `python-dotenv>=1.0.0`, `pydantic>=2.0.0`, `httpx>=0.27.0`, `pypdf>=4.0.0`.

### 1.3 Target Stitch Prototype Screen
- **File**: `/Users/bharathbr/reasearch_agent/stitch_screen/screen_1940b14692274c4197c2b8086465105d.html` (1,133 lines, 69,172 bytes).
- Head Resources:
  - Fonts: Inter, Plus Jakarta Sans, JetBrains Mono (line 9).
  - Icons: Material Symbols Outlined (line 10).
  - Tailwind CSS: Loaded from CDN `https://cdn.tailwindcss.com?plugins=forms,container-queries` (line 11).
  - Tailwind configuration: Customized colors (`brand`, `primary`, `surface`) and font families (lines 12–40).
- Layout Shell:
  - Fixed dark sidebar (`aside`, w-64, bg `#0f111a`, lines 76–193).
  - Toast notification element (`#toast-notification`, lines 71–74).
  - SPA Views Container (`flex-1 flex overflow-hidden`, line 196) housing 4 view elements:
    1. **Dashboard View** (`#view-dashboard`, lines 200–531): Contains Hero card, Quick Problem input (`#dashboard-input`), domain suggestion chips, 4-stage pipeline preview cards, Recent Research sidebar list, and Research Snapshot metrics.
    2. **Start Session View** (`#view-start`, lines 535–674, marked `class="hidden ..."`): Intake form with textarea (`#start-problem-textarea`), context tag adder buttons, recommended benchmark cards (`selectTestCase(...)`), and pipeline phase info.
    3. **Active Research View** (`#view-active`, lines 678–811, marked `class="hidden ..."`): Session header with title & Session ID badge (`Session #AG-9042`), progress bar (`#active-progress-bar`), 4 agent state cards (01 Orchestrator, 02 Project Finder, 03 Paper Finder, 04 Evaluator), and dark console (`#telemetry-log`).
    4. **Report View** (`#view-report`, lines 815–979, marked `class="hidden ..."`): Report header, confidence score, 4-metric ribbon, sticky section navigation TOC, 01 Executive Summary (`#rep-sec-1`), 04 Comparative Evaluation Matrix (`#rep-sec-4`), 06 Recommended Next Step Card (`#rep-sec-6`), and sticky bottom action bar (`shareReport()`, `exportFullSpec()`).
- Prototype Script:
  - `switchView(viewName)` (lines 989–1023) toggles Tailwind `hidden` class across `view-dashboard`, `view-start`, `view-active`, and `view-report`, while updating sidebar `active-nav` class.
  - Telemetry simulated via `startLiveTelemetrySimulation()` using a timer updating `currentProgress` (lines 1088–1102).

---

## 2. Logic Chain

### 2.1 SPA View Navigation Architecture
- **Step 1 (Observation 1.3)**: The prototype implements view switching via class toggling in `switchView(viewName)`. However, the raw prototype implementation lacks URL synchronization, page reload persistence, and browser navigation (Back/Forward buttons).
- **Step 2 (Inference)**: Direct migration of `switchView` without hash routing would mean that hitting refresh or sharing a link always resets the user to Dashboard view (`switchView('dashboard')` called on `DOMContentLoaded` at line 1130).
- **Step 3 (Solution)**: An SPA hash-routing layer (`#/dashboard`, `#/start`, `#/active`, `#/report`) should be layered on top of `switchView`.
  - When switching views, set `window.location.hash = '#/' + viewName`.
  - Listen to `window.addEventListener('hashchange', () => handleHashChange())`.
  - On initial page load (`DOMContentLoaded`), check `window.location.hash`; if present, route to that view; otherwise default to `#/dashboard`.
  - This preserves instant zero-reload transitions while enabling bookmarking, back/forward navigation, and deep linking (e.g. `#/report?session=...`).

### 2.2 Client-Side State Management Design
- **Step 1 (Observation 1.1 & 1.2)**: Backend requires a `session_id: str` for each conversation in `POST /chat`. The current frontend generates a random UUID in memory and throws it away on refresh.
- **Step 2 (Inference)**: To support viewing previous sessions, switching between views, and preserving active research in progress, state must be centralized and persisted in the browser (`localStorage`).
- **Step 3 (Data Architecture)**:
  - Central State Store:
    ```javascript
    const store = {
      activeView: 'dashboard',
      sessionId: null,
      problemTitle: '',
      messages: [], // Array of { role: 'user'|'assistant', text: string, timestamp: string }
      pipelineState: {
        stage: 1, // 1: Orchestrator, 2: ProjectFinder, 3: PaperFinder, 4: Evaluator
        stageLabel: 'Orchestrator Clarification',
        progressPercent: 20,
        isFinalized: false,
        isPaused: false
      },
      spec: null, // Parsed ResearchSpec when finalized
      sessionsIndex: [] // List of { sessionId, title, timestamp, finalized, outputDir }
    };
    ```
  - **Session Lifecycle**:
    - "New Research" button (`#btn-sidebar-new`) or submitting from Dashboard / Start view generates a new `sessionId = crypto.randomUUID()`.
    - Active session ID stored in `localStorage.setItem('active_research_session_id', id)`.
    - Session index stored in `localStorage.getItem('research_sessions_list')` so that the Dashboard "Recent research" sidebar list can dynamically display previous sessions.
  - **Message History & Timeline**:
    - Messages cached under `localStorage.setItem('msgs_' + sessionId, JSON.stringify(store.messages))`.
    - Chat history rendered dynamically in the Active Research view.
  - **Phase Tracking**:
    - Stage 1: Problem Clarification (Active while `finalized: false`).
    - Stage 2: Codebase Discovery.
    - Stage 3: Literature Synthesis.
    - Stage 4: Audit & Synthesis.
    - Once `finalized: true` is received, Stage 1 marks "DONE" (green badge), progress advances to 100%, and Report view becomes fully unlocked.

### 2.3 The Critical Active View Integration Gap (Dialogue vs Telemetry)
- **Step 1 (Observation 1.3 & Grep)**: In `stitch_screen/screen_1940b14692274c4197c2b8086465105d.html`, lines 678–811 define `#view-active`. It contains a progress bar, 4 agent state cards, and `#telemetry-log` (a read-only terminal). **It has NO text input area or conversation message list!**
- **Step 2 (Observation 1.1 & 1.2, prompts/orchestrator.md)**: The orchestrator backend is conversational. It asks clarifying questions (up to 8 turns) and requires user read-back confirmation before calling `finalize_research_spec`.
- **Step 3 (Requirement R2 & Acceptance Criteria)**: "Submitting a prompt in the Start view dispatches a valid request to /chat. Orchestrator responses are received and displayed in the Active view timeline/chat."
- **Step 4 (Resolution)**: In `#view-active`, we must provide an interactive Orchestrator Dialogue interface.
  - Design: In the bottom section of `#view-active`, implement a 2-column responsive layout (`grid grid-cols-1 lg:grid-cols-2 gap-6`):
    - **Left Column**: "Orchestrator Clarification & Dialogue" card.
      - Styled matching the prototype (white rounded-2xl card, slate border, subtle shadow).
      - Scrollable message bubble history container (`#active-chat-history`) displaying user and orchestrator turns with distinct styling.
      - Animated typing/thinking indicator.
      - Auto-resizing input textarea (`#active-chat-input`) + "Send Reply" button.
      - When `finalized === true`, displays green completion badge and locks input.
    - **Right Column**: "Live Agent Telemetry & Evidence Stream" (`#telemetry-log`).
      - Preserves the dark monospace console from the Stitch prototype.
      - Real-time logging of user submissions, agent queries, tool execution, and state transitions.

### 2.4 Loading States, Waiting Feedback, and Error Handling
- **Step 1 (User Experience & LLM Latency)**: Calling LLMs via Ollama / `POST /chat` typically takes 5–25 seconds. If the UI freezes without visual feedback, users may click repeatedly or assume the app crashed.
- **Step 2 (Solution)**:
  - **In-flight State**:
    - Disable Send buttons (`#dash-start-btn`, `#start-submit-btn`, `#active-chat-send`) and set `busy = true`.
    - Show typing bubble (`typing-indicator`) with animated bouncing dots in the chat timeline.
    - Top toast notification: `showToast('Orchestrator analyzing input...')`.
    - Progress bar pulse effect.
  - **Network Error Handling**:
    - Wrap `fetch("/chat", ...)` in robust `try...catch`.
    - On failure (HTTP 500, network drop, timeout):
      - Display an inline warning card in the conversation stream: `"⚠️ Error communicating with Orchestrator: <error message>. Please try again."`
      - Re-enable the input box and keep the user's unsent message intact.
      - Append error event to `#telemetry-log` in red.
      - Display error toast alert: `showToast('Network error: request failed')`.

### 2.5 Report View Data Hydration
- **Step 1 (Observation 1.2)**: `POST /chat` returns `{"reply": "...", "finalized": true, "output_dir": "outputs/<session_id>"}`.
  - `outputs/<session_id>/research_spec.json` contains:
    - `original_problem_statement`
    - `clarified_problem_statement`
    - `expected_input`
    - `expected_output`
    - `constraints`
    - `datasets_and_technologies`
    - `other_requirements`
    - `assumptions`
    - `research_focus`
- **Step 2 (Backend Serving Strategy)**:
  - To allow the frontend to fetch `research_spec.json`, FastAPI can mount `outputs/` via `app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")` in `app/main.py`. This uses FastAPI's existing `StaticFiles` without adding ANY new dependencies.
  - Alternatively or concurrently, `ChatResponse` can optionally include the parsed spec object in its payload (`spec: dict | None = None`), or the client can parse the orchestrator's structured read-back markdown.
- **Step 3 (DOM Population)**:
  - Header: Update `#report-title` with problem title; update badge with `#REP-${sessionId.slice(0, 6).toUpperCase()}`.
  - Section 01 (`#rep-sec-1`): Render `spec.clarified_problem_statement`.
  - Section 02 (`#rep-sec-2`): Render structured cards for Expected Input, Expected Output, Constraints, Datasets & Technologies, and Assumptions.
  - Export Button (`exportFullSpec()`): Create a `Blob` containing `spec` formatted as JSON, trigger native browser file download `research_spec_${sessionId}.json`, and show success toast.
  - Share Button (`shareReport()`): Copy deep link `window.location.origin + "/#/report?session=" + sessionId` to clipboard.

---

## 3. Caveats
1. **Downstream Agents (Agents 2, 3, 4)**: The current FastAPI backend only executes the Orchestrator (`app/main.py`). The existing project research agent (`project_research/run.py`) and paper research agent (`paper_research/run.py`) are CLI scripts. Therefore, stages 2–4 in the Active Research view will display verified spec completion from the Orchestrator, with downstream steps shown as queued/ready.
2. **Network Mode**: In CODE_ONLY / local development mode, third-party CDNs (Tailwind CDN, Google Fonts) will be fetched by the user's browser client when accessing the web page. The FastAPI server itself does not download them.
3. **No Alternative Interpretations**: The requirement explicitly specifies replicating the Stitch layout directly into `research_orchestrator/static/index.html` without introducing heavy backend frameworks (e.g. no React/Next.js/Node build steps). Single-page vanilla JS with Tailwind CDN matches both the prototype and the project's dependency constraints.

---

## 4. Conclusion
1. **File Target**: The target implementation is a single unified HTML file in `/Users/bharathbr/reasearch_agent/research_orchestrator/static/index.html` that replaces the 295-line legacy chat UI with the 1,133-line Stitch workspace.
2. **Architecture**:
   - Shell: Fixed dark sidebar with persistent navigation, brand badge, and system status.
   - SPA Views: 4 views (`dashboard`, `start`, `active`, `report`) toggled seamlessly with URL hash routing (`#/dashboard`, `#/start`, `#/active`, `#/report`).
   - Dialogue Integration: A two-column layout in `#view-active` providing an interactive Orchestrator clarification conversation on the left, and the live telemetry stream on the right.
   - State & Persistence: LocalStorage-backed session management, message history, and recent research list.
   - Backend Connectivity: Communicates with `POST /chat` with `{"session_id": sessionId, "message": text}`.
   - Report Hydration: Renders confirmed research specifications into Report View with direct JSON/PDF spec export.
3. **Zero New Backend Dependencies**: All changes in backend (if mounting `/outputs`) use existing `fastapi.staticfiles.StaticFiles`. `requirements.txt` remains unchanged.

---

## 5. Verification Method

To independently verify the frontend integration architecture:

### 5.1 Static Serving & Contract Verification (Pytest / HTTPX)
Run the project's test suite and check static asset serving:
```bash
cd /Users/bharathbr/reasearch_agent/research_orchestrator
python -m pytest test_e2e.py -v
```
Or execute a direct curl verification script:
```bash
# 1. Verify GET / returns 200 with the SPA DOM structure
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/
# Expected: 200

# 2. Verify existence of the 4 SPA view IDs in response HTML
curl -s http://127.0.0.1:8000/ | grep -E "id=\"view-(dashboard|start|active|report)\""
# Expected: matches for all 4 views

# 3. Verify POST /chat contract
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-001", "message": "Test research idea"}'
# Expected: JSON response with {"reply": "...", "finalized": false, "output_dir": null}
```

### 5.2 Browser & Playwright Automated Verification
Using Playwright or headless browser:
1. Navigate to `http://localhost:8000/#/dashboard`:
   - Verify `#view-dashboard` is visible (no `hidden` class).
   - Verify `#view-start`, `#view-active`, `#view-report` have `hidden` class.
2. Click `#btn-sidebar-new`:
   - Verify URL hash updates to `#/start`.
   - Verify `#view-start` becomes visible.
3. Type `"Build an agricultural drone pest detection system"` into `#start-problem-textarea` and click "Start Research Pipeline":
   - Verify view transitions to `#/active`.
   - Verify chat dialogue container displays the submitted user message.
   - Verify typing indicator is displayed while request is pending.
   - Verify orchestrator response appears upon completion.
   - Verify `#telemetry-log` logs event `[Orchestrator] ...`.
4. Send clarifying reply:
   - Type `"Expected input is drone RGB video; output is bounding box coordinates and pest count."` into `#active-chat-input` and submit.
   - Verify response is appended.
5. Invalidation conditions:
   - Page reloads on view switch (indicates broken SPA routing).
   - Uncaught JavaScript errors in browser console (`console.error` > 0).
   - Inability to reply to the Orchestrator from the Active view.

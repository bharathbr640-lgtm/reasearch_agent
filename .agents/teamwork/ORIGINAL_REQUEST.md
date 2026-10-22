# Original User Request

## 2026-10-14T09:49:45Z

Replicate the Stitch interactive prototype UI ("AI Research Agent - Unified Workspace") directly into research_orchestrator/static/index.html, connecting its 4 SPA views (Dashboard, Start Session, Active Research, and Report) to the existing FastAPI orchestrator backend without adding heavy new backend dependencies.

Working directory: /Users/bharathbr/reasearch_agent/research_orchestrator
Integrity mode: development

## Reference Material
- Prototype Screen ID: 1940b14692274c4197c2b8086465105d
- Prototype HTML source: /Users/bharathbr/reasearch_agent/stitch_screen/screen_1940b14692274c4197c2b8086465105d.html
- Prototype Screenshot: /Users/bharathbr/reasearch_agent/stitch_screen/screen_1940b14692274c4197c2b8086465105d.png
- Backend entrypoint: /Users/bharathbr/reasearch_agent/research_orchestrator/app/main.py

## Requirements

### R1. Complete UI Replication
Replace research_orchestrator/static/index.html with the modern unified workspace layout based on stitch_screen/screen_1940b14692274c4197c2b8086465105d.html. Preserve the visual fidelity (Tailwind CSS, fonts, Material Symbols, color palette, dark/light styling, and responsive layout) across all 4 SPA views:
1. Dashboard View: Recent research list, metrics snapshot, and quick start cards.
2. Start View: Form to define research problem statement, parameters, and preset benchmarks.
3. Active Session View: Real-time status display, autonomous pipeline phase tracker, telemetry/logs, and control buttons.
4. Report View: Executive summary, comparative evaluation matrix, and findings breakdown.

### R2. FastAPI Backend Integration
Connect frontend interactions to the existing FastAPI backend (app/main.py):
- Submitting a new research problem initiates a session and interacts with POST /chat.
- Messages and agent status updates are dynamically rendered in the active session view.
- When finalized: true or report outputs are available, transition to or populate the Report view with the orchestrator results.
- Keep existing backend dependencies intact; do not introduce heavy new backend frameworks.

### R3. Interactive Client State & Error Handling
- Manage client session state (session ID generation, message history, active view navigation).
- Provide visual feedback for loading, waiting states, and network errors.

## Acceptance Criteria

### Visual & Interactive Fidelity
- [ ] GET / serves the new unified workspace cleanly.
- [ ] View switching (Dashboard, Start, Active, Report) works seamlessly without page reloads or broken layouts.
- [ ] UI elements (cards, badges, buttons, typography) match the prototype styling.

### Backend Connectivity & Functional Flow
- [ ] Submitting a prompt in the Start view dispatches a valid request to /chat.
- [ ] Orchestrator responses are received and displayed in the Active view timeline/chat.
- [ ] Completed sessions (finalized: true) correctly surface output in the Report view.
- [ ] Existing backend dependencies remain unchanged in requirements.txt.

### Objective Verification
- [ ] Verification script or test confirms GET / returns status 200 with the new SPA structure.
- [ ] Verification confirms POST /chat succeeds and responses are parseable by the UI logic.
- [ ] No uncaught JavaScript exceptions during page load or view switching.

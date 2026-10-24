# End-to-End Testing Infrastructure & Architecture Specification

## 1. Test Philosophy

The testing methodology for the AI Research Orchestrator and Unified Workspace SPA adheres to an **opaque-box, requirement-driven verification philosophy**, derived directly from the authoritative requirements specified in `ORIGINAL_REQUEST.md` and synthesized in `PROJECT.md`.

### Core Principles
1. **Opaque-Box Boundary Testing**: All test suites evaluate the system strictly through its observable external boundaries: HTTP wire protocol (`GET /`, `POST /chat`, static file asset serving), standard HTTP status codes, JSON payload schemas, DOM structure, and DOM event flow. Internal implementation details (in-memory dictionary internals, private agent methods) are never coupled directly to assertions.
2. **Authoritative Specification Derivation**: Every test case derives its inputs and expected outputs from `ORIGINAL_REQUEST.md` (R1 Complete UI Replication, R2 FastAPI Backend Integration, R3 Client State & Error Handling) and `PROJECT.md` (§ Feature Inventory & Interface Contracts).
3. **Deterministic & Isolated Execution**: Tests are fully self-contained. Each test creates unique UUID session identifiers, sets up required test environments or mock boundaries, executes independently of test execution order, and operates with zero cross-test interference.
4. **Dual Verification Pipeline**: Combines rapid ASGI in-process contract testing (`httpx` + `ASGITransport` / `starlette.testclient`) with DOM structure and headless browser validation (`BeautifulSoup4` and `playwright`).
5. **Progressive Testability**: Tests support progressive delivery across Milestones M1 through M4. Core backend routes and contract boundaries are validated immediately; structural SPA DOM tests check both the current working template and target prototype specifications cleanly.

---

## 2. Feature Inventory Mapping (4-Tier Taxonomy)

The testing track maps all 40 features defined in `PROJECT.md` into four distinct testing tiers:

```
┌─────────────────────────────────────────────────────────────┐
│ Tier 4: Real-World Lifecycles & Full Simulation             │
│ - Full session lifecycle (Start -> Clarify -> Finalize)     │
│ - Artifact generation & static outputs retrieval             │
│ - Interactive UI navigation & DOM structure verification    │
├─────────────────────────────────────────────────────────────┤
│ Tier 3: Combinations, Interactions & Session Isolation      │
│ - Multi-turn conversational flow across repeated turns      │
│ - Session isolation across concurrent/interleaved sessions  │
│ - Dialogue history accumulation and state retention         │
├─────────────────────────────────────────────────────────────┤
│ Tier 2: Boundary, Edge Cases & Error Cascading              │
│ - 422 Unprocessable Entity on missing/malformed fields       │
│ - Empty strings, extreme payload lengths, non-string types  │
│ - 404 Not Found on missing static assets & 405 Method check │
│ - Content-Type header validation and error response shape   │
├─────────────────────────────────────────────────────────────┤
│ Tier 1: Core Feature Coverage & Contract Baselines          │
│ - GET / serves 200 OK with text/html content                │
│ - Static directory mounts (/static/)                        │
│ - POST /chat valid payload contract schema validation        │
│ - 4 SPA View containers (#view-dashboard, #view-start, etc.)│
└─────────────────────────────────────────────────────────────┘
```

### Detailed Tier Breakdown

| Tier | Category | Target Behaviors / Contracts | Target Modules / Suites |
|---|---|---|---|
| **Tier 1** | **Core Feature Coverage** | • `GET /` returns 200 OK with `text/html; charset=utf-8`<br>• Static asset mounting at `/static` serves assets with 200 OK<br>• `POST /chat` responds with valid JSON schema (`reply`: str, `finalized`: bool, `output_dir`: str\|null)<br>• SPA root contains 4 essential view containers (`#view-dashboard`, `#view-start`, `#view-active`, `#view-report`)<br>• Persistent sidebar, toast container, and key input elements present | `test_api_contract.py`<br>`test_spa_structure.py` |
| **Tier 2** | **Boundary & Corner Cases** | • Missing `session_id` or `message` returns HTTP 422 Unprocessable Entity with standard detail format<br>• Non-string datatypes (integers, arrays, nulls) in required fields return 422<br>• Empty string message payloads handled predictably<br>• Large message payload stress handling<br>• Unmounted/missing paths return HTTP 404<br>• Disallowed HTTP methods (e.g. GET on `/chat`, POST on `/`) return HTTP 405 Method Not Allowed<br>• Header integrity: requests without proper Content-Type rejected or parsed | `test_api_contract.py` |
| **Tier 3** | **Combinations & Session Isolation** | • Multi-turn dialogue: subsequent messages to the same `session_id` maintain conversation continuity<br>• Session isolation: multiple independent session IDs submitted simultaneously do not cross-pollinate histories<br>• Interleaved calls across session A and session B maintain discrete histories<br>• Output directory path contracts: null during active dialogue, string upon completion | `test_flow_scenarios.py` |
| **Tier 4** | **Real-World Scenarios & Full Lifecycles** | • Complete research lifecycle: Session initialization -> Problem intake -> Clarification dialogue -> Spec confirmation -> File artifact verification on disk & HTTP retrieval<br>• Prototype DOM Fidelity: Verification of 4-stage pipeline indicators, benchmark preset cards, agent state cards, telemetry console, and report evaluation matrix<br>• UI View Navigation: Headless verification that view switching mechanisms (hash navigation or toggle functions) operate without script syntax errors | `test_flow_scenarios.py`<br>`test_spa_structure.py` |

---

## 3. Architecture & Test Runner Specifications

### 3.1 Test Framework & Runner
- **Test Runner**: `pytest` (version 9.0+)
- **Execution Mode**: In-process ASGI transport testing via `httpx.ASGITransport` against `fastapi.FastAPI` application instance (`app.main.app`).
- **DOM & Structure Parser**: `BeautifulSoup4` (`bs4`) for fast, robust server-rendered HTML inspection and DOM query validation.
- **Headless Browser Execution**: `playwright` (Chromium headless) for browser context initialization, script evaluation, and DOM interactions.
- **Deterministic Mocking**: For LLM interactions in CI/test runner environments where live Ollama/OpenAI servers may be unavailable or non-deterministic, tests provide a deterministic runner mock via pytest fixtures (`conftest.py`) simulating realistic Orchestrator responses, tool calls, and finalization sequences while keeping the full FastAPI HTTP endpoint, schema validation, and session store completely intact.

### 3.2 Directory Structure
All automated tests reside under `tests/`:
```
tests/
├── __init__.py
├── conftest.py               # Shared fixtures, test clients, mock runners
├── test_api_contract.py      # Tier 1 & Tier 2: Endpoint schemas, validation, headers, 404/405/422
├── test_spa_structure.py     # Tier 1 & Tier 4: DOM verification, 4 views, IDs, prototype fidelity
└── test_flow_scenarios.py    # Tier 3 & Tier 4: Multi-turn chat, isolation, lifecycle simulation
```

### 3.3 Test Execution Commands
- **Run all E2E test suites**:
  ```bash
  cd /Users/bharathbr/reasearch_agent && python3 -m pytest tests/ -v
  ```
- **Run specific tier / suite**:
  ```bash
  python3 -m pytest tests/test_api_contract.py -v
  python3 -m pytest tests/test_spa_structure.py -v
  python3 -m pytest tests/test_flow_scenarios.py -v
  ```
- **Run with coverage report**:
  ```bash
  python3 -m pytest tests/ -v --tb=short
  ```

---

## 4. Verification & Validation Metrics

| Metric | Target | Verification Method |
|---|---|---|
| **Pass Rate** | 100% | `pytest tests/` returns exit code 0 |
| **API Schema Compliance** | 100% | Response schemas match Pydantic `ChatResponse` model precisely |
| **Error Handling Coverage** | 100% of defined edge cases | 422, 404, 405 correctly validated with strict assertions |
| **DOM Element Presence** | 100% required SPA elements | All 4 views, sidebar, toast, forms, and report components validated |
| **Session Isolation** | Zero cross-talk | Assert distinct histories across multiple concurrent UUID sessions |

# Milestone 1 Review & Adversarial Stress Report: Backend Foundation & Static Output Mounting

**Reviewer**: `reviewer_m1_2`  
**Roles**: Reviewer, Adversarial Critic  
**Date**: 2026-10-14  
**Milestone**: Milestone 1 (Backend Foundation & Static Output Mounting)  
**Verdict**: **APPROVE**  

---

## 1. Observation

1. **Static Output & Static Asset Mounting (`research_orchestrator/app/main.py`)**:
   - Lines 20–25:
     ```python
     BASE_DIR = Path(__file__).resolve().parent.parent
     STATIC_DIR = BASE_DIR / "static"
     OUTPUTS_DIR = BASE_DIR / "outputs"

     STATIC_DIR.mkdir(parents=True, exist_ok=True)
     OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
     ```
   - Lines 100–106:
     ```python
     app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
     app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

     @app.get("/")
     async def root():
         return FileResponse(str(STATIC_DIR / "index.html"))
     ```
   - Observations: All paths are anchored to `BASE_DIR = Path(__file__).resolve().parent.parent` rather than relative string literals. Directory creation uses `parents=True, exist_ok=True` to guarantee idempotent startup without race conditions.

2. **Input Validation on `ChatRequest` (`research_orchestrator/app/main.py`)**:
   - Lines 30, 39–56:
     ```python
     SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
     ...
     @field_validator("session_id")
     @classmethod
     def validate_session_id(cls, v: str) -> str:
         v = v.strip()
         if not SESSION_ID_PATTERN.match(v):
             raise ValueError(
                 "session_id must be alphanumeric with hyphens or underscores (1-64 characters)"
             )
         return v

     @field_validator("message")
     @classmethod
     def validate_message(cls, v: str) -> str:
         v = v.strip()
         if not v:
             raise ValueError("message cannot be empty")
         return v
     ```
   - Observations: Enforces strict alphanumeric/hyphen/underscore format (1-64 characters) for `session_id`. Strips whitespace and requires non-empty `message`, rejecting empty strings or whitespace-only inputs with HTTP 422 Unprocessable Entity.

3. **Defense-in-Depth in Spec Persistence (`research_orchestrator/app/tools.py`)**:
   - Lines 72–80:
     ```python
     base_dir = (Path(__file__).resolve().parent.parent / "outputs").resolve()
     base_dir.mkdir(parents=True, exist_ok=True)
     output_dir = (base_dir / ctx.context.session_id).resolve()

     if not output_dir.is_relative_to(base_dir) or output_dir == base_dir:
         raise ValueError(f"Unsafe session_id: {ctx.context.session_id!r}")

     output_dir.mkdir(parents=True, exist_ok=True)
     ```
   - Line 95:
     ```python
     ctx.context.output_dir = f"outputs/{ctx.context.session_id}"
     ```
   - Observations: Traversal attempts bypassing the endpoint regex are trapped by `output_dir.is_relative_to(base_dir)` and `output_dir != base_dir`, preventing filesystem escaping. Returns standard relative output path `outputs/{session_id}`.

4. **Zero Dependency Footprint (`research_orchestrator/requirements.txt`)**:
   - `git diff research_orchestrator/requirements.txt` produced 0 output lines. File remains verbatim with 8 packages:
     ```
     openai-agents>=0.0.7
     openai>=1.60.0
     fastapi>=0.115.0
     uvicorn>=0.34.0
     python-dotenv>=1.0.0
     pydantic>=2.0.0
     httpx>=0.27.0
     pypdf>=4.0.0
     ```

5. **Pytest Execution**:
   - Command: `python3 -m pytest tests/ -v` from `research_orchestrator/`:
     ```
     ======================== 30 passed, 1 skipped in 1.58s =========================
     ```
   - Command from repository root `/Users/bharathbr/reasearch_agent`:
     ```
     ======================== 30 passed, 1 skipped in 1.63s =========================
     ```
   - Command from `/tmp`:
     ```
     ======================== 30 passed, 1 skipped in 1.91s =========================
     ```
   - The 1 skipped test is `test_tier1_live_spa_view_containers_contract`, which is an intentional, documented progressive gate waiting for Milestone 2 SPA shell integration (`TEST_READY.md` Section 4).

6. **Integrity Check**:
   - Inspected `app/main.py`, `app/tools.py`, and test files.
   - No hardcoded test responses or bypass facades detected. Real Starlette `StaticFiles` mounting, real Pydantic validation, and real OpenAI-agents execution pipeline are present.

---

## 2. Logic Chain

1. **CWD Independence**:
   - Observation 1 demonstrates that all directory resolution (`BASE_DIR`, `STATIC_DIR`, `OUTPUTS_DIR`, `base_dir`) is anchored to `Path(__file__).resolve().parent.parent`.
   - Observation 5 confirms that running test suites from `research_orchestrator/`, workspace root, or `/tmp` executes with identical results and 0 path failures.
   - Conclusion: The application is completely decoupled from the process's working directory.

2. **Mounting Correctness & Security**:
   - Observation 1 shows `app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")` and `app.mount("/static", ...)`.
   - Independent verification tests confirmed:
     - `GET /` -> HTTP 200 `text/html`.
     - `GET /static/index.html` -> HTTP 200 `text/html`.
     - `GET /outputs/{session_id}/research_spec.json` -> HTTP 200 `application/json`.
     - `GET /outputs` and `/outputs/` -> HTTP 404/403 (directory browsing disabled by default).
     - Encoded traversal `/outputs/%2e%2e/requirements.txt` -> HTTP 404.
   - Conclusion: Static mounting satisfies `PROJECT.md` Features #1 and #2 while securing against path traversal.

3. **Input Validation & Attack Surface Resistance**:
   - Observation 2 shows `SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")` and non-empty `message` validation.
   - Observation 3 shows defense-in-depth in `finalize_research_spec`.
   - Adversarial stress testing subjected the endpoints to 21 hostile `session_id` variants (including `../../etc/passwd`, command injection strings, template injection, whitespace, null bytes) and 4 invalid `message` variants:
     - All 25 malicious probes were rejected with HTTP 422 Unprocessable Entity.
     - Unicode text, emojis, and HTML tags in messages were processed safely without crashing or breaking JSON responses.
     - Direct invocation of `finalize_research_spec` with directory escaping arguments was blocked with `ValueError`.
   - Conclusion: Input validation and artifact persistence are hardened against boundary violations and path traversal.

4. **Dependency Compliance**:
   - Observation 4 confirms `git diff research_orchestrator/requirements.txt` is empty.
   - Conclusion: Zero new dependencies constraint is 100% satisfied.

---

## 3. Caveats

- **Progressive Test Gate**: `test_tier1_live_spa_view_containers_contract` is skipped in `tests/test_spa_structure.py`. This is expected per `TEST_READY.md` because `static/index.html` currently contains the initial template and will be replaced with the 4-view SPA layout during Milestone 2.
- **In-Memory History**: Session conversation history is kept in `sessions: dict[str, list]` in memory. Restarting the FastAPI process resets conversation memory, though disk outputs under `outputs/{session_id}/` remain persistent. This matches the current architecture specification.

---

## 4. Conclusion & Verdict

**Verdict**: **APPROVE**

Milestone 1 deliverables meet all criteria outlined in `PROJECT.md`, `TEST_READY.md`, and the user request:
- Static output mounting (`/outputs`) is cleanly mounted via `StaticFiles`.
- Root route (`GET /`) and static route (`GET /static/*`) correctly resolve to absolute paths.
- Directory creation is safe and idempotent (`mkdir(parents=True, exist_ok=True)`).
- Path resolution is fully independent of CWD.
- Robust input validation and defense-in-depth prevent path traversal and malformed payloads.
- Strict zero-dependency compliance maintained in `requirements.txt`.
- No integrity violations found.
- 100% of applicable tests pass (30 passed, 1 skipped M2 progressive gate).

---

## 5. Verification Method

To independently reproduce and verify this assessment:

1. **Run full automated pytest suite**:
   ```bash
   cd /Users/bharathbr/reasearch_agent/research_orchestrator
   python3 -m pytest tests/ -v
   ```
   *Expected outcome*: `30 passed, 1 skipped`

2. **Verify CWD independence (run from /tmp)**:
   ```bash
   PYTHONPATH=/Users/bharathbr/reasearch_agent/research_orchestrator python3 -m pytest /Users/bharathbr/reasearch_agent/research_orchestrator/tests -v
   ```
   *Expected outcome*: `30 passed, 1 skipped`

3. **Verify zero diff on requirements.txt**:
   ```bash
   git diff /Users/bharathbr/reasearch_agent/research_orchestrator/requirements.txt
   ```
   *Expected outcome*: 0 lines output (clean diff).

4. **Run adversarial boundary and traversal probe**:
   ```bash
   cd /Users/bharathbr/reasearch_agent/research_orchestrator
   python3 -c "
   from starlette.testclient import TestClient
   from app.main import app

   client = TestClient(app)
   assert client.get('/outputs/%2e%2e/requirements.txt').status_code == 404
   assert client.post('/chat', json={'session_id': '../../escape', 'message': 'ok'}).status_code == 422
   assert client.post('/chat', json={'session_id': 's1', 'message': '   '}).status_code == 422
   print('ADVERSARIAL_CHECK_PASSED')
   "
   ```
   *Expected outcome*: `ADVERSARIAL_CHECK_PASSED`

---

## Quality Review Summary

- **Verdict**: APPROVE
- **Correctness**: Pass. All routes, static mounts, and tool persistence logic function as specified.
- **Completeness**: Pass. All M1 items from `PROJECT.md` Feature Inventory (Items 1, 2, 3) are complete.
- **Quality**: Pass. Type annotations, clean Pydantic validators, explicit error handling.
- **Risk Assessment**: Low risk. Robust input validation and `is_relative_to` checks prevent path escaping.

## Adversarial Challenge Summary

- **Overall Risk Assessment**: LOW
- **Assumption Tested**: Can an attacker exploit static mounts or session IDs to read or overwrite arbitrary filesystem files?
  - Attack Scenario: Supply `../` or `%2e%2e` in `/outputs` route or `session_id` in `/chat`.
  - Result: Blocked at route resolution (404), Pydantic validation (422), and tool boundary (`ValueError`).
- **Assumption Tested**: Does moving the working directory cause startup or runtime failures?
  - Attack Scenario: Launch test suite from `/tmp` and workspace root.
  - Result: All paths resolve via `Path(__file__).resolve().parent.parent`; 100% pass rate.

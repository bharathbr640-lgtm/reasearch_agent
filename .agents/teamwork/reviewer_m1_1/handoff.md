# Review & Adversarial Challenge Report: Milestone 1 (Backend Foundation & Static Output Mounting)

**Reviewer**: `reviewer_m1_1`  
**Roles**: Reviewer & Adversarial Critic  
**Working Directory**: `/Users/bharathbr/reasearch_agent/.agents/teamwork/reviewer_m1_1`  
**Target Milestone**: Milestone 1 (Backend Foundation & Static Output Mounting)  
**Verdict**: **APPROVE**  
**Date**: 2026-10-14  

---

## 1. Observation

1. **Static Mounts and Path Resolution (`research_orchestrator/app/main.py`)**:
   - `BASE_DIR = Path(__file__).resolve().parent.parent` (line 20) ensures root-independent directory resolution.
   - `STATIC_DIR = BASE_DIR / "static"` (line 21) and `OUTPUTS_DIR = BASE_DIR / "outputs"` (line 22) are created with `mkdir(parents=True, exist_ok=True)` at lines 24–25.
   - Static mounting is configured via:
     - Line 100: `app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")`
     - Line 101: `app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")`
   - Line 104-106: Root route `GET /` serves `FileResponse(str(STATIC_DIR / "index.html"))`.

2. **Schema Validation & Boundary Hardening (`research_orchestrator/app/main.py`)**:
   - Line 30: `SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")`
   - Lines 39–47: `@field_validator("session_id")` strips whitespace and enforces regex compliance, rejecting traversal patterns (`../`), path separators (`/`, `\`), empty strings, or strings exceeding 64 characters with HTTP 422.
   - Lines 49–55: `@field_validator("message")` strips whitespace and rejects empty strings or pure whitespace with HTTP 422.
   - Lines 80–87: In `@app.post("/chat")`, exceptions caught during `Runner.run` pop the uncommitted user message from `history` before returning `ChatResponse`, ensuring session history is rolled back cleanly without duplicate messages upon retry.

3. **Output Resolution & Traversal Guard in Tools (`research_orchestrator/app/tools.py`)**:
   - Lines 72–78: Resolves `base_dir = (Path(__file__).resolve().parent.parent / "outputs").resolve()`, creates it, and resolves `output_dir = (base_dir / ctx.context.session_id).resolve()`.
   - Line 77: Asserts `if not output_dir.is_relative_to(base_dir) or output_dir == base_dir: raise ValueError(...)`.
   - Lines 83–91: Writes `clarified_problem_statement.md` and `research_spec.json` directly into `output_dir`.
   - Line 95: Sets `ctx.context.output_dir = f"outputs/{ctx.context.session_id}"`.

4. **Zero Dependency Enforcement (`research_orchestrator/requirements.txt`)**:
   - Command: `git diff /Users/bharathbr/reasearch_agent/research_orchestrator/requirements.txt`
   - Output: 0 lines changed (exact match with repository base).

5. **Automated Test Suite Execution**:
   - Command: `cd /Users/bharathbr/reasearch_agent/research_orchestrator && python3 -m pytest tests/ -v`
   - Result: `30 passed, 1 skipped in 1.75s`.
   - Skipped test: `test_tier1_live_spa_view_containers_contract` (properly gated with `pytest.skip` until M2 SPA layout is integrated into `static/index.html`).

6. **Standalone Verification & Adversarial Scripts**:
   - Explorer M1-3 One-Liner check: `✅ ALL 4 MILESTONE 1 CHECKS VERIFIED SUCCESSFULLY!`
   - Adversarial Boundary Probes: `✅ ALL ADVERSARIAL BOUNDARY PROBES PASSED!`
   - URL-encoded directory traversal probes on `/outputs`:
     - `/outputs/..%2frequirements.txt` -> HTTP 404
     - `/outputs/%2e%2e%2frequirements.txt` -> HTTP 404
     - `/outputs/%2e%2e/requirements.txt` -> HTTP 404
     - `/outputs/..%5crequirements.txt` -> HTTP 404
     - `/outputs/test/../../../../etc/passwd` -> HTTP 404
     - Zero leakage of file contents outside `outputs/`.
   - Direct tool invocation traversal probe: `../../escape`, `/etc/passwd`, `.`, `..`, and empty string all raised `ValueError: Unsafe session_id: ...`.

7. **Integrity Violation Audit**:
   - Checked for hardcoded test outputs: None found.
   - Checked for facade or dummy implementations: None found (`Runner.run` and `finalize_research_spec` contain genuine business logic).
   - Checked for bypassed task components: None found.
   - Checked for fabricated attestation: All claims independently reproduced and verified on local environment.

---

## 2. Logic Chain

1. **Compliance with PROJECT.md Specifications**:
   - `PROJECT.md` Feature 1 ("Backend Static Asset Mounting") requires serving `static/index.html` on `GET /` and mounting `/static`. Observations 1 and 5 show this is implemented and passing tests.
   - `PROJECT.md` Feature 2 ("Backend Spec Artifact Mounting") requires mounting `outputs/` via `StaticFiles` for direct client retrieval. Observations 1, 3, and 5 show `outputs/` is mounted and `test_tier1_get_outputs_research_spec` confirms HTTP 200 retrieval with `Content-Type: application/json`.
   - `PROJECT.md` Feature 3 ("Dependency Footprint Enforcement") mandates zero new dependencies. Observation 4 verifies `requirements.txt` is 100% unchanged.

2. **Security & Robustness Assessment**:
   - Input validation in `ChatRequest` (Observation 2) prevents invalid session IDs and empty messages at the HTTP boundary before invoking LLM runners.
   - Defense-in-depth in `tools.py` (Observation 3 and 6) guarantees that even if an invalid session ID were passed internally, directory traversal cannot escape `outputs/`.
   - Static file serving via Starlette `StaticFiles` normalizes paths and forbids escaping the mounted directory (Observation 6).
   - Error handling in `/chat` (Observation 2) cleanly pops pending user messages upon exceptions, avoiding corrupted conversation histories across retries.

3. **Integrity and Test Suite Health**:
   - Automated tests in `tests/test_api_contract.py`, `tests/test_flow_scenarios.py`, and `tests/test_spa_structure.py` exercise both positive and negative paths without mocking the routing layer or embedding false assertions.
   - Zero integrity violations were detected.

---

## 3. Caveats

1. **In-Memory Session Store**: `sessions: dict[str, list]` resides in-memory in the FastAPI application process. If the server process restarts, in-memory conversation history is reset, though artifacts on disk in `outputs/{session_id}/` remain persistent. This matches the specification in `PROJECT.md`.
2. **Pre-M2 Live SPA Gate**: `test_tier1_live_spa_view_containers_contract` is currently skipped by design until Milestone 2 integrates the Stitch prototype layout into `static/index.html`.

---

## 4. Conclusion

**Verdict**: **APPROVE**

Worker `worker_m1_1` has completely, cleanly, and securely implemented all Milestone 1 deliverables:
- `research_orchestrator/app/main.py`: Absolute directory paths, `/static` and `/outputs` static mounts, `session_id` and `message` validation, and error rollback.
- `research_orchestrator/app/tools.py`: Defensive path traversal checks and spec persistence.
- `research_orchestrator/requirements.txt`: 100% untouched.
- `tests/test_api_contract.py`: Full API contract test suite passing (30 passed, 1 skipped).

The codebase is robust, conforms strictly to `PROJECT.md`, and is ready to proceed to Milestone 2 (SPA Shell & High-Fidelity 4-View Layout).

---

## 5. Verification Method

To independently reproduce this verification:

```bash
# 1. Run full automated test suite
cd /Users/bharathbr/reasearch_agent/research_orchestrator && python3 -m pytest tests/ -v
# Expected: 30 passed, 1 skipped

# 2. Run standalone ASGI / TestClient verification script
cd /Users/bharathbr/reasearch_agent/research_orchestrator && python3 -c "
import uuid, json, shutil
from pathlib import Path
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

# GET /
r_root = client.get('/')
assert r_root.status_code == 200
assert 'text/html' in r_root.headers.get('content-type', '')

# GET /static/index.html
r_static = client.get('/static/index.html')
assert r_static.status_code == 200

# GET /outputs
sid = 'verify-m1-' + str(uuid.uuid4())
out_dir = Path('outputs') / sid
out_dir.mkdir(parents=True, exist_ok=True)
dummy_spec = {'original_problem_statement': 'Verification spec', 'status': 'finalized'}
(out_dir / 'research_spec.json').write_text(json.dumps(dummy_spec), encoding='utf-8')

try:
    r_out = client.get(f'/outputs/{sid}/research_spec.json')
    assert r_out.status_code == 200
    assert 'application/json' in r_out.headers.get('content-type', '')
    assert r_out.json()['original_problem_statement'] == 'Verification spec'
finally:
    shutil.rmtree(out_dir, ignore_errors=True)

print('✅ ALL 4 MILESTONE 1 CHECKS VERIFIED SUCCESSFULLY!')
"

# 3. Check requirements.txt diff
git diff /Users/bharathbr/reasearch_agent/research_orchestrator/requirements.txt
# Expected: 0 lines changed
```

# Milestone 1 Handoff Report: Backend Foundation & Static Output Mounting

**Agent**: `worker_m1_1`  
**Milestone**: Milestone 1 (Backend Foundation & Static Output Mounting)  
**Date**: 2026-10-14  

---

## 1. Observation

1. **Path Resolution & Static Mounting (`research_orchestrator/app/main.py`)**:
   - Previously, `app/main.py` mounted only `/static` using the relative string literal `"static"`, and `root()` returned `FileResponse("static/index.html")`. If launched from outside `research_orchestrator/`, Starlette raised `RuntimeError: Directory 'static' does not exist`.
   - `/outputs` was not mounted at all. Client requests to fetch finalized specs via HTTP (`/outputs/{session_id}/research_spec.json`) returned HTTP 404.
   - `ChatRequest` lacked input validation on `session_id` and `message`. Unsanitized strings with path traversal characters (`../../`) or empty strings were accepted into application logic.

2. **Output Resolution in Tools (`research_orchestrator/app/tools.py`)**:
   - `finalize_research_spec` created output directories via `Path("outputs") / ctx.context.session_id`. Because this was not checked against the base output directory, traversal strings could escape into arbitrary filesystem locations.

3. **API Contract Tests (`research_orchestrator/tests/test_api_contract.py`)**:
   - Did not include a test case verifying the `/outputs` static mount for finalized research specs.
   - `test_tier2_empty_string_message` had previously expected HTTP 200 before validation was introduced.

4. **Zero Dependency Constraint (`research_orchestrator/requirements.txt`)**:
   - Confirmed via `git diff`: 0 lines changed in `requirements.txt`.

---

## 2. Logic Chain

1. **Portable Directory Resolution**:
   By defining `BASE_DIR = Path(__file__).resolve().parent.parent`, `STATIC_DIR = BASE_DIR / "static"`, and `OUTPUTS_DIR = BASE_DIR / "outputs"`, with `.mkdir(parents=True, exist_ok=True)` executed at module initialization, directory paths are resolved accurately regardless of current working directory. This prevents startup crashes when running tests or servers from workspace roots.

2. **Clean Mounting of Static Outputs**:
   Adding `app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")` directly satisfies `PROJECT.md` Feature #2, enabling client browsers and test clients to fetch generated research artifacts (`research_spec.json` and `clarified_problem_statement.md`) via standard HTTP GET with proper MIME types (`application/json`, `text/markdown`).

3. **Input Sanitization & Boundary Hardening**:
   - In `app/main.py`, `SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")` and `@field_validator` on `ChatRequest` reject empty IDs, whitespace, path traversal tokens (`..`), path separators (`/`, `\`), and strings over 64 characters with HTTP 422 Unprocessable Entity.
   - `message` validator enforces non-empty strings (after `.strip()`), rejecting empty strings or pure whitespace with HTTP 422.
   - In `app/tools.py`, defense-in-depth is established using `output_dir.is_relative_to(base_dir) and output_dir != base_dir`, raising a `ValueError` if any path escapes the base outputs folder.

4. **Contract Verification**:
   - Added `test_tier1_get_outputs_research_spec` to `tests/test_api_contract.py` asserting that `GET /outputs/{session_id}/research_spec.json` serves valid JSON with HTTP 200 and `Content-Type: application/json`.
   - Updated `test_tier2_empty_string_message` to assert HTTP 422 for empty string messages and whitespace.
   - Added `test_tier2_invalid_session_id_format` to assert HTTP 422 for traversal and invalid session IDs.

---

## 3. Caveats

- In-memory conversation history (`sessions: dict[str, list]`) resets on server process restart, while disk-persisted outputs in `outputs/{session_id}/` remain persistent.
- `StaticFiles` default setting does not enable directory listing (browsing `/outputs` or `/outputs/{session_id}/` returns 404, while specific files return 200), which is the intended secure behavior.

---

## 4. Conclusion

All Milestone 1 requirements have been implemented and verified:
1. `research_orchestrator/app/main.py`:
   - Resolved absolute paths relative to `__file__`.
   - Mounted `/outputs` cleanly via `StaticFiles`.
   - Updated `/static` mount and `root()` route to use absolute paths.
   - Enforced Pydantic validation on `session_id` and non-empty `message` in `ChatRequest`.
2. `research_orchestrator/app/tools.py`:
   - Enforced safe path resolution and `is_relative_to` verification in `finalize_research_spec`.
3. `research_orchestrator/tests/test_api_contract.py`:
   - Added `test_tier1_get_outputs_research_spec`.
   - Validated empty message rejection (422) and invalid session ID formats.
4. `requirements.txt`:
   - 100% unchanged (0 diff).
5. All test suites pass:
   - Pytest suite: 30 passed, 1 skipped (pre-M2 layout).
   - Explorer verification scripts: All passed with 0 failures.

---

## 5. Verification Method

To independently verify the implementation, execute the following commands:

### Command 1: Full Pytest Suite
```bash
cd /Users/bharathbr/reasearch_agent/research_orchestrator
python3 -m pytest tests/ -v
```
**Expected Result**: 30 passed, 1 skipped.

### Command 2: Explorer M1-3 One-Liner Verification
```bash
cd /Users/bharathbr/reasearch_agent/research_orchestrator
python3 -c "
import uuid, json, shutil
from pathlib import Path
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. GET /
r_root = client.get('/')
assert r_root.status_code == 200, f'GET / failed: {r_root.status_code}'
assert 'text/html' in r_root.headers.get('content-type', ''), 'GET / content-type mismatch'

# 2. GET /static/index.html
r_static = client.get('/static/index.html')
assert r_static.status_code == 200, f'GET /static/index.html failed: {r_static.status_code}'
assert 'text/html' in r_static.headers.get('content-type', ''), 'GET /static content-type mismatch'

# 3. GET /outputs/{session_id}/research_spec.json
sid = 'verify-m1-' + str(uuid.uuid4())
out_dir = Path('outputs') / sid
out_dir.mkdir(parents=True, exist_ok=True)
dummy_spec = {'original_problem_statement': 'Verification spec', 'status': 'finalized'}
(out_dir / 'research_spec.json').write_text(json.dumps(dummy_spec), encoding='utf-8')

try:
    r_out = client.get(f'/outputs/{sid}/research_spec.json')
    assert r_out.status_code == 200, f'GET /outputs failed with status {r_out.status_code}'
    assert 'application/json' in r_out.headers.get('content-type', ''), f'MIME type is {r_out.headers.get(\"content-type\")}'
    assert r_out.json()['original_problem_statement'] == 'Verification spec'
finally:
    shutil.rmtree(out_dir, ignore_errors=True)

# 4. POST /chat schema validation (deterministic mock)
from unittest.mock import patch
from tests.conftest import MockRunResult

async def fake_run(agent, input, context):
    return MockRunResult(final_output='Ready', history=input)

with patch('agents.Runner.run', side_effect=fake_run):
    r_chat = client.post('/chat', json={'session_id': sid, 'message': 'Ping'})
    assert r_chat.status_code == 200, f'POST /chat failed: {r_chat.status_code}'
    data = r_chat.json()
    assert 'reply' in data and 'finalized' in data and 'output_dir' in data

print('✅ ALL 4 MILESTONE 1 CHECKS VERIFIED SUCCESSFULLY!')
"
```
**Expected Result**: `✅ ALL 4 MILESTONE 1 CHECKS VERIFIED SUCCESSFULLY!`

### Command 3: Adversarial Traversal & Boundary Probes
```bash
cd /Users/bharathbr/reasearch_agent/research_orchestrator
python3 -c "
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. Directory Traversal Immunity
r1 = client.get('/outputs/../requirements.txt')
assert r1.status_code == 404, f'Expected 404 for path traversal, got {r1.status_code}'

# 2. Method Not Allowed
assert client.post('/').status_code == 405
assert client.get('/chat').status_code == 405
assert client.put('/chat', json={'session_id':'x','message':'y'}).status_code == 405

# 3. Unprocessable Entity (422) Boundary Matrix
assert client.post('/chat', json={}).status_code == 422
assert client.post('/chat', json={'session_id': 's1'}).status_code == 422
assert client.post('/chat', json={'message': 'm1'}).status_code == 422
assert client.post('/chat', json={'session_id': ['bad'], 'message': 'm1'}).status_code == 422
assert client.post('/chat', json={'session_id': '../../bad', 'message': 'm1'}).status_code == 422
assert client.post('/chat', json={'session_id': 's1', 'message': ''}).status_code == 422
assert client.post('/chat', json={'session_id': 's1', 'message': '   '}).status_code == 422

print('✅ ALL ADVERSARIAL BOUNDARY PROBES PASSED!')
"
```
**Expected Result**: `✅ ALL ADVERSARIAL BOUNDARY PROBES PASSED!`

### Command 4: Zero Dependency Check
```bash
git diff /Users/bharathbr/reasearch_agent/research_orchestrator/requirements.txt
```
**Expected Result**: 0 lines changed (empty output).

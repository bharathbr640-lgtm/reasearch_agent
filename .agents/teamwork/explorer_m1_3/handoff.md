# Milestone 1 Verification Architecture & Test Specification Report

**Author**: `explorer_m1_3`  
**Milestone**: Milestone 1 — Backend Foundation & Static Output Mounting  
**Target Codebase**: `/Users/bharathbr/reasearch_agent/research_orchestrator`  
**Date**: 2026-10-14  

---

## 1. Observation

### 1.1 Existing Endpoint & Route Implementation (`app/main.py`)
In `/Users/bharathbr/reasearch_agent/research_orchestrator/app/main.py`:
- Lines 35-64 declare `POST /chat` handling `ChatRequest` (`session_id: str`, `message: str`) and returning `ChatResponse` (`reply: str`, `finalized: bool`, `output_dir: str | None`).
- Line 68 mounts the static directory:
  ```python
  app.mount("/static", StaticFiles(directory="static"), name="static")
  ```
- Lines 71-73 define root GET handler:
  ```python
  @app.get("/")
  async def root():
      return FileResponse("static/index.html")
  ```
- **Crucial Absence**: There is currently **no route or static mount** for `/outputs` in `app/main.py`.

### 1.2 Output Generation Behavior (`app/tools.py`)
In `/Users/bharathbr/reasearch_agent/research_orchestrator/app/tools.py`:
- Lines 72-84: When the research spec is confirmed, `finalize_research_spec` writes:
  - `outputs/{session_id}/clarified_problem_statement.md`
  - `outputs/{session_id}/research_spec.json`
- Line 88 sets `ctx.context.output_dir = str(output_dir)` (e.g., `"outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742"`).
- Existing session directories already present on disk in `outputs/`:
  - `outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/research_spec.json` (2,590 bytes)
  - `outputs/72356611-f0ef-4258-9ed1-17feb57880c3/`

### 1.3 Path Traversal and CWD Fragility
- Running Python from repo root `/Users/bharathbr/reasearch_agent`:
  ```
  RuntimeError: Directory 'static' does not exist
  ```
  Because `StaticFiles(directory="static")` and `FileResponse("static/index.html")` use CWD-relative paths rather than `Path(__file__).resolve().parent.parent`.
- If `outputs/` does not exist prior to `app.mount("/outputs", StaticFiles(directory="outputs"))`, Starlette raises `RuntimeError("Directory 'outputs' does not exist")`.

### 1.4 Test Infrastructure & Execution Environment
- Environment contains two Python invocations:
  - System Python: `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3` (Python 3.14.2) with `pytest 9.0.3` installed.
  - Virtual Environment: `/Users/bharathbr/reasearch_agent/research_orchestrator/.venv/bin/python` (Python 3.14.2) containing `fastapi` 0.142.2, `starlette` 1.7.0, `httpx` 0.28.1, `uvicorn` 0.54.0, `pydantic` 2.13.5, `pypdf` 6.19.0, `openai-agents` 0.22.3, `openai` 3.22.1. Note: `pytest` binary is not inside `.venv/bin/`.
- Both `python3` and `.venv/bin/python` can run tests via `starlette.testclient.TestClient` and `httpx.AsyncClient(transport=httpx.ASGITransport(app=app))`.
- Running `python3 -m pytest tests/test_api_contract.py -v` executes 14 tests in 0.05s: **14 PASSED**.
- Running `python3 -m pytest tests/test_flow_scenarios.py -v` executes 5 tests in 0.03s: **5 PASSED**.
- In `tests/test_flow_scenarios.py` lines 204-212, `GET /outputs/{session_id}/research_spec.json` currently returns `404` because `/outputs` is not yet mounted in `app/main.py`.
- Running empirical test with `app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")`:
  - `GET /outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/research_spec.json` immediately returns:
    `Status: 200`, `Content-Type: application/json`.
  - `GET /outputs/../requirements.txt` returns `Status: 404` (Path traversal blocked).
  - `POST /outputs/...` returns `Status: 405 Method Not Allowed`.

---

## 2. Logic Chain

1. **Static Outputs Requirement**:
   `PROJECT.md` Feature #2 states: *"Mount outputs/ static directory via existing FastAPI StaticFiles for direct client retrieval"*. Observation 1.1 reveals `main.py` only mounts `/static`. Therefore, client attempts to fetch finalized specs via HTTP fail with 404.

2. **Mounting Mechanics**:
   FastAPI leverages Starlette's `StaticFiles`. When `app.mount("/outputs", StaticFiles(directory=...), name="outputs")` is added, any request to `/outputs/{session_id}/{filename}` routes directly to the local filesystem file at `outputs/{session_id}/{filename}`.

3. **Content-Type Handling**:
   Starlette's `StaticFiles` uses Python's standard `mimetypes` library.
   - For `.json` files (e.g. `research_spec.json`), it automatically responds with `Content-Type: application/json`.
   - For `.html` files, it responds with `Content-Type: text/html; charset=utf-8`.
   - For `.md` files, it responds with `Content-Type: text/markdown; charset=utf-8`.
   This satisfies the acceptance criterion that `GET /outputs/{session_id}/research_spec.json` returns status 200 with `application/json`.

4. **Directory Resolution & Safety**:
   Observation 1.3 demonstrated that using relative string literals like `"static"` and `"outputs"` makes the service fail if launched from any directory other than `research_orchestrator/`. By defining:
   ```python
   BASE_DIR = Path(__file__).resolve().parent.parent
   STATIC_DIR = BASE_DIR / "static"
   OUTPUTS_DIR = BASE_DIR / "outputs"
   OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
   ```
   both directory existence is guaranteed and CWD independence is achieved.

5. **In-Process ASGI vs External HTTP Server**:
   To test the backend without socket overhead or port collisions, `httpx.ASGITransport(app=app)` and `starlette.testclient.TestClient(app)` invoke the ASGI application directly in memory.
   - `TestClient` provides synchronous testing.
   - `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")` provides asynchronous testing.
   - Both produce exact wire-protocol fidelity matching `uvicorn` without spinning up a live network daemon.

6. **Dependency Footprint Invariant**:
   `PROJECT.md` Feature #3 requires zero additions to `requirements.txt`. Because `fastapi`, `starlette`, and `httpx` are already installed and locked in `requirements.txt`, all M1 verification methods and changes require **0 new dependencies**.

---

## 3. Caveats

1. **Pytest Invocation Context**:
   `pytest` is installed in the system Python (`/Library/Frameworks/Python.framework/Versions/3.14/bin/pytest`) but not inside `.venv/bin/`. Running `python3 -m pytest tests/` or `pytest tests/` works immediately. For environments where `pytest` is completely unavailable, a standalone script using standard Python and `TestClient` is provided in Section 4.
2. **Live OpenAI Execution vs Offline Determinism**:
   Executing `POST /chat` without mocking requires an active `OPENAI_API_KEY` and network connection, incurring latency and token cost. All automated M1 regression tests use deterministic `unittest.mock.patch("agents.Runner.run")` so they run in milliseconds with zero cost and 100% reproducibility.
3. **Pre-existing vs Generated Output Dirs**:
   Session outputs created during tests must be cleaned up in a `finally` block or fixture to prevent cluttering `research_orchestrator/outputs/`.

---

## 4. Conclusion & Actionable Implementation Guidance

### 4.1 Required Worker Code Changes in `research_orchestrator/app/main.py`
To complete Milestone 1, the Worker should update `app/main.py` around lines 67-74 to:

```python
from pathlib import Path

# Base directories resolved relative to this source file
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Ensure output directory exists before mounting
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Static files & output artifact mounts
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


@app.get("/")
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))
```

---

## 5. Verification Method

### 5.1 Verification Commands for Reviewers

Reviewers can execute the following commands to confirm Milestone 1 compliance:

#### Command 1: Automated Pytest Suite Run
```bash
cd /Users/bharathbr/reasearch_agent/research_orchestrator
python3 -m pytest tests/test_api_contract.py tests/test_flow_scenarios.py -v
```
*Expected*: All 19 tests PASS with exit code 0.

#### Command 2: Zero Dependency Invariance Check
```bash
git diff /Users/bharathbr/reasearch_agent/research_orchestrator/requirements.txt
```
*Expected*: Empty output (0 lines changed).

#### Command 3: One-Liner M1 Contract Verification Script
Run directly using either `python3` or `.venv/bin/python`:
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
*Expected Output*:
```
✅ ALL 4 MILESTONE 1 CHECKS VERIFIED SUCCESSFULLY!
```

---

### 5.2 Verification Commands for Challengers & Adversarial Testing

Challengers should run the following boundary and error-injection checks:

#### Test 1: Directory Traversal Immunity
```bash
python3 -c "
from starlette.testclient import TestClient
from app.main import app
client = TestClient(app)
r = client.get('/outputs/../requirements.txt')
assert r.status_code == 404, f'Expected 404 for path traversal, got {r.status_code}'
print('PASS: Path traversal blocked with 404')
"
```

#### Test 2: Method Not Allowed on Static & Chat Routes
```bash
python3 -c "
from starlette.testclient import TestClient
from app.main import app
client = TestClient(app)
assert client.post('/').status_code == 405
assert client.get('/chat').status_code == 405
assert client.put('/chat', json={'session_id':'x','message':'y'}).status_code == 405
print('PASS: HTTP 405 correctly returned for disallowed methods')
"
```

#### Test 3: Unprocessable Entity (422) Boundary Matrix
```bash
python3 -c "
from starlette.testclient import TestClient
from app.main import app
client = TestClient(app)
assert client.post('/chat', json={}).status_code == 422
assert client.post('/chat', json={'session_id': 's1'}).status_code == 422
assert client.post('/chat', json={'message': 'm1'}).status_code == 422
assert client.post('/chat', json={'session_id': 999, 'message': 'm1'}).status_code in [200, 422]
assert client.post('/chat', json={'session_id': ['bad'], 'message': 'm1'}).status_code == 422
print('PASS: 422 schema boundaries enforced')
"
```

#### Test 4: Live HTTP Server (Uvicorn & cURL)
To verify with network socket transport:
```bash
# Terminal 1: Launch uvicorn
cd /Users/bharathbr/reasearch_agent/research_orchestrator
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2: cURL verification probes
# 1. Root check
curl -i http://127.0.0.1:8000/ | grep "HTTP/1.1 200 OK"
# 2. Static asset check
curl -i http://127.0.0.1:8000/static/index.html | grep "HTTP/1.1 200 OK"
# 3. Output artifact check (using existing session)
curl -i http://127.0.0.1:8000/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/research_spec.json | grep -E "(HTTP/1.1 200 OK|content-type: application/json)"
# 4. Invalid chat payload check
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{}'
# -> Should output: 422
```

---

### 5.3 Test Suite Expansion for Test Writers
To make `tests/test_api_contract.py` assert `GET /outputs` as an unconditional Tier 1 test (replacing the conditional check in `test_flow_scenarios.py`), add the following test case:

```python
def test_tier1_get_outputs_research_spec(sync_client: TestClient):
    """GET /outputs/{session_id}/research_spec.json must serve static JSON artifact with 200 OK."""
    session_id = f"test-spec-{uuid.uuid4()}"
    output_dir = Path("outputs") / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    spec_data = {
        "original_problem_statement": "Automated hate speech detection",
        "clarified_problem_statement": "Real-time toxic comment detector",
        "expected_input": "Social media comments",
        "expected_output": "Toxicity scores",
        "constraints": "< 50ms latency",
        "datasets_and_technologies": "BERT, Jigsaw",
        "other_requirements": "English",
        "assumptions": "None",
        "research_focus": "Throughput"
    }
    spec_file = output_dir / "research_spec.json"
    spec_file.write_text(json.dumps(spec_data), encoding="utf-8")

    try:
        response = sync_client.get(f"/outputs/{session_id}/research_spec.json")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "application/json" in response.headers.get("content-type", "")
        data = response.json()
        assert data["original_problem_statement"] == spec_data["original_problem_statement"]
        assert data["research_focus"] == spec_data["research_focus"]
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
```

---

## 6. Summary Checklist for Milestone 1 Completion

- [x] Verification methods formulated for `pytest`, `httpx.AsyncClient` (ASGITransport), and `starlette.testclient.TestClient`.
- [x] Exact commands specified for `GET /` (200 text/html).
- [x] Exact commands specified for `GET /static/...` (200 static asset).
- [x] Exact commands specified for `GET /outputs/{session_id}/research_spec.json` (200 application/json).
- [x] Exact commands specified for `POST /chat` (200 ChatResponse schema).
- [x] Worker code snippet provided with path resolution and directory creation.
- [x] Reviewer verification commands & standalone script provided.
- [x] Challenger adversarial checks (path traversal, 404, 405, 422) provided.
- [x] Zero backend dependency constraint verified.

# Milestone 1 Empirical Challenge Report

**Agent**: `challenger_m1_2`  
**Milestone**: Milestone 1 (Backend Foundation & Static Output Mounting)  
**Date**: 2026-10-14  
**Verdict**: **APPROVE**

---

## 1. Observation

Direct empirical observations gathered by executing tests, harnesses, and inspection scripts:

### A. Static Artifact Serving on `/outputs`
1. **JSON Artifact Retrieval**:
   - Command: `client.get('/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/research_spec.json')`
   - HTTP Status: `200 OK`
   - Verbatim Content-Type: `'content-type': 'application/json'`
   - Content-Length: `2590` bytes
   - Payload Validation: Successfully parsed via `json.loads()`. Verified keys: `original_problem_statement`, `clarified_problem_statement`, `expected_input`, `expected_output`, `constraints`, `datasets_and_technologies`, `other_requirements`, `assumptions`, `research_focus`.
2. **Markdown Artifact Retrieval**:
   - Command: `client.get('/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/clarified_problem_statement.md')`
   - HTTP Status: `200 OK`
   - Verbatim Content-Type: `'content-type': 'text/markdown; charset=utf-8'`
   - Content-Length: `574` bytes (Body length: 552 bytes)
3. **Non-existent Session Artifact**:
   - Command: `client.get('/outputs/nonexistent-id-00000000/research_spec.json')`
   - HTTP Status: `404 Not Found`
4. **Directory Browsing Protection**:
   - `client.get('/outputs')` -> `404 Not Found`
   - `client.get('/outputs/')` -> `404 Not Found`
   - `client.get('/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742')` -> `404 Not Found`
   - Direct directory browsing without a file target is blocked cleanly by Starlette's `StaticFiles`.

### B. Session Isolation (Sequential & Concurrent)
1. **Sequential Multi-turn Isolation**:
   - Evaluated 3 distinct sessions (`s_alpha`, `s_beta`, `s_gamma`) interleaved sequentially.
   - `sessions[s_alpha]` recorded 4 turns (2 user, 2 assistant). Content strictly contained Alpha prompts; zero instances of Beta or Gamma tokens.
   - `sessions[s_beta]` recorded 4 turns. Content strictly contained Beta prompts; zero instances of Alpha or Gamma tokens.
   - Finalizing `s_beta` generated artifacts strictly at `outputs/{s_beta}/`. No directories were created for `s_alpha` or `s_gamma`.
2. **Concurrent Multi-threaded Stress Isolation**:
   - Tested 8 simultaneous worker threads using `concurrent.futures.ThreadPoolExecutor(max_workers=8)` issuing multi-turn requests with randomized async delays (5ms to 20ms) in mock model execution.
   - All 8 concurrent sessions completed turn accumulation and spec finalization with `200 OK` and `finalized: True`.
   - Verified that every `sessions[sid]` contained exactly 4 turns belonging exclusively to `sid`, with 0 cross-contamination across all permutations of session pairs.
   - Verified each session created an independent directory `outputs/{sid}/` containing valid `research_spec.json` and `clarified_problem_statement.md` matching only that session's data.

### C. Working Directory (CWD) Independence
1. **Multi-CWD Execution Tests**:
   Executed test harness across 5 distinct working directories:
   - `/Users/bharathbr/reasearch_agent` (repository root)
   - `/Users/bharathbr/reasearch_agent/research_orchestrator` (module directory)
   - `/Users/bharathbr/reasearch_agent/research_orchestrator/app` (submodule directory)
   - `/private/tmp` (arbitrary system directory)
   - `/Users/bharathbr` (user home directory)
2. **Path Verification**:
   - `app.main.BASE_DIR`: Resolved to `/Users/bharathbr/reasearch_agent/research_orchestrator` in all cases.
   - `app.main.STATIC_DIR`: Resolved to `/Users/bharathbr/reasearch_agent/research_orchestrator/static`.
   - `app.main.OUTPUTS_DIR`: Resolved to `/Users/bharathbr/reasearch_agent/research_orchestrator/outputs`.
   - `app.tools.finalize_research_spec`: Resolved destination directory strictly inside `/Users/bharathbr/reasearch_agent/research_orchestrator/outputs/` and never inside the executing CWD.
   - Zero crashes or relative path resolution errors occurred.

### D. Full Pytest Suite Execution
- Executed from `/Users/bharathbr/reasearch_agent`:
  `python3 -m pytest research_orchestrator/tests/ -v`
- Result: **91 passed, 1 skipped** (the 1 skip is `test_tier1_live_spa_view_containers_contract` which is explicitly guarded for Milestone 2 SPA deployment).

---

## 2. Logic Chain

1. **Static Serving Verification (Observation A.1 - A.4)**:
   In `research_orchestrator/app/main.py`:
   - Line 22: `OUTPUTS_DIR = BASE_DIR / "outputs"`
   - Line 101: `app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")`
   Starlette's `StaticFiles` serves files directly with MIME type detection using Python's standard `mimetypes` library.
   - `.json` files are served with `application/json` Content-Type and parsed without error.
   - `.md` files are served with `text/markdown; charset=utf-8` Content-Type.
   - Non-existent files/directories trigger Starlette's `404 Not Found` response without crashing or exposing directory trees.

2. **Session Isolation Verification (Observation B.1 - B.2)**:
   In `research_orchestrator/app/main.py`:
   - Line 28: `sessions: dict[str, list] = {}`
   - Lines 69-70 & 90: `history = sessions.get(req.session_id, [])`, `sessions[req.session_id] = result.to_input_list()`
   - Line 72: `ctx = SessionContext(session_id=req.session_id)`
   Because each request extracts and updates `sessions[req.session_id]` independently and instantiates a unique `SessionContext` instance per request invocation, there is no shared mutable request state. Even under high-concurrency multi-threaded execution with variable async latency, conversations remain completely partitioned by session ID.
   In `research_orchestrator/app/tools.py`:
   - Lines 74-80: `output_dir = (base_dir / ctx.context.session_id).resolve()` ensures output directories are keyed strictly by `session_id`.

3. **CWD Independence (Observation C.1 - C.2)**:
   In `research_orchestrator/app/main.py`:
   - Line 20: `BASE_DIR = Path(__file__).resolve().parent.parent`
   In `research_orchestrator/app/tools.py`:
   - Line 72: `base_dir = (Path(__file__).resolve().parent.parent / "outputs").resolve()`
   Because all paths are resolved anchored to `__file__` rather than `Path.cwd()` or relative string literals, process working directory changes have zero effect on path resolution.

---

## 3. Caveats

1. **APFS Case-Insensitive Filesystem**:
   On macOS APFS, the filesystem preserves case but is case-insensitive. If a client creates `session_id="ABC"` and another creates `session_id="abc"`, `sessions` dict will treat them as two separate in-memory conversations, but on disk `outputs/ABC` and `outputs/abc` will reference the same directory. In production, standard UUIDs (such as those generated by `crypto.randomUUID()`) are uniformly lowercase hex strings with hyphens, preventing this collision.
2. **Hidden Files in `/outputs`**:
   StaticFiles mounts the entire `outputs/` directory. OS-generated metadata files (e.g. `outputs/.DS_Store` or `outputs/.gitkeep`) return `200 OK` if requested directly by exact name (`GET /outputs/.DS_Store`), though directory browsing remains blocked (`404`).
3. **In-Memory Store Lifespan**:
   The `sessions` dictionary resides in server memory. Process restart wipes session history in memory, while persisted output artifacts on disk remain available under `/outputs/{session_id}/`.

---

## 4. Conclusion

**Verdict: APPROVE**

Milestone 1 satisfies all contract and functional requirements:
- Static artifact mounting on `/outputs` operates correctly for JSON and Markdown artifacts with accurate Content-Type headers and 404 handling.
- Sequential and concurrent multi-threaded sessions exhibit strict isolation with zero memory or filesystem crosstalk.
- Directory resolution is fully decoupled from CWD and operates reliably regardless of invocation path.
- Test coverage is extensive: 91 passing tests (0 failures).

---

## 5. Verification Method

To independently reproduce and verify this assessment, run the following commands:

### Command 1: Pytest Regression Suite
```bash
cd /Users/bharathbr/reasearch_agent
python3 -m pytest research_orchestrator/tests/ -v
```
**Expected Output**: `91 passed, 1 skipped` in ~3.5s.

### Command 2: Empirical Milestone 1 Stress Verification Script
```bash
cd /Users/bharathbr/reasearch_agent
python3 -c "
import sys
from starlette.testclient import TestClient
sys.path.insert(0, '/Users/bharathbr/reasearch_agent/research_orchestrator')
from app.main import app

client = TestClient(app)

# 1. JSON Artifact
r_json = client.get('/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/research_spec.json')
assert r_json.status_code == 200
assert 'application/json' in r_json.headers.get('content-type', '')
assert 'original_problem_statement' in r_json.json()

# 2. Markdown Artifact
r_md = client.get('/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/clarified_problem_statement.md')
assert r_md.status_code == 200
assert 'text/markdown' in r_md.headers.get('content-type', '')

# 3. 404 Nonexistent
r_404 = client.get('/outputs/nonexistent-id-00000000/research_spec.json')
assert r_404.status_code == 404

print('ALL EMPIRICAL M1 CHECKS PASSED!')
"
```
**Expected Output**: `ALL EMPIRICAL M1 CHECKS PASSED!`

# Milestone 1 Investigation & Handoff Report: Backend Foundation & Static Output Mounting

**Author**: `explorer_m1_1`  
**Target File**: `research_orchestrator/app/main.py`  
**Working Directory**: `/Users/bharathbr/reasearch_agent/research_orchestrator`  
**Date**: 2026-10-14  

---

## 1. Observation

### Observation 1.1: Agent Output Generation and Placement
In `research_orchestrator/app/tools.py` (lines 39–90), the `finalize_research_spec` function tool is defined as follows:
```python
40: async def finalize_research_spec(
...
72:     output_dir = Path("outputs") / ctx.context.session_id
73:     output_dir.mkdir(parents=True, exist_ok=True)
74: 
75:     # Clarified problem statement as Markdown
76:     md_path = output_dir / "clarified_problem_statement.md"
77:     md_path.write_text(
78:         f"# Clarified Problem Statement\n\n{spec.clarified_problem_statement}\n",
79:         encoding="utf-8",
80:     )
81: 
82:     # Full research spec as JSON
83:     json_path = output_dir / "research_spec.json"
84:     json_path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
85: 
86:     # Mark session as finalized so the endpoint can report it
87:     ctx.context.finalized = True
88:     ctx.context.output_dir = str(output_dir)
89: 
90:     return f"Research specification saved to {output_dir}/"
```
In `research_orchestrator/app/main.py` (lines 35–64), the `/chat` route populates `ChatResponse`:
```python
60:     return ChatResponse(
61:         reply=result.final_output,
62:         finalized=ctx.finalized,
63:         output_dir=ctx.output_dir if ctx.finalized else None,
64:     )
```
Downstream agents (`project_research/run.py` lines 99–100, and `paper_research/run.py` lines 90–91) consume `outputs/{session_id}/research_spec.json` and persist:
- `outputs/{session_id}/project_findings.json`
- `outputs/{session_id}/project_findings.md`
- `outputs/{session_id}/project_research_trace.json`
- `outputs/{session_id}/paper_findings.json`
- `outputs/{session_id}/paper_findings.md`
- `outputs/{session_id}/paper_research_trace.json`

Existing sample session directories are directly observed on disk:
- `/Users/bharathbr/reasearch_agent/research_orchestrator/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/`
- `/Users/bharathbr/reasearch_agent/research_orchestrator/outputs/72356611-f0ef-4258-9ed1-17feb57880c3/`

### Observation 1.2: Current Static Mounting in `app/main.py`
In `research_orchestrator/app/main.py` (lines 6–7 and lines 67–74):
```python
6: from fastapi.responses import FileResponse
7: from fastapi.staticfiles import StaticFiles
...
67: # Static files & root page
68: app.mount("/static", StaticFiles(directory="static"), name="static")
69: 
70: 
71: @app.get("/")
72: async def root():
73:     return FileResponse("static/index.html")
```
Notice `StaticFiles` is already imported from `fastapi.staticfiles`. Currently, only `/static` is mounted, pointing to `"static"`. `/outputs` is not mounted.

### Observation 1.3: Starlette `StaticFiles` Initialization Failure on Missing Directory
Direct execution test running `StaticFiles(directory="nonexistent_dir")` demonstrated:
```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    from starlette.staticfiles import StaticFiles; StaticFiles(directory='nonexistent_dir_12345')
  File ".../site-packages/starlette/staticfiles.py", line 56, in __init__
    raise RuntimeError(f"Directory '{directory}' does not exist")
RuntimeError: Directory 'nonexistent_dir_12345' does not exist
```
Starlette synchronously validates `os.path.isdir(directory)` during `StaticFiles.__init__`. If `outputs` does not exist on disk when `FastAPI` initializes (e.g. fresh clone, container deployment, or clean git checkout), the server crashes immediately with `RuntimeError`.

### Observation 1.4: Direct Retrieval Test of Mounted Outputs
Running a standalone FastAPI TestClient mounting `outputs` after ensuring directory existence:
```python
outputs_dir = Path("outputs")
outputs_dir.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
```
Verified results:
- `GET /outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/research_spec.json` -> Status `200`, `Content-Type: application/json`
- `GET /outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/clarified_problem_statement.md` -> Status `200`, `Content-Type: text/markdown; charset=utf-8`
- `GET /outputs/nonexistent-session-id/research_spec.json` -> Status `404 Not Found`
- `GET /outputs/../requirements.txt` -> Status `404 Not Found` (Directory traversal prevented by Starlette)

### Observation 1.5: Dependency Footprint (`requirements.txt`)
`research_orchestrator/requirements.txt` contains:
```
1: openai-agents>=0.0.7
2: openai>=1.60.0
3: fastapi>=0.115.0
4: uvicorn>=0.34.0
5: python-dotenv>=1.0.0
6: pydantic>=2.0.0
7: httpx>=0.27.0
8: pypdf>=4.0.0
```
- `fastapi` depends on `starlette`. `starlette.staticfiles.StaticFiles` is already installed and re-exported by `fastapi.staticfiles.StaticFiles`.
- `pathlib` is in Python's standard library.
- Zero changes are needed in `requirements.txt`.

---

## 2. Logic Chain

1. **Step 1 (Path Alignment)**: From Obs 1.1, `app/tools.py` creates session directories at `Path("outputs") / ctx.context.session_id`. When the orchestrator finalizes a spec, `ctx.context.output_dir` is returned as `"outputs/<session_id>"`. Downstream agents also write their artifacts to `outputs/<session_id>/`. Therefore, mounting the root `/outputs` URL prefix to directory `"outputs"` creates a direct 1:1 match with the relative path string returned to the client and stored on disk.
2. **Step 2 (Startup Safety)**: From Obs 1.3, Starlette's `StaticFiles` executes `os.path.isdir(directory)` in `__init__`. If the folder is absent, it throws a fatal `RuntimeError`. Because `outputs/` is gitignored in production repositories, a fresh checkout will lack this directory until the first research run. Pre-creating the directory with `Path("outputs").mkdir(parents=True, exist_ok=True)` in `app/main.py` guarantees idempotent, crash-free application startup.
3. **Step 3 (Contract & Security Compliance)**: From Obs 1.4, mounting `/outputs` with `StaticFiles(directory="outputs")` cleanly satisfies the interface contract defined in `PROJECT.md` line 97: `GET /outputs/{session_id}/{filename}` serves `research_spec.json` as `application/json` and `clarified_problem_statement.md` as `text/markdown`. Furthermore, Starlette natively rejects path traversal attempts.
4. **Step 4 (Zero New Dependencies)**: From Obs 1.5, `StaticFiles` is already imported in `app/main.py`, and `Path` is a Python built-in module. No new packages or version changes are needed in `requirements.txt`, strictly meeting Requirement R2 and Feature #3.

---

## 3. Caveats

- **Working Directory Assumption**: The relative paths `directory="static"` and `directory="outputs"` assume the application is executed from `research_orchestrator/` (as specified in README: `cd research_orchestrator && uvicorn app.main:app`). This is consistent with existing code in `app/main.py` (`"static"`) and `app/tools.py` (`"outputs"`).
- **Directory Browsing**: By default, `StaticFiles(html=False)` disables directory listing. Navigating directly to `GET /outputs` or `GET /outputs/{session_id}/` returns 404, while specific files (`.../research_spec.json`) return 200. This is the desired secure behavior.
- **Client Cache Headers**: StaticFiles sets default caching headers. In development/testing, cache bust or conditional requests are standard.

---

## 4. Conclusion & Recommended Code Changes for Worker

### Target File
`/Users/bharathbr/reasearch_agent/research_orchestrator/app/main.py`

### Proposed Changes
1. Add `from pathlib import Path` to the top imports.
2. In the static mount section, ensure `outputs_dir = Path("outputs")` is created with `exist_ok=True`.
3. Mount `/outputs` via `app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")`.

### Precise Code Diffs

#### Chunk 1: Import `Path`
**Lines 3–8 in `research_orchestrator/app/main.py`:**
```python
<<<< BEFORE
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
====
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
>>>> AFTER
```

#### Chunk 2: Create `outputs` dir and mount `/outputs`
**Lines 67–74 in `research_orchestrator/app/main.py`:**
```python
<<<< BEFORE
# Static files & root page
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")
====
# ── Static files & output directory mounting ─────────────────────────

outputs_dir = Path("outputs")
outputs_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


@app.get("/")
async def root():
    return FileResponse("static/index.html")
>>>> AFTER
```

### Complete Resulting `app/main.py`
For reference and sanity check, the complete file will be:
```python
"""FastAPI application – serves the chat endpoint and the static UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agents import Runner

from app.agent import orchestrator_agent
from app.tools import SessionContext

app = FastAPI(title="AI Research Orchestrator")

# ── In-memory conversation store ─────────────────────────────────────
sessions: dict[str, list] = {}


# ── Request / response schemas ───────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    finalized: bool
    output_dir: str | None = None


# ── Endpoints ────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Send a user message and receive the Orchestrator's reply."""
    history = sessions.get(req.session_id, [])
    history.append({"role": "user", "content": req.message})

    ctx = SessionContext(session_id=req.session_id)

    try:
        result = await Runner.run(
            orchestrator_agent,
            input=history,
            context=ctx,
        )
    except Exception as exc:
        # Remove the message we just appended so the user can retry.
        history.pop()
        return ChatResponse(
            reply=f"Error communicating with the model: {exc}",
            finalized=False,
        )

    # Persist the full conversation (including assistant + tool turns).
    sessions[req.session_id] = result.to_input_list()

    return ChatResponse(
        reply=result.final_output,
        finalized=ctx.finalized,
        output_dir=ctx.output_dir if ctx.finalized else None,
    )


# ── Static files & output directory mounting ─────────────────────────

outputs_dir = Path("outputs")
outputs_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


@app.get("/")
async def root():
    return FileResponse("static/index.html")
```

---

## 5. Verification Method

To verify the implementation once applied:

### Command 1: Fast Python Unit / Contract Verification
Run the following verification script from `research_orchestrator/`:
```bash
python3 -c "
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. Verify GET /
r_root = client.get('/')
assert r_root.status_code == 200, f'GET / failed: {r_root.status_code}'

# 2. Verify static mount
r_static = client.get('/static/index.html')
assert r_static.status_code == 200, f'GET /static/index.html failed: {r_static.status_code}'

# 3. Verify outputs mount on an existing session spec
r_spec = client.get('/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/research_spec.json')
assert r_spec.status_code == 200, f'GET /outputs/.../research_spec.json failed: {r_spec.status_code}'
assert r_spec.headers.get('content-type') == 'application/json'

# 4. Verify outputs mount on an existing markdown summary
r_md = client.get('/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/clarified_problem_statement.md')
assert r_md.status_code == 200, f'GET /outputs/.../clarified_problem_statement.md failed: {r_md.status_code}'
assert 'text/markdown' in r_md.headers.get('content-type', '')

# 5. Verify 404 on nonexistent session
r_404 = client.get('/outputs/nonexistent-session-id/research_spec.json')
assert r_404.status_code == 404, f'Expected 404, got {r_404.status_code}'

# 6. Verify traversal prevention
r_trav = client.get('/outputs/../requirements.txt')
assert r_trav.status_code in (404, 400), f'Expected traversal blocked, got {r_trav.status_code}'

print('✅ Milestone 1 backend mounting verification PASSED!')
"
```

### Command 2: Existing Unit Test Suite
Ensure no regression in existing tests:
```bash
pytest paper_research/test_agent2.py
```
Expected output: 10 passed.

### Invalidation Conditions
- If `outputs` directory does not exist and `Path("outputs").mkdir(parents=True, exist_ok=True)` is omitted, importing `app.main` or launching `uvicorn` will fail with `RuntimeError: Directory 'outputs' does not exist`.
- If `/outputs` mount is missing `name="outputs"` or uses an incorrect mount path, client requests to `GET /outputs/{session_id}/...` will return 404.

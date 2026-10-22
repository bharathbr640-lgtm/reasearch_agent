# Investigation & Safeguards Report: Backend Error Handling & Session Security (Milestone 1)

## Executive Summary
This report analyzes error handling, session edge cases, and static mounting security in `research_orchestrator/app/main.py` and `app/tools.py`.
Key findings:
1. **Directory Traversal in Session Storage**: Unsanitized `session_id` in `app/tools.py` (`Path("outputs") / session_id`) allows escaping `outputs/` via `../../` or absolute paths (`/tmp/...`), enabling arbitrary directory and file writes.
2. **CWD Dependency in Static Mounts**: Relative paths (`"static"`, `"outputs"`) cause `RuntimeError` if the server is started from outside `research_orchestrator/`.
3. **Edge Case Behavior**: Unknown `session_id`s cleanly initialize a new session in `/chat`, but return 404 on `/outputs`. Traversal requests to `/outputs/` are safely caught as 404 by Starlette `StaticFiles`, but the backend write path (`POST /chat` -> `finalize_research_spec`) was unprotected.
4. **Concrete Worker Recommendations**: Add Pydantic validation on `ChatRequest` (`r"^[a-zA-Z0-9_-]{1,64}$"`), defense-in-depth path check in `tools.py` via `Path.is_relative_to()`, directory creation (`mkdir`) on server startup, and absolute path mounting for both `/static` and `/outputs`.

---

## 1. Observation

### 1.1 Source Code Locations & Relevant Lines

#### A. `research_orchestrator/app/main.py`
- **Lines 16-18**: In-memory session dictionary
  ```python
  # ── In-memory conversation store ─────────────────────────────────────
  sessions: dict[str, list] = {}
  ```
- **Lines 22-31**: Request & Response schemas
  ```python
  class ChatRequest(BaseModel):
      session_id: str
      message: str

  class ChatResponse(BaseModel):
      reply: str
      finalized: bool
      output_dir: str | None = None
  ```
  *Observation*: `session_id` is an unbounded `str` without regex, length, or character constraints. Empty strings (`""`), spaces (`"   "`), traversal tokens (`"../../"`), and null bytes (`"\x00"`) pass Pydantic schema validation.
- **Lines 35-65**: `POST /chat` handler
  ```python
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
  ```
- **Lines 67-74**: Static file mounts and root endpoint
  ```python
  # Static files & root page
  app.mount("/static", StaticFiles(directory="static"), name="static")


  @app.get("/")
  async def root():
      return FileResponse("static/index.html")
  ```
  *Observation*: Relative directory paths `"static"` and `"static/index.html"` are used. `/outputs` is not mounted.

#### B. `research_orchestrator/app/tools.py`
- **Lines 72-89**: Output path creation and persistence
  ```python
      output_dir = Path("outputs") / ctx.context.session_id
      output_dir.mkdir(parents=True, exist_ok=True)

      # Clarified problem statement as Markdown
      md_path = output_dir / "clarified_problem_statement.md"
      md_path.write_text(
          f"# Clarified Problem Statement\n\n{spec.clarified_problem_statement}\n",
          encoding="utf-8",
      )

      # Full research spec as JSON
      json_path = output_dir / "research_spec.json"
      json_path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")

      # Mark session as finalized so the endpoint can report it
      ctx.context.finalized = True
      ctx.context.output_dir = str(output_dir)
  ```
  *Observation*: `Path("outputs") / ctx.context.session_id` directly joins the unvalidated `session_id` string.

---

### 1.2 Empirical Tests & Verbatim Output

#### Observation 1: Relative Path Startup Failure Outside Working Directory
Command executed from `/Users/bharathbr/reasearch_agent`:
```bash
./research_orchestrator/.venv/bin/python -c '
from starlette.staticfiles import StaticFiles
StaticFiles(directory="static")
'
```
Verbatim Error:
```
RuntimeError: Directory 'static' does not exist
```

#### Observation 2: Directory Traversal via `Path("outputs") / session_id`
Command executed in `research_orchestrator`:
```bash
./.venv/bin/python -c '
from pathlib import Path
outputs_base = Path("outputs").resolve()
cases = [
    ("normal_uuid", "28a8c6cf-20c9-45e8-8707-0d4162a66742"),
    ("traversal_relative", "../../escape_test"),
    ("absolute_path", "/tmp/escape_test"),
    ("empty_string", ""),
    ("null_byte", "bad\x00id"),
    ("long_string", "x" * 300),
]
for name, s in cases:
    try:
        p = (Path("outputs") / s).resolve()
        is_safe = p.is_relative_to(outputs_base) and p != outputs_base
        print(f"[{name}] -> {str(p)} | is_safe={is_safe}")
    except Exception as e:
        print(f"[{name}] -> Exception: {type(e).__name__}: {e}")
'
```
Verbatim Output:
```
[normal_uuid] -> /Users/bharathbr/reasearch_agent/research_orchestrator/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742 | is_safe=True
[traversal_relative] -> /Users/bharathbr/reasearch_agent/escape_test | is_safe=False
[absolute_path] -> /private/tmp/escape_test | is_safe=False
[empty_string] -> /Users/bharathbr/reasearch_agent/research_orchestrator/outputs | is_safe=False
[null_byte] -> Exception: ValueError: lstat: embedded null character in path
[long_string] -> /Users/bharathbr/reasearch_agent/research_orchestrator/outputs/xxxx... | is_safe=True
```
`mkdir` on `long_string` (300 chars):
```
Failed with OSError: [Errno 63] File name too long
```

#### Observation 3: StaticFiles URL Traversal Protection
Command executed:
```bash
./.venv/bin/python -c '
import asyncio, httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

test_app = FastAPI()
test_app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

async def test():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as c:
        r1 = await c.get("/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/research_spec.json")
        r2 = await c.get("/outputs/unknown-session/research_spec.json")
        r3 = await c.get("/outputs/../app/main.py")
        r4 = await c.get("/outputs/%2e%2e%2fapp/main.py")
        r5 = await c.get("/outputs/")
        print("valid:", r1.status_code, "unknown:", r2.status_code, "traversal:", r3.status_code, "enc_traversal:", r4.status_code, "dir_list:", r5.status_code)

asyncio.run(test())
'
```
Verbatim Output:
```
valid: 200 unknown: 404 traversal: 404 enc_traversal: 404 dir_list: 404
```

---

## 2. Logic Chain

1. **Vulnerability in Write Path vs. Security in Read Path**:
   - Observation 3 shows Starlette's `StaticFiles` prevents client GET URL directory traversal (`/outputs/../app/main.py` -> `404`).
   - However, Observation 2 proves that `Path("outputs") / ctx.context.session_id` in `app/tools.py` has **no traversal protection**.
   - If an adversarial or corrupted request sends `session_id: "../../malicious"` or `/tmp/malicious`, `output_dir.mkdir(parents=True, exist_ok=True)` writes `research_spec.json` and `clarified_problem_statement.md` completely outside the `outputs` directory.
   - Therefore, input sanitization must be enforced at the schema boundary (`ChatRequest`) and backed by a defensive check in `app/tools.py`.

2. **Session ID Format & Contract Compatibility**:
   - `PROJECT.md` line 77 states `session_id: "string (UUID)"`.
   - `PROJECT.md` line 31 states `#AG-9042` is used as a session badge identifier in the prototype UI.
   - Existing valid session IDs in the repository include `28a8c6cf-20c9-45e8-8707-0d4162a66742` (36-character standard UUID4) and test IDs like `test-session-1` or `curl-test-1`.
   - A validation regex pattern `^[a-zA-Z0-9_-]{1,64}$`:
     - Disallows `/`, `\`, `.`, null bytes, control characters, and whitespace.
     - Disallows relative directory stepping (`..` or `.`).
     - Disallows absolute filesystem paths.
     - Constrains length to 64 characters (well below the 255-byte filesystem limit).
     - Fully accommodates standard UUIDs, alphanumeric slugs, and hyphenated session IDs.

3. **Unknown Session ID Behavior**:
   - When an unknown `session_id` is submitted to `POST /chat`, `sessions.get(req.session_id, [])` returns `[]`. The model treats it as the first message of a new conversation and persists it upon turn completion.
   - When an unknown `session_id` is requested via `GET /outputs/{session_id}/research_spec.json`, Starlette's `StaticFiles` checks disk existence and returns HTTP 404 Not Found.
   - Thus, unknown session IDs handle gracefully on both endpoints without exceptions.

4. **Error Handling Architecture**:
   - In `app/main.py`:
     ```python
     except Exception as exc:
         history.pop()
         return ChatResponse(
             reply=f"Error communicating with the model: {exc}",
             finalized=False,
         )
     ```
   - Returning HTTP 200 with an error reply provides soft recovery for the conversational frontend, but if the client inspects HTTP status codes (e.g. `res.ok`), it treats this as a successful response.
   - The Pydantic schema validation returns HTTP 422 Unprocessable Entity automatically on invalid/empty `session_id` or `message`, aligning with `PROJECT.md` line 91.

5. **Path Resolution & Startup Portability**:
   - Observation 1 proved that relative path initialization (`StaticFiles(directory="static")`) crashes when the command working directory is not `research_orchestrator/`.
   - Resolving paths relative to `Path(__file__).resolve().parent.parent` (`STATIC_DIR` and `OUTPUTS_DIR`) guarantees portability across all execution environments (tests, workspace root, CI, Docker).
   - Calling `mkdir(parents=True, exist_ok=True)` on startup prevents `RuntimeError: Directory does not exist` when mounting `/outputs`.

---

## 3. Caveats
1. **In-Memory Volatility**: Conversation history in `sessions: dict[str, list]` is in-memory. Server restarts purge ongoing sessions, but files saved in `outputs/{session_id}/` remain persistent on disk.
2. **Concurrent Request Race Conditions**: Simultaneous requests with the identical `session_id` could execute concurrently in `Runner.run`. Milestone 3 plans client-side request debouncing (disabling send buttons during in-flight turns).
3. **No File Deletion Endpoint**: There is currently no endpoint to delete sessions or prune `outputs/`. Disk growth is bounded only by storage capacity.

---

## 4. Conclusion
1. `research_orchestrator/app/main.py` requires three targeted updates for Milestone 1:
   - Validate `session_id` and non-empty `message` in `ChatRequest` using Pydantic `@field_validator`.
   - Resolve absolute directory paths for `static` and `outputs` relative to `__file__`, creating `outputs` if missing.
   - Mount `/outputs` via `StaticFiles(directory=str(OUTPUTS_DIR))` alongside `/static`.
2. `research_orchestrator/app/tools.py` requires defense-in-depth path validation ensuring `output_dir.is_relative_to(outputs_base)`.
3. Zero new packages are needed in `requirements.txt`.

---

## 5. Concrete Recommendations for the Worker

### Recommendation 1: Update `research_orchestrator/app/main.py`

```python
"""FastAPI application – serves the chat endpoint and the static UI."""

from __future__ import annotations

import re
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from agents import Runner

from app.agent import orchestrator_agent
from app.tools import SessionContext

app = FastAPI(title="AI Research Orchestrator")

# ── Directory paths & static mounts ──────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
OUTPUTS_DIR = BASE_DIR / "outputs"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# ── In-memory conversation store ─────────────────────────────────────
sessions: dict[str, list] = {}

SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


# ── Request / response schemas ───────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str

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
        if history:
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


# Static files & root page
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


@app.get("/")
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))
```

### Recommendation 2: Update `research_orchestrator/app/tools.py`
In `finalize_research_spec`:
```python
    base_dir = Path(__file__).resolve().parent.parent / "outputs"
    output_dir = (base_dir / ctx.context.session_id).resolve()

    # Defense-in-depth: Ensure the resolved path remains strictly inside outputs/
    if not output_dir.is_relative_to(base_dir) or output_dir == base_dir:
        raise ValueError(f"Unsafe session_id: {ctx.context.session_id!r}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Clarified problem statement as Markdown
    md_path = output_dir / "clarified_problem_statement.md"
    md_path.write_text(
        f"# Clarified Problem Statement\n\n{spec.clarified_problem_statement}\n",
        encoding="utf-8",
    )

    # Full research spec as JSON
    json_path = output_dir / "research_spec.json"
    json_path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")

    # Mark session as finalized so the endpoint can report it
    ctx.context.finalized = True
    ctx.context.output_dir = f"outputs/{ctx.context.session_id}"
```

---

## 6. Verification Method

### 6.1 In-Process ASGI Verification Script
Run the following verification command from `/Users/bharathbr/reasearch_agent/research_orchestrator`:
```bash
./.venv/bin/python -c '
import asyncio, httpx
from app.main import app

async def run_verification():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        # 1. GET / serves 200 with text/html
        r1 = await c.get("/")
        assert r1.status_code == 200, f"GET / failed: {r1.status_code}"
        assert "text/html" in r1.headers.get("content-type", "")

        # 2. GET /static/index.html serves 200
        r2 = await c.get("/static/index.html")
        assert r2.status_code == 200, f"GET /static failed: {r2.status_code}"

        # 3. GET /outputs/... serves 200 with application/json
        r3 = await c.get("/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/research_spec.json")
        assert r3.status_code == 200, f"GET /outputs failed: {r3.status_code}"
        assert "application/json" in r3.headers.get("content-type", "")

        # 4. Unknown session returns 404
        r4 = await c.get("/outputs/nonexistent-session-id/research_spec.json")
        assert r4.status_code == 404, f"Expected 404 for unknown session, got {r4.status_code}"

        # 5. Traversal on /outputs/ returns 404
        r5 = await c.get("/outputs/../app/main.py")
        assert r5.status_code == 404, f"Expected 404 for traversal, got {r5.status_code}"

        # 6. Valid POST /chat returns 200
        r6 = await c.post("/chat", json={"session_id": "test-session-m1", "message": "Hello"})
        assert r6.status_code == 200, f"Valid chat failed: {r6.status_code}"
        data = r6.json()
        assert "reply" in data and "finalized" in data

        # 7. Traversal in POST /chat returns 422
        r7 = await c.post("/chat", json={"session_id": "../../etc/passwd", "message": "Hello"})
        assert r7.status_code == 422, f"Expected 422 for traversal session_id, got {r7.status_code}"

        # 8. Empty session_id returns 422
        r8 = await c.post("/chat", json={"session_id": "", "message": "Hello"})
        assert r8.status_code == 422, f"Expected 422 for empty session_id, got {r8.status_code}"

        # 9. Empty message returns 422
        r9 = await c.post("/chat", json={"session_id": "valid-id", "message": "   "})
        assert r9.status_code == 422, f"Expected 422 for empty message, got {r9.status_code}"

        print("--> ALL M1 BACKEND VERIFICATION CHECKS PASSED SUCCESSFULLY")

asyncio.run(run_verification())
'
```

### 6.2 Invalidation Conditions
- If `r3` returns `404`, `/outputs` has not been mounted in `app/main.py`.
- If `r7` returns `200`, `session_id` directory traversal validation has not been applied.
- If `r8` or `r9` returns `200`, empty string validation has not been applied.

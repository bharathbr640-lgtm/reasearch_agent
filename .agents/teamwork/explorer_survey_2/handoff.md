# Survey Report: FastAPI Orchestrator Backend Investigation

## 1. Observation

### 1.1 Backend Files Examined
Direct inspections were performed on the following repository paths:
- `/Users/bharathbr/reasearch_agent/research_orchestrator/app/main.py`
- `/Users/bharathbr/reasearch_agent/research_orchestrator/app/agent.py`
- `/Users/bharathbr/reasearch_agent/research_orchestrator/app/tools.py`
- `/Users/bharathbr/reasearch_agent/research_orchestrator/app/config.py`
- `/Users/bharathbr/reasearch_agent/research_orchestrator/requirements.txt`
- `/Users/bharathbr/reasearch_agent/research_orchestrator/test_e2e.py`
- `/Users/bharathbr/reasearch_agent/research_orchestrator/static/index.html`
- `/Users/bharathbr/reasearch_agent/stitch_screen/screen_1940b14692274c4197c2b8086465105d.html`

### 1.2 Exact FastAPI Endpoints & Static Mounts
In `research_orchestrator/app/main.py`:
- **Line 14**:
  ```python
  app = FastAPI(title="AI Research Orchestrator")
  ```
- **Lines 35-37**:
  ```python
  @app.post("/chat", response_model=ChatResponse)
  async def chat(req: ChatRequest) -> ChatResponse:
      """Send a user message and receive the Orchestrator's reply."""
  ```
- **Line 68**:
  ```python
  # Static files & root page
  app.mount("/static", StaticFiles(directory="static"), name="static")
  ```
- **Lines 71-73**:
  ```python
  @app.get("/")
  async def root():
      return FileResponse("static/index.html")
  ```

### 1.3 Data Models & Schemas
In `research_orchestrator/app/main.py` (Lines 22-30):
```python
class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    finalized: bool
    output_dir: str | None = None
```

In `research_orchestrator/app/tools.py` (Lines 16-35, 72-89):
```python
@dataclass
class SessionContext:
    """Mutable context carried through a single /chat request."""
    session_id: str
    finalized: bool = False
    output_dir: str = ""

class ResearchSpec(BaseModel):
    original_problem_statement: str
    clarified_problem_statement: str
    expected_input: str
    expected_output: str
    constraints: str
    datasets_and_technologies: str
    other_requirements: str
    assumptions: str
    research_focus: str
```
When `finalize_research_spec` is invoked by the agent:
- Writes `outputs/{session_id}/clarified_problem_statement.md`
- Writes `outputs/{session_id}/research_spec.json`
- Sets `ctx.context.finalized = True`
- Sets `ctx.context.output_dir = "outputs/{session_id}"`

### 1.4 State & Session Management
In `research_orchestrator/app/main.py`:
- **Line 17**:
  ```python
  # In-memory conversation store
  sessions: dict[str, list] = {}
  ```
- **Lines 38-48, 58-64**:
  ```python
  history = sessions.get(req.session_id, [])
  history.append({"role": "user", "content": req.message})

  ctx = SessionContext(session_id=req.session_id)

  try:
      result = await Runner.run(
          orchestrator_agent,
          input=history,
          context=ctx,
      )
  ...
  sessions[req.session_id] = result.to_input_list()

  return ChatResponse(
      reply=result.final_output,
      finalized=ctx.finalized,
      output_dir=ctx.output_dir if ctx.finalized else None,
  )
  ```
- State is held in-memory across calls keyed by `session_id`. Process restarts clear active in-memory dialogues.
- Output artifacts are saved persistently on disk at `outputs/{session_id}/`.

### 1.5 Dependencies in `requirements.txt`
In `research_orchestrator/requirements.txt`:
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
Installed environment check (`pip list`):
- `fastapi 0.142.2`, `starlette 1.7.0`, `uvicorn 0.54.0`, `pydantic 2.13.5`, `httpx 0.28.1`, `openai-agents 0.22.3`.

### 1.6 Empirical Endpoint Verification Results
1. **GET `/` Verification**:
   Command:
   ```bash
   ./.venv/bin/python -c '
   import asyncio, httpx
   from app.main import app
   async def test():
       async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
           r = await c.get("/")
           print("status:", r.status_code, "content-type:", r.headers.get("content-type"))
   asyncio.run(test())
   '
   ```
   Output:
   ```
   status: 200 content-type: text/html; charset=utf-8
   ```

2. **GET `/static/index.html` Verification**:
   Output:
   ```
   status: 200 content-type: text/html; charset=utf-8
   ```

3. **POST `/chat` Success Verification**:
   Command:
   ```bash
   ./.venv/bin/python -c '
   import asyncio, httpx
   from app.main import app
   async def test():
       async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
           r = await c.post("/chat", json={"session_id": "test-session-1", "message": "Hello"})
           print("status:", r.status_code, "data:", r.json())
   asyncio.run(test())
   '
   ```
   Output:
   ```
   status: 200 data: {'reply': 'Hi! What project or research question would you like help scoping today?', 'finalized': False, 'output_dir': None}
   ```

4. **POST `/chat` Schema Validation Error Verification**:
   Payload: `{"session_id": "missing-message"}`
   Output:
   ```
   status: 422 data: {'detail': [{'type': 'missing', 'loc': ['body', 'message'], 'msg': 'Field required', 'input': {'session_id': 'missing-message'}}]}
   ```

5. **GET `/outputs/...` Static Mount Verification**:
   Tested URL: `/outputs/28a8c6cf-20c9-45e8-8707-0d4162a66742/research_spec.json`
   Output:
   ```
   status: 404 Not Found
   ```
   Observation: The `/outputs` folder is NOT currently mounted as a static directory in `app/main.py`.

---

## 2. Logic Chain

1. **Endpoint Topology**:
   - Observations 1.2 and 1.6 confirm that the backend exposes only two active HTTP routes (`GET /` and `POST /chat`) and mounts `/static`.
   - The browser requesting `GET /` receives `static/index.html` with MIME type `text/html`.
   - Consequently, replacing `research_orchestrator/static/index.html` with the unified Stitch prototype directly upgrades the entire UI served at `GET /` without changing FastAPI routing.

2. **Data Model Alignment**:
   - Observation 1.3 shows that `POST /chat` expects `{ "session_id": "<uuid>", "message": "<string>" }`.
   - The response always contains `{ "reply": "<string>", "finalized": <boolean>, "output_dir": <string|null> }`.
   - In the target Stitch prototype (`screen_1940b14692274c4197c2b8086465105d.html`), starting research can generate a client `sessionId = crypto.randomUUID()`, dispatch the problem statement to `POST /chat`, and transition the user from Dashboard/Start View to the Active Research View.
   - Clarifying turns from the Orchestrator are returned in `data.reply`. While `finalized === false`, the active session view displays the Orchestrator questions and accepts user clarification replies with the same `sessionId`.
   - When the Orchestrator confirms and saves the spec, `data.finalized` becomes `true` and `data.output_dir` indicates the path. The UI can then highlight 01 Orchestrator completion, notify the user, and transition/populate the Report View.

3. **Zero Heavy Backend Dependencies**:
   - Observation 1.5 confirms that `requirements.txt` contains only lightweight, necessary libraries: `fastapi`, `uvicorn`, `pydantic`, `httpx`, and `openai-agents`.
   - The Stitch UI uses client-side Tailwind CSS (via CDN) and standard browser `fetch()` APIs.
   - Therefore, no new backend dependencies (e.g. Celery, Redis, WebSockets, or additional database packages) are required to satisfy the user request.

4. **Session State Handling**:
   - Observation 1.4 confirms that backend conversation history is held in-memory in `app.main.sessions`.
   - The client retains `sessionId`, active view state (`'dashboard' | 'start' | 'active' | 'report'`), and conversation history.
   - Because `sessions` in `main.py` is an in-memory dictionary, client-side session continuity depends on keeping the same `session_id` across turns.

---

## 3. Caveats

1. **Unmounted `/outputs` Directory**:
   - `outputs/{session_id}/` on disk contains `research_spec.json` and `clarified_problem_statement.md`. However, `/outputs` is not mounted in `main.py` (it returned 404 in Observation 1.6).
   - If the frontend needs to directly `fetch('/outputs/' + sessionId + '/research_spec.json')`, `app/main.py` would need `app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")` (using Starlette's already-imported `StaticFiles`), OR the frontend can display the finalized summary from `data.reply` and client session state.
2. **Synchronous Unary POST (No Streaming / WebSockets)**:
   - `POST /chat` does not use Server-Sent Events (SSE) or WebSockets. It is a single async request that awaits `Runner.run` and returns `ChatResponse`.
   - Telemetry logs shown in the Stitch prototype (`telemetry-log`) must therefore either reflect request lifecycle phases or synthesize step progression during in-flight requests.
3. **In-Memory Volatility**:
   - Backend memory is wiped if the server restarts. The frontend should handle error responses gracefully if a session is lost.

---

## 4. Conclusion

1. The FastAPI backend is fully operational, clean, and requires no dependency additions or heavy refactoring.
2. The endpoint contract is:
   - `GET /` -> Serves `static/index.html`.
   - `POST /chat` -> `{ "session_id": str, "message": str }` -> `{ "reply": str, "finalized": bool, "output_dir": str | null }`.
3. Client-side integration into `research_orchestrator/static/index.html` requires:
   - Preserving all 4 views (`view-dashboard`, `view-start`, `view-active`, `view-report`) and styling from `screen_1940b14692274c4197c2b8086465105d.html`.
   - Wiring the input forms (`#dashboard-input` and `#start-problem-textarea`) to dispatch `fetch('/chat', ...)` with a generated `session_id`.
   - Rendering dialogue and agent feedback inside `#view-active`.
   - Transitioning to `#view-report` when `finalized: true`, displaying the confirmed specification and summary.

---

## 5. Verification Method

### 5.1 Standalone Python ASGI In-Process Verification
Run the following command directly from `/Users/bharathbr/reasearch_agent/research_orchestrator`:
```bash
./.venv/bin/python -c '
import asyncio, httpx
from app.main import app

async def verify_backend():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Verify GET /
        r1 = await client.get("/")
        assert r1.status_code == 200, f"GET / failed: {r1.status_code}"
        assert "text/html" in r1.headers["content-type"], "Invalid content type for GET /"

        # 2. Verify static mount
        r2 = await client.get("/static/index.html")
        assert r2.status_code == 200, f"GET /static/index.html failed: {r2.status_code}"

        # 3. Verify POST /chat 422 on invalid schema
        r3 = await client.post("/chat", json={"invalid_field": 123})
        assert r3.status_code == 422, f"POST /chat schema validation failed: {r3.status_code}"

        # 4. Verify POST /chat 200 on valid message
        r4 = await client.post("/chat", json={"session_id": "test-verify-session", "message": "Hello"})
        assert r4.status_code == 200, f"POST /chat failed: {r4.status_code}"
        data = r4.json()
        assert "reply" in data and "finalized" in data, f"Missing expected fields: {data}"

        print("ALL VERIFICATIONS PASSED SUCCESSFULLY")

asyncio.run(verify_backend())
'
```

### 5.2 Live HTTP / Curl Commands (with Uvicorn running)
1. Start server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. Check root:
   ```bash
   curl -I http://127.0.0.1:8000/
   ```
   *Expected*: `HTTP/1.1 200 OK`, `content-type: text/html; charset=utf-8`.
3. Check chat endpoint:
   ```bash
   curl -X POST http://127.0.0.1:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"session_id": "curl-test-1", "message": "Test research idea"}'
   ```
   *Expected*: JSON object with `"reply"`, `"finalized"`, `"output_dir"`.

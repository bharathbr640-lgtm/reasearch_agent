# Adversarial Challenge Report — Milestone 1 Backend Security & Boundary Verification

## 1. Observation

Direct empirical observations made on `research_orchestrator/app/main.py` and `research_orchestrator/app/tools.py`:

### Code Inspection
In `research_orchestrator/app/main.py`:
- Lines 30–56:
```python
SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

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
```
- Lines 100–106:
```python
# Static files & output directory mounting
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


@app.get("/")
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))
```

In `research_orchestrator/app/tools.py`:
- Lines 72–78:
```python
    base_dir = (Path(__file__).resolve().parent.parent / "outputs").resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    output_dir = (base_dir / ctx.context.session_id).resolve()

    # Defense-in-depth: Ensure the resolved path remains strictly inside outputs/
    if not output_dir.is_relative_to(base_dir) or output_dir == base_dir:
        raise ValueError(f"Unsafe session_id: {ctx.context.session_id!r}")
```

### Empirical Test Execution Results
An adversarial test suite (`research_orchestrator/tests/test_adversarial_m1.py`) comprising 54 test cases was authored and executed using `pytest research_orchestrator/tests/test_adversarial_m1.py -v`:

1. **Path Traversal Attacks**:
   - `GET /outputs/../requirements.txt` -> HTTP 404 (PASSED)
   - `GET /outputs/%2e%2e/app/main.py` -> HTTP 404 (PASSED)
   - `GET /outputs/%2e%2e%2frequirements.txt` -> HTTP 404 (PASSED)
   - `GET /outputs/....//app/main.py` -> HTTP 404 (PASSED)
   - `GET /static/../requirements.txt` -> HTTP 404 (PASSED)
   - `GET /static/%2e%2e/requirements.txt` -> HTTP 404 (PASSED)
   - `GET /outputs/test-sub/../../requirements.txt` -> HTTP 404 (PASSED)
   - Raw ASGI Scope Path Traversal (`path="/outputs/../requirements.txt"`, `path="/outputs/%2e%2e/app/main.py"`, `path="/outputs/..%2fapp/main.py"`) directly dispatched without HTTP client path canonicalization -> HTTP 404 (PASSED)
   - `POST /chat` with `session_id`:
     - `"../../etc/passwd"` -> HTTP 422 with `Value error, session_id must be alphanumeric with hyphens or underscores (1-64 characters)` (PASSED)
     - `"/tmp/bad"` -> HTTP 422 (PASSED)
     - `"bad\x00id"` -> HTTP 422 (PASSED)
     - `"../outputs"`, `".."` , `"."`, `"./"`, `"..\\..\\windows\\system32"` -> HTTP 422 (PASSED)
     - `"session;rm -rf /"`, `"$(whoami)"`, `"<script>alert(1)</script>"`, `"`"`, `"'"` -> HTTP 422 (PASSED)
     - Unicode homoglyphs/non-ASCII (`éèç_unicode`, `а-я_cyrillic`) -> HTTP 422 (PASSED)
     - Length overflow: `"a" * 65` -> HTTP 422 (PASSED)
     - Whitespace / Empty: `""`, `"   "` -> HTTP 422 (PASSED)

2. **Schema Boundary Stress**:
   - Empty body `{}` -> HTTP 422 (missing both `session_id` and `message`) (PASSED)
   - Empty message `""` -> HTTP 422 (`Value error, message cannot be empty`) (PASSED)
   - Whitespace messages `"   "`, `"\t\n\r"`, `" \t "` -> HTTP 422 (PASSED)
   - Invalid datatype `session_id=123` (integer) -> HTTP 422 `Input should be a valid string` (PASSED)
   - Invalid datatype `session_id=["list", "val"]` -> HTTP 422 (PASSED)
   - Invalid datatype `session_id=None` -> HTTP 422 (PASSED)
   - Invalid datatype `message=[]` (list) -> HTTP 422 `Input should be a valid string` (PASSED)
   - Invalid datatype `message={}` (dict) -> HTTP 422 (PASSED)
   - Invalid datatype `message=456` (integer) -> HTTP 422 (PASSED)
   - Invalid datatype `message=None` -> HTTP 422 (PASSED)
   - Boundary valid lengths: `session_id="a"` (1 char) -> HTTP 200 (PASSED); `session_id="a"*64` (64 chars) -> HTTP 200 (PASSED); `session_id="a"*65` (65 chars) -> HTTP 422 (PASSED)

3. **HTTP Method Enforcement**:
   - `POST /` -> HTTP 405 Method Not Allowed (PASSED)
   - `PUT /` -> HTTP 405 Method Not Allowed (PASSED)
   - `DELETE /` -> HTTP 405 Method Not Allowed (PASSED)
   - `PATCH /` -> HTTP 405 Method Not Allowed (PASSED)
   - `GET /chat` -> HTTP 405 Method Not Allowed (PASSED)
   - `PUT /chat` -> HTTP 405 Method Not Allowed (PASSED)
   - `DELETE /chat` -> HTTP 405 Method Not Allowed (PASSED)
   - `PATCH /chat` -> HTTP 405 Method Not Allowed (PASSED)

4. **Full Test Suite Run (`pytest research_orchestrator/tests -v`)**:
   - 84 passed, 1 skipped in 2.84s (0 failures, 0 errors).
   - The single skipped test (`test_tier1_live_spa_view_containers_contract`) is intentionally deferred to Milestone 2 when the full SPA HTML is mounted.

## 2. Logic Chain

1. **Path Traversal Resilience**:
   - Starlette's `StaticFiles` component implements internal path resolution that verifies the requested file path is contained within the root directory (`STATIC_DIR` or `OUTPUTS_DIR`).
   - When requests containing `..` or URL-encoded equivalents (`%2e%2e`) are sent via HTTP or raw ASGI scope, Starlette detects the traversal or non-existent file relative to the mount and returns `404 Not Found`.
   - In `research_orchestrator/app/tools.py`, `output_dir = (base_dir / ctx.context.session_id).resolve()` is guarded by `if not output_dir.is_relative_to(base_dir) or output_dir == base_dir: raise ValueError(...)`. Thus, even if a bypass occurred before the endpoint, the filesystem write would be blocked.

2. **Input Sanitization & Schema Defense**:
   - The regex `r"^[a-zA-Z0-9_-]{1,64}$"` restricts `session_id` strictly to ASCII alphanumeric characters, underscores, and hyphens.
   - Any character outside this set (slashes, backslashes, dots, null bytes, command injection tokens, whitespace, unicode) fails regex matching and raises `ValueError`, which FastAPI translates to `HTTP 422 Unprocessable Entity`.
   - The `message` validator calls `v = v.strip()` and verifies `bool(v)`. Any empty or whitespace-only string raises `ValueError("message cannot be empty")`, returning `HTTP 422`.
   - Pydantic v2 enforces type strictness on `session_id: str` and `message: str`, returning `HTTP 422` when receiving arrays, objects, numbers, or `None`.

3. **HTTP Method Enforcement**:
   - `GET /` is explicitly declared on `app.get("/")`, and `POST /chat` is declared on `app.post("/chat")`. Starlette router routes unmatched methods for an existing path to an automatic `405 Method Not Allowed` response.
   - All unauthorized verbs (`POST`, `PUT`, `DELETE`, `PATCH` on `/`, and `GET`, `PUT`, `DELETE`, `PATCH` on `/chat`) consistently return `HTTP 405`.

## 3. Caveats

- In-memory `sessions: dict[str, list] = {}` is non-persistent across server restarts. This is an intended design constraint for Milestone 1 as specified in `PROJECT.md` (no external databases added).
- Large payloads (e.g. 100KB messages) are accepted by the endpoint without a fixed length cap in the Pydantic schema, though FastAPI handles them without crashing. LLM token limits will naturally govern prompt size.
- Implementation code in `research_orchestrator/app/` was inspected in review-only mode and was NOT modified.

## 4. Conclusion

The Milestone 1 backend endpoints in `research_orchestrator/app/main.py` fully satisfy all security and boundary handling requirements. Path traversal attacks are rejected with HTTP 404, malicious session IDs and malformed schemas are rejected with HTTP 422, and unauthorized HTTP methods are blocked with HTTP 405.

**Verdict: APPROVE**

## 5. Verification Method

To independently verify all findings and execute the full adversarial and contract test suite:

```bash
cd /Users/bharathbr/reasearch_agent
pytest research_orchestrator/tests -v
```

Expected result:
- 84 passed, 1 skipped in ~2.8s
- 0 failed, 0 errors

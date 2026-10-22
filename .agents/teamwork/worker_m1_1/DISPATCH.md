## 2026-10-14T10:22:20Z
You are worker_m1_1.
Your working directory is: /Users/bharathbr/reasearch_agent/.agents/teamwork/worker_m1_1
You MUST read the authoritative user request at: /Users/bharathbr/reasearch_agent/.agents/teamwork/ORIGINAL_REQUEST.md before doing anything else.
Also read /Users/bharathbr/reasearch_agent/PROJECT.md.

Read the findings and code recommendations from the three Milestone 1 Explorers:
- /Users/bharathbr/reasearch_agent/.agents/teamwork/explorer_m1_1/handoff.md
- /Users/bharathbr/reasearch_agent/.agents/teamwork/explorer_m1_2/handoff.md
- /Users/bharathbr/reasearch_agent/.agents/teamwork/explorer_m1_3/handoff.md

Your exclusive write ownership is strictly restricted to:
- /Users/bharathbr/reasearch_agent/research_orchestrator/app/main.py
- /Users/bharathbr/reasearch_agent/research_orchestrator/app/tools.py
- /Users/bharathbr/reasearch_agent/research_orchestrator/tests/test_api_contract.py
DO NOT modify any other files. In particular, DO NOT touch research_orchestrator/requirements.txt (must remain 100% unchanged).

Tasks for Milestone 1 (Backend Foundation & Static Output Mounting):
1. In research_orchestrator/app/main.py:
   - Resolve absolute directory paths relative to __file__:
     BASE_DIR = Path(__file__).resolve().parent.parent
     STATIC_DIR = BASE_DIR / "static"
     OUTPUTS_DIR = BASE_DIR / "outputs"
     STATIC_DIR.mkdir(parents=True, exist_ok=True)
     OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
   - Mount /outputs static directory cleanly via:
     app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
   - Update /static mount to use str(STATIC_DIR).
   - Update root() route to return FileResponse(str(STATIC_DIR / "index.html")).
   - In ChatRequest, validate session_id (regex ^[a-zA-Z0-9_-]{1,64}$) and ensure message is not empty.
2. In research_orchestrator/app/tools.py:
   - Ensure output directory resolution is safe and checked via .is_relative_to().
3. In research_orchestrator/tests/test_api_contract.py:
   - Add test_tier1_get_outputs_research_spec to assert that GET /outputs/{session_id}/research_spec.json returns 200 OK with application/json.
4. Execute tests:
   - Run python3 -m pytest tests/ -v
   - Run the verification scripts provided in explorer_m1_3/handoff.md.
   - Verify all tests pass with 0 failures.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your handoff report to:
/Users/bharathbr/reasearch_agent/.agents/teamwork/worker_m1_1/handoff.md
Include passing test commands and output. When done, send a message to the caller.

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


# Static files & output directory mounting
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


@app.get("/")
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))

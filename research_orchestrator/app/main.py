"""FastAPI application – serves the chat endpoint and the static UI."""

from __future__ import annotations

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


# Static files & root page
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")

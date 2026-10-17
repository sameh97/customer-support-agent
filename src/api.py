"""
src/api.py — FastAPI REST layer.

Exposes the chatbot as an HTTP service.
Any frontend, mobile app, or external system can now talk to it.

Endpoints:
  POST /chat          — send a message, get a response
  POST /chat/confirm  — answer a pending confirmation (human-in-the-loop)
  GET  /info          — business name / support email for the UI
  GET  /health        — liveness check (used by Docker/k8s)
  POST /reset         — clear conversation history for a session

If the React app has been built (frontend/dist), it is served at /.
"""

import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from langgraph.types import Command
from pydantic import BaseModel

from src.config import settings
from src.graph import chatbot

app = FastAPI(
    title="Customer Support Bot",
    description="AI-powered support agent",
    version="1.0.0",
)


# ── Request / Response schemas ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # if omitted, a new session is created


class PendingAction(BaseModel):
    id: str
    title: str
    description: str
    confirm_label: str
    cancel_label: str


class ChatResponse(BaseModel):
    response: str
    session_id: str  # always returned so the client can continue the conversation
    pending_action: PendingAction | None = None  # set when the agent waits for the customer


class ConfirmRequest(BaseModel):
    session_id: str
    approved: bool


# ── Helpers ───────────────────────────────────────────────────────────────────

def _config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def _pending_action(session_id: str) -> PendingAction | None:
    """The confirmation the agent is paused on for this session, if any."""
    interrupts = chatbot.get_state(_config(session_id)).interrupts
    if not interrupts:
        return None
    return PendingAction(id=interrupts[0].id, **interrupts[0].value)


def _run(payload, session_id: str) -> ChatResponse:
    try:
        result = chatbot.invoke(payload, config=_config(session_id))
        pending = _pending_action(session_id)
        if pending:
            return ChatResponse(response="", session_id=session_id, pending_action=pending)
        return ChatResponse(response=result.content, session_id=session_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main chat endpoint.

    session_id ties messages to a conversation thread.
    The client (frontend/app) should:
      1. Call /chat without session_id on first message → get session_id back
      2. Pass that session_id on every following message → bot remembers context
      3. If pending_action is set, show it and answer via /chat/confirm
    """
    session_id = request.session_id or str(uuid.uuid4())

    if _pending_action(session_id):
        raise HTTPException(status_code=409, detail="Confirm or decline the pending action first.")

    return _run([{"role": "user", "content": request.message}], session_id)


@app.post("/chat/confirm", response_model=ChatResponse)
def confirm(request: ConfirmRequest):
    """Resume a paused conversation with the customer's yes/no."""
    if not _pending_action(request.session_id):
        raise HTTPException(status_code=409, detail="Nothing is waiting for confirmation.")

    return _run(Command(resume={"approved": request.approved}), request.session_id)


@app.get("/info")
def info():
    """Branding for the frontend."""
    return {
        "business_name": settings.business_name,
        "support_email": settings.support_email,
    }


@app.get("/health")
def health():
    """Liveness check — used by Docker, k8s, load balancers."""
    return {"status": "ok"}


@app.post("/reset/{session_id}")
def reset_session(session_id: str):
    """
    Clear conversation history for a session.
    Useful for 'start new conversation' buttons in a UI.
    Note: with InMemorySaver this just means the thread starts fresh
    on next message. With a persistent checkpointer you'd delete the DB record.
    """
    # InMemorySaver has no delete API — a new thread_id achieves the same effect.
    # When you swap to PostgresSaver/RedisSaver, delete the checkpoint here.
    new_session_id = str(uuid.uuid4())
    return {
        "message": "Session reset",
        "new_session_id": new_session_id,
    }


# ── Frontend ──────────────────────────────────────────────────────────────────
# Mounted last so the API routes above take priority.

_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")

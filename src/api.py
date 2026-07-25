"""
src/api.py — FastAPI REST layer.

Exposes the chatbot as an HTTP service.
Any frontend, mobile app, or external system can now talk to it.

Endpoints:
  POST /chat      — send a message, get a response
  GET  /health    — liveness check (used by Docker/k8s)
  POST /reset     — clear conversation history for a session
"""

import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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


class ChatResponse(BaseModel):
    response: str
    session_id: str  # always returned so the client can continue the conversation


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main chat endpoint.

    session_id ties messages to a conversation thread.
    The client (frontend/app) should:
      1. Call /chat without session_id on first message → get session_id back
      2. Pass that session_id on every following message → bot remembers context
    """
    session_id = request.session_id or str(uuid.uuid4())

    try:
        response = chatbot.invoke(
            [{"role": "user", "content": request.message}],
            config={"configurable": {"thread_id": session_id}},
        )
        return ChatResponse(response=response.content, session_id=session_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
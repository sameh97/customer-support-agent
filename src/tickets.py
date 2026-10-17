"""
src/tickets.py — support tickets.

Tools and scripts talk to tickets only through these functions, so the
storage can change (e.g. to Zendesk) without touching the agent.

Customer-facing lookups are always scoped to a session_id: a customer can
only see tickets opened in their own conversation.
"""

import secrets
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, Text, func, select
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base, SessionLocal

# Status → what it means for the customer (shown to the LLM so it doesn't guess)
STATUSES = {
    "open": "waiting for a teammate to pick it up",
    "in_progress": "a teammate is working on it",
    "waiting_on_customer": "the teammate is waiting for a reply from the customer",
    "resolved": "the issue has been resolved",
}

# No 0/O/1/I so codes are easy to read out and type
_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'in_progress', 'waiting_on_customer', 'resolved')",
            name="ck_tickets_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)  # customer-facing, e.g. T-7K2M9Q
    session_id: Mapped[str | None] = mapped_column(String(64), index=True)
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), server_default="open")
    last_update: Mapped[str | None] = mapped_column(Text)  # latest note from the teammate
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def _new_code() -> str:
    # Random, not sequential, so codes can't be guessed or enumerated
    return "T-" + "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))


def normalize_code(code: str) -> str:
    """Accept 't-7k2m9q', '7K2M9Q', ' T-7K2M9Q ' etc."""
    code = code.strip().upper()
    return code if code.startswith("T-") else f"T-{code}"


def create_ticket(session_id: str | None, summary: str) -> Ticket:
    with SessionLocal.begin() as db:
        ticket = Ticket(code=_new_code(), session_id=session_id, summary=summary, status="open")
        db.add(ticket)
    return ticket


def list_tickets(session_id: str) -> list[Ticket]:
    with SessionLocal() as db:
        query = select(Ticket).where(Ticket.session_id == session_id).order_by(Ticket.created_at.desc())
        return list(db.scalars(query))


def get_ticket(code: str, session_id: str) -> Ticket | None:
    """A ticket by code, only if it belongs to this session."""
    with SessionLocal() as db:
        query = select(Ticket).where(Ticket.code == normalize_code(code), Ticket.session_id == session_id)
        return db.scalar(query)


# ── Staff-only (not exposed to the agent) ─────────────────────────────────────

def list_all_tickets(limit: int = 50) -> list[Ticket]:
    with SessionLocal() as db:
        return list(db.scalars(select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)))


def update_ticket(code: str, status: str | None = None, note: str | None = None) -> Ticket | None:
    if status is not None and status not in STATUSES:
        raise ValueError(f"status must be one of: {', '.join(STATUSES)}")
    with SessionLocal.begin() as db:
        ticket = db.scalar(select(Ticket).where(Ticket.code == normalize_code(code)))
        if ticket is None:
            return None
        if status is not None:
            ticket.status = status
        if note is not None:
            ticket.last_update = note
    return ticket

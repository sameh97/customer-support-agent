"""
src/tools.py — all agent tools.

Each tool is a plain Python function decorated with @tool.
The LLM reads the docstring to decide WHEN to call each tool
and what arguments to pass — so write clear docstrings.

tools_by_name is used by the graph to dispatch tool calls.
tools list is bound to the LLM so it knows what's available.
"""

from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langgraph.config import get_config
from langchain_tavily import TavilySearch

from src.config import settings
from src.rag import get_retriever
from src.tickets import STATUSES, create_ticket, get_ticket, list_tickets

tavily_tool = TavilySearch(max_results=5)



# ── RAG tool ──────────────────────────────────────────────────────────────────

_retriever = None  # lazy-loaded on first use

def _get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = get_retriever()
    return _retriever


@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the company knowledge base for answers about products, pricing,
    billing, technical issues, onboarding, and company policies.
    Use this whenever a customer asks a question about the business.
    Returns the most relevant excerpts from our documentation.
    """
    docs = _get_retriever().invoke(query)
    if not docs:
        return "No relevant information found in the knowledge base."

    # Format results so the LLM can read them clearly
    results = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        results.append(f"[Result {i}] (source: {source})\n{doc.page_content}")

    return "\n\n---\n\n".join(results)


# ── Human handoff tool ────────────────────────────────────────────────────────

def _session_id() -> str | None:
    """The conversation's thread_id, or None when called outside a graph run."""
    try:
        return get_config()["configurable"].get("thread_id")
    except RuntimeError:
        return None


@tool
def escalate_to_human(summary: str) -> str:
    """
    Hand the conversation over to a human support teammate.
    Use this when the customer asks to talk to a person, is frustrated,
    or needs something you cannot do yourself (refunds, account changes, bugs).
    `summary` is one or two sentences written to the customer, in second person,
    saying what the teammate will help with, e.g. "You were charged twice
    this month and would like a refund." The customer sees it before confirming.
    """
    ticket = create_ticket(_session_id(), summary)
    return (
        f"Ticket {ticket.code} created. Tell the customer a teammate will follow up soon, "
        f"give them the ticket number {ticket.code} so they can ask about it later, "
        f"and mention they can also reach us at {settings.support_email}."
    )


# ── Ticket status tool ────────────────────────────────────────────────────────

def _format_ticket(t) -> str:
    return (
        f"Ticket {t.code}: {t.status.replace('_', ' ')} ({STATUSES[t.status]})\n"
        f"Opened: {t.created_at:%b %d, %Y}. About: {t.summary}\n"
        f"Latest update from the team: {t.last_update or 'none yet'}"
    )


@tool
def check_ticket_status(ticket_id: str | None = None) -> str:
    """
    Look up the status of the customer's support tickets.
    Use this when the customer asks about a ticket, a previous request,
    or whether a teammate has replied. Pass `ticket_id` (e.g. "T-7K2M9Q")
    only if the customer gives one. Otherwise call it with no arguments to get
    all their tickets. Never ask the customer for a ticket number first.
    """
    session_id = _session_id()
    if session_id is None:
        return "Ticket lookup isn't available outside a customer conversation."

    if ticket_id:
        ticket = get_ticket(ticket_id, session_id)
        if ticket is None:
            # Same answer whether it doesn't exist or belongs to someone else
            return (
                f"No ticket {ticket_id} was found for this customer. Ask them to double-check "
                f"the number, or to contact {settings.support_email}."
            )
        return _format_ticket(ticket)

    tickets = list_tickets(session_id)
    if not tickets:
        return "This customer has no support tickets in this conversation."
    return "\n\n".join(_format_ticket(t) for t in tickets)


# ── Tool registry ─────────────────────────────────────────────────────────────
# Add new tools to this list — graph.py picks them up automatically.

tools = [search_knowledge_base, escalate_to_human, check_ticket_status, tavily_tool]

tools_by_name: dict = {t.name: t for t in tools}


# ── Customer confirmation ─────────────────────────────────────────────────────
# Tools listed here change something for the customer, so the agent pauses
# and asks them to confirm first (see graph.py). Each entry turns the tool
# call's args into the confirmation card the customer sees.

confirmations: dict = {
    "escalate_to_human": lambda args: {
        "title": "Want me to bring in a teammate?",
        "description": args.get("summary", ""),
        "confirm_label": "Yes, connect me",
        "cancel_label": "Not now",
    },
}



def confirmation_for(tool_call: dict) -> dict | None:
    """Return the confirmation card for a tool call, or None if it can run directly."""
    build = confirmations.get(tool_call["name"])
    return build(tool_call["args"]) if build else None


# ── Tool executor ─────────────────────────────────────────────────────────────

def execute_tool_call(tool_call: dict) -> ToolMessage:
    """
    Execute a single tool call from the LLM and return a ToolMessage.
    ToolMessage wraps the result so the LLM knows which call it answers.
    """
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    print(f"[TOOL] {tool_name}({tool_args})")

    if tool_name not in tools_by_name:
        result = f"Error: unknown tool '{tool_name}'"
    else:
        try:
            result = tools_by_name[tool_name].invoke(tool_args)
        except Exception as e:
            result = f"Tool error: {str(e)}"

    return ToolMessage(
        content=str(result),
        tool_call_id=tool_call["id"],
    )
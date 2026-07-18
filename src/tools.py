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
from src.rag import get_retriever


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


# ── Tool registry ─────────────────────────────────────────────────────────────
# Add new tools to this list — graph.py picks them up automatically.

tools = [search_knowledge_base]

tools_by_name: dict = {t.name: t for t in tools}


# ── Tool executor ─────────────────────────────────────────────────────────────

def execute_tool_call(tool_call: dict) -> ToolMessage:
    """
    Execute a single tool call from the LLM and return a ToolMessage.
    ToolMessage wraps the result so the LLM knows which call it answers.
    """
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]

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